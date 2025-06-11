from typing import Tuple

import pygame
from CONSTANTS import COMBAT_THRESHOLD
from entity import Team
from lane import SingleLaneSimulator, WaveWrapper
from sim import Map


WAVE_SIZE = 7
PLAYER_SIZE = 11
TURRET_SIZE = 15
blue_team_color = (100,95,150)
red_team_color = (150,95,100)
combat_color = (255,100,255)
disengaging_combat_color = (200,200,200)

def coord2screen(pos) -> Tuple[float, float]:
  x, y = pos
  return x, y + 250

def screen2coord(pos) -> Tuple[float, float]:
  x, y = pos
  return x, y - 250

def renderLane(lane: SingleLaneSimulator, screen):
    for wrapper in lane.get_all_wrappers():
        ent_size = WAVE_SIZE if isinstance(wrapper, WaveWrapper) else TURRET_SIZE
        ent_x, ent_y = coord2screen(wrapper.entity.position)
        health_y = ent_y - ent_size - 5
        health_len = wrapper.entity.health / wrapper.entity.max_health * ent_size
        color_to_use = blue_team_color if wrapper.entity.team == Team.BLUE else red_team_color
        pygame.draw.circle(screen,color_to_use, (ent_x, ent_y), float(ent_size))
        pygame.draw.line(screen, blue_team_color, (ent_x - ent_size, health_y), (ent_x + health_len, health_y), 3)

def renderState(map: Map, screen):
  for lane in map.lanes.lanes:
      renderLane(map.lanes.lanes[lane], screen)
  
  for player in map.get_players():
    if not player.is_alive():
      continue
    ent_size = PLAYER_SIZE
    ent_x, ent_y = coord2screen(player.position)
    health_y = ent_y - ent_size - 5
    health_len = player.health / player.max_health * ent_size
    color_to_use = blue_team_color if player.team == Team.BLUE else red_team_color
    pygame.draw.circle(screen,color_to_use, (ent_x, ent_y), float(ent_size))
    pygame.draw.line(screen, blue_team_color, (ent_x - ent_size, health_y), (ent_x + health_len, health_y), 3)
  
  for combat in map.combats:
    c = coord2screen(combat.position)
    pygame.draw.circle(screen, combat_color if not combat.disengage_counter else disengaging_combat_color, c, float(COMBAT_THRESHOLD), 4)
