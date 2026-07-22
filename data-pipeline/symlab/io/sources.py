"""The dataset source registry: every real dataset, with its provenance and its redistribution terms.

This module is the answer to a question the research phase made unavoidable: the canonical URL for
one of the field's most-cited dataset collections is already dead (HTTP 404), while another
collection grew from 417 datasets in its paper to 450 today. A lab that hard-codes URLs and assumes
they mean the same thing next year is building on sand.

So every source here carries five things that are not optional:

1. **A live URL**, verified at the date recorded on the entry.
2. **A SHA-256** of the fetched bytes, recorded on first fetch and checked on every later fetch. A
   silent upstream change becomes a loud failure instead of a quiet shift in every published number.
3. **The licence**, and separately the REDISTRIBUTION verdict, because those are different questions.
   A dataset can be freely downloadable and still not be ours to re-host.
4. **A citation**, which the app prints next to any number derived from the source.
5. **Known defects**, carried verbatim rather than fixed silently. Three of these datasets have a
   documented trap, and hiding a trap is worse than the trap.

Nothing here is committed to git. Raw data lands in the vault on the scratch volume; only compact
derived artifacts, and tiny contract-passing samples from permissively licensed sets, ever enter the
repository.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

#: Where raw downloads land. Never inside the repository.
VAULT = Path("E:/_Datos/symlab/raw")

#: Redistribution verdicts. The distinction matters legally and is enforced by the pipeline.
REDISTRIBUTE_MIRROR = "mirror"        # permissive: a compact sample may be committed with attribution
REDISTRIBUTE_DERIVED = "derived"      # only derived metrics/artifacts may be published
REDISTRIBUTE_LINK = "link-only"       # never re-hosted in any form; fetch script plus citation only


@dataclass(frozen=True)
class Source:
    """One fetchable dataset."""

    id: str
    name: str
    url: str
    filename: str
    licence: str
    redistribution: str
    citation: str
    verified_on: str
    approx_bytes: int | None = None
    sha256: str | None = None          # filled in on first fetch, then enforced
    defects: tuple[str, ...] = ()
    notes: str = ""
    unpack: str | None = None          # "zip" when the payload is an archive

    @property
    def path(self) -> Path:
        return VAULT / self.id / self.filename

    @property
    def may_commit_sample(self) -> bool:
        return self.redistribution == REDISTRIBUTE_MIRROR


def sha256_of(path: Path, *, chunk: int = 1 << 20) -> str:
    """Stream a SHA-256 so a multi-hundred-megabyte file does not have to fit in memory."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(chunk)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


SOURCES: dict[str, Source] = {}


def _register(source: Source) -> Source:
    SOURCES[source.id] = source
    return source


# --------------------------------------------------------------------------------------------
# Mining
# --------------------------------------------------------------------------------------------

