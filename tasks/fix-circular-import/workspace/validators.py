"""Validation logic for the application."""

import re

from models import User  # noqa: F401
from utils import log_validation


def validate_email(email):
    """Validate an email address format."""
    log_validation("email", email)
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        raise ValueError(f"Invalid email: {email}")
    return True


def validate_age(age):
    """Validate that age is a reasonable integer."""
    log_validation("age", age)
    if not isinstance(age, int) or age < 0 or age > 150:
        raise ValueError(f"Invalid age: {age}")
    return True


def validate_user(user):
    """Validate a complete User object."""
    if not isinstance(user, User):
        raise TypeError("Expected a User instance")
    validate_email(user.email)
    validate_age(user.age)
    if not user.name or not user.name.strip():
        raise ValueError("User name cannot be empty")
    return True
