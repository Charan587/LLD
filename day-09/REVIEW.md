# Day 9 Review — SQL Query Builder (Python)

Reviewed 2026-08-25. Submission preserved as `solution.submitted.py`.

## Verdict

```
$ python3 solution.py
all checks passed
exit: 0
```

**Best day of the nine, and not marginally.** 18/25 against a previous best of 16.

Four things landed that have been open for a long time:

**The `offset(0)` trap — avoided.** `if self._offset is not None` rather than `if self._offset`. Assert 10 passes and renders `OFFSET 0`. Eight days of boundary misses, and this one you got.

**The pattern is named, correctly, in the file.** *"patterns used is builder pattern, single responsibility."* First time you've named the right pattern without hedging.

**Validation hoisted to a module-level function.** `validator(s)` called from `limit` and `offset` rather than duplicated. That's day 4's `_check_amount` lesson applied unprompted, six days later.

**The rejected design is genuinely thoughtful** — `*args` for where, a join-type parameter, direction inferred from the last arg. That's the first time this section reads like someone actually considered alternatives rather than describing what they built.

**11 of 14 asserts**, your best ratio.

## Score

| Axis | D5 | D6 | D7 | D8 | D9 | Why |
|---|---|---|---|---|---|---|
| Correctness | 2 | 2 | 1 | 2 | **3** / 5 | `limit(0)` accepted; same-table joins collapse; `select()` with no args emits a double space |
| Extensibility | 4 | 4 | 3 | 3 | **4** / 5 | One block per clause; GROUP BY is a field plus a block. Joins-as-dict blocks LEFT JOIN. |
| SOLID | 4 | 4 | 3 | 3 | **4** / 5 | Builder correct; validation hoisted; the fat class is the right call and you justified it |
| Readability | 3 | 2 | 2 | 2 | **3** / 5 | `validator`'s message contradicts its code; `cols` vs `_table`; `_order_by` dict keyed `'col'`/`'d'` |
| Communication | 3 | 3 | 1 | 3 | **4** / 5 | All three items, pattern correctly named, rejected design substantive |

**18 / 25.** Trend: 6 → 14 → 9 → 15 → 16 → 15 → 10 → 13 → **18**.

---

## The bug, and it's a good one

```python
def validator(s: int):
    if s < 0:
        raise ValueError("only greater than zero is accepted")
```

```
limit(0)   -> NO ERROR
limit(-1)  -> raises: only greater than zero is accepted
offset(-1) -> raises: only greater than zero is accepted

your validator message says:  only greater than zero is accepted
but validator(0) -> NO ERROR  <-- zero IS accepted

so: SELECT * FROM users LIMIT 0
```

**The error message states the correct rule. The code implements a different one.** `"only greater than zero"` is `> 0`; `if s < 0` is `>= 0`. You wrote down what you meant and then coded something else two lines later.

That's worth more attention than an ordinary off-by-one, because **the message is a free assertion of intent** and it disagreed with the implementation the whole time. When a guard's message and its condition don't say the same thing, one of them is wrong — and you can spot that by reading, without any test.

### The deeper cause: one validator, two different rules

Spec rule 3: `limit(0)` is an **error**. `offset(0)` is **valid**.

They're genuinely different questions. `LIMIT 0` returns no rows — a query nobody means to write. `OFFSET 0` means "start at the beginning" — completely ordinary, and pagination code generates it constantly for page 1.

One shared `validator` cannot express two different rules, so sharing it forced them to be the same. Two functions, two names, two messages:

```python
def _require_positive(name, value):       # limit
    if value <= 0: raise ValueError(f"{name} must be greater than zero, got {value}")

def _require_non_negative(name, value):   # offset
    if value < 0: raise ValueError(f"{name} must not be negative, got {value}")
```

**Hoisting validation was right. Hoisting it into one function was one step too far.** DRY applies to duplicated *rules*, not to code that merely looks similar.

This is `>` vs `>=` for the eighth day running — but it arrived a new way. Days 1-6 it was a comparison you wrote by hand. Day 9 it's a comparison you *reused* where it didn't apply.

## Joins as a dict

```python
self._joins: dict[str, str] = {}
self._joins[table] = condition
```

```
SELECT * FROM users u INNER JOIN orders o ON u.id = o.a  <-- second join vanished
```

The table is the key, so joining the same table twice silently keeps only the last one. Two real cases break:

- **Self-joins.** `users u JOIN users m ON u.mgr_id = m.id` — employees and their managers. Yours survives this only because the aliases differ (`users m` vs `users d` are different strings).
- **The same table on two conditions**, which is where it actually dies.

