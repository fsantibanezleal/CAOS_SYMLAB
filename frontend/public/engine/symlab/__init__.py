"""symlab: the offline engine and shared expression core for the SymLab research lab.

Symbolic regression, meaning the recovery of an explicit closed-form expression from data, run
across the full method ladder on the same open cases with the same protocol.

The package is layered so that the browser lane can import a strict subset:

- `model/`   the shared expression core. numpy only, so the same code runs offline, under Pyodide in
             the browser, and in the dormant API. The ONLY code shared across lanes.
- `search/`  the engines. A genetic-programming search whose every classical rung is a switch, and a
             bounded exhaustive search that returns a completeness certificate.
- `cases/`   the case registry and the first-principles generators whose governing law is known.
- `io/`      the source registry, the loaders, and the ingestion contract.
- `core/`    the artifact contract, frozen at schema_version 1.0.0, and the lane gate.
- `stages/`  the six named offline pipeline stages.
"""

__version__ = "0.03.000"
