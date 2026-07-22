/**
 * The TypeScript mirror of CONTRACT 2, the pipeline-to-web payload.
 *
 * This file exists so that a drift between what the Python exporter writes and what the app expects
 * fails the BUILD rather than producing a blank panel at runtime. If a field is renamed on the
 * Python side and not here, `tsc --noEmit` stops the deploy.
 *
 * The schema is frozen at 1.0.0 and was written before any of this user interface existed, which is
 * deliberate: every view in the app is a pure function of this payload, so there is exactly one
 * place a number can be wrong.
 */

/** Bumping the MAJOR component is a breaking change and must be matched on both sides. */
export const SUPPORTED_SCHEMA_MAJOR = 1;

export interface InputDescriptor {
  key: string;
  display: string;
  unit: string;
  dims: number[];
  min: number;
  max: number;
  mean: number;
  std: number;
}

/** The full row accounting. `n_rows` alone is the TRAINING count and on its own contradicts the
 *  case description, which quotes the size of the published dataset. */
export interface RowAccounting {
  /** Rows the source carried, before any subsample. Null for artifacts baked before this shipped. */
  source: number | null;
  used: number;
  train: number;
  test: number;
  extrapolation: number;
}

export interface DatasetDescriptor {
  name: string;
  /** The TRAINING row count. Prefer `rows` when present. */
  n_rows: number;
  rows?: RowAccounting;
  n_inputs: number;
  real_or_synthetic: 'real' | 'synthetic';
  source: string | null;
  license: string | null;
  inputs: InputDescriptor[];
  target: InputDescriptor & { key: string };
}

/** One node of the flat expression-tree list. Flat, not nested: it serialises smaller, diffs
 *  cleanly, and the hierarchy is rebuilt in one call from `parent`. */
export interface TreeNode {
  id: number;
  parent: number | null;
  kind: 'op_binary' | 'op_unary' | 'var' | 'const';
  label: string;
  arity: number;
  depth: number;
  subtree_size: number;
  /** Normalised drop in R-squared when this subtree is replaced by its mean. Defined once in the
   *  pipeline and reused by every view that encodes importance, so node radius, term ordering and
   *  band ordering cannot disagree. */
  influence: number;
  mean_value: number | null;
  abs_value_p95: number | null;
  term_id: number | null;
  value?: number;
  var_index?: number;
  unit_ok?: boolean;
  unit_dims?: number[] | null;
  unit_label?: string | null;
}

export interface TreePayload {
  nodes: TreeNode[];
  max_depth: number;
  n_nodes: number;
}

/** A top-level additive term. `color_index` is assigned in Python so the equation, the tree and the
 *  contribution chart all read one ordering and their palettes cannot drift apart. */
export interface TermEntry {
  term_id: number;
  node_id: number | null;
  latex: string;
  mean_abs_contrib: number;
  var_share: number;
  complexity: number;
  color_index: number;
}

export interface DescriptionLengthParts {
  total: number;
  structure: number;
  constants: number;
  residuals: number;
}

export interface RoundingReport {
  sig_digits: number;
  tolerance: number;
  /** The relative error the rounding actually introduced, measured on the real rows. */
  max_rel_error: number | null;
  /** False means the rounding was REFUSED because it would have changed the model. */
  accepted: boolean;
}

export interface ParetoMember {
  index: number;
  complexity: number;
  complexity_weighted: number;
  description_length: DescriptionLengthParts;
  bic: number | null;
  loss_train: number | null;
  loss_test: number | null;
  r2_train: number | null;
  r2_test: number | null;
  score: number;
  on_front: boolean;
  raw_string: string;
  /** What the engine actually produced. Shipped alongside the prettified form on purpose. */
  latex_raw: string;
  /** Carries `\htmlData{nid=N}` node ids and `\htmlClass{sym-term-N}` colour classes. */
  latex_pretty: string;
  latex_aligned: string;
  rounding: RoundingReport;
  tree: TreePayload;
  terms: TermEntry[];
  variables_used: number[];
  n_variables_available: number;
  operator_counts: Record<string, number>;
  units_ok: boolean | null;
  units_reason: string;
}

