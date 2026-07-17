#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'Michael Rendier'
# Ptolemy / Phaleron — WalkTheHalls.py
# Forensic binary/filesystem analysis engine
# Primary data ingestion pre-processor for APISniff and Alexandria
# Console tool — acts on files queued for Ptolemy ingestion
#
# USAGE: python3 WalkTheHalls.py <target_file_or_device> [--report] [--json]

import os
import sys
import struct
import argparse
import subprocess
import json
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from pathlib import Path


# ─────────────────────────────────────────────
# DATACLASSES — The Fingerprint Vector
# ─────────────────────────────────────────────

@dataclass
class PartitionEntry:
    index:      int
    type_guid:  str
    name:       str
    start_lba:  int
    end_lba:    int
    size_bytes: int
    gap_before: int        # unallocated bytes before this partition — negative space


@dataclass
class MountEntry:
    device:     str
    mount_point: str
    fs_type:    str
    options:    str


@dataclass
class MagicHit:
    offset:     int
    magic:      str        # human label
    bytes_hex:  str        # raw matched bytes
    context:    str        # nearby strings


@dataclass
class StringHit:
    offset:     int
    length:     int
    value:      str
    section:    str        # rodata / data / unknown


@dataclass
class FstabEntry:
    source:     str
    mount_point: str
    fs_type:    str
    options:    str
    declared:   bool       # True=in fstab, may not be mounted
    mounted:    bool       # True=actually mounted


@dataclass
class FingerprintVector:
    """
    The structure IS the hash.
    This is the Alexandria input — topology of the binary as a graph.
    Each field feeds a district in the cityscape render.
    """
    source_file:        str
    file_size:          int
    partition_table:    str                        # GPT / MBR / NONE
    partitions:         List[PartitionEntry]       = field(default_factory=list)
    gaps:               List[Tuple[int,int]]       = field(default_factory=list)   # (offset, size) unallocated
    kernel_fs_types:    List[str]                  = field(default_factory=list)   # /proc/filesystems
    mounted_fs:         List[MountEntry]           = field(default_factory=list)   # live mounts
    fstab_entries:      List[FstabEntry]           = field(default_factory=list)   # declared vs actual delta
    fstab_orphans:      List[FstabEntry]           = field(default_factory=list)   # declared but NOT mounted
    magic_hits:         List[MagicHit]             = field(default_factory=list)   # known headers in raw image
    string_hits:        List[StringHit]            = field(default_factory=list)   # rodata strings
    fastboot_commands:  List[str]                  = field(default_factory=list)   # extracted OEM command table
    selinux_types:      List[str]                  = field(default_factory=list)   # policy type list if found
    inode_tombstones:   int                        = 0                             # deleted file count estimate
    sqlite_offsets:     List[int]                  = field(default_factory=list)   # SQLite DBs in raw image
    edges:              List[Tuple[str,str,str]]   = field(default_factory=list)   # (entity, relation, entity) graph


# ─────────────────────────────────────────────
# MAGIC BYTE TABLE
# ─────────────────────────────────────────────

MAGIC_TABLE = [
    (b'\x7fELF',                    'ELF Binary'),
    (b'SQLite format 3\x00',        'SQLite DB'),
    (b'PK\x03\x04',                 'ZIP/APK/JAR'),
    (b'\x1f\x8b',                   'gzip'),
    (b'BZh',                        'bzip2'),
    (b'\xfd7zXZ\x00',              'XZ'),
    (b'\x89PNG\r\n\x1a\n',         'PNG'),
    (b'\xff\xd8\xff',               'JPEG'),
    (b'ANDROID!',                   'Android Sparse Image'),
    (b'\x3a\xff\x26\xed',          'YAFFS2'),
    (b'\x06\x05\x36\x19',          'SquashFS LE'),
    (b'\x19\x73\x51\x6e',          'SquashFS BE'),
    (b'\x55\xAA',                   'MBR Signature'),     # at offset 510
    (b'\xef\xbe\xad\xde',          'EFI/Qualcomm Magic'),
    (b'OKIMG',                      'Qualcomm OTA'),
    (b'CHROMEOS',                   'ChromeOS Kernel'),
    (b'\x27\x05\x19\x56',          'U-Boot Image'),
    (b'SEANDROIDENFORCE',           'SEAndroid Policy'),
    (b'DHTB',                       'Samsung DHTB'),
]

# Known ELF section names to extract strings from
ELF_SECTIONS_OF_INTEREST = ['.rodata', '.data', '.dynstr', '.strtab']

