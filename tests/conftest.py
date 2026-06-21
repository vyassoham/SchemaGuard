import pytest
import pandas as pd
import sys
import os
import types

# Get the path to SchemaGuard directory and parent directory
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
parent_dir = os.path.dirname(root_dir)

# Add the parent directory of SchemaGuard to path so unischema can find packages relatively
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Create virtual package 'unischema' pointing to root_dir
unischema = types.ModuleType('unischema')
unischema.__path__ = [root_dir]
unischema.__file__ = os.path.join(root_dir, '__init__.py')
sys.modules['unischema'] = unischema


@pytest.fixture(autouse=True)
def mock_tabula(mocker):
    """Mock tabula to avoid relying on Java virtual machine setup on test runner machine"""
    try:
        import tabula
        # Mock tabula.read_pdf to return a list of dummy dataframes
        dummy_df = pd.DataFrame({
            "id": ["1", "2"],
            "name": ["Alice", "Bob"],
            "email": ["alice@example.com", "bob@example.com"],
            "age": ["25", "30"],
            "phone": ["1234567890", "0987654321"],
            "is_active": ["True", "False"]
        })
        mock_read = mocker.patch("tabula.read_pdf")
        mock_read.return_value = [dummy_df]
        return mock_read
    except (ImportError, Exception):
        return None
