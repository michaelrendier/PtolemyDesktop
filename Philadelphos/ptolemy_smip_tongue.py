"""
==============================================================================
THE TONGUE — SMNNIP Output Filter
==============================================================================
Hydroradiolysis Chromatography Clathrate Layer

Final pre-output filter in the SMNNIP retrieval pipeline:

    Noether (extinction) → Higgs (collapse/focal) → Yang-Mills (RG rotation)
    → Inversion J_N (fixed-point test) → THE TONGUE → Output

The Tongue enforces *which foldings of the algebra elements are valid* as
outputs, given the current gauge field state and algebra stratum.

ANALOGY: Protein folding clathrate cages — the cage (Fano structure) does not
block the molecule; it limits which conformations are reachable. Non-reachable
conformations are extinct. The first valid folding that closes is the output.

ALGEBRA GROUNDING:
  At ℝ:  trivial — all orderings equivalent (commutative + associative)
  At ℂ:  trivial — still commutative
  At ℍ:  non-commutative — ordering matters, two distinct folding classes
  At 𝕆:  non-commutative AND non-associative — Fano plane governs
          which triples (e_i, e_j, e_k) close under multiplication.
          (e_i · e_j) · e_k ≠ e_i · (e_j · e_k) in general.
          Only Fano-line triples produce consistent closure.

THE TONGUE tests each surviving focal-point candidate:
  1. Enumerate all possible folding orderings for the element's basis sequence.
  2. For each ordering: check Fano validity (𝕆 stratum) or algebra rules.
  3. Score valid orderings by Noether conservation + gauge consistency.
  4. Extinct: orderings that violate Fano lines or produce zero divisors (𝕊 layer).
  5. Output: lowest-score valid folding (first closure), or NONE.

Author: O Captain My Captain + Claude (Anthropic)
Date:   April 2026
==============================================================================
"""

import math
import itertools
from typing import List, Tuple, Optional, Dict, Any


# ==============================================================================
# SECTION 0: FANO PLANE STRUCTURE
# ==============================================================================

# The 7 lines of the Fano plane (octonion basis indices 1..7)
# Each line (i,j,k): e_i * e_j = +e_k  (cyclic), -e_k (anticyclic)
FANO_LINES: List[Tuple[int,int,int]] = [
    (1, 2, 4),
    (2, 3, 5),
    (3, 4, 6),
    (4, 5, 7),
    (5, 6, 1),
    (6, 7, 2),
    (7, 1, 3),
]

# Build lookup: (i,j) -> (k, sign) for e_i * e_j
def _build_fano_table() -> Dict[Tuple[int,int], Tuple[int,int]]:
    table = {}
    # e_0 = identity
    for i in range(8):
        table[(0, i)] = (i, +1)
        table[(i, 0)] = (i, +1)
    # e_i * e_i = -1 (represented as (0, -1) → scalar -1)
    for i in range(1, 8):
        table[(i, i)] = (0, -1)
    # Fano lines: cyclic = +, anticyclic = -
    for (a, b, c) in FANO_LINES:
        table[(a, b)] = (c, +1)
        table[(b, c)] = (a, +1)
        table[(a, c)] = (b, -1)   # anticyclic: e_a * e_c = -e_b
        table[(b, a)] = (c, -1)
        table[(c, b)] = (a, -1)
        table[(c, a)] = (b, +1)
    return table

FANO_TABLE = _build_fano_table()


def oct_multiply(i: int, j: int) -> Tuple[int, int]:
    """
    Multiply octonion basis elements e_i * e_j.
    Returns (result_index, sign): sign * e_{result_index}
    """
    return FANO_TABLE.get((i, j), (0, 0))


def is_fano_valid_triple(i: int, j: int, k: int) -> bool:
    """
    Is (e_i * e_j) * e_k consistent with Fano structure?
    Checks that intermediate product lands on a Fano line or identity.
    Non-associativity means (e_i * e_j) * e_k ≠ e_i * (e_j * e_k) in general.
    This returns True if the LEFT-associative folding is Fano-consistent.
    """
    mid_idx, mid_sign = oct_multiply(i, j)
    if mid_sign == 0:
        return False  # zero divisor — extinct
    final_idx, final_sign = oct_multiply(mid_idx, j if mid_idx == 0 else mid_idx)
    # Actually test the full triple closure
    final_idx, final_sign = oct_multiply(mid_idx, k)
    return final_sign != 0


def fano_line_for(i: int, j: int) -> Optional[Tuple[int,int,int]]:
    """Return the Fano line containing both i and j (if any)."""
    for line in FANO_LINES:
        if i in line and j in line:
            return line
    return None


