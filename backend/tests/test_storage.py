"""Tests for the LocalFileStorage backend.

Uses TemporaryDirectory to avoid polluting the real filesystem.
"""

import os
from tempfile import TemporaryDirectory
from app.storage.local_storage import LocalFileStorage


class TestLocalFileStorage:
    """Tests for LocalFileStorage operations."""

    def test_save_and_get(self):
        """Verify saved bytes can be retrieved and match the original content."""
        with TemporaryDirectory() as tmpdir:
            storage = LocalFileStorage(base_path=tmpdir)
            data = b"fake pdf content"
            storage.save("doc1", data)
            result = storage.get("doc1")
            assert result == data

    def test_get_nonexistent(self):
        """Verify fetching a non-existent document returns None."""
        with TemporaryDirectory() as tmpdir:
            storage = LocalFileStorage(base_path=tmpdir)
            result = storage.get("nonexistent")
            assert result is None

    def test_delete_removes_file(self):
        """Verify after deletion the document can no longer be retrieved."""
        with TemporaryDirectory() as tmpdir:
            storage = LocalFileStorage(base_path=tmpdir)
            storage.save("doc1", b"data")
            storage.delete("doc1")
            assert storage.get("doc1") is None

    def test_delete_idempotent(self):
        """Verify deleting a document twice does not raise an error."""
        with TemporaryDirectory() as tmpdir:
            storage = LocalFileStorage(base_path=tmpdir)
            storage.save("doc1", b"data")
            storage.delete("doc1")
            storage.delete("doc1")  # second delete should not raise

    def test_base_path_created_on_init(self):
        """Verify the storage directory is created if it does not exist."""
        with TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, "nested", "storage")
            assert not os.path.exists(new_dir)
            storage = LocalFileStorage(base_path=new_dir)
            assert os.path.isdir(new_dir)
