from enum import Enum
import math
from typing import Optional, Tuple, Union

from CONSTANTS import DEFAULT_WAVE_REWARD, TARGET_LOC_THRESHOLD
from stats import AllStats, DamageStats, DynamicStats

# Constants
DEFAULT_WAVE_HEALTH = 100
CANNON_WAVE_HEALTH = 125

def GET_DEFAULT_WAVE_STATS(isCannon=False):
    return DynamicStats.make_stats(CANNON_WAVE_HEALTH if isCannon else DEFAULT_WAVE_HEALTH, 7, 20, 0, 15)

def GET_DEFAULT_TURRET_STATS():
    return DynamicStats.make_stats(500, 25, 50, 0, 0)

class EntityState(Enum):
    NORMAL = 'normal'
    COMBAT = 'combat'
    RECALLING = 'recalling' # preparing to return to the base
    DEAD = 'dead'
    RESPAWNING = 'respawning'
    FINISHED = 'finished' # this means it should no longer be in the simulation

class Team(Enum):
    RED = 'red'
    BLUE = 'blue'
    NEUTRAL = 'neutral'

    def enemy(self):
        assert self != Team.NEUTRAL, "Don't have enemy defined for neutral"
        if self == Team.RED: return Team.BLUE
        return Team.RED

class Entity:
    def __init__(self, position, stats: DynamicStats, team: Team):
        self.position = position
        self.stats = stats
        self._state = EntityState.NORMAL
        self.path: Optional[Path] = None
        self.team = team 
        self.attacking: Optional[Entity] = None

    def move(self, time_delta):
        if self.path is None:
            return
        dist = self.get_speed() * time_delta
        self.position = self.path.move(self.position, dist)
    
    def set_pos(self, pos):
        self.position = pos

    def is_alive(self):
        return self._state not in [EntityState.DEAD, EntityState.RESPAWNING, EntityState.FINISHED]
    
    def get_damage(self) -> DamageStats:
        return self.stats.effective.damage_stats

    def take_damage(self, damage: DamageStats):
        effective_damage = self.stats.take_damage(damage)
        if self.stats.health <= 0:
            self.set_state(EntityState.DEAD)
        return effective_damage

    def set_state(self, state: EntityState):
        self._state = state

    def distance_to_entity(self, other):
        dx = self.position[0] - other.position[0]
        dy = self.position[1] - other.position[1]
        return math.hypot(dx, dy)
    
    def distance_to_point(self, point):
        dx = self.position[0] - point[0]
        dy = self.position[1] - point[1]
        return math.hypot(dx, dy)

    def get_speed(self):
        return self.stats.effective.move_speed

    def get_health(self):
        return self.stats.health
    
    def get_max_health(self):
        return self.stats.effective.health_stats.max_health
    
    def __repr__(self) -> str:
        return f"[{type(self)}] team={self.team.name} health={self.stats.health} / {self.stats.effective.health_stats.max_health}"

PathTarget = Union[Entity, Tuple[float, float]]

class Path:
    def __init__(self, target: PathTarget, reached_target_callback = None):
        self.target: PathTarget = target
        self.reached_target_callback = reached_target_callback

    def get_target_pos(self):
        if isinstance(self.target, Entity):
            return self.target.position
        return self.target

    def get_dir(self, current_pos):
        target_pos = self.get_target_pos()
        dx = target_pos[0] - current_pos[0]
        dy = target_pos[1] - current_pos[1]
        distance = math.hypot(dx, dy)
        if distance == 0:
            return (0, 0), 0
        return (dx / distance, dy / distance), distance
    
    def move(self, current_pos, speed):
        dir_vec, distance = self.get_dir(current_pos)
        if distance <= speed + TARGET_LOC_THRESHOLD:
            new_x, new_y = self.get_target_pos()
            if self.reached_target_callback is not None:
                self.reached_target_callback()
        else:
            new_x = current_pos[0] + dir_vec[0] * speed
            new_y = current_pos[1] + dir_vec[1] * speed
        return (new_x, new_y)

class Wave(Entity):
    def __init__(self, position, stats, team):
        super().__init__(position, stats, team=team)
        self.accumulated_reward = 0

    @staticmethod
    def default_wave(wave_num, team: Team):
        stats = GET_DEFAULT_WAVE_STATS(wave_num % 3 == 2)
        return Wave((0, 0), stats, team)
    
    def get_health_fraction(self):
        return  (self.stats.health / self.stats.effective.health_stats.max_health)

    def get_damage(self):
        return super().get_damage() * self.get_health_fraction()
    
    def take_damage(self, amount):
        effective_damage = super().take_damage(amount)
        reward = effective_damage * DEFAULT_WAVE_REWARD / DEFAULT_WAVE_HEALTH
        self.accumulated_reward += reward

    def accept_reward(self):
        rew = self.accumulated_reward
        self.accumulated_reward = 0
        return rew

class Turret(Entity):
    def __init__(self, position, stats, team):
        super().__init__(position, stats, team=team)
    
    @staticmethod
    def default_turret(pos, team: Team):
        stats = GET_DEFAULT_TURRET_STATS()
        return Turret(pos, stats, team)

LaneEntity = Union[Turret, Wave]