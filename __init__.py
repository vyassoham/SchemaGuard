"""
UniSchema – Universal Data Validation & Quality Analysis Engine

A production-quality data validation engine that validates structured data
from multiple file types (CSV, Excel, JSON, PDF) using a single Pydantic schema.
"""

__version__ = "1.0.0"
__author__ = "UniSchema Contributors"
__license__ = "MIT"

import sys
import types
from pathlib import Path

# Ensure root directory is in sys.path and register 'unischema' module shim
root_dir = str(Path(__file__).resolve().parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

if "unischema" not in sys.modules:
    mod = types.ModuleType("unischema")
    mod.__path__ = [root_dir]
    mod.__file__ = str(Path(root_dir) / "__init__.py")
    sys.modules["unischema"] = mod

try:
    from .validator.validator import UniversalValidator
    from .schema.user_schema import UserSchema
except (ImportError, ValueError):
    from unischema.validator.validator import UniversalValidator
    from unischema.schema.user_schema import UserSchema

__all__ = ["UniversalValidator", "UserSchema", "__version__"]
