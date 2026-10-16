
import pygame
from game.maze import CELL

SPEED = 3


class Player:
    def __init__(self, r, c):
        self.r = r
        self.c = c

        x = c * CELL + CELL // 2
        y = r * CELL + CELL // 2

        self.rect = pygame.Rect(
            x - 10,
            y - 10,
            20,
            20
        )

        self.color = (60, 120, 220)

    def move(self, keys, walls, rows, cols):
        dx, dy = 0, 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -SPEED

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = SPEED

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -SPEED

        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = SPEED

        # Move horizontally first
        if dx != 0:
            new_rect = self.rect.move(dx, 0)

            if not self._hits_wall(
                new_rect, walls, rows, cols
            ):
                self.rect = new_rect

        # Move vertically second
        if dy != 0:
            new_rect = self.rect.move(0, dy)

            if not self._hits_wall(
                new_rect, walls, rows, cols
            ):
                self.rect = new_rect

        # Update current cell coordinates
        center_x, center_y = self.rect.center

        self.c = center_x // CELL
        self.r = center_y // CELL

    def _hits_wall(self, rect, walls, rows, cols):
        """
        Check whether the player's rectangle
        crosses any maze wall.

        Wall indices:
        0 = North
        1 = South
        2 = East
        3 = West
        """

        # Check outer maze boundaries
        if (
            rect.left < 0
            or rect.top < 0
            or rect.right > cols * CELL
            or rect.bottom > rows * CELL
        ):
            return True

        # Cells overlapped by player's rectangle
        left_col = rect.left // CELL
        right_col = (rect.right - 1) // CELL

        top_row = rect.top // CELL
        bottom_row = (rect.bottom - 1) // CELL

        # Check vertical wall segments
        # between horizontally adjacent cells
        for c in range(left_col + 1, right_col + 1):
            boundary_x = c * CELL

            if not (rect.left < boundary_x < rect.right):
                continue

            for r in range(top_row, bottom_row + 1):

                # East wall of left cell
                east_wall = walls[r][c - 1][2]

                # West wall of right cell
                west_wall = walls[r][c][3]

                if east_wall or west_wall:
                    return True

        # Check horizontal wall segments
        # between vertically adjacent cells
        for r in range(top_row + 1, bottom_row + 1):
            boundary_y = r * CELL

            if not (rect.top < boundary_y < rect.bottom):
                continue

            for c in range(left_col, right_col + 1):

                # South wall of upper cell
                south_wall = walls[r - 1][c][1]

                # North wall of lower cell
                north_wall = walls[r][c][0]

                if south_wall or north_wall:
                    return True

        return False

    def draw(self, screen):
        pygame.draw.ellipse(
            screen,
            self.color,
            self.rect
        )
