"""character(name, baseHealth , baseAttack)
    weapon(name, attackBonus)
    armor(name, defense)
    
    so later as we mjust support extra wepons and armors we can use interface or abstract class and all various type of different armor and weapon will support that. and creator class which have factory method to create weapon and armor with different combination of character 
    i am assuming shield will be with respcet to the gamer here so if a gamer has a shield we can add as an extra field for him like an name or if it comes with chacarcter or armor we can add respctive place.
     
    assuming charcter has an weapon and an armor and we can swap them with new one and we can attack other character with the weapon and armor he has.
      methods 
      swapWeapon(weapon, character)
      swapArmor(armor, character)
      attack(character)"""

from __future__ import annotations
from unicodedata import name


class character:
    name = str
    baseHealth = int
    baseAttack = int
    weapon: "weapon" = None
    armor: "armor" = None

    def __init__(self, weapon_arg: "weapon" = None, armor_arg: "armor" = None):

        if weapon_arg is None:
            self.weapon = weapon()
        elif isinstance(weapon_arg, type):
            self.weapon = weapon_arg()
        else:
            self.weapon = weapon_arg

        if armor_arg is None:
            self.armor = armor()
        elif isinstance(armor_arg, type):
            self.armor = armor_arg()
        else:
            self.armor = armor_arg

    def attack(self, target):
        # safely compute bonuses and defenses (weapon or armor may be None)
        weapon_bonus = getattr(self.weapon, "attackBonus", 0)
        armor_defense = getattr(getattr(target, "armor", None), "defense", 0)
        damage = max(0, self.baseAttack + weapon_bonus - armor_defense)
        target.baseHealth -= damage

class warrior(character):
    name = "warrior"
    baseHealth = 120
    baseAttack = 12

    def __init__(self, weapon: "weapon" = None, armor: "armor" = None):
        super().__init__(weapon, armor)

class mage(character):
    name = "mage"
    baseHealth = 70
    baseAttack = 20

    def __init__(self, weapon: "weapon" = None, armor: "armor" = None):
        super().__init__(weapon, armor)

class archer(character):
    name = "archer"
    baseHealth = 90
    baseAttack = 15

    def __init__(self, weapon: "weapon" = None, armor: "armor" = None):
        super().__init__(weapon, armor)

class weapon:
    name: str = "fists"
    attackBonus: int = 0

class Sword(weapon):
    name = "sword"
    attackBonus = 10

class Bow(weapon):
    name = "bow"
    attackBonus = 7

class staff(weapon):
    name = "staff"
    attackBonus = 5


class armor:
    name: str = "None"
    defense: int = 0

class leatherArmor(armor):
    name = "leather"
    defense = 5

class plateArmor(armor):
    name = "plate"
    defense = 15

class Game:
    def __init__(self):
        self.count = 1
        self.players : dict[int, character] = {}
        self.deadplayers : dict[int, character] = {}

    def swapWeapon(self, weapon: weapon, id : int):
        character = self.players.get(id)
        if character:
            character.weapon = weapon
            return True
        return False

    def swapArmor(self, armor: armor, id : int):
        character = self.players.get(id)
        if character:
            character.armor = armor
            return True
        return False

    def addPlayer(self, character: character):
        self.players[self.count] = character
        self.count += 1

    def attack(self, attacker_id: int, target_id: int):
        attacker = self.players.get(attacker_id)
        target = self.players.get(target_id)
        if attacker and target:
            attacker.attack(target)
            if target.baseHealth <= 0:
                self.deadplayers[target_id] = target
                del self.players[target_id]
            return True
        return False



if __name__ == "__main__":
    warrior1 = warrior(armor=plateArmor, weapon=Sword)
    warrior2 = warrior()
    mage1 = mage(armor=leatherArmor, weapon=staff)
    mage2 = mage()
    archer1 = archer(armor=leatherArmor, weapon=Bow)
    archer2 = archer()

    print(f"Character: {warrior1.name}, Health: {warrior1.baseHealth}, Attack: {warrior1.baseAttack}")
    print(f"Character: {mage1.name}, Health: {mage1.baseHealth}, Attack: {mage1.baseAttack}")
    print(f"Character: {archer1.name}, Health: {archer1.baseHealth}, Attack: {archer1.baseAttack}")

    game = Game()

    game.addPlayer(warrior1)
    game.addPlayer(warrior2)
    game.addPlayer(mage1)
    game.addPlayer(mage2)
    game.addPlayer(archer1)
    game.addPlayer(archer2)

    assert game.attack(1, 2) == True
    assert game.attack(3, 4) == True
    assert game.attack(5, 6) == True

    assert game.attack(1, 3) == True
    assert game.attack(1, 3) == True
    assert game.attack(1, 3) == True 
    print(f"Character: {mage1.name}, Health: {mage1.baseHealth}, Attack: {mage1.baseAttack}")
    assert game.attack(1, 3) == True  
    print(f"Character: {mage1.name}, Health: {mage1.baseHealth}, Attack: {mage1.baseAttack}")
    assert game.attack(1, 3) == True  
    print(f"Character: {mage1.name}, Health: {mage1.baseHealth}, Attack: {mage1.baseAttack}")
    assert game.attack(1, 3) == False 
    print(game.deadplayers)

    assert game.swapWeapon(Sword(), 2) == True
    assert game.swapArmor(plateArmor(), 2) == True
    assert game.swapWeapon(Sword(), 3) == False
    

