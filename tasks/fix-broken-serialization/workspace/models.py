"""Data models with JSON serialization support."""

import json
from datetime import datetime
from enum import Enum


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Status(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Comment:
    def __init__(self, author, text, created_at=None):
        self.author = author
        self.text = text
        self.created_at = created_at or datetime.now()

    def to_json(self):
        return {
            "author": self.author,
            "text": self.text,
            # BUG: datetime is not converted to string
            "created_at": self.created_at,
        }

    @classmethod
    def from_json(cls, data):
        return cls(
            author=data["author"],
            text=data["text"],
            # BUG: string is not converted back to datetime
            created_at=data["created_at"],
        )

    def __eq__(self, other):
        if not isinstance(other, Comment):
            return False
        return self.author == other.author and self.text == other.text


class Ticket:
    def __init__(self, title, description, priority, status=None, assignee=None, created_at=None, comments=None):
        self.title = title
        self.description = description
        self.priority = priority
        self.status = status or Status.OPEN
        self.assignee = assignee
        self.created_at = created_at or datetime.now()
        self.comments = comments or []

    def to_json(self):
        return {
            "title": self.title,
            "description": self.description,
            # BUG: enum is serialized as the Enum object, not its value
            "priority": self.priority,
            # BUG: same issue with status
            "status": self.status,
            "assignee": self.assignee,
            # BUG: datetime not converted
            "created_at": self.created_at,
            # BUG: nested comments not serialized to dicts
            "comments": self.comments,
        }

    @classmethod
    def from_json(cls, data):
        return cls(
            title=data["title"],
            description=data["description"],
            # BUG: string not converted back to Priority enum
            priority=data["priority"],
            # BUG: string not converted back to Status enum
            status=data["status"],
            assignee=data["assignee"],
            # BUG: string not converted back to datetime
            created_at=data["created_at"],
            # BUG: dicts not converted back to Comment objects
            comments=data.get("comments", []),
        )

    def __eq__(self, other):
        if not isinstance(other, Ticket):
            return False
        return (
            self.title == other.title
            and self.description == other.description
            and self.priority == other.priority
            and self.status == other.status
            and self.assignee == other.assignee
            and self.comments == other.comments
        )


def serialize(obj):
    """Serialize a model object to a JSON string."""
    return json.dumps(obj.to_json())


def deserialize(json_str, cls):
    """Deserialize a JSON string to a model object."""
    data = json.loads(json_str)
    return cls.from_json(data)
