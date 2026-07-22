/**
 * The Context sub-tab: the deep write-up, in the fixed section order the product standard requires.
 *
 * The order is not decorative. It walks a reader from what the problem is, through what was
 * measured, to what the result does and does not license them to say. The last two sections are the
 * ones most tools omit and the ones this lab exists for.
 */
import { Callout, Equation } from '@fasl-work/caos-app-shell';

import type { RunPayload } from '../../lib/contract.types';

export function CaseContext({ run, lang }: { run: RunPayload; lang: 'en' | 'es' }) {
  const notes = run.notes;
  const es = lang === 'es';

  return (
    <div className="prose sym-context">
      <h3>{es ? 'El problema' : 'The problem'}</h3>
      <p>{es ? notes.summary_es : notes.summary_en}</p>
      <p>
        {es
          ? `Los datos son ${notes.real_or_synthetic === 'real' ? 'mediciones reales' : 'sinteticos con verdad conocida'}. Fuente: ${run.dataset.source ?? 'no declarada'}. Licencia: ${run.dataset.license ?? 'no declarada'}.`
          : `The data are ${notes.real_or_synthetic === 'real' ? 'real measurements' : 'synthetic with a known truth'}. Source: ${run.dataset.source ?? 'not declared'}. Licence: ${run.dataset.license ?? 'not declared'}.`}
      </p>

      <h3>{es ? 'Componentes y variables' : 'Components and variables'}</h3>
      <div className="sym-table-scroll">
        <table className="sym-table">
          <thead>
            <tr>
              <th>{es ? 'entrada' : 'input'}</th>
              <th>{es ? 'unidad' : 'unit'}</th>
              <th>{es ? 'dimension' : 'dimension'}</th>
              <th>{es ? 'rango muestreado' : 'sampled range'}</th>
              <th>{es ? 'decadas' : 'decades'}</th>
            </tr>
          </thead>
          <tbody>
            {notes.sampling.map((entry) => (
              <tr key={entry.key}>
                <td>
                  <code>{entry.key}</code>
                </td>
                <td>{entry.unit}</td>
                <td>{entry.dims_label}</td>
                <td>
                  {entry.min.toPrecision(4)} to {entry.max.toPrecision(4)}
                </td>
                <td>{entry.decades_spanned === null ? '-' : entry.decades_spanned.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p>
        {es
          ? 'El rango muestreado importa tanto como la ecuacion: una ley recuperada sobre una decada y una recuperada sobre cuatro no estan igualmente respaldadas, y el lector no puede notarlo mirando solo la formula.'
          : 'The sampled range matters as much as the equation: a law recovered over one decade and one recovered over four are not equally supported, and a reader cannot tell that from the formula alone.'}
      </p>

      <h3>{es ? 'Formalizacion' : 'Formalisation'}</h3>
      {notes.ground_truth_latex ? (
        <Equation
          tex={notes.ground_truth_latex}
          caption={
            es
              ? 'La relacion conocida o esperada para este caso, contra la cual se compara la expresion recuperada.'
              : 'The known or expected relationship for this case, against which the recovered expression is compared.'
          }
        />
      ) : (
        <Callout variant="honest" title={es ? 'Sin forma cerrada conocida' : 'No known closed form'}>
          <p>
            {es
              ? 'Este caso no tiene una respuesta publicada contra la cual comparar. Por eso contribuye a las metricas de error pero NO a la tasa de recuperacion: mezclar ambas permitiria citar un porcentaje de recuperacion que incluye en silencio problemas donde la recuperacion no se puede comprobar.'
              : 'This case has no published answer to compare against. It therefore contributes to the error metrics but NOT to the recovery rate: mixing the two would let a lab quote a recovery percentage that silently includes problems where recovery cannot be checked.'}
          </p>
        </Callout>
      )}

      <h3>{es ? 'Alcance y supuestos' : 'Scope and assumptions'}</h3>
      <p>{notes.split_note}</p>
      <p>{notes.features_note}</p>
      {notes.caveats.length > 0 && (
        <Callout variant="honest" title={es ? 'Lo que este caso NO demuestra' : 'What this case does NOT show'}>
          <ul>
            {notes.caveats.map((caveat, index) => (
              <li key={index}>{caveat}</li>
            ))}
          </ul>
        </Callout>
      )}

      <h3>{es ? 'Que muestra cada variante' : 'What each variant shows'}</h3>
      <ul>
        {notes.variants.map((variant) => (
          <li key={variant.id}>
            <strong>{es ? variant.label_es : variant.label_en}</strong>: {es ? variant.note_es : variant.note_en}
          </li>
        ))}
      </ul>

      <h3>{es ? 'Como leer y usar estas vistas' : 'How to read and use these views'}</h3>
      <ol>
        <li>
          {es
            ? 'Empieza por el frente, no por una sola ecuacion. El entregable es el frente completo; una ecuacion aislada esconde el intercambio que la produjo.'
            : 'Start at the front, not at a single equation. The deliverable is the whole front; one equation in isolation hides the trade-off that produced it.'}
        </li>
        <li>
          {es
            ? 'El anillo marca el punto elegido por longitud de descripcion minima, no por mejor exactitud.'
            : 'The ring marks the point chosen by minimum description length, not by best accuracy.'}
        </li>
        <li>
          {es
            ? 'Pasa el cursor por un termino de la ecuacion: se resalta el mismo subarbol en el arbol, porque ambos comparten un unico espacio de identificadores.'
            : 'Hover a term in the equation: the same subtree highlights in the tree, because both share one integer id space.'}
        </li>
        <li>
          {es
            ? 'Mira la vista de extrapolacion antes de creer nada. Ahi es donde la literatura de benchmarks dice que todos los metodos se degradan.'
            : 'Look at the extrapolation view before believing anything. That is where the benchmark literature says every method degrades.'}
        </li>
      </ol>

      {notes.certificate && (
        <>
          <h3>{es ? 'Certificado de completitud' : 'Completeness certificate'}</h3>
          <Callout
            variant={notes.certificate.complete ? 'note' : 'honest'}
            title={
              notes.certificate.complete
                ? es
                  ? 'Busqueda exhaustiva completa'
                  : 'Exhaustive search complete'
                : es
                  ? 'Enumeracion truncada, el certificado NO se sostiene'
                  : 'Enumeration truncated, the certificate does NOT hold'
            }
          >
            <p>{notes.certificate.statement}</p>
            <p>
              {es ? 'Enumeradas' : 'Enumerated'} {notes.certificate.n_enumerated.toLocaleString()},{' '}
              {es ? 'admisibles' : 'admissible'} {notes.certificate.n_admissible.toLocaleString()}.
              {notes.certificate.best_infix && (
                <>
                  {' '}
                  {es ? 'Mejor' : 'Best'}: <code>{notes.certificate.best_infix}</code>
                </>
              )}
            </p>
            <ul>
              {notes.certificate.caveats.map((caveat, index) => (
                <li key={index}>{caveat}</li>
              ))}
            </ul>
          </Callout>
        </>
      )}
    </div>
  );
}
