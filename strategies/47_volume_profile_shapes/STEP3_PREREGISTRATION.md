# Preregistration — Step 3 prior-session structural boundaries

Date frozen: 2026-09-20, before any Step 3 boundary table, next-session interaction count, or gallery was computed.

This file does not replace earlier preregistrations. Step 2 region and gap tables are inputs. The 0.20 separation cut and the 0.30 valley-depth cut stay exactly as in Step 2. They are not searched against next-session behavior.

Step 3 does not test profitability, entries, exits, stops, targets, forward returns, or P&L. An interaction is not a trade.

## Question

When a prior analysis session contains a material separation between two accepted volume regions, and the next analysis session's price first meets the low-volume band between those regions, does the path into that band differ by where price came from: the lower region, the upper region, or outside the prior structure?

This is a structural audit of the interaction. It is not a claim that the band predicts direction.

## Sample

Prior sessions and gaps come from:

- `results/step2_sessions.csv`
- `results/step2_regions.csv`
- `results/step2_gaps.csv`
- `results/profile_shape_dataset.parquet`

Re-verify the Step 1 analysis sample the same way Step 1B and Step 2 did. If it is not 96 sessions with P-like 1, b-like 2, D-like 0, B-like 7, UNCLASSIFIED 86, stop.

A prior gap is eligible when `material` is true in the stored Step 2 gap table. Do not re-rank gaps by valley depth. Do not drop a gap because it is unclean or because one region is thin. Those facts are stored and used only for descriptive cross-tabs.

The next session is the next later `session_date` that is also in the analysis sample. If no later analysis session exists, the prior gap is counted as `no_next_session` and excluded from the interaction table. Do not bridge through a missing day by inventing a session.

## Session clocks

Profile `session_date` uses the Step 1 rule: New York time at or after 18:00 belongs to that calendar date. The economic window is `[18:00, next 18:00)`.

Next-session prices are built from the same Databento `trades_24h_*.dbn.zst` files used in Step 1. Positive-size trades in the next profile session are aggregated to one-minute OHLC in `America/New_York`. The continuous `nq_1m_continuous.parquet` file is not used for interaction, because roll adjustment moves absolute prices away from the unadjusted profile grid.

Sync check: for every next analysis session in the interaction sample, the trade-built one-minute high and low must each match that session's stored profile high and low within 1.0 point. If any pair fails, stop.

The next session is already an analysis-sample session, so Step 1 already required it to be complete. The trade-built minute bars must still contain at least one bar whose open is in 18:00–18:05 ET inclusive and at least one bar in 16:00–16:59 ET. If either check fails, count the row as `incomplete_next_trades` and exclude it from the interaction table.

## Boundary object

One row per eligible prior material gap.

Take the two regions that the gap splits: the region that owns the valley tick (lower region) and the region that starts on the next tick (upper region).

Record, all from the prior session only:

| Field | Definition |
| --- | --- |
| `lower_hvn_price` | Price of the left major peak of the gap |
| `upper_hvn_price` | Price of the right major peak of the gap |
| `lower_mode_price` | Mode price of the lower region |
| `upper_mode_price` | Mode price of the upper region |
| `lower_left` / `lower_right` | Prior lower-region price span |
| `upper_left` / `upper_right` | Prior upper-region price span |
| `separation` | Stored Step 2 gap separation |
| `valley_price` | Stored valley price |
| `valley_depth` | Stored valley depth, for audit only |
| `clean` | Stored clean flag |
| `minor_peaks_between` | Stored count |
| `lower_share` / `upper_share` | Region volume shares |
| `both_regions_sized` | `min(lower_share, upper_share) >= 0.25` |
| `poc_price` | Prior POC |
| `lower_mode_to_poc` | `lower_mode_price - poc_price` |
| `upper_mode_to_poc` | `upper_mode_price - poc_price` |
| `profile_low` / `profile_high` | Prior profile extremes |

`0.25` is frozen here as a size label. It is not a trading filter and is not revised after results.

## Valley width

Valley depth is not used to rank boundaries. Width is.

Between the two major peaks, exclusive of the peak ticks, a tick is low-volume when:

```text
volume <= 0.70 * min(left_peak_volume, right_peak_volume)
```

`0.70` is the complement of the frozen 0.30 depth cut. It is not a new search.

The low-volume band is the maximal contiguous run of such ticks that contains the valley tick. If the valley tick is not low-volume under that rule, stop for that gap.

```text
valley_width_ticks = right_edge_index - left_edge_index + 1
valley_width = valley_width_ticks / R
valley_left_price = price at left_edge_index
valley_right_price = price at right_edge_index
```

`R` is the prior profile's range in ticks. The interaction target is the closed price interval `[valley_left_price, valley_right_price]`.

## Zones on the next session

Using only prior prices:

| Zone | Rule |
| --- | --- |
| `lower_region` | `lower_left <= price <= lower_right` |
| `upper_region` | `upper_left <= price <= upper_right` |
| `lvn_band` | `valley_left_price <= price <= valley_right_price` |
| `outside_below` | `price < profile_low` |
| `outside_above` | `price > profile_high` |
| `other_inside` | inside `[profile_low, profile_high]` but in none of the rows above |

`other_inside` can occur when the prior day had three regions and this gap is only one of the splits: price may sit in a third accepted region. It is reported, not forced into lower or upper.

A one-minute bar intersects a zone when its high/low range overlaps that zone's closed interval.

## First interaction

Scan the next session's bars in time order.

The first interaction bar is the first bar whose `[low, high]` intersects the LVN band. If no bar does, the outcome is `no_touch`. That is an audit count, not a failure of the prior object.

Approach location:

- If the first bar of the session is the interaction bar, approach is `open_in_band` when the open lies in the LVN band, otherwise the zone of the open under the table above.
- If a later bar is the first interaction, approach is the zone of the previous bar's close.

Allowed approach labels for the primary cross-tab:

```text
lower_region
upper_region
outside_below
outside_above
other_inside
open_in_band
```

If the previous close falls in `lvn_band` but the previous bar was not counted as the first interaction, stop. That case means the intersection rule failed and must not be patched.

Also store, still without returns:

- Session-open zone, using the first bar's open
- Minutes from the first bar's open timestamp to the interaction bar's open timestamp
- Whether any later bar after the interaction intersects the opposite HVN side: if approach was `lower_region`, the opposite side is a touch of `upper_hvn_price` or higher into the upper region; if approach was `upper_region`, the opposite side is a touch of `lower_hvn_price` or lower into the lower region; for outside approaches, record whether both HVNs are touched later
- Whether any later bar after the interaction returns into the approach zone, when approach was `lower_region` or `upper_region`

None of those later-path flags is a P&L. They are path audits.

## Primary summaries

Report counts and shares only:

1. How many eligible prior gaps have a usable next session.
2. Touch rate: share with a first LVN-band touch.
3. Approach mix among touches.
4. The same approach mix on the `both_regions_sized` subset and on the `clean` subset, separately. Do not invent a new combined filter after seeing the numbers.
5. Open-zone mix for all usable next sessions, including no-touch rows.
6. Width and separation distributions of the boundary objects. Do not sort the sample by valley depth.

## What this step will not do

- It will not change 0.20, 0.30, 0.25, or 0.70 after looking at touches.
- It will not compute a forward return, MFE, MAE, or win rate.
- It will not choose an entry at the band.
- It will not treat `clean` or `both_regions_sized` as a strategy filter.
- It will not revive P, b, D, or B labels as the object under test.
