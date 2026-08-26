# Builder

Derived from day 9. Every trace is real output from code that was run.

---

## 1. The problem

A fluent SQL `SELECT` builder. Eight parts, one required (`FROM`), seven optional:

```
SELECT {columns} FROM {table} [JOINs] [WHERE ...] [ORDER BY ...] [LIMIT n] [OFFSET n]
```

Three constraints that matter:

- **Call order must not matter.** `.limit(10).from_("users")` and `.from_("users").limit(10)` produce the same string.
- **`offset` requires `limit`.** A cross-field rule.
- **A built query is finished.** Touching the builder afterwards must not change it.

---

## 2. Why the obvious design fails

Put every part in the constructor.

```python
class Query:
    def __init__(self, columns=None, table=None, joins=None, wheres=None,
                 order_col=None, direction=None, limit=None, offset=None):
```

```
ATTEMPT 1 — one constructor taking every part
   a query that is just a table:
     Query(None, 'users', None, None, None, None, None, None)
```

**Eight positional arguments, seven of them `None`.** At the call site you cannot tell which `None` is the limit without counting commas. Add `GROUP BY` and every existing call has to grow a `None`.

This is the **telescoping constructor** problem, and the usual first response is keyword defaults:

```
   now with keywords:
     Query(table='users', limit=10)  -> readable, better
```

Genuinely better. **In many languages that's where you stop** — Python's keyword arguments solve most of what Builder was invented for in Java, and reaching for a Builder when a keyword constructor would do is over-engineering.

So what's left?

### The part keywords don't fix

```
   but the validation problem does not go away:
     Query(table='users', offset=20) -> offset requires limit
   ...which is correct here ONLY because every part arrived at once.
   The moment parts arrive over time, a constructor cannot help:

     q = Query(table='users')      # valid so far
     q.offset = 20                 # now invalid, and nothing checked
     -> object is now in an invalid state, silently. No guard ran.
```

**A constructor has to decide validity at the instant it is called.** That works when everything is known then. It cannot work when the parts arrive one at a time — and the moment you allow assignment afterwards, the cross-field rule has no place to live.

Three more things a constructor can't give you:

- **Order independence** — parameters have positions; a fluent chain doesn't.
- **Repeated parts** — `where()` twice, `join()` twice. A parameter is set once.
- **A finished value** — the constructed object stays mutable unless you freeze it separately.

---

## 3. The pattern

> **Builder** — separate constructing an object from representing it, so the same construction process can produce a complete object in steps, validated once at the end.

The mechanics are three rules:

1. **Every setter records and returns `self`.** The `return self` *is* the fluent interface.
2. **Fields start as `None`** meaning "not set." Nothing is computed until the end.
3. **`build()` validates, then assembles.**

```python
def limit(self, n):
    _require_positive("limit", n)
    self._limit = n
    return self                    # miss this and the next call gets AttributeError on None
```

**Order independence is not implemented — it falls out.** Nothing computes anything until `build()`, so the order in which fields were set cannot matter. If you find yourself writing code to handle ordering, you've computed too early.

### Single vs repeated decides the field type

| Part | Semantics | Field |
|---|---|---|
| select, from_, order_by, limit, offset | last call wins | scalar |
| where, join | accumulate | list |

Getting this backwards is the most common Builder bug: `where` overwriting instead of appending, and nobody notices because one `where` is the common case.

---

## 4. Where validation goes — and it's two places

Not everything belongs in `build()`.

| Rule | Checked where | Why |
|---|---|---|
| `limit` must be > 0 | in `limit()` | wrong on its own, immediately |
| `direction` must be ASC/DESC | in `order_by()` | same |
| a table is required | in `build()` | can't know it's missing until the end |
| `offset` requires `limit` | in `build()` | the limit might still be coming |

**Fail as early as you can, but no earlier.** A rule about one value goes in the setter — the stack trace then points at the bad call. A rule spanning several values can only go in `build()`, and that is precisely why `build()` exists as a separate step.

### Two rules that look the same and aren't

Day 9's actual bug. One shared validator was used for both limit and offset:

```python
def validator(s):
    if s < 0:
        raise ValueError("only greater than zero is accepted")
```

```
limit(0)   -> NO ERROR
so: SELECT * FROM users LIMIT 0
```

Two problems in four lines.

