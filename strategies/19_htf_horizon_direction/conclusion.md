# Conclusion — Longer-horizon direction

## Verdict

**`B→kill` — CLOSED.** Do not promote. Do not expand `*_follow` variants.

## Refined conclusion (not too strong)

**Not:** “Strategy 12 has no directional information.”

**Yes:**

> Strategy 12 robustly identifies a future change in activity, but the tested
> static and simple directional resolvers do not provide a stable **conditional**
> direction edge (including at longer horizons).

Individual OOS cells can look hot (e.g. London H240 57.9%, NY_PM SESS_END 56.8%,
resolver spikes 58–61%). They fail **stability + conditional lift**
(IS→Val→OOS, multi-clock). Soft `gap_follow` @ NY_AM SESS_END and interesting
`mom15_follow` H240 medians are not enough to promote.

## Escape route closed

> Maybe HIGH doesn’t tell direction immediately, but direction becomes
> identifiable over a longer horizon.

**Strategy 19: FAIL.**

## What not to do next

- No more generic `*_follow` / fade / HTF-location fishing
- Do not retune Strategy 12
- Next class must explain **why one side should win** (see research tree)
