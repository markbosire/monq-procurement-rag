import sys
import pytest
from app.config import settings
from app.db.session import _clear_engine_cache, get_engine, init_db
from app.db.models import Base

settings.database_url = "sqlite:///:memory:"
settings.groq_api_key = "fake-key-for-testing"
_clear_engine_cache()

# Track modules replaced in sys.modules so they can be restored
# after the test session (prevents mocks from leaking across test files).
_SAVED_MODULES: dict[str, object] = {}


def pytest_configure(config):
    """Save original module references before any tests are collected."""
    for mod_name in ("sentence_transformers", "spacy", "groq"):
        _SAVED_MODULES[mod_name] = sys.modules.get(mod_name)


def pytest_unconfigure(config):
    """Restore original modules that tests may have replaced in sys.modules."""
    for mod_name, orig in _SAVED_MODULES.items():
        if orig is not None:
            sys.modules[mod_name] = orig
        else:
            sys.modules.pop(mod_name, None)


@pytest.fixture(autouse=True)
def _reset_db():
    init_db()
    yield
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
