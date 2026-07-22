/**
 * The accuracy-versus-complexity Pareto front: the deliverable, not a summary of it.
 *
 * This lab's whole argument is that symbolic regression should report a front rather than a winner,
 * so this view is the primary one and clicking a point loads that expression into every other panel.
 * That is why it is hand-rolled SVG rather than a charting library: the interaction is click-to-load
 * with cross-highlighting into the equation and the tree, and a general chart library makes that
 * fight its event model.
 *
 * Two marks that are not decoration:
 *
 * - The **selected** point is the one chosen by minimum description length, not by best accuracy.
 *   Selecting by accuracy is precisely how a method scores above 0.999 while recovering the wrong
 *   structure, so the default marker has to be the honest one.
 * - The **elbow score** per point is the drop in log loss per unit of added complexity relative to
 *   the previous front member. It makes "where the front bends" a number rather than an impression.
 */
import { scaleLinear, scaleLog } from 'd3-scale';
import { useMemo, useState } from 'react';

import type { ParetoMember } from '../lib/contract.types';

export interface ParetoFrontProps {
  members: ParetoMember[];
  selectedIndex: number;
  activeIndex: number;
  onSelect: (index: number) => void;
  /** Exported versus total, so a cap on the exported front is disclosed rather than implied. */
  exported: number;
  total: number;
  lang: 'en' | 'es';
}

const WIDTH = 720;
const HEIGHT = 320;
const PAD = { top: 20, right: 24, bottom: 46, left: 66 };

