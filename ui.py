from time import sleep
from typing import Optional
import pygame

from CONSTANTS import MAP_X, SCREEN_X, SCREEN_Y
from controller import ActionEntry, ActionType, Controller, DisplayLocationType, InputAction
from entity import Team
from CONSTANTS import MAP_Y
from game_tree import GameTree, GameTreeAction, GameTreeActionType
from overlay_manager import OverlayManager, OverlayType
from player import Player
from ui_utils import PLAYER_SIZE, WHITE, renderState, screen2coord, coord2screen


class UI:
    def __init__(self, use_game_tree=False) -> None:
        pygame.init()
        self.controller = Controller()
        self.overlay_manager = OverlayManager()
        self.clock = pygame.time.Clock()
        self.selected_player = None
        self.screen = pygame.display.set_mode((SCREEN_X, SCREEN_Y))
        self.game_tree = GameTree(self.controller.sim) if use_game_tree else None
        self.paused = False
        self.run()

    def set_selected_player(self, player: Optional[Player]):
        self.selected_player = player

    def get_type_and_callback_game_actions(self, action_entry: ActionEntry, player: Optional[Player] = None):
        def callback(position):
            self.controller.apply_action(InputAction(source_entry=action_entry, player=player, position=position))
        if action_entry.type == ActionType.ATTACK_LANE_ENTITY:
            type = OverlayType.ATTACK_LANE_ENTITY
        elif action_entry.type == ActionType.START_RECALL:
            type = OverlayType.START_RECALL
        elif action_entry.type == ActionType.STOP_RECALL:
            type = OverlayType.STOP_RECALL
        elif action_entry.type == ActionType.STOP_ATTACKING_LANE_ENTITY:
            type = OverlayType.STOP_ATTACKING_LANE_ENTITY
        elif action_entry.type == ActionType.ENGAGE_COMBAT:
            type = OverlayType.ENGAGE_COMBAT
        elif action_entry.type == ActionType.JOIN_COMBAT:
            type = OverlayType.JOIN_COMBAT
        elif action_entry.type == ActionType.DISENGAGE_COMBAT:
            type = OverlayType.DISENGAGE_COMBAT
        elif action_entry.type == ActionType.BUY_ITEM:
            type = OverlayType.BUY_ITEM
        else:
            assert False, f"Action type {action_entry.type} is not mapped here"
        return type, callback

    def get_type_and_callback_game_tree_actions(self, action: GameTreeAction):
        if action.action_type == GameTreeActionType.ADD_NODE:
            type = OverlayType.ADD_NODE
        elif action.action_type == GameTreeActionType.UP_TREE:
            type = OverlayType.UP_TREE
        elif action.action_type == GameTreeActionType.DOWN_TREE:
            type = OverlayType.DOWN_TREE
        elif action.action_type == GameTreeActionType.RESET_NODE:
            type = OverlayType.RESET_NODE
        else:
            assert False, f"Action type {action.action_type} is not mapped here"
        
        def callback(position):
            new_sim = action.callback(self.controller.sim)
            self.controller.sim = new_sim # The callback from the action will return the current simulator state to use, so that needs to be set into the controller
        
        return type, callback
    
    def create_available_actions_overlay(self):
        self.overlay_manager.clear()
        for player in self.controller.sim.map.players:
            position = coord2screen(player.position)
            callback = lambda position, p=player: self.set_selected_player(p)
            self.overlay_manager.add_circle(position=position, radius=PLAYER_SIZE, item_type=OverlayType.SELECT_PLAYER, callback=callback)
        available_actions = self.controller.get_all_available_actions()
        for player_actions in available_actions.player_actions:
            on_player = [a for a in player_actions.actions if a.display_location.type == DisplayLocationType.ON_PLAYER]
            #on_dash = [a for a in player_actions.actions if a.display_location.type == DisplayLocationType.DASH]
            boxes_center = coord2screen(player_actions.player.position)
            boxes_center = (boxes_center[0], boxes_center[1] + 25)
            self.overlay_manager.add_multiple_boxes(
                boxes_center,
                [self.get_type_and_callback_game_actions(action_entry=a, player=player_actions.player) for a in on_player]
            )
        for map_position_action in available_actions.map_actions:
            type, callback = self.get_type_and_callback_game_actions(map_position_action)
            if map_position_action.display_location.type == DisplayLocationType.DASH:
                position = "on_dash"
            else:
                position = coord2screen(map_position_action.display_location.position)
            self.overlay_manager.add_box(position, type, callback)
        if self.game_tree is not None:
            for game_tree_action in self.game_tree.get_available_actions():
                type, callback = self.get_type_and_callback_game_tree_actions(game_tree_action)
                self.overlay_manager.add_box("on_dash", type, callback)
    
        if not self.paused:
            self.overlay_manager.add_box("on_dash", OverlayType.PAUSE, lambda pos: self.pause())
        else:
            self.overlay_manager.add_box("on_dash", OverlayType.RESUME, lambda pos: self.resume())


    def pause(self):
        self.paused = True
    
    def resume(self):
        self.paused = False

    def step(self):
        running = True
        self.create_available_actions_overlay()
        self.overlay_manager.consolidate()
        for event in pygame.event.get():
            hit_box = False
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                hit_box = self.overlay_manager.handle_click(event.pos)
                if not hit_box and self.selected_player is not None:
                    remapped = screen2coord(event.pos)
                    self.selected_player.set_path_target(remapped)
                    self.set_selected_player(None)

        if not self.paused:
            self.controller.sim.step()

        self.screen.fill(WHITE)
        renderState(self.controller.sim.map, self.screen)
        self.overlay_manager.render_all(self.screen, [
            f"Sim step = {self.controller.sim.sim_step}",
            f"current game tree node: {None if self.game_tree is None else self.game_tree.cur_node.id}",
            f"current game tree sim_step: {None if self.game_tree is None else self.game_tree.cur_node.sim.sim_step}",
        ])
        pygame.display.flip()
        sleep(0.02)
        return running
    
    def run(self):
        while True:
            if not self.step():
                break
        pygame.quit()

if __name__ == "__main__":
    UI(use_game_tree=True)

