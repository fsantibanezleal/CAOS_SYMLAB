/**
 * Tab 1: what the search FOUND, next to what the relationship ACTUALLY IS.
 *
 * A reader arriving at a rendered equation has no way to tell whether it is the result of the
 * search or the law that was typed in, and that distinction is the entire claim of this product.
 * So the panel is built as a comparison rather than as a display: the discovered expression on the
 * left under an explicit "found by the search" heading, the published law on the right under
 * "the relationship we expected", and the verdict of the equivalence test between them.
 *
 * Where no published law exists, the right-hand side says so instead of going blank. A measured
 * plant dataset has no closed form to recover, and reporting that as a failed recovery would be a
 * false statement about the method.
 */
import katex from 'katex';
import type React from 'react';
import { useEffect, useMemo, useRef } from 'react';

import type { ParetoMember, VariantScore } from '../lib/contract.types';
import { formatR2 } from '../lib/format';

/**
 * Mark the wrapper when its mathematics is wider than its box, so the fade and the scrollbar
 * appear. Silent clipping is the failure mode: a formula cut at the panel edge reads as a broken
 * renderer rather than as something the reader can scroll.
 */
function useClipDetection(inner: React.RefObject<HTMLDivElement | null>, deps: unknown[]) {
  const wrap = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const node = inner.current;
    const box = wrap.current;
    if (!node || !box) return;
    const measure = () => {
      box.classList.toggle('is-clipped', node.scrollWidth - node.clientWidth > 2);
    };
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(node);
    return () => observer.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return wrap;
}

function MathBlock({ tex }: { tex: string }) {
  const host = useRef<HTMLDivElement>(null);
  const wrap = useClipDetection(host, [tex]);
  useEffect(() => {
    if (!host.current) return;
    try {
      katex.render(tex, host.current, {
        displayMode: true,
        throwOnError: false,
        trust: (c) => c.command === '\\htmlData' || c.command === '\\htmlClass',
        strict: false,
      });
    } catch (error) {
      if (host.current) host.current.textContent = String(error);
    }
  }, [tex]);
  return (
    <div ref={wrap} className="sym-math-wrap">
      <div ref={host} className="sym-math" />
    </div>
  );
}

export interface ExpressionPanelProps {
  member: ParetoMember;
  targetSymbol: string;
  /** The published law, when the case has one. */
  truthLatex: string | null;
  truthAvailable: boolean;
  /** "structure": the parameters were input columns, so only the form was unknown.
   *  "structure+constants": the numbers had to be recovered too. */
  regime: string;
  score: VariantScore;
  variantLabel: string;
  longForm: boolean;
  showRaw: boolean;
  onHoverNode: (id: number | null) => void;
  lang: 'en' | 'es';
}

