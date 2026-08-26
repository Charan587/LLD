"""Day 9 — SQL Query Builder. Interview-grade rewrite.

═══════════════════════════════════════════════════════════════════════════
INTERVIEW WALKTHROUGH — what you say out loud, in order
═══════════════════════════════════════════════════════════════════════════

1. READ-BACK (~20s)
   "A fluent SELECT builder. Eight optional parts, one required table, and
    the output is an exact string. The two constraints I'm designing around
    are that call order mustn't matter, and that a built query can't be
    changed afterwards by touching the builder."

2. CLARIFYING QUESTIONS
   - "Is limit(0) a valid query that returns nothing, or an error?"
     -> and separately, is offset(0) valid? They are NOT the same question
   - "Can the same table be joined twice — self-joins, or two aliases?"
   - "Should the builder be reusable after build(), or one-shot?"

3. HOW I FOUND THE CLASSES
   Nouns: query, column, table, join, condition, order, limit, offset.

   Almost none of them become classes. That's the point of this problem.
   Everything is a field on ONE builder, because the parts are meaningless
   alone — a WHERE with no query is not a thing.

     builder -> accumulates parts, hands back self       -> Sql
     query   -> the finished string                      -> str

   A "fat class" here is CORRECT, and worth saying out loud because it
   looks like the SRP violation from day 3. It isn't: SRP is one reason to
   change, not few fields. All eight fields change for exactly one reason —
   the SQL grammar changed. Day 3's Cart had four teams filing tickets.

   Which parts are single vs repeated decides the field type:
     select, from_, order_by, limit, offset -> last call wins    -> scalar
     where, join                            -> accumulate        -> list

4. ASSUMPTIONS
   - Single-threaded; one builder is not shared across threads.
   - Columns and conditions are trusted strings; no escaping, no binding.
   - Later call of a scalar setter overwrites the earlier one.
   - Builder is reusable after build(); build() takes a snapshot.

5. THE DESIGN I REJECTED
   "A constructor taking every part:
      Query(None, 'users', None, None, None, None, None, None)
    Eight positional arguments where seven are None, no way to tell at the
    call site which None is the limit, and adding GROUP BY changes every
    existing call. Keyword defaults help the readability but not the
    validation — the object would have to be valid at construction, and
    'offset requires limit' is a rule you can only check once everything
    has arrived."

6. THE DESIGN + PATTERN NAME
   "BUILDER. It separates constructing an object from representing it, so
    the parts arrive one at a time, in any order, and validation happens
    once at the end when the thing is finally complete. A constructor can't
    do that — it has to decide validity at the instant it's called."
   "It gives me OPEN/CLOSED for the grammar: GROUP BY is one field plus one
    block in build(), and no existing call site changes."

7. LIMITS I'D VOLUNTEER
   - "Strings are concatenated, so this is SQL-injectable. Parameter binding
      is the real fix — where('age > ?', 18) collecting params alongside."
   - "Only INNER JOIN. LEFT/CROSS means the join type becomes a field on
      the join record rather than hardcoded in build()."
   - "No validation that a column exists — that needs a schema, which is a
      different layer."

═══════════════════════════════════════════════════════════════════════════
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Join:
    """A record, so two joins on the same table can coexist."""
    table: str
    condition: str
    kind: str = "INNER"


def _require_positive(name: str, value: int) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero, got {value}")


def _require_non_negative(name: str, value: int) -> None:
    if value < 0:
        raise ValueError(f"{name} must not be negative, got {value}")


class Sql:
    def __init__(self):
        self._columns: list[str] = []
        self._table: str | None = None
        self._joins: list[Join] = []
        self._wheres: list[str] = []
        self._order_by: tuple[str, str] | None = None
        self._limit: int | None = None
        self._offset: int | None = None

    # ── each setter: record, return self ──────────────────────────────────

    def select(self, *columns: str) -> "Sql":
        if not columns:
            raise ValueError("select() needs at least one column")
        self._columns = list(columns)
        return self

    def from_(self, table: str) -> "Sql":
        self._table = table
        return self

    def where(self, condition: str) -> "Sql":
        self._wheres.append(condition)
        return self

    def join(self, table: str, condition: str) -> "Sql":
        self._joins.append(Join(table, condition))
        return self

    def order_by(self, column: str, direction: str = "ASC") -> "Sql":
        if direction not in ("ASC", "DESC"):
            raise ValueError(f"direction must be ASC or DESC, got {direction!r}")
        self._order_by = (column, direction)
        return self

    def limit(self, n: int) -> "Sql":
        _require_positive("limit", n)          # 0 rows is not a query worth running
        self._limit = n
        return self

    def offset(self, n: int) -> "Sql":
        _require_non_negative("offset", n)     # 0 IS valid — different rule
        self._offset = n
        return self

    # ── build: validate what only now can be known, then assemble ─────────

    def build(self) -> str:
        if self._table is None:
            raise ValueError("no table: call from_() before build()")
        if self._offset is not None and self._limit is None:
            raise ValueError("offset requires limit")     # cross-field: only knowable here

        columns = ", ".join(self._columns) if self._columns else "*"
        parts = [f"SELECT {columns} FROM {self._table}"]

        parts += [f"{j.kind} JOIN {j.table} ON {j.condition}" for j in self._joins]
        if self._wheres:
            parts.append("WHERE " + " AND ".join(self._wheres))
        if self._order_by is not None:
            column, direction = self._order_by
            parts.append(f"ORDER BY {column} {direction}")
        if self._limit is not None:
            parts.append(f"LIMIT {self._limit}")
        if self._offset is not None:           # is not None — 0 must survive
            parts.append(f"OFFSET {self._offset}")

        return " ".join(parts)


def raises(fn, *args) -> bool:
    try:
        fn(*args)
    except ValueError:
        return True
    return False


if __name__ == "__main__":
    # 1, 2 — columns
    assert Sql().select("id", "name").from_("users").build() == "SELECT id, name FROM users"
    assert Sql().from_("users").build() == "SELECT * FROM users"

    # 3, 4 — conditions accumulate
    assert (Sql().from_("users").where("age > 18").build()
            == "SELECT * FROM users WHERE age > 18")
    assert (Sql().from_("users").where("age > 18").where("active = 1").build()
            == "SELECT * FROM users WHERE age > 18 AND active = 1")

    # 5, 6 — joins, in call order
    assert (Sql().select("u.name").from_("users u")
            .join("orders o", "u.id = o.user_id").build()
            == "SELECT u.name FROM users u INNER JOIN orders o ON u.id = o.user_id")
    assert (Sql().from_("users u")
            .join("orders o", "u.id = o.user_id")
            .join("payments p", "u.id = p.user_id").build()
            == "SELECT * FROM users u INNER JOIN orders o ON u.id = o.user_id "
               "INNER JOIN payments p ON u.id = p.user_id")

    # the same table twice — a self-join must not collapse
    assert (Sql().from_("users u")
            .join("users m", "u.mgr_id = m.id")
            .join("users d", "u.dept_lead = d.id").build().count("INNER JOIN") == 2)
    assert (Sql().from_("orders o")
            .join("items i", "o.id = i.a")
            .join("items i", "o.id = i.b").build().count("INNER JOIN") == 2)

    # 7, 8 — ordering
    assert (Sql().from_("users").order_by("created_at", "DESC").limit(10).build()
            == "SELECT * FROM users ORDER BY created_at DESC LIMIT 10")
    assert (Sql().from_("users").order_by("name").build()
            == "SELECT * FROM users ORDER BY name ASC")

    # 9, 10 — offset(0) is valid and must render
    assert (Sql().from_("users").limit(10).offset(20).build()
            == "SELECT * FROM users LIMIT 10 OFFSET 20")
    assert (Sql().from_("users").limit(10).offset(0).build()
            == "SELECT * FROM users LIMIT 10 OFFSET 0")

    # 11 — call order does not matter
    canonical = ("SELECT id FROM users WHERE active = 1 "
                 "ORDER BY name ASC LIMIT 10 OFFSET 5")
    a = Sql().select("id").from_("users").where("active = 1").order_by("name").limit(10).offset(5)
    b = Sql().limit(10).offset(5).order_by("name").where("active = 1").from_("users").select("id")
    c = Sql().where("active = 1").order_by("name").select("id").offset(5).limit(10).from_("users")
    assert a.build() == b.build() == c.build() == canonical

    # 12 — no table
    assert raises(Sql().select("id").build)

    # 13 — every invalid value, and the cross-field rule
    assert raises(Sql().limit, 0)
    assert raises(Sql().limit, -1)
    assert raises(Sql().offset, -1)
    assert raises(Sql().from_("users").offset(5).build)     # offset without limit
    assert raises(Sql().select)                             # no columns
    assert raises(Sql().order_by, "name", "SIDEWAYS")

    # 14 — a built query is a finished value
    builder = Sql().from_("users").limit(10)
    first = builder.build()
    builder.limit(99).where("x = 1").select("id")
    assert first == "SELECT * FROM users LIMIT 10"
    assert builder.build() == "SELECT id FROM users WHERE x = 1 LIMIT 99"

    # adding a clause to the grammar: one field, one block, no call site changes
    assert (Sql().select("dept", "COUNT(*)").from_("users")
            .where("active = 1").order_by("dept").limit(5).build()
            == "SELECT dept, COUNT(*) FROM users WHERE active = 1 "
               "ORDER BY dept ASC LIMIT 5")

    print("all checks passed")
