"""Derived features, basin grid masks, artifact retention class, susceptibility gauge config.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-24

Everything P3 (docs/research/p3-surfaces-design-2026-08-24.md §1.6, §3.4, §8) needs before a
surface can be computed, and nothing else. Conventions follow 0001 exactly: naive-UTC
``sa.DateTime`` columns (the ORM's ``UTCDateTime`` is what makes them aware in Python),
``sa.Identity()`` surrogate keys, append-only value semantics, explicit index names.

- ``derived_feature`` (docs/DOMAIN_MODEL.md §2.3) — one row per number Cascadia Papsukkal
  computed, carrying the chain back to what it came from: ``method_id``, the upstream
  ``product_id`` (nullable; it is what lets the assembler resolve ``source_kind`` from the
  registry instead of assuming it), ``raw_artifact_id`` / ``inputs`` / ``raw_inputs_hash``, and
  the three times. Append-only: a recomputation is a new row. Not partitioned — ADR-0013 says
  partition when measured, and §8 measures ~73k rows/month.
- ``grid_mask`` — basin x grid definition -> fractional cell weights. ``grid_definition_hash``
  is in the primary key so a silent provider grid change makes the lookup MISS (and the job
  refuse) instead of silently area-weighting the wrong cells.
- ``raw_artifact.retention_class`` (§8) — nullable; NULL means keep indefinitely,
  ``'gridded-90d'`` means an object-store lifecycle rule may expire the bytes while the row
  survives, so provenance can say the grid expired rather than 404.
- ``basin.susceptibility_gauge_id`` / ``_confidence_ceiling`` / ``_note`` (§2.3) — CONFIGURED
  seed metadata naming the gauge whose flow percentile stands in for basin wetness, the highest
  confidence that gauge may justify, and the caveat that must be rendered with it. No FK on the
  gauge id (``station.basin_id`` already points the other way; a second FK would make the seed
  flush order circular), matching how ``basin.outlet_fp_id`` is already modeled.

Neither new table is PostgreSQL-only: both exist on SQLite too, so the offline suite exercises
the same shapes. JSON columns are JSONB here and plain JSON on SQLite via the ORM's
``JSONVariant``; ``uq_derived_feature_identity`` is declared NULLS NOT DISTINCT because
``window`` and ``issued_at`` are legitimately NULL and PostgreSQL would otherwise let the
identity constraint be bypassed exactly where it matters most.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("raw_artifact", sa.Column("retention_class", sa.String(), nullable=True))

    op.add_column("basin", sa.Column("susceptibility_gauge_id", sa.String(), nullable=True))
    op.add_column("basin", sa.Column("susceptibility_confidence_ceiling", sa.String(), nullable=True))
    op.add_column("basin", sa.Column("susceptibility_note", sa.String(), nullable=True))
    op.create_check_constraint(
        "ck_basin_susceptibility_ceiling",
        "basin",
        "susceptibility_confidence_ceiling IS NULL OR "
        "susceptibility_confidence_ceiling IN ('high', 'moderate', 'low', 'unknown')",
    )

    op.create_table(
        "derived_feature",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("feature", sa.String(), nullable=False),
        sa.Column("scope_kind", sa.String(), nullable=False),
        sa.Column("scope_id", sa.String(), nullable=False),
        sa.Column("window", sa.String(), nullable=True),
        sa.Column("valid_time", sa.DateTime(), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=True),
        sa.Column("computed_at", sa.DateTime(), nullable=False),
        sa.Column("available_at", sa.DateTime(), nullable=False),
        sa.Column("method_id", sa.String(), nullable=False),
        sa.Column("product_id", sa.String(), sa.ForeignKey("source_product.id"), nullable=True),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("values_json", postgresql.JSONB(), nullable=True),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("percentile", sa.Float(), nullable=True),
        sa.Column("climatology_ref", sa.String(), nullable=True),
        sa.Column("confidence_label", sa.String(), nullable=False, server_default="unknown"),
        sa.Column("quality", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("inputs", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("raw_inputs_hash", sa.String(), nullable=True),
        sa.Column("raw_artifact_id", sa.Integer(), sa.ForeignKey("raw_artifact.id"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "method_id", "feature", "scope_id", "window", "valid_time", "issued_at",
            name="uq_derived_feature_identity",
            postgresql_nulls_not_distinct=True,
        ),
        sa.CheckConstraint(
            "confidence_label IN ('high', 'moderate', 'low', 'unknown')",
            name="ck_derived_feature_confidence",
        ),
    )
    op.create_index("ix_derived_feature_valid_time", "derived_feature", ["valid_time"])
    op.create_index("ix_derived_feature_available_at", "derived_feature", ["available_at"])
    op.create_index("ix_derived_feature_scope_time", "derived_feature", ["scope_id", "feature", "valid_time"])

    op.create_table(
        "grid_mask",
        sa.Column("basin_id", sa.String(), sa.ForeignKey("basin.id"), nullable=False),
        sa.Column("grid_definition_hash", sa.String(), nullable=False),
        sa.Column("method_id", sa.String(), nullable=False),
        sa.Column("cells", postgresql.JSONB(), nullable=False),
        sa.Column("cell_count", sa.Integer(), nullable=False),
        sa.Column("masked_area_km2", sa.Float(), nullable=False),
        sa.Column("polygon_source", sa.String(), nullable=False),
        sa.Column("computed_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("basin_id", "grid_definition_hash"),
    )


def downgrade() -> None:
    op.drop_table("grid_mask")
    op.drop_index("ix_derived_feature_scope_time", table_name="derived_feature")
    op.drop_index("ix_derived_feature_available_at", table_name="derived_feature")
    op.drop_index("ix_derived_feature_valid_time", table_name="derived_feature")
    op.drop_table("derived_feature")
    op.drop_constraint("ck_basin_susceptibility_ceiling", "basin", type_="check")
    op.drop_column("basin", "susceptibility_note")
    op.drop_column("basin", "susceptibility_confidence_ceiling")
    op.drop_column("basin", "susceptibility_gauge_id")
    op.drop_column("raw_artifact", "retention_class")
