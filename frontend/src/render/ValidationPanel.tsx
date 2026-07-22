/**
 * Tab 3: parity and residuals, then the two views that decide whether the expression is worth
 * anything outside the rows it was fitted on.
 *
 * The order is deliberate. Parity first, because it is the view every reader can check by eye.
 * Residuals against each input second, because structure left in the residual is the evidence that
 * the expression is missing a term, and a parity plot hides it. Extrapolation third, because it is
 * where the benchmark literature says every method degrades and it is the panel almost no tool
 * ships. Partial dependence last, as the summary of shape rather than of error.
 */
import { scaleLinear } from 'd3-scale';
import { useMemo, useState } from 'react';

import type { ValidationPayload } from '../lib/contract.types';
import { ExtrapolationPlot, ParityPlot, PartialDependence } from './ModelValidation';

const W = 300;
const H = 180;
const PAD = { top: 14, right: 12, bottom: 32, left: 46 };

/**
 * Residuals against one input. A flat, structureless band means the expression captured what that
 * variable does. A curve, a fan or a step means it did not, and that is a specific, actionable
 * finding rather than a global error number.
 */
function ResidualScatter({
  name,
  x: xs,
  residual,
  lang,
}: {
  name: string;
  x: number[];
  residual: number[];
  lang: 'en' | 'es';
}) {
  const points = useMemo(
    () =>
      xs
        .map((v, i) => ({ v, r: residual[i] }))
        .filter((d) => Number.isFinite(d.v) && Number.isFinite(d.r)),
    [xs, residual],
  );

  if (points.length === 0) {
    return (
      <figure className="sym-resid">
        <figcaption>{name}</figcaption>
        <p className="sym-empty">
          {lang === 'es' ? 'Sin residuos finitos.' : 'No finite residuals.'}
        </p>
      </figure>
    );
  }

  const vs = points.map((d) => d.v);
  const rs = points.map((d) => d.r);
  const bound = Math.max(Math.abs(Math.min(...rs)), Math.abs(Math.max(...rs))) || 1;
  const x = scaleLinear().domain([Math.min(...vs), Math.max(...vs)]).range([PAD.left, W - PAD.right]);
  const y = scaleLinear().domain([-bound, bound]).range([H - PAD.bottom, PAD.top]);

  return (
    <figure className="sym-resid">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label={
          lang === 'es' ? `Residuos frente a ${name}` : `Residuals against ${name}`
        }
      >
        <line className="sym-zero-line" x1={PAD.left} x2={W - PAD.right} y1={y(0)} y2={y(0)} />
        {points.map((d, i) => (
          <circle key={i} className="sym-resid-point" cx={x(d.v)} cy={y(d.r)} r={1.9} />
        ))}
        <text className="sym-axis-label" x={PAD.left - 6} y={y(bound)} dy="0.32em" textAnchor="end">
          {bound.toExponential(0)}
        </text>
        <text className="sym-axis-label" x={PAD.left - 6} y={y(-bound)} dy="0.32em" textAnchor="end">
          {(-bound).toExponential(0)}
        </text>
      </svg>
      <figcaption>{name}</figcaption>
    </figure>
  );
}

export function ValidationPanel({
  validation,
  lang,
}: {
  validation: ValidationPayload;
  lang: 'en' | 'es';
}) {
  const es = lang === 'es';
  const residuals = Object.entries(validation.residuals_by_input ?? {});
  const [showAllResiduals, setShowAllResiduals] = useState(false);
  const shownResiduals = showAllResiduals ? residuals : residuals.slice(0, 6);

  return (
    <div className="sym-validation">
      <section className="sym-block">
        <h3>{es ? 'Paridad' : 'Parity'}</h3>
        <p className="sym-block-lede">
          {es
            ? 'Valor predicho frente a valor medido. Los puntos de prueba estan resaltados: son las filas que la busqueda nunca vio.'
            : 'Predicted against measured. Test points are highlighted: those are the rows the search never saw.'}
        </p>
        <ParityPlot validation={validation} lang={lang} />
      </section>

      <section className="sym-block">
        <h3>{es ? 'Residuos frente a cada entrada' : 'Residuals against each input'}</h3>
        <p className="sym-block-lede">
          {es
            ? 'Una banda plana y sin estructura significa que la expresion capturo lo que hace esa variable. Una curva, un abanico o un escalon significan que no, y eso es un hallazgo concreto: falta un termino. Un grafico de paridad lo esconde.'
            : 'A flat, structureless band means the expression captured what that variable does. A curve, a fan or a step means it did not, and that is a concrete finding: a term is missing. A parity plot hides it.'}
        </p>
        {residuals.length === 0 ? (
          <p className="sym-empty">
            {es ? 'Sin residuos por entrada en este artefacto.' : 'No per-input residuals in this artifact.'}
          </p>
        ) : (
          <>
            <div className="sym-resid-grid">
              {shownResiduals.map(([name, entry]) => (
                <ResidualScatter
                  key={name}
                  name={name}
                  x={entry.x}
                  residual={entry.residual}
                  lang={lang}
                />
              ))}
            </div>
            {residuals.length > 6 && (
              <button
                type="button"
                className="chip"
                onClick={() => setShowAllResiduals((v) => !v)}
              >
                {showAllResiduals
                  ? es ? 'mostrar menos' : 'show fewer'
                  : es
                    ? `mostrar las ${residuals.length} entradas`
                    : `show all ${residuals.length} inputs`}
              </button>
            )}
          </>
        )}
      </section>

      <section className="sym-block">
        <h3>{es ? 'Fuera del soporte de entrenamiento' : 'Outside the training support'}</h3>
        <p className="sym-block-lede">
          {es
            ? 'La banda sombreada es el rango sobre el que se ajusto. Fuera de ella nada restringio la expresion, y ahi es donde la literatura de benchmarks dice que todos los metodos se degradan.'
            : 'The shaded band is the range it was fitted over. Outside it nothing constrained the expression, and that is where the benchmark literature says every method degrades.'}
        </p>
        <ExtrapolationPlot validation={validation} lang={lang} />
      </section>

      <section className="sym-block">
        <h3>{es ? 'Dependencia parcial' : 'Partial dependence'}</h3>
        <p className="sym-block-lede">
          {es
            ? 'La forma que la expresion asigna a cada variable con las demas promediadas. Es un resumen de forma, no de error.'
            : 'The shape the expression assigns to each variable with the others averaged out. A summary of shape, not of error.'}
        </p>
        <PartialDependence validation={validation} lang={lang} />
      </section>
    </div>
  );
}
