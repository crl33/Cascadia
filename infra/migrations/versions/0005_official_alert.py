"""Official NWS alerts — storage for the CAP records the envelopes have always promised.

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-28

`BasinVisualizationState.official_alerts` has been in the contract since the spike and the
assembler has emitted `()` for it ever since, because nothing stored an alert. This creates the
table the live `nws.fetch_alerts` job writes.

Design points that are doctrine, not taste:

- **Append-only.** A CAP Update or Cancel arrives as a NEW alert whose `references` name the ids
  it supersedes — the ForecastRun supersession shape. No row is ever mutated; the read path
  resolves the chain. History therefore replays: the alert set known at T is exactly the rows
  with `available_at <= T`, minus those a later-known row supersedes.
- **Two knowledge times.** `sent` is when NWS issued it; `available_at` is when Cascadia first
  held the bytes. A poll loop learns an alert minutes after issuance, and a replay must not
  pretend otherwise (ADR-0010).
- **`basin_ids` is resolved at WRITE time** from the UGC codes via the derived zone mapping
  (`method:basin-ugc-mapping@1.0.0`), so the read path is a lookup, not a geometry operation.
  The mapping used is named per row: if the mapping ever changes, old rows still say which
  version routed them.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "official_alert",
        sa.Column("id", sa.String(), primary_key=True),  # the CAP urn — globally unique by design
        sa.Column("event", sa.String(), nullable=False),  # "Flood Warning", verbatim
        sa.Column("status", sa.String(), nullable=False),  # Actual | Exercise | Test | ...
        sa.Column("message_type", sa.String(), nullable=False),  # Alert | Update | Cancel
        sa.Column("severity", sa.String(), nullable=True),
        sa.Column("certainty", sa.String(), nullable=True),
        sa.Column("urgency", sa.String(), nullable=True),
        sa.Column("headline", sa.String(), nullable=True),
        sa.Column("sender_name", sa.String(), nullable=True),  # "NWS Seattle WA"
        sa.Column("sent", sa.DateTime(), nullable=False),
        sa.Column("onset", sa.DateTime(), nullable=True),
        sa.Column("expires", sa.DateTime(), nullable=True),
        sa.Column("ends", sa.DateTime(), nullable=True),
        sa.Column("ugc", postgresql.JSONB(), nullable=False),  # the codes as served, verbatim
        sa.Column("basin_ids", postgresql.JSONB(), nullable=False),  # resolved at write time; may be []
        sa.Column("mapping_method_id", sa.String(), nullable=False),
        sa.Column("references", postgresql.JSONB(), nullable=False),  # CAP ids this alert supersedes
        sa.Column("retrieved_at", sa.DateTime(), nullable=False),
        sa.Column("available_at", sa.DateTime(), nullable=False, index=True),
        sa.Column("raw_artifact_id", sa.Integer(), sa.ForeignKey("raw_artifact.id"), nullable=True),
    )
    op.create_index("ix_official_alert_expires", "official_alert", ["expires"])


def downgrade() -> None:
    op.drop_index("ix_official_alert_expires", table_name="official_alert")
    op.drop_table("official_alert")
