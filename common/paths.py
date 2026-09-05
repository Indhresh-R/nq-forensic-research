"""Repository paths + family-grouped artifact resolution."""
from __future__ import annotations

from pathlib import Path

from common.artifact_homes import ARTIFACT_HOMES

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
DATA = ROOT / "data"
STRATEGIES = ROOT / "strategies"

ART.mkdir(exist_ok=True)
DATA.mkdir(exist_ok=True)


def art(name: str) -> Path:
    """
    Resolve an artifact by basename into its family folder.

    Known names map via ``ARTIFACT_HOMES``. Unknown names go under ``artifacts/_other/``.
    Parent dirs are created on resolve so writers can open paths safely.
    """
    base = Path(name).name
    family = ARTIFACT_HOMES.get(base)
    if family:
        path = ART / family / base
    else:
        # Prefer an existing nested copy if present
        for d in ART.iterdir() if ART.exists() else []:
            if d.is_dir():
                cand = d / base
                if cand.exists():
                    path = cand
                    break
        else:
            flat = ART / base
            path = flat if flat.exists() else (ART / "_other" / base)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
