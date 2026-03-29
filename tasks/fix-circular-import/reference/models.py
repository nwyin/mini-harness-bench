"""Data models for the application."""


class User:
    def __init__(self, name, email, age):
        from validators import validate_age, validate_email

        validate_email(email)
        validate_age(age)
        self.name = name
        self.email = email
        self.age = age

    def to_dict(self):
        from serializers import serialize_user

        return serialize_user(self)

    def __repr__(self):
        return f"User(name={self.name!r}, email={self.email!r}, age={self.age})"


class UserGroup:
    def __init__(self, name, members=None):
        self.name = name
        self.members = members or []

    def add_member(self, user):
        if not isinstance(user, User):
            raise TypeError("Member must be a User instance")
        self.members.append(user)

    def get_emails(self):
        return [m.email for m in self.members]
