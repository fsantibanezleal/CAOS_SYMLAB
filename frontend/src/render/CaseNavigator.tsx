/**
 * The case navigator: source lane, category, case. Three controls, in that order.
 *
 * Why this rather than the shell `CaseSelector`: that component renders a chip deck, one chip per
 * case under a heading per category. That shape is right for a deck of six or eight cases. This lab
 * publishes dozens (two registry entries are SUITES that bake out to one case per member, eighteen
 * Feynman and seven Strogatz), and in a sidebar the deck becomes a wall of chips
 * with no ordering a reader can hold in their head. So the same information is bound to native
 * `<select>` elements: category narrows, case picks, and the sidebar stays one screen tall no
 * matter how many cases the registry grows to.
 *
 * Everything the shell contract provides is preserved: the source lane control, the `?case=` deep
 * link, the validation anchor for the selected case, and the locked-knobs note when the active lane
 * is measured data rather than a generator.
 */
import { useEffect, useMemo } from 'react';

import type { IndexEntry } from '../lib/contract.types';

export type SourceLane = 'synthetic' | 'real';

export interface CaseNavigatorProps {
  entries: IndexEntry[];
  selectedId: string;
  onSelect: (id: string) => void;
  source: SourceLane;
  onSourceChange: (lane: SourceLane) => void;
  lang: 'en' | 'es';
}

const CASE_PARAM = 'case';

export function CaseNavigator({
  entries,
  selectedId,
  onSelect,
  source,
  onSourceChange,
  lang,
}: CaseNavigatorProps) {
  const es = lang === 'es';

  /**
   * The lane of a case, with anything unrecognised resolved to the generator lane rather than
   * dropped. An index entry whose lane this component does not offer would be unreachable in the
   * app while the catalogue still counted it as published, which is worse than putting it in the
   * slightly wrong lane.
   */
  const laneOf = (entry: IndexEntry): SourceLane =>
    entry.real_or_synthetic === 'real' ? 'real' : 'synthetic';

  /** Which lanes actually carry published cases. A lane with nothing in it is not offered. */
  const lanes = useMemo(() => {
    const present = new Set(entries.map(laneOf));
    return (['synthetic', 'real'] as SourceLane[]).filter((l) => present.has(l));
  }, [entries]);

  const inLane = useMemo(() => entries.filter((e) => laneOf(e) === source), [entries, source]);

  /** Category order is first-seen, matching the registry, so it is stable between deploys. The
   *  Spanish name comes from the index rather than from a lookup table here: the taxonomy belongs
   *  to the registry, and a second copy in the frontend would drift the first time one is added. */
  const categories = useMemo(() => {
    const seen = new Map<string, { code: string; name: string; n: number }>();
    inLane.forEach((e) => {
      const existing = seen.get(e.category);
      if (existing) {
        existing.n += 1;
      } else {
        const name = (es ? e.category_name_es : e.category_name) ?? e.category_name ?? e.category;
        seen.set(e.category, { code: e.category, name, n: 1 });
      }
    });
    return [...seen.values()];
  }, [inLane, es]);

  const selected = entries.find((e) => e.case_id === selectedId) ?? null;
  const activeCategory =
    selected && laneOf(selected) === source ? selected.category : (categories[0]?.code ?? '');

  const casesInCategory = useMemo(
    () => inLane.filter((e) => e.category === activeCategory),
    [inLane, activeCategory],
  );

  /** Keep the selection inside the visible lane and category rather than leaving a stale id that
   *  renders an empty panel. A silently empty panel is indistinguishable from a genuine null. */
  useEffect(() => {
    if (inLane.length === 0) return;
    if (!inLane.some((e) => e.case_id === selectedId)) {
      onSelect(inLane[0].case_id);
    }
  }, [inLane, selectedId, onSelect]);

  /** Deep link, so a case can be shared as a URL. */
  useEffect(() => {
    if (!selectedId) return;
    const url = new URL(window.location.href);
    if (url.searchParams.get(CASE_PARAM) !== selectedId) {
      url.searchParams.set(CASE_PARAM, selectedId);
      window.history.replaceState(null, '', url.toString());
    }
  }, [selectedId]);

  return (
    <section className="sym-nav" aria-label={es ? 'Seleccion de caso' : 'Case selection'}>
      <div className="sym-nav-field">
        <span className="sym-nav-label">{es ? 'Origen de los datos' : 'Data source'}</span>
        <div className="sym-lane" role="radiogroup" aria-label={es ? 'Origen' : 'Source'}>
          {lanes.map((lane) => (
            <button
              key={lane}
              type="button"
              role="radio"
              aria-checked={source === lane}
              className={`sym-lane-button${source === lane ? ' on' : ''}`}
              onClick={() => onSourceChange(lane)}
            >
              {lane === 'synthetic'
                ? es ? 'Generador' : 'Generator'
                : es ? 'Datos medidos' : 'Measured data'}
            </button>
          ))}
        </div>
      </div>

      <label className="sym-nav-field">
        <span className="sym-nav-label">{es ? 'Categoria' : 'Category'}</span>
        <select
          className="sym-select"
          value={activeCategory}
          onChange={(event) => {
            const first = inLane.find((e) => e.category === event.target.value);
            if (first) onSelect(first.case_id);
          }}
        >
          {categories.map((c) => (
            <option key={c.code} value={c.code}>
              {c.name} ({c.n})
            </option>
          ))}
        </select>
      </label>

      <label className="sym-nav-field">
        <span className="sym-nav-label">{es ? 'Caso' : 'Case'}</span>
        <select
          className="sym-select"
          value={selectedId}
          onChange={(event) => onSelect(event.target.value)}
        >
          {casesInCategory.map((e) => (
            <option key={e.case_id} value={e.case_id}>
              {es ? e.name_es : e.name_en}
            </option>
          ))}
        </select>
      </label>

      {selected && (
        <p className="sym-nav-anchor">
          {selected.ground_truth_known
            ? es
              ? 'La ley verdadera se conoce, asi que la recuperacion es comprobable.'
              : 'The true law is known, so recovery is checkable.'
            : es
              ? 'Sin forma cerrada publicada: contribuye solo a las metricas de error.'
              : 'No published closed form: contributes to the error metrics only.'}
        </p>
      )}

      {source === 'real' && (
        <p className="sym-nav-anchor">
          {es
            ? 'Los casos medidos vienen de una planta o un instrumento real: no hay parametros que ajustar, solo lo que se registro.'
            : 'Measured cases come from a real plant or instrument: there are no knobs to turn, only what was recorded.'}
        </p>
      )}
    </section>
  );
}
