from tkinter import NORMAL
from typing import Optional
from CONSTANTS import COMBAT_START_THRESHOLD, PRESENCE_THRESHOLD, RECALL_TIME, RESPAWN_TIME
from entity import Entity, EntityState, Path, PathTarget, Team
from entity import LaneEntity
from MAP_CONSTANTS import MAP_X
from inventory import Inventory
from item import Item
from stats import AllStats, DamageStats, DynamicStats, HealthStats, LeveledStats


RESPAWN_POINT = {
    Team.BLUE: (0, 25),
    Team.RED: (MAP_X, 25),
}

def GET_DEFAULT_PLAYER_STATS():
    return DynamicStats(
        LeveledStats(
            base=AllStats(
                health_stats=HealthStats(max_health=300, health_regen=1, armor=30, magic_resist=10),
                damage_stats=DamageStats(15, 5, 0),
                move_speed=17,
            ),
            level_increase=AllStats(
                health_stats=HealthStats(max_health=50, health_regen=0.2, armor=5, magic_resist=2),
                damage_stats=DamageStats(7, 2, 0)
            )
        )
    )

class Player(Entity):
    def __init__(self, position, stats, team, player_id):
        super().__init__(position, stats, team)
        self.player_id = player_id
        self.inventory = Inventory(0, [])
        self.respawn_timer = None
        self.recall_timer = None
    
    def set_respawning(self):
        self.respawn_timer = RESPAWN_TIME
        self.set_state(EntityState.RESPAWNING)
        self.position = RESPAWN_POINT[self.team]
    
    def at_spawn(self):
        return self.distance_to_point(RESPAWN_POINT[self.team]) <= PRESENCE_THRESHOLD
    
    def step(self, time_delta, is_damage_tick):
        if self._state == EntityState.RESPAWNING:
            assert self.respawn_timer is not None, "Must have a respawn timer if respawning"
            self.respawn_timer -= time_delta
            if self.respawn_timer <= 0:
                self.reset_core()
        elif self._state == EntityState.RECALLING:
            assert self.recall_timer is not None, "Must have a recall timer if recalling"
            self.recall_timer -= time_delta
            if self.recall_timer <= 0:
                self.recall_timer = None
                self.set_state(EntityState.NORMAL)
                self.position = RESPAWN_POINT[self.team]
        elif self.attacking is not None:
            if self.attacking._state != EntityState.NORMAL:
                self.set_attacking(None)
                return
            if not is_damage_tick:
                return
            self.attacking.take_damage(self.get_damage())
        else:
            self.move(time_delta)
        
        if self.is_alive() and self.at_spawn():
            self.stats.heal()
    
    def reset_core(self):
        self.attacking = None
        self.clear_path()
        self.respawn_timer = None
        self.recall_timer = None
        self.stats.heal()
        self.set_state(EntityState.NORMAL)

    def set_state(self, state: EntityState):
        if self._state == EntityState.RECALLING and state != EntityState.RECALLING: self.recall_timer = None # Any state change should stop recall
        return super().set_state(state)

    def can_recall(self):
        #must be not doing anything in order to recall
        return self.path is None and self.attacking is None and self._state == EntityState.NORMAL

    def start_recall(self):
        if not self.can_recall():
            print("can't recall")
            return
        self.recall_timer = RECALL_TIME
        self.set_state(EntityState.RECALLING)
    
    def stop_recall(self, new_state: Optional[EntityState] = None):
        if self._state != EntityState.RECALLING:
            return
        self.recall_timer = None
        if new_state is not None:
            self.set_state(new_state)
        else:
            self.set_state(EntityState.NORMAL)

    def clear_path(self):
        self.path = None

    def set_path_target(self, target: PathTarget):
        self.stop_recall()
        self.path = Path(target, reached_target_callback=self.clear_path)
    
    def set_attacking(self, target: Optional[LaneEntity]):
        self.stop_recall()
        if target is None:
            self.attacking = None
        elif self.distance_to_entity(target) <= COMBAT_START_THRESHOLD:
            self.attacking = target
    
    def apply_reward(self, reward):
        self.inventory.add_gold(reward)
        self.stats.gain_experience(reward)

    def buy(self, item: Item):
        if self.at_spawn() and self.inventory.buy(item):
            self.stats.apply_item_stats(self.inventory.get_item_stats())
            return True
        return False
    
    @staticmethod
    def default_player(position, team: Team, player_id):
        return Player(position, GET_DEFAULT_PLAYER_STATS(), team, player_id)