A join isn't a key-value pair. It's a **record** with a table, a condition, and — once LEFT JOIN arrives — a kind. A list of them preserves order, allows duplicates, and has somewhere to put the join type:

```python
@dataclass(frozen=True)
class Join:
    table: str
    condition: str
    kind: str = "INNER"
```

Note the dict *did* preserve order (Python 3.7+ keeps insertion order), so assert 6 passed. Order was never the problem — uniqueness was.

## The commented-out assert

```python
# assert Sql().select("id","name").build()
```

That's assert 12, and it's disabled. It would have failed — not because your code is wrong (`build()` correctly raises "no table"), but because **`assert` can't test for an exception.** The call raises before `assert` ever evaluates.

```python
assert raises(Sql().select("id").build)
```

You already know this — you wrote a `raises()` helper on days 4, 6 and 8. Here you hit the wall and commented the line out instead.

**W11, second sighting.** Day 3's edit history showed you writing three asserts and deleting two when they failed. A failing or awkward assert is the highest-value line in the file at that moment. Comment it out and you keep the passing run and lose the information.

Same for assert 13 — none of `limit(0)`, `limit(-1)`, `offset(-1)`, or offset-without-limit are tested. **`limit(0)` is exactly the bug above**, and the assert that finds it is one line.

## Assert 14 passes — by luck, not by design

```
first  : SELECT * FROM users LIMIT 10
second : SELECT * FROM users WHERE x = 1 LIMIT 99
```

Correct behaviour, and you never tested it. It works because `build()` returns a **string**, and Python strings are immutable — there's no way for the builder to reach into one it already handed out.

Worth knowing *why* it's safe, because it isn't always. Had `build()` returned a `Query` object holding `self._wheres`, the builder and the query would share one list, and `.where("x = 1")` would have mutated a query you'd already produced. Same aliasing bug as day 6's `Rental`.

**The rule: a builder must hand back a snapshot, not a window.** Strings give you that free; objects don't.

## Smaller things

- **`select()` with no arguments** produces `'SELECT  FROM users'` — two spaces, invalid SQL. `", ".join([])` is `""`. Either default to `*` or reject the call; silently emitting broken SQL is the worst option.
- **`cols` is public, everything else is `_`-prefixed.** Pick one.
- **`_order_by` as `{'col': ..., 'd': ...}`** — a dict with two fixed keys is a tuple with worse ergonomics and no type checking. `'d'` also isn't a word.
- **You implemented the thing you called a rejected design.** The docstring says *"rejected design - we can add multiple where in a single where by using \*args"* — and `where(self, *args)` does exactly that. If you changed your mind, that's fine; the file should say the same thing twice.
- **`order_by` accepts any direction string.** `order_by("name", "SIDEWAYS")` renders happily.
- **The offset/limit cross-check sits between two appends in `build()`.** It works, but validation reads better as a block at the top — the reader learns the preconditions before the assembly.

## The rewrite

`rewrite.py`, `all checks passed`. Your structure kept entirely — setters record and return `self`, `build()` validates then assembles. Changed: two validators instead of one, `Join` as a record in a list, `_order_by` as a tuple, direction checked, `select()` with no columns rejected, and all fourteen asserts including the self-join case and the build-then-mutate check.

Also carries the interview walkthrough block, including the bit worth rehearsing: **why the fat class is correct here** and how to say that when an interviewer pokes at it.

## Grill

1. I said the fat builder is fine because SRP is "one reason to change." **Name the change that would split it** into more than one class.
lets say we want postgres sql or sqlite query at that time it can split and bceaome ocp
2. `build()` can be called twice on the same builder. **Argue that's wrong** — some builders forbid it. What breaks if you allow it, and what breaks if you don't?
if i allow it first build gives string and not self. so it breakes there
3. Parameter binding arrives: `where("age > ?", 18)`. **What new field appears**, and what does `build()` return that it doesn't now?
I am not sure how we can map like which charcter resembers exacly what needs to be replaces. if yes we will store in list like tuple and replce 
4. I made `Join` a frozen dataclass rather than a tuple. **Name one thing that buys** beyond readability.
we can easily change to left join left inner and any type of join . and while build we can add kind while we are joining
5. Your `validator` was shared by two callers with different rules. **State the general test** for when two call sites can share a helper.
when they have similar functionality to do that time we can create a helper 
6. A caller does `q = Sql().from_("users")` then passes `q` to two functions that each add a `where`. **What goes wrong**, and which pattern from day 1-8 does the fix resemble?
so this one after adding two where now two where included will get printed . dip principle?