FLOTATION = _register(Source(
    id="flotation-mining-process",
    name="Quality Prediction in a Mining Process (froth flotation plant)",
    # CORRECTED 2026-07-22. The research dossier recorded file id 22102255, which downloads a
    # completely different dataset (Counter-Strike round snapshots, 97 attributes, 50 MB). The
    # correct id, resolved through the OpenML API for dataset 43311, is 22102136. The wrong file
    # arrived with HTTP 200 and a plausible size, so only reading the content caught it.
    url="https://openml.org/data/v1/download/22102136/Quality-Prediction-in-a-Mining-Process.arff",
    filename="Quality-Prediction-in-a-Mining-Process.arff",
    licence="CC0 1.0 Public Domain (OpenML dataset 43311)",
    redistribution=REDISTRIBUTE_MIRROR,
    citation=(
        "Quality Prediction in a Mining Process, OpenML dataset 43311, CC0 Public Domain. "
        "Real froth flotation plant, 20-second process readings with hourly laboratory assays."
    ),
    verified_on="2026-07-21",
    approx_bytes=185_000_000,
    defects=(
        "THE RECORDED SOURCE URL WAS WRONG. The research dossier gave OpenML file id 22102255, which "
        "serves an unrelated Counter-Strike dataset with HTTP 200. The correct id for dataset 43311 is "
        "22102136, resolved through the OpenML API. A fetcher that trusts the status code cannot catch "
        "this; the pipeline verifies the attribute names before accepting the file.",
        "THE TARGET IS BROADCAST. The iron and silica concentrate assays are HOURLY laboratory "
        "measurements copied across every 20-second row: 737,453 rows over 4,097 distinct "
        "timestamps, so each assay appears 180 times. Fitting row-wise scores a model against 180 "
        "copies of the same measurement. The pipeline aggregates to the hourly grid BEFORE any "
        "fitting and refuses to proceed otherwise.",
        "The file uses a comma as the decimal separator inside quoted fields. A naive parse silently "
        "produces wrong numbers rather than an error.",
    ),
    notes=(
        "Measured with the parser this repository ships: all 737,453 data lines parse cleanly, and "
        "corr(Fe_feed, Si_feed) = -0.9718. OLS gives Fe = 67.08 - 0.736*Si against the two-mineral "
        "stoichiometric prediction 69.94 - 0.699*Si, and that discrepancy is itself a case. The feed "
        "assays do not vary within an hour, so the hourly fit is the same line, "
        "Fe = 67.0831 - 0.7363*Si."
    ),
))

GEOMET = _register(Source(
    id="geomet",
    name="GeoMet: a geometallurgical dataset (Vale S.A. and IMPA)",
    url="https://zenodo.org/api/records/7051975",
    filename="record.json",
    licence="CC BY 4.0",
    redistribution=REDISTRIBUTE_DERIVED,
    citation="GeoMet dataset, Zenodo record 7051975, CC BY 4.0. Vale S.A. and IMPA.",
    verified_on="2026-07-21",
    notes=(
        "The only permissively licensed geometallurgy data found in the research. Comminution table "
        "78 x 28 with F80 and P80; flotation 49 x 26 with locked-cycle copper recovery; drillholes "
        "2000 x 22. The companion paper must be read to pin the semantics of the th1/th2/th3, M, A, "
        "fr and xr columns before the comminution case is scored."
    ),
))

# --------------------------------------------------------------------------------------------
# Industrial process
# --------------------------------------------------------------------------------------------

CCPP = _register(Source(
    id="ccpp",
    name="UCI Combined Cycle Power Plant",
    url="https://archive.ics.uci.edu/static/public/294/combined+cycle+power+plant.zip",
    filename="ccpp.zip",
    licence="CC BY 4.0 (UCI Machine Learning Repository)",
    redistribution=REDISTRIBUTE_MIRROR,
    citation=(
        "Tufekci, P. and Kaya, H. Combined Cycle Power Plant. UCI Machine Learning Repository, "
        "doi:10.24432/C5002N. 9,568 hourly records from a combined cycle plant at full load."
    ),
    verified_on="2026-07-21",
    approx_bytes=3_674_852,
    unpack="zip",
    notes=(
        "Inputs: ambient temperature, exhaust vacuum, ambient pressure, relative humidity. Target: "
        "net hourly electrical energy output. The expected structure is ambient derating with an "
        "AP/AT density term."
    ),
))

CONCRETE = _register(Source(
    id="concrete",
    name="UCI Concrete Compressive Strength",
    url="https://archive.ics.uci.edu/static/public/165/concrete+compressive+strength.zip",
    filename="concrete.zip",
    licence="CC BY 4.0 (UCI Machine Learning Repository)",
    redistribution=REDISTRIBUTE_MIRROR,
    citation=(
        "Yeh, I.-C. Concrete Compressive Strength. UCI Machine Learning Repository, "
        "doi:10.24432/C5PK67. 1,030 mixes, 8 inputs."
    ),
    verified_on="2026-07-21",
    approx_bytes=34_444,
    unpack="zip",
    notes=(
        "Expected structure: the Abrams water-to-cement law fc = A / B^(w/c) together with a "
        "logarithmic maturity term in age. A good test of whether a search finds a ratio it was not "
        "handed as an input."
    ),
))

