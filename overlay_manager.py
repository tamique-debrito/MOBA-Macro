from enum import Enum
import math
import pygame

from CONSTANTS import DASH_START_Y, MAP_X, SCREEN_X
from ui_utils import ACTION_SYMBOL_FONT, INFO_FONT
from ui_utils import BLACK, WHITE, screen2coord

CONSOLIDATE_THRESHOLD: int = 40
DASH_PADDING: int = 5
DASH_SEPARATOR_THICKNESS: int = 5

class OverlayType(Enum):
    # In game
    MOVE_TO_LOCATION = 0
    ATTACK_LANE_ENTITY = 1
    STOP_ATTACKING_LANE_ENTITY = 2
    ENGAGE_COMBAT = 3
    JOIN_COMBAT = 3.5
    DISENGAGE_COMBAT = 4
    SELECT_PLAYER = 5
    START_RECALL = 6
    STOP_RECALL = 7
    BUY_ITEM = 8
    # Sim control
    PAUSE = "PAUSE"
    RESUME = "RESUME"
    # Game tree
    UP_TREE = 9
    DOWN_TREE = 10
    ADD_NODE = 11
    RESET_NODE = 12

# Define some colors
COLORS_BY_TYPE = {
    OverlayType.ATTACK_LANE_ENTITY: (255, 0, 0),
    OverlayType.ENGAGE_COMBAT: (255, 0, 0),
    OverlayType.JOIN_COMBAT: (255, 0, 0),
    OverlayType.DISENGAGE_COMBAT: (0, 255, 255),
    OverlayType.MOVE_TO_LOCATION: (0, 255, 0),
    OverlayType.STOP_ATTACKING_LANE_ENTITY: (0, 255, 255),
    OverlayType.START_RECALL: (0, 0, 255),
    OverlayType.STOP_RECALL: (0, 0, 255),
    OverlayType.BUY_ITEM: (0, 255, 0),
    #
    OverlayType.PAUSE: (0, 0, 255),
    OverlayType.RESUME: (0, 255, 0),
    #
    OverlayType.UP_TREE: (100, 100, 100),
    OverlayType.DOWN_TREE: (100, 100, 100),
    OverlayType.ADD_NODE: (100, 100, 100),
    OverlayType.RESET_NODE: (100, 100, 100),
}
TEXT_BY_TYPE = {
    OverlayType.ATTACK_LANE_ENTITY: "⛏",
    OverlayType.ENGAGE_COMBAT: "⚔",
    OverlayType.JOIN_COMBAT: "+⚔",
    OverlayType.MOVE_TO_LOCATION: "📌",
    OverlayType.STOP_ATTACKING_LANE_ENTITY: "x⛏",
    OverlayType.DISENGAGE_COMBAT: "x⚔",
    OverlayType.START_RECALL: "✨",
    OverlayType.STOP_RECALL: "x✨",
    OverlayType.BUY_ITEM: "💰",
    #
    OverlayType.PAUSE: "❚❚",
    OverlayType.RESUME: "▶",
    #
    OverlayType.UP_TREE: "↑",
    OverlayType.DOWN_TREE: "↓",
    OverlayType.ADD_NODE: "➕",
    OverlayType.RESET_NODE: "↶",
}

BOX_SIZE = 25
DASH_BUTTON_MARGIN = 3

class OverlayItem:
    next_id = 0
    def __init__(self, position, item_type, callback, name=''):
        self.position = position
        self.type = item_type
        self.callback = callback
        self.item_id = OverlayItem.next_id
        OverlayItem.next_id += 1

    def render(self, screen):
        raise NotImplementedError

    def contains_point(self, point):
        """Check if a point (x, y) is inside this item."""
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"Overlay {self.type}, {self.position}"


class Box(OverlayItem):
    def __init__(self, position, size, item_type, callback, name=''):
        super().__init__(position, item_type, callback, name)
        self.size = (size, size)  # (width, height)
        self.rect = pygame.Rect(position[0], position[1], size, size)

    def render(self, screen):
        color = COLORS_BY_TYPE.get(self.type, BLACK)
        symbol = TEXT_BY_TYPE.get(self.type, "???")
        pygame.draw.rect(screen, color, self.rect)
        text = ACTION_SYMBOL_FONT.render(symbol, True, WHITE)
        screen.blit(text, (self.rect.x, self.rect.y))

    def contains_point(self, point):
        return self.rect.collidepoint(point)


class Circle(OverlayItem):
    def __init__(self, position, radius, item_type, callback, name=''):
        super().__init__(position, item_type, callback, name)
        self.radius = radius

    def render(self, screen):
        if self.type == OverlayType.SELECT_PLAYER:
            #pygame.draw.circle(screen, BLACK, self.position, 25, width=3)
            return # Don't render this
        color = COLORS_BY_TYPE.get(self.type, BLACK)
        symbol = TEXT_BY_TYPE.get(self.type, "???")
        pygame.draw.circle(screen, color, self.position, self.radius)
        text = ACTION_SYMBOL_FONT.render(symbol, True, WHITE)
        text_rect = text.get_rect(center=self.position)
        screen.blit(text, text_rect)

    def contains_point(self, point):
        dx = point[0] - self.position[0]
        dy = point[1] - self.position[1]
        return dx * dx + dy * dy <= self.radius * self.radius


