from dataclasses import dataclass, field
from enum import Enum, auto
from uuid import uuid4


class OrderSide(Enum):
    bid = auto()
    ask = auto()


@dataclass
class Order:
    price: float
    size: float
    side: OrderSide
    sender_id: str
    id: str = field(init=False)

    def __post_init__(self):
        self.id = str(uuid4())

    def __str__(self) -> str:
        return f"{self.price:.3f} ({self.size} lots)"


@dataclass
class Trade:
    buyer_id: str
    seller_id: str
    size: float
    price: float