# ==============================================================================
# SECTION 1: FOLDING ENUMERATOR
# ==============================================================================

class FoldingEnumerator:
    """
    Given a sequence of basis element indices [e_i0, e_i1, ..., e_in],
    enumerate all valid parenthesizations (Catalan tree structures).

    For n elements, there are C(n-1) = Catalan(n-1) parenthesizations.
    The Tongue tests ALL of them and keeps only Fano-valid ones.
    """

    def __init__(self, algebra: int):
        """
        algebra: 0=ℝ, 1=ℂ, 2=ℍ, 3=𝕆, -1=𝕊
        """
        self.algebra = algebra

    def all_parenthesizations(self, seq: List[int]) -> List[List]:
        """
        Return all Catalan tree parenthesizations of seq.
        Each result is a nested list representing left/right splits.
        """
        n = len(seq)
        if n == 1:
            return [seq[0]]
        if n == 2:
            return [(seq[0], seq[1])]
        results = []
        for split in range(1, n):
            for left in self._paren_list(seq[:split]):
                for right in self._paren_list(seq[split:]):
                    results.append((left, right))
        return results

    def _paren_list(self, seq: List[int]) -> List:
        n = len(seq)
        if n == 1:
            return [seq[0]]
        if n == 2:
            return [(seq[0], seq[1])]
        results = []
        for split in range(1, n):
            for left in self._paren_list(seq[:split]):
                for right in self._paren_list(seq[split:]):
                    results.append((left, right))
        return results

    def evaluate_tree(self, tree) -> Tuple[Optional[int], int]:
        """
        Evaluate a parenthesization tree.
        Returns (basis_index, sign) or (None, 0) if extinct (zero divisor).
        """
        if isinstance(tree, int):
            return (tree, +1)

        left_tree, right_tree = tree
        left_idx, left_sign = self.evaluate_tree(left_tree)
        right_idx, right_sign = self.evaluate_tree(right_tree)

        if left_sign == 0 or right_sign == 0:
            return (None, 0)  # propagate extinction

        if self.algebra <= 1:
            # ℝ, ℂ: commutative + associative, use complex multiply
            # treat indices as: 0=real, 1=i
            if left_idx == 0:
                return (right_idx, left_sign * right_sign)
            if right_idx == 0:
                return (left_idx, left_sign * right_sign)
            # i*i = -1
            if self.algebra == 1 and left_idx == 1 and right_idx == 1:
                return (0, -left_sign * right_sign)
            return (left_idx, left_sign * right_sign)

        elif self.algebra == 2:
            # ℍ: quaternion multiplication (non-commutative, associative)
            return self._quat_mul(left_idx, left_sign, right_idx, right_sign)

        elif self.algebra == 3:
            # 𝕆: octonion — Fano table
            result_idx, result_sign = oct_multiply(left_idx, right_idx)
            if result_sign == 0:
                return (None, 0)
            return (result_idx, left_sign * right_sign * result_sign)

        elif self.algebra == -1:
            # 𝕊: sedenion — may have zero divisors
            # Simplified: flag potential zero divisors
            result_idx, result_sign = oct_multiply(
                left_idx % 8, right_idx % 8
            )
            if left_idx >= 8 and right_idx >= 8:
                return (None, 0)  # potential zero divisor — extinct
            return (result_idx, left_sign * right_sign * result_sign)

        return (None, 0)

    def _quat_mul(self, i: int, si: int, j: int, sj: int) -> Tuple[Optional[int], int]:
        """Quaternion basis multiplication table."""
        QUAT = {
            (0,0):(0,+1),(0,1):(1,+1),(0,2):(2,+1),(0,3):(3,+1),
            (1,0):(1,+1),(1,1):(0,-1),(1,2):(3,+1),(1,3):(2,-1),
            (2,0):(2,+1),(2,1):(3,-1),(2,2):(0,-1),(2,3):(1,+1),
            (3,0):(3,+1),(3,1):(2,+1),(3,2):(1,-1),(3,3):(0,-1),
        }
        k, sk = QUAT.get((i % 4, j % 4), (0, 0))
        if sk == 0:
            return (None, 0)
        return (k, si * sj * sk)

    def valid_foldings(self, seq: List[int]) -> List[Dict[str, Any]]:
        """
        Return all valid (non-extinct) foldings of seq under current algebra.
        Each result: {'tree': ..., 'result_idx': int, 'sign': int, 'n_steps': int}
        """
        if len(seq) == 0:
            return []
        if len(seq) == 1:
            return [{'tree': seq[0], 'result_idx': seq[0], 'sign': +1,
                     'n_steps': 0, 'extinct': False}]

        trees = self._paren_list(seq)
        results = []
        for tree in trees:
            idx, sign = self.evaluate_tree(tree)
            extinct = (sign == 0 or idx is None)
            if not extinct:
                results.append({
                    'tree': tree,
                    'result_idx': idx,
                    'sign': sign,
                    'n_steps': len(seq) - 1,
                    'extinct': False,
                })
        return results


