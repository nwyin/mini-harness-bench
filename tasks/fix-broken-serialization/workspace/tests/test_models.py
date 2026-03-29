"""Tests for model serialization roundtrip."""

from datetime import datetime

from models import Comment, Priority, Status, Ticket, deserialize, serialize


def test_comment_roundtrip():
    """A Comment should survive a serialize/deserialize roundtrip."""
    ts = datetime(2024, 6, 15, 10, 30, 0)
    comment = Comment(author="Alice", text="Looks good", created_at=ts)
    json_str = serialize(comment)
    restored = deserialize(json_str, Comment)
    assert restored.author == "Alice"
    assert restored.text == "Looks good"
    assert restored.created_at == ts


def test_ticket_basic_roundtrip():
    """A Ticket with no comments should roundtrip."""
    ts = datetime(2024, 3, 1, 9, 0, 0)
    ticket = Ticket(
        title="Fix bug",
        description="Something is broken",
        priority=Priority.HIGH,
        status=Status.OPEN,
        assignee="Bob",
        created_at=ts,
    )
    json_str = serialize(ticket)
    restored = deserialize(json_str, Ticket)
    assert restored.title == "Fix bug"
    assert restored.priority == Priority.HIGH
    assert restored.status == Status.OPEN
    assert restored.assignee == "Bob"
    assert restored.created_at == ts


def test_ticket_with_comments():
    """A Ticket with nested Comments should roundtrip."""
    ts = datetime(2024, 1, 10, 12, 0, 0)
    comments = [
        Comment("Alice", "I can reproduce this", datetime(2024, 1, 11, 8, 0, 0)),
        Comment("Bob", "Working on a fix", datetime(2024, 1, 11, 14, 30, 0)),
    ]
    ticket = Ticket(
        title="Login broken",
        description="Users cannot log in",
        priority=Priority.CRITICAL,
        status=Status.IN_PROGRESS,
        created_at=ts,
        comments=comments,
    )
    json_str = serialize(ticket)
    restored = deserialize(json_str, Ticket)
    assert len(restored.comments) == 2
    assert isinstance(restored.comments[0], Comment)
    assert restored.comments[0].author == "Alice"
    assert restored.comments[1].text == "Working on a fix"


def test_ticket_none_assignee():
    """A Ticket with assignee=None should roundtrip without crashing."""
    ticket = Ticket(
        title="Unassigned task",
        description="No one owns this",
        priority=Priority.LOW,
        assignee=None,
        created_at=datetime(2024, 5, 20, 16, 0, 0),
    )
    json_str = serialize(ticket)
    restored = deserialize(json_str, Ticket)
    assert restored.assignee is None


def test_enum_values_preserved():
    """Priority and Status enums should survive roundtrip as proper enum types."""
    ticket = Ticket(
        title="Enum test",
        description="Testing enum serialization",
        priority=Priority.MEDIUM,
        status=Status.RESOLVED,
        created_at=datetime(2024, 7, 1, 0, 0, 0),
    )
    json_str = serialize(ticket)
    restored = deserialize(json_str, Ticket)
    assert isinstance(restored.priority, Priority)
    assert isinstance(restored.status, Status)
    assert restored.priority == Priority.MEDIUM
    assert restored.status == Status.RESOLVED


def test_json_is_valid_string():
    """serialize() should produce a valid JSON string (not crash on non-serializable types)."""
    ticket = Ticket(
        title="Serialize test",
        description="Should produce valid JSON",
        priority=Priority.LOW,
        created_at=datetime(2024, 2, 14, 12, 0, 0),
        comments=[Comment("Carol", "test comment", datetime(2024, 2, 15, 8, 0, 0))],
    )
    import json

    json_str = serialize(ticket)
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict)
    assert parsed["title"] == "Serialize test"


def test_empty_comments_list():
    """A Ticket with an empty comments list should roundtrip."""
    ticket = Ticket(
        title="No comments",
        description="Fresh ticket",
        priority=Priority.HIGH,
        created_at=datetime(2024, 8, 1, 0, 0, 0),
        comments=[],
    )
    json_str = serialize(ticket)
    restored = deserialize(json_str, Ticket)
    assert restored.comments == []
