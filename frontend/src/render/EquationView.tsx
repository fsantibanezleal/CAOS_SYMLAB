/**
 * The discovered expression, rendered as mathematics and addressable term by term.
 *
 * Three decisions, all forced by evidence rather than taste:
 *
 * - **KaTeX, pinned.** It is synchronous, small, and emits MathML for assistive technology. It
 *   cannot line-break display math, which is why the long-form reading mode exists below.
 * - **Node ids travel INSIDE the markup.** The pipeline emits `\htmlData{nid=N}` around every
 *   subexpression, so hovering a term here highlights the same subtree in the tree view. Without
 *   that, the two views would need a second, parallel mapping, and parallel mappings drift.
 * - **Colour is a CSS class, never a baked hex.** The pipeline emits `\htmlClass{sym-term-N}` and
 *   the palette resolves from CSS custom properties, so the equation follows the light and dark
 *   themes. A hex written in Python is unreadable in one of them.
 *
 * The rounding report is shown rather than hidden. Constants are rounded for readability only when
 * the measured relative error stays inside tolerance; when it does not, full precision is shown and
 * the panel says so. Prettier output that is quietly a different model is not an improvement.
 */
import katex from 'katex';
import { useEffect, useMemo, useRef } from 'react';

import type { ParetoMember } from '../lib/contract.types';

export interface EquationViewProps {
  member: ParetoMember;
  targetSymbol: string;
  activeNodeId: number | null;
  onHoverNode: (id: number | null) => void;
  /** Long form wraps a many-term sum across lines. KaTeX cannot break display math on its own. */
  longForm: boolean;
  showRaw: boolean;
  lang: 'en' | 'es';
}

export function EquationView({
  member,
  targetSymbol,
  activeNodeId,
  onHoverNode,
  longForm,
  showRaw,
  lang,
}: EquationViewProps) {
  const hostRef = useRef<HTMLDivElement>(null);

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
        // `trust` is an ALLOW-LIST, not a blanket permission: only the two commands the pipeline
        // emits are honoured, so a payload cannot smuggle arbitrary markup through the renderer.
        trust: (context) => context.command === '\\htmlData' || context.command === '\\htmlClass',
        strict: false,
      });
    } catch (error) {
      host.textContent = String(error);
    }
  }, [tex]);

  // Hover is delegated from the container, so one listener serves every term rather than one per
  // node. The ids come from the same integer space as the tree, which is what makes this work.
  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const onOver = (event: Event) => {
      const target = (event.target as HTMLElement).closest('[data-nid]');
      onHoverNode(target ? Number((target as HTMLElement).dataset.nid) : null);
    };
    const onOut = () => onHoverNode(null);
    host.addEventListener('mouseover', onOver);
    host.addEventListener('mouseout', onOut);
    return () => {
      host.removeEventListener('mouseover', onOver);
      host.removeEventListener('mouseout', onOut);
    };
  }, [onHoverNode]);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    host.querySelectorAll('[data-nid]').forEach((element) => {
      element.classList.toggle('is-active', Number((element as HTMLElement).dataset.nid) === activeNodeId);
    });
  }, [activeNodeId, tex]);

  const rounding = member.rounding;

  return (
    <div className="sym-equation">
      <div ref={hostRef} className="sym-equation-body" />

      <ul className="sym-equation-meta">
        <li>
          <span>{lang === 'es' ? 'complejidad' : 'complexity'}</span>
          <strong>{member.complexity}</strong>
          <em>{lang === 'es' ? 'nodos' : 'nodes'}</em>
        </li>
        <li>
          <span>{lang === 'es' ? 'ponderada' : 'weighted'}</span>
          <strong>{member.complexity_weighted.toFixed(1)}</strong>
        </li>
        <li>
          <span>{lang === 'es' ? 'longitud de descripcion' : 'description length'}</span>
          <strong>{member.description_length.total.toFixed(1)}</strong>
          <em>nats</em>
        </li>
        {member.r2_test !== null && (
          <li>
            <span>R2 {lang === 'es' ? 'prueba' : 'test'}</span>
            <strong>{member.r2_test.toFixed(5)}</strong>
          </li>
        )}
        <li>
          <span>{lang === 'es' ? 'variables usadas' : 'variables used'}</span>
          <strong>
            {member.variables_used.length} / {member.n_variables_available}
          </strong>
        </li>
      </ul>

      <p className="sym-rounding">
        {rounding.accepted ? (
          <>
            {lang === 'es'
              ? `Constantes redondeadas a ${rounding.sig_digits} cifras significativas; el error relativo maximo introducido es `
              : `Constants rounded to ${rounding.sig_digits} significant figures; the maximum relative error this introduced is `}
            <strong>{rounding.max_rel_error === null ? 'n/a' : rounding.max_rel_error.toExponential(2)}</strong>
            {lang === 'es' ? ', dentro de la tolerancia.' : ', within tolerance.'}
          </>
        ) : (
          <>
            {lang === 'es'
              ? 'Se MUESTRA la precision completa: redondear habria cambiado el modelo mas alla de la tolerancia. Una expresion mas bonita que es en realidad un modelo distinto no es una mejora.'
              : 'Full precision is SHOWN: rounding would have changed the model beyond tolerance. A prettier expression that is quietly a different model is not an improvement.'}
          </>
        )}
      </p>

      {member.units_ok === false && (
        <p className="sym-units-warning">
          {lang === 'es' ? 'Inconsistencia dimensional: ' : 'Dimensional inconsistency: '}
          {member.units_reason}
        </p>
      )}
    </div>
  );
}