# ==============================================================================
# SECTION 2: NOETHER SCORER
# ==============================================================================

class NoetherScorer:
    """
    Score a folding by its Noether conservation quality.
    Lower score = better conserved = preferred output.

    Conservation proxy: for a folding f producing element e_k,
    the score is the Noether violation |∂_μJ^μ| estimated as:
      - 0.0 if result is on a Fano line (𝕆)
      - ε if result is identity e_0 (over-collapsed — penalized)
      - increases with non-Fano distance
    """

    def __init__(self, algebra: int):
        self.algebra = algebra

    def score(self, folding: Dict[str, Any], focal_r: float) -> float:
        if folding['extinct']:
            return float('inf')

        idx = folding['result_idx']
        sign = folding['sign']
        score = 0.0

        # Penalize collapse to identity (over-reduction)
        if idx == 0:
            score += 1.0

        # At 𝕆: penalize if result index is not reachable from focal_r
        if self.algebra == 3:
            # Preferred outputs: indices on Fano lines
            fano_indices = set()
            for line in FANO_LINES:
                fano_indices.update(line)
            if idx not in fano_indices and idx != 0:
                score += 0.5

        # Penalize negative sign (represents anticyclic — higher energy)
        if sign < 0:
            score += 0.2

        # Reward closeness to φ fixed point in r-space
        phi = (1.0 + math.sqrt(5.0)) / 2.0
        r_proxy = phi if idx == 1 else (1.0 / phi if idx == 2 else float(idx))
        score += abs(r_proxy - focal_r) * 0.1

        return score


# ==============================================================================
# SECTION 3: THE TONGUE
# ==============================================================================

