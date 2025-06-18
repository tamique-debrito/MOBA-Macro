from typing import Tuple

import pygame
from CONSTANTS import COMBAT_START_THRESHOLD, PRESENCE_THRESHOLD, RECALL_TIME
from MAP_CONSTANTS import BASE_CIRCLES, GET_MAP_LANE_POLYGONS, MAP_Y, SCREEN_X, SCREEN_Y
from entity import Entity, Team, Wave
from lane import SingleLaneSimulator, WaveWrapper
from player import Player
from sim import Map

pygame.init()


WAVE_SIZE = 7
PLAYER_SIZE = 10
TURRET_SIZE = 15

blue_team_color = (100,95,150)
red_team_color = (150,95,100)
combat_color = (255,100,255)
recall_color = (0,0,255)
health_bar_color = (255,0,0)
presence_radius_color = (0,255,0)
disengaging_combat_color = (200,200,200)

map_background_color = (150, 205, 150)
map_path_color = (250, 255, 150)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)



ACTION_SYMBOL_FONT = pygame.font.Font("seguisym.ttf", 16)
INFO_FONT = pygame.font.SysFont(None, 12)

WAVE_SYMBOL = pygame.font.Font("seguisym.ttf", WAVE_SIZE * 2).render("♟", True, BLACK)
PLAYER_SYMBOL = pygame.font.Font("seguisym.ttf", PLAYER_SIZE * 2).render("♛", True, BLACK)
TURRET_SYMBOL = pygame.font.Font("seguisym.ttf", TURRET_SIZE * 2).render("♜", True, BLACK)
BASE_SYMBOL = pygame.font.Font("seguisym.ttf", 32).render("♚", True, BLACK)

MAP_BACKGROUND = pygame.Surface((SCREEN_X, SCREEN_Y))
MAP_BACKGROUND.fill(map_background_color)

def init_map_bg():
    for poly in GET_MAP_LANE_POLYGONS():
        mapped_poly = [coord2screen(p) for p in poly]
        pygame.draw.polygon(MAP_BACKGROUND, map_path_color, mapped_poly)

    for base_circle in BASE_CIRCLES:
        c = coord2screen(base_circle[0])
        r = base_circle[1]
        pygame.draw.circle(MAP_BACKGROUND, map_path_color, center=c, radius=r)


def coord2screen(pos) -> Tuple[float, float]:
    x, y = pos
    return x, y + int(MAP_Y // 2)

def screen2coord(pos) -> Tuple[float, float]:
    x, y = pos
    return x, y - int(MAP_Y // 2)

def draw_resource_bar(screen, color, ent_x, ent_y, ent_size, proportion, index=0):
    bar_len = proportion * ent_size * 2
    bar_x = ent_x - ent_size
    bar_y = ent_y - ent_size - 5 - index * 3
    pygame.draw.line(screen, color, (bar_x, bar_y), (bar_x + bar_len, bar_y), 2)
    
    # font = pygame.font.SysFont(None, 12)
    # text = font.render(f"{int(proportion * 100)}%", True, BLACK)
    # screen.blit(text, (ent_x - ent_size, bar_y - 9))

def renderLane(lane: SingleLaneSimulator, screen):
    for wrapper in lane.get_all_wrappers():
        draw_entity_base(wrapper.entity, screen)

def draw_entity_base(entity: Entity, screen):
        ent_size = PLAYER_SIZE if isinstance(entity, Player) else (WAVE_SIZE if isinstance(entity, Wave) else TURRET_SIZE)
        ent_x, ent_y = coord2screen(entity.position)
        color_to_use = blue_team_color if entity.team == Team.BLUE else red_team_color
        symbol_to_use = PLAYER_SYMBOL if isinstance(entity, Player) else (WAVE_SYMBOL if isinstance(entity, Wave) else TURRET_SYMBOL)
        pygame.draw.circle(screen, color_to_use, (ent_x, ent_y), float(ent_size))
        pygame.draw.circle(screen, BLACK, (ent_x, ent_y), float(ent_size) + 2, 3)
        symbol_rect = symbol_to_use.get_rect(center=(ent_x, ent_y))
        screen.blit(symbol_to_use, symbol_rect)
        draw_resource_bar(screen, health_bar_color, ent_x, ent_y, ent_size, entity.get_health() / entity.get_max_health())
        return ent_x, ent_y, ent_size


def renderState(map: Map, screen):
    screen.blit(MAP_BACKGROUND, (0, 0))
    for lane in map.lanes.lanes:
      renderLane(map.lanes.lanes[lane], screen)

    for player in map.get_players():
        if not player.is_alive():
            continue
        
        ent_x, ent_y, ent_size = draw_entity_base(player, screen)

        pygame.draw.circle(screen, presence_radius_color, (ent_x, ent_y), float(PRESENCE_THRESHOLD), 1) # presence radius
        if player.recall_timer is not None:
            draw_resource_bar(screen, recall_color, ent_x, ent_y, ent_size, player.recall_timer / RECALL_TIME, index=1)
    
        more_info = f"Player <{player.player_id}>"
        more_info = more_info + "\nitems=" + ", ".join([i.name for i in player.inventory.items])
        more_info = more_info + f"\ngold={int(player.inventory.gold)}, level={player.stats.leveled.level}"
        text = INFO_FONT.render(more_info, True, BLACK)
        screen.blit(text, (ent_x - len(more_info) * 2, ent_y + ent_size + 8))

    for combat in map.combats:
        c = coord2screen(combat.position)
        pygame.draw.circle(screen, combat_color if not combat.disengage_counter else disengaging_combat_color, c, float(COMBAT_START_THRESHOLD), 4)

init_map_bg()