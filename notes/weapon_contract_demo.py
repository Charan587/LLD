"""Data and behavior coexisting behind one contract.

The point: 40 flat weapons live in a config file and need zero classes.
Only a weapon with a *rule* gets its own class. `Character.attack` never
learns that daggers exist.

Run: python3 weapon_contract_demo.py
"""

from dataclasses import dataclass
from typing import Protocol


# --- context -----------------------------------------------------------
# What the weapon is allowed to know about the situation. Grows as rules
# demand it; nothing outside this struct leaks into weapons.

@dataclass(frozen=True)
class AttackContext:
    from_behind: bool = False


# --- the contract ------------------------------------------------------

class Weapon(Protocol):
    name: str

    def damage(self, base_attack: int, ctx: AttackContext) -> int: ...


# --- data: one class, N instances, loaded from config ------------------

@dataclass(frozen=True)
class SimpleWeapon:
    """A flat bonus. Sword, Bow, Staff and 37 others are all *this*."""
    name: str
    attack_bonus: int

    def damage(self, base_attack: int, ctx: AttackContext) -> int:
        return base_attack + self.attack_bonus


WEAPON_CONFIG = [           # in production: json.load(open("weapons.json"))
    ("Fists", 0),
    ("Sword", 10),
    ("Bow", 7),
    ("Staff", 5),
]
CATALOG: dict[str, Weapon] = {n: SimpleWeapon(n, b) for n, b in WEAPON_CONFIG}


# --- behavior: earns a class because it carries a rule -----------------

@dataclass(frozen=True)
class Dagger:
    name: str = "Dagger"
    attack_bonus: int = 4

    def damage(self, base_attack: int, ctx: AttackContext) -> int:
        raw = base_attack + self.attack_bonus
        return raw * 2 if ctx.from_behind else raw


CATALOG["Dagger"] = Dagger()


# --- the caller, which knows only the contract -------------------------

class Character:
    def __init__(self, name: str, health: int, base_attack: int,
                 weapon: Weapon = CATALOG["Fists"]):
        self.name = name
        self.health = health
        self.base_attack = base_attack
        self.weapon = weapon

    def equip(self, weapon: Weapon) -> None:
        self.weapon = weapon

    def attack(self, target: "Character", ctx: AttackContext = AttackContext()) -> None:
        # no isinstance, no name check, no if-chain — and none is ever needed
        target.health -= self.weapon.damage(self.base_attack, ctx)


if __name__ == "__main__":
    FRONT = AttackContext(from_behind=False)
    BEHIND = AttackContext(from_behind=True)

    rogue = Character("Rogue", 80, 12, CATALOG["Dagger"])
    guard = Character("Guard", 100, 10, CATALOG["Sword"])

    # flat weapon: context is irrelevant, same damage either way
    assert guard.weapon.damage(guard.base_attack, FRONT) == 20
    assert guard.weapon.damage(guard.base_attack, BEHIND) == 20

    # the rule lives in the dagger
    assert rogue.weapon.damage(rogue.base_attack, FRONT) == 16
    assert rogue.weapon.damage(rogue.base_attack, BEHIND) == 32

    # same call site, two behaviors — this is polymorphism doing the work
    victim = Character("Victim", 100, 5)
    guard.attack(victim, BEHIND)
    assert victim.health == 80          # sword ignores position
    rogue.attack(victim, BEHIND)
    assert victim.health == 48          # dagger doubles

    # a designer adds a weapon: one config row, zero code
    WEAPON_CONFIG.append(("Warhammer", 18))
    CATALOG["Warhammer"] = SimpleWeapon("Warhammer", 18)
    guard.equip(CATALOG["Warhammer"])
    assert guard.weapon.damage(guard.base_attack, FRONT) == 28

    # runtime swap still free — identity preserved, health untouched
    assert guard.health == 100
    guard.equip(CATALOG["Bow"])
    assert guard.weapon.damage(guard.base_attack, FRONT) == 17

    print("all checks passed")
