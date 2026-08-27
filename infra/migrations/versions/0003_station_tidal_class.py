"""Station tidal class — the marker rate of rise refuses without.

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-26

`method:rate-of-rise@2.0.0` refuses to publish a rate for a station whose semidiurnal
amplitude has never been measured, because a tide injects a false rate that no estimator
removes: a 1.0 ft M2 signal on a real record produces 4.6-6.5x the STEADY epsilon under every
candidate, and the MOST robust estimator is the WORST of them
(`docs/research/trend-estimator-selection-2026-08-26.md` §5).

The column is nullable and NULL is the refusing state, deliberately. A future station seeded
without a measurement loses its trend rather than silently acquiring a fabricated one; there is
no code path in which an unmarked station is treated as fluvial. The six seeded forecast points
and the Sauk are backfilled to 'FLUVIAL' here on measured evidence only — M2 <= 0.008 ft,
injected 6 h rate <= 0.025 ft/h against a 0.05 ft/h epsilon
(`docs/research/tidal-gauge-verification-2026-08-26.md` §3). SNAW1 12155500 would be 'TIDAL'
(M2 2.97 ft) and is not seeded.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

#: Backfilled ONLY for stations whose tidal class was measured, named explicitly rather than
#: swept with an UPDATE over the whole table: a blanket default is exactly the silent
#: assumption this column exists to prevent.
MEASURED_FLUVIAL = (
    "station:usgs:12119000", "station:usgs:12100490", "station:usgs:12200500",
    "station:usgs:12213100", "station:usgs:12113000", "station:usgs:12149000",
    "station:usgs:12189500",
)


def upgrade() -> None:
    op.add_column("station", sa.Column("tidal_class", sa.String(), nullable=True))
    op.execute(
        sa.text("UPDATE station SET tidal_class = 'FLUVIAL' WHERE id IN :ids").bindparams(
            sa.bindparam("ids", value=MEASURED_FLUVIAL, expanding=True)
        )
    )


def downgrade() -> None:
    op.drop_column("station", "tidal_class")