class TheTongue:
    """
    Final pre-output filter in the SMNNIP pipeline.

    Input:
        candidates  — list of surviving focal points from J_N layer
                      each: {'r': float, 'theta': float, 'basis_seq': List[int]}
        algebra     — current stratum (0=ℝ, 1=ℂ, 2=ℍ, 3=𝕆, -1=𝕊)
        gauge_state — dict with current gauge field parameters (optional)

    Process:
        For each candidate:
          1. Enumerate all valid foldings of its basis_seq
          2. Score each folding (Noether conservation + gauge consistency)
          3. Extinct: zero-sign foldings (violate Fano / produce zero divisors)
          4. Keep lowest-score valid folding per candidate

        Across all candidates:
          5. If only one candidate survives: direct output
          6. If multiple: apply cross-candidate Fano consistency check
             (can two outputs coexist on the same Fano line? → keep both)
             (off-line: discard lower-score one)
          7. If none survive: OUTPUT = NONE (extinction cascade)

    Output:
        TongueResult with the validated, scored output element(s)
    """

    ALGEBRA_NAMES = {0: 'ℝ', 1: 'ℂ', 2: 'ℍ', 3: '𝕆', -1: '𝕊 [Master Key]'}

    def __init__(self, algebra: int = 3):
        self.algebra = algebra
        self.enumerator = FoldingEnumerator(algebra)
        self.scorer = NoetherScorer(algebra)
        self._log: List[str] = []

    def _log_line(self, s: str):
        self._log.append(s)

    def filter(self, candidates: List[Dict[str, Any]]) -> 'TongueResult':
        """
        Main entry point. Run the full Tongue filter on candidates.
        """
        self._log = []
        alg_name = self.ALGEBRA_NAMES.get(self.algebra, '?')
        self._log_line(f"THE TONGUE  [{alg_name} stratum]")
        self._log_line("═" * 54)
        self._log_line(f"  Candidates in:  {len(candidates)}")

        if not candidates:
            self._log_line("  No candidates — extinction cascade.")
            return TongueResult(outputs=[], extinct_count=0,
                                log=self._log, algebra=self.algebra)

        scored_outputs = []
        total_extinct = 0

        for i, cand in enumerate(candidates):
            r = cand.get('r', 1.0)
            basis_seq = cand.get('basis_seq', [1])
            self._log_line(f"\n  Candidate {i+1}: r={r:.6f}  seq={basis_seq}")

            # Enumerate valid foldings
            valid = self.enumerator.valid_foldings(basis_seq)
            n_total = max(1, self._catalan(len(basis_seq) - 1))
            n_extinct = n_total - len(valid)
            total_extinct += n_extinct

            self._log_line(f"    Parenthesizations: {n_total}  "
                           f"valid={len(valid)}  extinct={n_extinct}")

            if not valid:
                self._log_line(f"    ALL FOLDINGS EXTINCT — candidate eliminated.")
                continue

            # Score each valid folding
            scored = []
            for f in valid:
                s = self.scorer.score(f, r)
                scored.append((s, f))
                self._log_line(
                    f"    folding → e_{f['result_idx']} "
                    f"(sign={'+' if f['sign']>0 else '-'})  "
                    f"score={s:.4f}"
                )

            # Keep minimum-score folding for this candidate
            scored.sort(key=lambda x: x[0])
            best_score, best_folding = scored[0]
            scored_outputs.append({
                'candidate': cand,
                'folding': best_folding,
                'score': best_score,
                'r': r,
                'result_idx': best_folding['result_idx'],
                'sign': best_folding['sign'],
            })
            self._log_line(
                f"    SELECTED: e_{best_folding['result_idx']}  "
                f"score={best_score:.4f}"
            )

        self._log_line(f"\n  After folding filter: {len(scored_outputs)} surviving")

        # Cross-candidate Fano consistency (𝕆 stratum only)
        if self.algebra == 3 and len(scored_outputs) > 1:
            scored_outputs = self._cross_fano_filter(scored_outputs)

        # Final sort and output
        scored_outputs.sort(key=lambda x: x['score'])

        self._log_line(f"\n  Final outputs: {len(scored_outputs)}")
        for out in scored_outputs:
            self._log_line(
                f"    e_{out['result_idx']}  r={out['r']:.6f}  "
                f"score={out['score']:.4f}"
            )

        if not scored_outputs:
            self._log_line("\n  TONGUE OUTPUT: NONE — full extinction cascade.")
        else:
            self._log_line(
                f"\n  TONGUE OUTPUT: e_{scored_outputs[0]['result_idx']}  "
                f"(sign={'+'if scored_outputs[0]['sign']>0 else '-'})"
            )

        return TongueResult(
            outputs=scored_outputs,
            extinct_count=total_extinct,
            log=self._log,
            algebra=self.algebra,
        )

    def _cross_fano_filter(self, outputs: List[Dict]) -> List[Dict]:
        """
        Check if multiple surviving outputs are mutually Fano-consistent.
        Two outputs e_i and e_j can coexist if they share a Fano line.
        If not, keep only the lower-score one.
        """
        self._log_line("\n  Cross-Fano consistency check (𝕆 stratum):")
        if len(outputs) < 2:
            return outputs

        keep = [outputs[0]]
        for candidate in outputs[1:]:
            can_coexist = False
            for existing in keep:
                i = existing['result_idx']
                j = candidate['result_idx']
                if i == j:
                    can_coexist = True
                    break
                line = fano_line_for(i, j)
                if line is not None:
                    self._log_line(
                        f"    e_{i} and e_{j} share Fano line {line} — coexist ✓"
                    )
                    can_coexist = True
                    break
            if can_coexist:
                keep.append(candidate)
            else:
                self._log_line(
                    f"    e_{candidate['result_idx']} off Fano line from "
                    f"existing outputs — EXTINCT"
                )
        return keep

    @staticmethod
    def _catalan(n: int) -> int:
        """nth Catalan number."""
        if n <= 0:
            return 1
        result = 1
        for i in range(n + 1, 2 * n + 1):
            result *= i
        for i in range(1, n + 1):
            result //= i
        result //= (n + 1)
        return result


# ==============================================================================
# SECTION 4: RESULT DATACLASS
# ==============================================================================

class TongueResult:
    def __init__(self, outputs: List[Dict], extinct_count: int,
                 log: List[str], algebra: int):
        self.outputs = outputs
        self.extinct_count = extinct_count
        self.log = log
        self.algebra = algebra
        self.has_output = len(outputs) > 0
        self.primary = outputs[0] if outputs else None

    def print_log(self):
        for line in self.log:
            print(line)

    def summary(self) -> str:
        if not self.has_output:
            return "TONGUE: EXTINCT (no valid output)"
        p = self.primary
        alg = {0:'ℝ',1:'ℂ',2:'ℍ',3:'𝕆',-1:'𝕊'}.get(self.algebra,'?')
        sign_str = '+' if p['sign'] > 0 else '-'
        return (f"TONGUE OUTPUT [{alg}]: "
                f"{sign_str}e_{p['result_idx']}  "
                f"score={p['score']:.4f}  "
                f"r={p['r']:.6f}  "
                f"extinct_foldings={self.extinct_count}")


