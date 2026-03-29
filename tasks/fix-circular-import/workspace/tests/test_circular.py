"""Tests verifying the public API works correctly after fixing circular imports."""


def test_import_models():
    """models.User and models.UserGroup must be importable."""
    from models import User, UserGroup

    u = User("Alice", "alice@example.com", 30)
    assert u.name == "Alice"
    g = UserGroup("team", [u])
    assert g.get_emails() == ["alice@example.com"]


def test_import_validators():
    """validators functions must be importable and work."""
    from validators import validate_age, validate_email, validate_user  # noqa: F401

    assert validate_email("test@example.com") is True
    assert validate_age(25) is True


def test_import_serializers():
    """serializers functions must be importable and work."""
    from models import User
    from serializers import deserialize_user, serialize_group, serialize_user  # noqa: F401

    u = User("Bob", "bob@example.com", 40)
    data = serialize_user(u)
    assert data["name"] == "Bob"
    assert data["type"] == "user"

    u2 = deserialize_user(data)
    assert u2.name == "Bob"
    assert u2.email == "bob@example.com"


def test_import_services():
    """services functions must be importable and work."""
    from services import create_group, create_user, export_group  # noqa: F401

    u = create_user("Carol", "carol@example.com", 35)
    assert u.name == "Carol"


def test_import_utils():
    """utils functions must be importable and work."""
    from models import User
    from utils import clear_logs, get_action_log, log_action, user_summary

    clear_logs()
    log_action("test", "value")
    assert len(get_action_log()) == 1

    u = User("Dave", "dave@example.com", 28)
    summary = user_summary(u)
    assert "Dave" in summary
    assert "dave@example.com" in summary


def test_user_to_dict():
    """User.to_dict() must work (crosses models -> serializers boundary)."""
    from models import User

    u = User("Eve", "eve@example.com", 22)
    d = u.to_dict()
    assert d["name"] == "Eve"
    assert d["email"] == "eve@example.com"
    assert d["age"] == 22
    assert d["type"] == "user"


def test_validate_user_object():
    """validate_user must accept User objects."""
    from models import User
    from validators import validate_user

    u = User("Frank", "frank@example.com", 45)
    assert validate_user(u) is True


def test_roundtrip_group():
    """Create a group via services and export it."""
    from services import create_group, export_group

    user_dicts = [
        {"name": "Grace", "email": "grace@example.com", "age": 29, "type": "user"},
        {"name": "Hank", "email": "hank@example.com", "age": 33, "type": "user"},
    ]
    group = create_group("engineers", user_dicts)
    exported = export_group(group)
    assert exported["name"] == "engineers"
    assert len(exported["members"]) == 2
