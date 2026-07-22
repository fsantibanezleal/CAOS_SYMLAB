/**
 * The expression tree: the structure behind the formula.
 *
 * Symbolic regression produces three things that need to be seen, and most tooling shows only the
 * first: the formula, the structure behind it, and the search that earned it. This is the second.
 *
 * Implementation decisions, each argued rather than defaulted:
 *
 * - **`d3-hierarchy` for layout, a hand-rolled inline SVG for rendering.** An expression tree is a
 *   strict rooted tree with arity at most two, which is exactly the case `d3.tree()` solves
 *   optimally (Reingold-Tilford as improved by Buchheim et al., 2002) at 5.6 KB gzipped. The
 *   general graph libraries were measured and rejected: one of them is 433 KB gzipped under a dual
 *   copyleft licence, which is six times the whole rest of this app's visualisation stack.
 * - **Inline SVG, not canvas, up to a few hundred nodes.** Inline SVG inherits CSS custom
 *   properties, so the tree repaints correctly when the theme changes with no re-render and no
 *   duplicated palette. A canvas cannot resolve a CSS variable and would need the palette copied
 *   into JavaScript, where it would drift.
 * - **Node radius encodes `influence`**, the single definition computed once in the pipeline, so
 *   the tree, the equation highlighting and the contribution chart cannot disagree about which part
 *   of the expression matters.
 *
 * Interaction contract: hovering a node reads out its label, its subtree size and its influence;
 * hovering also highlights the corresponding term in the equation, because both are keyed by the
 * same integer id space.
 */
import { hierarchy, tree as d3tree, type HierarchyPointNode } from 'd3-hierarchy';
import { useMemo, useState } from 'react';

import type { TreeNode, TreePayload } from '../lib/contract.types';

export interface ExpressionTreeProps {
  payload: TreePayload;
  /** The currently highlighted node id, driven from the equation or from this component. */
  activeNodeId: number | null;
  onHoverNode: (id: number | null) => void;
  /** Collapse subtrees below this size, so a 300-node expression stays readable. */
  collapseBelowInfluence?: number;
  lang: 'en' | 'es';
}

interface Datum {
  node: TreeNode;
  children: Datum[];
}

const NODE_RADIUS_MIN = 7;
const NODE_RADIUS_MAX = 18;
const MARGIN = { top: 28, right: 24, bottom: 28, left: 24 };

function buildHierarchy(nodes: TreeNode[]): Datum | null {
  if (nodes.length === 0) return null;
  const byId = new Map<number, Datum>();
  nodes.forEach((node) => byId.set(node.id, { node, children: [] }));
  let root: Datum | null = null;
  nodes.forEach((node) => {
    const entry = byId.get(node.id)!;
    if (node.parent === null) {
      root = entry;
    } else {
      byId.get(node.parent)?.children.push(entry);
    }
  });
  return root;
}

/**
 * The label as it should READ, not as it is stored.
 *
 * Variable labels arrive as LaTeX (`T_{amb}`, `\mathrm{RH}`) because the same string feeds the
 * equation renderer. Dropped into an SVG circle they render as raw markup and clip to `{amb`, which
 * is unreadable and looks like a rendering fault. Braces and command prefixes are stripped, and
 * anything still too wide for a circle is drawn BELOW the node instead of inside it.
 */
function readableLabel(raw: string): string {
  return raw
    .replace(/\\mathrm|\\text|\\operatorname/g, '')
    .replace(/[{}\\]/g, '')
    .replace(/\s+/g, '');
}

/** Labels up to this many characters fit inside a node circle; longer ones sit below it. */
const INSIDE_MAX = 3;

/** Class per node kind, so colour lives in CSS and follows the theme. */
function kindClass(node: TreeNode): string {
  switch (node.kind) {
    case 'var':
      return 'sym-node sym-node-var';
    case 'const':
      return 'sym-node sym-node-const';
    case 'op_unary':
      return 'sym-node sym-node-unary';
    default:
      return 'sym-node sym-node-binary';
  }
}

