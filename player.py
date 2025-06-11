from typing import Optional
from CONSTANTS import COMBAT_THRESHOLD, DAMAGE_SIM_STEPS_PERIOD, RESPAWN_STEPS
from entity import Entity, EntityState, Path, PathTarget, Team
from entity import LaneEntity
from CONSTANTS import MAP_X


RESPAWN_POINT = {
    Team.BLUE: (0, 25),
    Team.RED: (MAP_X, 25),
}

class Player(Entity):
    def __init__(self, position, health, speed, damage, team):
        super().__init__(position, health, speed, damage, team)
        self.gold = 0
        self.attacking: Optional[LaneEntity] = None
        self.respawn_timer = None
    
    def set_respawning(self):
        self.respawn_timer = RESPAWN_STEPS
        self.state = EntityState.RESPAWNING
        self.position = RESPAWN_POINT[self.team]
    
    def step(self, sim_step):
        if self.state == EntityState.RESPAWNING:
            assert self.respawn_timer is not None, "Must have a respawn timer if respawning"
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                self.respawn_timer = None
                self.state = EntityState.NORMAL
        elif self.attacking is not None:
            if self.attacking.state != EntityState.NORMAL:
                self.set_attacking(None)
                return
            if sim_step % DAMAGE_SIM_STEPS_PERIOD != 0:
                return
            self.attacking.take_damage(self.damage)
        else:
            self.move()

    def set_path_target(self, target: PathTarget):
        self.path = Path(target)
    
    def set_attacking(self, target: Optional[LaneEntity]):
        if target is None:
            self.attacking = None
        elif self.distance_to(target) <= COMBAT_THRESHOLD:
            self.attacking = target
    
    def apply_reward(self, reward):
        self.gold += reward
    
    @staticmethod
    def default_player(position, team: Team):
        return Player(position, 300, 6, 15, team)