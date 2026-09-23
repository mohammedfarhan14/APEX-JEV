"""Schema definitions for raw MT5 exports and the canonical candle representation.

Any change to the canonical columns, dtypes, or semantics MUST bump SCHEMA_VERSION.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

SCHEMA_VERSION = "1.0.0"

# MetaTrader 5 "Export bars" format. Headers appear as <DATE>, <TIME>, ... and the file is tab separated.
RAW_COLUMNS: tuple[str, ...] = ("DATE", "TIME", "OPEN", "HIGH", "LOW", "CLOSE", "TICKVOL", "VOL", "SPREAD")

RAW_TO_CANONICAL: dict[str, str] = {
    "OPEN": "open",
    "HIGH": "high",
    "LOW": "low",
    "CLOSE": "close",
    "TICKVOL": "tick_volume",
    "VOL": "volume",
    "SPREAD": "spread",
}

# Canonical candle frame. `ts` is the candle OPEN time in broker server time (see DATA_SPEC.md).
CANONICAL_COLUMNS: tuple[str, ...] = (
    "ts",
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "volume",
    "spread",
)

CANONICAL_DTYPES: dict[str, str] = {
    "ts": "datetime64[ns]",
    "open": "float64",
    "high": "float64",
    "low": "float64",
    "close": "float64",
    "tick_volume": "int64",
    "volume": "int64",
    "spread": "int64",
}

# Timezone policy (Level 0): timestamps are kept NAIVE and labelled as broker server time. No UTC
# conversion is performed because the broker's server offset is not encoded in the files. This is an
# explicit ASSUMPTION recorded in every manifest and report until verified against the broker.
TIMEZONE_LABEL = "broker_server_time_naive"


class Timeframe(str, Enum):
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"

    @property
    def minutes(self) -> int:
        return {"M15": 15, "M30": 30, "H1": 60}[self.value]


_FILENAME_RE = re.compile(
    r"^(?P<symbol>[A-Z0-9]+)_(?P<timeframe>M15|M30|H1)_(?P<start>\d{12})_(?P<end>\d{12})\.csv$"
)


@dataclass(frozen=True)
class DatasetIdentity:
    symbol: str
    timeframe: Timeframe
    declared_start: str  # yyyymmddHHMM as found in the filename (not trusted until verified)
    declared_end: str
    source_filename: str

    @property
    def dataset_id(self) -> str:
        return f"{self.symbol}_{self.timeframe.value}"


def parse_identity(path: str | Path) -> DatasetIdentity:
    """Derive symbol/timeframe from an MT5 export filename, e.g. XAUUSD_M30_201801240100_202607280400.csv."""
    name = Path(path).name
    m = _FILENAME_RE.match(name)
    if not m:
        raise ValueError(
            f"Unrecognised MT5 export filename {name!r}; expected SYMBOL_TF_yyyymmddHHMM_yyyymmddHHMM.csv"
        )
    return DatasetIdentity(
        symbol=m.group("symbol"),
        timeframe=Timeframe(m.group("timeframe")),
        declared_start=m.group("start"),
        declared_end=m.group("end"),
        source_filename=name,
    )
