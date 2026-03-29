"""Serialization logic for the application."""

from models import User, UserGroup  # noqa: F401
from validators import validate_user


def serialize_user(user):
    """Serialize a User to a dictionary."""
    validate_user(user)
    return {
        "name": user.name,
        "email": user.email,
        "age": user.age,
        "type": "user",
    }


def deserialize_user(data):
    """Deserialize a dictionary to a User."""
    if data.get("type") != "user":
        raise ValueError("Invalid data type for User")
    return User(name=data["name"], email=data["email"], age=data["age"])


def serialize_group(group):
    """Serialize a UserGroup to a dictionary."""
    return {
        "name": group.name,
        "members": [serialize_user(m) for m in group.members],
        "type": "group",
    }
