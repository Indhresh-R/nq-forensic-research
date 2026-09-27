"""Score the frozen order-fate partial associations. One pass. No refit."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from mbo_orderflow.order_fate.code.definitions import (
    BANNED_P_COLUMNS,
    DECISION_HORIZON,
    HORIZONS,
    MIN_ROWS,
    P_COLUMNS,
    PARTIAL_FLOOR,
    R_COLUMNS,
    assert_study_p_schema,
)
from research.mbo.sessions import IS_SESSIONS
from research.mbo.version import REPLAY_ENGINE_VERSION

OUT = Path(__file__).resolve().parents[1] / "results"
REPORT = Path(__file__).resolve().parents[1] / "REPORT.md"
CONTROLS = ("obi", "depth_change", "trade_imbalance", "replenishment")
DISCOVERY = IS_SESSIONS[:13]
HELD_OUT = IS_SESSIONS[13:]


def _assert_split() -> None:
    if (
        DISCOVERY[0] != "2026-07-08"
        or DISCOVERY[-1] != "2026-07-24"
        or HELD_OUT[0] != "2026-07-27"
        or HELD_OUT[-1] != "2026-08-12"
        or len(DISCOVERY) != 13
        or len(HELD_OUT) != 13
    ):
        raise RuntimeError("session split does not match the preregistration")


def _load(study: str, dates: tuple[str, ...]) -> pd.DataFrame:
    columns = P_COLUMNS if study == "P" else R_COLUMNS
    if study == "P":
        assert_study_p_schema(columns)
    frames = []
    for date_str in dates:
        path = OUT / study.lower() / f"date={date_str}" / "rows.parquet"
        frame = pd.read_parquet(path, columns=list(columns))
        if study == "P" and BANNED_P_COLUMNS.intersection(frame.columns):
            raise RuntimeError(f"{path} contains completed-order fields")
        for name in frame.columns:
            if name != "date" and frame[name].dtype != object:
                frame[name] = frame[name].astype(np.float32)
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def _audit_invalid() -> None:
    for date_str in IS_SESSIONS:
        audit = json.loads((OUT / "audit" / f"{date_str}.json").read_text(encoding="utf-8"))
        if audit["replay_version"] != REPLAY_ENGINE_VERSION:
            raise RuntimeError(f"{date_str} was not extracted with {REPLAY_ENGINE_VERSION}")
        if audit["book_mismatches"] != 0:
            raise RuntimeError(f"{date_str} book diverged from the frozen store")
        names = pd.read_parquet(OUT / "p" / f"date={date_str}" / "rows.parquet").columns
        assert_study_p_schema(list(names))


def _partial(feature: np.ndarray, outcome: np.ndarray, controls: np.ndarray) -> tuple[float, int]:
    mask = np.isfinite(feature) & np.isfinite(outcome) & np.isfinite(controls).all(axis=1)
    n = int(mask.sum())
    if n < MIN_ROWS:
        return float("nan"), n
    x = feature[mask]
    y = outcome[mask]
    c = controls[mask]
    if np.unique(x).size < 2 or np.unique(y).size < 2:
        return float("nan"), n
    ranked = [rankdata(x, method="average"), rankdata(y, method="average")]
    ranked.extend(rankdata(c[:, i], method="average") for i in range(c.shape[1]))
    rx = ranked[0]
    ry = ranked[1]
    design = np.column_stack([np.ones(n, dtype=np.float64), *ranked[2:]])
    beta_x, *_ = np.linalg.lstsq(design, rx, rcond=None)
    beta_y, *_ = np.linalg.lstsq(design, ry, rcond=None)
    resid_x = rx - design @ beta_x
    resid_y = ry - design @ beta_y
    if np.std(resid_x) == 0 or np.std(resid_y) == 0:
        return float("nan"), n
    return float(np.corrcoef(resid_x, resid_y)[0, 1]), n


def _feature_values(frame: pd.DataFrame, name: str) -> np.ndarray:
    if name == "log_lifetime":
        return np.log1p(frame["lifetime_ms"].to_numpy(dtype=np.float64))
    if name == "fate":
        return frame["fate"].to_numpy(dtype=np.float64)
    if name == "log_age":
        return np.log1p(frame["age_ms"].to_numpy(dtype=np.float64))
    if name == "log_trade_size":
        return np.log1p(frame["trade_size_at_price"].to_numpy(dtype=np.float64))
    raise KeyError(name)


def _controls(frame: pd.DataFrame, side: np.ndarray) -> np.ndarray:
    raw = np.column_stack([frame[name].to_numpy(dtype=np.float64) for name in CONTROLS])
    return raw * side[:, None]


def _outcome(frame: pd.DataFrame, horizon: int, side: np.ndarray) -> np.ndarray:
    return side * frame[f"y{horizon}"].to_numpy(dtype=np.float64)


def _sign(value: float) -> int:
    if not np.isfinite(value) or value == 0:
        return 0
    return 1 if value > 0 else -1


def _label(held: float, discovery: float) -> str:
    if not np.isfinite(held):
        return "INCONCLUSIVE"
    if abs(held) < PARTIAL_FLOOR:
        return "NOT SUPPORTED"
    if _sign(held) == 0 or _sign(held) != _sign(discovery):
        return "INCONCLUSIVE"
    return "SUPPORTED"


def _fifth_spread(feature: np.ndarray, outcome: np.ndarray) -> float:
    mask = np.isfinite(feature) & np.isfinite(outcome)
    x = feature[mask]
    y = outcome[mask]
    if x.size < MIN_ROWS or np.unique(x).size < 2:
        return float("nan")
    order = np.argsort(x, kind="mergesort")
    k = x.size // 5
    if k == 0:
        return float("nan")
    return float(np.mean(y[order[-k:]]) - np.mean(y[order[:k]]))


def _question_label(labels: list[str]) -> str:
    if "SUPPORTED" in labels:
        return "SUPPORTED"
    if "INCONCLUSIVE" in labels:
        return "INCONCLUSIVE"
    return "NOT SUPPORTED"


def _score_block(frame: pd.DataFrame, feature_key: str, horizon: int) -> tuple[float, int]:
    side = frame["side_sign"].to_numpy(dtype=np.float64)
    return _partial(
        _feature_values(frame, feature_key),
        _outcome(frame, horizon, side),
        _controls(frame, side),
    )


def _session_loop(
    study: str, feature_key: str, horizon: int, dates: tuple[str, ...], pooled_sign: int
) -> tuple[float, int, int]:
    values = []
    match = 0
    for date_str in dates:
        path = OUT / study.lower() / f"date={date_str}" / "rows.parquet"
        columns = P_COLUMNS if study == "P" else R_COLUMNS
        part = pd.read_parquet(path, columns=list(columns))
        for name in part.columns:
            if name != "date":
                part[name] = part[name].astype(np.float32)
        side = part["side_sign"].to_numpy(dtype=np.float64)
        value, _n = _partial(
            _feature_values(part, feature_key),
            _outcome(part, horizon, side),
            _controls(part, side),
        )
        if not np.isfinite(value):
            continue
        values.append(value)
        if _sign(value) == pooled_sign and pooled_sign != 0:
            match += 1
    mean = float(np.mean(values)) if values else float("nan")
    return mean, len(values), match


def score() -> dict:
    _assert_split()
    _audit_invalid()
    specs = (
        ("P", "log_age", "log(1 + age_ms)"),
        ("P", "log_trade_size", "log(1 + trade_size_at_price)"),
        ("R", "log_lifetime", "log(1 + lifetime_ms)"),
        ("R", "fate", "fate, fill versus cancel"),
    )
    rows = []
    for study, key, label in specs:
        print(f"scoring {study} {key}", flush=True)
        for horizon in HORIZONS:
            discovery_frame = _load(study, DISCOVERY)
            discovery, discovery_n = _score_block(discovery_frame, key, horizon)
            del discovery_frame
            held_frame = _load(study, HELD_OUT)
            held, held_n = _score_block(held_frame, key, horizon)
            verdict = _label(held, discovery) if horizon == DECISION_HORIZON else ""
            mean_session, defined, match = _session_loop(study, key, horizon, HELD_OUT, _sign(held))
            spread = float("nan")
            if horizon == DECISION_HORIZON and verdict == "SUPPORTED":
                side = held_frame["side_sign"].to_numpy(dtype=np.float64)
                spread = _fifth_spread(
                    _feature_values(held_frame, key),
                    _outcome(held_frame, DECISION_HORIZON, side),
                )
            del held_frame
            rows.append(
                {
                    "study": study,
                    "feature": label,
                    "feature_key": key,
                    "horizon_s": horizon,
                    "decision": horizon == DECISION_HORIZON,
                    "discovery_partial": discovery,
                    "discovery_n": discovery_n,
                    "held_out_partial": held,
                    "held_out_n": held_n,
                    "held_out_mean_session_partial": mean_session,
                    "held_out_sessions_defined": defined,
                    "held_out_sessions_matching_pooled_sign": match,
                    "verdict": verdict,
                    "fifth_spread_1s": spread,
                }
            )
            print(
                f"  h={horizon} discovery={discovery:.6f} held={held:.6f} n={held_n} {verdict}",
                flush=True,
            )
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "partial_association.csv", index=False)
    decision = table[table["decision"]].copy()
    question = _question_label(decision["verdict"].tolist())
    p_only = _question_label(decision.loc[decision["study"] == "P", "verdict"].tolist())
    payload = {
        "replay_version": REPLAY_ENGINE_VERSION,
        "question_verdict": question,
        "study_p_verdict": p_only,
        "partial_floor": PARTIAL_FLOOR,
        "decision_horizon_s": DECISION_HORIZON,
        "rows": rows,
    }
    (OUT / "verdict.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_report(table, question, p_only)
    return payload


def _fmt(value: float) -> str:
    if not np.isfinite(value):
        return ""
    return f"{value:.6f}"


def _write_report(table: pd.DataFrame, question: str, study_p: str) -> None:
    lines = [
        "# Order lifetime and cancel-versus-fill fate",
        "",
        "The definitions in `PREREGISTRATION.md` were not changed. This file records the one scoring pass.",
        "",
        f"Question verdict: `{question}`",
        "",
        f"Study P, the two real-time features together: `{study_p}`",
        "",
        "Study R is not a real-time signal. A supported association is not an execution rule.",
        "",
        "The decision row is the held-out 1-second partial association. A feature is supported only when that absolute value is at least 0.02 and the sign matches discovery. Horizons 5, 15, and 30 seconds are confirmatory and do not change the label.",
        "",
        "| Study | Feature | Horizon | Discovery partial | Held-out partial | Held-out N | Mean session partial | Sessions matching pooled sign | Verdict |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in table.itertuples(index=False):
        match = f"{row.held_out_sessions_matching_pooled_sign}/{row.held_out_sessions_defined}"
        lines.append(
            f"| {row.study} | {row.feature} | {row.horizon_s} | {_fmt(row.discovery_partial)} | "
            f"{_fmt(row.held_out_partial)} | {row.held_out_n} | {_fmt(row.held_out_mean_session_partial)} | "
            f"{match} | {row.verdict} |"
        )
    supported = table[(table["decision"]) & (table["verdict"] == "SUPPORTED")]
    if not supported.empty:
        lines.extend(["", "## Fifth-to-fifth spread", ""])
        lines.append("Reported only for a supported 1-second feature. It is not a gate.")
        lines.append("")
        for row in supported.itertuples(index=False):
            lines.append(
                f"- {row.study} {row.feature}: held-out mean top fifth minus mean bottom fifth "
                f"of the side-signed 1-second mid change = {_fmt(row.fifth_spread_1s)} points."
            )
    lines.extend(["", "## Reading", "",])
    if study_p == "NOT SUPPORTED":
        lines.append(
            "Study P does not clear the gate. On this sample, age so far and trade size already printed at the order's price add no incremental 1-second directional association beyond the four one-second controls. That closes this real-time order-fate test. It does not authorize another feature search."
        )
    elif study_p == "SUPPORTED":
        lines.append(
            "Study P clears the gate as an incremental association inside this 26-morning sample. That is not a strategy. The next question would be why the association exists, and only after that whether it survives execution. No entry, stop, or threshold is defined here."
        )
    else:
        lines.append(
            "Study P is inconclusive under the frozen rule. The real-time order-fate question is not established, and it is not a strategy."
        )
    lines.append("")
    REPORT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    result = score()
    print(result["question_verdict"], result["study_p_verdict"])