# Known fastboot/OEM command prefixes to flag
FASTBOOT_MARKERS = [b'oem ', b'fastboot ', b'getvar:', b'erase:', b'flash:',
                    b'reboot-bootloader', b'continue', b'download:']


# ─────────────────────────────────────────────
# CLASS: HallwayStroll — Filesystem Topology
# ─────────────────────────────────────────────

class HallwayStroll:
    """
    Maps the filesystem topology of a target binary or live system.
    Produces the 'floorplan' — mount geometry as an adjacency structure.
    """

    def __init__(self, target: str, workdir: str):
        self.target  = target
        self.workdir = workdir
        self.fstypes: List[str] = []

    def the_rooms(self) -> List[str]:
        """Read kernel-supported fs types from /proc/filesystems"""
        types = []
        try:
            with open('/proc/filesystems') as f:
                for line in f:
                    t = line.strip().replace('nodev\t', '').replace('\t', '')
                    if t:
                        types.append(t)
        except FileNotFoundError:
            pass
        self.fstypes = types
        return types

    def the_hallway(self, fp: FingerprintVector):
        """
        Mount target via FUSE/guestfs (userspace — no sudo).
        Walk mounted structure to identify actual fs types present.
        Falls back to structural scan if guestfs unavailable.
        """
        hallway = os.path.join(self.workdir, 'Hallway')
        os.makedirs(os.path.join(hallway, 'All'), exist_ok=True)

        # Try libguestfs (userspace, no root)
        try:
            import guestfs
            g = guestfs.GuestFS(python_return_dict=True)
            g.add_drive_opts(self.target, readonly=1)
            g.launch()
            filesystems = g.list_filesystems()
            for device, fstype in filesystems.items():
                mp = os.path.join(hallway, fstype.replace('/', '_'))
                os.makedirs(mp, exist_ok=True)
                fp.edges.append((device, 'has_fs_type', fstype))
                fp.mounted_fs.append(MountEntry(device, mp, fstype, 'ro'))
            g.close()
            print(f"[HALLWAY] libguestfs found {len(filesystems)} filesystems")
        except ImportError:
            print("[HALLWAY] libguestfs not available — using structural scan")
            self._structural_scan(hallway, fp)
        except Exception as e:
            print(f"[HALLWAY] guestfs error: {e} — falling back")
            self._structural_scan(hallway, fp)

    def _structural_scan(self, hallway: str, fp: FingerprintVector):
        """Fallback: create dirs for each kernel-supported type, note which exist"""
        for fstype in self.fstypes:
            os.makedirs(os.path.join(hallway, fstype), exist_ok=True)
            fp.edges.append(('kernel', 'supports_fs', fstype))

    def live_mounts(self, fp: FingerprintVector):
        """Read /proc/mounts for live system topology"""
        try:
            with open('/proc/mounts') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 4:
                        e = MountEntry(parts[0], parts[1], parts[2], parts[3])
                        fp.mounted_fs.append(e)
                        fp.edges.append((parts[0], 'mounted_at', parts[1]))
        except Exception:
            pass

    def fstab_delta(self, fp: FingerprintVector, fstab_path: str = '/etc/fstab'):
        """Three-way diff: fstab declared vs /proc/mounts vs partition table"""
        mounted_points = {m.mount_point for m in fp.mounted_fs}
        try:
            with open(fstab_path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split()
                    if len(parts) < 4:
                        continue
                    is_mounted = parts[1] in mounted_points
                    e = FstabEntry(parts[0], parts[1], parts[2], parts[3],
                                   declared=True, mounted=is_mounted)
                    fp.fstab_entries.append(e)
                    if not is_mounted:
                        fp.fstab_orphans.append(e)   # declared but not mounted = hidden
                        fp.edges.append((parts[0], 'orphaned_mount', parts[1]))
        except FileNotFoundError:
            pass


# ─────────────────────────────────────────────
# CLASS: HallwayForensics — Binary Analysis
# ─────────────────────────────────────────────

class HallwayForensics:
    """
    Deep binary forensics layer.
    Works on raw image files, factory images, BIN files, ELF binaries.
    Feeds FingerprintVector for Alexandria cityscape render.
    """

    BLOCK = 65536  # read block size

    def __init__(self, target: str):
        self.target = target
        self.size   = os.path.getsize(target)

    # ── Partition Geometry ──────────────────

    def parse_gpt(self, fp: FingerprintVector):
        """Parse GPT partition table from raw image"""
        try:
            with open(self.target, 'rb') as f:
                f.seek(512)  # LBA 1
                header = f.read(92)
                if header[0:8] != b'EFI PART':
                    fp.partition_table = 'NOT_GPT'
                    self._try_mbr(f, fp)
                    return
                fp.partition_table = 'GPT'
                num_parts  = struct.unpack_from('<I', header, 80)[0]
                entry_size = struct.unpack_from('<I', header, 84)[0]
                f.seek(1024)  # LBA 2
                prev_end = 0
                for i in range(num_parts):
                    data = f.read(entry_size)
                    if data[16:32] == b'\x00' * 16:
                        continue
                    start = struct.unpack_from('<Q', data, 32)[0]
                    end   = struct.unpack_from('<Q', data, 40)[0]
                    name  = data[56:128].decode('utf-16-le', errors='replace').rstrip('\x00')
                    type_guid = data[0:16].hex()
                    size_bytes = (end - start + 1) * 512
                    gap = (start - prev_end) * 512 if prev_end else 0
                    pe = PartitionEntry(i, type_guid, name, start, end, size_bytes, gap)
                    fp.partitions.append(pe)
                    fp.edges.append(('image', 'has_partition', name))
                    if gap > 0:
                        fp.gaps.append((prev_end * 512, gap))
                        fp.edges.append((name, 'preceded_by_gap', str(gap)))
                    prev_end = end + 1
        except Exception as e:
            fp.partition_table = f'PARSE_ERROR: {e}'

    def _try_mbr(self, f, fp: FingerprintVector):
        f.seek(446)
        for i in range(4):
            entry = f.read(16)
            ptype = entry[4]
            if ptype == 0:
                continue
            start = struct.unpack_from('<I', entry, 8)[0]
            size  = struct.unpack_from('<I', entry, 12)[0]
            fp.partitions.append(
                PartitionEntry(i, hex(ptype), f'MBR_p{i}', start,
                               start+size-1, size*512, 0))
            fp.partition_table = 'MBR'

    # ── Magic Byte Survey ───────────────────

    def magic_survey(self, fp: FingerprintVector):
        """
        Walk every block scanning for known magic bytes.
        Maps what lives in the raw image including unallocated space.
        """
        print(f"[FORENSICS] Magic survey on {self.size // 1024 // 1024}MB image...")
        sqlite_magic = b'SQLite format 3\x00'

        with open(self.target, 'rb') as f:
            offset = 0
            while True:
                block = f.read(self.BLOCK)
                if not block:
                    break
                for magic_bytes, label in MAGIC_TABLE:
                    idx = 0
                    while True:
                        pos = block.find(magic_bytes, idx)
                        if pos == -1:
                            break
                        abs_offset = offset + pos
                        # grab surrounding context strings
                        ctx_start = max(0, pos - 32)
                        ctx = block[ctx_start:pos+64]
                        ctx_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in ctx)
                        hit = MagicHit(abs_offset, label,
                                       magic_bytes.hex(), ctx_str.strip())
                        fp.magic_hits.append(hit)
                        fp.edges.append(('image', f'contains_{label.replace(" ","_")}',
                                         hex(abs_offset)))
                        if magic_bytes == sqlite_magic:
                            fp.sqlite_offsets.append(abs_offset)
                        idx = pos + 1
                offset += len(block)

    # ── ELF String Extraction ───────────────

    def extract_elf_strings(self, fp: FingerprintVector, elf_path: Optional[str] = None):
        """
        Extract strings from ELF .rodata and .data sections.
        This is where fastboot OEM command tables live.
        Uses readelf if available, falls back to raw string scan.
        """
        target = elf_path or self.target
        print(f"[FORENSICS] ELF string extraction: {os.path.basename(target)}")

        # Try readelf for section-aware extraction
        try:
            for section in ELF_SECTIONS_OF_INTEREST:
                result = subprocess.run(
                    ['readelf', '-p', section, target],
                    capture_output=True, text=True, timeout=30
                )
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if line.startswith('[') and ']' in line:
                        parts = line.split(']', 1)
                        if len(parts) == 2:
                            try:
                                offset = int(parts[0].lstrip('[').strip(), 16)
                            except ValueError:
                                offset = 0
                            val = parts[1].strip()
                            if val:
                                fp.string_hits.append(
                                    StringHit(offset, len(val), val, section))
                                self._check_fastboot(val, fp)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # readelf not available — raw strings scan
            self._raw_strings(target, fp)

    def _raw_strings(self, path: str, fp: FingerprintVector):
        """Fallback: extract printable strings >= 6 chars from raw binary"""
        try:
            result = subprocess.run(
                ['strings', '-n', '6', '-t', 'x', path],
                capture_output=True, text=True, timeout=60
            )
            for line in result.stdout.splitlines():
                parts = line.strip().split(None, 1)
                if len(parts) == 2:
                    try:
                        offset = int(parts[0], 16)
                    except ValueError:
                        offset = 0
                    val = parts[1]
                    fp.string_hits.append(StringHit(offset, len(val), val, 'raw'))
                    self._check_fastboot(val, fp)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    def _check_fastboot(self, s: str, fp: FingerprintVector):
        """Flag strings that look like fastboot OEM command entries"""
        sl = s.lower()
        for marker in [b'oem ', b'getvar', b'erase', b'flash', b'reboot-bootloader']:
            if marker.decode() in sl:
                if s not in fp.fastboot_commands:
                    fp.fastboot_commands.append(s)
                    fp.edges.append(('bootloader', 'has_command', s))
                break

    # ── SELinux Policy ──────────────────────

    def extract_selinux_types(self, fp: FingerprintVector):
        """
        If sepolicy binary is found (or present in image), extract type names.
        The type enforcement graph is the AppArmor lattice made visible.
        """
        candidates = []
        # Check mounted/extracted dirs for sepolicy
        for root, _, files in os.walk('/'):
            for fn in files:
                if fn in ('sepolicy', 'precompiled_sepolicy'):
                    candidates.append(os.path.join(root, fn))
            break  # only top level for now, avoid full scan

        for policy_path in candidates:
            try:
                result = subprocess.run(
                    ['seinfo', '--type', policy_path],
                    capture_output=True, text=True, timeout=30
                )
                types = [l.strip() for l in result.stdout.splitlines()
                         if l.strip() and not l.startswith('Types:')]
                fp.selinux_types.extend(types)
                for t in types:
                    fp.edges.append(('selinux', 'enforces_type', t))
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

    # ── Deleted File Estimation ─────────────

    def estimate_tombstones(self, fp: FingerprintVector, mount_point: str):
        """
        Estimate deleted file count from ext4 journal / inode table.
        These are the ghost rooms in the hallway.
        """
        try:
            result = subprocess.run(
                ['debugfs', '-R', 'icheck 0', mount_point],
                capture_output=True, text=True, timeout=30
            )
            # Rough count — deleted inodes show as 'deleted inode' in debugfs output
            count = result.stdout.count('deleted')
            fp.inode_tombstones = count
            fp.edges.append(('filesystem', 'has_deleted_inodes', str(count)))
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    # ── Hidden Variable FS Detection ────────

    def hidden_variable_survey(self, fp: FingerprintVector):
        """
        The 'hidden variable' filesystems — kernel virtual fs types that are
        non-block but carry real state: proc, sysfs, bpf, tracefs, etc.
        These are the infrastructure layer beneath userspace.
        Cross-reference: which are supported but not declared in fstab?
        """
        HIDDEN_FS = {
            'proc':       'Process and kernel state',
            'sysfs':      'Device and driver topology',
            'bpf':        'BPF program and map filesystem',
            'tracefs':    'Kernel trace event filesystem',
            'debugfs':    'Kernel debug interface',
            'securityfs': 'Security module interface',
            'devtmpfs':   'Device node filesystem — hardware topology',
            'efivarfs':   'EFI variable storage',
            'pstore':     'Persistent kernel panic/oops storage',
            'hugetlbfs':  'Huge page memory allocation',
            'binfmt_misc':'Binary format registration',
            'cpuset':     'CPU and memory control groups',
            'cgroup':     'Control group v1',
            'cgroup2':    'Control group v2 unified',
        }
        declared = {e.fs_type for e in fp.fstab_entries}
        mounted  = {m.fs_type for m in fp.mounted_fs}

        for fstype, description in HIDDEN_FS.items():
            status = []
            if fstype in mounted:   status.append('MOUNTED')
            if fstype in declared:  status.append('DECLARED')
            if not status:          status.append('GHOST')   # kernel supports, nothing declared
            fp.edges.append((fstype, 'hidden_var_status', '|'.join(status)))
            print(f"  [{' '.join(status):20s}] {fstype:15s} — {description}")


