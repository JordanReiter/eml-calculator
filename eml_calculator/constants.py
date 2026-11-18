"""Single source for every shared number (constitution Principle VI).

Nothing in this package, the test suite, or the corpus may retype these values.
Import them by name instead.
"""

from __future__ import annotations

from typing import NamedTuple

# Equivalence tolerance and the complex-to-real display rule (FR-008, FR-014).
REL_TOL_EPSILON = 1e-9
IMAG_ABS_FLOOR = 1e-12

# Evaluation guards (FR-013).  Depth is counted per tree node, not per source token.
MAX_NODE_EVAL_DEPTH = 20_000
MAX_FINITE_MAGNITUDE = 1e300

# Internal construction-verification samples only.  Runtime input is closed (FR-002).
class SampleRange(NamedTuple):
    name: str
    start: float
    stop: float
    step: float


DEFAULT_FREE_VAR_SAMPLES: tuple[float, ...] = (0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0)
SAMPLE_RANGE_DESCRIPTORS: tuple[SampleRange, ...] = (
    SampleRange("unit", 0.25, 4.0, 0.25),
    SampleRange("negative", -4.0, -0.25, 0.25),
)

# Corpus data: enough nested exponentials to leave IEEE-754 finite (SC-002).
OVERFLOW_EXPONENTIAL_COUNT = 12

# Deterministic output paths and rendering knobs.
DEFAULT_CONFIG_PATH = "config.toml"
DEFAULT_HTML_PATH = "out.html"
DETAILS_DEPTH_THRESHOLD = 3
DETAILS_OPEN_LEVELS = 2
