/**
 * The recovery verdict, decided in ONE place.
 *
 * "Did the search recover the law" is the single most important claim this lab makes, and it was
 * being decided independently in four components (ExpressionPanel, Benchmark, AblationResult, and
 * the App readout), each writing the same rule `symbolic ?? numerical` by hand. That is the
 * arrangement this product refuses everywhere else: term colours are assigned once in Python so the
 * equation, the tree and the contribution chart cannot disagree. A verdict written four times is a
 * verdict that drifts three times.
 *
 * The pipeline now exports `equivalence.recovered`, so the rule lives in the artifact. These
 * helpers prefer it and fall back to the derivation for artifacts baked before it shipped, and
 * `tests/test_recovery_verdict_is_one_rule.py` asserts the two agree on every variant of every case.
 */
import type { VariantScore } from './contract.types';

type Equivalence = NonNullable<VariantScore['equivalence']>;

/** Is a variant's recovery even decidable? False for a case with no published law, or where both
 *  tests declined. Recovery rates are counted over this set, never over all variants. */
export function isCheckable(equivalence: Equivalence | null | undefined): boolean {
  if (!equivalence) return false;
  return equivalence.symbolic !== null || equivalence.numerical !== null;
}

/** The recovery verdict: the exported field where present, otherwise the lab's rule (the symbolic
 *  test where it decided, the numerical one where it did not). Null when not checkable. */
export function isRecovered(equivalence: Equivalence | null | undefined): boolean | null {
  if (!isCheckable(equivalence)) return null;
  const eq = equivalence as Equivalence;
  if (eq.recovered !== undefined) return eq.recovered;
  return eq.symbolic !== null ? eq.symbolic : Boolean(eq.numerical);
}