GAS_TURBINE = _register(Source(
    id="gas-turbine-emissions",
    name="UCI Gas Turbine CO and NOx Emission",
    url="https://archive.ics.uci.edu/static/public/551/gas+turbine+co+and+nox+emission+data+set.zip",
    filename="gas-turbine.zip",
    licence="CC BY 4.0 (UCI Machine Learning Repository)",
    redistribution=REDISTRIBUTE_MIRROR,
    citation=(
        "Kaya, H., Tufekci, P. and Uzun, E. Gas Turbine CO and NOx Emission Data Set. UCI Machine "
        "Learning Repository, doi:10.24432/C5WC95. 36,733 hourly records, 2011 to 2015."
    ),
    verified_on="2026-07-21",
    unpack="zip",
    notes="Expected structure: Zeldovich thermal NOx, an exp(-a/TIT) dependence on turbine inlet temperature.",
))

WATER_TREATMENT = _register(Source(
    id="water-treatment",
    name="UCI Water Treatment Plant",
    url="https://archive.ics.uci.edu/static/public/106/water+treatment+plant.zip",
    filename="water-treatment.zip",
    licence="CC BY 4.0 (UCI Machine Learning Repository)",
    redistribution=REDISTRIBUTE_MIRROR,
    citation="Water Treatment Plant. UCI Machine Learning Repository, doi:10.24432/C5854H. 527 days.",
    verified_on="2026-07-21",
    unpack="zip",
    defects=(
        "THE LANDING PAGE IS WRONG about missing values. It states there are none; the shipped file "
        "contains 591. The ingestion contract records the real count and the pipeline refuses to "
        "silently impute them.",
    ),
    notes=(
        "Carries an EXACT identity: the removal-efficiency columns are 100*(in - out)/in of other "
        "columns in the same file. A search that cannot recover an exact identity present in its own "
        "inputs is not going to recover a physical law from noisy data, which makes this the cheapest "
        "sanity case in the whole set."
    ),
))

# --------------------------------------------------------------------------------------------
# Physics ground truth
# --------------------------------------------------------------------------------------------

# PMLB stores its dataset files in Git LFS. The ordinary raw.githubusercontent URL returns a
# 132-byte LFS POINTER, not the data, and it returns it with HTTP 200, so a fetcher that only checks
# the status code will report success and write garbage. Verified 2026-07-22: the pointer route gave
# 132 bytes, the media route gives real gzip (nikuradse_1: 362 rows, columns r_k, log_Re, target).
# `scripts/fetch_data.py` also detects the pointer signature and fails loudly, so this cannot regress.
PMLB_MEDIA_BASE = "https://media.githubusercontent.com/media/EpistasisLab/pmlb/master/datasets"

PMLB_INDEX = _register(Source(
    id="pmlb-index",
    name="PMLB dataset index (summary statistics)",
    url="https://raw.githubusercontent.com/EpistasisLab/pmlb/master/pmlb/all_summary_stats.tsv",
    filename="all_summary_stats.tsv",
    licence="MIT (EpistasisLab/pmlb)",
    redistribution=REDISTRIBUTE_MIRROR,
    citation=(
        "Romano, J. D. et al. PMLB v1.0: an open source dataset collection for benchmarking machine "
        "learning methods. arXiv:2012.00058. MIT licensed."
    ),
    verified_on="2026-07-21",
    notes=(
        "The live carrier for the Feynman equation set. The ORIGINAL canonical host for that "
        "collection returns HTTP 404 and must never be pointed at, yet it remains the cited source "
        "inside PMLB's own metadata. Counted during research: 450 datasets today, of which 119 "
        "feynman_* and 14 strogatz_*, against 417 reported in the PMLB paper."
    ),
))


