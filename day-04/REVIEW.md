# Day 4 Review — Payment Methods (Python)

Reviewed 2026-08-01. Submission preserved as `solution.submitted.py`.

## Read this first: you lost work

Edit history shows the file at **16:00:10** (`vbnY.py`) contained the assumptions block, the rejected design, **both principles named correctly**, `ABC`/`@abstractmethod`, `if amount <= 0: raise ValueError` in five places, and `cancel_autodebit`. At **16:00:58** it was reverted to an earlier state — that's the file you submitted.

The scores below grade what you submitted, because that's the rule and because it's what an interviewer sees. But the record should say: **you did the work.** After four days of the principle-naming item being open, you named ISP and LSP correctly and unprompted. That counts.

Recovery:
```bash
cp "/Users/charant/Library/Application Support/Code/User/History/-50d9d3e0/vbnY.py" \
   ~/Documents/Backend/LLD/day-04/solution_recovered.py
```
Had that file been submitted, this would have scored roughly **19/25**, not 15.

## Verdict

```
$ python3 solution.py
Refund failed for UPI: Refund amount exceeds the amount used.
All tests passed successfully!
exit: 0
```

**It runs, and you showed me the output.** W10 closed on the first attempt.

**And the day's actual lesson landed completely.** Three capability interfaces, each class implementing exactly the ones it can honour, `GiftCard` with no `refund` method at all, and `refund_all` filtering by `isinstance`. That's the correct answer to LSP + ISP, and you got there after being stuck on it mid-session. `refund_all` returns **800** on the mixed list — genuinely correct, and requirement 5 never explodes.

## Score

| Axis | D1 | D2 | D3 | D4 | Why |
|---|---|---|---|---|---|
| Correctness | 1 | 3 | 1 | **2** / 5 | Runs, but refunds are unlimited, negative payments add money, the 2% fee only applies above ₹1000, no cancel |
| Extensibility | 1 | 4 | 2 | **4** / 5 | New wallet = new class ticking columns. Nothing existing changes. |
| SOLID | 1 | 3 | 3 | **4** / 5 | Capability split is right. `fee()` is an undeclared implicit contract; `refund_all` type hint is wrong |
| Readability | 2 | 2 | 2 | **3** / 5 | `fee()` returns the total, not the fee; duplicated validation; `autodebit` annotated `-> float`, returns None |
| Communication | 1 | 2 | 1 | **2** / 5 | Assumptions present. Rejected design and principles were written, then lost. |

**15 / 25.** Best so far.

---

## The money bugs

### 1. Refunds are unlimited

`refund` adds to `balance` but never decrements `amount_used`:

```
paid 1000, amount_used = 1000
  refund(1000) #1 -> 1000   amount_used still 1000   balance 99980.0
  refund(1000) #2 -> 1000   amount_used still 1000   balance 100980.0
  refund(1000) #3 -> 1000   amount_used still 1000   balance 101980.0
  refund(1000) #4 -> 1000   amount_used still 1000   balance 102980.0
```

₹4000 refunded on a ₹1000 payment, and it keeps going. Rule 3 says *"you cannot refund more than was paid on that method"* — the check exists, but the thing it checks against never moves.

`amount_used` is the wrong name for the job. It means "total ever paid," which is a *historical* fact and shouldn't shrink. What `refund` needs is **"how much is still refundable"** — a *current* balance that decreases as you refund. One field trying to be both is why the decrement looks wrong to write.

Rename it and the correct code becomes obvious:

```python
self.refundable -= amount        # the line that was missing
self.balance += amount
```

Same shape as day 2's `baseHealth` doing double duty as max and current health. **When a field can't decide whether it's history or state, split it.**

### 2. Paying a negative amount adds money

```
UPI balance before      : 500
u.pay(-100) returns     : -100
UPI balance after       : 600  <-- paying negative ADDED money
```

Rule 1 of the spec: *"Paying zero or a negative amount is an error."* No method checks it. `balance -= -100` is `balance += 100`, so a customer paying ₹-100 gets ₹100.

This is **W5, fourth appearance** — and it's the one that was in the lost version. You wrote the guard; it didn't survive.

Note *where* it belongs. You'd need the same three lines in eight places (four `pay`, four `refund`). That duplication is the signal to hoist it:

```python
def _check_amount(amount: float) -> None:
    if amount <= 0:
        raise ValueError(f"amount must be positive, got {amount}")
```

One function, called at every entry point. Rule 1 now lives in exactly one place, and the wallet you add next month gets it for free.

### 3. The 2% fee only applies above ₹1000

```python
return amount * self.fee_percentage + amount if amount >= self.max_amount else amount
```

```
fee(1000) -> 1020.0   (spec 1020)      ✓
fee(999)  -> 999      (spec 1018.98)   ✗ no fee at all
fee(500)  -> 500      (spec 510)       ✗
```

`max_amount=1000` is invented — it's not in my spec. My table says *"Credit Card: 2%"*, unconditionally. Your one assert used exactly ₹1000, the single value where the bug is invisible.

Also worth seeing the precedence, because it isn't what it looks like:

```python
amount * pct + amount if amount >= max else amount
# parses as:
(amount * pct + amount) if (amount >= max) else amount
```

The conditional swallows the whole arithmetic expression. Parenthesise anything mixing a ternary with arithmetic, or use an `if` statement.

### 4. `cancel` doesn't exist

Rule 4: *"...and can be cancelled."* `autodebit` sets `self.autodebit_day` and there's no way to unset it. Also annotated `-> float` while returning `None`. This too was in the lost version.

## `fee()` returns the total, not the fee

```python
def fee(self, amount: float) -> float:
    return amount + self.flat_fee      # this is the total charged
```

