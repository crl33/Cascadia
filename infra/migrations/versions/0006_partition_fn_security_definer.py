"""Partition function becomes SECURITY DEFINER — the one DDL door ingest_writer may open.

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-28

ADR-0019: the monthly partition-maintenance job stays in the worker (and therefore in the
`job_run` health machinery), while the worker's role loses every other DDL capability.
`cascade_ensure_month_partitions` was already the only partition-DDL path, already
parameterized (`format %I/%L`, bound date arguments) and idempotent; this recreates it
byte-identical in body, with `SECURITY DEFINER` and a pinned `search_path` (the standard
definer hardening — no schema-shadowing of `observation` or `to_regclass`).

On SQLite (the offline suite) this migration is a no-op, like 0001's function install.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_FN = """
CREATE OR REPLACE FUNCTION cascade_ensure_month_partitions(from_month date, to_month date)
RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    m date := date_trunc('month', from_month)::date;
    last_month date := date_trunc('month', to_month)::date;
    part_name text;
    created integer := 0;
BEGIN
    WHILE m <= last_month LOOP
        part_name := format('observation_y%sm%s', to_char(m, 'YYYY'), to_char(m, 'MM'));
        IF to_regclass(part_name) IS NULL THEN
            EXECUTE format(
                'CREATE TABLE %I PARTITION OF observation FOR VALUES FROM (%L) TO (%L)',
                part_name, m, (m + interval '1 month')::date
            );
            created := created + 1;
        END IF;
        m := (m + interval '1 month')::date;
    END LOOP;
    RETURN created;
END;
$$
"""

_FN_INVOKER = _FN.replace("SECURITY DEFINER\nSET search_path = public, pg_temp\n", "")


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    op.execute(_FN)


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    op.execute(_FN_INVOKER)
