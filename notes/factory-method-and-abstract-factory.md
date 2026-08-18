# Factory Method and Abstract Factory

Derived from day 8. Every trace is real output from code that was run.

---

## 1. The problem

Two payment gateways, Razorpay and Stripe. For **each** you need three things:

| | Razorpay | Stripe |
|---|---|---|
| **client** — charges a card | ids `pay_rzp_N`, fee 2% | ids `ch_stripe_N`, fee 2.9% + 300 |
| **verifier** — checks webhook signatures | valid sig is `rzp_<payload>` | valid sig is `whsec_<payload>` |
| **refunder** — issues refunds | accepts `pay_rzp_*`, returns `rfnd_*` | accepts `ch_stripe_*`, returns `re_*` |

Two constraints:

- The application must never name a gateway class. It says `"stripe"` once, in config.
- **It must be impossible to end up with Stripe's client and Razorpay's verifier.**

---

## 2. Why the obvious design fails

Obvious version: define the six classes, let callers build what they need.

```python
client, verifier, refunder = StripeClient(), RzpVerifier(), RzpRefunder()
```

```
STEP 1 — caller builds the pieces itself. Nothing stops a mismatch:
   charged with Stripe -> ch_stripe_1
   verify with Razorpay's verifier -> False  <-- real Stripe signature rejected
   refund -> not a Razorpay id: ch_stripe_1
   every object is individually valid. The COMBINATION is the bug.
```

Read the last line twice. **`RzpVerifier` is a perfectly good verifier.** It has the right method, the right signature, correct logic. `StripeClient` is a perfectly good client. Nothing is broken.

The bug lives in a place no object can see: **the relationship between three objects.**

### Why day 4's tool can't help

You might reach for `isinstance` — the ISP move from day 4:

```python
isinstance(verifier, WebhookVerifier)   # True. It IS a verifier.
```

**Protocols check shape, not family.** Every verifier satisfies `WebhookVerifier`; that's the point of the protocol. It can tell you *"this is a verifier"* and can never tell you *"this is the wrong one."*

This is the same lesson as the day-4 note's library class — an unrelated class with a `refund()` method passed `isinstance(x, Refundable)` and "refunded" a book. Structural typing matches on names.

### Why "we'll be careful" isn't a design

Six classes, three roles: nine wrong combinations, three right ones. The wrong ones compile, pass type checks, and often work in staging where only one gateway is configured. They fail in production at 2am on the gateway nobody tested.

**When correctness depends on remembering, it isn't correct — it's lucky.**

---

## 3. The two patterns

### Factory Method

> Create **one** product, with the concrete type decided at runtime.

```python
FACTORIES = {"razorpay": RazorpayFactory, "stripe": StripeFactory}

def get_gateway(name):
    if name not in FACTORIES:
        raise ValueError(f"unknown gateway: {name!r}")
    return FACTORIES[name]()
```

The caller says `"stripe"` and gets an object. It never types `StripeFactory`.

### Abstract Factory

> Create a **family** of related products that must be consistent with each other.

```python
class StripeFactory:
    name = "stripe"
    def create_client(self):   return StripeClient()
    def create_verifier(self): return StripeVerifier()
    def create_refunder(self): return StripeRefunder()
```

### The one-line difference — this is the exam question

> **Factory Method creates one product. Abstract Factory creates a set of products that have to be consistent with each other.**

You reach for the second the moment "get me a thing" becomes "get me several things that must match."

---

## 4. Dry run of the fixed design

```
STEP 2 — nobody constructs pieces. One object hands out a matched set:
   charged -> ch_stripe_1
   verify  -> True
   refund  -> re_ch_stripe_1
   to mix families you would have to call get_gateway twice on purpose.
```

That last line is the property that matters. **Mixing isn't forbidden — it's unreachable by accident.** A caller writes `f = get_gateway("stripe")` and then `f.create_*()`; nothing in that flow can produce a Razorpay verifier. You'd have to deliberately call `get_gateway` twice and cross the wires.

