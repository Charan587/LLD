# Day 11 — Report Export (Consolidation)

**Time box: 60 minutes.** Longer on purpose.

Three patterns from days 7-10 have to work together. No new ones.

---

## Before you write any code

**Write the docstring first.** Not last.

Day 10 you worked out every cost of the Singleton out loud and none of it reached the file. Day 9, when you wrote it as you designed, it was your best. The fix is mechanical: assumptions, rejected design and pattern names go in **before** the first `class` line, while that reasoning is the thing you're actually doing.

---

## The problem

A loan platform exports collection reports.

### The data

```python
ROWS = [
    {"id": 1, "name": "Asha",  "amount": 5000,  "status": "PAID"},
    {"id": 2, "name": "Ben",   "amount": 12000, "status": "DUE"},
    {"id": 3, "name": "Chen",  "amount": 300,   "status": "PAID"},
    {"id": 4, "name": "Dev",   "amount": 1000,  "status": "DUE"},
]
```

### Building a report

A report is assembled from parts, in any order:

| Call | Effect |
|---|---|
| `title("Collections")` | report title |
| `columns("id", "name", "amount")` | which columns appear, in this order |
| `rows(ROWS)` | the data |
| `min_amount(1000)` | keep rows where `amount >= 1000` |
| `status("DUE")` | keep rows with this status |
| `sort_by("amount", descending=True)` | sort order |
| `format("csv")` | how to render |
| `build()` | produces a finished report |

Rules:

1. `columns` and `rows` are **required**; `build()` without either is an error.
2. Filters combine: both `min_amount` and `status` means rows must satisfy both.
3. Filtering happens **before** sorting.
4. **`min_amount(1000)` keeps a row whose amount is exactly 1000.**
5. `sort_by` on a column that isn't in `columns` → error.
6. Building twice from the same builder must produce independent results.

### Rendering

Three formats. `render(report)` returns a string.

**`csv`**
```
id,name,amount
2,Ben,12000
1,Asha,5000
4,Dev,1000
```

**`json`** — a JSON array of objects, keys in column order, via `json.dumps`.

**`table`**
```
| id | name | amount |
| --- | --- | --- |
| 2 | Ben | 12000 |
| 1 | Asha | 5000 |
| 4 | Dev | 1000 |
```

7. `format("xml")` → error, naming the formats that do exist.
8. **A renderer must not filter or sort.** Hand a renderer the rows directly and it renders exactly those, in exactly that order. Filtering and sorting belong to the build step.

### Delivery

9. `ReportService(renderer_factory, mailer).send(report, "ops@bank.com")` renders the report and hands the text to the mailer.
10. **A test must assert what the mailer received**, without sending anything and without editing `ReportService`.

### Later we must support (do not build it)

- PDF and XLSX renderers, added by another team who may not edit the report or the service.
- A `max_amount` filter, and a `branch` filter.
- Delivery to Slack instead of email.

---

## Required before the code

1. **Assumptions.**
2. **The design you rejected.**
3. **Name every pattern you used and say what each one is doing here.** There is more than one. For each, one line: what varies, and what stays the same.

---

## Required asserts

**Paste all fifteen in first. Delete none, comment out none.**

Use a typed `raises` — `except ValueError`, not bare `except`. Day 10's bare `except:` would have returned `True` for a typo.

1. builder with columns + rows, no filters, csv → all four rows, in original order
2. `min_amount(1000)` → three rows; Chen (300) is gone
3. **`min_amount(1000)` keeps Dev, whose amount is exactly 1000** *(the boundary)*
4. `status("DUE")` → Ben and Dev only
5. both filters together → Ben and Dev
6. `sort_by("amount", descending=True)` with `min_amount(1000)` → the exact CSV block above
7. the same report rendered as `json` → parses back to the right list of dicts
8. the same report rendered as `table` → the exact table block above
9. `format("xml")` → error, and the message names csv, json and table
10. `build()` with no columns → error; with no rows → error
11. `sort_by("balance")` when `balance` isn't a column → error
12. **hand a renderer three rows in a deliberately wrong order — it renders them in that order**, proving it doesn't sort
13. build twice from one builder, mutate between, first result unchanged
14. **`ReportService` with a fake mailer — assert the text the mailer received**, not that the renderer works
15. add a fourth format in the assert block and render with it, without editing the factory's existing entries

Print `all checks passed` at the end.

---

## Two things to watch

**Assert 12** is requirement 8 made testable. If your renderer sorts "to be helpful", it fails — and that helpfulness is what makes the next four renderers each reimplement sorting slightly differently.

**Assert 14** is day 10's mistake in a new costume. There the assert reached past `OrderService` and called the pool directly. Here, assert on what the **mailer received** — the service is the thing under test.

---

## Before you say done

Run it, look for the printed line, paste the output.
