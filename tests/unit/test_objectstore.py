"""Raw archive backends (ADR-0004): ObstoreStore semantics and the settings factory.

Fully offline: ObstoreStore is exercised over ``obstore.store.LocalStore`` in a tmp dir;
the s3 factory path constructs an S3Store client but never performs network I/O.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from obstore.store import LocalStore

from cascade_core.objectstore import (
    LocalFilesystemStore,
    ObstoreStore,
    object_key_for,
    store_from_settings,
)
from cascade_core.settings import Settings

PAYLOAD = b'{"site":"12200500","flow_cfs":141000}'


@pytest.fixture
def store(tmp_path: Path) -> ObstoreStore:
    return ObstoreStore(LocalStore(tmp_path))


def test_put_returns_content_addressed_key(store: ObstoreStore) -> None:
    key = store.put(PAYLOAD)
    assert key == object_key_for(PAYLOAD)
    h = key.split("/")[-1].removesuffix(".json")
    assert key == f"{h[:2]}/{h[2:4]}/{h}.json"


def test_second_put_of_same_bytes_is_noop_success(store: ObstoreStore) -> None:
    # create-mode put refuses overwrite; AlreadyExists is swallowed as success because
    # a sha256-derived key already present can only hold these exact bytes.
    key = store.put(PAYLOAD)
    assert store.put(PAYLOAD) == key
    assert store.get(key) == PAYLOAD


def test_get_round_trips_bytes(store: ObstoreStore) -> None:
    key = store.put(PAYLOAD)
    got = store.get(key)
    assert isinstance(got, bytes) and got == PAYLOAD


def test_exists_true_after_put_false_for_absent(store: ObstoreStore) -> None:
    key = store.put(PAYLOAD)
    assert store.exists(key)
    assert not store.exists(object_key_for(b"never stored"))


def test_get_of_absent_key_raises_keyerror(store: ObstoreStore) -> None:
    missing = object_key_for(b"never stored")
    with pytest.raises(KeyError, match=missing.split("/")[-1][:8]):
        store.get(missing)


def test_colliding_key_with_different_bytes_is_impossible_by_construction(store: ObstoreStore) -> None:
    # The interface never accepts a caller-chosen key: put() derives the key from the
    # payload's sha256. Different bytes therefore land under different keys, and each
    # key permanently holds the bytes it was derived from — the immutability contract.
    a, b = b'{"v":1}', b'{"v":2}'
    key_a, key_b = store.put(a), store.put(b)
    assert key_a != key_b
    assert store.get(key_a) == a and store.get(key_b) == b
    # Re-putting either payload cannot disturb the other (or itself).
    assert store.put(a) == key_a and store.get(key_a) == a


def test_obstore_and_local_filesystem_stores_are_byte_compatible(tmp_path: Path) -> None:
    # Same tree, same keys, same bytes — the ADR-0004 migration guarantee.
    local = LocalFilesystemStore(tmp_path)
    wrapped = ObstoreStore(LocalStore(tmp_path))
    key = local.put(PAYLOAD)
    assert wrapped.exists(key) and wrapped.get(key) == PAYLOAD
    other = b'{"written":"via obstore"}'
    key2 = wrapped.put(other)
    assert local.exists(key2) and local.get(key2) == other


def test_localfilesystemstore_get_absent_key_raises_keyerror(tmp_path: Path) -> None:
    with pytest.raises(KeyError):
        LocalFilesystemStore(tmp_path).get(object_key_for(b"never stored"))


def test_factory_local_selects_filesystem_store(tmp_path: Path) -> None:
    settings = Settings(object_store="local", raw_dir=tmp_path)
    built = store_from_settings(settings)
    assert isinstance(built, LocalFilesystemStore)
    assert built.root == tmp_path


def test_factory_s3_selects_obstore_over_s3store(monkeypatch: pytest.MonkeyPatch) -> None:
    # obstore reads credentials from the standard env vars itself; Settings never carries
    # them. Placeholder values only — construction performs no network I/O.
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "PLACEHOLDER")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "PLACEHOLDER")
    settings = Settings(
        object_store="s3",
        s3_endpoint="https://ACCOUNT_ID.r2.cloudflarestorage.com",
        s3_bucket="cascadia-raw",
    )
    built = store_from_settings(settings)
    assert isinstance(built, ObstoreStore)
    from obstore.store import S3Store

    assert isinstance(built.store, S3Store)


@pytest.mark.parametrize(
    ("endpoint", "bucket", "expected"),
    [
        (None, "cascadia-raw", "s3_endpoint"),
        ("https://ACCOUNT_ID.r2.cloudflarestorage.com", None, "s3_bucket"),
        (None, None, "s3_endpoint and s3_bucket"),
    ],
)
def test_factory_s3_missing_config_raises_valueerror(
    endpoint: str | None, bucket: str | None, expected: str
) -> None:
    settings = Settings(object_store="s3", s3_endpoint=endpoint, s3_bucket=bucket)
    with pytest.raises(ValueError, match=expected):
        store_from_settings(settings)
