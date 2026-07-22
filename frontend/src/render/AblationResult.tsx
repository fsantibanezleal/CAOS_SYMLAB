/**
 * What the ablation actually MEASURED, per rung, across the published cases.
 *
 * The Experiments page listed the question each rung answers and then never answered any of them.
 * A table of questions with no results is a research plan, not a result, and the whole point of
 * building the ladder as one-mechanism-per-step was to make each answer attributable.
 *
 * Two earlier versions of this table were wrong in opposite directions, and the shape below is what
 * survives both:
 *
 * 1. **Medians over whatever ran.** The unit-typed rung only runs where units are declared, so its
 *    median was computed over two cases and printed beside a baseline computed over seventeen. The
 *    reader compares the numbers side by side and attributes the difference to the mechanism.
 * 2. **Medians over the fully common set.** No case runs every rung, so the intersection was empty
 *    and the table showed nothing at all. Correct, and useless.
 *
 * So: each rung reports over the cases that actually ran it, the case COUNT is a column rather than
 * a footnote, and the delta against the rung above is computed only over the cases that ran BOTH.
 * That is the one comparison the ladder design licenses, and it is the only number here that
 * compares two rungs directly.
 */
import { useMemo } from 'react';

import type { RunPayload } from '../lib/contract.types';

interface RungRow {
  id: string;
  label: string;
  cases: number;
  checkable: number;
  recovered: number;
  accuracy: number;
  medianR2: number | null;
  medianSeconds: number | null;
  /** Recovered minus the previous rung's recovered, over cases that ran both. Null when none do. */
  pairedDelta: number | null;
  pairedCases: number;
}

function median(values: number[]): number | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 0 ? (sorted[middle - 1] + sorted[middle]) / 2 : sorted[middle];
}

function recoveredIn(run: RunPayload, rungId: string): boolean | null {
  const variant = run.notes.variants.find((v) => v.id === rungId);
  const eq = variant?.score.equivalence;
  if (!eq || (eq.symbolic === null && eq.numerical === null)) return null;
  const verdict = eq.symbolic !== null ? eq.symbolic : eq.numerical;
  // Coerced rather than compared against `true`. Artifacts baked before the exporter stopped
  // writing booleans as 0/1 carry a number here, and `1 === true` is false, which silently turned
  // every recovery in this table into a non-recovery.
  return Boolean(verdict);
}

