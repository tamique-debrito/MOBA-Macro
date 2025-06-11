"""
This class represents the actions that may be taken by the human or AI controller for each team
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple
from CONSTANTS import COMBAT_THRESHOLD
from combat import Combat
from entity import EntityState, LaneEntity
from player import Player
from sim import Simulator

class ActionType(Enum):
    MOVE_TO_LOCATION = "MOVE_TO_LOCATION"
    ATTACK_LANE_ENTITY = "ATTACK_LANE_ENTITY"
    STOP_ATTACKING_LANE_ENTITY = "STOP_ATTACKING_LANE_ENTITY"
    ENGAGE_COMBAT = "ENGAGE_COMBAT"
    JOIN_COMBAT = "JOIN_COMBAT"
    DISENGAGE_COMBAT = "DISENGAGE_COMBAT"

class DisplayLocationType(Enum):
    MAP_POSITION = 1
    ON_PLAYER = 1
    DASH = 2
    CURSOR = 3

@dataclass
class DisplayLocation:
    type: DisplayLocationType
    position: Optional[Tuple[float, float]] = None

@dataclass
class ActionEntry:
    type: ActionType
    display_location: DisplayLocation = field(init=False)
    combat: Optional[Combat] = None

    def __post_init__(self):
        if self.type in [ActionType.ATTACK_LANE_ENTITY, ActionType.STOP_ATTACKING_LANE_ENTITY, ActionType.ENGAGE_COMBAT]:
            self.display_location = DisplayLocation(DisplayLocationType.ON_PLAYER)
        elif self.type in [ActionType.MOVE_TO_LOCATION]:
            self.display_location = DisplayLocation(DisplayLocationType.CURSOR)
        elif self.type in [ActionType.DISENGAGE_COMBAT]:
            assert self.combat
            self.display_location = DisplayLocation(DisplayLocationType.MAP_POSITION, self.combat.position)

@dataclass
class PlayerActionList:
    # Actions that display next to each other in the UI
    player: Player
    actions: list[ActionEntry]
    
@dataclass
class InputAction:
    source_entry: ActionEntry
    player: Optional[Player] = None
    position: Optional[Tuple[float, float]] = None

@dataclass
class AvailableActions:
    player_actions: list[PlayerActionList]
    map_actions: list[ActionEntry]

class Controller:
    def __init__(self) -> None:
        self.sim = Simulator()
    
    def get_all_available_actions(self):
        all_available = AvailableActions([], [])
        for p in self.sim.map.players:
            available = self.get_available_player_actions(p)
            if available is not None:
                all_available.player_actions.append(available)
        
        for combat in self.sim.map.combats:
            if combat.disengage_counter is not None:
                continue
            all_available.map_actions.append(ActionEntry(combat=combat, type=ActionType.DISENGAGE_COMBAT))
        
        return all_available

    def get_available_player_actions(self, player: Player):
        entities = self.sim.map.find_entities_in_range(player.position, COMBAT_THRESHOLD, team=player.team.enemy())
        combat_in_range = self.sim.map.find_combat_in_range(player)
        if player.state == EntityState.DEAD:
            return None
        actions = []
        if player.state != EntityState.COMBAT and any([isinstance(e, Player) and e.state != Combat for e in entities]):
            actions.append(ActionEntry(ActionType.ENGAGE_COMBAT))
        if player.state != EntityState.COMBAT and combat_in_range is not None:
            actions.append(ActionEntry(ActionType.JOIN_COMBAT, combat=combat_in_range))
        if player.state != EntityState.COMBAT and player.attacking is None and any([isinstance(e, LaneEntity) for e in entities]):
            actions.append(ActionEntry(ActionType.ATTACK_LANE_ENTITY))
        if player.state != EntityState.COMBAT and player.attacking is not None:
            actions.append(ActionEntry(ActionType.STOP_ATTACKING_LANE_ENTITY))
        if player.state == EntityState.NORMAL:
            actions.append(ActionEntry(ActionType.MOVE_TO_LOCATION))
        return PlayerActionList(player=player, actions=actions)

    def apply_action(self, action: InputAction):
        if action.source_entry.type == ActionType.MOVE_TO_LOCATION:
            assert action.position is not None, "Tried to move to location without location specified"
            assert action.player is not None, "Tried to move to location without player specified"
            action.player.set_path_target(action.position)
        elif action.source_entry.type == ActionType.ENGAGE_COMBAT:
            assert action.player is not None, "Tried to start combat without player specified"
            self.sim.map.start_combat_at_location(action.player.position)
        elif action.source_entry.type == ActionType.JOIN_COMBAT:
            assert action.player is not None, "Tried to join combat without player specified"
            assert action.source_entry.combat is not None, "Tried to join combat without target combat specified"
            self.sim.map.join_combat(action.player, action.source_entry.combat)
        elif action.source_entry.type == ActionType.ATTACK_LANE_ENTITY:
            assert action.player is not None, "Tried to attack lane entity without player specified"
            self.sim.map.attack_enemy_lane_entity_in_range(action.player)
        elif action.source_entry.type == ActionType.STOP_ATTACKING_LANE_ENTITY:
            assert action.player is not None, "Tried to stop attacking lane entity without player specified"
            action.player.set_attacking(None)
        elif action.source_entry.type == ActionType.DISENGAGE_COMBAT:
            assert action.source_entry.combat is not None, "Tried to start disengage combat without combat specified"
            action.source_entry.combat.start_disengage()
        else:
            assert False, "Unknown action type specified"