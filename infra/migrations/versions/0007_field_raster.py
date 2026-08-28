"""Observed weather fields as quantized window rasters (ADR-0020).

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-28

C3b: the MRMS QPE hour rendered as a spatial field. The worker already decodes the full plane
every hour and threw the spatial information away after six basin means; this table keeps the
seeded-window cut (236x283 cells at MRMS's own 0.01 deg), quantized to uint16 and gzipped —
1-40 KB an hour, 72 h retention.

Design points that are doctrine, not taste:

- **The grid spec rides in the row.** The window is a decision, not a constant; a reader that
  assumed the extent would silently misplace the field the day the window changes.
- **The sentinel is not a value.** Packed 0xFFFF means missing/no-coverage and renders as
  absence, never as zero precipitation — the same -3-sentinel honesty the basin means keep.
- **Regenerable, so deletable.** The source grib stays archived; retention pruning is the one
  DELETE `ingest_writer` holds on a data table (roles.sql documents it with the ADR).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "field_raster",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("product_id", sa.String(), nullable=False),
        sa.Column("field", sa.String(), nullable=False),
        sa.Column("valid_time", sa.DateTime(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(), nullable=False),
        sa.Column("available_at", sa.DateTime(), nullable=False),
        sa.Column("lo1", sa.Float(), nullable=False),
        sa.Column("la1", sa.Float(), nullable=False),
        sa.Column("dlon", sa.Float(), nullable=False),
        sa.Column("dlat", sa.Float(), nullable=False),
        sa.Column("nx", sa.Integer(), nullable=False),
        sa.Column("ny", sa.Integer(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("scale", sa.Float(), nullable=False),
        sa.Column("max_value", sa.Float(), nullable=False),
        sa.Column("cells", sa.LargeBinary(), nullable=False),
        sa.Column("method_id", sa.String(), nullable=False),
        sa.Column("raw_artifact_id", sa.Integer(), sa.ForeignKey("raw_artifact.id"), nullable=True),
        sa.UniqueConstraint("product_id", "field", "valid_time", name="uq_field_raster_scope"),
    )
    op.create_index("ix_field_raster_read", "field_raster", ["product_id", "field", "available_at"])
    # Grants live in scripts/sql/roles.sql, never in migrations (the pg suite's scratch DBs
    # have no roles). Default privileges already give api_reader SELECT and ingest_writer
    # SELECT+INSERT here; the retention DELETE is the one addition roles.sql carries for this
    # table (ADR-0020 §3).


def downgrade() -> None:
    op.drop_index("ix_field_raster_read", table_name="field_raster")
    op.drop_table("field_raster")
