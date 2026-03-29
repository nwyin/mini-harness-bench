"""Utility functions for the application."""

_action_log = []
_validation_log = []


def log_action(action, detail):
    """Log a business action."""
    _action_log.append({"action": action, "detail": detail})


def log_validation(field, value):
    """Log a validation event."""
    _validation_log.append({"field": field, "value": str(value)})


def get_action_log():
    """Return the action log."""
    return list(_action_log)


def get_validation_log():
    """Return the validation log."""
    return list(_validation_log)


def clear_logs():
    """Clear all logs."""
    _action_log.clear()
    _validation_log.clear()


def user_summary(user):
    """Return a one-line summary string for a user."""
    from serializers import serialize_user

    data = serialize_user(user)
    return f"{data['name']} <{data['email']}> age={data['age']}"
