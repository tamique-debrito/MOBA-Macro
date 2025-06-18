from operator import le
from typing import Tuple, Union

# Dimensions
MAP_Y: int = 750
MAP_X: int = 750
MAP_HALF_X: float = MAP_X / 2

DASH_START_Y: int = MAP_Y
DASH_HEIGHT: int = 40

SCREEN_X: int = MAP_X
SCREEN_Y: int = MAP_Y + DASH_HEIGHT

COORD_LIST = list[Tuple[Union[int, float], Union[int, float]]]

FIRST_TOWER_DX, FIRST_TOWER_DY = MAP_HALF_X * 0.2, MAP_Y / 5

SECOND_TOWER_DX, SECOND_TOWER_DY = MAP_HALF_X * 0.5 , MAP_Y * 0.35

THIRD_TOWER_DX, THIRD_TOWER_DY = MAP_HALF_X * 0.8, MAP_Y * 0.4

MIDPOINT_DY = THIRD_TOWER_DY

TOWER_BASE_POINTS = [(FIRST_TOWER_DX, FIRST_TOWER_DY), (SECOND_TOWER_DX, SECOND_TOWER_DY), (THIRD_TOWER_DX, THIRD_TOWER_DY)]

SIDE_LANE_POINTS: COORD_LIST = TOWER_BASE_POINTS + [(MAP_HALF_X, MIDPOINT_DY)] + [(MAP_X - p[0], p[1]) for p in reversed(TOWER_BASE_POINTS)]

TOP_LANE_POINTS = SIDE_LANE_POINTS
MID_LAND_POINTS = [(p[0], 0) for p in SIDE_LANE_POINTS]
BOT_LANE_POINTS = [(p[0], -p[1]) for p in SIDE_LANE_POINTS]

def get_tower_points(y_sign, from_end):
    if from_end:
        return [(MAP_X - p[0], y_sign * p[1]) for p in TOWER_BASE_POINTS]
    else:
        return [(p[0], y_sign * p[1]) for p in TOWER_BASE_POINTS]

HALF_PATH_WIDTH = 35

MAP_LANE_POLYGONS = [
    [(p[0], p[1] + HALF_PATH_WIDTH) for p in points] + [(p[0], p[1] - HALF_PATH_WIDTH) for p in reversed(points)] for points in [TOP_LANE_POINTS, MID_LAND_POINTS, BOT_LANE_POINTS]
]


BASE_CIRCLE_RADIUS = 175
WATER_CIRCLE_Y_RADIUS = THIRD_TOWER_DY // 3
WATER_CIRCLE_X_RADIUS = WATER_CIRCLE_Y_RADIUS // 3
WATER_CIRCLE_DY = THIRD_TOWER_DY // 2
def get_water_circle_point(top_bot_lane_sgn):
    return (MAP_HALF_X - WATER_CIRCLE_X_RADIUS, top_bot_lane_sgn * WATER_CIRCLE_DY - WATER_CIRCLE_Y_RADIUS), (WATER_CIRCLE_X_RADIUS * 2,  WATER_CIRCLE_Y_RADIUS * 2)
BASE_CIRCLES = [((0, 0), BASE_CIRCLE_RADIUS), ((MAP_X, 0), BASE_CIRCLE_RADIUS)]
WATER_ELLIPSES = [get_water_circle_point(1), get_water_circle_point(-1)]