Compare the two designs on how they *prevent* the bug:

| | prevents mismatch by |
|---|---|
| caller builds pieces | discipline |
| `isinstance` checks | nothing — can't see it |
| one fat class per gateway | there's only one object |
| **Abstract Factory** | the caller never constructs a piece |

---

## 5. The fat-class alternative, honestly

One class per gateway with `charge`, `verify` and `refund` on it also guarantees consistency — one object, nothing to mix. **It's a legitimate answer and worth saying you considered it.**

What it costs:

- **ISP** — a charge-only gateway must still implement refunds.
- **Different dependencies in one class** — the client needs an API key, the verifier needs a webhook secret. Now one constructor takes both.
- **Can't substitute one piece.** Sandbox mode wanting a fake verifier but a real client is impossible.
- Three reasons to change in one file.

**Pick either. Say which and why.** The choice *is* the answer to "what's the difference between the two patterns."

---

## 6. Making it actually work: one uniform signature

The trap that silently undoes the pattern:

```python
class RazorpayFactory:
    def create_client(self, percentage, min_amount, prefix): ...
class StripeFactory:
    def create_client(self, percentage, min_amount, base_cost, prefix): ...
```

```
razorpay: create_client() -> TypeError: missing 3 required positional arguments
stripe:   create_client() -> TypeError: missing 4 required positional arguments
```

Different signatures mean you **cannot** write:

```python
for name in ("razorpay", "stripe"):
    client = get_gateway(name).create_client()
```

The caller must know which concrete factory it holds — which is what the factory existed to prevent. And it leaks the coupling a second way: the app doesn't name `RazorpayClient`, but it has to know Razorpay's fee rate and id prefix.

**A factory that needs to be told how to build its own product isn't a factory.** Configuration belongs inside the product, or in the *factory's* constructor — never at the call site.

---

## 7. What it buys

**A third gateway is one class and one registry row.** Nothing that charges, verifies or refunds changes — that's Open/Closed, and the way to prove it in an interview is to add a gateway inside your assert block rather than claim it.

**Sandbox mode is one more factory.** `FakeGatewayFactory` returning three recording fakes. Same inversion as day 5's `FixedClock`/`FakeNotifier` — this time for a whole family.

**The gateway name appears exactly once.** In config. Grep for `"stripe"` and you find one line.

---

## 8. Bug list

- **`if name == "stripe": ... elif name == "razorpay":`** repeated in more than one place. Each repetition is a place someone forgets to update.
- **Different `create_*` signatures per factory** — kills polymorphism; see above.
- **Config passed at the call site** — the coupling you removed, wearing a hat.
- **Factory returning a cached instance** when the product holds mutable state. Day 8's clients hold an id counter; a shared instance means two callers share a counter.
- **A factory method returning `None`** because a stub was never filled. `CashfreeFactory.create_client()` returning `None` fails far away from the cause.
- **Using `isinstance` to catch a family mismatch.** It structurally cannot.
- **Reaching for Strategy here.** Two gateways are not two algorithms for one job — they're two families of collaborating objects. Strategy swaps *how one thing is done*; Abstract Factory swaps *which set of collaborators you get*.

---

## 9. Saying it in an interview

> "`get_gateway(name)` returns one object chosen at runtime from a registry — that's **Factory Method**. Each of those factories then produces a matched set of three: client, verifier, refunder — that's **Abstract Factory**.
>
> The difference is exactly that: Factory Method creates one product, Abstract Factory creates a family that has to be self-consistent. I need the second one because the three objects have to come from the same gateway — Stripe's verifier is a perfectly valid `WebhookVerifier`, it's just the wrong one, and no `isinstance` check can see that. The bug isn't in any object, it's in the combination.
>
> I did consider one fat class per gateway with all three methods — that also guarantees consistency, and I'd take it for three methods. I went the other way because they have different dependencies and the sandbox requirement wants to swap them independently.
>
> It gives me **Open/Closed**: a third gateway is one factory class and one registry row, and nothing that charges, verifies or refunds changes."
