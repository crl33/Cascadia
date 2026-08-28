# ADR-0018: Hindcasts replay on a second clock (`knowable_at`), never by rewriting `available_at`

- Status: Accepted
- Date: 2026-08-28
- Amends: ADR-0010 (resolves a divergence between its letter and settled practice)

## Context

ADR-0010's letter said backfilled data should carry "the provider's publication time when
known" as `available_at`. Practice diverged from the first backfill onward, deliberately: the
P2 Event Zero scripts and the 2026-08-28 MRMS backfill all set `available_at` to the
RETRIEVAL instant, because a December-2025 `available_at` on a row written in August 2026
makes `as_known_at` claim this platform knew something before it existed. The MRMS backfill
introduced the third piece: it preserves the instant the data COULD have been known
(`values_json.original_available_at`, from IEM's kept mtimes — measured at the same ~57-minute
publication lag the live pipeline sees today).

The P6 hindcast harness needs exactly that second notion. Replaying the platform's own
knowledge (`as_known_at`) through December 2025 correctly answers UNKNOWN for everything —
true, and useless for evaluating the method. The hindcast question is different: *what would
this method have said, given what was knowable at T?*

## Decision

Three times, three meanings, no overloading:

1. **`valid_time`** — when the world was in this state. Unchanged.
2. **`available_at`** — when THIS PLATFORM first held the value. Always the write-path
   instant; a backfill writes its retrieval time, never a historical one. `as_known_at` and
   every `as_of` API parameter read this clock exclusively, and it can never claim knowledge
   the platform did not have. (This amends ADR-0010's backfill sentence to match settled
   practice.)
3. **`knowable_at`** — when the value was retrievable from its authority. For live-ingested
   rows this IS `available_at` (the two clocks coincide within the poll cadence). For
   backfilled rows it is `values_json.original_available_at`, present only when the archive
   preserved a defensible publication instant (IEM mtimes; NWPS `creation_datetime`; FLS
   issuance headers). It is NEVER inferred from `valid_time` plus an assumed lag.

The hindcast harness gets its own reader, `as_knowable_at(T)`, distinct from `as_known_at` and
never exposed on public API endpoints:

- live-ingested rows: included when `available_at <= T`;
- backfilled rows with a preserved `original_available_at`: included when that instant `<= T`;
- backfilled rows WITHOUT one: **excluded and counted**, never admitted on an assumed lag.

Every hindcast report must open with the audit these rules make possible: how many inputs were
live-measured, how many reconstructed-with-preserved-instant, how many excluded — per product.
A hindcast whose inputs are mostly reconstructed says so in its first table, not a footnote.

## Consequences

- Public replays stay incapable of lying about the platform (`available_at` untouched).
- Backfill scripts have one more obligation: preserve the original instant when the archive
  offers one, under the single key `original_available_at`, or omit it — the harness's
  exclusion count is the honest cost of an archive that kept no times.
- The Dec-2025 MRMS rows are already compliant. The P2 USGS/FLS backfills predate the key;
  before the harness runs over them, a one-off pass should populate it where the archived
  payloads state publication instants (FLS issuance times do; USGS instantaneous values do
  not, and those rows will be counted as excluded — which is itself a finding about how much
  of the December picture was knowable in real time).
- `as_knowable_at` is harness-only. If it ever appears on an API route, that route is
  claiming the platform's history is something it is not.
