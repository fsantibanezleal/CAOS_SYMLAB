/**
 * Model validation: parity, residuals, and the extrapolation behaviour that decides whether a
 * discovered expression is worth anything.
 *
 * The extrapolation panel is the one that matters most and the one almost no tool shows. The
 * benchmark literature is explicit that extrapolation is where every method degrades, so an app
 * that only ever plots predictions against truth inside the training region is showing the easy
 * half of the question. Here the training support is shaded, everything outside it is the part
 * nobody constrained, and points where the expression is undefined are COUNTED and stated rather
 * than dropped so the curve looks continuous.
 */
import { scaleLinear } from 'd3-scale';
import { useMemo, useState } from 'react';

import type { ValidationPayload } from '../lib/contract.types';

const W = 620;
const H = 300;
const PAD = { top: 18, right: 20, bottom: 42, left: 62 };

export function ParityPlot({ validation, lang }: { validation: ValidationPayload; lang: 'en' | 'es' }) {
  const [hover, setHover] = useState<number | null>(null);
  const parity = validation.parity;

  const points = useMemo(() => {
    if (!parity) return [];
    return parity.y_true
      .map((t, i) => ({ t, p: parity.y_pred[i], split: parity.split[i] }))
      .filter((d): d is { t: number; p: number; split: number } => d.p !== null && Number.isFinite(d.p));
  }, [parity]);

  if (!parity || points.length === 0) {
    return (
      <p className="sym-empty">
        {lang === 'es'
          ? 'La expresion seleccionada no produce predicciones finitas en estas filas. Eso es informacion, no un panel vacio.'
          : 'The selected expression produces no finite predictions on these rows. That is information, not an empty panel.'}
      </p>
    );
  }

  const all = points.flatMap((d) => [d.t, d.p]);
  const lo = Math.min(...all);
  const hi = Math.max(...all);
  const x = scaleLinear().domain([lo, hi]).range([PAD.left, W - PAD.right]);
  const y = scaleLinear().domain([lo, hi]).range([H - PAD.bottom, PAD.top]);

  const shown = hover !== null ? points[hover] : null;

  return (
    <div className="sym-parity">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label={lang === 'es' ? 'Grafico de paridad' : 'Parity plot'}
      >
        <line className="sym-parity-ideal" x1={x(lo)} y1={y(lo)} x2={x(hi)} y2={y(hi)} />
        {points.map((d, i) => (
          <circle
            key={i}
            className={`sym-parity-point${d.split === 1 ? ' is-test' : ''}${hover === i ? ' is-active' : ''}`}
            cx={x(d.t)}
            cy={y(d.p)}
            r={hover === i ? 5 : 2.6}
            onMouseEnter={() => setHover(i)}
            onMouseLeave={() => setHover(null)}
          />
        ))}
        <text className="sym-axis-title" x={(W + PAD.left) / 2} y={H - 8} textAnchor="middle">
          {lang === 'es' ? 'valor medido' : 'measured value'}
        </text>
        <text className="sym-axis-title" transform={`translate(14,${H / 2}) rotate(-90)`} textAnchor="middle">
          {lang === 'es' ? 'valor predicho' : 'predicted value'}
        </text>
      </svg>
      <div className="sym-readout" aria-live="polite">
        {shown ? (
          <>
            <span>
              {lang === 'es' ? 'medido' : 'measured'} <strong>{shown.t.toPrecision(5)}</strong>
            </span>
            <span>
              {lang === 'es' ? 'predicho' : 'predicted'} <strong>{shown.p.toPrecision(5)}</strong>
            </span>
            <span>
              {lang === 'es' ? 'residuo' : 'residual'} <strong>{(shown.t - shown.p).toPrecision(3)}</strong>
            </span>
            <span className="sym-chip">{shown.split === 1 ? (lang === 'es' ? 'prueba' : 'test') : (lang === 'es' ? 'entrenamiento' : 'train')}</span>
          </>
        ) : (
          <span className="sym-hint">
            {lang === 'es' ? 'Pasa el cursor por un punto.' : 'Hover a point for its values.'}
          </span>
        )}
      </div>
      <p className="sym-note">
        {lang === 'es'
          ? `Mostrando ${parity.n_shown} de ${parity.n_total} filas. Los puntos de prueba estan resaltados.`
          : `Showing ${parity.n_shown} of ${parity.n_total} rows. Test points are highlighted.`}
      </p>
    </div>
  );
}