class Consolidation:
    # Helper class for tracking boxes to consolidate together
    def __init__(self, boxes, mean_coord):
        self.boxes = boxes
        self.mean_coord = mean_coord

class OverlayManager:
    def __init__(self):
        self.items = []
        self.dash_start_y = DASH_START_Y
        self.current_dash_x = DASH_PADDING

    def get_dash_pos_and_increment(self, size):
        curr = self.current_dash_x
        self.current_dash_x += size + DASH_BUTTON_MARGIN
        return (curr, self.dash_start_y + DASH_SEPARATOR_THICKNESS + DASH_PADDING)

    def add_box(self, position, item_type, callback, name='', size=BOX_SIZE):
        if position == "on_dash":
            position = self.get_dash_pos_and_increment(size)
        box = Box(position, size, item_type, callback, name)
        self.items.append(box)

    def add_multiple_boxes(self, center_pos, types_and_callbacks, size=BOX_SIZE, padding=3):
        """types_and_callbacks is a list of pairs of overlay types and callbacks"""
        count = len(types_and_callbacks)
        if count == 0:
            return  # no boxes to add

        # Calculate total width of all boxes including paddings
        total_width = count * size + (count - 1) * padding

        start_x = center_pos[0] - total_width / 2

        for i in range(count):
            x = start_x + i * (size + padding)
            y = center_pos[1]  # align all boxes horizontally
            position = (x, y)
            item_type, callback = types_and_callbacks[i]
            name = f"Box_{i+1}"
            self.add_box(position, item_type, callback, name, size=size)

    def add_circle(self, position, radius, item_type, callback, name=''):
        circle = Circle(position, radius, item_type, callback, name)
        self.items.append(circle)

    def render_additional_dash_info(self, screen, info: list[str]):
        for i, info_line in enumerate(info):
            text = INFO_FONT.render(info_line, True, BLACK)
            screen.blit(text, (SCREEN_X - 200, self.dash_start_y + DASH_SEPARATOR_THICKNESS + 5 + i * 6))

    def handle_click(self, point):
        for item in reversed(self.items):
            if item.contains_point(point):
                remapped = screen2coord(point) # Make sure to undo translation to put back into map coordinate system
                item.callback(remapped)
                return True
        return False
    
    def clear(self):
        """Clear all overlays"""
        self.items = []
        self.current_dash_x = DASH_PADDING

    def render_all(self, screen, additional_dash_info: list[str]):
        pygame.draw.line(screen, BLACK, (0, self.dash_start_y), (SCREEN_X, self.dash_start_y), DASH_SEPARATOR_THICKNESS)
        for item in self.items:
            item.render(screen)
        self.render_additional_dash_info(screen, additional_dash_info)
    
    def consolidate(self):
        """
        Consolidate boxes within the threshold distance, grouping by action type.
        All callbacks of the grouped boxes are called in sequence when the new box is clicked.
        """
        all_types_consolidations = {}

        to_consolidate = []
        to_skip = []

        for item in self.items:
            if not isinstance(item, Box) or item.type in [OverlayType.UP_TREE, OverlayType.DOWN_TREE, OverlayType.ADD_NODE]:
                to_skip.append(item)
            else:
                to_consolidate.append(item)

        for box in to_consolidate:
            
            action_type = box.type
            if action_type not in all_types_consolidations:
                all_types_consolidations[action_type] = []

            consolidations = all_types_consolidations[action_type]
            found_consolidation = False

            for consolidation in consolidations:
                dist = math.dist(box.position, consolidation['mean_coord'])
                if dist <= CONSOLIDATE_THRESHOLD:
                    consolidation['boxes'].append(box)
                    coords = [b.position for b in consolidation['boxes']]
                    mean_x = sum(p[0] for p in coords) / len(coords)
                    mean_y = sum(p[1] for p in coords) / len(coords)
                    consolidation['mean_coord'] = (mean_x, mean_y)
                    found_consolidation = True
                    break

            if not found_consolidation:
                # Create a new consolidation for this box
                consolidations.append({
                    'boxes': [box],
                    'mean_coord': box.position
                })

        # After grouping, create new consolidated boxes
        consolidated = []
        for action_type, consolidations in all_types_consolidations.items():
            for consolidation in consolidations:
                boxes_in_group = consolidation['boxes']
                mean_position = consolidation['mean_coord']
                mean_position = (int(mean_position[0]), int(mean_position[1]))

                def combined_callback(pos, boxes=boxes_in_group):
                    for b in boxes:
                        b.callback(pos)

                new_box = Box(mean_position, BOX_SIZE, action_type, combined_callback, name="Combined box")
                consolidated.append(new_box)
                #print(f"combined {[repr(b) for b in boxes_in_group]} into {repr(new_box)}")

        self.items = consolidated + to_skip