export interface HistoryPayload {
  generation: number[];
  evals: number[];
  best_loss: (number | null)[];
  mean_loss: (number | null)[];
  worst_loss: (number | null)[];
  diversity: {
    structural: number[];
    semantic: number[];
    operator_entropy: number[];
  };
  operator_freq: { ops: string[]; matrix: number[][] };
  islands: { id: number; best_loss: (number | null)[]; size: number[] }[];
  migrations: {
    generation: number;
    from: number;
    to: number;
    count: number;
    mean_fitness_delta: number;
  }[];
}

export interface ValidationPayload {
  parity?: {
    y_true: number[];
    y_pred: (number | null)[];
    split: number[];
    /** Both counts always ship, so a downsample is disclosed rather than implied. */
    n_shown: number;
    n_total: number;
  };
  residuals_by_input?: Record<string, { x: number[]; residual: number[] }>;
  pdp?: { var: string; grid: number[]; mean: (number | null)[]; support: [number, number] }[];
  extrapolation?: {
    var: string;
    grid: number[];
    support: [number, number];
    y: (number | null)[];
    /** How many probe points the expression was undefined at. Counted, never dropped. */
    n_nonfinite: number;
  }[];
  term_contributions?: {
    sort_key: string;
    order: number[];
    terms: { term_id: number; values: number[] }[];
  };
}

export interface VariantScore {
  variant_id: string;
  label: string;
  seconds: number;
  evaluations: number;
  duplicates_avoided: number;
  invalid_rejected: number;
  front_size: number;
  best_train_mse: number | null;
  best_test_mse: number | null;
  best_test_r2: number | null;
  best_extrapolation_mse: number | null;
  /** Clearing the accuracy threshold. NOT the same claim as recovering the right expression. */
  accuracy_solution: boolean;
  selected_index: number;
  selected_complexity: number;
  selected_description_length: number;
  n_irrelevant_features: number;
  equivalence: {
    symbolic: boolean | null;
    symbolic_error: string;
    numerical: boolean | null;
    numerical_max_rel_error: number | null;
    structural_distance: number | null;
    agreed: boolean;
    disagreement_note: string;
  } | null;
  notes: string[];
}

export interface VariantConfig {
  /** Null for a non-GP family, which has neither. Exporting the ladder's numbers for an arm that
   *  never ran a population would put figures in the audit record describing a search that did not
   *  happen. */
  population: number | null;
  generations: number | null;
  primitive_set: string;
  linear_scaling: boolean;
  interval_guard: boolean;
  constant_tuning: boolean;
  multi_objective: boolean;
  epsilon_lexicase: boolean;
  age_fitness: boolean;
  n_islands: number;
  dedup: boolean;
  unit_typed: boolean;
  parsimony_coefficient: number;
}

export interface VariantPayload {
  id: string;
  /** Which search FAMILY this variant belongs to. "gp" is a rung of the genetic-programming
   *  ladder, where each entry adds one mechanism to the one above it. Anything else is a separate
   *  family and must not be presented as a further step along that ladder. */
  method?: string;
  label_en: string;
  label_es: string;
  note_en: string;
  note_es: string;
  config: VariantConfig;
  pareto: ParetoMember[];
  /** Both counts ship, so an export cap is disclosed rather than implied. */
  pareto_exported: number;
  pareto_total: number;
  selected_index: number;
  history: HistoryPayload;
  validation: ValidationPayload;
  score: VariantScore;
  seconds: number;
}

export interface SamplingEntry {
  key: string;
  display: string;
  unit: string;
  dims: number[];
  dims_label: string;
  min: number;
  max: number;
  mean: number;
  std: number;
  decades_spanned: number | null;
  guard_low: number;
  guard_high: number;
}

export interface Certificate {
  statement: string;
  caveats: string[];
  /** The ingestion contract's own warnings, carried into the web payload rather than only into the
   *  audit manifest. A leakage warning the pipeline raised is useless to the one reader who most
   *  needs it if it only exists in a file the app never opens. */
  contract_warnings?: string[];
  /** What the loader had to do to the data on the way in: rows dropped, folds ignored, aggregation
   *  applied. Recorded verbatim rather than tidied away. */
  defects_applied?: string[];
  /** False means the enumeration was truncated and the completeness claim does NOT hold. */
  complete: boolean;
  n_enumerated: number;
  n_admissible: number;
  max_nodes: number;
  best_infix?: string;
  best_mse?: number;
}

