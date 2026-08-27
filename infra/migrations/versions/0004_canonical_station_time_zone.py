"""Correct the one seeded station time zone the deployment image cannot resolve.

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-27

Stations were seeded `time_zone='PST8PDT'`. It names Pacific time and a developer laptop
resolves it, but `python:3.14-slim` ships Debian's `tzdata` without `tzdata-legacy` — 486
resolvable keys over 436 distinct zone files, with the POSIX aliases dropped — so `ZoneInfo`
raised there. `climatology.daily_mean_valid_time` did what it promises with an unresolvable
zone: it fell back to the UTC day boundary and flagged `day_boundary_assumed_utc`. The rows
were honest and the surface was dead, because a UTC-stamped row sits 7 h (PDT) or 8 h (PST)
from a correctly stamped one, past `STATE_CHANGE_TOLERANCE_H = 6`, so the 24 h velocity refused
every pairing (ADR-0017).

The seed already carries the canonical name as of 603d5cb. This migration exists because
CONFIGURED reference data that is already in a database is not corrected by changing the seed
file — re-seeding is a separate, manual act, and until it happens production keeps the old
value with nothing warning anyone. Shipping the correction as a migration puts it on the path
the deployment already runs.

Deliberately narrow, for three reasons:

- **Only `station.time_zone`, and only where it is exactly the legacy alias.** No other column
  and no other table is touched, so the change cannot move a hydrologic value.
- **Idempotent by construction.** The `WHERE` clause is the guard: a second run matches nothing.
  It is also safe to run against a database seeded after 603d5cb, where it matches nothing.
- **`US/Pacific` and the other dropped aliases are NOT swept up.** Nothing was ever seeded with
  them; correcting values nobody wrote would be a blanket assumption of exactly the kind
  `SEEDABLE_TIME_ZONES` exists to refuse. If one ever appears, that is a seed bug to fix at the
  seed, and the seed now rejects it before it can be written.

Historical `derived_feature` rows keep their `day_boundary_assumed_utc` flag and their
UTC-midnight `valid_time`. They are evidence of when the boundary was guessed, and DATA_DOCTRINE
forbids rewriting them; the 24 h growth returns on its own once two correctly stamped daily rows
exist. Nothing here backfills one into existence.

The literals below are duplicated from `cascade_core.seed` rather than imported. A migration is
a historical record of a database state and must keep meaning the same thing after the
application constant moves on — importing it would make this file's behaviour change retroactively.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

#: The legacy POSIX alias seeded before 603d5cb, and the canonical IANA name replacing it.
LEGACY_ALIAS = "PST8PDT"
CANONICAL_ZONE = "America/Los_Angeles"


def upgrade() -> None:
    result = op.get_bind().execute(
        sa.text("UPDATE station SET time_zone = :canonical WHERE time_zone = :legacy"),
        {"canonical": CANONICAL_ZONE, "legacy": LEGACY_ALIAS},
    )
    # Printed rather than assumed: on a database seeded after 603d5cb this is legitimately 0,
    # and on production it was 7. Either is correct; a surprise is worth seeing in the log.
    print(f"0004: station.time_zone {LEGACY_ALIAS!r} -> {CANONICAL_ZONE!r} on {result.rowcount} row(s)")


def downgrade() -> None:
    """Deliberately a no-op.

    This migration changes no schema, so a downgrade has nothing structural to undo. Writing the
    alias back would reintroduce the defect — every daily mean returns to the UTC boundary in the
    container — and would put the database in a state the current seed can no longer produce,
    since `_validate_time_zones` refuses `PST8PDT` outright. A downgrade that recreates a fixed
    bug is worse than one that does nothing, so this one says so instead.
    """
