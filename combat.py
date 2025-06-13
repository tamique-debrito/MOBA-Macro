from typing import Sequence
from CONSTANTS import DISENGAGE_TIME, PLAYER_ATTACK_MISS_PROBABILITY
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
        assert entity._state != EntityState.COMBAT, "Tried to add an Entity to Combat that is already in the COMBAT state"
        entity.set_state(EntityState.COMBAT)
        self.entities.append(entity)
        if isinstance(entity, Player):
            self.players_by_team[entity.team].append(entity)

    def start_disengage(self):
        if self.disengage_counter is not None:
            return
        self.disengage_counter = DISENGAGE_TIME
    
    def cleanup(self):
        for e in self.entities:
            if e._state == EntityState.COMBAT:
                e.set_state(EntityState.NORMAL)
        print("combat ended")

    def step(self, time_delta, is_damage_tick):
        self.steps_run += 1
        if self.disengage_counter is not None:
            self.disengage_counter -= time_delta
            if self.disengage_counter <= 0:
                self.active = False
        if not is_damage_tick:
            return self.active # Combat/damage is only applied every DAMAGE_TICK_TIME sim steps

        to_remove = []
        for entity in self.entities:
            if entity.is_alive():
                enemies = self.players_by_team[entity.team.enemy()]
                if len(enemies) == 0:
                    print("got empty enemies list")
                    break
                if random.random() <= PLAYER_ATTACK_MISS_PROBABILITY:
                    continue # Incorporate some additional combat randomness via a miss probability
                target = random.choice(enemies)
                target.take_damage(entity.get_damage())
                if not target.is_alive():
                    enemies.remove(target)
                    to_remove.append(target)
        for target in to_remove:
            self.entities.remove(target)
        if len(self.players_by_team[Team.BLUE]) == 0 or len(self.players_by_team[Team.RED]) == 0:
            self.active = False
        return self.active