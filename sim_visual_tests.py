from time import sleep
import pygame

from CONSTANTS import COMBAT_START_THRESHOLD
from entity import Path, Team, Turret, Wave
from lane import LaneSimulator, SingleLaneSimulator, WaveWrapper
from player import Player
from sim import Map, Simulator

background_colour = (255,255,255)
blue_team_color = (100,95,150)
red_team_color = (150,95,100)
combat_color = (255,100,255)
disengaging_combat_color = (200,200,200)

(width, height) = (500, 500)

def coord2screen(pos):
  x, y = pos
  return x, y + 250

def setupScreen(test_name):
  screen = pygame.display.set_mode((width, height))
  pygame.display.set_caption(f'Test - {test_name}')
  screen.fill(background_colour)
  pygame.display.flip()
  return screen

def renderLane(lane: SingleLaneSimulator, screen):
  for wrapper in lane.get_all_wrappers():
    ent_size = 10 if isinstance(wrapper, WaveWrapper) else 20
    ent_x, ent_y = coord2screen(wrapper.entity.position)
    health_y = ent_y - ent_size - 5
    health_len = wrapper.entity.health / wrapper.entity.max_health * ent_size
    color_to_use = blue_team_color if wrapper.entity.team == Team.BLUE else red_team_color
    pygame.draw.circle(screen,color_to_use, (ent_x, ent_y), float(ent_size))
    pygame.draw.line(screen, blue_team_color, (ent_x - ent_size, health_y), (ent_x + health_len, health_y), 3)
  

def renderState(map: Map, screen):
  screen.fill(background_colour)
  for lane in map.lanes.lanes:
      renderLane(map.lanes.lanes[lane], screen)
  
  for player in map.get_players():
    if not player.is_alive():
      continue
    ent_size = 15
    ent_x, ent_y = coord2screen(player.position)
    health_y = ent_y - ent_size - 5
    health_len = player.health / player.max_health * ent_size
    color_to_use = blue_team_color if player.team == Team.BLUE else red_team_color
    pygame.draw.circle(screen,color_to_use, (ent_x, ent_y), float(ent_size))
    pygame.draw.line(screen, blue_team_color, (ent_x - ent_size, health_y), (ent_x + health_len, health_y), 3)
  
  for combat in map.combats:
    c = coord2screen(combat.position)
    pygame.draw.circle(screen, combat_color if not combat.disengage_counter else disengaging_combat_color, c, float(COMBAT_START_THRESHOLD), 4)

  pygame.display.flip()

def remove_dead(lanes: LaneSimulator):
  for l in lanes.lanes:
    lane = lanes.lanes[l]
    for w in lane.get_all_wrappers():
        if not w.entity.is_alive():
            lane.remove_wrapper(w)

def sim_test_basic():
  screen = setupScreen("sim test basic")
  sim = Simulator()
  for i in range(400):
    sim.step()
    renderState(sim.map, screen)
    remove_dead(sim.map.lanes)
    sleep(0.25)

def sim_test_player_attack():
  screen = setupScreen("sim test player attack")
  sim = Simulator()
  player: Player = sim.map.get_players()[0]
  player.path = Path((240, 0))
  for i in range(400):
    sim.map.attack_enemy_lane_entity_in_range(player)
    sim.step()
    renderState(sim.map, screen)
    remove_dead(sim.map.lanes)
    sleep(0.25)

def sim_test_player_combat():
  screen = setupScreen("sim test player combat 1")
  sim = Simulator()
  player1: Player = sim.map.get_players()[0]
  player2: Player = sim.map.get_players()[3]
  player1.path = Path((240, 50))
  player2.path = Path((240, 50))
  for i in range(400):
    sim.map.start_combat_at_location((240, 50))
    sim.step()
    renderState(sim.map, screen)
    remove_dead(sim.map.lanes)
    sleep(0.25)
  
def sim_test_player_combat2():
  screen = setupScreen("sim test player combat 2")
  sim = Simulator()
  player1: Player = sim.map.get_players()[0]
  player2: Player = sim.map.get_players()[3]
  player1.path = Path((240, 50))
  player2.path = Path((240, 50))
  for i in range(400):
    if i == 15:
      sim.map.get_players()[1].path = Path((240, 50))
      sim.map.get_players()[2].path = Path((240, 50))
    sim.map.start_combat_at_location((240, 50))
    if len(sim.map.combats) > 0:
      sim.map.join_combat(sim.map.get_players()[1], sim.map.combats[0])
      sim.map.join_combat(sim.map.get_players()[2], sim.map.combats[0])
    sim.step()
    renderState(sim.map, screen)
    remove_dead(sim.map.lanes)
    sleep(0.05)
  
def sim_test_player_disengage_combat():
  screen = setupScreen("sim test player disengage combat")
  sim = Simulator()
  player1: Player = sim.map.get_players()[0]
  player2: Player = sim.map.get_players()[3]
  player1.path = Path((240, 50))
  player2.path = Path((240, 50))
  disengaged = False
  for i in range(400):
    
    if len(sim.map.combats) == 0:
      if not disengaged:
        sim.map.start_combat_at_location((240, 50))
    elif sim.map.combats[0].steps_run > 10:
        sim.map.combats[0].start_disengage()
        disengaged = True
    sim.step()
    renderState(sim.map, screen)
    remove_dead(sim.map.lanes)
    sleep(0.05)

if __name__ == "__main__":
    sim_test_player_disengage_combat()