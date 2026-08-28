# QPF agreement: the forecaster vs the blend — design note (2026-08-28)

Both now exist per basin per cycle: the WPC forecaster's 24-h windows
(`basin_qpf_24h_official`, OFFICIAL_FORECAST, Day 1/2/3 of each 00/12Z cycle) and the NBM
blend (`basin_qpf_{24,48,72}h_*`, MODELED, cumulative windows with pointwise percentiles and a
deterministic member). Their DISAGREEMENT is information (DATA_DOCTRINE §10) and must never
become an average. This note fixes the semantics before any code exists, because the failure
modes here are all quiet arithmetic.

## What may be compared (and what may not)

1. **Day-1, directly.** WPC f024 covers cycle+0..24 h; NBM's 24-h window covers the same
   period of the same nominal cycle. Same window, same basin mask family → the difference is a
   fact about the two products.
2. **The 72-h totals.** WPC Day 1+2+3 summed (the total the forcing surface already carries)
   vs the NBM 72-h window. Same period; both are totals; comparable.
3. **NOT Day-2/Day-3 individually.** NBM stores CUMULATIVE windows, and differencing
   percentile fields is invalid arithmetic: `p50(0–48) − p50(0–24)` is not `p50(24–48)` —
   percentiles do not subtract. Only the deterministic NBM member could be differenced, and a
   one-member comparison against the forecaster adds little over the two comparisons above.
   Deliberately out of scope.
4. **Cycle identity is exact.** Compare only rows whose `issued_at` is the SAME nominal
   instant (both products cycle at 00/12Z). The availability skew is real and reported — WPC
   publishes ~48 min BEFORE the nominal hour, NBM's windows land ~7.5 h after — so at most
   knowledge times one side is a cycle ahead; then there is NO comparison, with the reason,
   rather than a stale-vs-fresh one presented as agreement.

## What is reported

Per basin, when a matching cycle pair exists:

- `delta_mm = official − blend_p50` and the same against the deterministic member, each signed;
- **placement**: whether the official total falls inside the blend's pointwise p10–p90 band —
  ALWAYS carrying the pointwise caveat verbatim (a basin mean of per-cell percentiles is not a
  basin-scale percentile band; "inside the band" is therefore a qualified statement, and the
  qualification travels with it);
- no ratio when the blend p50 is < 1 mm (a 0.2-vs-0.6 mm "3×" reads as violent disagreement
  about nothing; the delta already says everything at trace amounts).

## Where it surfaces

The FORCING surface's drivers — beside the existing official-total context driver — as
`qpf_official_vs_blend_24h_delta` and `qpf_official_vs_blend_72h_delta`, direction
`context_not_scored`, prov naming BOTH cycles and both products. NOT the agreement surface:
`AgreementState` is the river-crest comparison at the outlet, and folding a forcing-level
comparison into it would let one word ("agreement") mean two different measurements. If a
dedicated contract field is ever wanted, that is a 1.5.0 discussion with its own note.

## What the method id pins

`method:qpf-agreement@1.0.0`: the window-alignment rule (§1), the same-cycle rule (§4), the
no-percentile-differencing rule (§3), the sub-millimetre ratio suppression (§2). Any change to
one of these is a new method version, because each changes what a rendered number means.

## Test obligations (before code ships)

- same-cycle enforcement: an offset pair (WPC 00Z vs NBM 12Z) yields NO driver, with reason;
- percentile subtraction is nowhere in the code path (mutation: introduce it; a Day-2 test
  must catch the fabricated window);
- the pointwise caveat reaches the rendered label verbatim;
- trace-amount suppression: p50 = 0.4 mm yields delta only, never a ratio.
