#!/usr/bin/python3
"""
HyperWebster - Infinite Permutation Indexer
============================================
Maps any string to a unique coordinate in the infinite permutation of a
fixed character set, and back again.

Address format: 256-bit value encoded as a 64-character hex string.
Index record:   (address_hex: str, length: int, timestamp: str)
"""

import time
import sys


class HyperWebster:
    """
    Bijective base-N encoding over an ordered character set.

    Every finite string over `self.characters` has a unique non-negative
    integer coordinate (address).  Address 0 maps to the first character,
    addresses increase lexicographically.

    The 256-bit address is simply the integer address zero-padded to 64
    hex digits.  Strings whose address exceeds 2^256 - 1 are still handled
    correctly; the hex representation will just be wider than 64 chars.
    """

    # ---------------------------------------------------------------------------
    # Keyboard-order character universe (same as your original)
    # ---------------------------------------------------------------------------
    _DEFAULT_CHARS = (
        r"""`1234567890-="""
        "\t"
        r"""qwertyuiop[]\asdfghjkl;'"""
        "\n"
        r"""zxcvbnm,./ ~!@#$%^&*()_+QWERTYUIOP{}|ASDFGHJKL:"ZXCVBNM<>?"""
    )

    def __init__(self, characters: str = _DEFAULT_CHARS):
        self.characters = characters
        self.char_list  = list(self.characters)
        self.N          = len(self.char_list)

        # O(1) char → index lookup (beats list.index() for long texts)
        self._char_index: dict[str, int] = {
            ch: i for i, ch in enumerate(self.char_list)
        }

        # Allow Python to stringify arbitrarily large integers
        sys.set_int_max_str_digits(0)

    # ------------------------------------------------------------------
    # Core math: string ↔ integer  (bijective base-N)
    # ------------------------------------------------------------------

    def point_to_text(self, text: str) -> int:
        """
        INDEXING  —  string → unique non-negative integer address.

        Uses bijective base-N (no zero digit), so every string including
        those starting with the first character get a distinct address.
        """
        address = 0
        for i, ch in enumerate(reversed(text)):
            try:
                index = self._char_index[ch] + 1          # 1-based
            except KeyError:
                raise ValueError(
                    f"Character {ch!r} is not in the character set."
                )
            address += index * (self.N ** i)
        return address - 1                                 # 0-based coordinate

    def regenerate_text(self, address: int) -> str:
        """
        REGENERATION  —  non-negative integer address → string.
        """
        if address < 0:
            raise ValueError("Address must be a non-negative integer.")

        res     = []
        address += 1                                       # shift for bijective logic

        while address > 0:
            address, rem = divmod(address - 1, self.N)
            res.append(self.char_list[rem])

        return "".join(reversed(res))

    # ------------------------------------------------------------------
    # 256-bit hex address helpers
    # ------------------------------------------------------------------

    @staticmethod
    def int_to_hex256(n: int) -> str:
        """
        Encode a non-negative integer as a 256-bit hex string (64 chars).
        Strings whose address > 2^256-1 produce a wider hex string — still
        valid, just not strictly 256-bit.
        """
        if n < 0:
            raise ValueError("Address must be non-negative.")
        hex_str = format(n, "x")                           # no '0x' prefix
        # zero-pad to at least 64 hex digits (= 256 bits)
        return hex_str.zfill(64)

    @staticmethod
    def hex256_to_int(hex_str: str) -> int:
        """Decode a hex address string back to an integer."""
        return int(hex_str, 16)

    # ------------------------------------------------------------------
    # Public API: index and regenerate
    # ------------------------------------------------------------------

    def index_text(self, text: str) -> tuple[str, int, str]:
        """
        Index a block of text.

        Returns
        -------
        (address_hex, length, timestamp)
            address_hex : 64-char (256-bit) hex string locating `text`
                          in the infinite permutation.
            length      : number of characters in `text`.
            timestamp   : time.ctime() at the moment of indexing.
        """
        integer_address = self.point_to_text(text)
        address_hex     = self.int_to_hex256(integer_address)
        length          = len(text)
        timestamp       = time.ctime()
        return (address_hex, length, timestamp)

    def regenerate_from_address(self, address_hex: str, length: int) -> str:
        """
        Regenerate text from a hex address and length.

        Parameters
        ----------
        address_hex : hex string produced by `index_text`.
        length      : number of characters to return (the second element
                      of the index tuple).

        Returns
        -------
        The original string.

        Notes
        -----
        The bijective encoding gives each *complete* string a unique address,
        so `length` is used only to verify the result matches expectations —
        the full string is recovered from `address_hex` alone.
        """
        integer_address = self.hex256_to_int(address_hex)
        text            = self.regenerate_text(integer_address)

        if len(text) != length:
            raise ValueError(
                f"Regenerated text has length {len(text)}, "
                f"but the stored length is {length}.  "
                f"The address or length may be corrupted."
            )
        return text



# ~ text = open(PTOL_ROOT + "/TESTdb-struct.sql").read()
# ~ text_length = len(text)
# ~ print("Length of Data Set", text_length)
# ~ HW = HyperWebster()
# ~ pointer = HW.index_text(text)
# ~ addr_hex, length, ts = pointer
# ~ print("this will be a json file evetually\n", addr_hex, length, ts)
# ---------------------------------------------------------------------------
# Demo / smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    hw = HyperWebster()

    # ~ samples = [
        # ~ "Hello, World!",
        # ~ "python3",
        # ~ "The quick brown fox jumps over the lazy dog.\n",
        # ~ "`~!@#",
    # ~ ]

    # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
    sample = open(PTOL_ROOT + "/TESTdb-struct.sql").read()

    print("=" * 72)
    print(f"{'HyperWebster  —  Infinite Permutation Indexer':^72}")
    print(f"Character-set size: {hw.N} symbols")
    print("=" * 72)

    # ~ for sample in samples:
    record = hw.index_text(sample)
    addr_hex, length, ts = record

        # ~ recovered = hw.regenerate_from_address(addr_hex, length)
        # ~ ok        = "✓" if recovered == sample else "✗ MISMATCH"

    print(f"\nInput    : {sample!r}")
    print(f"Address  : {addr_hex}")
    print("DEBUG", len(addr_hex))
    print(f"Length   : {length}")
    print(f"Timestamp: {ts}")
    # ~ print(f"Recovered: {recovered!r}  [{ok}]")

    print("\n" + "=" * 72)
    # ~ print("All round-trips passed." if all(
        # ~ hw.regenerate_from_address(*hw.index_text(s)[:2]) == s
        # ~ for s in samples
    # ~ ) else "SOME ROUND-TRIPS FAILED.")
