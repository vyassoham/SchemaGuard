"""
Validator Module

Core validation engine for UniSchema.
"""

from .validator import UniversalValidator, ValidationResult, ValidationError

__all__ = ["UniversalValidator", "ValidationResult", "ValidationError"]
