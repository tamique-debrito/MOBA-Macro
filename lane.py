from __future__ import annotations
from enum import Enum
from math import dist
from typing import List, Optional, Sequence, Tuple

from CONSTANTS import COMBAT_START_THRESHOLD, MAP_X, MAP_Y, SIM_STEPS_PER_SECOND, WAVE_COMBINE_THRESHOLD
from entity import Entity, LaneEntity, Wave, EntityState, Team, Turret, Wave
from player import Player

FIRST_TOWER_DX, FIRST_TOWER_DY = 25, MAP_Y / 5

SECOND_TOWER_DX, SECOND_TOWER_DY = MAP_X / 3, MAP_Y / 3

WAVE_SPAWN_INTERVAL = 100


class Lane(Enum):
    TOP = 1
    MID = 2
    BOTTOM = 3

class LaneEntityWrapper:
    entity: LaneEntity
    attacking: Optional[LaneEntity]
    def __init__(self, entity) -> None:
        self.entity = entity
        self.attacking = None

    def run_attack_step(self, is_damage_tick):
        assert self.attacking is not None, "Tried to run attack when not attacking"
        if not is_damage_tick:
            return
        self.attacking.take_damage(self.entity.get_damage())
    
    def clear_attacking(self):
        self.attacking = None

    def set_attacking(self, attacking):
        if self.attacking is None:
            self.attacking = attacking
        elif isinstance(self.attacking, Wave): # If we are already attacking a turret, do not override. This encodes that turrets have higher priority
            self.attacking = attacking

    def __repr__(self):
        return (f"entity={self.entity})")

class WaveWrapper(LaneEntityWrapper):
    entity: Wave
    def __init__(self, wave: Wave):
        super().__init__(wave)
        self.segment_number = 0
        self.distance_along_segment = 0.0
        self.overall_distance = 0.0

    def increment_distance(self, time_delta, current_seg_len):
        # Returns True if the distance update cause a move to the next segment
        # Note that distance deltas will never be enough to traverse multiple segments
        dist = self.entity.get_speed() * time_delta
        new_dist = self.distance_along_segment + dist
        self.overall_distance += dist
        if new_dist > current_seg_len:
            self.segment_number += 1
            self.distance_along_segment = new_dist - current_seg_len
            return True
        else:
            self.distance_along_segment = new_dist
            return False

    def combine_from(self, other: WaveWrapper):
        # This is a bit of a hacky way of combining because it assumes that waves will not recalculate their stats
        self.entity.stats.effective = self.entity.stats.effective + other.entity.stats.effective
        self.entity.stats.health += other.entity.stats.health
        other.entity.set_state(EntityState.DEAD) # Mark as dead so it gets cleaned up
        # For now assume same damage, other attributes

class TurretWrapper(LaneEntityWrapper):
    entity: Turret
    def __init__(self, entity) -> None:
        super().__init__(entity)

