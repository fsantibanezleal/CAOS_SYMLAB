/**
 * The search that earned the formula: convergence, diversity and the measured cost.
 *
 * The cost panel is not bookkeeping. The benchmark literature names budget unfairness as a standing
 * problem, and this lab measured a selection method that buys quality at roughly 22 times the
 * baseline wall-clock in isolation, and around 30 times cumulatively at the published budgets.
 * Showing seconds and evaluations next to the loss curve is what lets a reader
 * ask whether a rung earned its price, instead of comparing rungs at equal generation count and
 * calling that fair.
 */
import type { HistoryPayload, VariantScore } from '../lib/contract.types';
import { UPlotChart } from './UPlotChart';
import { groupDigits } from '../lib/format';



export function SearchHistory({
  history,
  score,
  lang,
}: {
  history: HistoryPayload;
  score: VariantScore;
  lang: 'en' | 'es';
}) {
  const generations = history.generation ?? [];
  if (generations.length === 0) {
    return (
      <p className="sym-empty">
        {lang === 'es' ? 'Sin historia de busqueda.' : 'No search history.'}
      </p>
    );
  }

  const clean = (values: (number | null)[]) =>
    values.map((v) => (v === null || !Number.isFinite(v) ? null : Math.max(v, 1e-300)));

  return (
    <div className="sym-history">
      <UPlotChart
        data={[generations, clean(history.best_loss), clean(history.mean_loss)] as never}
        series={[
          { label: lang === 'es' ? 'mejor' : 'best', cssVar: '--color-accent' },
          { label: lang === 'es' ? 'media' : 'mean', cssVar: '--color-fg-subtle' },
        ]}
        xLabel={lang === 'es' ? 'generacion' : 'generation'}
        yLabel={lang === 'es' ? 'error (log)' : 'loss (log)'}
        logY
        ariaLabel={lang === 'es' ? 'Curva de convergencia' : 'Convergence curve'}
      />

      <UPlotChart
        data={[generations, history.diversity.structural, history.diversity.semantic] as never}
        series={[
          { label: lang === 'es' ? 'estructural' : 'structural', cssVar: '--color-accent' },
          { label: lang === 'es' ? 'semantica' : 'semantic', cssVar: '--color-fg-subtle' },
        ]}
        xLabel={lang === 'es' ? 'generacion' : 'generation'}
        yLabel={lang === 'es' ? 'diversidad (fraccion unica)' : 'diversity (unique fraction)'}
        height={200}
        ariaLabel={lang === 'es' ? 'Diversidad de la poblacion' : 'Population diversity'}
      />

      <div className="sym-cost">
        <h4>{lang === 'es' ? 'Lo que costo esta variante' : 'What this variant cost'}</h4>
        <dl>
          <dt>{lang === 'es' ? 'segundos' : 'seconds'}</dt>
          <dd>{score.seconds.toFixed(1)}</dd>
          <dt>{lang === 'es' ? 'evaluaciones' : 'evaluations'}</dt>
          <dd>{groupDigits(score.evaluations)}</dd>
          <dt>{lang === 'es' ? 'duplicados evitados' : 'duplicates avoided'}</dt>
          <dd>{groupDigits(score.duplicates_avoided)}</dd>
          <dt>{lang === 'es' ? 'candidatos invalidos' : 'invalid candidates'}</dt>
          <dd>{groupDigits(score.invalid_rejected)}</dd>
          <dt>{lang === 'es' ? 'tamano del frente' : 'front size'}</dt>
          <dd>{score.front_size}</dd>
        </dl>
        <p className="sym-note">
          {lang === 'es'
            ? 'Los candidatos invalidos son los rechazados por la guarda de intervalos o por producir valores no finitos. Se cuentan, no se ocultan: la fraccion rechazada dice algo real sobre el conjunto de primitivas y sobre los datos.'
            : 'Invalid candidates are those rejected by the interval guard or producing non-finite values. They are counted, not hidden: the rejected fraction says something real about the primitive set and about the data.'}
        </p>
      </div>
    </div>
  );
}
