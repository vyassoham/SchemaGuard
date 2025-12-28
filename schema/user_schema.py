"""
User Schema Module

Defines Pydantic models for validating user/employee data.
These schemas demonstrate the validation capabilities of UniSchema
and serve as templates for custom schema definitions.
"""

from datetime import date, datetime
from typing import Optional, Union
from decimal import Decimal
import re

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    EmailStr,
    ConfigDict,
)


class UserSchema(BaseModel):
    """
    Schema for validating user data records.
    
    This schema validates common user data fields with appropriate
    constraints. Use this as a template for creating custom schemas.
    
    Fields:
        id: Unique user identifier (required, positive integer)
        name: User's full name (required, 2-100 characters)
        email: Valid email address (required)
        age: User's age (optional, 0-120 years)
        phone: Phone number (optional, 10-15 digits)
        country: Country code or name (optional)
        registration_date: Date of registration (optional)
        is_active: Whether user is active (default: True)
    
    Example:
        >>> from unischema.schema import UserSchema
        >>> user = UserSchema(
        ...     id=1,
        ...     name="John Doe",
        ...     email="john@example.com",
        ...     age=30
        ... )
    """
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
        extra="ignore",  # Ignore extra fields
    )
    
    id: int = Field(
        ...,
        gt=0,
        description="Unique user identifier, must be a positive integer"
    )
    
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="User's full name"
    )
    
    email: str = Field(
        ...,
        description="Valid email address"
    )
    
    age: Optional[int] = Field(
        default=None,
        ge=0,
        le=120,
        description="User's age in years (0-120)"
    )
    
    phone: Optional[str] = Field(
        default=None,
        min_length=10,
        max_length=15,
        description="Phone number (10-15 characters)"
    )
    
    country: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Country code or name"
    )
    
    registration_date: Optional[Union[date, str]] = Field(
        default=None,
        description="Date of user registration"
    )
    
    is_active: bool = Field(
        default=True,
        description="Whether the user account is active"
    )
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format using regex pattern."""
        if not v:
            raise ValueError("Email is required")
        
        # More permissive email pattern
        email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_pattern, v.strip()):
            raise ValueError(f"Invalid email format: '{v}'")
        
        return v.strip().lower()
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and clean name field."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        
        # Remove extra whitespace
        cleaned = " ".join(v.split())
        
        # Check for only whitespace or special characters
        if not any(c.isalpha() for c in cleaned):
            raise ValueError("Name must contain at least one letter")
        
        return cleaned
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if v is None:
            return None
        
        # Remove common separators
        cleaned = re.sub(r"[\s\-\.\(\)\+]", "", v)
        
        if not cleaned.isdigit():
            raise ValueError(f"Phone must contain only digits, got: '{v}'")
        
        if len(cleaned) < 10 or len(cleaned) > 15:
            raise ValueError(
                f"Phone must be 10-15 digits, got {len(cleaned)} digits"
            )
        
        return cleaned
    
    @field_validator("registration_date", mode="before")
    @classmethod
    def parse_date(cls, v: Optional[Union[date, str]]) -> Optional[date]:
        """Parse various date formats."""
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        
        if isinstance(v, date):
            return v
        
        if isinstance(v, datetime):
            return v.date()
        
        if isinstance(v, str):
            # Try common date formats
            formats = [
                "%Y-%m-%d",
                "%d-%m-%Y",
                "%m/%d/%Y",
                "%d/%m/%Y",
                "%Y/%m/%d",
                "%d.%m.%Y",
                "%Y.%m.%d",
            ]
            
            v_clean = v.strip()
            for fmt in formats:
                try:
                    return datetime.strptime(v_clean, fmt).date()
                except ValueError:
                    continue
            
            raise ValueError(
                f"Could not parse date '{v}'. "
                f"Supported formats: YYYY-MM-DD, DD-MM-YYYY, MM/DD/YYYY, etc."
            )
        
        raise ValueError(f"Invalid date type: {type(v)}")


class EmployeeSchema(BaseModel):
    """
    Schema for validating employee/HR data records.
    
    Extended schema with salary, department, and employment information.
    Demonstrates more complex validation rules.
    
    Fields:
        employee_id: Unique employee identifier (required, positive)
        first_name: Employee's first name (required)
        last_name: Employee's last name (required)
        email: Work email address (required)
        department: Department name (required)
        salary: Annual salary (required, positive)
        hire_date: Date of hiring (required)
        manager_id: ID of direct manager (optional)
        job_title: Job title/position (optional)
        is_full_time: Full-time status (default: True)
    
    Example:
        >>> from unischema.schema import EmployeeSchema
        >>> emp = EmployeeSchema(
        ...     employee_id=101,
        ...     first_name="Jane",
        ...     last_name="Smith",
        ...     email="jane.smith@company.com",
        ...     department="Engineering",
        ...     salary=85000.00,
        ...     hire_date="2023-01-15"
        ... )
    """
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
        extra="ignore",
    )
    
    employee_id: int = Field(
        ...,
        gt=0,
        description="Unique employee identifier"
    )
    
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Employee's first name"
    )
    
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Employee's last name"
    )
    
    email: str = Field(
        ...,
        description="Work email address"
    )
    
    department: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Department name"
    )
    
    salary: float = Field(
        ...,
        gt=0,
        description="Annual salary (must be positive)"
    )
    
    hire_date: Optional[Union[date, str]] = Field(
        ...,
        description="Date of hiring"
    )
    
    manager_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="ID of direct manager"
    )
    
    job_title: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Job title/position"
    )
    
    is_full_time: bool = Field(
        default=True,
        description="Whether employee is full-time"
    )
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if not v:
            raise ValueError("Email is required")
        
        email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_pattern, v.strip()):
            raise ValueError(f"Invalid email format: '{v}'")
        
        return v.strip().lower()
    
    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, v: str) -> str:
        """Validate name fields."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        
        cleaned = v.strip()
        if not any(c.isalpha() for c in cleaned):
            raise ValueError("Name must contain letters")
        
        return cleaned
    
    @field_validator("salary", mode="before")
    @classmethod
    def parse_salary(cls, v: Union[float, str, int]) -> float:
        """Parse salary from various formats."""
        if isinstance(v, (int, float)):
            return float(v)
        
        if isinstance(v, str):
            # Remove currency symbols and commas
            cleaned = re.sub(r"[$€£¥,\s]", "", v)
            try:
                return float(cleaned)
            except ValueError:
                raise ValueError(f"Cannot parse salary value: '{v}'")
        
        raise ValueError(f"Invalid salary type: {type(v)}")
    
    @field_validator("hire_date", mode="before")
    @classmethod
    def parse_hire_date(cls, v: Optional[Union[date, str]]) -> Optional[date]:
        """Parse hire date from various formats."""
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        
        if isinstance(v, date):
            return v
        
        if isinstance(v, datetime):
            return v.date()
        
        if isinstance(v, str):
            formats = [
                "%Y-%m-%d",
                "%d-%m-%Y",
                "%m/%d/%Y",
                "%d/%m/%Y",
                "%Y/%m/%d",
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(v.strip(), fmt).date()
                except ValueError:
                    continue
            
            raise ValueError(f"Could not parse hire date: '{v}'")
        
        raise ValueError(f"Invalid date type: {type(v)}")
    
    @field_validator("department")
    @classmethod
    def validate_department(cls, v: str) -> str:
        """Validate and normalize department name."""
        if not v or not v.strip():
            raise ValueError("Department cannot be empty")
        
        # Capitalize department name
        return v.strip().title()


def get_schema_fields_info(schema_class: type[BaseModel]) -> dict:
    """
    Get detailed information about schema fields.
    
    Args:
        schema_class: Pydantic model class to inspect.
    
    Returns:
        Dictionary with field information including types, 
        constraints, and descriptions.
    """
    fields_info = {}
    
    for field_name, field_info in schema_class.model_fields.items():
        fields_info[field_name] = {
            "type": str(field_info.annotation),
            "required": field_info.is_required(),
            "default": field_info.default if not field_info.is_required() else None,
            "description": field_info.description,
        }
    
    return fields_info
