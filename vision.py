from typing import Sequence
from CONSTANTS import SIM_STEPS_PER_SECOND, VISION_RECALCULATE_PERIOD
from entity import Entity, Team

VISION_RECALCULATE_SIM_STEPS: int = int(VISION_RECALCULATE_PERIOD * SIM_STEPS_PER_SECOND)

class Vision:
    def __init__(self, entities: Sequence[Entity]) -> None:
        self.entities = entities
        self.viewable_by_team: dict[Team, list[Entity]] = {}
    
    def get_visibile_units(self, team: Team) -> list[Entity] # type: ignore
        ...
    
    def step(self, sim_step):
        if sim_step % VISION_RECALCULATE_SIM_STEPS != 0:
            return # Only recalculate periodically
        ...