from dataclasses import dataclass

from item import Item
from stats import AllStats

MAX_ITEMS = 6

@dataclass
class Inventory:
    gold: int
    items: list[Item]
    
    def buy(self, item: Item):
        owned_dependencies = [i for i in self.items if i in item.dependencies]
        if len(self.items) - len(owned_dependencies) + 1 > MAX_ITEMS:
            print("Cannot buy - have too many items")
            return False
        mitigated_cost = item.cost - sum([i.cost for i in owned_dependencies])
        if mitigated_cost > self.gold:
            print(f"Cannot buy - not enough gold (have {self.gold}, need {mitigated_cost})")
            return False
        for i in owned_dependencies:
            self.items.remove(i)
        self.items.append(item)
        self.gold -= mitigated_cost
        return True

    def add_gold(self, gold):
        self.gold += gold
    
    def get_item_stats(self) -> list[AllStats]:
        return [i.stats for i in self.items]