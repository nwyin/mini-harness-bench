"""In-memory data models for the API."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class User:
    user_id: int
    user_name: str
    email: str
    created_at: str
    is_active: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Product:
    product_id: int
    product_name: str
    unit_price: float
    stock_count: int
    category_name: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Order:
    order_id: int
    user_id: int
    product_id: int
    quantity: int
    total_price: float
    order_date: str
    shipping_status: str = "pending"

    def to_dict(self) -> dict:
        return asdict(self)


# In-memory data store
USERS: list[User] = [
    User(1, "alice", "alice@example.com", "2024-01-15T10:30:00Z"),
    User(2, "bob", "bob@example.com", "2024-02-20T14:00:00Z"),
    User(3, "charlie", "charlie@example.com", "2024-03-10T09:15:00Z"),
    User(4, "diana", "diana@example.com", "2024-04-05T16:45:00Z", is_active=False),
]

PRODUCTS: list[Product] = [
    Product(1, "Widget A", 9.99, 100, "widgets"),
    Product(2, "Gadget B", 24.99, 50, "gadgets"),
    Product(3, "Widget C", 14.99, 0, "widgets"),
    Product(4, "Doohickey D", 49.99, 25, "doohickeys"),
]

ORDERS: list[Order] = [
    Order(1, 1, 1, 3, 29.97, "2024-05-01T12:00:00Z", "shipped"),
    Order(2, 1, 2, 1, 24.99, "2024-05-02T13:00:00Z", "delivered"),
    Order(3, 2, 4, 2, 99.98, "2024-05-03T14:00:00Z", "pending"),
    Order(4, 3, 1, 5, 49.95, "2024-05-04T15:00:00Z", "shipped"),
    Order(5, 2, 3, 1, 14.99, "2024-05-05T16:00:00Z", "cancelled"),
]
