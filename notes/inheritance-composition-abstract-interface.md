# Inheritance vs Composition · Abstract Class vs Interface

Reference note. Reread before any problem where you're deciding what subclasses to make.

---

## Part 1 — Inheritance vs Composition

### The two relationships

| | Reads as | Code | Fixed when |
|---|---|---|---|
| **Inheritance** | Warrior **is a** Character | `class Warrior(Character)` | Construction. Permanent. |
| **Composition** | Warrior **has a** Weapon | `self.weapon = sword` | Never. Swappable any time. |

### The test that actually decides it

Ask: **"can this change during the object's lifetime?"**

- A Warrior is always a Character. Never changes → inheritance is *allowed*.
- A Warrior's weapon changes constantly → composition is *required*.

That's not a style preference, and this is the part people miss: **inheritance physically cannot model something that changes.** An object's class is set at `__new__` and is not a mutable field. To "change class" you must construct a different object.

### Why that's a correctness argument

Say you modelled it as `SwordWarrior(Warrior)` and now the character picks up a bow:

```python
old = SwordWarrior("Conan", health=43)     # mid-fight, damaged
new = BowWarrior("Conan", health=43)       # copy every field across by hand
```

Three things just broke:

1. **Every field must be copied by hand.** Miss one — a status effect, a cooldown, an XP counter — and it silently vanishes. This gets worse with every field ever added.
2. **Object identity is destroyed.** `new is not old`. Anything else holding a reference — the party list, an enemy's current target, a damage-over-time effect, an event subscription — still points at `old`. Those references now track a character who no longer exists. This is the killer, and it's the one to say out loud in an interview.
3. **The combinatorial explosion.** 3 characters × 4 weapons × 3 armors = 36 classes. Add one weapon → 9 more. Add a shield slot → multiply again.

Point 3 is the one everybody quotes, but it's the *weakest* of the three — it's about volume of code. Points 1 and 2 are about **the program being wrong**. That's the distinction between an aesthetics argument and a correctness argument.

### When inheritance is genuinely right

Not never. Use it when **all** of these hold:

- The relationship is permanent (a `Circle` is always a `Shape`)
- Subclasses **override behavior** — they do something differently, not just hold different numbers
- Every subclass can stand in for the base without surprising the caller (this is LSP, day 4)

### The trap: subclasses that override nothing

```python
class Sword(weapon):
    name = "sword"
    attackBonus = 10
```

`Sword` overrides no methods. It adds no behavior. It is **two values wearing a class costume.**

Inheritance exists to provide **polymorphism** — different classes responding to the same call differently. No override means no polymorphism, which means the subclass is buying you nothing while costing you a type.

**The test: does this subclass override any behavior?**
- **No** → it's data. Make it an instance. `SWORD = Weapon("Sword", 10)`
- **Yes** → it's a type. Make it a class.

This isn't one of the SOLID five — don't go hunting for a name, because there isn't a canonical one. It's the **type vs instance** distinction, and the practical consequence is what sells it:

> Your spec said *a designer adds 40 weapons.*
> As classes: 40 code edits, a code review, a deploy.
> As data: 40 rows in a config file, no code at all.

```python
WEAPONS = [Weapon(n, b) for n, b in load_json("weapons.json")]
```

A designer can ship that. A designer cannot ship a subclass.

### Type vs instance — the distinction underneath all of this

A **class (type)** answers: *what kind of thing is this, and what can it do?*
An **instance** answers: *which particular one is it?*

So the question for `Sword` is: **is a sword a different *kind* of thing from a bow, or the same kind with different numbers?**

Same kind. Both are "a thing you hold that adds to your attack." They differ in a `name` and an `int`. That's not a different kind — that's a different *value*.

The absurdity test makes it obvious. Nobody writes:

```python
class Room101(Room): number = 101      # ✗ obviously
class Room102(Room): number = 102
class Age37(Age): value = 37           # ✗ obviously
class India(Country): name = "India"   # ✗ obviously
```

`Sword(weapon)` with `attackBonus = 10` is the identical mistake — it just doesn't *look* absurd, because weapons feel like categories in a way room numbers don't. **The feeling is the trap.** Apply the mechanical test instead: does it override behavior?

`class India(Country)` becomes correct the moment India needs behavior no other country has. Same for the dagger.

### Why it actually matters: classes are code, instances are data

This is the practical payoff, and it's what to say in an interview:

