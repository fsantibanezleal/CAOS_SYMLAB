/**
 * Tab 2: the structure behind the formula, and the components it is built from.
 *
 * Three views of one object, all keyed by the SAME integer node id space the pipeline emits, so
 * hovering a term in the equation, a node in the tree and a bar in the contribution chart all
 * highlight the same subexpression. A second, parallel mapping would drift; there is only one.
 *
 * The component table answers the question the tree cannot: which additive term actually carries
 * the signal. A term can be structurally large and contribute almost nothing, and that is the
 * single most common way a discovered expression is worse than it looks.
 */
import katex from 'katex';
import { useEffect, useMemo, useRef } from 'react';

import type { ParetoMember, ValidationPayload } from '../lib/contract.types';
import { ExpressionTree } from './ExpressionTree';

/**
 * A term rendered as mathematics rather than as its own source.
 *
 * The payload carries LaTeX, and printing it into a table cell showed the reader
 * `\ln(\frac{1}{T_{amb} \cdot T_{amb}^{2}})`. That is the markup, not the term.
 */
function TermMath({ latex }: { latex: string }) {
  const host = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    if (!host.current) return;
    try {
      katex.render(latex, host.current, {
        displayMode: false,
        throwOnError: false,
        trust: (c) => c.command === '\\htmlData' || c.command === '\\htmlClass',
        strict: false,
      });
    } catch {
      // Falling back to the source is better than an empty cell: the reader still sees the term,
      // and the failure is visible rather than silent.
      if (host.current) host.current.textContent = latex;
    }
  }, [latex]);
  return <span ref={host} className="sym-term-math" />;
}

export interface StructurePanelProps {
  member: ParetoMember;
  validation: ValidationPayload;
  activeNodeId: number | null;
  onHoverNode: (id: number | null) => void;
  collapseBelowInfluence: number;
  lang: 'en' | 'es';
}

