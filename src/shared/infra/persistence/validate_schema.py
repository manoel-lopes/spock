"""
Schema validator: compares SQLAlchemy models against the actual database schema.
Similar to Zod validation in Node.js — catches mismatches at startup or CI time.

Usage:
    python -m src.shared.infra.persistence.validate_schema
"""

import sys
from typing import Any

from sqlalchemy import DateTime, Float, Integer, String, Text, create_engine, inspect, text
from sqlalchemy.dialects.postgresql import JSONB

from src.shared.infra.env.env_service import env_service
from src.shared.infra.persistence.models import Base

# Map SQLAlchemy types to expected DB udt_names
SA_TO_PG: dict[type, set[str]] = {
    String: {"text", "varchar"},
    Text: {"text"},
    Integer: {"int4", "int8"},
    Float: {"float4", "float8"},
    DateTime: {"timestamp", "timestamptz"},
    JSONB: {"jsonb"},
}


def _sa_type_to_pg_types(sa_type: Any) -> set[str]:
    """Convert a SQLAlchemy column type instance to expected PG udt_names."""
    from sqlalchemy import Boolean
    if isinstance(sa_type, Boolean):
        return {"bool"}
    for sa_cls, pg_names in SA_TO_PG.items():
        if isinstance(sa_type, sa_cls):
            return pg_names
    return {str(sa_type).lower()}


def validate() -> list[str]:
    """Compare all registered models against the live database. Returns a list of errors."""
    engine = create_engine(env_service.sync_database_url)
    errors: list[str] = []

    with engine.connect() as conn:
        db_inspector = inspect(engine)
        db_tables = set(db_inspector.get_table_names())

        for mapper in Base.registry.mappers:
            model = mapper.class_
            table_name = model.__tablename__  # type: ignore[attr-defined]

            if table_name not in db_tables:
                errors.append(f"[{table_name}] Table missing from database")
                continue

            # Get actual DB columns
            db_cols_raw = conn.execute(
                text(
                    "SELECT column_name, udt_name, is_nullable, column_default "
                    "FROM information_schema.columns "
                    f"WHERE table_name = '{table_name}' ORDER BY ordinal_position"
                )
            ).fetchall()
            db_cols = {row[0]: {"udt_name": row[1], "nullable": row[2], "default": row[3]} for row in db_cols_raw}

            # Check each model column
            for col in model.__table__.columns:  # type: ignore[attr-defined]
                col_name = col.name

                if col_name not in db_cols:
                    errors.append(f"[{table_name}.{col_name}] Column exists in model but not in DB")
                    continue

                db_col = db_cols[col_name]

                # Type check
                expected_pg = _sa_type_to_pg_types(col.type)
                actual_pg = db_col["udt_name"]
                if actual_pg not in expected_pg:
                    errors.append(
                        f"[{table_name}.{col_name}] Type mismatch: "
                        f"model expects {expected_pg}, DB has '{actual_pg}'"
                    )

                # Nullable check
                model_nullable = col.nullable if col.nullable is not None else True
                db_nullable = db_col["nullable"] == "YES"
                if col.primary_key:
                    pass  # PKs are always NOT NULL
                elif model_nullable != db_nullable:
                    errors.append(
                        f"[{table_name}.{col_name}] Nullable mismatch: "
                        f"model={'nullable' if model_nullable else 'not null'}, "
                        f"DB={'nullable' if db_nullable else 'not null'}"
                    )

            # Check for DB columns not in model
            model_col_names = {col.name for col in model.__table__.columns}  # type: ignore[attr-defined]
            for db_col_name in db_cols:
                if db_col_name not in model_col_names:
                    errors.append(f"[{table_name}.{db_col_name}] Column exists in DB but not in model")

    engine.dispose()
    return errors


if __name__ == "__main__":
    errs = validate()
    if errs:
        print(f"Schema validation FAILED ({len(errs)} errors):\n")
        for e in errs:
            print(f"  ✗ {e}")
        sys.exit(1)
    else:
        print("Schema validation PASSED — all models match the database.")
        sys.exit(0)