| | Class | Instance |
|---|---|---|
| Lives in | source code | memory, a DB row, a JSON file |
| Created by | a programmer, at edit time | anyone, at runtime |
| To add one | edit → review → deploy | insert a row |
| Can you load 500 from a file? | no | yes |
| Can you count / filter / sort them? | awkward (`__subclasses__`) | trivially, they're a list |
| Can a designer add one? | **no** | **yes** |

Your spec said *a designer adds 40 weapons and may not edit character classes.* Classes make that literally impossible — a designer cannot write Python and ship a deploy. Instances make it a config file.

That's the whole argument in one line: **you cannot load a class from a JSON file, but you can load a thousand instances from one.**

### The line: when a weapon earns a class

The moment it has **behavior**, not just values.

```python
Weapon("Sword", 10)           # data — a number
DaggerFromBehind()            # class — a rule ("double damage if attacker is behind")
```

Both coexist. `Weapon` becomes an interface with `damage_against(target, context)`; flat weapons share one `SimpleWeapon` implementation and stay data-driven; only weapons with real rules get their own class.

**What you must not do** is put the dagger's rule inside `Character.attack`:

```python
def attack(self, target):
    if self.weapon.name == "dagger" and self.is_behind(target):   # ✗
        damage *= 2
    elif self.weapon.name == "flaming_sword":                     # ✗ and it grows
        ...
```

That's an `if`-chain in the caller that grows with every new weapon — the exact Open/Closed violation composition was supposed to prevent. **The variation belongs in the thing that varies.**

---

## Part 2 — Abstract Class vs Interface

Both let you write code against an abstraction instead of a concrete type. They differ in what they can carry.

### Java

| | `interface` | `abstract class` |
|---|---|---|
| Method bodies | only `default` methods | yes, freely |
| Fields / state | no (constants only) | yes |
| Constructor | no | yes |
| How many can you have | **many** — `implements A, B, C` | **one** — `extends` |
| Answers | "what can it *do*" | "what *is* it, partially built" |

```java
interface Weapon {                    // a contract
    int attackBonus();
}

abstract class Character {            // shared state + partial implementation
    protected int currentHealth;      // state — an interface cannot hold this
    protected Weapon weapon;

    public boolean isDead() {         // shared implementation
        return currentHealth <= 0;
    }

    public abstract String battleCry();   // subclasses must supply this
}
```

**Choosing:** shared *state* or shared *implementation* → abstract class. Pure capability, especially one an unrelated class might also want → interface. Single-inheritance is the constraint that usually decides it: a class can only extend one thing, so spend that budget carefully and put capabilities in interfaces.

### Python

Python has no `interface` keyword. Two tools:

```python
from abc import ABC, abstractmethod

class Weapon(ABC):                    # ≈ abstract class
    @abstractmethod
    def attack_bonus(self) -> int: ...
```
Subclass must implement `attack_bonus` or instantiation raises `TypeError`. Can also hold state and concrete methods.

```python
from typing import Protocol

class Weapon(Protocol):               # ≈ interface, structural
    def attack_bonus(self) -> int: ...
```
**Nothing needs to inherit from it.** Any class with a matching `attack_bonus` method satisfies it — checked by the type checker, not at runtime. This is "static duck typing."

### And the third option, which is what you actually did

Nothing at all. Python's duck typing means `character.attack()` calls `self.weapon.attack_bonus` and any object with that attribute works. **Your day-2 solution had no abstraction and ran correctly.**

That's the real answer to "interfaces vs abstract classes in Python": you often need neither. Reach for one when you want:

- **A declared contract** so a reader knows what a Weapon must provide without grepping every call site
- **An enforced error at construction** rather than an `AttributeError` deep in combat at runtime
- **Type-checker support** so `mypy` catches a bad weapon before it ships

For a 45-minute round with 3 weapons, no abstraction is a defensible call — **say so out loud**: *"I'm skipping the ABC since duck typing covers it; I'd add one if the team needed a declared contract."* That reads as judgment. Silently omitting it reads as not knowing.

### Quick chooser

| Situation | Use |
|---|---|
| Shared state or shared implementation | abstract class (`ABC`) |
| Pure capability, possibly across unrelated types | interface (`Protocol`) |
| Only data varies, no behavior | **neither — use instances** |
| Small script, one obvious implementation | neither; note the choice |

---

## The one-liner for each

- **Inheritance** = "is-a", permanent, gives polymorphism. Justified only when subclasses override behavior.
- **Composition** = "has-a", swappable at runtime, preserves identity. Default choice.
- **Abstract class** = partial implementation + state. One per class.
- **Interface** = pure contract, no state. Many per class.
- **Data** = when nothing varies but the numbers. Most "subclasses" are secretly this.
