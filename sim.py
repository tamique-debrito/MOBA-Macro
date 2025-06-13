
import math
from typing import Optional, Sequence

from CONSTANTS import COMBAT_INCLUDE_THRESHOLD, COMBAT_START_THRESHOLD, DAMAGE_APPLY_INTERVAL, MAP_X, PRESENCE_THRESHOLD, SIM_STEPS_PER_SECOND
from combat import Combat
from lane import LaneSimulator
from player import Player
from entity import Entity, LaneEntity, Wave, EntityState, Team, Turret, Wave

PLAYER_START_INFO = {
    Team.BLUE: [
        ((0, 25), "A"),
        ((25, 25), "B"),
        ((50, 25), "C"),
    ],
    Team.RED: [
        ((MAP_X, 25), "D"),
        ((MAP_X - 25, 25), "E"),
        ((MAP_X - 50, 25), "F")
    ]
}

class Map:
    def __init__(self):
        self.entities: list[Entity] = []
        self.combats: list[Combat] = []
        self.players: Sequence[Player] = []
        for team in PLAYER_START_INFO:
            for info in PLAYER_START_INFO[team]:
                player = Player.default_player(info[0], team, info[1])
                self.add_entity(player)
                self.players.append(player)
        self.lanes = LaneSimulator(self.add_entity, self.players, lambda x: None)

    def add_entity(self, entity):
        self.entities.append(entity)

    def find_entities_in_range(
            self, position, range_dist,
            exclude=None, entities_list: Optional[Sequence[Entity]] = None, team: Optional[Team] = None, state: Optional[EntityState] = None) -> Sequence[Entity]:
        result = []
        if entities_list is None:
            entities_list = self.entities
        for e in entities_list:
            if state is not None and e._state != state:
                continue
            if team is not None and e.team != team:
                continue
            if e != exclude and e._state != EntityState.DEAD:
                if math.hypot(e.position[0] - position[0], e.position[1] - position[1]) <= range_dist:
                    result.append(e)
        return result

    def find_combat_in_range(self, player: Player):
        for combat in self.combats:
            if player.distance_to_entity(combat) <= COMBAT_INCLUDE_THRESHOLD:
                return combat
    
    def start_combat_at_location(self, position):
        entities = self.find_entities_in_range(position, COMBAT_START_THRESHOLD, state=EntityState.NORMAL)
        has_red_player = any([e.team == Team.RED for e in entities if e._state == EntityState.NORMAL])
        has_blue_player = any([e.team == Team.BLUE for e in entities if e._state == EntityState.NORMAL])
        if has_red_player and has_blue_player:
            entities_to_use = self.find_entities_in_range(position, COMBAT_INCLUDE_THRESHOLD, state=EntityState.NORMAL)
            self.combats.append(Combat(entities_to_use, position))

    def join_combat(self, player: Player, combat: Combat):
        if player.distance_to_entity(combat) <= COMBAT_INCLUDE_THRESHOLD:
            combat.add_entity(player)
    
    def get_players(self) -> list[Player]:
        return [e for e in self.entities if isinstance(e, Player)]
    
    def get_player_by_id(self, player_id):
        for p in self.get_players():
            if p.player_id == player_id:
                return p
    
    def distribute_rewards(self):
        # Distributes rewards for damaging waves
        players = self.get_players()
        for e in self.entities:
            if isinstance(e, Wave):
                rew = e.accept_reward()
                in_range: list[Player] = self.find_entities_in_range(e.position, PRESENCE_THRESHOLD, entities_list=players, team=e.team.enemy()) # type:ignore it's restricted to a list of players
                if len(in_range) > 0:
                    if len(in_range) > 1:
                        rew = rew * 1.3 # Sharing multiplier
                    split_reward = rew / len(in_range)
                    for player in in_range:
                        player.apply_reward(split_reward)
    
    def on_entity_death(self, entity: Entity):
        if isinstance(entity, Player):
            entity.set_respawning()
        else:
            self.entities.remove(entity)
            self.lanes.remove_entity(entity)

    def step(self, time_delta, sim_time, is_damage_tick, sim_step):
        for entity in self.get_players():
            # Only handle things for players. LaneSimulator handles wave movement
            if entity._state == EntityState.COMBAT:
                continue # The combat class does handling for this state
            entity.step(time_delta, is_damage_tick)
        self.lanes.step(time_delta, sim_time, is_damage_tick, sim_step)

        finished_combats = []
        for combat in self.combats:
            done = not combat.step(time_delta, is_damage_tick)
            if done:
                combat.cleanup()
                finished_combats.append(combat)
        for finished_combat in finished_combats:
            self.combats.remove(finished_combat)
        
        for entity in self.entities:
            if entity._state == EntityState.DEAD:
                self.on_entity_death(entity)
        
        self.distribute_rewards()


    def attack_enemy_lane_entity_in_range(self, player: Player):
        # If there is a LaneEntity in range, will command the player to attack it
        for e in self.entities:
            if e.team == player.team.enemy() and isinstance(e, LaneEntity):
                player.set_attacking(e)

class Simulator:
    def __init__(self) -> None:
        self.map = Map()
        self.sim_step = 0
        self.time_delta = 1 / SIM_STEPS_PER_SECOND
        self.damage_tick_timer = DAMAGE_APPLY_INTERVAL
    
    def step(self):
        is_damage_tick = self.damage_tick_timer < 0
            
        self.map.step(self.time_delta, self.sim_step * self.time_delta, is_damage_tick, self.sim_step)
        self.sim_step += 1
        if is_damage_tick:
            self.damage_tick_timer = DAMAGE_APPLY_INTERVAL
        else:
            self.damage_tick_timer -= self.time_delta