"""Day 3 — Shopping Cart Checkout. Interview-grade rewrite.

═══════════════════════════════════════════════════════════════════════════
INTERVIEW WALKTHROUGH — what you say out loud, in order
═══════════════════════════════════════════════════════════════════════════

1. READ-BACK (~20s)
   "A cart of line items. Three discounts all apply at once, each computed
    against the subtotal, then tax on what's left, then a receipt. The two
    things I'm designing around are the 30 more discounts and the JSON
    receipt."

2. CLARIFYING QUESTIONS
   - "Do discounts stack against the original subtotal, or against a running
      total?" -> changes every number
   - "What happens if stacked discounts exceed the subtotal — can the bill
      go negative?" -> the one people miss
   - "Is the receipt format likely to change, or is text final?"

3. HOW I FOUND THE CLASSES
   Nouns: cart, line item, product, price, quantity, category, discount,
          tax, receipt, customer.
     product   -> name/price/category, no behaviour   -> data
     line item -> product + quantity                  -> LineItem
     cart      -> holds line items. THAT IS ALL.      -> Cart
     discount  -> carries a RULE                      -> class per rule
     receipt   -> a rendering of a computed result    -> its own function
     customer  -> needed for the member discount      -> Customer on the Cart

   THE KEY QUESTION I ask myself: "what IS a cart?" A cart is a collection
   of line items. It does not know tax law, marketing promotions, or what a
   receipt looks like. Those are three separate jobs.

4. ASSUMPTIONS
   - Each discount computes against the original subtotal, then they sum.
   - Total discount is capped at the subtotal — the bill never goes negative.
   - Money rounded to 2dp only at the end.

5. THE DESIGN I REJECTED
   "Putting subtotal, discounts, tax and receipt formatting all on Cart. It
    reads fine until you ask who files the next ticket: product team for
    cart contents, marketing for discounts, finance for tax, mobile for JSON.
    Four teams editing one class is four reasons to change."
   "I also rejected discounts returning the new total instead of the amount
    off — three discounts each claiming 'the total is X' can't be combined
    by any operator."

6. THE DESIGN + PRINCIPLE NAMES
   "Discounts are objects behind one amount_off(cart) contract, held in a
    list — that's OPEN/CLOSED, so discount 31 is a new file and checkout
    never changes."
   "The receipt is a separate function, not a Cart method — that's SINGLE
    RESPONSIBILITY. A cart changes when what it holds changes; a receipt
    changes when the output format changes."
   "They're different principles: OCP is about adding without editing, SRP
    is about separating things that change for different reasons."

7. LIMITS I'D VOLUNTEER
   - "Floats for money. Production wants Decimal or integer paise."
   - "Discount order doesn't matter here because they all hit the subtotal.
      If marketing wants 'apply after other discounts', I'd need an explicit
      ordering, and I'd push back on that requirement first."

═══════════════════════════════════════════════════════════════════════════
"""

from dataclasses import dataclass, field
from typing import Protocol

TAX_RATE = 0.18


@dataclass(frozen=True)
class Product:
    name: str
    unit_price: float
    category: str


@dataclass(frozen=True)
class LineItem:
    product: Product
    quantity: int

    @property
    def line_total(self) -> float:          # property, not cached in __init__
        return self.product.unit_price * self.quantity


@dataclass(frozen=True)
class Customer:
    name: str
    is_member: bool = False


@dataclass
class Cart:
    """Holds line items. Knows nothing about money rules, tax, or output."""
    customer: Customer
    line_items: list[LineItem] = field(default_factory=list)

    def add(self, product: Product, quantity: int) -> None:
        self.line_items.append(LineItem(product, quantity))

    @property
    def subtotal(self) -> float:
        return sum(li.line_total for li in self.line_items)

    def total_for_category(self, category: str) -> float:
        return sum(li.line_total for li in self.line_items
                   if li.product.category == category)


# --- discounts: uniform signature, so they stack in a loop ---------------

class Discount(Protocol):
    name: str
    def amount_off(self, cart: Cart) -> float: ...


@dataclass(frozen=True)
class FlatDiscount:
    amount: float
    minimum: float
    name: str = "Flat"

    def amount_off(self, cart: Cart) -> float:
        return self.amount if cart.subtotal >= self.minimum else 0.0   # >= not >