A method called `fee` returning ₹1050 when the fee is ₹50. **This is day 3's bug wearing a new hat** — `apply_discount` returned the new total instead of the amount off, and here `fee` returns the new total instead of the fee.

The tell is the same both times: the caller can't use the number for what its name promises. If a receipt wants to print `Fee: ₹50`, it has to compute `fee(amount) - amount` — the caller undoing the callee again.

`fee()` also raises when `amount > balance`. That's a *validation* concern living inside a *calculation*. Two consequences: you can't ask "what would this cost?" without risking an exception, and the check is duplicated in `pay` right after.

## `refund_all` swallows failures

```python
except ValueError as e:
    print(f"Refund failed for {payment.__class__.__name__}: {e}")
```

Your own run printed `Refund failed for UPI` — an over-refund silently became ₹0 and the function reported success. In a payments system, "a refund quietly didn't happen" is the failure mode you least want to be silent.

Two smaller things: business logic shouldn't `print` (there's no way for a caller to react to a printed string), and the try/except is doing work the `isinstance` filter already did — with capability filtering in place, the only exceptions left are *real* errors you want to see.

`refund_all` is also annotated `list[Refundable]` while you pass `[card, upi, gift_card, cod]`. If it truly took `Refundable`s, no filter would be needed. It takes `Payable`s.

## The asserts

Real progress — every assert checks a **value**, not `== True`. W1b is closing.

But roughly half the required list is missing, and the missing half is exactly the part that protects money:

| Required | Present? |
|---|---|
| fees 1020 / 1000 / 1000 / 1050 | ✓ |
| gift card 5000 → pays 1000 → balance 4000 | ✗ (used 200/200, so the walk is invisible) |
| gift card 500 paying 1000 → error, balance unchanged | ✗ |
| paying 0 or −100 → error, every method | ✗ ← would have caught bug 2 |
| card refunds 400 of 1000 → 400 back | ✗ ← would have caught bug 1 |
| refunding more than paid → error | ✗ |
| `refund_all` returns what it refunded | ✗ asserted only that it *didn't raise* |
| recurring setup, then cancel | ✗ ← would have caught bug 4 |

Three of the four bugs above have an assert on that list that finds them immediately.

And this one:

```python
assert raises(refund_all, payments, 100) is None
```

That says *"it didn't crash."* It's the day-2 pattern in a new costume — a no-exception assert instead of a `== True` one. `refund_all` actually returns **800**, which is correct, and nothing you wrote checks it. You had the right answer and didn't record it.

**Pattern across four days: you assert what you built, not what the spec demanded.** Today the spec's list was a checklist — the fix is to paste all eight lines in first and delete none.

## The rewrite

`rewrite.py`, verified `all checks passed`. **Your capability split is kept exactly as you had it** — that part was right. What changed: `_check_amount` hoisted to one function, `refundable` as its own decrementing field, `fee()` returning the fee, `cancel()` added, and `refund_all` as a one-line `sum(...)` with no try/except.

Note the asserts that prove capability is visible without calling anything:

```python
assert [type(m).__name__ for m in methods if isinstance(m, Refundable)] == ["CreditCard", "UPI"]
assert not hasattr(GiftCard(1), "refund")
```

That second line is the whole point of the day, in one assert.

## On taking over an hour

> I took more than an hour... initially I took almost 15 minutes to write assert and understand, and when writing code for credit card I was getting idea about amount used and balance

Fifteen minutes on asserts before coding is **correct**, not slow. That's the plan working — day 3 you wrote them at minute 27 and the file didn't run; today you wrote them first and it ran. Don't optimise that away.

The hour went elsewhere: the design was still unsettled when you started typing. History shows 15:21 (a docstring and a stub `main`) then **nothing until 15:53** — 32 minutes where the capability question was being resolved. Once it was, the whole file appeared at once and the remaining 9 minutes were tight iteration.

That's the right diagnosis and the right fix: the time went into *deciding*, not typing. As the tabulate-by-column move becomes reflex, that 32 minutes compresses. Speed comes last — correctness first, then discipline, then speed. You're on step two.

One process note: your discovery that `amount_used` and `balance` were separate ideas came *while implementing*, which is normal and fine. But it half-landed — you created both fields and then only maintained one. When a distinction surfaces mid-build, **go back and write the assert for it immediately** (`refund twice → second one fails`). That converts an insight into a check while you still have it.

## Grill

1. `amount_used` and `refundable` — I said one is history and one is state. **Give me a business requirement that needs both**, kept separately.
okay if we want to know spend history we can use amount used there and refundable for same cause we have to refund them so . 
2. My `_check_amount` is a module-level function, not a method. **Why does that matter** for the wallet class you add next month?
check amount will also be used by all methods and can be kept in commons file and alsoi if refund all want to check amount it doesnt need to imolement any class to check so 
3. `GiftCard` in my rewrite inherits from `_Account`, which has `_refund`. So a gift card *can* refund internally — but `isinstance(gift, Refundable)` is False. **Is that a violation of anything?** Argue both sides.
yes its violation of lsp may be _Account means protocol not immeditae class so they must implement this . but yeah it can happen can you explain. me about this
4. You caught errors in `refund_all` and printed them. **Name one situation where catching is right there**, and say what you'd return instead of printing.
to get the logs we can print them . when i return is when there is fata code error 
5. `fee()` isn't declared in `Payable`, but `pay()` in every class calls `self.fee()`. **What breaks** when someone writes a new payment method and forgets `fee`? Which principle covers this?
isp priciple here . when some one implements payable and lets say we are calling self.fee in every class that is fine unless they will already overrude that and define themself. 
6. Requirement: wallets can be topped up, and nothing else can. **How many files change** in my rewrite, and which ones?

write a topup protocol extends topup account and implement your topup in wallet class .