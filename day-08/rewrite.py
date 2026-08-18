"""Day 8 — Payment Gateway Integration. Interview-grade rewrite.

═══════════════════════════════════════════════════════════════════════════
INTERVIEW WALKTHROUGH — what you say out loud, in order
═══════════════════════════════════════════════════════════════════════════

1. READ-BACK (~20 seconds, before any questions)

   "Two payment gateways. For each one I need to charge, verify webhooks,
    and issue refunds. Each has its own id format, fee formula, signature
    convention and refund prefix. The constraint I'm hearing is that the
    application shouldn't know gateway names, and the three objects for a
    gateway have to stay matched."

2. CLARIFYING QUESTIONS (ask 3, not 10)

   - "Is this single-threaded, or will multiple charges run concurrently?"
     -> decides whether the id counter needs a lock
   - "Do fees ever depend on amount tiers, or is 2% flat at every amount?"
     -> the actual answer is flat; asking stops you inventing a threshold
   - "Should a mismatched refund raise, or return a failure value?"
     -> decides your error convention before you write eight methods

3. HOW I FOUND THE CLASSES (say this while sketching)

   Underline the nouns in the statement:
     gateway, payment, fee, webhook, signature, refund, payment id

     payment    -> a value object. It has data, no behaviour.        -> Payment
     gateway    -> not one class. It is three roles that travel together.
     charge     -> PaymentClient
     verify     -> WebhookVerifier
     refund     -> RefundProcessor
     fee        -> a number the client computes, not its own class (yet)
     signature  -> a string, not a class

   Circle the verbs: charge, verify, refund. One per role. That is the
   capability table from day 4, and it is why there are three protocols
   rather than one interface with three methods on it.

4. ASSUMPTIONS (state them, don't ask)

   - Single-threaded. Id counters are plain ints, not locked.
   - Amounts are integer paise throughout; no floats in the money path.
   - A payment can be refunded once. Second attempt raises.
   - Webhook payloads are opaque strings; I'm not parsing them.

5. THE DESIGN I REJECTED (say this unprompted — it is scored)

   "First instinct was one class per gateway with charge/verify/refund on it.
    That does guarantee the three stay matched, and I'd accept it for three
    methods. I moved off it because they have different dependencies — the
    client needs an API key, the verifier needs a webhook secret — and the
    sandbox requirement wants to swap all three for fakes independently.
    One fat class also forces a charge-only gateway to implement refunds."

   "Second thing I rejected: letting callers construct the three pieces
    themselves and relying on discipline. isinstance can't catch a mismatch —
    Stripe's verifier is a perfectly valid WebhookVerifier, it's just the
    wrong one. The bug isn't in any object, it's in the combination."

6. THE DESIGN + PATTERN NAMES (this is the sentence that scores)

   "get_gateway(name) returns one object chosen at runtime — that's
    FACTORY METHOD. Each factory then produces a matched set of three —
    that's ABSTRACT FACTORY. The difference is exactly that: Factory Method
    creates one product; Abstract Factory creates a family that has to be
    consistent with itself. Requirement 7 is why I need the second one."

   "It gives me Open/Closed — a third gateway is one factory class and one
    registry row, and nothing that charges, verifies or refunds changes."

7. LIMITS I'D VOLUNTEER AT THE END (before being asked)

   - "Id counters are per-process. Two app servers would both mint _1.
      Real fix is the gateway's own id, or a DB sequence."
   - "No retry or idempotency key — a network timeout could double-charge."
   - "Fee formulas are hardcoded in the clients. If finance changes them
      weekly, they belong in config."

═══════════════════════════════════════════════════════════════════════════
"""

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


def _check_amount(paise: int) -> None:
    if paise <= 0:
        raise ValueError(f"amount must be positive, got {paise}")


@dataclass(frozen=True)
class Payment:
    id: str
    amount_paise: int
    fee_paise: int

    @property
    def total_paise(self) -> int:
        return self.amount_paise + self.fee_paise


