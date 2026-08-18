# Day 8 — Payment Gateway Integration

**Time box: 45 minutes.** Two patterns today — the second is a small delta on the first.

---

## Part 1

You integrate with two payment gateways: **Razorpay** and **Stripe**. All amounts are handled in **paise** (₹1 = 100 paise).

### Charging

| | Payment id | Fee on a ₹500 charge |
|---|---|---|
| Razorpay | `pay_rzp_1`, `pay_rzp_2`, … | 2% → **1000 paise** |
| Stripe | `ch_stripe_1`, `ch_stripe_2`, … | 2.9% + 300 paise → **1750 paise** |

1. `charge(amount_paise)` returns a payment record with the gateway's id format, the amount, and the fee.
2. Ids increment **per gateway**, starting at 1.
3. Charging zero or a negative amount is an error.

4. **The rest of the application must never name a gateway class.** It says "razorpay" or "stripe" once, in configuration, and gets back something it can charge with. Adding a third gateway must not touch any calling code.

---

## Part 2

Charging isn't the whole integration. Each gateway also needs:

- a **webhook verifier** — checks that an incoming payload's signature is genuine
- a **refund processor** — issues a refund against a payment id

| | Valid signature for payload `X` | Refund id |
|---|---|---|
| Razorpay | `rzp_X` | `rfnd_<payment_id>` |
| Stripe | `whsec_X` | `re_<payment_id>` |

5. A refund processor **only accepts payment ids from its own gateway.** Razorpay's processor given `ch_stripe_1` is an error.
6. A webhook verifier returns `True`/`False` for a signature — that one is a genuine yes/no question, not an error.

### Requirement 7 — the one that decides your design

**It must be impossible to end up with Stripe's client and Razorpay's verifier.**

The three objects for a gateway are a matched set. Ask for "stripe" once and get all three, consistent. There should be no code path where a caller picks them individually and gets it wrong.

### Requirement 8

A mismatched refund **raises**. It does not return `False`, `None`, or `0`.

On day 4 a gift card's `refund()` returning `False` silently refunded cash-on-delivery and reported success. On day 7 `algorithm in self.algorithms` was always `False` and silently ignored an argument. **Wrong-and-quiet is the failure mode that costs money.** Make this one loud.

### Later we must support (do not build it)

- PayU, Cashfree, and PhonePe.
- A sandbox mode where all three objects are fakes that record calls instead of making them.

### Constraints

- No real HTTP, no `requests`. Standard library only. **No `print()` in business logic.**
- `solution.py` required.

---

## Required before the code

1. **Assumptions.** One line each.
2. **The design you rejected.** One sketch, one sentence on what breaks.
3. **Name both patterns.** One for Part 1, one for Part 2 — and say in one line **what the second one adds that the first can't do.** That sentence is the whole point of pairing them.

Day 7 the word "Strategy" never appeared in your file, and that's five days running. Write the names down.

---

## Required asserts

**Paste all twelve in before you implement. Delete none.** Fresh state per block.

1. Razorpay charge of 50000 paise → fee 1000
2. Stripe charge of 50000 paise → fee 1750
3. Razorpay ids run `pay_rzp_1`, `pay_rzp_2`; Stripe ids run `ch_stripe_1` — **counters are independent**
4. charging 0 and −100 → error, on both gateways
5. asking for `"razorpay"` returns something that charges like Razorpay, **without the calling code naming the class**
6. asking for an unknown gateway name → error
7. Razorpay verifier: `rzp_abc` on payload `abc` → True; `whsec_abc` → False
8. Stripe verifier: `whsec_abc` → True; `rzp_abc` → False
9. Razorpay refund of `pay_rzp_1` → `rfnd_pay_rzp_1`
10. **Razorpay refund of `ch_stripe_1` → raises.** Not `False`, not `None`.
11. **the whole family for `"stripe"` is consistent** — charge with it, verify with it, refund with it, all three from one request, and the refund of the id you just created succeeds
12. adding a third gateway requires no change to any code that charges, verifies, or refunds — demonstrate it in the asserts by defining one

Print `all checks passed` at the end.

---

## Before you say done

**Run the file and look for the printed line.**

Day 7 you wrote `if __name__ == "main":` — missing two underscores — so every assert was skipped, the file exited 0, and it was submitted with empty output. `exit 0` is not "tests passed."

If nothing prints, nothing ran. Paste the terminal output.
