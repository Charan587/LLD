# Day 8 Review — Payment Gateway Integration (Python)

Reviewed 2026-08-18. Submission preserved as `solution.submitted.py`.

## Verdict

```
$ python3 solution.py
all test case passed
exit: 0
```

**It ran and it printed.** W10 closed again after day 7's silent `exit 0`.

**And both patterns are structurally right.** `Factory` base with `create_client` / `create_verifier` / `create_refunder`, concrete `RazorPayFactory` and `StripeFactory`, and `FactoryGateWay` holding a name→factory map with `get_factory` raising on unknown names. That is Abstract Factory sitting behind Factory Method, which is exactly the day's shape. The `add()` method for registering a gateway is a nice touch I didn't ask for.

You also named a pattern in the file — *"patterns - as far i know ISP, factory and startergy"* — first time in six days that anything got named.

Then the details.

## Score

| Axis | D4 | D5 | D6 | D7 | D8 | Why |
|---|---|---|---|---|---|---|
| Correctness | 2 | 2 | 2 | 1 | **2** / 5 | Fee gated by an invented threshold; Stripe refund prefix wrong; no amount validation; verifier checks the wrong thing |
| Extensibility | 4 | 4 | 4 | 3 | **3** / 5 | Registry + `add()` is right — but `create_client` has a different signature per factory, so factories aren't interchangeable |
| SOLID | 4 | 4 | 4 | 3 | **3** / 5 | Family consistency achieved. The non-uniform `create_client` breaks the abstraction it sits behind. |
| Readability | 3 | 3 | 2 | 2 | **2** / 5 | `Verifier.verifier`; base methods missing `self`; Protocol annotated `-> None` while returning `Payment` |
| Communication | 2 | 3 | 3 | 1 | **3** / 5 | All three items present; a pattern named — but not *which* factory, and "Strategy" isn't in play here |

**13 / 25.** Up from 10.

---

## The one that undercuts the pattern

```python
class RazorPayFactory(Factory):
    def create_client(self, percentage, min_amount, prefixPay): ...

class StripeFactory(Factory):
    def create_client(self, percentage, min_amount, base_cost, prefixPay): ...
```

```
razorpay: create_client() -> TypeError: missing 3 required positional arguments
stripe:   create_client() -> TypeError: missing 4 required positional arguments
```

**The two factories have different signatures**, so you cannot write code that works against `Factory` without knowing which one you have:

```python
for name in ("razorpay", "stripe"):
    client = get_gateway(name).create_client()      # impossible in your version
```

This is day 4's lesson, arriving from a new angle. Polymorphism needs **one uniform signature** — the moment they differ, the caller must know the concrete type, and knowing the concrete type is precisely what the factory existed to prevent.

It also leaks the thing requirement 4 was protecting. Your caller writes:

```python
razorPayFactory.create_client(percentage=0.02, min_amount=50000, prefixPay="pay_rzp_")
```

The application doesn't name `RazorPayClient` — but it knows Razorpay's fee rate and id prefix, which is the same coupling wearing a hat. **A factory that needs to be told how to build its own product isn't a factory.** Move the config inside:

```python
class RazorpayClient:
    def __init__(self):
        self._next_id = 1
    def charge(self, paise):
        return Payment(f"pay_rzp_{self._next_id}", paise, round(paise * 0.02))
```

Now `create_client()` takes nothing, all factories match, and the loop above works. If those rates must be configurable later, they go into the *factory's* constructor — `RazorpayFactory(fee_percent=0.02)` — never the call site.

## `min_amount` — an invented requirement, second time

```python
if amount >= self.min_amount:
    charge = self.percentage * amount
```

```
razorpay charge(50000) -> fee 1000.0   (spec: 1000.0)
razorpay charge(49999) -> fee None     (spec: 999.98)
razorpay charge(1000)  -> fee None     (spec: 20.0)
```

My spec says Razorpay charges **2%**. Unconditionally. There is no minimum anywhere in the statement. Below ₹500 your fee is `None`, and `Payment.total_amount` has a special case to cope with the `None` you invented.

**Day 7 was `max_amount` gating the credit card fee. Today it's `min_amount` gating the gateway fee.** Twice now you've added a threshold the spec didn't ask for, and both times your one test used the exact value where the invention is invisible.

Two costs worth naming: it's unrequested work, and it manufactures a `None` in a money path — the thing you then have to defend against everywhere downstream.

If you genuinely think a real gateway has a minimum, that's a **clarifying question** at minute three, or an assumption line. Not silent code.

## Stripe's refund prefix

```python
class StripePayRefund(Refund):
    def refund(self, payment):
        payment.refund_id = f"rfnd_{payment.id}"     # spec says re_
```

```
stripe refund id -> rfnd_ch_stripe_1   (spec: re_ch_stripe_1)
```

Copy-pasted from `RazorPayRefund` with the guard updated and the prefix left behind. **Identical shape to day 7's `PerMinute` using `ride.km`** — copy the class, change the check, forget the payload.