# ── the three roles ────────────────────────────────────────────────────────

@runtime_checkable
class PaymentClient(Protocol):
    def charge(self, paise: int) -> Payment: ...


@runtime_checkable
class WebhookVerifier(Protocol):
    def verify(self, payload: str, signature: str) -> bool: ...


@runtime_checkable
class RefundProcessor(Protocol):
    def refund(self, payment_id: str) -> str: ...


# ── Razorpay ───────────────────────────────────────────────────────────────

class RazorpayClient:
    def __init__(self):
        self._next_id = 1                      # instance state — see assert 3

    def charge(self, paise: int) -> Payment:
        _check_amount(paise)
        payment = Payment(f"pay_rzp_{self._next_id}", paise, round(paise * 0.02))
        self._next_id += 1
        return payment


class RazorpayVerifier:
    def verify(self, payload: str, signature: str) -> bool:
        return signature == f"rzp_{payload}"    # a bool: this IS a yes/no question


class RazorpayRefunder:
    def refund(self, payment_id: str) -> str:
        if not payment_id.startswith("pay_rzp_"):
            raise ValueError(f"not a Razorpay payment id: {payment_id}")
        return f"rfnd_{payment_id}"             # raises: this is a BROKEN CALL


# ── Stripe ─────────────────────────────────────────────────────────────────

class StripeClient:
    def __init__(self):
        self._next_id = 1

    def charge(self, paise: int) -> Payment:
        _check_amount(paise)
        payment = Payment(f"ch_stripe_{self._next_id}", paise, round(paise * 0.029) + 300)
        self._next_id += 1
        return payment


class StripeVerifier:
    def verify(self, payload: str, signature: str) -> bool:
        return signature == f"whsec_{payload}"


class StripeRefunder:
    def refund(self, payment_id: str) -> str:
        if not payment_id.startswith("ch_stripe_"):
            raise ValueError(f"not a Stripe payment id: {payment_id}")
        return f"re_{payment_id}"               # re_, not rfnd_


# ── ABSTRACT FACTORY: a family, guaranteed consistent ──────────────────────

class GatewayFactory(Protocol):
    name: str
    def create_client(self) -> PaymentClient: ...
    def create_verifier(self) -> WebhookVerifier: ...
    def create_refunder(self) -> RefundProcessor: ...


class RazorpayFactory:
    name = "razorpay"
    def create_client(self) -> PaymentClient:      return RazorpayClient()
    def create_verifier(self) -> WebhookVerifier:  return RazorpayVerifier()
    def create_refunder(self) -> RefundProcessor:  return RazorpayRefunder()


class StripeFactory:
    name = "stripe"
    def create_client(self) -> PaymentClient:      return StripeClient()
    def create_verifier(self) -> WebhookVerifier:  return StripeVerifier()
    def create_refunder(self) -> RefundProcessor:  return StripeRefunder()


# ── FACTORY METHOD: one product, chosen at runtime ─────────────────────────

FACTORIES: dict[str, type] = {"razorpay": RazorpayFactory, "stripe": StripeFactory}


def get_gateway(name: str) -> GatewayFactory:
    if name not in FACTORIES:
        raise ValueError(f"unknown gateway: {name!r}")
    return FACTORIES[name]()


def register_gateway(name: str, factory_cls: type) -> None:
    FACTORIES[name] = factory_cls


def raises(fn, *args) -> bool:
    try:
        fn(*args)
    except ValueError:
        return True
    return False


