# Step 4 — Wyckoff Translation Audit

**Status:** Complete.  
**Date:** 2026-09-22  
**Scope:** Evaluate whether Strategy 50 tested Wyckoff-as-sourced, or a much narrower researcher-built object.  
**Forbidden here:** outcome joins, parameter rescue of Step 3, strategy construction.

Governing context: Steps 1–3 remain frozen. Step 3 verdict stays **`INCONCLUSIVE`**. This audit does not reopen or rewrite that experiment.

---

## Closing question

> Did we faithfully translate the source framework, or did our quantitative operationalization accidentally manufacture a 20-event phenomenon?

**Answer:** The 20 Class-C events are primarily a property of a **stacked researcher-defined machine grammar**, not a direct count of “how often Wyckoff springs occur.” The source concept is broader and more discretionary than the intersection of rules we froze.

That does **not** mean Wyckoff is false. It means Strategy 50 tested:

> **our frozen NQ 15m operationalization of a Wyckoff-like sequence**

not:

> **Wyckoff as practiced / as stated qualitatively in the sources.**

---

## 1. Source concept vs our implementation

| Rule / object | In Wyckoff sources? | Class | Notes |
| --- | --- | --- | --- |
| Trading range / equilibrium after trend halt | Yes | `SOURCE-EXPLICIT` concept | |
| Boundary penetration then return into range | Yes (spring / UT) | `SOURCE-EXPLICIT` core geometry | |
| “Quickly” returns / “late” in the range | Yes (qualitative) | `SOURCE-INSPIRED` | No numeric bars in sources |
| Test with better extreme + lesser volume | Yes | `SOURCE-EXPLICIT` intent | Exact averages / windows ours |
| Effort vs result | Yes | `SOURCE-EXPLICIT` | Used only via confirm volume |
| 15-minute bars | No | `RESEARCHER-DEFINED` | Convenience / noise control |
| Swing pivots `L=2` | No | `RESEARCHER-DEFINED` | |
| ≥12-bar TR development | No | `RESEARCHER-DEFINED` | Phase B proxy |
| Late filter ≥8 bars after eligibility | No | `RESEARCHER-DEFINED` | “Late Phase C” proxy |
| ATR tolerances / min height | No | `RESEARCHER-DEFINED` | |
| Min violation `max(1 tick, 0.05×height)` | No | `RESEARCHER-DEFINED` | |
| **Max excursion `1× TR_height`** | **Not in sources** | **`RESEARCHER-DEFINED`** | Strong filter |
| **Recovery ≤ 6 × 15m bars (~90m)** | **Not in sources** | **`RESEARCHER-DEFINED`** | Operationalizes “quickly” |
| Confirm window ≤ 12 bars | No | `RESEARCHER-DEFINED` | |
| Specific test-pullback construction | No | `RESEARCHER-DEFINED` | |
| Omit PS/SC/AR/ST phase labeling | Scope choice | `RESEARCHER-DEFINED` | Avoids discretion; also drops campaign narrative |
| Omit SOS/SOW / nine tests / P&F | Scope choice | `RESEARCHER-DEFINED` | |

**Bottom line:** the only parts that are truly source-explicit are the *ideas* of TR, false boundary break + return, and a confirmatory better-extreme / lesser-volume test. Almost every numeric gate that made C rare is ours.

---

## 2. Funnel reminder (Step 2, frozen grammar)

```text
2,402 eligible TRs
 → 4,491 terminal violations
 → 480 returns into TR
 → 221 candidate tests
 → 20 Class C
```

| Abort at violation→return (from `funnel.json`) | Count |
| --- | ---: |
| Excursion cap (`>1× TR_height`) | **3,538** |
| Acceptance (4 closes outside) | 285 |
| Segment break | 188 |
| Pure recovery timeout (`R_max`) | **0** |

So under the **joint** frozen rules, the 6-bar window almost never “times out.” Failures inside the window are dominated by the **excursion cap** (plus acceptance/gaps).

---

## 3. Decomposition: 6-bar vs 1×height

Descriptive counterfactual paths on frozen-style violation *starts*  
(`results/translation_audit_summary.json`; `translation_violation_paths.parquet`).

**Caveat:** this replay records **1,817** violation starts vs funnel **4,491**, because concurrency / early-abort bookkeeping is slightly simplified. Use it for **relative** 6-bar vs excursion evidence, and keep the funnel as the authoritative absolute collapse.

Within the 1,817:

