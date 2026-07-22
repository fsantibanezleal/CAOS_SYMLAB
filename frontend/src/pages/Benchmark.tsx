import { Callout, Cite, Refs } from '@fasl-work/caos-app-shell';
import { useEffect, useMemo, useState } from 'react';

import { loadIndex, loadRun } from '../lib/data';
import type { CaseIndex, RunPayload } from '../lib/contract.types';
import { useLang } from '../lib/useLang';
import { groupDigits } from '../lib/format';

/**
 * Benchmark: numbers read from the committed artifacts, never typed into the page.
 *
 * The two headline columns are the accuracy rate and the recovery rate, side by side and never
 * merged. Their gap is the measurement this lab exists to make, and putting them in one table where
 * they can be compared row by row is the point of this page.
 */
export default function Benchmark() {
  const es = useLang() === 'es';
  const [, setIndex] = useState<CaseIndex | null>(null);
  const [runs, setRuns] = useState<RunPayload[]>([]);

  useEffect(() => {
    loadIndex()
      .then((loaded) => {
        setIndex(loaded);
        return Promise.all(loaded.cases.map((entry) => loadRun(entry.case_id).catch(() => null)));
      })
      .then((loaded) => setRuns(loaded.filter((r): r is RunPayload => r !== null)))
      .catch(() => setIndex(null));
  }, []);

  const rows = useMemo(
    () =>
      runs.flatMap((run) =>
        run.notes.variants.map((variant) => ({
          caseId: run.notes.case_id,
          category: run.notes.category,
          label: es ? variant.label_es : variant.label_en,
          score: variant.score,
          member: variant.pareto[variant.selected_index] ?? variant.pareto[0] ?? null,
        })),
      ),
    [runs, es],
  );

  const totals = useMemo(() => {
    if (rows.length === 0) return null;
    const withR2 = rows.filter((r) => r.score.best_test_r2 !== null);

    // Recovery is counted over the configurations where it is CHECKABLE, never over all of them.
    // Dividing recoveries by the full row count would silently include problems that have no
    // published law to recover, which is the exact arithmetic this page exists to refuse.
    const checkable = rows.filter((r) => {
      const eq = r.score.equivalence;
      return eq !== null && (eq.symbolic !== null || eq.numerical !== null);
    });
    const recovered = checkable.filter((r) => {
      const eq = r.score.equivalence!;
      return eq.symbolic !== null ? eq.symbolic : eq.numerical;
    });
    // Accuracy WITHOUT recovery, on the same configurations: the gap, as a count.
    const fitButNotFound = checkable.filter((r) => {
      const eq = r.score.equivalence!;
      const found = eq.symbolic !== null ? eq.symbolic : eq.numerical;
      return r.score.accuracy_solution && !found;
    });

    return {
      variants: rows.length,
      cases: runs.length,
      accuracySolutions: rows.filter((r) => r.score.accuracy_solution).length,
      checkable: checkable.length,
      recovered: recovered.length,
      fitButNotFound: fitButNotFound.length,
      seconds: rows.reduce((sum, r) => sum + r.score.seconds, 0),
      evaluations: rows.reduce((sum, r) => sum + r.score.evaluations, 0),
      medianR2:
        withR2.length > 0
          ? withR2.map((r) => r.score.best_test_r2 as number).sort((a, b) => a - b)[
              Math.floor(withR2.length / 2)
            ]
          : null,
    };
  }, [rows, runs.length]);

  return (
    <div className="page-body prose">
      <div className="page-head">
        <h1>Benchmark</h1>
        <p className="lede">
          {es
            ? 'Numeros leidos de los artefactos versionados, nunca escritos a mano en esta pagina. Las dos columnas principales son la tasa de exactitud y la tasa de recuperacion, lado a lado y jamas fusionadas: la brecha entre ellas es la medicion que justifica este laboratorio.'
            : 'Numbers read from the committed artifacts, never typed into this page. The two headline columns are the accuracy rate and the recovery rate, side by side and never merged: the gap between them is the measurement that justifies this lab.'}
        </p>
      </div>

      <section>
        <h2>{es ? 'El resultado por variante' : 'The per-variant result'}</h2>
        {rows.length === 0 ? (
          <p className="sym-empty">
            {es
              ? 'Aun no hay artefactos publicados en este despliegue. La tabla se rellena sola cuando el horneado se completa; no hay numeros de reserva escritos a mano en esta pagina.'
              : 'No artifacts are published in this deployment yet. This table fills itself when the bake completes; there are no hand-written fallback numbers on this page.'}
          </p>
        ) : (
          <div className="sym-table-scroll">
            <table className="sym-table">
              <thead>
                <tr>
                  <th>{es ? 'Caso' : 'Case'}</th>
                  <th>{es ? 'Variante' : 'Variant'}</th>
                  <th>{es ? 'Nodos' : 'Nodes'}</th>
                  <th>R2 {es ? 'prueba' : 'test'}</th>
                  <th>{es ? 'Sol. exactitud' : 'Acc. solution'}</th>
                  <th>{es ? 'Recuperacion' : 'Recovery'}</th>
                  <th>{es ? 'Vars usadas' : 'Vars used'}</th>
                  <th>s</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, i) => (
                  <tr key={`${row.caseId}-${row.score.variant_id}-${i}`}>
                    <td>
                      <code>{row.caseId}</code>
                    </td>
                    <td>{row.label}</td>
                    <td>{row.score.selected_complexity}</td>
                    <td>
                      {row.score.best_test_r2 === null ? '-' : row.score.best_test_r2.toFixed(4)}
                    </td>
                    <td>{row.score.accuracy_solution ? (es ? 'si' : 'yes') : 'no'}</td>
                    <td>
                      {row.score.equivalence === null
                        ? es
                          ? 'no comprobable'
                          : 'not checkable'
                        : row.score.equivalence.symbolic === null
                          ? es
                            ? 'evaluador fallo'
                            : 'scorer failed'
                          : row.score.equivalence.symbolic
                            ? es
                              ? 'si'
                              : 'yes'
                            : 'no'}
                    </td>
                    <td>
                      {row.member
                        ? `${row.member.variables_used.length}/${row.member.n_variables_available}`
                        : '-'}
                    </td>
                    <td>{row.score.seconds.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {totals && (
        <section>
          <h2>{es ? 'Totales medidos' : 'Measured totals'}</h2>
          <ul>
            <li>
              {es ? 'casos publicados' : 'cases published'}: <strong>{totals.cases}</strong>
            </li>
            <li>
              {es ? 'configuraciones ejecutadas' : 'configurations run'}: <strong>{totals.variants}</strong>
            </li>
            <li>
              {es ? 'soluciones por exactitud' : 'accuracy solutions'}:{' '}
              <strong>
                {totals.accuracySolutions} / {totals.variants}
              </strong>
            </li>
            <li>
              {es ? 'recuperaciones exactas' : 'exact recoveries'}:{' '}
              <strong>
                {totals.recovered} / {totals.checkable}
              </strong>{' '}
              {es
                ? `(sobre las ${totals.checkable} configuraciones donde la recuperacion ES comprobable, no sobre las ${totals.variants})`
                : `(over the ${totals.checkable} configurations where recovery IS checkable, not over all ${totals.variants})`}
            </li>
            <li>
              <strong>
                {es ? 'ajustaron bien y NO encontraron la ley' : 'fitted well and did NOT find the law'}
              </strong>
              : <strong>{totals.fitButNotFound}</strong>{' '}
              {es
                ? 'configuraciones superaron el umbral de exactitud y devolvieron la estructura equivocada. Esa cuenta es la medicion que justifica este laboratorio.'
                : 'configurations cleared the accuracy threshold and returned the wrong structure. That count is the measurement this lab exists to make.'}
            </li>
            <li>
              {es ? 'R2 mediano en prueba' : 'median test R2'}:{' '}
              <strong>{totals.medianR2 === null ? '-' : totals.medianR2.toFixed(4)}</strong>
            </li>
            <li>
              {es ? 'evaluaciones totales' : 'total evaluations'}:{' '}
              <strong>{groupDigits(totals.evaluations)}</strong>
            </li>
            <li>
              {es ? 'segundos de busqueda' : 'search seconds'}: <strong>{totals.seconds.toFixed(0)}</strong>
            </li>
          </ul>
        </section>
      )}

      <section>
        <h2>{es ? 'Como leer esta tabla, y como no' : 'How to read this table, and how not to'}</h2>
        <Callout variant="honest" title={es ? 'Una tasa de exactitud alta no es un descubrimiento' : 'A high accuracy rate is not a discovery'}>
          <p>
            {es
              ? 'La columna de exactitud dice que la expresion ajusta las filas retenidas. La columna de recuperacion dice que es la expresion CORRECTA. Sobre un conjunto de descubrimiento cientifico, un metodo preentrenado alcanzo 26,7 por ciento en la primera con 0,00 por ciento en la segunda. Leer la primera columna como si fuera la segunda es el error que esta pagina existe para impedir.'
              : 'The accuracy column says the expression fits the held-out rows. The recovery column says it is the CORRECT expression. On a scientific-discovery benchmark, a pretrained method reached 26.7 percent on the first with 0.00 percent on the second. Reading the first column as if it were the second is the mistake this page exists to prevent.'}{' '}
            <Cite id="matsubara2022" paren />
          </p>
        </Callout>
        <Callout variant="honest" title={es ? 'Evaluador fallo no significa metodo fallo' : 'Scorer failed does not mean method failed'}>
          <p>
            {es
              ? 'Cuando la columna de recuperacion dice que el evaluador fallo, el simplificador simbolico no pudo decidir. Eso es un defecto de la herramienta de medicion. La practica comun lo cuenta contra el metodo, lo que penaliza sistematicamente a quien produce expresiones dificiles de simplificar; aqui se distingue.'
              : 'When the recovery column says the scorer failed, the symbolic simplifier could not decide. That is a defect of the measurement tool. Common practice counts it against the method, which systematically penalises whichever method produces expressions that are hard to simplify; here it is distinguished.'}
          </p>
        </Callout>
        <Callout variant="honest" title={es ? 'Las variables usadas importan mas de lo que parece' : 'Variables used matters more than it looks'}>
          <p>
            {es
              ? 'La evaluacion mas amplia del campo encontro que NINGUN algoritmo recupero la expresion correcta libre de caracteristicas irrelevantes. Esa columna hace medible ese hallazgo aqui: una expresion que usa mas entradas de las que la ley necesita no es la ley, por bien que ajuste.'
              : 'The broadest evaluation in the field found that NO algorithm recovered the correct expression free of irrelevant features. That column makes the finding measurable here: an expression using more inputs than the law needs is not the law, however well it fits.'}{' '}
            <Cite id="defranca2024" paren />
          </p>
        </Callout>
        <Refs ids={['defranca2024', 'matsubara2022', 'lacava2021', 'shojaee2025']} label={es ? 'Referencias' : 'References'} />
      </section>
    </div>
  );
}
