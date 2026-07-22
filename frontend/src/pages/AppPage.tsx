/**
 * The App: the workbench, one case at a time.
 *
 * Structure is fixed by the product standard and mirrored from the exemplar lab: a case selector, a
 * variant bar of pre-baked configurations, then four sub-tabs. What differs here is what each one
 * means for symbolic regression:
 *
 * - **Field** is the discovered EXPRESSION: rendered as mathematics, as an interactive tree, and as
 *   the model-validation views that decide whether it is worth anything.
 * - **Live** re-runs a real reduced search in the browser on the selected case.
 * - **Charts** is the accuracy-versus-complexity Pareto front, where clicking a point loads that
 *   expression into Field.
 * - **Context** is the deep bilingual write-up.
 *
 * The variant bar is the ablation. Each chip differs from its neighbour by exactly ONE mechanism, so
 * moving along it attributes a measured difference to a named change rather than to a bundle.
 */
import { Callout, SubTabs } from '@fasl-work/caos-app-shell';
import { useEffect, useMemo, useState } from 'react';

import { loadIndex, loadRun } from '../lib/data';
import type { CaseIndex, RunPayload, VariantPayload } from '../lib/contract.types';
import { useLang } from '../lib/useLang';
import { EquationView } from '../render/EquationView';
import { ExpressionTree } from '../render/ExpressionTree';
import { ExtrapolationPlot, ParityPlot, PartialDependence } from '../render/ModelValidation';
import { ParetoFront } from '../render/ParetoFront';
import { SearchHistory } from '../render/SearchHistory';
import { LiveLane } from './workbench/LiveLane';
import { CaseContext } from './workbench/CaseContext';

