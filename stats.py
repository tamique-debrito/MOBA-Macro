from dataclasses import dataclass, field
from typing import Callable, Optional
import textwrap


EXPERIENCE_THRESHOLDS = {
    1: 0,
    2: 100,
    3: 200,
    4: 350,
    5: 500,
    6: 700,
    7: 900,
    8: 1150,
    9: 1400,
    10: 2000,
}

MAX_LEVEL = max(EXPERIENCE_THRESHOLDS.keys())


def indent(string: str, indentLevel: int = 1):
    prefix = indentLevel * "  "
    return textwrap.indent(string, prefix)

@dataclass
class DamageStats:
    physical_damage: float = 0
    magic_damage: float = 0
    true_damage: float = 0

    def __add__(self, other):
        if not isinstance(other, DamageStats):
            return NotImplemented
        return DamageStats(
            physical_damage=self.physical_damage + other.physical_damage,
            magic_damage=self.magic_damage + other.magic_damage,
            true_damage=self.true_damage + other.true_damage
        )

    def __mul__(self, scalar):
        if not isinstance(scalar, (int, float)):
            return NotImplemented
        return DamageStats(
            physical_damage=self.physical_damage * scalar,
            magic_damage=self.magic_damage * scalar,
            true_damage=self.true_damage * scalar
        )

@dataclass
class HealthStats:
    max_health: float = 0
    health_regen: float = 0
    armor: float = 0
    magic_resist: float = 0

    def __add__(self, other):
        if not isinstance(other, HealthStats):
            return NotImplemented
        return HealthStats(
            max_health=self.max_health + other.max_health,
            health_regen=self.health_regen + other.health_regen,
            armor=self.armor + other.armor,
            magic_resist=self.magic_resist + other.magic_resist
        )

    def __mul__(self, scalar):
        if not isinstance(scalar, (int, float)):
            return NotImplemented
        return HealthStats(
            max_health=self.max_health * scalar,
            health_regen=self.health_regen * scalar,
            armor=self.armor * scalar,
            magic_resist=self.magic_resist * scalar
        )

    def get_effective_damage(self, damage: DamageStats):

        physical_multiplier = 100 / (100 + self.armor)
        magic_multiplier = 100 / (100 + self.magic_resist)

        total_damage = 0

        # effective physical damage
        effective_physical_damage = damage.physical_damage * physical_multiplier
        total_damage += effective_physical_damage

        # effective magic damage
        effective_magic_damage = damage.magic_damage * magic_multiplier
        total_damage += effective_magic_damage

        # True damage
        total_damage += damage.true_damage

        return total_damage

@dataclass
class AllStats:
    health_stats: HealthStats = HealthStats()
    damage_stats: DamageStats = DamageStats()
    move_speed: float = 0

    def get_effective_damage(self, damage: DamageStats):
        return self.health_stats.get_effective_damage(damage)

    def __add__(self, other):
        if not isinstance(other, AllStats):
            return NotImplemented
        return AllStats(
            health_stats=self.health_stats + other.health_stats,
            damage_stats=self.damage_stats + other.damage_stats,
            move_speed=self.move_speed + other.move_speed
        )

    def __mul__(self, scalar):
        if not isinstance(scalar, (int, float)):
            return NotImplemented
        return AllStats(
            health_stats=self.health_stats * scalar,
            damage_stats=self.damage_stats * scalar,
            move_speed=self.move_speed * scalar
        )

    @staticmethod
    def make_stats(max_health=0, health_regen=0, armor=0, magic_resist=0, physical_damage=0, magic_damage=0, move_speed=0):
        return AllStats(
            health_stats=HealthStats(
                max_health=max_health,
                health_regen=health_regen,
                armor=armor,
                magic_resist=magic_resist,
            ),
            damage_stats = DamageStats(
                physical_damage=physical_damage,
                magic_damage=magic_damage
            ),
            move_speed=move_speed
        )

@dataclass
class LeveledStats:
    base: AllStats
    level_increase: AllStats
    effective: AllStats = field(init=False)
    level: int = field(init=False)
    experience: int = 0

    def __post_init__(self):
        self.set_level(1)
    
    def set_level(self, level):
        self.effective = self.base + (self.level_increase * (level - 1))
        self.level = level

    def gain_experience(self, experience):
        self.experience += experience
        if self.canLevelUp():
            self.updateLevel()
            return True
        return False
    
    def canLevelUp(self):
        return self.level < MAX_LEVEL and EXPERIENCE_THRESHOLDS[self.level + 1] <= self.experience
    
    def updateLevel(self):
        for newLevel in range(self.level + 1, MAX_LEVEL + 1):
            if EXPERIENCE_THRESHOLDS[newLevel] <= self.experience:
                self.level = newLevel
            else:
                break

@dataclass
class ItemStats:
    effective: AllStats = AllStats() # everything is zero by default

    def apply_item_stats(self, item_stats: list[AllStats]):
        self.effective = AllStats()
        for stats in item_stats:
            self.effective = self.effective + stats

@dataclass
class DynamicStats:
    # This stats object should persist on entities
    health: float = field(init=False)
    effective: AllStats = field(init=False)
    leveled: LeveledStats
    items: ItemStats = ItemStats()
    
    def __post_init__(self):
        self.effective = self.leveled.effective + self.items.effective
        self.health = self.effective.health_stats.max_health
    
    def reevaluate(self):
        missing_health = self.effective.health_stats.max_health - self.health
        self.effective = self.leveled.effective + self.items.effective
        self.health = self.effective.health_stats.max_health - missing_health
        

    def apply_item_stats(self, item_stats: list[AllStats]):
        self.items.apply_item_stats(item_stats)
        self.reevaluate()

    def gain_experience(self, experience):
        if self.leveled.gain_experience(experience):
            self.reevaluate() # recompute stats if we leveled up
    
    def take_damage(self, damage: DamageStats):
        effective_damage = self.effective.get_effective_damage(damage)
        self.health = max(self.health - effective_damage, 0)
        return effective_damage

    def heal(self):
        self.health = self.effective.health_stats.max_health
    
    def step_heal(self, time_delta):
        new_health = self.health + self.effective.health_stats.health_regen * time_delta
        self.health = max(self.effective.health_stats.max_health, new_health)

    @staticmethod
    def make_stats(max_health, physical_damage, armor, magic_resist, move_speed):
        return DynamicStats(
            leveled=LeveledStats(
                base=AllStats(
                    health_stats=HealthStats(
                        max_health=max_health,
                        armor=armor,
                        magic_resist=magic_resist,
                    ),
                    damage_stats = DamageStats(physical_damage=physical_damage),
                    move_speed=move_speed
                ),
                level_increase=AllStats()
            )
        )