**The message says `> 0`; the code says `>= 0`.** The message is a free assertion of intent, and it disagreed with the implementation from the moment it was written. **When a guard's message and its condition don't describe the same rule, one is wrong — and you can see it by reading, without running anything.**

**And the rules genuinely differ.** `LIMIT 0` returns nothing — nobody means it. `OFFSET 0` means "start at the beginning" — pagination generates it for page 1 constantly. One function cannot express two rules, so sharing it forced them to be the same.

> **DRY applies to duplicated rules, not to code that merely looks similar.** Before extracting a helper, check that both callers want the same *rule*, not just the same *shape*.

---

## 5. `build()` must return a snapshot, not a window

```python
builder = Sql().from_("users").limit(10)
first = builder.build()
builder.limit(99).where("x = 1")
assert first == "SELECT * FROM users LIMIT 10"     # must still hold
```

This passes automatically when `build()` returns a **string**, because strings are immutable.

It does **not** pass automatically if `build()` returns an object holding builder internals:

```python
return Query(self._wheres)     # builder and query now share ONE list
```

`.where("x = 1")` then mutates a query you already handed out. Copy the lists, or freeze the result.

Same aliasing bug as a rental holding a live reference to a vehicle's price — the general rule is: **anything you hand out must be a value, not a view into your state.**

---

## 6. Why the fat class is correct here

Eight fields on one class looks like the SRP violation from the cart problem. It isn't.

**SRP is one reason to change, not few fields.** All eight fields change for exactly one reason: the SQL grammar changed. Compare a `Cart` that also does discounts, tax and receipts — four teams, four reasons.

Ask the diagnostic question: *who files the ticket that edits this class?* For the builder, one answer. For the cart, four.

Say this out loud in an interview, because a good interviewer will poke at the fat class specifically to see whether you can defend it.

---

## 7. Builder vs the patterns next to it

| | |
|---|---|
| **Builder** | assemble one complex object over several steps, validate at the end |
| **Factory Method** | decide *which class* to instantiate. Builder already knows the class; it's assembling the arguments |
| **Abstract Factory** | produce a *family* of related objects. Builder produces one |
| **Fluent interface** | just the `return self` style. Builder often uses it; they aren't the same thing |

A builder can be the product of a factory (`get_query_builder(dialect)`), and they compose cleanly.

### When NOT to use it

- **Three or four parameters with keyword defaults.** In Python that's already readable. Builder earns its keep at "many optional parts **plus** cross-field validation **plus** parts arriving over time." One of the three isn't enough.
- **All parameters required.** Then a constructor is correct — the object is never partially built.
- **No validation.** A frozen dataclass with defaults does the job in one line.

---

## 8. Bug list

- **A missing `return self`** on one setter. The *next* call in the chain fails with `AttributeError: 'NoneType' object has no attribute ...`. Always the method before the one that blew up.
- **`if self._offset:` instead of `if self._offset is not None:`** — `0` is falsy and silently vanishes. Every optional numeric or string field has this trap.
- **`where` overwriting instead of appending.** Invisible until someone calls it twice.
- **A dict keyed by a part of the record** — day 9 used `{table: condition}` for joins, so the same table joined twice kept only the last. A join is a record, not a key-value pair. Use a list.
- **One validator shared by rules that differ.** See section 4.
- **A guard whose message contradicts its condition.** Free to spot, and it means one of the two is wrong.
- **`build()` returning something that aliases builder state.** Copy or freeze.
- **`", ".join([])` producing `""`** — an empty `select()` gives `SELECT  FROM users`, two spaces, invalid SQL. Reject the empty call or default it.
- **Testing an exception with a bare `assert`.** `assert builder.build()` never evaluates if `build()` raises. Use a `raises()` helper.

---

## 9. Saying it in an interview

> "The parts of a query arrive one at a time and in any order, and one rule — offset requires limit — can't be checked until they've all arrived. So the setters just record and return self, and `build()` validates and assembles.
>
> That's **Builder**. A constructor can't do this: it has to decide validity at the moment it's called, and here the object isn't complete until the caller says it is.
>
> I'd note the fat class is deliberate — eight fields, but one reason to change, which is that the SQL grammar changed. And `build()` returns a string rather than a live object, so a query I've handed out can't be altered by touching the builder afterwards.
>
> The limits I'd flag: strings are concatenated so this is injectable — parameter binding is the real fix — and only INNER JOIN is supported, which would make join type a field on the join record."