def pmlb_source(dataset: str) -> Source:
    """Build a source entry for one PMLB dataset, fetched on demand."""
    return Source(
        id=f"pmlb-{dataset}",
        name=f"PMLB {dataset}",
        url=f"{PMLB_MEDIA_BASE}/{dataset}/{dataset}.tsv.gz",
        filename=f"{dataset}.tsv.gz",
        licence="MIT (EpistasisLab/pmlb)",
        redistribution=REDISTRIBUTE_MIRROR,
        citation=PMLB_INDEX.citation,
        verified_on="2026-07-21",
        notes="Ground truth formula and SI units are machine-readable in the PMLB metadata.",
    )


#: The Feynman problems used as the physics ground-truth case. Chosen across arities so the case
#: spans easy single-variable laws and genuinely multi-variable ones, rather than being padded with
#: near-duplicates of the same shape.
FEYNMAN_SELECTION: tuple[str, ...] = (
    "feynman_I_6_2a",      # Gaussian, one variable
    "feynman_I_12_1",      # F = mu*Nn, two variables, trivially linear (the floor)
    "feynman_I_12_5",      # F = q2*Ef
    "feynman_I_14_3",      # U = m*g*z
    "feynman_I_25_13",     # V = q/C
    "feynman_I_26_2",      # arcsin(n*sin(theta2))
    "feynman_I_29_4",      # k = omega/c
    "feynman_I_34_27",     # E = h/(2*pi)*omega
    "feynman_I_39_1",      # E = 3/2*pr*V
    "feynman_I_43_31",     # D = mob*kb*T
    "feynman_II_3_24",     # h = Pwr/(4*pi*r**2)
    "feynman_II_8_31",     # E = Ef**2*epsilon/2
    "feynman_II_10_9",     # Ef = sigma_den/epsilon/(1+chi)
    "feynman_II_27_18",    # E = epsilon*Ef**2
    "feynman_II_38_14",    # G = Y/(2*(1+sigma))
    "feynman_III_12_43",   # L = n*h/(2*pi)
    # m = h**2/(8*pi**2 * E_n * d**2). This read `h/(2*pi)**2/(E_n*d**2)`, which is a different
    # formula: measured against the shipped rows it is off by a relative 1.0, while the form
    # below reproduces them to 1.5e-15. The verified builder is in cases/physics_truths.py.
    "feynman_III_15_14",
    "feynman_III_17_37",   # f = beta*(1+alpha*cos(theta))
)

#: The Strogatz two-state ODE right-hand sides shipped as the dynamics case.
STROGATZ_SELECTION: tuple[str, ...] = (
    "strogatz_bacres1", "strogatz_bacres2",
    "strogatz_barmag1", "strogatz_barmag2",
    "strogatz_glider1", "strogatz_glider2",
    "strogatz_lv1", "strogatz_lv2",
    "strogatz_predprey1", "strogatz_predprey2",
    "strogatz_shearflow1", "strogatz_shearflow2",
    "strogatz_vdp1", "strogatz_vdp2",
)

for _dataset in FEYNMAN_SELECTION + STROGATZ_SELECTION:
    _register(pmlb_source(_dataset))


# --------------------------------------------------------------------------------------------
# Link-only sources: fetched by script, never re-hosted
# --------------------------------------------------------------------------------------------

#: The Nikuradse rough-pipe measurements. The Princeton host cited by the research dossier returns
#: HTTP 404 (verified 2026-07-22), which is the SECOND dead canonical URL found in this field. PMLB
#: carries the same 362 measured points under MIT, which is strictly better than the original: the
#: original stated no licence at all and could only ever have been link-only, while this can be
#: mirrored with attribution. `nikuradse_1` has two features (relative roughness and log Reynolds),
#: `nikuradse_2` has one.
NIKURADSE_1 = _register(pmlb_source("nikuradse_1"))
NIKURADSE_2 = _register(pmlb_source("nikuradse_2"))
