# Day 9 — SQL Query Builder

**Time box: 45 minutes.** Timer on.

---

## The problem

Build a fluent SQL `SELECT` builder. The output is a string, so every assert is exact.

### The parts

| Call | Effect |
|---|---|
| `select("id", "name")` | the columns. If never called, use `*` |
| `from_("users")` | the table. **Required.** |
| `where("age > 18")` | a condition. May be called more than once — conditions join with ` AND ` |
| `join("orders o", "u.id = o.user_id")` | an `INNER JOIN`. May be called more than once |
| `order_by("created_at", "DESC")` | direction defaults to `"ASC"` |
| `limit(10)` | row limit |
| `offset(20)` | row offset |
| `build()` | returns the SQL string |

### Output format — exact

```
SELECT {columns} FROM {table}[ {joins}][ WHERE {conditions}][ ORDER BY {col} {dir}][ LIMIT {n}][ OFFSET {n}]
```

- columns joined with `", "`
- conditions joined with `" AND "`
- each join renders as `INNER JOIN {table} ON {condition}`
- clauses appear in exactly that order, single-spaced, no trailing space

### Rules

1. **Call order must not matter.** `.limit(10).from_("users").select("*")` and `.select("*").from_("users").limit(10)` produce the identical string.
2. `build()` with no table → error.
3. `limit(0)`, `limit(-1)`, `offset(-1)` → error. `offset(0)` is **valid** and renders `OFFSET 0`.
4. `offset` without `limit` → error.
5. **`build()` returns a finished value. Mutating the builder afterwards must not change a string you already built.**

### Worked examples — use these for your asserts

```
SELECT id, name FROM users
SELECT * FROM users WHERE age > 18
SELECT * FROM users WHERE age > 18 AND active = 1
SELECT u.name FROM users u INNER JOIN orders o ON u.id = o.user_id
SELECT * FROM users ORDER BY created_at DESC LIMIT 10
SELECT * FROM users LIMIT 10 OFFSET 20
```

### Later we must support (do not build it)

- `LEFT JOIN` and `CROSS JOIN`, not just inner.
- `GROUP BY` and `HAVING`.
- Parameter binding — `where("age > ?", 18)` — so values never get concatenated into the string.

### Constraints

- Standard library only. **No `print()` in business logic.**
- `solution.py` required.

---

## Required before the code

1. **Assumptions.** One line each.
2. **The design you rejected.** The obvious one is a constructor taking every part. Write down what `Query(cols, table, joins, wheres, order, direction, limit, offset)` looks like at a call site that only needs a table, and one sentence on what breaks.
3. **Name the pattern.** Say what problem it solves that a constructor cannot, and name **one SOLID principle** it touches.

Day 8 you wrote "factory" but not *which* factory. Today: the name, and the one-line reason.

---

## Required asserts

**Paste all fourteen in before you implement. Delete none.** Fresh builder per block.

1. `select("id","name").from_("users")` → `SELECT id, name FROM users`
2. no `select()` call at all → `SELECT * FROM users`
3. one `where` → `SELECT * FROM users WHERE age > 18`
4. two `where` calls → `... WHERE age > 18 AND active = 1`
5. a join → `SELECT u.name FROM users u INNER JOIN orders o ON u.id = o.user_id`
6. two joins → both appear, in call order
7. `order_by("created_at","DESC").limit(10)` → `SELECT * FROM users ORDER BY created_at DESC LIMIT 10`
8. `order_by("name")` with no direction → `ORDER BY name ASC`
9. `limit(10).offset(20)` → `SELECT * FROM users LIMIT 10 OFFSET 20`
10. **`offset(0)` renders `OFFSET 0`** — it is valid, not falsy-skipped
11. **call order independence** — build the same query with the calls in three different orders, assert all three strings are equal
12. `build()` with no table → error
13. `limit(0)`, `limit(-1)`, `offset(-1)` → error; `offset` without `limit` → error
14. **build, then mutate the builder, then assert the first string is unchanged**

Print `all checks passed` at the end.

---

## Two traps worth naming in advance

**Assert 10** is the one this problem exists to catch. `if self._offset:` is falsy for `0`, so a valid `OFFSET 0` silently vanishes. Guard on `is not None`, not on truthiness.

**Assert 14** is the one people fail without noticing. If `build()` hands back something that still points at the builder's internals, a later `.limit(5)` reaches back and changes a query you already produced.

---

## Before you say done

Run it. Look for the printed line. Paste the terminal output.
