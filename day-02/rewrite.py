"""Day 2 — interview-grade rewrite. Compare against solution.submitted.py.

The composition call was right. What changes here:
  - data-only subclasses become instances (Warrior/Mage/Sword/Plate were classes with no behavior)
  - Character owns its own death rule instead of Game inferring it from dict membership
  - current_health separated from max_health
  - no Game registry — it wasn't asked for, and it made equip() unreachable without one
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Weapon:
    name: str
    attack_bonus: int


@dataclass(frozen=True)
class Armor:
    name: str
    defense: int


FISTS = Weapon("Fists", 0)
SWORD = Weapon("Sword", 10)
BOW = Weapon("Bow", 7)
STAFF = Weapon("Staff", 5)

NO_ARMOR = Armor("None", 0)
LEATHER = Armor("Leather", 5)
PLATE = Armor("Plate", 15)


class Character:
    def __init__(self, name: str, max_health: int, base_attack: int,
                 weapon: Weapon = FISTS, armor: Armor = NO_ARMOR):
        self.name = name
        self.max_health = max_health
        self.current_health = max_health
        self.base_attack = base_attack
        self.weapon = weapon
        self.armor = armor

    @property
    def is_dead(self) -> bool:
        return self.current_health <= 0

    @property
    def damage_output(self) -> int:
        return self.base_attack + self.weapon.attack_bonus

    def equip(self, weapon: Weapon) -> None:
        self.weapon = weapon

    def wear(self, armor: Armor) -> None:
        self.armor = armor

    def take_damage(self, incoming: int) -> None:
        self.current_health -= max(0, incoming - self.armor.defense)

    def attack(self, target: "Character") -> None:
        if self.is_dead:
            raise ValueError(f"{self.name} is dead and cannot attack")
        if target.is_dead:
            raise ValueError(f"{target.name} is dead and cannot be attacked")
        target.take_damage(self.damage_output)


# Warrior/Mage/Archer are data, not types — they add no behavior over Character.
def warrior(**kw) -> Character: 
    return Character("Warrior", 120, 12, **kw)
def mage(**kw) -> Character:    return Character("Mage", 70, 20, **kw)
def archer(**kw) -> Character:  return Character("Archer", 90, 15, **kw)


def raises(fn, *args) -> bool:
    try:
        fn(*args)
    except ValueError:
        return True
    return False


if __name__ == "__main__":
    # damage output
    assert warrior(weapon=SWORD).damage_output == 22
    assert mage(weapon=STAFF).damage_output == 25

    # armor subtracts
    m = mage(armor=LEATHER)
    warrior(weapon=SWORD).attack(m)
    assert m.current_health == 53, m.current_health

    # armor floors at 0 — must NOT heal
    tank = warrior(armor=PLATE)
    warrior().attack(tank)                     # 12 damage vs 15 defense
    assert tank.current_health == 120, tank.current_health

    # runtime swap: same character, health untouched
    w = warrior(weapon=SWORD)
    assert w.damage_output == 22
    w.equip(BOW)
    assert w.damage_output == 19
    assert w.current_health == 120

    # no weapon / no armor defaults
    plain = warrior()
    assert plain.damage_output == 12
    victim = mage()
    plain.attack(victim)
    assert victim.current_health == 58

    # death
    doomed = mage()
    killer = warrior(weapon=SWORD)
    for _ in range(4):
        killer.attack(doomed)                  # 4 x 22 = 88 vs 70 hp
    assert doomed.is_dead
    assert doomed.current_health == -18

    # dead characters are inert, without needing a Game to police it
    assert raises(killer.attack, doomed)       # cannot be attacked
    assert raises(doomed.attack, killer)       # cannot attack
    assert killer.current_health == 120        # dead character dealt no damage

    print("all checks passed")
