/**
 * A thin uPlot wrapper for the dense search-history charts.
 *
 * uPlot for these and hand-rolled SVG for the Pareto front is a deliberate split, not an
 * inconsistency: the history charts are many points with a standard cursor readout, which is exactly
 * what uPlot is fastest at, while the front needs click-to-load and cross-highlighting, which a
 * chart library fights.
 *
 * Series colours are read from CSS custom properties at mount and re-read on theme change, because a
 * canvas cannot resolve a CSS variable on its own. That is the trap this wrapper exists to absorb
 * once rather than in every chart.
 */
import { useEffect, useRef } from 'react';
import uPlot from 'uplot';
import 'uplot/dist/uPlot.min.css';

export interface UPlotChartProps {
  data: uPlot.AlignedData;
  series: { label: string; cssVar: string }[];
  xLabel: string;
  yLabel: string;
  logY?: boolean;
  height?: number;
  ariaLabel: string;
}

function readVar(name: string, fallback: string): string {
  if (typeof window === 'undefined') return fallback;
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || fallback;
}

const FALLBACKS = ['#4f7cff', '#e0733d', '#2fa37a', '#8b5cd6'];

export function UPlotChart({
  data,
  series,
  xLabel,
  yLabel,
  logY = false,
  height = 260,
  ariaLabel,
}: UPlotChartProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const plotRef = useRef<uPlot | null>(null);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;

    const build = () => {
      plotRef.current?.destroy();
      const width = host.clientWidth || 640;
      const options: uPlot.Options = {
        width,
        height,
        cursor: { drag: { x: true, y: false } },
        scales: { y: logY ? { distr: 3 } : {} },
        axes: [
          { label: xLabel, stroke: readVar('--color-fg-subtle', '#888'),
            grid: { stroke: readVar('--color-border', '#3333') } },
          { label: yLabel, stroke: readVar('--color-fg-subtle', '#888'),
            grid: { stroke: readVar('--color-border', '#3333') } },
        ],
        series: [
          {},
          ...series.map((s, i) => ({
            label: s.label,
            stroke: readVar(s.cssVar, FALLBACKS[i % FALLBACKS.length]),
            width: 2,
            spanGaps: true,
          })),
        ],
      };
      plotRef.current = new uPlot(options, data, host);
    };

    build();

    // Re-read the palette when the theme flips. The canvas holds resolved colours, not variables.
    const observer = new MutationObserver(build);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    const onResize = () => plotRef.current?.setSize({ width: host.clientWidth || 640, height });
    window.addEventListener('resize', onResize);

    return () => {
      observer.disconnect();
      window.removeEventListener('resize', onResize);
      plotRef.current?.destroy();
      plotRef.current = null;
    };
  }, [data, series, xLabel, yLabel, logY, height]);

  return <div ref={hostRef} className="sym-uplot" role="img" aria-label={ariaLabel} />;
}
