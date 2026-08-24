"""Settings: the Phase 0 env contract — defaults, overrides, object-store validation, secret hygiene."""

import pytest

from cascade_core.settings import SEED_FILE, Settings


def test_defaults_from_empty_env() -> None:
    s = Settings.from_env({})
    assert s.db_url == "sqlite+aiosqlite:///./data/cascade.db"
    assert s.queue_db_url is None
    assert s.effective_queue_db_url == s.db_url  # local dev: db_url is already direct
    assert s.object_store == "local"
    assert s.s3_endpoint is None and s.s3_bucket is None
    assert s.usgs_api_key is None
    assert s.seed_file == SEED_FILE
    assert s.cors_origins == ("http://localhost:5173",)


def test_env_overrides_roundtrip() -> None:
    s = Settings.from_env(
        {
            "CASCADE_DB_URL": "postgresql+psycopg://USER:PLACEHOLDER@host-pooler.example/db?sslmode=require",
            "CASCADE_QUEUE_DB_URL": "postgresql+psycopg://USER:PLACEHOLDER@host.example/db?sslmode=require",
            "CASCADE_OBJECT_STORE": "s3",
            "CASCADE_S3_ENDPOINT": "https://ACCOUNT_ID.r2.cloudflarestorage.com",
            "CASCADE_S3_BUCKET": "cascadia-raw",
            "CASCADE_USGS_API_KEY": "PLACEHOLDER-KEY",
            "CASCADE_RAW_DIR": "/tmp/raw",
            "CASCADE_CONTACT": "ops@example.invalid",
            "CASCADE_CORS_ORIGINS": "https://cascadia.example, https://cascadia.example",
        }
    )
    # the queue gets the DIRECT string, never the pooled db_url
    assert s.queue_db_url == "postgresql+psycopg://USER:PLACEHOLDER@host.example/db?sslmode=require"
    assert s.effective_queue_db_url == s.queue_db_url
    assert s.object_store == "s3"
    assert s.s3_endpoint == "https://ACCOUNT_ID.r2.cloudflarestorage.com"
    assert s.s3_bucket == "cascadia-raw"
    assert s.usgs_api_key == "PLACEHOLDER-KEY"
    assert str(s.raw_dir) == "/tmp/raw"
    assert s.contact == "ops@example.invalid"
    assert s.cors_origins == ("http://localhost:5173", "https://cascadia.example")


def test_empty_env_strings_mean_unset_for_optional_fields() -> None:
    s = Settings.from_env(
        {
            "CASCADE_QUEUE_DB_URL": "",
            "CASCADE_OBJECT_STORE": "",
            "CASCADE_S3_ENDPOINT": "",
            "CASCADE_S3_BUCKET": "",
            "CASCADE_USGS_API_KEY": "",
        }
    )
    assert s.queue_db_url is None
    assert s.object_store == "local"
    assert s.s3_endpoint is None and s.s3_bucket is None
    assert s.usgs_api_key is None


@pytest.mark.parametrize("bad", ["gcs", "minio", "S3", "Local"])
def test_object_store_rejects_unknown_backends(bad: str) -> None:
    with pytest.raises(ValueError, match="object_store"):
        Settings.from_env({"CASCADE_OBJECT_STORE": bad})
    with pytest.raises(ValueError, match="object_store"):
        Settings(object_store=bad)  # direct construction validates too


def test_object_store_env_value_is_stripped() -> None:
    assert Settings.from_env({"CASCADE_OBJECT_STORE": " s3 "}).object_store == "s3"


def test_usgs_api_key_is_excluded_from_repr() -> None:
    s = Settings.from_env({"CASCADE_USGS_API_KEY": "PLACEHOLDER-KEY"})
    assert s.usgs_api_key == "PLACEHOLDER-KEY"
    assert "PLACEHOLDER-KEY" not in repr(s)
    assert "usgs_api_key" not in repr(s)


def test_credentialed_db_urls_are_excluded_from_repr() -> None:
    # Production DSNs embed a password; a logged/raised Settings must never leak them.
    s = Settings.from_env(
        {
            "CASCADE_DB_URL": "postgresql+psycopg://USER:HUNTER2@host-pooler.example/db?sslmode=require",
            "CASCADE_QUEUE_DB_URL": "postgresql+psycopg://USER:HUNTER2@host.example/db?sslmode=require",
        }
    )
    assert "HUNTER2" not in repr(s)
    assert "db_url" not in repr(s)  # covers queue_db_url too