@dataclass(frozen=True)
class CategoryDiscount:
    category: str
    percent: float
    name: str = "Category"

    def amount_off(self, cart: Cart) -> float:
        return cart.total_for_category(self.category) * self.percent / 100


@dataclass(frozen=True)
class LoyaltyDiscount:
    percent: float
    name: str = "Loyalty"

    def amount_off(self, cart: Cart) -> float:
        # reads membership off the cart — signature stays amount_off(cart)
        return cart.subtotal * self.percent / 100 if cart.customer.is_member else 0.0


# --- checkout: arithmetic only, no formatting ---------------------------

@dataclass(frozen=True)
class Order:
    """The computed result. A receipt formatter needs nothing else."""
    cart: Cart
    breakdown: list[tuple[str, float]]
    subtotal: float
    total_discount: float
    taxable: float
    tax: float
    total: float


def checkout(cart: Cart, discounts: list[Discount], tax_rate: float = TAX_RATE) -> Order:
    subtotal = cart.subtotal
    breakdown = [(d.name, d.amount_off(cart)) for d in discounts]
    total_discount = min(sum(a for _, a in breakdown), subtotal)   # never below zero
    taxable = subtotal - total_discount
    tax = taxable * tax_rate
    return Order(cart, breakdown, subtotal, total_discount,
                 taxable, round(tax, 2), round(taxable + tax, 2))


# --- output: separate. JSON later = a second function, zero edits above --

def text_receipt(order: Order) -> str:
    lines = [f"{li.product.name} x{li.quantity}  {li.line_total:.2f}"
             for li in order.cart.line_items]
    lines.append(f"Subtotal  {order.subtotal:.2f}")
    lines += [f"{name}  -{amt:.2f}" for name, amt in order.breakdown if amt]
    lines.append(f"Tax  {order.tax:.2f}")
    lines.append(f"Total  {order.total:.2f}")
    return "\n".join(lines)


if __name__ == "__main__":
    LAPTOP = Product("Laptop", 40000, "ELECTRONICS")
    MOUSE = Product("Mouse", 1000, "ELECTRONICS")
    RICE = Product("Rice", 100, "GROCERY")

    DISCOUNTS = [FlatDiscount(100, 1000),
                 CategoryDiscount("ELECTRONICS", 10),
                 LoyaltyDiscount(5)]

    def build(is_member: bool) -> Cart:
        cart = Cart(Customer("Charan", is_member))
        cart.add(LAPTOP, 1); cart.add(MOUSE, 2); cart.add(RICE, 4)
        return cart

    member = build(True)
    assert member.subtotal == 42400

    # each discount alone, as an AMOUNT OFF
    assert FlatDiscount(100, 1000).amount_off(member) == 100
    assert CategoryDiscount("ELECTRONICS", 10).amount_off(member) == 4200
    assert LoyaltyDiscount(5).amount_off(member) == 2120

    o = checkout(member, DISCOUNTS)
    assert o.total_discount == 6420
    assert o.taxable == 35980
    assert o.tax == 6476.40
    assert o.total == 42456.40

    # non-member: loyalty contributes nothing
    n = checkout(build(False), DISCOUNTS)
    assert LoyaltyDiscount(5).amount_off(build(False)) == 0
    assert n.total_discount == 4300
    assert n.taxable == 38100
    assert n.total == 44958.00

    # boundary: exactly 1000 qualifies
    exact = Cart(Customer("x")); exact.add(Product("Bag", 1000, "CLOTHING"), 1)
    assert FlatDiscount(100, 1000).amount_off(exact) == 100
    under = Cart(Customer("x")); under.add(Product("Bag", 999, "CLOTHING"), 1)
    assert FlatDiscount(100, 1000).amount_off(under) == 0

    # no electronics -> no category discount
    veg = Cart(Customer("x")); veg.add(RICE, 4)
    assert CategoryDiscount("ELECTRONICS", 10).amount_off(veg) == 0

    # empty cart doesn't crash
    empty = checkout(Cart(Customer("x")), DISCOUNTS)
    assert empty.subtotal == 0 and empty.total == 0

    # discounts can never push the total negative
    silly = checkout(build(True), [FlatDiscount(999999, 0)])
    assert silly.total == 0

    assert "42456.40" in text_receipt(o)

    print("all checks passed")