export function ParetoFront({
  members,
  selectedIndex,
  activeIndex,
  onSelect,
  exported,
  total,
  lang,
}: ParetoFrontProps) {
  const [hover, setHover] = useState<number | null>(null);

  const usable = useMemo(
    () => members.filter((m) => m.loss_train !== null && Number.isFinite(m.loss_train)),
    [members],
  );

  const scales = useMemo(() => {
    if (usable.length === 0) return null;
    const losses = usable.map((m) => Math.max(m.loss_train as number, 1e-300));
    const complexities = usable.map((m) => m.complexity);
    const x = scaleLinear()
      .domain([Math.min(...complexities) - 1, Math.max(...complexities) + 1])
      .range([PAD.left, WIDTH - PAD.right]);
    // Log scale on the loss axis: a front routinely spans many orders of magnitude, and a linear
    // axis collapses every good member onto the baseline where the interesting structure is.
    const y = scaleLog()
      .domain([Math.min(...losses) * 0.5, Math.max(...losses) * 2])
      .range([HEIGHT - PAD.bottom, PAD.top]);
    return { x, y };
  }, [usable]);

  if (!scales || usable.length === 0) {
    return (
      <p className="sym-empty">
        {lang === 'es'
          ? 'Esta variante no produjo ningun candidato finito. Eso es un resultado, no un fallo de la vista.'
          : 'This variant produced no finite candidate. That is a result, not a missing view.'}
      </p>
    );
  }

  const { x, y } = scales;
  const shownIndex = hover ?? activeIndex;
  const shown = usable.find((m) => m.index === shownIndex) ?? usable[0];

  const path = usable
    .slice()
    .sort((a, b) => a.complexity - b.complexity)
    .map((m, i) => `${i === 0 ? 'M' : 'L'}${x(m.complexity)},${y(Math.max(m.loss_train as number, 1e-300))}`)
    .join(' ');

  // `scaleLog.ticks(n)` treats n as a hint and returns every minor step when the domain spans
  // several decades, which overlapped into an unreadable smear down the axis. Decades only, and if
  // there are still too many, every other one.
  const decades = y.ticks(5).filter((t) => Number.isInteger(Math.round(Math.log10(t) * 1e6) / 1e6));
  const yTicks = decades.length > 6 ? decades.filter((_, i) => i % 2 === 0) : decades;
  const xTicks = x.ticks(Math.min(8, usable.length + 2)).filter((t) => Number.isInteger(t));

  return (
    <div className="sym-pareto">
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        className="sym-pareto-svg"
        role="img"
        aria-label={
          lang === 'es'
            ? `Frente de Pareto: error de entrenamiento frente a complejidad, ${usable.length} miembros`
            : `Pareto front: training loss against complexity, ${usable.length} members`
        }
      >
        {yTicks.map((tick) => (
          <g key={`y${tick}`}>
            <line className="sym-grid" x1={PAD.left} x2={WIDTH - PAD.right} y1={y(tick)} y2={y(tick)} />
            <text className="sym-axis-label" x={PAD.left - 8} y={y(tick)} dy="0.32em" textAnchor="end">
              {tick.toExponential(0)}
            </text>
          </g>
        ))}
        {xTicks.map((tick) => (
          <text
            key={`x${tick}`}
            className="sym-axis-label"
            x={x(tick)}
            y={HEIGHT - PAD.bottom + 18}
            textAnchor="middle"
          >
            {tick}
          </text>
        ))}
        <text className="sym-axis-title" x={(WIDTH + PAD.left) / 2} y={HEIGHT - 8} textAnchor="middle">
          {lang === 'es' ? 'complejidad (nodos)' : 'complexity (nodes)'}
        </text>
        <text
          className="sym-axis-title"
          transform={`translate(14,${HEIGHT / 2}) rotate(-90)`}
          textAnchor="middle"
        >
          {lang === 'es' ? 'error cuadratico medio' : 'mean squared error'}
        </text>

        <path className="sym-pareto-path" d={path} />

        {usable.map((member) => {
          const cx = x(member.complexity);
          const cy = y(Math.max(member.loss_train as number, 1e-300));
          const isSelected = member.index === selectedIndex;
          const isActive = member.index === shownIndex;
          return (
            <g key={member.index}>
              {isSelected && <circle className="sym-pareto-selected-ring" cx={cx} cy={cy} r={13} />}
              <circle
                className={`sym-pareto-point${isActive ? ' is-active' : ''}${isSelected ? ' is-selected' : ''}`}
                cx={cx}
                cy={cy}
                r={isActive ? 8 : 6}
                onMouseEnter={() => setHover(member.index)}
                onMouseLeave={() => setHover(null)}
                onClick={() => onSelect(member.index)}
                tabIndex={0}
                role="button"
                aria-label={`${lang === 'es' ? 'complejidad' : 'complexity'} ${member.complexity}`}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') onSelect(member.index);
                }}
              />
            </g>
          );
        })}
      </svg>

      <div className="sym-pareto-readout" aria-live="polite">
        <div>
          <span>{lang === 'es' ? 'complejidad' : 'complexity'}</span>
          <strong>{shown.complexity}</strong>
        </div>
        <div>
          <span>MSE</span>
          <strong>{(shown.loss_train as number).toExponential(3)}</strong>
        </div>
        <div>
          <span>R2 {lang === 'es' ? 'prueba' : 'test'}</span>
          <strong>{shown.r2_test === null ? 'n/a' : shown.r2_test.toFixed(5)}</strong>
        </div>
        <div>
          <span>{lang === 'es' ? 'long. descripcion' : 'description length'}</span>
          <strong>{shown.description_length.total.toFixed(1)}</strong>
        </div>
        <div>
          <span>{lang === 'es' ? 'codo' : 'elbow score'}</span>
          <strong>{shown.score.toFixed(3)}</strong>
        </div>
      </div>

      <p className="sym-pareto-note">
        {lang === 'es'
          ? 'El anillo marca el punto elegido por longitud de descripcion minima, NO por mejor exactitud. Elegir por exactitud es exactamente como un metodo supera 0,999 recuperando la estructura equivocada.'
          : 'The ring marks the point chosen by minimum description length, NOT by best accuracy. Choosing by accuracy is exactly how a method exceeds 0.999 while recovering the wrong structure.'}
        {exported < total && (
          <>
            {' '}
            {lang === 'es'
              ? `Mostrando ${exported} de ${total} miembros del frente.`
              : `Showing ${exported} of ${total} front members.`}
          </>
        )}
      </p>
    </div>
  );
}