export interface CaseSummary {
  n_variants: number;
  accuracy_solutions: number;
  /** Reported separately from recovery, always. The gap between them is the headline measurement. */
  accuracy_solution_rate: number;
  exact_recoveries: number;
  exact_recovery_rate: number | null;
  mean_structural_distance: number | null;
  /** A property of the SCORER, not of the method. Published rather than absorbed. */
  symbolic_test_failure_rate: number | null;
  test_disagreement_count: number;
  total_seconds: number;
  total_evaluations: number;
  variants_with_irrelevant_features: number;
}

export interface CaseNotes {
  case_id: string;
  category: string;
  category_name: string;
  /** The Spanish category name, produced by the registry so the taxonomy is bilingual at source. */
  category_name_es?: string;
  name_en: string;
  name_es: string;
  summary_en: string;
  summary_es: string;
  ground_truth_known: boolean;
  ground_truth_latex: string | null;
  /** True when a machine-comparable law exists, so recovery is scoreable at all. Distinct from
   *  `ground_truth_known`: a case can have a law we can print but not one we can compare against. */
  ground_truth_available?: boolean;
  /** "structure" when the physical parameters were given as input columns, so only the form was
   *  unknown; "structure+constants" when the numbers had to be recovered too. */
  regime?: string;
  real_or_synthetic: 'real' | 'synthetic';
  caveats: string[];
  /** The ingestion contract's own warnings, carried into the web payload rather than only into the
   *  audit manifest. A leakage warning the pipeline raised is useless to the one reader who most
   *  needs it if it only exists in a file the app never opens. */
  contract_warnings?: string[];
  /** What the loader had to do to the data on the way in: rows dropped, folds ignored, aggregation
   *  applied. Recorded verbatim rather than tidied away. */
  defects_applied?: string[];
  split_note: string;
  features_note: string;
  sampling: SamplingEntry[];
  variants: VariantPayload[];
  summary: CaseSummary;
  certificate: Certificate | null;
  max_exported_members: number;
}

export interface RunPayload {
  schema_version: string;
  run_id: string;
  dataset: DatasetDescriptor;
  engine: {
    name: string;
    version: string;
    seed: number;
    primitive_set: string;
    deterministic: boolean;
  };
  notes: CaseNotes;
}

export interface IndexEntry {
  case_id: string;
  category: string;
  /** The human category name. The sidebar must never render the raw single-letter code. */
  category_name: string;
  /** The Spanish category name. The taxonomy is a property of the registry, so both languages are
   *  produced there rather than translated in the frontend, where a second copy would drift. */
  category_name_es?: string;
  name_en: string;
  name_es: string;
  ground_truth_known: boolean;
  real_or_synthetic: 'real' | 'synthetic' | 'unknown';
  manifest_path: string;
  artifact_path: string;
  bytes: number;
  n_variants: number;
  summary: CaseSummary;
}

export interface CaseIndex {
  schema: string;
  schema_version: string;
  engine_version: string;
  generated_on: string;
  n_cases: number;
  coverage: {
    n_cases: number;
    n_categories: number;
    categories: Record<string, number>;
    ground_truth_known: number;
    real: number;
    synthetic: number;
    total_variants: number;
    min_variants: number;
    max_variants: number;
  };
  cases: IndexEntry[];
}

/**
 * Refuse to render a payload whose major version this build does not know.
 *
 * Visibly, with a message, rather than by rendering a blank panel: a schema mismatch that shows an
 * empty chart is indistinguishable from a genuine empty result, and that ambiguity is exactly what
 * this contract exists to remove.
 */
export function assertSchemaSupported(schemaVersion: string, source: string): void {
  const major = Number.parseInt(schemaVersion.split('.')[0] ?? '', 10);
  if (Number.isNaN(major) || major !== SUPPORTED_SCHEMA_MAJOR) {
    throw new Error(
      `${source} declares schema ${schemaVersion}, but this build understands major ` +
        `${SUPPORTED_SCHEMA_MAJOR}. Refusing to render rather than showing an empty panel.`,
    );
  }
}