export default function AppPage() {
  const lang = useLang();
  const [index, setIndex] = useState<CaseIndex | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [caseId, setCaseId] = useState<string | null>(null);
  const [run, setRun] = useState<RunPayload | null>(null);
  const [variantIndex, setVariantIndex] = useState(0);
  const [memberIndex, setMemberIndex] = useState<number | null>(null);
  const [activeNodeId, setActiveNodeId] = useState<number | null>(null);
  const [longForm, setLongForm] = useState(false);
  const [showRaw, setShowRaw] = useState(false);
  const [collapse, setCollapse] = useState(0);

  useEffect(() => {
    loadIndex()
      .then((loaded) => {
        setIndex(loaded);
        if (loaded.cases.length > 0) setCaseId(loaded.cases[0].case_id);
      })
      .catch((err) => setError(String(err)));
  }, []);

  useEffect(() => {
    if (!caseId) return;
    setRun(null);
    setMemberIndex(null);
    setVariantIndex(0);
    loadRun(caseId)
      .then(setRun)
      .catch((err) => setError(String(err)));
  }, [caseId]);

  const variant: VariantPayload | null = useMemo(() => {
    if (!run) return null;
    const variants = run.notes.variants;
    if (variants.length === 0) return null;
    return variants[Math.min(variantIndex, variants.length - 1)];
  }, [run, variantIndex]);

  const member = useMemo(() => {
    if (!variant || variant.pareto.length === 0) return null;
    const target = memberIndex ?? variant.selected_index;
    return variant.pareto[Math.min(target, variant.pareto.length - 1)] ?? variant.pareto[0];
  }, [variant, memberIndex]);

  if (error) {
    return (
      <div className="page-body">
        <Callout variant="honest" title={lang === 'es' ? 'No se pudieron cargar los artefactos' : 'Artifacts could not be loaded'}>
          <p>{error}</p>
          <p>
            {lang === 'es'
              ? 'Los artefactos se generan sin conexion y se publican junto a la aplicacion. Si esta viendo esto, el horneado aun no ha terminado para este despliegue.'
              : 'Artifacts are generated offline and published alongside the app. If you are seeing this, the bake has not completed for this deployment.'}
          </p>
        </Callout>
      </div>
    );
  }

  if (!index) {
    return (
      <div className="page-body">
        <p className="sym-loading">{lang === 'es' ? 'Cargando el catalogo de casos...' : 'Loading the case catalogue...'}</p>
      </div>
    );
  }

  const grouped = index.cases.reduce<Record<string, typeof index.cases>>((acc, entry) => {
    (acc[entry.category] ??= []).push(entry);
    return acc;
  }, {});

  const subTabs = [
    {
      id: 'field',
      label: lang === 'es' ? 'Expresion' : 'Expression',
      content:
        member && variant ? (
          <div className="sym-field">
            <div className="sym-field-controls">
              <button type="button" className={`chip${longForm ? ' on' : ''}`} onClick={() => setLongForm((v) => !v)}>
                {lang === 'es' ? 'forma larga' : 'long form'}
              </button>
              <button type="button" className={`chip${showRaw ? ' on' : ''}`} onClick={() => setShowRaw((v) => !v)}>
                {lang === 'es' ? 'salida cruda del motor' : 'raw engine output'}
              </button>
              <label className="sym-slider">
                {lang === 'es' ? 'colapsar bajo influencia' : 'collapse below influence'}
                <input
                  type="range"
                  min={0}
                  max={0.3}
                  step={0.01}
                  value={collapse}
                  onChange={(event) => setCollapse(Number(event.target.value))}
                />
                <output>{collapse.toFixed(2)}</output>
              </label>
            </div>

            <EquationView
              member={member}
              targetSymbol={run?.dataset.target.display ?? 'y'}
              activeNodeId={activeNodeId}
              onHoverNode={setActiveNodeId}
              longForm={longForm}
              showRaw={showRaw}
              lang={lang}
            />

            <h3>{lang === 'es' ? 'La estructura detras de la formula' : 'The structure behind the formula'}</h3>
            <ExpressionTree
              payload={member.tree}
              activeNodeId={activeNodeId}
              onHoverNode={setActiveNodeId}
              collapseBelowInfluence={collapse}
              lang={lang}
            />

            <h3>{lang === 'es' ? 'Paridad y residuos' : 'Parity and residuals'}</h3>
            <ParityPlot validation={variant.validation} lang={lang} />

            <h3>{lang === 'es' ? 'Comportamiento fuera del soporte' : 'Behaviour outside the support'}</h3>
            <ExtrapolationPlot validation={variant.validation} lang={lang} />

            <h3>{lang === 'es' ? 'Dependencia parcial' : 'Partial dependence'}</h3>
            <PartialDependence validation={variant.validation} lang={lang} />
          </div>
        ) : (
          <p className="sym-empty">{lang === 'es' ? 'Sin expresion seleccionada.' : 'No expression selected.'}</p>
        ),
    },
    {
      id: 'live',
      label: lang === 'es' ? 'En vivo (tu navegador)' : 'Live (your browser)',
      content: run ? <LiveLane run={run} lang={lang} /> : null,
    },
    {
      id: 'charts',
      label: lang === 'es' ? 'Frente y busqueda' : 'Front and search',
      content:
        variant && member ? (
          <div className="sym-charts">
            <h3>{lang === 'es' ? 'Frente exactitud frente a complejidad' : 'Accuracy against complexity'}</h3>
            <ParetoFront
              members={variant.pareto}
              selectedIndex={variant.selected_index}
              activeIndex={member.index}
              onSelect={setMemberIndex}
              exported={variant.pareto_exported}
              total={variant.pareto_total}
              lang={lang}
            />
            <h3>{lang === 'es' ? 'Progreso de la busqueda' : 'Search progress'}</h3>
            <SearchHistory history={variant.history} score={variant.score} lang={lang} />
          </div>
        ) : null,
    },
    {
      id: 'context',
      label: lang === 'es' ? 'Contexto' : 'Context',
      content: run ? <CaseContext run={run} lang={lang} /> : null,
    },
  ];

  return (
    <div className="page-body symlab-layout">
      <aside className="symlab-side">
        <h2>{lang === 'es' ? 'Casos' : 'Cases'}</h2>
        <p className="sym-side-note">
          {lang === 'es'
            ? `${index.coverage.n_cases} casos en ${index.coverage.n_categories} categorias, ${index.coverage.real} sobre datos reales medidos.`
            : `${index.coverage.n_cases} cases across ${index.coverage.n_categories} categories, ${index.coverage.real} on real measured data.`}
        </p>
        {Object.entries(grouped).map(([category, entries]) => (
          <div key={category} className="sym-case-group">
            <h3>{entries[0]?.case_id ? category : category}</h3>
            <ul>
              {entries.map((entry) => (
                <li key={entry.case_id}>
                  <button
                    type="button"
                    className={`sym-case-button${entry.case_id === caseId ? ' on' : ''}`}
                    onClick={() => setCaseId(entry.case_id)}
                  >
                    {entry.case_id}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))}

        {run && (
          <div className="sym-live-readout">
            <h3>{lang === 'es' ? 'Lectura del caso' : 'Case readout'}</h3>
            <dl>
              <dt>{lang === 'es' ? 'filas' : 'rows'}</dt>
              <dd>{run.dataset.n_rows.toLocaleString()}</dd>
              <dt>{lang === 'es' ? 'entradas' : 'inputs'}</dt>
              <dd>{run.dataset.n_inputs}</dd>
              <dt>{lang === 'es' ? 'origen' : 'origin'}</dt>
              <dd>{run.dataset.real_or_synthetic === 'real' ? (lang === 'es' ? 'medido' : 'measured') : (lang === 'es' ? 'sintetico' : 'synthetic')}</dd>
              <dt>{lang === 'es' ? 'tasa de exactitud' : 'accuracy rate'}</dt>
              <dd>{(run.notes.summary.accuracy_solution_rate * 100).toFixed(0)}%</dd>
              <dt>{lang === 'es' ? 'tasa de recuperacion' : 'recovery rate'}</dt>
              <dd>
                {run.notes.summary.exact_recovery_rate === null
                  ? lang === 'es'
                    ? 'no comprobable'
                    : 'not checkable'
                  : `${(run.notes.summary.exact_recovery_rate * 100).toFixed(0)}%`}
              </dd>
            </dl>
            <p className="sym-gap-note">
              {lang === 'es'
                ? 'Las dos tasas se reportan por separado, siempre. La brecha entre ellas es la medicion mas importante de este laboratorio.'
                : 'The two rates are reported separately, always. The gap between them is this lab’s most important measurement.'}
            </p>
          </div>
        )}
      </aside>

      <main className="symlab-main">
        {!run ? (
          <p className="sym-loading">{lang === 'es' ? 'Cargando el caso...' : 'Loading the case...'}</p>
        ) : (
          <>
            <div className="page-head">
              <h1>{lang === 'es' ? run.notes.name_es : run.notes.name_en}</h1>
              <p className="lede">{lang === 'es' ? run.notes.summary_es : run.notes.summary_en}</p>
            </div>

            <div className="variant-bar">
              <span className="variant-bar-label">
                {lang === 'es' ? 'variantes' : 'variants'} ({run.notes.variants.length})
                {' · '}
                {lang === 'es' ? 'reproducido' : 'replayed'}
              </span>
              <div className="variant-chips">
                {run.notes.variants.map((v, i) => (
                  <button
                    key={v.id}
                    type="button"
                    className={`variant-chip${i === variantIndex ? ' active' : ''}`}
                    onClick={() => {
                      setVariantIndex(i);
                      setMemberIndex(null);
                    }}
                  >
                    {lang === 'es' ? v.label_es : v.label_en}
                  </button>
                ))}
              </div>
              {variant && (
                <p className="variant-note">{lang === 'es' ? variant.note_es : variant.note_en}</p>
              )}
            </div>

            <SubTabs tabs={subTabs} ariaLabel={lang === 'es' ? 'Vistas del caso' : 'Case views'} />
          </>
        )}
      </main>
    </div>
  );
}
