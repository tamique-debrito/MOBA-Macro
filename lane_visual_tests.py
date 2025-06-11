from time import sleep
import pygame

from entity import Team, Turret, Wave
from lane import SingleLaneSimulator, WaveWrapper

background_colour = (255,255,255)
blue_team_color = (100,95,150)
red_team_color = (150,95,100)


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

def renderState(lane: SingleLaneSimulator, screen):
   screen.fill(background_colour)
   for wrapper in lane.get_all_wrappers():
        ent_size = 10 if isinstance(wrapper, WaveWrapper) else 20
        ent_x, ent_y = coord2screen(wrapper.entity.position)
        health_y = ent_y - ent_size - 5
        health_len = wrapper.entity.health / wrapper.entity.max_health * ent_size
        color_to_use = blue_team_color if wrapper.entity.team == Team.BLUE else red_team_color
        pygame.draw.circle(screen,color_to_use, (ent_x, ent_y), float(ent_size))
        pygame.draw.line(screen, blue_team_color, (ent_x - ent_size, health_y), (ent_x + health_len, health_y), 3)
    
   pygame.display.flip()

def remove_dead(lane: SingleLaneSimulator):
    for w in lane.get_all_wrappers():
        if not w.entity.is_alive():
            lane.remove_wrapper(w)

def lane_test_basic():
   screen = setupScreen("lane test basic")
   lane = SingleLaneSimulator([(0, 0), (500, 0)])
   lane.add_wave(Wave((0, 0), 100, 5, 10, Team.BLUE))
   lane.add_wave(Wave((0, 0), 150, 5, 20, Team.RED))
   for i in range(400):
        lane.step(i)
        renderState(lane, screen)
        sleep(0.25)
        remove_dead(lane)

def lane_test_combine_wave():
    screen = setupScreen("lane test combine wave")
    lane = SingleLaneSimulator([(0, 0), (500, 0)])
    lane.add_wave(Wave((0, 0), 150, 5, 20, Team.RED))
    for i in range(300):
        if i % 25 == 0 and i < 100: 
            lane.add_wave(Wave((0, 0), 100, 5, 10, Team.BLUE))
        lane.step(i)
        renderState(lane, screen)
        sleep(0.25)
        remove_dead(lane)


def lane_test_basic_turret():
    screen = setupScreen("lane test combine wave")
    lane = SingleLaneSimulator([(0, 0), (500, 0)])
    lane.add_wave(Wave((0, 0), 150, 5, 20, Team.RED))
    lane.add_turret(Turret((250, 0), 500, 50, Team.BLUE))
    for i in range(300):
        if i % 25 == 0 and i < 100: 
            lane.add_wave(Wave((0, 0), 100, 5, 10, Team.RED))
        lane.step(i)
        renderState(lane, screen)
        sleep(0.1)
        remove_dead(lane)

def lane_test_turret_overrun():
    screen = setupScreen("lane test combine wave")
    lane = SingleLaneSimulator([(0, 0), (500, 0)])
    lane.add_wave(Wave((0, 0), 150, 5, 20, Team.RED))
    lane.add_turret(Turret((250, 0), 500, 50, Team.BLUE))
    for i in range(300):
        if i % 5 == 0 and i < 100: 
            lane.add_wave(Wave((0, 0), 100, 5, 10, Team.RED))
        lane.step(i)
        renderState(lane, screen)
        sleep(0.1)
        remove_dead(lane)

if __name__ == "__main__":
    lane_test_turret_overrun()