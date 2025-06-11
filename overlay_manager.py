from enum import Enum
import pygame

from ui_utils import screen2coord

# Initialize Pygame
pygame.init()

class OverlayType(Enum):
    MOVE_TO_LOCATION = 0
    ATTACK_LANE_ENTITY = 1
    STOP_ATTACKING_LANE_ENTITY = 2
    ENGAGE_COMBAT = 3
    DISENGAGE_COMBAT = 4
    SELECT_PLAYER = 5

# Define some colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
COLORS_BY_TYPE = {
    OverlayType.ATTACK_LANE_ENTITY: (255, 0, 0),
    OverlayType.ENGAGE_COMBAT: (255, 0, 0),
    OverlayType.MOVE_TO_LOCATION: (0, 255, 0),
    OverlayType.STOP_ATTACKING_LANE_ENTITY: (0, 0, 255),
    OverlayType.DISENGAGE_COMBAT: (0, 0, 255),
}
TEXT_BY_TYPE = {
    OverlayType.ATTACK_LANE_ENTITY: "#",
    OverlayType.ENGAGE_COMBAT: "!!!",
    OverlayType.MOVE_TO_LOCATION: "v",
    OverlayType.STOP_ATTACKING_LANE_ENTITY: "--",
    OverlayType.DISENGAGE_COMBAT: "/ \\",
}

class OverlayItem:
    def __init__(self, position, item_type, callback, name=''):
        self.position = position
        self.type = item_type
        self.callback = callback

    def render(self, surface):
        raise NotImplementedError

    def contains_point(self, point):
        """Check if a point (x, y) is inside this item."""
        raise NotImplementedError


class Box(OverlayItem):
    def __init__(self, position, size, item_type, callback, name=''):
        super().__init__(position, item_type, callback, name)
        self.size = size  # (width, height)
        self.rect = pygame.Rect(position[0], position[1], size, size)

    def render(self, surface):
        color = COLORS_BY_TYPE.get(self.type, BLACK)
        symbol = TEXT_BY_TYPE.get(self.type, "???")
        pygame.draw.rect(surface, color, self.rect)
        font = pygame.font.SysFont(None, 24)
        text = font.render(symbol, True, WHITE)
        surface.blit(text, (self.rect.x + 5, self.rect.y + 5))

    def contains_point(self, point):
        return self.rect.collidepoint(point)


class Circle(OverlayItem):
    def __init__(self, position, radius, item_type, callback, name=''):
        super().__init__(position, item_type, callback, name)
        self.radius = radius

    def render(self, surface):
        if self.type == OverlayType.SELECT_PLAYER:
            #pygame.draw.circle(surface, BLACK, self.position, 25, width=3)
            return # Don't render this
        color = COLORS_BY_TYPE.get(self.type, BLACK)
        symbol = TEXT_BY_TYPE.get(self.type, "???")
        pygame.draw.circle(surface, color, self.position, self.radius)
        font = pygame.font.SysFont(None, 16)
        text = font.render(symbol, True, WHITE)
        text_rect = text.get_rect(center=self.position)
        surface.blit(text, text_rect)

    def contains_point(self, point):
        dx = point[0] - self.position[0]
        dy = point[1] - self.position[1]
        return dx * dx + dy * dy <= self.radius * self.radius


class OverlayManager:
    def __init__(self):
        self.items = []

    def add_box(self, position, size, item_type, callback, name=''):
        box = Box(position, size, item_type, callback, name)
        self.items.append(box)

    def add_multiple_boxes(self, center_pos, size, types_and_callbacks, padding=3):
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
            self.add_box(position, size, item_type, callback, name)

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

    def render_all(self, surface):
        for item in self.items:
            item.render(surface)