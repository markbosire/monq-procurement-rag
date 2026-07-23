"""Tests for custom SQLAlchemy model types.

Verifies the VectorType serialisation and deserialisation logic.
"""

from app.db.models import VectorType


class TestVectorType:
    """Tests for the VectorType TypeDecorator."""

    def test_process_bind_param_list(self):
        """Verify a Python list is serialised to a JSON string."""
        vt = VectorType()
        result = vt.process_bind_param([1, 2, 3], None)
        assert result == "[1, 2, 3]"

    def test_process_bind_param_none(self):
        """Verify None is returned as-is during bind."""
        vt = VectorType()
        result = vt.process_bind_param(None, None)
        assert result is None

    def test_process_result_value_list(self):
        """Verify a JSON string is deserialised back to a Python list."""
        vt = VectorType()
        result = vt.process_result_value("[1, 2, 3]", None)
        assert result == [1, 2, 3]

    def test_process_result_value_none(self):
        """Verify None is returned as-is during result processing."""
        vt = VectorType()
        result = vt.process_result_value(None, None)
        assert result is None

    def test_process_result_value_empty_list(self):
        """Verify an empty JSON array is deserialised to an empty list."""
        vt = VectorType()
        result = vt.process_result_value("[]", None)
        assert result == []
