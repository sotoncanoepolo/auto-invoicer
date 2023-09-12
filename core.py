from dataclasses import dataclass, field

from utils import to_decimal_cost


class InvoiceItem:
    def __init__(self, name: str, description: str, cost: int):
        self.name = name
        self.description = description
        # Cost is in pence
        self.cost = cost

    def to_invoice(self) -> dict[str]:
        cost = to_decimal_cost(self.cost)

        return {"ItemID": "0", "ItemName": self.name, "ItemDescription": self.description,
                "UnitCost": f'{cost}', "Qty": "1"}


@dataclass
class Person:
    name: str
    row: int
    costs: list[InvoiceItem] = field(default_factory=list)
    client_id: int | None = None
    invoice_id: int | None = None
    direct_url: str | None = None
    total_cost: int | None = None
