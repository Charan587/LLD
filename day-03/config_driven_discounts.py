"""Two levels of "add a discount without changing code".

  Level 1  new RULE SHAPE      -> one new class, zero edits to existing files
  Level 2  same shape, new numbers -> zero code at all, a config row

Most of marketing's 30 discounts are level 2. Only genuinely new rules are level 1.

Run: python3 config_driven_discounts.py
"""

import json
from dataclasses import dataclass
from rewrite import Cart, Customer, Product, checkout

# --- the registry: maps a config string to a class ----------------------
# A new discount class registers ITSELF. Nothing here is ever edited.

REGISTRY: dict[str, type] = {}


def discount_type(name: str):
    def register(cls):
        REGISTRY[name] = cls
        return cls
    return register


def build_discounts(config: list[dict]) -> list:
    """Turn plain data into discount objects."""
    return [REGISTRY[row["type"]](**{k: v for k, v in row.items() if k != "type"})
            for row in config]


# --- the rule shapes: written once ---------------------------------------

@discount_type("flat")
@dataclass(frozen=True)
class FlatDiscount:
    amount: float
    minimum: float = 0
    name: str = "Flat"

    def amount_off(self, cart: Cart) -> float:
        return self.amount if cart.subtotal >= self.minimum else 0.0


@discount_type("percent")
@dataclass(frozen=True)
class PercentDiscount:
    percent: float
    max_off: float | None = None
    category: str | None = None          # None = whole cart
    name: str = "Percent"

    def amount_off(self, cart: Cart) -> float:
        base = cart.subtotal if self.category is None else cart.total_for_category(self.category)
        off = base * self.percent / 100
        return min(off, self.max_off) if self.max_off is not None else off


@discount_type("loyalty")
@dataclass(frozen=True)
class LoyaltyDiscount:
    percent: float
    name: str = "Loyalty"

    def amount_off(self, cart: Cart) -> float:
        return cart.subtotal * self.percent / 100 if cart.customer.is_member else 0.0


# --- LEVEL 2: marketing edits this. No Python involved. ------------------

CONFIG = json.loads("""[
    {"type": "flat",    "amount": 100, "minimum": 1000,        "name": "Flat100"},
    {"type": "percent", "percent": 10, "category": "ELECTRONICS", "name": "Electronics10"},
    {"type": "loyalty", "percent": 5,                          "name": "Member5"}
]""")


# --- LEVEL 1: a genuinely new RULE. New class, zero edits above. ---------
# In real life this lives in its own file that nobody else imports.

@discount_type("cheapest_free")
@dataclass(frozen=True)
class CheapestItemFree:
    """Buy-N-get-cheapest-free. No existing rule shape can express this."""
    minimum_items: int
    name: str = "CheapestFree"

    def amount_off(self, cart: Cart) -> float:
        if len(cart.line_items) < self.minimum_items:
            return 0.0
        return min(li.product.unit_price for li in cart.line_items)


if __name__ == "__main__":
    def build_cart(is_member=True):
        cart = Cart(Customer("Charan", is_member))
        cart.add(Product("Laptop", 40000, "ELECTRONICS"), 1)
        cart.add(Product("Mouse", 1000, "ELECTRONICS"), 2)
        cart.add(Product("Rice", 100, "GROCERY"), 4)
        return cart

    # the day-3 spec, driven entirely from CONFIG
    order = checkout(build_cart(), build_discounts(CONFIG))
    assert order.total_discount == 6420
    assert order.total == 42456.40

    # LEVEL 2 — marketing adds "20% off clothing, max 500 off".
    # A config row. No class, no import, no deploy of Python.
    CONFIG.append({"type": "percent", "percent": 20, "category": "CLOTHING",
                   "max_off": 500, "name": "Clothing20"})

    cart = build_cart()
    cart.add(Product("Jacket", 5000, "CLOTHING"), 1)
    order = checkout(cart, build_discounts(CONFIG))
    # 20% of 5000 = 1000, capped at 500
    assert dict(order.breakdown)["Clothing20"] == 500

    # the cap actually binds only when it should
    small = Cart(Customer("x"))
    small.add(Product("Cap", 1000, "CLOTHING"), 1)
    assert PercentDiscount(20, max_off=500, category="CLOTHING").amount_off(small) == 200

    # LEVEL 1 — the new rule shape, added by a class and one config row
    CONFIG.append({"type": "cheapest_free", "minimum_items": 3, "name": "Cheapest"})
    order = checkout(cart, build_discounts(CONFIG))
    assert dict(order.breakdown)["Cheapest"] == 100      # rice is cheapest

    # nothing above ever learned these discounts exist
    assert set(REGISTRY) == {"flat", "percent", "loyalty", "cheapest_free"}

    print("all checks passed")
