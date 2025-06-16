from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from stats import AllStats


@dataclass
class Item:
    name: str
    stats: AllStats
    cost: int
    dependencies: list[Item] # Items that if in inventory can be sold at original price to help cover the cost

SWORD = Item("Sword", AllStats.make_stats(physical_damage=15), 350, [])
ARMOR = Item("Armor", AllStats.make_stats(armor=15), 350, [])
SHIELD = Item("Shield", AllStats.make_stats(max_health=50), 350, [])
STAFF = Item("Staff", AllStats.make_stats(magic_damage=10), 350, [])

ALL_ITEMS = {
    i.name : i for i in [SWORD, ARMOR, SHIELD, STAFF]
}