export function ExtrapolationPlot({
  validation,
  lang,
}: {
  validation: ValidationPayload;
  lang: 'en' | 'es';
}) {
  const [variable, setVariable] = useState(0);
  const entries = validation.extrapolation ?? [];
  if (entries.length === 0) {
    return (
      <p className="sym-empty">
        {lang === 'es' ? 'Sin datos de extrapolacion.' : 'No extrapolation data.'}
      </p>
    );
  }
  const entry = entries[Math.min(variable, entries.length - 1)];
  const finite = entry.y
    .map((v, i) => ({ v, g: entry.grid[i] }))
    .filter((d): d is { v: number; g: number } => d.v !== null && Number.isFinite(d.v));

  if (finite.length === 0) {
    return (
      <p className="sym-empty">
        {lang === 'es'
          ? 'La expresion no esta definida en ningun punto fuera del soporte. Ese es un hallazgo fuerte sobre el modelo.'
          : 'The expression is undefined at every point outside the support. That is a strong finding about the model.'}
      </p>
    );
  }

  const x = scaleLinear().domain([Math.min(...entry.grid), Math.max(...entry.grid)]).range([PAD.left, W - PAD.right]);
  const values = finite.map((d) => d.v);
  const y = scaleLinear().domain([Math.min(...values), Math.max(...values)]).range([H - PAD.bottom, PAD.top]);
  const path = finite.map((d, i) => `${i === 0 ? 'M' : 'L'}${x(d.g)},${y(d.v)}`).join(' ');

  return (
    <div className="sym-extrap">
      {entries.length > 1 && (
        <div className="sym-chiprow">
          {entries.map((e, i) => (
            <button
              key={e.var}
              className={`chip${i === variable ? ' on' : ''}`}
              onClick={() => setVariable(i)}
              type="button"
            >
              {e.var}
            </button>
          ))}
        </div>
      )}
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={lang === 'es' ? 'Comportamiento en extrapolacion' : 'Extrapolation behaviour'}>
        <rect
          className="sym-support-band"
          x={x(entry.support[0])}
          width={Math.max(1, x(entry.support[1]) - x(entry.support[0]))}
          y={PAD.top}
          height={H - PAD.top - PAD.bottom}
        />
        <path className="sym-extrap-path" d={path} />
        <text className="sym-axis-title" x={(W + PAD.left) / 2} y={H - 8} textAnchor="middle">
          {entry.var}
        </text>
      </svg>
      <p className="sym-note">
        {lang === 'es'
          ? 'La banda sombreada es el soporte de entrenamiento. Fuera de ella nada restringio la expresion, y ahi es donde la literatura de benchmarks dice que todos los metodos se degradan.'
          : 'The shaded band is the training support. Outside it nothing constrained the expression, and that is where the benchmark literature says every method degrades.'}
        {entry.n_nonfinite > 0 && (
          <strong>
            {' '}
            {lang === 'es'
              ? `La expresion es indefinida en ${entry.n_nonfinite} puntos de la rejilla.`
              : `The expression is undefined at ${entry.n_nonfinite} grid points.`}
          </strong>
        )}
      </p>
    </div>
  );
}

export function PartialDependence({
  validation,
  lang,
}: {
  validation: ValidationPayload;
  lang: 'en' | 'es';
}) {
  const entries = validation.pdp ?? [];
  if (entries.length === 0) {
    return <p className="sym-empty">{lang === 'es' ? 'Sin dependencia parcial.' : 'No partial dependence.'}</p>;
  }
  return (
    <div className="sym-pdp-grid">
      {entries.map((entry) => {
        const finite = entry.mean
          .map((v, i) => ({ v, g: entry.grid[i] }))
          .filter((d): d is { v: number; g: number } => d.v !== null && Number.isFinite(d.v));
        if (finite.length === 0) return null;
        const x = scaleLinear().domain([entry.grid[0], entry.grid[entry.grid.length - 1]]).range([44, 280]);
        const vs = finite.map((d) => d.v);
        const y = scaleLinear().domain([Math.min(...vs), Math.max(...vs)]).range([148, 16]);
        return (
          <figure key={entry.var} className="sym-pdp">
            <svg viewBox="0 0 300 170" role="img" aria-label={`${entry.var}`}>
              <path
                className="sym-pdp-path"
                d={finite.map((d, i) => `${i === 0 ? 'M' : 'L'}${x(d.g)},${y(d.v)}`).join(' ')}
              />
            </svg>
            <figcaption>{entry.var}</figcaption>
          </figure>
        );
      })}
    </div>
  );
}
