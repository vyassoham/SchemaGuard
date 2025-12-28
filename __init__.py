"""
UniSchema – Universal Data Validation & Quality Analysis Engine

A production-quality data validation engine that validates structured data
from multiple file types (CSV, Excel, JSON, PDF) using a single Pydantic schema.
"""

__version__ = "1.0.0"
__author__ = "UniSchema Contributors"
__license__ = "MIT"

from .validator.validator import UniversalValidator
from .schema.user_schema import UserSchema

__all__ = ["UniversalValidator", "UserSchema", "__version__"]
