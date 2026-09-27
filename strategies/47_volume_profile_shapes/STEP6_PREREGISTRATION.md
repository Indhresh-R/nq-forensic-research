# Preregistration — Step 6 prior volume location / acceptance

Date frozen: 2026-09-21, before any Step 6 next-session location table, migration count, or POC-reference tally was computed.

This file starts a **new** branch. It does not reopen Steps 2–5. It does not use LVN bands, traverse events, or reject events as inputs. The killed HVN→LVN→reaction story is not revived here.

Step 6 does not test profitability, entries, exits, stops, targets, forward returns, or P&L.

## Question

Does the prior analysis session’s **where volume sat** (POC location and upper/middle/lower concentration) relate to **where the next analysis session trades**, in the sense of:

- opening near or far from the prior POC,
- spending time near the prior high-volume region,
- migrating away from it,
- or treating the prior POC as a reference level that is touched / crossed?

This is an acceptance/location audit. It is not a support/resistance claim about LVNs.

## Sample

Use the same 96 analysis sessions as Steps 1–2 (`in_analysis_sample`, verified as before).

A pair is eligible when both the prior session and the next later analysis `session_date` are in that sample. Do not bridge missing days. Expected pair count equals the number of analysis sessions that have a later analysis session (from Step 3: 95 adjacent analysis pairs exist in the date list; confirm and stop if the verification identity breaks).

Prior geometry comes from stored Step 1 / Step 2 session columns and `raw_price_volume.parquet`. Do not rebuild the session clock.

Next-session path uses the same trade-built one-minute OHLC construction as Step 3 (not continuous adjusted bars), with the same high/low sync check against the next session’s stored profile.

## Prior-session location inputs (known before the next open)

From the prior session only:

| Field | Definition |
| --- | --- |
| `prior_poc` | Stored POC price |
| `prior_poc_location` | Stored POC index / range |
| `prior_lower_share` | Step 2 lower-third volume share |
| `prior_middle_share` | Step 2 middle-third volume share |
| `prior_upper_share` | Step 2 upper-third volume share |
| `prior_dominant_third` | Step 2 dominant third |
| `prior_vw_std_norm` | Stored normalized volume-weighted std |
| `prior_poc_concentration_10` | Stored POC concentration |
| `prior_profile_low` / `prior_profile_high` | Prior extremes |
| `prior_range` | `prior_profile_high - prior_profile_low` |

No LVN width, no material-gap flag, and no region-count filter enters the primary tables. Those may appear only as a later descriptive cross-tab, not as a gate.

## Next-session location measurements

Using next-session one-minute bars:

1. **Open distance to prior POC**
   ```text
   open_to_poc = first_bar_open - prior_poc
   open_to_poc_frac = open_to_poc / prior_range
   ```

2. **Open third relative to prior profile**
   Map the first-bar open onto the prior session’s lower/middle/upper third cuts (same integer third rule as Step 2, on the prior range). Labels: `prior_lower`, `prior_middle`, `prior_upper`, or `outside_below` / `outside_above`.

3. **Time near prior POC**
   A bar is near the prior POC when its `[low, high]` intersects
   ```text
   [prior_poc - 0.10 * prior_range, prior_poc + 0.10 * prior_range]
   ```
   `0.10` reuses the Step 1 POC-band fraction. It is not searched.
   Report the share of next-session bars that are near, and minutes until the first near touch (`no_touch` if never).

4. **Migration**
   Let `next_vwap_proxy` be the volume-weighted mean of next-session trade prices on the trade-built minute bars (volume-weighted typical price `(h+l+c)/3` by bar volume).  
   ```text
   migration_frac = (next_vwap_proxy - prior_poc) / prior_range
   ```
   Sign follows price. This is a location shift, not a return series for P&L.

5. **Prior POC as reference**
   - `touched_poc_band`: any near touch as in (3)
   - `crossed_poc`: some bar has `low <= prior_poc <= high` (exact level, not the 10% band)
   - After the first cross, whether the session’s later minute closes are predominantly above or below `prior_poc` (count of closes above minus closes below, after the cross bar). Descriptive only.

## Primary summaries (no P&L)

1. Distribution of `open_to_poc_frac` and open third.
2. Cross-tab: prior dominant third × next open third.
3. Share of sessions that touch the prior POC band; median time to first touch.
4. Distribution of `migration_frac`, including split by prior dominant third.
5. Among sessions that touch the POC band, the after-cross close imbalance.

No null that uses LVN geometry. A later step may add a location null; this step only measures the location object.

## What this step will not do

- It will not use LVN bands, traverse, or reject outcomes.
- It will not add ATR, day-of-week, opening-range, CVD, MBO, or direction filters.
- It will not compute strategy P&L.
- It will not change the 0.10 POC-band fraction after seeing tables.
