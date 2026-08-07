# Day 2 — Combat System

**Time box: 45 minutes.** Timer on.

Read `../notes/how-to-approach-lld.md` first if you haven't. Use it on this problem — nouns, verbs, boundaries, the "later" clause.

---

## The problem

Build the combat core of a game.

A **character** has a name, base health, and base attack power. A character carries a **weapon** and wears **armor**.

### Starting content

| Weapon | Attack bonus |
|---|---|
| Fists | 0 |
| Sword | 10 |
| Bow | 7 |
| Staff | 5 |

| Armor | Defense |
|---|---|
| None | 0 |
| Leather | 5 |
| Plate | 15 |

| Character | Base health | Base attack |
|---|---|---|
| Warrior | 120 | 12 |
| Mage | 70 | 20 |
| Archer | 90 | 15 |

### Rules

1. **Damage dealt** = character's base attack + weapon's attack bonus.
2. **Damage taken** = incoming damage − defender's armor defense, floored at 0. Never negative, never heals.
3. A character with health 0 or less is **dead**. A dead character cannot attack and cannot be attacked.
4. `attack(other)` reduces the other character's health by the damage taken.

### Must support

5. **Swapping a weapon at runtime.** A Warrior who picks up a Bow mid-fight uses the Bow's bonus from that moment on. Same character, same health, same everything — different weapon.
6. **Swapping armor at runtime**, same way.
7. A character starts with Fists and no armor if you don't give them any.

### Later we must support (do not build it, but your design must not block it)

- Roughly 40 more weapons and 20 more armors, added by a designer who is **not allowed to edit any character class**.
- Weapons with effects beyond a flat bonus — a Staff that costs mana, a dagger that does double damage from behind.
- A shield, worn *in addition* to armor.

### Constraints

- In-memory, single-threaded, standard library only.
- No randomness. Damage must be deterministic so your asserts can check exact numbers.
- `solution.py` required. `Solution.java` strongly encouraged today — see below.

---

## Required: three things in your file, before the code

**1. Assumptions block.** What did the problem leave unspecified? Decide, and write it down.

**2. The design you rejected.** In a comment, sketch the class list for the *first* design that came to mind. If it was `class Warrior`, `class SwordWarrior`, `class ArcherWithPlate` — write that down and then write one sentence on what breaks. I want the rejected design on the page, not just the final one. This is worth points.

**3. Name the principle.** One sentence naming the design principle your solution follows, and one naming the principle the rejected design violated. Use the actual names. Getting the name wrong is the thing we're drilling today — you described Open/Closed perfectly yesterday and called it SRP.

---

## Required: asserts

Non-negotiable from today. An empty `__main__` scores 0 on Correctness regardless of how good the code is. Yesterday's three bugs were all catchable by the asserts you didn't write.

**Write these before you implement.** Minimum coverage:

- Warrior with Sword deals 22; Mage with Staff deals 25
- Warrior with Sword (22) hitting Mage in Leather (5) leaves the Mage at 70 − 17 = 53
- Plate armor (15) vs a 12-damage hit leaves the defender at full health minus 0 — **not** healed by 3
- **Swap:** Warrior deals 22 with Sword; give the same Warrior a Bow, now deals 19; health unchanged by the swap
- A character taking lethal damage ends at 0 or less and reports dead
- A dead character cannot attack, and cannot be attacked
- A character created with no weapon and no armor deals base attack and takes full damage

Print `all checks passed` at the end.

---

## Why Java matters today

The topic is **composition vs inheritance, and interfaces vs abstract classes.** Python blurs the second one — duck typing means you can skip the abstraction entirely and it still runs. Java won't let you. Writing this twice will show you what the Python version let you get away with.

If you only have time for one, do Python. But if you do both, the interesting question I'll ask is *where the two solutions legitimately differ* versus where the Python one is just missing structure.

---

Say **done** when both files are in — or **done python** if that's all you got to.
