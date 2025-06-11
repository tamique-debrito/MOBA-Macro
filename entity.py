from enum import Enum
import math
from typing import Optional, Tuple, Union

from CONSTANTS import TARGET_LOC_THRESHOLD

# Constants
class EntityState(Enum):
    NORMAL = 'normal'
    COMBAT = 'combat'
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
    def __init__(self, position, health, speed, damage, team: Team):
        self.position = position
        self.health = health
        self.max_health = health
        self.speed = speed
        self.damage = damage
        self.state = EntityState.NORMAL
        self.path: Optional[Path] = None
        self.team = team 

    def move(self):
        if self.path is None:
            return
        self.position = self.path.move(self.position, self.speed)
    
    def set_pos(self, pos):
        self.position = pos

    def is_alive(self):
        return self.state in [EntityState.NORMAL, EntityState.COMBAT]
    
    def get_damage(self):
        return self.damage

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.state = EntityState.DEAD

    def distance_to(self, other):
        dx = self.position[0] - other.position[0]
        dy = self.position[1] - other.position[1]
        return math.hypot(dx, dy)
    
    def __repr__(self) -> str:
        return f"[{type(self)}] team={self.team.name} health={self.health} / {self.max_health}"

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
    def __init__(self, position, health, speed, damage, team):
        super().__init__(position, health, speed, damage, team=team)
        self.accumulated_reward = 0

    @staticmethod
    def default_wave(wave_num, team: Team):
        if wave_num % 3 == 2:
            return Wave((0, 0), 150, 5, 10, team)
        return Wave((0, 0), 100, 5, 7, team)
    
    def get_damage(self):
        return self.damage * self.health / self.max_health
    
    def take_damage(self, amount):
        super().take_damage(amount)
        reward = amount / self.max_health * 100
        self.accumulated_reward += reward

    def accept_reward(self):
        rew = self.accumulated_reward
        self.accumulated_reward = 0
        return rew

class Turret(Entity):
    def __init__(self, position, health, damage, team):
        super().__init__(position, health, speed=0, damage=damage, team=team)
    
    @staticmethod
    def default_turret(pos, team: Team):
        return Turret(pos, 500, 50, team)


LaneEntity = Union[Turret, Wave]