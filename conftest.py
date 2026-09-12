import sys
from pathlib import Path

# pipeline/ and forms/ live under src/ - this makes them importable repo-wide for every
# test, without each test file needing its own sys.path hack. conftest.py is loaded by
# pytest before any test collection, so this runs first no matter which test file executes.
sys.path.insert(0, str(Path(__file__).parent / "src"))


def pytest_addoption(parser):
    parser.addoption("--jnid", action="store", default=None, help="JNB job JNID to preview")