if __name__ == "__main__":
    # 1, 2 — fees
    assert RazorpayClient().charge(50000).fee_paise == 1000
    assert StripeClient().charge(50000).fee_paise == 1750

    # the fee is unconditional — no invented threshold
    assert RazorpayClient().charge(1000).fee_paise == 20
    assert StripeClient().charge(1000).fee_paise == 329

    # 3 — ids increment per gateway, counters independent
    rzp, stripe = RazorpayClient(), StripeClient()
    assert rzp.charge(50000).id == "pay_rzp_1"
    assert rzp.charge(50000).id == "pay_rzp_2"
    assert stripe.charge(50000).id == "ch_stripe_1"      # not _3
    assert RazorpayClient().charge(50000).id == "pay_rzp_1"   # a new client restarts

    # 4 — zero and negative
    for client in (RazorpayClient(), StripeClient()):
        assert raises(client.charge, 0)
        assert raises(client.charge, -100)

    # 5 — the caller never names a gateway class
    client = get_gateway("razorpay").create_client()
    assert client.charge(50000).id.startswith("pay_rzp_")

    # 6 — unknown gateway
    assert raises(get_gateway, "paypal")

    # 7, 8 — verifiers. Note these return bools, they do not raise.
    assert get_gateway("razorpay").create_verifier().verify("abc", "rzp_abc") is True
    assert get_gateway("razorpay").create_verifier().verify("abc", "whsec_abc") is False
    assert get_gateway("stripe").create_verifier().verify("abc", "whsec_abc") is True
    assert get_gateway("stripe").create_verifier().verify("abc", "rzp_abc") is False

    # 9 — refund, right family
    assert get_gateway("razorpay").create_refunder().refund("pay_rzp_1") == "rfnd_pay_rzp_1"
    assert get_gateway("stripe").create_refunder().refund("ch_stripe_1") == "re_ch_stripe_1"

    # 10 — wrong family RAISES. Not False, not None.
    rzp_refunder = get_gateway("razorpay").create_refunder()
    assert raises(rzp_refunder.refund, "ch_stripe_1")
    assert raises(get_gateway("stripe").create_refunder().refund, "pay_rzp_1")

    # 11 — one request, three consistent objects, end to end
    for name, sig_prefix, refund_prefix in [("razorpay", "rzp_", "rfnd_"),
                                            ("stripe", "whsec_", "re_")]:
        f = get_gateway(name)
        c, v, r = f.create_client(), f.create_verifier(), f.create_refunder()
        payment = c.charge(50000)
        assert v.verify(payment.id, f"{sig_prefix}{payment.id}") is True
        assert r.refund(payment.id) == f"{refund_prefix}{payment.id}"

    # 12 — a third gateway. Nothing above changes.
    class CashfreeClient:
        def __init__(self): self._next_id = 1
        def charge(self, paise):
            _check_amount(paise)
            p = Payment(f"cf_{self._next_id}", paise, round(paise * 0.018))
            self._next_id += 1
            return p

    class CashfreeVerifier:
        def verify(self, payload, signature): return signature == f"cf_{payload}"

    class CashfreeRefunder:
        def refund(self, payment_id):
            if not payment_id.startswith("cf_"):
                raise ValueError(f"not a Cashfree payment id: {payment_id}")
            return f"cfrfnd_{payment_id}"

    class CashfreeFactory:
        name = "cashfree"
        def create_client(self):   return CashfreeClient()
        def create_verifier(self): return CashfreeVerifier()
        def create_refunder(self): return CashfreeRefunder()

    register_gateway("cashfree", CashfreeFactory)

    f = get_gateway("cashfree")
    c, v, r = f.create_client(), f.create_verifier(), f.create_refunder()
    p = c.charge(50000)
    assert p.id == "cf_1" and p.fee_paise == 900
    assert v.verify(p.id, f"cf_{p.id}") is True
    assert r.refund(p.id) == "cfrfnd_cf_1"
    assert raises(r.refund, "pay_rzp_1")

    # every factory is usable through the SAME calls — no per-gateway signatures
    for name in ("razorpay", "stripe", "cashfree"):
        f = get_gateway(name)
        assert isinstance(f.create_client(), PaymentClient)
        assert isinstance(f.create_verifier(), WebhookVerifier)
        assert isinstance(f.create_refunder(), RefundProcessor)

    print("all checks passed")