export function ExpressionPanel({
  member,
  targetSymbol,
  truthLatex,
  truthAvailable,
  regime,
  score,
  variantLabel,
  longForm,
  showRaw,
  onHoverNode,
  lang,
}: ExpressionPanelProps) {
  const es = lang === 'en' ? false : true;
  const hostRef = useRef<HTMLDivElement>(null);
  const foundWrap = useClipDetection(hostRef, [member, showRaw, longForm]);

  const tex = useMemo(() => {
    if (showRaw) return `${targetSymbol} = ${member.latex_raw}`;
    if (longForm) return member.latex_aligned;
    return `${targetSymbol} = ${member.latex_pretty}`;
  }, [member, targetSymbol, longForm, showRaw]);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    try {
      katex.render(tex, host, {
        displayMode: true,
        throwOnError: false,
        trust: (c) => c.command === '\\htmlData' || c.command === '\\htmlClass',
        strict: false,
      });
    } catch (error) {
      host.textContent = String(error);
    }
  }, [tex]);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const over = (event: Event) => {
      const target = (event.target as HTMLElement).closest('[data-nid]');
      onHoverNode(target ? Number((target as HTMLElement).dataset.nid) : null);
    };
    const out = () => onHoverNode(null);
    host.addEventListener('mouseover', over);
    host.addEventListener('mouseout', out);
    return () => {
      host.removeEventListener('mouseover', over);
      host.removeEventListener('mouseout', out);
    };
  }, [onHoverNode]);

  /**
   * A long expression in a half-width column clips, and a clipped formula reads as a broken page
   * rather than as a scrollable one. So the comparison stacks to full width as soon as either side
   * is long enough to need it, and the threshold is measured on the markup rather than guessed from
   * node count: `\frac` and `\cdot` cost characters without costing nodes.
   */
  const stacked = Math.max(
    (showRaw ? member.latex_raw : member.latex_pretty).length,
    truthLatex?.length ?? 0,
  ) > 95;

  const eq = score.equivalence;
  const recovered = eq ? (eq.symbolic !== null ? eq.symbolic : eq.numerical) : null;

  const verdict = !truthAvailable
    ? { key: 'none', text: es ? 'nada que comparar' : 'nothing to compare against' }
    : eq === null
      ? { key: 'none', text: es ? 'sin veredicto' : 'no verdict' }
      : eq.symbolic === null && eq.numerical === null
        ? { key: 'unknown', text: es ? 'el evaluador no pudo decidir' : 'the scorer could not decide' }
        : recovered
          ? { key: 'yes', text: es ? 'ESTRUCTURA RECUPERADA' : 'STRUCTURE RECOVERED' }
          : { key: 'no', text: es ? 'ESTRUCTURA NO RECUPERADA' : 'STRUCTURE NOT RECOVERED' };

  return (
    <div className="sym-compare">
      {/* -------------------------------------------------- the two sides, labelled before the maths */}
      <div className={`sym-compare-grid${stacked ? ' is-stacked' : ''}`}>
        <section className="sym-side sym-side-found">
          <header>
            <span className="sym-tag sym-tag-found">
              {es ? 'ENCONTRADO POR LA BUSQUEDA' : 'FOUND BY THE SEARCH'}
            </span>
            <p>
              {es
                ? `Salida de la busqueda. Solo recibio las columnas de datos. Configuracion: ${variantLabel}.`
                : `Output of the search. It received only the data columns. Configuration: ${variantLabel}.`}
            </p>
          </header>
          <div ref={foundWrap} className="sym-math-wrap">
            <div ref={hostRef} className="sym-math" />
          </div>
          <dl className="sym-side-metrics">
            <div>
              <dt>R2 {es ? 'prueba' : 'test'}</dt>
              <dd>{formatR2(member.r2_test)}</dd>
            </div>
            <div>
              <dt>{es ? 'complejidad' : 'complexity'}</dt>
              <dd>{member.complexity}</dd>
            </div>
            <div>
              <dt>{es ? 'long. descripcion' : 'description length'}</dt>
              <dd>{member.description_length.total.toFixed(1)}</dd>
            </div>
          </dl>
        </section>

        <div className={`sym-verdict-rail is-${verdict.key}`} aria-hidden="true">
          <span className="sym-verdict-mark">
            {verdict.key === 'yes' ? '=' : verdict.key === 'no' ? '≠' : '?'}
          </span>
        </div>

        <section className="sym-side sym-side-truth">
          <header>
            <span className="sym-tag sym-tag-truth">
              {es ? 'LA RELACION ESPERADA' : 'THE RELATIONSHIP WE EXPECTED'}
            </span>
            <p>
              {truthAvailable
                ? es
                  ? 'La ley publicada que genero estos datos. Se usa SOLO para puntuar: la busqueda nunca la vio.'
                  : 'The published law that generated this data. Used ONLY for scoring: the search never saw it.'
                : es
                  ? 'Este caso son mediciones de planta o instrumento. No existe forma cerrada publicada.'
                  : 'This case is plant or instrument measurement. No published closed form exists.'}
            </p>
          </header>
          {truthAvailable && truthLatex ? (
            <>
              <MathBlock tex={`${targetSymbol} = ${truthLatex}`} />
              <dl className="sym-side-metrics">
                <div>
                  <dt>{es ? 'regimen' : 'regime'}</dt>
                  <dd>{regime === 'structure' ? (es ? 'solo la forma' : 'form only') : (es ? 'forma y constantes' : 'form and constants')}</dd>
                </div>
                <div>
                  <dt>{es ? 'distancia estructural' : 'structural distance'}</dt>
                  <dd>
                    {eq && eq.structural_distance !== null ? eq.structural_distance.toFixed(3) : 'n/a'}
                  </dd>
                </div>
                <div>
                  <dt>{es ? 'error rel. maximo' : 'max rel. error'}</dt>
                  <dd>
                    {eq && eq.numerical_max_rel_error !== null
                      ? eq.numerical_max_rel_error.toExponential(2)
                      : 'n/a'}
                  </dd>
                </div>
              </dl>
            </>
          ) : (
            <p className="sym-side-blank">
              {es
                ? 'La expresion de la izquierda es un HALLAZGO sin referencia. Contribuye a las metricas de error y a ninguna tasa de recuperacion. Reportarla como recuperacion cero seria falso.'
                : 'The expression on the left is a FINDING with no reference. It contributes to the error metrics and to no recovery rate. Reporting it as zero recovery would be false.'}
            </p>
          )}
        </section>
      </div>

      {/* -------------------------------------------------- the verdict, stated in words */}
      <div className={`sym-verdict is-${verdict.key}`}>
        <strong>{verdict.text}</strong>
        {truthAvailable && eq && (
          <>
            <span>
              {es ? 'prueba simbolica' : 'symbolic test'}{' '}
              <b>{eq.symbolic === null ? (es ? 'sin decidir' : 'undecided') : eq.symbolic ? (es ? 'igual' : 'equal') : (es ? 'distinta' : 'different')}</b>
            </span>
            <span>
              {es ? 'prueba numerica' : 'numerical test'}{' '}
              <b>{eq.numerical === null ? 'n/a' : eq.numerical ? (es ? 'igual' : 'equal') : (es ? 'distinta' : 'different')}</b>
            </span>
            {eq.structural_distance !== null && (
              <span>
                {es ? 'distancia' : 'distance'} <b>{eq.structural_distance.toFixed(3)}</b>{' '}
                {es ? '(0 identica, 1 sin parecido)' : '(0 identical, 1 nothing in common)'}
              </span>
            )}
          </>
        )}
      </div>

      {truthAvailable && eq && !eq.agreed && (
        <p className="sym-note sym-warn">
          {es
            ? 'Las pruebas simbolica y numerica no coincidieron. Suelen coincidir dentro de la caja muestreada y diferir fuera de ella, que es exactamente donde una expresion equivocada se delata.'
            : 'The symbolic and numerical tests disagreed. They usually agree inside the sampled box and differ outside it, which is exactly where a wrong expression gives itself away.'}
          {eq.disagreement_note ? ` ${eq.disagreement_note}` : ''}
        </p>
      )}

      {truthAvailable && eq && eq.symbolic === null && eq.symbolic_error && (
        <p className="sym-note sym-warn">
          {es ? 'Fallo del evaluador, no del metodo: ' : 'A scorer failure, not a method failure: '}
          {eq.symbolic_error}
        </p>
      )}

      {truthAvailable && (
        <p className="sym-note">
          {regime === 'structure'
            ? es
              ? 'Regimen: los parametros fisicos se entregaron como COLUMNAS de entrada, asi que lo desconocido era la FORMA y no los numeros. Es la convencion de los benchmarks de fisica publicados y es mas facil que recuperar tambien las constantes.'
              : 'Regime: the physical parameters were given as input COLUMNS, so what was unknown was the FORM and not the numbers. This is the convention the published physics benchmarks use, and it is easier than also recovering the constants.'
            : es
              ? 'Regimen: las constantes estan dentro del generador, asi que habia que recuperar tambien los NUMEROS. Es materialmente mas dificil que recuperar solo la forma.'
              : 'Regime: the constants are baked into the generator, so the NUMBERS had to be recovered too. That is materially harder than recovering the form alone.'}
        </p>
      )}

      {/* -------------------------------------------------- how the constants were shown */}
      <div className="sym-rounding">
        <h4>{es ? 'Redondeo de las constantes' : 'Constant rounding'}</h4>
        {member.rounding.accepted ? (
          <p className="sym-note">
            {es
              ? `Constantes mostradas con ${member.rounding.sig_digits} cifras significativas. El redondeo cambio las predicciones en ${
                  member.rounding.max_rel_error === null
                    ? 'menos de la tolerancia'
                    : member.rounding.max_rel_error.toExponential(2)
                }, medido sobre las filas reales.`
              : `Constants shown to ${member.rounding.sig_digits} significant digits. The rounding moved predictions by ${
                  member.rounding.max_rel_error === null
                    ? 'less than tolerance'
                    : member.rounding.max_rel_error.toExponential(2)
                }, measured on the real rows.`}
          </p>
        ) : (
          <p className="sym-note sym-warn">
            {es
              ? 'El redondeo fue RECHAZADO: habria cambiado el modelo mas alla de la tolerancia, asi que se muestra la precision completa. Una salida mas bonita que es en silencio otro modelo no es una mejora.'
              : 'Rounding was REFUSED: it would have changed the model beyond tolerance, so full precision is shown. Prettier output that is quietly a different model is not an improvement.'}
          </p>
        )}
      </div>

      {/* `=== false` never fired while the exporter wrote 0 for false. */}
      {member.units_ok !== null && !member.units_ok && (
        <p className="sym-note sym-warn">
          {es ? 'Coherencia dimensional: ' : 'Dimensional consistency: '}
          {member.units_reason}
        </p>
      )}
    </div>
  );
}