class SingleLaneSimulator:
    def __init__(self, lane_points: List[Tuple[float, float]], players: Sequence[Player], on_remove_callback):
        self.players = players
        self.points = lane_points
        self.on_remove_callback = on_remove_callback
        self.lengths, self.deltas = self._compute_path_info()
        self.overall_length = sum(self.lengths)
        self.waves: List[WaveWrapper] = []
        self.last_seg_index = len(self.lengths) - 1
        self.waves_by_team: dict[Team, list[WaveWrapper]] = {
            Team.RED: [],
            Team.BLUE: [],
        }
        self.all_by_team: dict[Team, list[LaneEntityWrapper]] = {
            Team.RED: [],
            Team.BLUE: [],
        }

    def _compute_path_info(self):
        lengths = []
        deltas = []
        for i in range(len(self.points) - 1):
            p1, p2 = self.points[i], self.points[i + 1]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            length = (dx**2 + dy**2)**0.5
            lengths.append(length)
            deltas.append((dx / length, dy / length))
        return lengths, deltas

    def add_wave(self, wave: Wave):
        wrapper = WaveWrapper(wave)
        self.move_wave(0, wrapper) # This initializes the position
        self.waves.append(wrapper)
        self.waves_by_team[wrapper.entity.team].append(wrapper)
        self.all_by_team[wrapper.entity.team].append(wrapper)

    def add_turret(self, turret: Turret):
        wrapper = TurretWrapper(turret)
        self.all_by_team[wrapper.entity.team].append(wrapper)

    def remove_entity(self, e: Entity):
        to_remove = None
        for w in self.get_all_wrappers():
            if w.entity == e:
                to_remove = w
                break
        if to_remove is not None:
            self.remove_wrapper(w)

    def remove_wrapper(self, wrapper: LaneEntityWrapper):
        if isinstance(wrapper, WaveWrapper):
            self.waves.remove(wrapper)
            self.waves_by_team[wrapper.entity.team].remove(wrapper)
        self.all_by_team[wrapper.entity.team].remove(wrapper)
        self.on_remove_callback(wrapper.entity)

    def get_seg_info_for_wave(self, wave_wrapper: WaveWrapper):
        # Get segment info accounting for the fact that team determines direction
        if wave_wrapper.entity.team == Team.RED:
            idx = self.last_seg_index - wave_wrapper.segment_number
            point_index = idx + 1
            delta_sgn = -1
        else:
            idx = wave_wrapper.segment_number
            point_index = idx
            delta_sgn = 1

        delta = (self.deltas[idx][0] * delta_sgn, self.deltas[idx][1] * delta_sgn)

        return self.lengths[idx], delta, point_index

    def move_wave(self, time_delta: float, wave_wrapper: WaveWrapper):
        seg_len, seg_delta, point_index = self.get_seg_info_for_wave(wave_wrapper)
        new_seg = wave_wrapper.increment_distance(time_delta, seg_len)
        if not new_seg:
            point = self.points[point_index]
            new_pos = (point[0] + seg_delta[0] * wave_wrapper.distance_along_segment, point[1] + seg_delta[1] * wave_wrapper.distance_along_segment)
            wave_wrapper.entity.set_pos(new_pos)

    def combine_waves(self, sim_step):
        if sim_step % 5 != 0: # Run this only periodically for efficiency
            return
        to_combine: list[Tuple[WaveWrapper, WaveWrapper]] = []
        for team in self.waves_by_team:
            for wave1, wave2 in zip(self.waves_by_team[team], self.waves_by_team[team][1:]):
                if abs(wave1.overall_distance - wave2.overall_distance) <= WAVE_COMBINE_THRESHOLD:
                    to_combine.append((wave1, wave2))
                    break
        for w1, w2 in to_combine:
            w1.combine_from(w2) # Assume that the first one is further along and should be combined into
            self.remove_wrapper(w2)

    def set_attacking(self):
        for w in self.get_all_wrappers():
            w.clear_attacking()
        for w1 in self.all_by_team[Team.RED]:
            for w2 in self.all_by_team[Team.BLUE]:
                if w1.entity.distance_to_entity(w2.entity) <= COMBAT_START_THRESHOLD:
                    w1.set_attacking(w2.entity)
                    w2.set_attacking(w1.entity)
        for w in self.get_all_wrappers():
            # If any lane entities are not attacking and can attack a player, they should
            if w.attacking is not None:
                continue
            for player in self.players:
                if player.team == w.entity.team.enemy() and w.entity.distance_to_entity(player) <= COMBAT_START_THRESHOLD:
                    w.set_attacking(player)

    def step(self, time_delta, is_damage_tick, sim_step):
        """
        Move each wave along the lane segments for one simulation step.
        """
        self.combine_waves(sim_step)
        self.set_attacking()

        for wrapper in self.get_all_wrappers():
            if wrapper.entity._state == EntityState.COMBAT:
                continue # Don't process entities that are in regular combat
            if isinstance(wrapper, WaveWrapper) and wrapper.segment_number > self.last_seg_index:
                #self.waves.remove(wave_wrapper)
                continue # Don't process waves that have reached the end
            if wrapper.attacking is not None:
                wrapper.run_attack_step(is_damage_tick)
            elif isinstance(wrapper, WaveWrapper):
                self.move_wave(time_delta, wrapper)

    def get_all_wrappers(self):
        return self.all_by_team[Team.BLUE] + self.all_by_team[Team.RED]

    def remove_dead(self):
        for w in self.get_all_wrappers():
            if not w.entity.is_alive():
                self.remove_wrapper(w)

    def __repr__(self) -> str:
        return f"{[repr(wave) for wave in self.waves]}"