export function AblationResult({ runs, lang }: { runs: RunPayload[]; lang: 'en' | 'es' }) {
  const es = lang === 'es';

  const rungs = useMemo<RungRow[]>(() => {
    // Rung order is first-seen across the runs, which is the order the ladder defines them in.
    const order: string[] = [];
    runs.forEach((run) =>
      run.notes.variants.forEach((v) => {
        if (!order.includes(v.id)) order.push(v.id);
      }),
    );

    return order.map((rungId, index) => {
      const present = runs.filter((run) => run.notes.variants.some((v) => v.id === rungId));
      const variants = present.map((run) => run.notes.variants.find((v) => v.id === rungId)!);

      const checkableRuns = present.filter((run) => recoveredIn(run, rungId) !== null);
      const recovered = checkableRuns.filter((run) => recoveredIn(run, rungId) === true).length;

      let pairedDelta: number | null = null;
      let pairedCases = 0;
      if (index > 0) {
        const previousId = order[index - 1];
        const shared = runs.filter(
          (run) => recoveredIn(run, rungId) !== null && recoveredIn(run, previousId) !== null,
        );
        pairedCases = shared.length;
        if (shared.length > 0) {
          const here = shared.filter((run) => recoveredIn(run, rungId) === true).length;
          const before = shared.filter((run) => recoveredIn(run, previousId) === true).length;
          pairedDelta = here - before;
        }
      }

      return {
        id: rungId,
        label: es ? variants[0].label_es : variants[0].label_en,
        cases: present.length,
        checkable: checkableRuns.length,
        recovered,
        accuracy: variants.filter((v) => v.score.accuracy_solution).length,
        medianR2: median(
          variants
            .map((v) => v.score.best_test_r2)
            .filter((r): r is number => r !== null && Number.isFinite(r)),
        ),
        medianSeconds: median(variants.map((v) => v.score.seconds)),
        pairedDelta,
        pairedCases,
      };
    });
  }, [runs, es]);

  if (rungs.length === 0) {
    return (
      <p className="sym-empty">
        {es
          ? 'Aun no hay artefactos horneados para resumir la escalera.'
          : 'No baked artifacts yet to summarise the ladder.'}
      </p>
    );
  }

  const baseline = rungs[0];

  return (
    <section className="sym-block">
      <h3>{es ? 'Lo que midio la ablacion' : 'What the ablation measured'}</h3>
      <p className="sym-block-lede">
        {es
          ? 'Cada escalon se resume sobre los casos que realmente lo ejecutaron, y ese conteo es una columna y no una nota al pie: no todos los escalones corren en todos los casos, y una mediana sobre dos casos junto a una sobre diecisiete invita a atribuir al mecanismo una diferencia que es de muestra.'
          : 'Each rung is summarised over the cases that actually ran it, and that count is a column rather than a footnote: not every rung runs on every case, and a median over two cases printed beside a median over seventeen invites the reader to attribute to the mechanism a difference that belongs to the sample.'}
      </p>

      <div className="sym-table-scroll">
        <table className="sym-terms sym-ablation">
          <thead>
            <tr>
              <th scope="col">{es ? 'escalon' : 'rung'}</th>
              <th scope="col">{es ? 'casos' : 'cases'}</th>
              <th scope="col">{es ? 'recuperadas' : 'recovered'}</th>
              <th scope="col">{es ? 'vs anterior' : 'vs previous'}</th>
              <th scope="col">{es ? 'sobre el umbral' : 'above threshold'}</th>
              <th scope="col">{es ? 'R2 mediano' : 'median R2'}</th>
              <th scope="col">{es ? 'seg. medianos' : 'median seconds'}</th>
              <th scope="col">{es ? 'coste vs base' : 'cost vs baseline'}</th>
            </tr>
          </thead>
          <tbody>
            {rungs.map((rung) => {
              const costRatio =
                baseline.medianSeconds && rung.medianSeconds
                  ? rung.medianSeconds / baseline.medianSeconds
                  : null;
              return (
                <tr key={rung.id}>
                  <th scope="row">{rung.label}</th>
                  <td>{rung.cases}</td>
                  <td>
                    <strong>
                      {rung.checkable === 0 ? 'n/a' : `${rung.recovered} / ${rung.checkable}`}
                    </strong>
                  </td>
                  <td>
                    {rung.pairedDelta === null ? (
                      <span className="sym-hint">{es ? 'sin par' : 'no pair'}</span>
                    ) : (
                      <>
                        <span
                          className={`sym-delta${
                            rung.pairedDelta > 0
                              ? ' is-up'
                              : rung.pairedDelta < 0
                                ? ' is-down'
                                : ''
                          }`}
                        >
                          {rung.pairedDelta > 0 ? `+${rung.pairedDelta}` : rung.pairedDelta}
                        </span>{' '}
                        <span className="sym-hint">
                          {es ? `en ${rung.pairedCases}` : `on ${rung.pairedCases}`}
                        </span>
                      </>
                    )}
                  </td>
                  <td>
                    {rung.accuracy} / {rung.cases}
                  </td>
                  <td>{rung.medianR2 === null ? 'n/a' : rung.medianR2.toFixed(4)}</td>
                  <td>{rung.medianSeconds === null ? 'n/a' : rung.medianSeconds.toFixed(1)}</td>
                  <td>
                    {costRatio === null
                      ? 'n/a'
                      : costRatio < 1.05 && costRatio > 0.95
                        ? '1x'
                        : `${costRatio.toFixed(1)}x`}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="sym-note">
        {es
          ? 'La columna "vs anterior" es la unica comparacion directa entre dos escalones aqui, y se calcula SOLO sobre los casos que ejecutaron ambos, porque los vecinos difieren en exactamente un mecanismo. Las demas columnas describen cada escalon sobre su propio conjunto.'
          : 'The "vs previous" column is the only direct comparison between two rungs on this page, and it is computed ONLY over the cases that ran both, because neighbours differ by exactly one mechanism. Every other column describes a rung over its own set.'}
      </p>
      <p className="sym-note">
        {es
          ? 'Las recuperaciones se cuentan SOLO sobre las configuraciones donde la recuperacion es comprobable. Dividir por el total incluiria en silencio problemas sin ley publicada que recuperar, que es exactamente la aritmetica que este laboratorio rechaza en todas partes.'
          : 'Recoveries are counted ONLY over the configurations where recovery is checkable. Dividing by the full count would silently include problems with no published law to recover, which is exactly the arithmetic this lab refuses everywhere else.'}
      </p>
      <p className="sym-note">
        {es
          ? 'El coste es tiempo mediano relativo al escalon base, y tambien sobre conjuntos distintos. Un escalon que compra calidad a un multiplo grande del reloj no ha ganado de forma obvia: la literatura de benchmarks nombra la injusticia de presupuesto como un problema abierto.'
          : 'Cost is median wall clock relative to the baseline rung, and also over differing sets. A rung that buys quality at a large multiple of the clock has not obviously won: the benchmark literature names budget unfairness as a standing problem.'}
      </p>
    </section>
  );
}
