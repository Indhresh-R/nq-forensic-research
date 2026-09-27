"""Phase 4: causal comparison of IB continuation versus failed-breakout days."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]; sys.path.insert(0,str(ROOT))
from common.nq_session import load_es, load_nq  # noqa: E402
ART=ROOT/"artifacts"/"30_initial_balance_breakout"; OPEN=570; IB_END=630

def period(y): return "Train" if y<=2018 else "Inner_Validation" if y<=2021 else "Validation" if y<=2024 else "OOS"

def rth_features(df: pd.DataFrame, prefix: str) -> tuple[pd.DataFrame,pd.DataFrame]:
    x=df[(df.ny_min>=OPEN)&(df.ny_min<=959)].copy(); x["sd"]=x.session_date.astype(str)
    x["typ"]=(x.high+x.low+x.close)/3; x["pv"]=x.typ*x.volume
    x["vwap"]=x.groupby("sd",sort=False).pv.cumsum()/x.groupby("sd",sort=False).volume.cumsum()
    x["session_open"]=x.groupby("sd",sort=False).open.transform("first")
    x["path"]=x.groupby("sd",sort=False).close.diff().abs().fillna(0).groupby(x.sd,sort=False).cumsum()
    x["run_high"]=x.groupby("sd",sort=False).high.cummax(); x["run_low"]=x.groupby("sd",sort=False).low.cummin()
    ib=(x[x.ny_min<IB_END].groupby("sd",as_index=False).agg(ib_high=("high","max"),ib_low=("low","min"),ib_volume=("volume","sum"),ib_close=("close","last")))
    ib["ib_width"]=ib.ib_high-ib.ib_low; ib["prior20_med"]=ib.ib_width.shift(1).rolling(20,min_periods=20).median(); ib["ib_vs_prior20"]=ib.ib_width/ib.prior20_med
    x["bucket"]=(x.ny_min-OPEN)//5
    five=(x.groupby(["sd","bucket"],as_index=False).agg(bar_open=("open","first"),bar_high=("high","max"),bar_low=("low","min"),bar_close=("close","last"),bar_volume=("volume","sum"),bar_close_min=("ny_min","last")))
    return x, ib.merge(five, on="sd", how="left")

def main():
    t=pd.read_csv(ART/"nq_baseline_trades.csv")
    # A target before stop is continuation; a stop before target is a failed breakout.
    t=t[t.exit_kind.isin(["target","stop"])].copy(); t["label"]=(t.exit_kind=="target").astype(int); t["period"]=t.year.map(period)
    nq=load_nq(); es=load_es(); nrth,nfive=rth_features(nq,"nq"); erth,_=rth_features(es,"es")
    # NQ state exactly at the already-completed five-minute signal bar.
    at=nrth[["sd","ny_min","vwap","session_open","path","run_high","run_low"]]
    m=t.merge(at,left_on=["session_date","signal_ny_min"],right_on=["sd","ny_min"],how="left")
    f=nfive[nfive.bar_close_min.isin(m.signal_ny_min)][["sd","ib_high","ib_low","ib_width","ib_volume","ib_close","ib_vs_prior20","bar_open","bar_high","bar_low","bar_close","bar_volume","bar_close_min"]]
    m=m.merge(f,left_on=["session_date","signal_ny_min"],right_on=["sd","bar_close_min"],how="left",suffixes=("","_five"))
    # ES's state at the same known minute: a cross-market confirmation, never future data.
    eib=(erth[erth.ny_min<IB_END].groupby("sd",as_index=False).agg(es_ib_high=("high","max"),es_ib_low=("low","min"))).rename(columns={"sd":"es_sd"})
    eat=erth[["sd","ny_min","close"]].rename(columns={"sd":"es_sd","ny_min":"es_ny_min","close":"es_close"})
    m=m.merge(eat,left_on=["session_date","signal_ny_min"],right_on=["es_sd","es_ny_min"],how="left").merge(eib,on="es_sd",how="left")
    side=np.where(m.side.eq("long"),1.0,-1.0)
    m["ib_vs_prior20"]=m.ib_vs_prior20
    m["signal_delay_min"]=m.signal_ny_min-IB_END
    m["breakout_excess_ib"]=side*np.where(m.side.eq("long"),m.bar_close-m.ib_high,m.bar_close-m.ib_low)/m.ib_width
    m["signal_body_fraction"]=(m.bar_close-m.bar_open).abs()/(m.bar_high-m.bar_low).replace(0,np.nan)
    m["signal_range_ib"]=(m.bar_high-m.bar_low)/m.ib_width
    m["signal_vol_vs_ib5mean"]=m.bar_volume/(m.ib_volume/12)
    m["vwap_distance_ib"]=side*(m.bar_close-m.vwap)/m.ib_width
    m["trend_efficiency"]= (m.bar_close-m.session_open).abs()/m.path.replace(0,np.nan)
    m["range_sofar_ib"]=(m.run_high-m.run_low)/m.ib_width
    m["es_confirms"] = ((m.side.eq("long")&(m.es_close>=m.es_ib_high)) | (m.side.eq("short")&(m.es_close<=m.es_ib_low)))
    features=["ib_vs_prior20","signal_delay_min","breakout_excess_ib","signal_body_fraction","signal_range_ib","signal_vol_vs_ib5mean","vwap_distance_ib","trend_efficiency","range_sofar_ib"]
    rows=[]; selections=[]; cuts={}
    for feature in features:
        train=m[m.period.eq("Train")][feature].dropna(); q=train.quantile([1/3,2/3]).to_numpy()
        if len(q)!=2 or q[0]>=q[1]: continue
        cuts[feature]=[float(q[0]),float(q[1])]
        bins=pd.cut(m[feature],[-np.inf,q[0],q[1],np.inf],labels=["Low","Mid","High"])
        for (p,b),x in m.assign(bin=bins).dropna(subset=["bin"]).groupby(["period","bin"],observed=True): rows.append({"feature":feature,"period":p,"bin":str(b),"n":len(x),"continuation_rate":x.label.mean(),"failure_rate":1-x.label.mean()})
    # ES confirmation is already a causal boolean feature.
    for (p,b),x in m.assign(bin=np.where(m.es_confirms,"Confirms","Does_not_confirm")).groupby(["period","bin"]): rows.append({"feature":"es_confirms","period":p,"bin":b,"n":len(x),"continuation_rate":x.label.mean(),"failure_rate":1-x.label.mean()})
    out=pd.DataFrame(rows); out.to_csv(ART/"nq_phase4_continuation_failure_bins.csv",index=False)
    for feature,x in out.groupby("feature"):
        z=x.pivot(index="bin",columns="period",values="continuation_rate"); n=x.pivot(index="bin",columns="period",values="n")
        if {"Train","Inner_Validation"}.issubset(z.columns) and len(z)>=2:
            # strongest vs weakest Train bin must retain ordering in inner validation, with adequate observations.
            hi,lo=z.Train.idxmax(),z.Train.idxmin(); delta_train=z.loc[hi,"Train"]-z.loc[lo,"Train"]; delta_inner=z.loc[hi,"Inner_Validation"]-z.loc[lo,"Inner_Validation"]
            if n.loc[hi,"Train"]>=30 and n.loc[lo,"Train"]>=30 and n.loc[hi,"Inner_Validation"]>=20 and n.loc[lo,"Inner_Validation"]>=20 and delta_train>0 and delta_inner>0:
                selections.append({"feature":feature,"continuation_bin":hi,"failure_bin":lo,"train_gap":delta_train,"inner_gap":delta_inner,"oos_gap":(z.loc[hi,"OOS"]-z.loc[lo,"OOS"]) if "OOS" in z else np.nan})
    sel=pd.DataFrame(selections); sel.to_csv(ART/"nq_phase4_pre2022_patterns.csv",index=False)
    m.to_csv(ART/"nq_phase4_labeled_trades.csv",index=False)
    report=["# NQ IB — continuation vs failed-breakout audit", "", "Labels use only the later outcome: `continuation` = target hit before stop; `failure` = stop hit before target. Time exits are intentionally excluded from this classification. Every candidate feature is known no later than the completed signal bar.", "", f"Clean labeled trades: **{len(m)}** (continuations: {m.label.sum()}, failures: {(1-m.label).sum()}).", "", "## Pre-2022 patterns that preserved their ordering", "", sel.to_markdown(index=False) if len(sel) else "_None met the predeclared Train + Inner Validation rule._", "", "## Full tercile / boolean table", "", out.to_markdown(index=False)]
    (ART/"nq_phase4_continuation_failure_report.md").write_text("\n".join(report),encoding="utf-8")
    print(sel.to_string(index=False) if len(sel) else "No pre-2022 patterns survived.")

if __name__=="__main__": main()
