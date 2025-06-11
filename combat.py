from typing import Sequence
from CONSTANTS import DAMAGE_SIM_STEPS_PERIOD, DISENGAGE_SIM_STEPS, PLAYER_ATTACK_MISS_PROBABILITY
from player import Player
from entity import Entity, EntityState, Team


import random


class Combat:
    def __init__(self, entities: Sequence[Entity], position):
        self.entities: list[Entity] = []  # List of entities involved in combat
        self.position = position
        self.disengage_counter = None
        self.active = True
        self.steps_run = 0

        self.players_by_team: dict[Team, list[Player]] = {
            Team.RED: [],
            Team.BLUE: [],
        }

        for entity in entities:
            self.add_entity(entity)
        
        print("combat started")

    def add_entity(self, entity: Entity):
        assert entity.state != EntityState.COMBAT, "Tried to add an Entity to Combat that is already in the COMBAT state"
        entity.state = EntityState.COMBAT
        self.entities.append(entity)
        if isinstance(entity, Player):
            self.players_by_team[entity.team].append(entity)

    def start_disengage(self):
        if self.disengage_counter is not None:
            return
        self.disengage_counter = DISENGAGE_SIM_STEPS
    
    def cleanup(self):
        for e in self.entities:
            if e.state == EntityState.COMBAT:
                e.state = EntityState.NORMAL
        print("combat ended")

    def step(self, sim_step):
        self.steps_run += 1
        if sim_step % DAMAGE_SIM_STEPS_PERIOD != 0:
            return self.active # Combat/damage is only applied every DAMAGE_TICK_TIME sim steps
        if self.disengage_counter is not None:
            self.disengage_counter -= DAMAGE_SIM_STEPS_PERIOD
            if self.disengage_counter <= 0:
                self.active = False

        to_remove = []
        for entity in self.entities:
            if entity.is_alive():
                enemies = self.players_by_team[entity.team.enemy()]
                if random.random() <= PLAYER_ATTACK_MISS_PROBABILITY:
                    continue # Incorporate some additional combat randomness via a miss probability
                target = random.choice(enemies)
                target.take_damage(entity.damage)
                if not target.is_alive():
                    enemies.remove(target)
                    to_remove.append(target)
                if len(enemies) == 0:
                    break
        for target in to_remove:
            self.entities.remove(target)
        if len(self.players_by_team[Team.BLUE]) == 0 or len(self.players_by_team[Team.RED]) == 0:
            self.active = False
        return self.active