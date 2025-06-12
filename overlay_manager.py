from enum import Enum
import math
import pygame

from ui_utils import BLACK, WHITE, screen2coord

# Initialize Pygame
pygame.init()

CONSOLIDATE_THRESHOLD = 40

class OverlayType(Enum):
    MOVE_TO_LOCATION = 0
    ATTACK_LANE_ENTITY = 1
    STOP_ATTACKING_LANE_ENTITY = 2
    ENGAGE_COMBAT = 3
    JOIN_COMBAT = 3.5
    DISENGAGE_COMBAT = 4
    SELECT_PLAYER = 5
    START_RECALL = 6
    STOP_RECALL = 7

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
}

SYMBOL_FONT = pygame.font.Font("seguisym.ttf", 16)
BOX_SIZE = 25

class OverlayItem:
    def __init__(self, position, item_type, callback, name=''):
        self.position = position
        self.type = item_type
        self.callback = callback

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
        text = SYMBOL_FONT.render(symbol, True, WHITE)
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
        text = SYMBOL_FONT.render(symbol, True, WHITE)
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

    def add_box(self, position, item_type, callback, name='', size=BOX_SIZE):
        box = Box(position, size, item_type, callback, name)
        self.items.append(box)

    def add_multiple_boxes(self, center_pos, types_and_callbacks, size=BOX_SIZE, padding=3):
        """
        Adds multiple boxes evenly spaced around the center_pos.

        Args:
            center_pos (tuple): (x, y) center position
            size (tuple): (width, height) size of each box
            item_types (list): list of item_type strings for each box
            callbacks (list): list of callback functions for each box
            padding (int): space between boxes
        """
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

    def render_all(self, screen):
        for item in self.items:
            item.render(screen)
    
    def consolidate(self):
        """
        Consolidate boxes within the threshold distance, grouping by action type.
        All callbacks of the grouped boxes are called in sequence when the new box is clicked.
        """
        all_types_consolidations = {}

        for box in self.items:
            if not isinstance(box, Box):
                continue  # only process Box instances
            
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
        new_items = []
        for action_type, consolidations in all_types_consolidations.items():
            for consolidation in consolidations:
                boxes_in_group = consolidation['boxes']
                mean_position = consolidation['mean_coord']
                mean_position = (int(mean_position[0]), int(mean_position[1]))

                def combined_callback(pos, boxes=boxes_in_group):
                    for b in boxes:
                        b.callback(pos)

                new_box = Box(mean_position, BOX_SIZE, action_type, combined_callback, name="Combined box")
                new_items.append(new_box)
                #print(f"combined {[repr(b) for b in boxes_in_group]} into {repr(new_box)}")

        self.items = new_items + [item for item in self.items if not isinstance(item, Box)]