"""Data models with JSON serialization support."""

import json
from datetime import datetime
from enum import Enum

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


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
            "created_at": self.created_at.strftime(DATETIME_FORMAT),
        }

    @classmethod
    def from_json(cls, data):
        return cls(
            author=data["author"],
            text=data["text"],
            created_at=datetime.strptime(data["created_at"], DATETIME_FORMAT),
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
            "priority": self.priority.value,
            "status": self.status.value,
            "assignee": self.assignee,
            "created_at": self.created_at.strftime(DATETIME_FORMAT),
            "comments": [c.to_json() for c in self.comments],
        }

    @classmethod
    def from_json(cls, data):
        return cls(
            title=data["title"],
            description=data["description"],
            priority=Priority(data["priority"]),
            status=Status(data["status"]),
            assignee=data.get("assignee"),
            created_at=datetime.strptime(data["created_at"], DATETIME_FORMAT),
            comments=[Comment.from_json(c) for c in data.get("comments", [])],
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
