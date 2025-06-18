from typing import Sequence, Union
from CONSTANTS import PRESENCE_THRESHOLD, SIM_STEPS_PER_SECOND, VISION_RECALCULATE_PERIOD
from entity import Entity, Team

VISION_RECALCULATE_SIM_STEPS: int = int(VISION_RECALCULATE_PERIOD * SIM_STEPS_PER_SECOND)

WARD_LIFETIME = 20

class Ward:
    def __init__(self, team: Team, position) -> None:
        self.team = team
        self.position = position
        self.time_remaining = WARD_LIFETIME
    
    def step(self, time_delta):
        self.time_remaining -= time_delta
    
    def expired(self):
        return self.time_remaining <= 0

VisionSource = Union[Entity, Ward]

class Vision:
    def __init__(self, entities: Sequence[Entity]) -> None:
        self.entities = entities
        self.wards: list[Ward] = []
        self.viewable_by_team: dict[Team, list[Entity]] = {Team.BLUE: [], Team.RED: []}
    
    def get_visibile_units(self, team: Team) -> list[Entity]:
        return self.viewable_by_team[team]
    
    def step(self, time_delta, sim_step):
        w_to_remove = []
        for w in self.wards:
            w.step(time_delta)
            if w.expired():
                w_to_remove.append(w)
        for w in w_to_remove:
            self.wards.remove(w)
        
        if sim_step % VISION_RECALCULATE_SIM_STEPS != 0:
            return # Only recalculate periodically
        self.viewable_by_team = {Team.BLUE: [], Team.RED: []}
        vision_sources = list(self.entities) + self.wards
        vision_sources_by_team = {team: [e for e in vision_sources if e.team == team] for team in (Team.RED, Team.BLUE)}
        entities_by_team = {team: [e for e in self.entities if e.team == team] for team in (Team.RED, Team.BLUE)}
        for team in (Team.RED, Team.BLUE):
            for vision_source in vision_sources_by_team[team]:
                for enemy_e in entities_by_team[team.enemy()]:
                    if enemy_e.distance_to_point(vision_source.position) <= PRESENCE_THRESHOLD:
                        self.viewable_by_team[team].append(enemy_e)