export function ExpressionTree({
  payload,
  activeNodeId,
  onHoverNode,
  collapseBelowInfluence = 0,
  lang,
}: ExpressionTreeProps) {
  const [hover, setHover] = useState<TreeNode | null>(null);

  const visible = useMemo(() => {
    if (collapseBelowInfluence <= 0) return payload.nodes;
    // Collapsing hides a subtree ROOTED at a low-influence node, rather than hiding scattered
    // individual nodes, so what remains is always a valid tree.
    const hidden = new Set<number>();
    const byId = new Map(payload.nodes.map((n) => [n.id, n]));
    payload.nodes.forEach((node) => {
      if (node.parent === null) return;
      let cursor: TreeNode | undefined = node;
      while (cursor && cursor.parent !== null) {
        if (cursor.influence < collapseBelowInfluence && cursor.id !== node.id) {
          hidden.add(node.id);
          break;
        }
        cursor = byId.get(cursor.parent);
      }
    });
    return payload.nodes.filter((n) => !hidden.has(n.id));
  }, [payload.nodes, collapseBelowInfluence]);

  const laidOut = useMemo(() => {
    const rootDatum = buildHierarchy(visible);
    if (!rootDatum) return null;
    const nodeCount = visible.length;
    const width = Math.max(560, Math.min(1180, nodeCount * 46));
    const height = Math.max(220, (payload.max_depth + 1) * 74);
    const layout = d3tree<Datum>().size([
      width - MARGIN.left - MARGIN.right,
      height - MARGIN.top - MARGIN.bottom,
    ]);
    const positioned = layout(hierarchy(rootDatum, (d) => d.children));
    return { positioned, width, height };
  }, [visible, payload.max_depth]);

  if (!laidOut) {
    return (
      <p className="sym-empty">
        {lang === 'es' ? 'Sin arbol para mostrar.' : 'No tree to display.'}
      </p>
    );
  }

  const { positioned, width, height } = laidOut;
  const nodes = positioned.descendants() as HierarchyPointNode<Datum>[];
  const links = positioned.links();

  const radius = (influence: number) =>
    NODE_RADIUS_MIN + (NODE_RADIUS_MAX - NODE_RADIUS_MIN) * Math.sqrt(Math.max(0, Math.min(1, influence)));

  const shown = hover ?? (activeNodeId !== null ? visible.find((n) => n.id === activeNodeId) ?? null : null);

  return (
    <div className="sym-tree-wrap">
      <svg
        className="sym-tree"
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={
          lang === 'es'
            ? `Arbol de expresion con ${payload.n_nodes} nodos y profundidad ${payload.max_depth}`
            : `Expression tree with ${payload.n_nodes} nodes and depth ${payload.max_depth}`
        }
      >
        <g transform={`translate(${MARGIN.left},${MARGIN.top})`}>
          {links.map((link, index) => {
            const source = link.source as HierarchyPointNode<Datum>;
            const target = link.target as HierarchyPointNode<Datum>;
            const midY = (source.y + target.y) / 2;
            return (
              <path
                key={index}
                className="sym-link"
                d={`M${source.x},${source.y} C${source.x},${midY} ${target.x},${midY} ${target.x},${target.y}`}
              />
            );
          })}
          {nodes.map((point) => {
            const node = point.data.node;
            const isActive = activeNodeId === node.id || hover?.id === node.id;
            return (
              <g
                key={node.id}
                transform={`translate(${point.x},${point.y})`}
                className={`${kindClass(node)}${isActive ? ' is-active' : ''}${
                  node.term_id !== null ? ` sym-term-${node.term_id}` : ''
                }`}
                onMouseEnter={() => {
                  setHover(node);
                  onHoverNode(node.id);
                }}
                onMouseLeave={() => {
                  setHover(null);
                  onHoverNode(null);
                }}
                tabIndex={0}
                onFocus={() => onHoverNode(node.id)}
                onBlur={() => onHoverNode(null)}
              >
                <circle r={radius(node.influence)} />
                {(() => {
                  const label = readableLabel(node.label);
                  return label.length <= INSIDE_MAX ? (
                    <text className="sym-node-label" dy="0.34em">
                      {label}
                    </text>
                  ) : (
                    <text
                      className="sym-node-label sym-node-label-outside"
                      dy={radius(node.influence) + 13}
                    >
                      {label}
                    </text>
                  );
                })()}
              </g>
            );
          })}
        </g>
      </svg>

      <div className="sym-tree-readout" aria-live="polite">
        {shown ? (
          <>
            <strong>{shown.label}</strong>
            <span>
              {lang === 'es' ? 'subarbol' : 'subtree'} {shown.subtree_size}
            </span>
            <span>
              {lang === 'es' ? 'influencia' : 'influence'} {(shown.influence * 100).toFixed(1)}%
            </span>
            {shown.mean_value !== null && (
              <span>
                {lang === 'es' ? 'valor medio' : 'mean value'} {shown.mean_value.toPrecision(4)}
              </span>
            )}
            {shown.unit_label && (
              <span>
                {lang === 'es' ? 'unidad' : 'unit'} {shown.unit_label}
              </span>
            )}
          </>
        ) : (
          <span className="sym-hint">
            {lang === 'es'
              ? 'Pasa el cursor por un nodo: tamano del subarbol, influencia y valor medio.'
              : 'Hover a node for its subtree size, influence and mean value.'}
          </span>
        )}
      </div>

      <p className="sym-tree-note">
        {lang === 'es'
          ? `${payload.n_nodes} nodos, profundidad ${payload.max_depth}. El radio codifica la influencia: la caida en R2 al reemplazar ese subarbol por su media.`
          : `${payload.n_nodes} nodes, depth ${payload.max_depth}. Radius encodes influence: the drop in R-squared when that subtree is replaced by its mean.`}
        {visible.length < payload.nodes.length && (
          <>
            {' '}
            {lang === 'es'
              ? `Mostrando ${visible.length} de ${payload.nodes.length} nodos.`
              : `Showing ${visible.length} of ${payload.nodes.length} nodes.`}
          </>
        )}
      </p>
    </div>
  );
}