export function StructurePanel({
  member,
  validation,
  activeNodeId,
  onHoverNode,
  collapseBelowInfluence,
  lang,
}: StructurePanelProps) {
  const es = lang === 'es';

  const maxContrib = useMemo(
    () => Math.max(1e-30, ...member.terms.map((t) => t.mean_abs_contrib)),
    [member.terms],
  );

  const operators = useMemo(
    () =>
      Object.entries(member.operator_counts)
        .filter(([, n]) => n > 0)
        .sort((a, b) => b[1] - a[1]),
    [member.operator_counts],
  );

  const unused = member.n_variables_available - member.variables_used.length;

  return (
    <div className="sym-structure">
      <section className="sym-block">
        <h3>{es ? 'El arbol de la expresion' : 'The expression tree'}</h3>
        <p className="sym-block-lede">
          {es
            ? 'El radio de cada nodo codifica su influencia: la caida en R2 al reemplazar ese subarbol por su media. Pasa el cursor por un nodo y el termino correspondiente se resalta en la ecuacion.'
            : 'Node radius encodes influence: the drop in R-squared when that subtree is replaced by its mean. Hover a node and the matching term highlights in the equation.'}
        </p>
        <ExpressionTree
          payload={member.tree}
          activeNodeId={activeNodeId}
          onHoverNode={onHoverNode}
          collapseBelowInfluence={collapseBelowInfluence}
          lang={lang}
        />
      </section>

      <section className="sym-block">
        <h3>{es ? 'Componentes de la expresion' : 'Components of the expression'}</h3>
        <p className="sym-block-lede">
          {es
            ? 'Cada termino aditivo de nivel superior, con lo que aporta realmente. Un termino puede ser grande y no aportar casi nada: esa es la forma mas comun de que una expresion sea peor de lo que parece.'
            : 'Each top-level additive term, with what it actually contributes. A term can be structurally large and contribute almost nothing, which is the most common way a discovered expression is worse than it looks.'}
        </p>

        {member.terms.length === 0 ? (
          <p className="sym-empty">
            {es
              ? 'La expresion no es una suma de terminos, asi que no se descompone aditivamente. El arbol de arriba es la descomposicion valida.'
              : 'The expression is not a sum of terms, so it does not decompose additively. The tree above is the valid decomposition.'}
          </p>
        ) : (
          <table className="sym-terms">
            <thead>
              <tr>
                <th scope="col">{es ? 'termino' : 'term'}</th>
                <th scope="col">{es ? 'aporte medio |.|' : 'mean |contribution|'}</th>
                <th scope="col">{es ? 'share de varianza' : 'variance share'}</th>
                <th scope="col">{es ? 'nodos' : 'nodes'}</th>
              </tr>
            </thead>
            <tbody>
              {member.terms.map((term) => (
                <tr
                  key={term.term_id}
                  className={`sym-term-row sym-term-${term.color_index}${
                    activeNodeId !== null && term.node_id === activeNodeId ? ' is-active' : ''
                  }`}
                  onMouseEnter={() => term.node_id !== null && onHoverNode(term.node_id)}
                  onMouseLeave={() => onHoverNode(null)}
                >
                  <th scope="row">
                    <span className="sym-term-swatch" aria-hidden="true" />
                    <TermMath latex={term.latex} />
                  </th>
                  <td>
                    <span className="sym-bar-cell">
                      <span
                        className="sym-bar"
                        style={{ width: `${(term.mean_abs_contrib / maxContrib) * 100}%` }}
                      />
                      <span className="sym-bar-value">{term.mean_abs_contrib.toPrecision(3)}</span>
                    </span>
                  </td>
                  <td>{(term.var_share * 100).toFixed(1)}%</td>
                  <td>{term.complexity}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <div className="sym-two-col">
        <section className="sym-block">
          <h3>{es ? 'Operadores usados' : 'Operators used'}</h3>
          {operators.length === 0 ? (
            <p className="sym-empty">
              {es ? 'La expresion no contiene operadores.' : 'The expression contains no operators.'}
            </p>
          ) : (
            <ul className="sym-oplist">
              {operators.map(([op, n]) => (
                <li key={op}>
                  <code>{op}</code>
                  <span>{n}</span>
                </li>
              ))}
            </ul>
          )}
          <p className="sym-note">
            {es
              ? `${member.tree.n_nodes} nodos, profundidad ${member.tree.max_depth}, complejidad ponderada ${member.complexity_weighted.toFixed(1)}. La complejidad ponderada cobra mas por un exponencial que por una suma, porque no cuestan lo mismo de leer ni de justificar.`
              : `${member.tree.n_nodes} nodes, depth ${member.tree.max_depth}, weighted complexity ${member.complexity_weighted.toFixed(1)}. Weighted complexity charges more for an exponential than for an addition, because they do not cost the same to read or to justify.`}
          </p>
        </section>

        <section className="sym-block">
          <h3>{es ? 'Variables' : 'Variables'}</h3>
          <p className="sym-kv">
            <span>{es ? 'usadas' : 'used'}</span>
            <strong>
              {member.variables_used.length} / {member.n_variables_available}
            </strong>
          </p>
          <p className="sym-note">
            {unused > 0
              ? es
                ? `La expresion ignora ${unused} de las entradas disponibles. Eso puede ser seleccion de variables correcta o puede ser que la busqueda nunca las alcanzo; el frente de la otra pestana distingue entre ambas.`
                : `The expression ignores ${unused} of the available inputs. That can be correct variable selection or it can be that the search never reached them; the front in the other tab separates the two.`
              : es
                ? 'La expresion usa todas las entradas disponibles. En un caso con variables irrelevantes conocidas, eso es una senal de alarma, no de completitud.'
                : 'The expression uses every available input. On a case with known irrelevant variables, that is a warning sign rather than a sign of completeness.'}
          </p>
          {validation.term_contributions && (
            <p className="sym-note">
              {es
                ? `Los aportes por termino se calcularon sobre las filas ordenadas por ${validation.term_contributions.sort_key}.`
                : `Per-term contributions were computed over rows ordered by ${validation.term_contributions.sort_key}.`}
            </p>
          )}
        </section>
      </div>
    </div>
  );
}
