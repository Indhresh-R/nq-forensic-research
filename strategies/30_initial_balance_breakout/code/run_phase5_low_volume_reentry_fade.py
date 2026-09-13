"""Causal fade of a low-volume IB breakout after five-minute re-entry."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]; sys.path.insert(0,str(ROOT))
from common.nq_session import load_nq  # noqa: E402
ART=ROOT/"artifacts"/"30_initial_balance_breakout"; OPEN=570; IB_END=630; LAST_CLOSE=929; FLAT=955; TICK=.25; COST=1.0
def split(y): return "Train" if y<=2018 else "Inner_Validation" if y<=2021 else "Validation" if y<=2024 else "OOS"

def result(side,entry,stop,target,g,entry_min):
    for m in range(entry_min,FLAT):
        hi,lo=float(g.at[m,"high"]),float(g.at[m,"low"])
        hs=lo<=stop if side>0 else hi>=stop; ht=hi>=target if side>0 else lo<=target
        if hs: return stop,"stop" # hostile same-minute rule
        if ht: return target,"target"
    return float(g.at[FLAT,"open"]),"time"

def main():
    base=pd.read_csv(ART/"nq_baseline_trades.csv")
    nq=load_nq(); nq=nq[(nq.ny_min>=OPEN)&(nq.ny_min<=FLAT)].copy(); nq["sd"]=nq.session_date.astype(str); nq["bucket"]=(nq.ny_min-OPEN)//5
    five=(nq.groupby(["sd","bucket"],as_index=False).agg(open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"),volume=("volume","sum"),close_min=("ny_min","last")))
    # Frozen threshold is the lowest Train tertile of signal-bar / IB average 5m volume.
    ib=(nq[nq.ny_min<IB_END].groupby("sd",as_index=False).agg(ib_volume=("volume","sum")))
    signal=base.merge(ib,left_on="session_date",right_on="sd",how="left").merge(five,left_on=["session_date","signal_ny_min"],right_on=["sd","close_min"],how="left",suffixes=("","_sig"))
    signal["relative_volume"]=signal.volume/(signal.ib_volume/12)
    threshold=signal[signal.year<=2018].relative_volume.quantile(1/3)
    eligible=signal[signal.relative_volume<=threshold].copy()
    sessions={sd:g.sort_values("ny_min").set_index("ny_min") for sd,g in nq.groupby("sd",sort=False)}
    five_by={sd:g.sort_values("close_min") for sd,g in five.groupby("sd",sort=False)}
    rows=[]
    for _,t in eligible.iterrows():
        g=sessions.get(t.session_date); bars=five_by.get(t.session_date)
        if g is None or bars is None: continue
        breakout_side=1 if t.side=="long" else -1
        # First later 5m close back inside the original IB. It is known only at `close_min`.
        later=bars[(bars.close_min>t.signal_ny_min)&(bars.close_min<=LAST_CLOSE)]
        inside=(later.close<=t.ib_high) if breakout_side>0 else (later.close>=t.ib_low)
        hit=later[inside]
        if hit.empty: continue
        r=hit.iloc[0]; reentry_close=int(r.close_min); entry_min=reentry_close+1
        if entry_min>=FLAT: continue
        side=-breakout_side; entry=float(g.at[entry_min,"open"])
        route=bars[(bars.close_min>=t.signal_ny_min)&(bars.close_min<=reentry_close)]
        # The extreme of the rejected excursion is the invalidation level.
        stop=(float(route.high.max())+TICK) if side<0 else (float(route.low.min())-TICK)
        risk=side*(entry-stop)
        if risk<=0: continue
        for target_name,target in (("ib_mid",(float(t.ib_high)+float(t.ib_low))/2), ("opposite_ib",float(t.ib_low) if side<0 else float(t.ib_high))):
            reward=side*(target-entry)
            if reward<=0: continue
            exit_price,kind=result(side,entry,stop,target,g,entry_min)
            rows.append({"session_date":t.session_date,"year":t.year,"split":split(t.year),"side":"long" if side>0 else "short","relative_volume":t.relative_volume,"reentry_close_min":reentry_close,"entry_min":entry_min,"entry":entry,"stop":stop,"target":target,"target_name":target_name,"risk_points":risk,"reward_r":reward/risk,"exit_kind":kind,"net_points":side*(exit_price-entry)-COST})
    out=pd.DataFrame(rows)
    sums=[]
    for (target_name,sp),x in out.groupby(["target_name","split"]):
        p=x.net_points.to_numpy(float); w,l=p[p>0],p[p<0]
        sums.append({"target":target_name,"split":sp,"trades":len(x),"avg_net_points":p.mean(),"win_rate":(p>0).mean(),"profit_factor":w.sum()/abs(l.sum()) if len(l) else np.nan,"median_risk":x.risk_points.median(),"median_reward_r":x.reward_r.median(),"target_rate":(x.exit_kind=="target").mean(),"stop_rate":(x.exit_kind=="stop").mean()})
    summary=pd.DataFrame(sums); out.to_csv(ART/"nq_phase5_low_volume_fade_trades.csv",index=False); summary.to_csv(ART/"nq_phase5_low_volume_fade_summary.csv",index=False)
    report=["# NQ IB — low-volume re-entry fade", "", f"Low relative-volume threshold (frozen from 2010–2018 lower tertile): **{threshold:.3f}**.", "", "Rules: first baseline IB breakout must be low-volume; wait for the first later completed five-minute close back inside IB; enter opposite direction at the next one-minute open; stop beyond the excursion extreme plus one tick. Both IB-midpoint and opposite-IB targets are reported as predeclared alternatives.", "", "## Results", "", summary.to_markdown(index=False) if len(summary) else "_No trades._", "", "Same-minute stop/target collision is a stop. Costs are 1.0 NQ point round trip. The target variant must be selected only from Train + Inner Validation."]
    (ART/"nq_phase5_low_volume_fade_report.md").write_text("\n".join(report),encoding="utf-8")
    print(summary.to_string(index=False))

if __name__=="__main__": main()