The guard direction is right though, and worth crediting: `if "rzp" not in payment.id: raise` — **it raises.** Requirement 8, and the correction from day 7's grill, both landed. The double-refund guard is extra credit; I didn't ask for it.

## The verifier verifies the wrong thing

```python
def verifier(self, payment: Payment, signature: str):
    return signature == f"rzp_{payment.id}"
```

A webhook signature signs the **payload** — the body of the message the gateway POSTs you. Your version signs the payment id, which means you can only verify webhooks about payments you already have objects for. A real webhook arrives as bytes from the internet before you know anything about it.

The spec's signature is `verify(payload, signature)`. Asserts 7 and 8 weren't written, which is why this went unnoticed.

Also: the class is `Verifier` and the method is `verifier`. A class is a noun, a method is a verb — `Verifier.verify`.

## No amount validation

```
charge(0)    -> id pay_rzp_1, amount 0, fee None
charge(-100) -> id pay_rzp_2, amount -100, fee None
```

Requirement 3, assert 4. A charge of −100 creates a payment and burns an id. **This is W5's sixth appearance** — day 1's date range, day 3, day 4's negative payment adding money, day 5, day 6, now here.

It's one function called from two places:

```python
def _check_amount(paise: int) -> None:
    if paise <= 0:
        raise ValueError(f"amount must be positive, got {paise}")
```

I'd put this on your permanent pre-submit checklist: **for every public method that takes a number, ask what it does with 0 and with −1.**

## Asserts

Roughly 8 of 12. Missing: **4** (zero/negative), **7 and 8** (both verifiers), **11** (the family end-to-end), and **12** is half-done — `CashFreeFactory` exists but every method is `pass`, `gateway.add` is called *after* the print, and nothing asserts anything about it.

```
cashfree create_client()   -> None
create_verifier()          -> None
```

Assert 12 was the one that proves the OCP claim. My rewrite defines a full third gateway inside the assert block and charges, verifies and refunds with it.

**Assert 11 is the one that would have caught the Stripe prefix bug.** "Charge with the family, verify with the family, refund the id you just created" — one loop over both gateways, and `rfnd_ch_stripe_1` fails immediately.

## Patterns named — half credit

> patterns - as far i know ISP , factory and startergy

**"Factory" is right and it's progress.** But:

- **Which factory?** The whole point of pairing them today is that `get_factory(name)` is **Factory Method** (one product, chosen at runtime) and `RazorPayFactory` is **Abstract Factory** (a family that must be self-consistent). You built both and named neither specifically.
- **Strategy isn't here.** Strategy is interchangeable algorithms for *one* job — day 7's fare calculation. Two gateways aren't two strategies; they're two families of collaborating objects. Reaching for the most recent name is worth watching for.
- **ISP is fair** — three protocols rather than one fat gateway interface.

The sentence to have ready:

> "Factory Method creates one product; Abstract Factory creates a set of products that must be consistent with each other. Requirement 7 is why I need the second one."

## Smaller things

- `PaymentClient` protocol: `def charge(amount:int)->None` — missing `self`, and annotated `None` while every implementation returns a `Payment`.
- `Verifier` and `Refund` base classes have methods without `self`. They're never called, so it never fires — but `Refund.refund(payment)` would bind `payment` to `self`.
- `RazorPayClient(PaymentClient)` inherits from a `Protocol`. It works (nominal), but you use protocols structurally elsewhere. Pick one style per file.
- `Payment` is mutable with every field defaulting to `None`, so `Payment()` is a valid empty payment. Required fields shouldn't have defaults.
- The `print` sits before `gateway.add("cashfree", ...)`, so the last two lines aren't covered by "all test case passed."

## The rewrite

`rewrite.py`, `all checks passed`. Your factory structure kept and made uniform: `create_client()` takes no arguments, so all three factories are interchangeable; config lives inside the clients; verifier takes a payload; Stripe refunds with `re_`; `_check_amount` at every entry; and a complete Cashfree gateway defined inside the asserts.

**It also now opens with the interview walkthrough you asked for** — read-back, the three questions to ask, how the nouns became classes, assumptions, the rejected design in quotes, the pattern sentence, and the limits to volunteer at the end. **Days 1-7 have the same block added**, all still passing.

## Grill

1. I said "a factory that needs to be told how to build its own product isn't a factory." **Where should the fee rates live** if finance changes them weekly and can't deploy code?
2. Your `FactoryGateWay` stores factory **classes** and instantiates on lookup; mine stores classes too but `get_gateway` returns a fresh instance each call. **Name one bug** that appears if it returned a cached singleton instead.
3. Requirement: sandbox mode where all three objects are fakes. **How many files change** in my rewrite, and which pattern does it exercise?
4. You added a double-refund guard I never asked for. **Argue it's wrong** — then say what convinces you it's right.
5. `verify` returns a bool but `refund` raises. **State the rule** that decides which, and give one case from days 1-7 where you picked wrong.
6. Two app servers run this. **Which assert in my file starts failing**, and what's the fix that doesn't involve locks?