| Recovery definition | Count | Share of violations |
| --- | ---: | ---: |
| Frozen return (`≤6` bars **and** never `>1×` height) | 771 | 42% |
| Return within 6 bars **ignoring** excursion cap | 952 | 52% |
| Killed **only** by excursion cap at the 6-bar horizon | **181** | — |
| No return within 6 even ignoring excursion | **865** | 48% |
| Return within 12 ignoring excursion | 1,101 | |
| Return within 24 ignoring excursion | 1,177 | |
| Return within 48 ignoring excursion | 1,202 | |

Extras from lengthening the window (ignore excursion):

- 6 → 12: **+149**
- 12 → 24: **+76**
- 24 → 48: **+25** (diminishing)

Among the 952 that would return within 6 ignoring the cap:

- max excursion ≤ 1×: 771  
- max excursion > 1×: 181  
- median max excursion ≈ **0.30×** height; p90 ≈ **1.36×**

### Reading

1. **Pure 6-bar timeout is not the silent killer** in the frozen joint system (`timeout=0` in the funnel).
2. **Many violations never return quickly at all** (~half in the audit sample even with no excursion cap).
3. **The 1× height cap still removes a material minority** of otherwise-valid 6-bar returns (~19% of ign6 returns in the audit sample) and, in the full funnel, is the labeled cause of most recovery aborts (3,538).
4. Lengthening “quickly” from ~90m toward several hours adds returns, but **does not by itself get anywhere near a large Class-C sample** once confirmation remains as frozen (221 → 20).

---

## 4. Prevalence ladder (recovery geometry only — not a new test)

```text
P0  frozen return (6 + 1×exc)              ~480 funnel / 771 audit subset
P1  return ≤6 bars, ignore exc             higher than P0
P2  return ≤12 bars, ignore exc            modest add
P3–P4  ≤24 / ≤48 bars                      diminishing
P5  Step 2 candidate tests                   221
P6  Step 2 Class C                            20
```

Even a much looser recovery definition only addresses the **middle** of the stack. Class C also requires the full confirm grammar (better extreme + lesser volume + window + construction). That second choke (221 → 20) is still severe.

**None of P1–P4 is a Step 3 replacement.** They are translation diagnostics.

---

## 5. Why people study Wyckoff (and why 20 ≠ “Wyckoff is rare”)

A practitioner’s object typically includes discretionary campaign reading:

- phases A–E, PS/SC/AR/ST, SOS/SOW  
- multiple tests, backups, effort–result judgment  
- ranges on **chosen** scales (often daily / multi-day for classical stock work)  
- springs that are “late” by eye, not by `≥8` fifteen-minute bars  

Our algorithm instead asks whether a **local 15m geometry** satisfies a long conjunction of numeric gates. That conjunction can be rare even when a human would still annotate a spring on a higher-scale chart.

So:

> **20 is too small to conclude the underlying Wyckoff phenomenon is rare on NQ.**  
> It is large enough to conclude our **frozen operationalization is extremely selective.**

---

## 6. What this means for the research program

| Keep | Do not do |
| --- | --- |
| Step 3 = `INCONCLUSIVE` (underpowered C) | Loosen rules and re-label as Strategy 50 Step 3 |
| Treat 50 as a completed, honest negative-on-power experiment for *this* grammar | Claim Wyckoff is falsified |
| If continuing Wyckoff: **new preregistration** with fewer researcher-defined gates, explicit scale choice, and a prevalence target stated *before* outcomes | Quietly delete the excursion cap because C was small |

### Legitimate next Wyckoff specification directions (only as new freezes)

Examples of translation reforms that would need their own Step 1 — not patches to 50:

1. **Scale:** define springs on daily / multi-session ranges (closer to classical campaign charts), not only 15m local boxes.  
2. **Recovery:** replace `1× height` + `6` bars with source-nearer language (“returns and holds back in range”) with a single predeclared window, or excursion cap justified from sources (there isn’t one).  
3. **Campaign state:** require a coarser TR with repeated tests before terminal events (more Wyckoff, not less).  
4. **Confirmation:** keep better-extreme + lesser volume (source-explicit) but simplify test detection.

---

## Artifacts

| Path | Role |
| --- | --- |
| `results/funnel.json` | Absolute Stage 2 funnel |
| `results/translation_audit_summary.json` | 6-bar vs excursion counterfactuals |
| `results/translation_violation_paths.parquet` | Per-violation path facts |
| `FUNNEL_DIAGNOSTIC.md` | Earlier descriptive funnel |
| `STEP3_REPORT.md` | Frozen outcome verdict (unchanged) |

---

## Final Step 4 statement

Strategy 50 did **not** measure “how often Wyckoff occurs.”  
It measured how often a **tight, multi-gate, researcher-quantized 15m sequence** occurs.

The skepticism that “20 events in 16 years cannot be the whole Wyckoff object” is **justified**.  
The correct response is **translation reform via a new preregistration**, not a rescue of the frozen run.