class LaneSimulator:
    # Simulates all three lanes
    def __init__(self, add_entity_callback, players: Sequence[Player], on_remove_callback):
        self.lanes: dict[Lane, SingleLaneSimulator] = {
            Lane.TOP: SingleLaneSimulator([ (FIRST_TOWER_DX, FIRST_TOWER_DY), (MAP_X / 2, SECOND_TOWER_DY), (MAP_X - FIRST_TOWER_DX, FIRST_TOWER_DY) ], players, on_remove_callback),
            Lane.MID: SingleLaneSimulator([ (FIRST_TOWER_DX, 0), (MAP_X - FIRST_TOWER_DX, 0) ], players, on_remove_callback),
            Lane.BOTTOM: SingleLaneSimulator([ (FIRST_TOWER_DX, -FIRST_TOWER_DY), (MAP_X / 2, -SECOND_TOWER_DY), (MAP_X - FIRST_TOWER_DX, -FIRST_TOWER_DY) ], players, on_remove_callback)
        }
        self.spawn_interval_sim_steps = WAVE_SPAWN_INTERVAL * SIM_STEPS_PER_SECOND
        self.wave_num = 0
        self.add_entity_callback = add_entity_callback

        self.add_turrets()


    def add_turrets(self):
        turrets = {
            Team.BLUE : {
                Lane.TOP: [(FIRST_TOWER_DX, FIRST_TOWER_DY), (SECOND_TOWER_DX, SECOND_TOWER_DY)],
                Lane.MID: [(FIRST_TOWER_DX, 0), (SECOND_TOWER_DX, 0)],
                Lane.BOTTOM: [(FIRST_TOWER_DX, -FIRST_TOWER_DY), (SECOND_TOWER_DX, -SECOND_TOWER_DY)]
            },
            Team.RED: { 
                Lane.TOP: [(MAP_X - FIRST_TOWER_DX, FIRST_TOWER_DY), (MAP_X - SECOND_TOWER_DX, SECOND_TOWER_DY)],
                Lane.MID: [(MAP_X - FIRST_TOWER_DX, 0), (MAP_X - SECOND_TOWER_DX, 0)],
                Lane.BOTTOM: [(MAP_X - FIRST_TOWER_DX, -FIRST_TOWER_DY), (MAP_X - SECOND_TOWER_DX, -SECOND_TOWER_DY)],        
            }
        }
        for team in turrets:
            for lane in turrets[team]:
                for pos in turrets[team][lane]:
                    self.add_turret(Turret.default_turret(pos, team), lane)
    
    def remove_entity(self, entity):
        for lane in self.lanes:
            self.lanes[lane].remove_entity(entity)
    
    def add_turret(self, turret: Turret, lane: Lane):
        self.add_entity_callback(turret)
        self.lanes[lane].add_turret(turret)

    def add_wave(self, wave: Wave, lane: Lane):
        self.add_entity_callback(wave)
        self.lanes[lane].add_wave(wave)
    
    def step(self, time_delta, sim_time, is_damage_tick, sim_step):
        self.spawn_waves(sim_step)
        for lane in self.lanes:
            self.lanes[lane].step(time_delta, sim_time, is_damage_tick)

    def spawn_waves(self, sim_time):
        if sim_time % self.spawn_interval_sim_steps == 0:
            for lane in self.lanes:
                self.add_wave(Wave.default_wave(self.wave_num, Team.BLUE), lane)
                self.add_wave(Wave.default_wave(self.wave_num, Team.RED), lane)
            self.wave_num += 1