"""so here product(name, unit_price, category)
  line_item(product , quantity, line_total )
  disocunt (name , rule)
  
  """
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Product:
    name: str
    unit_price: float
    category: str

class LineItem:
    def __init__(self, product: Product, quantity: int):
        self.product = product
        self.quantity = quantity
        self.line_total = self.calculate_line_total()

    def calculate_line_total(self) -> float:
        return self.product.unit_price * self.quantity

class Discount:
    def __init__(self, name: str):
        self.name = name

class FlatDiscount(Discount):
    def __init__(self, name: str, amount: float):
        super().__init__(name)
        self.amount = amount

    def apply_discount(self, cart: "Cart", is_loyal: bool) -> float:
        total = 0
        for line_item in cart.line_items:
            total += line_item.line_total
        return total - self.amount if total > 1000 else total

class CategoryDiscount(Discount):
    def __init__(self, name: str, category: str):
        super().__init__(name)
        self.category = category

    def apply_discount(self, cart: "Cart", is_loyal: bool) -> float:
        total = 0
        for line_item in cart.line_items:
            if line_item.product.category == self.category:
                total += line_item.line_total * 0.9
            else:
                total += line_item.line_total
        return total

class LoyaltyDiscount(Discount):
    def __init__(self, name: str):
        super().__init__(name)

    def apply_discount(self, cart: "Cart", is_loyal: bool) -> float:
        if is_loyal:
            return cart.calculate_total() * 0.95 
        return cart.calculate_total()


class Cart:
    def __init__(self):
        self.line_items = []

    def add_line_item(self, line_item: LineItem):
        self.line_items.append(line_item)


    def calculate_total(self) -> float:
        return sum(item.line_total for item in self.line_items)


class Checkout:
    def __init__(self, cart: Cart):
        self.cart = cart
        self.discounts = []

    def add_discount(self, discount: Discount):
            self.discounts.append(discount)

    def calculate_total(self) -> float:
        return self.cart.calculate_total()

    def calculate_discount(self, is_loyal: bool) -> float:
        total = self.cart.calculate_total()
        discounted_total = 0
        for discount in self.discounts:
            discounted_total += total - discount.apply_discount(self.cart, is_loyal)
        return discounted_total

    def calculate_discounted_total(self, is_loyal: bool) -> float:
            total = self.cart.calculate_total()
            for discount in self.discounts:
                total = discount.apply_discount(self.cart, is_loyal)
            return total

    def calculate_final_total(self, is_loyal: bool) -> float:
        return self.cart.calculate_discounted_total(is_loyal)

    def taxable_amount(self, is_loyal: bool) -> float:
        return self.calculate_final_total(is_loyal) 

    def tax_amount(self, tax_rate: float, is_loyal: bool) -> float:
        return self.taxable_amount(is_loyal) * tax_rate

    def final_amount(self, tax_rate: float, is_loyal: bool) -> float:
        return self.taxable_amount(is_loyal) + self.tax_amount(tax_rate, is_loyal)


if __name__ == "__main__":
    # Example usage
    product1 = Product("Laptop", 40000, "Electronics")
    product2 = Product("Shirt", 200, "Clothing")
    product3 = Product("Rice", 100, "Grocery")
    product4 = Product("Mouse", 1000, "Electronics")

    line_item1 = LineItem(product1, 1)
    line_item2 = LineItem(product2, 1)
    line_item3 = LineItem(product3, 4)
    line_item4 = LineItem(product4, 2)

    cart = Cart()
    cart.add_line_item(line_item1)
    cart.add_line_item(line_item3)
    cart.add_line_item(line_item4)

    checkout = Checkout(cart)

    checkout.add_discount(FlatDiscount("Flat Discount", 100))
    checkout.add_discount(CategoryDiscount("Electronics Discount", "Electronics"))
    checkout.add_discount(LoyaltyDiscount("Loyalty Discount"))


    assert checkout.calculate_total() == 42400
    assert FlatDiscount("Flat Discount", 100).apply_discount(cart, is_loyal=False) == 42300
    assert CategoryDiscount("Electronics Discount", "Electronics").apply_discount(cart, is_loyal=False) == 41600
    assert LoyaltyDiscount("Loyalty Discount").apply_discount(cart, is_loyal=True) == 40280.0
    assert checkout.calculate_discount(is_loyal=True) == 2120.0
    assert checkout.calculate_discounted_total(is_loyal=True) == 40280.0
    assert checkout.calculate_final_total(is_loyal=True) == 40280.0
    assert checkout.taxable_amount(is_loyal=True) == 40280.0
    assert checkout.tax_amount(tax_rate=0.18, is_loyal=True) == 7250.4
    assert checkout.final_amount(tax_rate=0.18, is_loyal=True) == 47530.4


    print("All test cases passed!")