# ─────────────────────────────────────────────
# REPORT OUTPUT
# ─────────────────────────────────────────────

def print_report(fp: FingerprintVector):
    sep = '─' * 60
    print(f"\n{sep}")
    print(f"  WALKHALLWAY FORENSIC REPORT")
    print(f"  Target : {fp.source_file}")
    print(f"  Size   : {fp.file_size:,} bytes")
    print(f"  Part.  : {fp.partition_table}")
    print(sep)

    if fp.partitions:
        print(f"\n  PARTITIONS ({len(fp.partitions)})")
        for p in fp.partitions:
            print(f"    [{p.index}] {p.name:20s} {p.size_bytes//1024:>8}KB  "
                  f"gap_before={p.gap_before//1024}KB")

    if fp.gaps:
        print(f"\n  UNALLOCATED GAPS — Negative Space ({len(fp.gaps)})")
        for offset, size in fp.gaps:
            print(f"    offset={hex(offset)}  size={size//1024}KB")

    if fp.fstab_orphans:
        print(f"\n  FSTAB ORPHANS — Declared but NOT mounted ({len(fp.fstab_orphans)})")
        for e in fp.fstab_orphans:
            print(f"    {e.source:30s} -> {e.mount_point}  [{e.fs_type}]")

    if fp.magic_hits:
        # Deduplicate by label for summary
        by_type: Dict[str, int] = {}
        for h in fp.magic_hits:
            by_type[h.magic] = by_type.get(h.magic, 0) + 1
        print(f"\n  MAGIC BYTE SURVEY ({len(fp.magic_hits)} hits)")
        for label, count in sorted(by_type.items(), key=lambda x: -x[1]):
            print(f"    {count:4d}x  {label}")

    if fp.sqlite_offsets:
        print(f"\n  SQLITE DATABASES in raw image")
        for off in fp.sqlite_offsets:
            print(f"    {hex(off)}")

    if fp.fastboot_commands:
        print(f"\n  FASTBOOT / OEM COMMANDS ({len(fp.fastboot_commands)})")
        for cmd in fp.fastboot_commands[:40]:
            print(f"    {cmd}")

    if fp.selinux_types:
        print(f"\n  SELINUX TYPES: {len(fp.selinux_types)} types extracted")

    if fp.inode_tombstones:
        print(f"\n  DELETED INODES (tombstones): ~{fp.inode_tombstones}")

    print(f"\n  FINGERPRINT GRAPH EDGES: {len(fp.edges)}")
    print(f"  (Feed to Alexandria for cityscape render)")
    print(f"{sep}\n")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='WalkTheHalls — Ptolemy Forensic File Analysis Engine')
    parser.add_argument('target',
        help='Target binary, image file, or block device')
    parser.add_argument('--report', action='store_true',
        help='Print formatted report to console')
    parser.add_argument('--json', action='store_true',
        help='Output FingerprintVector as JSON')
    parser.add_argument('--live', action='store_true',
        help='Include live system mount analysis (/proc/mounts, /etc/fstab)')
    parser.add_argument('--strings-only', action='store_true',
        help='Skip partition/magic scan — only extract strings (fast mode)')
    parser.add_argument('--workdir', default='./Hallway',
        help='Working directory for mount points (default: ./Hallway)')
    args = parser.parse_args()

    if not os.path.exists(args.target):
        print(f"[ERROR] Target not found: {args.target}")
        sys.exit(1)

    target = os.path.abspath(args.target)
    workdir = os.path.abspath(args.workdir)
    os.makedirs(workdir, exist_ok=True)

    fp = FingerprintVector(
        source_file=target,
        file_size=os.path.getsize(target),
        partition_table='UNKNOWN'
    )

    # ── Topology Layer ──
    stroll = HallwayStroll(target, workdir)
    fp.kernel_fs_types = stroll.the_rooms()

    if args.live:
        stroll.live_mounts(fp)
        stroll.fstab_delta(fp)

    stroll.the_hallway(fp)

    # ── Forensics Layer ──
    forensics = HallwayForensics(target)

    if not args.strings_only:
        forensics.parse_gpt(fp)
        forensics.magic_survey(fp)

    forensics.extract_elf_strings(fp)
    forensics.hidden_variable_survey(fp)

    if args.live:
        forensics.extract_selinux_types(fp)

    # ── Output ──
    if args.report or not args.json:
        print_report(fp)

    if args.json:
        import dataclasses
        print(json.dumps(dataclasses.asdict(fp), indent=2, default=str))


if __name__ == '__main__':
    main()
