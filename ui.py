from time import sleep
from typing import Optional
import pygame

from CONSTANTS import MAP_X
from controller import ActionEntry, ActionType, Controller, DisplayLocationType, InputAction
from entity import Team
from CONSTANTS import MAP_Y
from lane_visual_tests import coord2screen
from overlay_manager import WHITE, OverlayManager, OverlayType
from player import Player
from ui_utils import PLAYER_SIZE, renderState, screen2coord


class UI:
    def __init__(self) -> None:
        pygame.init()
        self.controller = Controller()
        self.overlay_manager = OverlayManager()
        self.clock = pygame.time.Clock()
        self.selected_player = None
        self.screen = pygame.display.set_mode((MAP_X, MAP_Y))
        self.run()

    def set_selected_player(self, player: Optional[Player]):
        self.selected_player = player

    def get_type_and_callback(self, action_entry: ActionEntry, player: Optional[Player] = None):
        if action_entry.type == ActionType.ATTACK_LANE_ENTITY:
            def callback(position):
                self.controller.apply_action(InputAction(source_entry=action_entry, player=player))
            type = OverlayType.ATTACK_LANE_ENTITY
        elif action_entry.type == ActionType.STOP_ATTACKING_LANE_ENTITY:
            def callback(position):
                self.controller.apply_action(InputAction(source_entry=action_entry, player=player))
            type = OverlayType.STOP_ATTACKING_LANE_ENTITY
        elif action_entry.type == ActionType.ENGAGE_COMBAT:
            def callback(position):
                self.controller.apply_action(InputAction(source_entry=action_entry, player=player))
            type = OverlayType.ENGAGE_COMBAT
        elif action_entry.type == ActionType.JOIN_COMBAT:
            def callback(position):
                self.controller.apply_action(InputAction(source_entry=action_entry, player=player))
            type = OverlayType.ENGAGE_COMBAT
        elif action_entry.type == ActionType.DISENGAGE_COMBAT:
            def callback(position):
                self.controller.apply_action(InputAction(source_entry=action_entry))
            type = OverlayType.DISENGAGE_COMBAT
        else:
            assert False, f"Action type {action_entry.type} is not handled here"
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
                boxes_center, 20,
                [self.get_type_and_callback(action_entry=a, player=player_actions.player) for a in on_player]
            )
        for map_position_action in available_actions.map_actions:
            type, callback = self.get_type_and_callback(map_position_action)
            position = coord2screen(map_position_action.display_location.position)
            self.overlay_manager.add_box(position, 20, type, callback)

    def step(self):
        running = True
        self.create_available_actions_overlay()
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
        self.controller.sim.step()

        self.screen.fill(WHITE)
        renderState(self.controller.sim.map, self.screen)
        self.overlay_manager.render_all(self.screen)
        pygame.display.flip()
        sleep(0.2)
        return running
    
    def run(self):
        while True:
            if not self.step():
                break
        pygame.quit()

if __name__ == "__main__":
    UI()