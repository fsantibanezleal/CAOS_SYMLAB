# 05 · The in-app Architecture / "How it works" modal (ADR-0058)

Every CAOS/Faena web app **MUST** ship an in-app **Architecture / "How it works"** modal, opened by an
always-visible **ⓘ button in the header**. It is the fast visual proof the app is a real, complete system
rather than a demo. The chrome (button + modal) comes from the shared shell; the product supplies only its
diagrams and copy.

Binding decision: ADR-0058, recorded in the private CAOS_MANAGE conventions repo, so it is named by number and
not linked. Reference implementations: Veta and Circuita.

## How it is wired here

- **Chrome**: `@fasl-work/caos-app-shell`, pinned `^0.3.0` in `frontend/package.json` (0.3.0 installed),
  exposes the ⓘ button and the `ArchitectureModal`. `ShellConfig` carries an `architecture` field; the button
  appears when it is present.
- **Config**: `frontend/src/architecture.ts` exports `ARCHITECTURE: ArchitectureConfig`, imported by
  `frontend/src/main.tsx` and passed as `architecture: ARCHITECTURE` inside the `AppShell` config, alongside
  `product`, `routes`, `links`, `version` and `footer`.
- **Diagrams**: five hand-authored SVGs in [`frontend/public/svg/tech/`](../../frontend/public/svg/tech/),
  `01-the-app.svg` through `05-data-contracts.svg`, 4 to 5 KB each. Every colour is a shell CSS-variable token
  (`--color-accent`, `--color-border`, `--color-fg`, `--color-fg-subtle`), so each diagram repaints with the
  active light/dark theme. The shell fetches and INLINES them rather than referencing them as images, because
  an `<img>` cannot inherit the page custom properties and would be unreadable in one of the two themes.

There is no `frontend/src/architecture.ts.txt` scaffold in this repo, and there must not be:
`scripts/check_template_residue.py` fails the build on any tracked `.ts.txt` file.

## The five tabs as shipped

| id | tab | generic? | what it shows |
|----|-----|----------|---------------|
| `what-it-is` | What it is | **product** | symbolic regression as this lab frames it: a Pareto front of candidate laws, and why accuracy and recovery are reported as two numbers |
| `lanes` | The lanes | generic | what runs live in the browser vs offline (the bake) vs replay |
| `web-flow` | The web flow | generic | the six pages, the contract mirror, the copy-data staging, the Pages deploy |
| `science` | The science | **product** | the search ladder and the selection criterion, with the real equations |
| `contracts` | The two contracts | generic | ingestion and artifact, plus cases-by-category |

Every body is bilingual (`body_en` / `body_es`). Adding a domain tab is fine; dropping below these five is not.

## Verify before deploy

The screenshot-verify step (mandatory before any deploy) **must open the modal and confirm every tab renders
its diagram (themed, no broken SVG) and its text with no error**, in both light and dark. A product is not
"done" without the ⓘ Architecture modal at full depth; it is a non-negotiable row in the product-quality bar.