# ==============================================================================
# SECTION 5: FULL PIPELINE HOOK
# ==============================================================================

def run_tongue_on_inversion_result(
    inversion_fixed_points: List[Dict[str, float]],
    algebra: int = 3,
    verbose: bool = True,
) -> TongueResult:
    """
    Convenience function: takes the output of the J_N inversion layer
    and runs it through The Tongue.

    inversion_fixed_points: list of {'r': float, 'theta': float}
    Each point is assigned a basis_seq based on its r value:
      r ≈ φ       → [1, 2, 4]  (first Fano line, canonical φ sequence)
      r ≈ 1/φ     → [2, 3, 5]  (second Fano line)
      r ≈ 1.0     → [1]        (boundary — single element)
      other       → [int(r*4) % 7 + 1]  (mapped to Fano index)
    """
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    phi_inv = 1.0 / phi

    candidates = []
    for fp in inversion_fixed_points:
        r = fp.get('r', 1.0)
        theta = fp.get('theta', 0.0)

        if abs(r - phi) < 0.01:
            seq = [1, 2, 4]  # e_1·e_2 = e_4 (first Fano line)
        elif abs(r - phi_inv) < 0.01:
            seq = [2, 3, 5]  # e_2·e_3 = e_5
        elif abs(r - 1.0) < 0.01:
            seq = [1]        # boundary — single element, no folding
        else:
            idx = max(1, min(7, int(r * 4) % 7 + 1))
            seq = [idx]

        candidates.append({
            'r': r,
            'theta': theta,
            'basis_seq': seq,
        })

    tongue = TheTongue(algebra=algebra)
    result = tongue.filter(candidates)

    if verbose:
        result.print_log()
        print()
        print(result.summary())

    return result


# ==============================================================================
# SECTION 6: DEMO / SELF-TEST
# ==============================================================================

def _demo():
    print()
    print("=" * 60)
    print("  THE TONGUE — Self-Test")
    print("  Hydroradiolysis Chromatography Clathrate Layer")
    print("=" * 60)

    phi = (1.0 + math.sqrt(5.0)) / 2.0

    # --- Test 1: Single φ focal point (expected: e_4, score low) ---
    print("\n[TEST 1]  Single φ focal point → 𝕆 stratum")
    result1 = run_tongue_on_inversion_result(
        [{'r': phi, 'theta': 0.0}], algebra=3, verbose=True
    )

    # --- Test 2: Two focal points, Fano-consistent (e_1, e_2) ---
    print("\n[TEST 2]  Two focal points — Fano consistency check")
    result2 = run_tongue_on_inversion_result(
        [{'r': phi, 'theta': 0.0},
         {'r': 1.0/phi, 'theta': math.pi/2}],
        algebra=3, verbose=True
    )

    # --- Test 3: ℍ stratum (quaternion — non-commutative only) ---
    print("\n[TEST 3]  ℍ stratum — quaternion folding")
    t3 = TheTongue(algebra=2)
    r3 = t3.filter([
        {'r': phi, 'theta': 0.0, 'basis_seq': [1, 2, 3]},
    ])
    r3.print_log()
    print(r3.summary())

    # --- Test 4: Zero divisor test at 𝕊 (sedenion) ---
    print("\n[TEST 4]  𝕊 stratum — zero divisor extinction")
    t4 = TheTongue(algebra=-1)
    r4 = t4.filter([
        {'r': 1.0, 'theta': 0.0, 'basis_seq': [8, 8]},
    ])
    r4.print_log()
    print(r4.summary())

    # --- Fano table printout ---
    print()
    print("=" * 60)
    print("  FANO TABLE (𝕆 basis multiplication)")
    print("  e_i * e_j = sign * e_k")
    print("=" * 60)
    print(f"  {'':6}", end="")
    for j in range(8):
        print(f"  e_{j}", end="")
    print()
    for i in range(8):
        print(f"  e_{i}  ", end="")
        for j in range(8):
            k, s = oct_multiply(i, j)
            if s == 0:
                print(f"  0  ", end="")
            elif k == 0:
                print(f" {'-' if s<0 else '+'} 1 ", end="")
            else:
                print(f" {'-' if s<0 else '+'}e_{k}", end="")
        print()


if __name__ == "__main__":
    _demo()
