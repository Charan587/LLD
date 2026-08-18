"""Day 2 — Combat System. Interview-grade rewrite.

═══════════════════════════════════════════════════════════════════════════
INTERVIEW WALKTHROUGH — what you say out loud, in order
═══════════════════════════════════════════════════════════════════════════

1. READ-BACK (~20s)
   "Characters with health and attack power, carrying a weapon and armor.
    Damage is attack plus weapon bonus, minus armor, floored at zero. The
    part I want to confirm: weapons and armor swap mid-fight."

2. CLARIFYING QUESTIONS
   - "Can a character swap equipment at runtime, or is loadout fixed at
      creation?" -> this is THE question; it eliminates one whole design
   - "Who adds new weapons — engineers, or designers with a config file?"
   - "Does armor ever heal, or is 0 the floor?"

3. HOW I FOUND THE CLASSES
   Nouns: character, weapon, armor, health, attack, damage.
     character -> has state and behaviour              -> Character (class)
     weapon    -> name + a number, no behaviour        -> DATA, one class, N instances
     armor     -> same                                 -> DATA
   Circle the verbs: attack, equip, take damage, die.
   Boundary words: "floored at 0", "0 or less is dead" -> write those as
   rules before coding: max(0, incoming - defense), health <= 0.

   THE TEST for weapon-as-class vs weapon-as-data:
     does the subclass override any behaviour? No -> it's data.
     Sword and Bow differ by an int. A dagger that doubles damage from
     behind carries a RULE, so that one earns a class.

4. ASSUMPTIONS
   - A character starts with Fists and no armor.
   - Damage is deterministic; no randomness, so tests can assert exactly.
   - Dead characters are inert: they cannot attack or be attacked.

5. THE DESIGN I REJECTED
   "SwordWarrior, BowWarrior, PlateArcher — subclassing per combination.
    3 characters x 4 weapons x 3 armors is 36 classes, and one new weapon
    adds 9 more. But the real reason I rejected it is correctness, not
    volume: a class is fixed at construction. A SwordWarrior picking up a
    bow would have to become a different object, so I'd copy every field by
    hand and lose object identity — anything else holding a reference to
    that character is now tracking someone who no longer exists."

6. THE DESIGN + PRINCIPLE NAMES
   "COMPOSITION OVER INHERITANCE — model has-a, not is-a, when the
    relationship changes at runtime. That also gives me OPEN/CLOSED: 40 more
    weapons are 40 config rows and zero edits to any character class."

7. LIMITS I'D VOLUNTEER
   - "Two equipment slots as two fields. At five slots I'd move to a
      dict[Slot, Equipment] so a shield doesn't mean a new method."
   - "is_dead lives on Character deliberately — it's a fact about a
      character, not about whichever collection is holding it."

═══════════════════════════════════════════════════════════════════════════
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
