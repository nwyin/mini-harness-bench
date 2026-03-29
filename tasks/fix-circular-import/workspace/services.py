"""Business logic services."""

from models import User, UserGroup  # noqa: F401
from serializers import deserialize_user, serialize_group, serialize_user  # noqa: F401
from utils import log_action


def create_user(name, email, age):
    """Create and return a new User."""
    log_action("create_user", name)
    return User(name=name, email=email, age=age)


def create_group(name, user_dicts):
    """Create a group from a list of user dictionaries."""
    log_action("create_group", name)
    group = UserGroup(name=name)
    for ud in user_dicts:
        user = deserialize_user(ud)
        group.add_member(user)
    return group


def export_group(group):
    """Export a group as a serialized dictionary."""
    log_action("export_group", group.name)
    return serialize_group(group)
