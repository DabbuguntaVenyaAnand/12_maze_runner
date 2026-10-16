
import json
import time
from collections import deque
from pathlib import Path

import pygame

from game.maze import CELL, generate_maze
from game.player import Player


# ---------------- CONFIGURATION ----------------

FPS = 60

BG = (240, 235, 220)
WALL_COLOR = (40, 40, 60)
EXIT_COLOR = (80, 200, 80)
HINT_COLOR = (255, 195, 75)
HUD_COLOR = (30, 30, 50)

FOG_COLOR = (0, 0, 0, 240)
FOG_RADIUS = 3 * CELL

HUD_HEIGHT = 60

DIFFICULTIES = {
    "Easy": (10, 8),
    "Medium": (15, 13),
    "Hard": (20, 18)
}

LEADERBOARD_FILE = (
    Path(__file__).resolve().parent.parent / "leaderboard.json"
)


class GameEngine:

    def __init__(self):
        pygame.init()

        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("monospace", 20)
        self.small_font = pygame.font.SysFont("monospace", 16)
        self.big_font = pygame.font.SysFont(
            "monospace", 34, bold=True
        )

        self.screen = pygame.display.set_mode((800, 780))
        pygame.display.set_caption("Maze Runner")

        self.state = "menu"
        self.difficulty = None

        self.cols = 0
        self.rows = 0

        self.leaderboard = self.load_leaderboard()

        self.menu_buttons = {}
        self.build_menu_buttons()

    # ---------------- TASK 4: DIFFICULTY ----------------

    def build_menu_buttons(self):
        center_x = self.screen.get_width() // 2

        self.menu_buttons = {
            name: pygame.Rect(
                center_x - 135,
                250 + i * 105,
                270,
                72
            )
            for i, name in enumerate(DIFFICULTIES)
        }

    def start_game(self, difficulty):
        self.difficulty = difficulty

        self.cols, self.rows = DIFFICULTIES[difficulty]

        self.screen = pygame.display.set_mode(
            (
                self.cols * CELL,
                self.rows * CELL + HUD_HEIGHT
            )
        )

        self.reset()
        self.state = "playing"

    def draw_text_center(self, message, font, color, y):
        surface = font.render(message, True, color)

        x = (
            self.screen.get_width() // 2
            - surface.get_width() // 2
        )

        self.screen.blit(surface, (x, y))

    def draw_menu(self):
        self.screen.fill(HUD_COLOR)

        self.draw_text_center(
            "MAZE RUNNER",
            self.big_font,
            (255, 220, 110),
            110
        )

        self.draw_text_center(
            "Choose a difficulty",
            self.font,
            (235, 235, 235),
            180
        )

        mouse = pygame.mouse.get_pos()

        for name, rect in self.menu_buttons.items():

            hovered = rect.collidepoint(mouse)

            color = (
                (85, 115, 170)
                if hovered
                else (58, 76, 118)
            )

            pygame.draw.rect(
                self.screen,
                color,
                rect,
                border_radius=12
            )

            cols, rows = DIFFICULTIES[name]

            self.draw_text_center(
                f"{name} ({cols} x {rows})",
                self.font,
                (255, 255, 255),
                rect.y + 22
            )

        self.draw_text_center(
            "Click a button to start",
            self.small_font,
            (180, 180, 190),
            645
        )

    # ---------------- MAZE RESET ----------------

    def reset(self):
        self.walls = generate_maze(
            self.cols,
            self.rows
        )

        self.player = Player(0, 0)

        self.exit_rect = pygame.Rect(
            (self.cols - 1) * CELL + 5,
            (self.rows - 1) * CELL + 5,
            CELL - 10,
            CELL - 10
        )

        self.start_time = time.monotonic()
        self.elapsed = 0.0

        self.won = False

        # Reset Task 1 hint
        self.show_hint = False
        self.solution_path = []

        self.state = "playing"

    # ---------------- TASK 1: BFS SHORTEST PATH ----------------

    def bfs_shortest_path(self):
        """
        Find shortest path from start to exit
        using Breadth-First Search.

        Wall directions:
        0 = North
        1 = South
        2 = East
        3 = West
        """

        start = (0, 0)
        goal = (self.rows - 1, self.cols - 1)

        directions = [
            (-1, 0, 0),
            (1, 0, 1),
            (0, 1, 2),
            (0, -1, 3)
        ]

        queue = deque([start])
        previous = {start: None}

        while queue:

            r, c = queue.popleft()

            if (r, c) == goal:

                path = []
                cell = goal

                while cell is not None:
                    path.append(cell)
                    cell = previous[cell]

                path.reverse()
                return path

            for dr, dc, wall_index in directions:

                nr = r + dr
                nc = c + dc

                neighbor = (nr, nc)

                if not (
                    0 <= nr < self.rows
                    and 0 <= nc < self.cols
                ):
                    continue

                # Cannot cross maze walls
                if self.walls[r][c][wall_index]:
                    continue

                if neighbor in previous:
                    continue

                previous[neighbor] = (r, c)
                queue.append(neighbor)

        return []

    def draw_hint(self):
        if not self.show_hint:
            return

        for r, c in self.solution_path:

            square = pygame.Rect(
                c * CELL + 6,
                r * CELL + 6,
                CELL - 12,
                CELL - 12
            )

            pygame.draw.rect(
                self.screen,
                HINT_COLOR,
                square,
                border_radius=5
            )

    # ---------------- TASK 2: FOG OF WAR ----------------

    def draw_fog(self):
        """
        Cover maze with dark overlay.

        Create transparent circular area
        around player with radius of 3 cells.
        """

        width = self.cols * CELL
        height = self.rows * CELL

        # Create transparent-capable surface
        fog = pygame.Surface(
            (width, height),
            pygame.SRCALPHA
        )

        # Darken entire maze
        fog.fill(FOG_COLOR)

        # Player position
        player_center = self.player.rect.center

        # Clear circular area around player
        pygame.draw.circle(
            fog,
            (0, 0, 0, 0),
            player_center,
            FOG_RADIUS
        )

        # Apply fog over maze
        self.screen.blit(fog, (0, 0))

    # ---------------- TASK 3: LEADERBOARD ----------------

    def load_leaderboard(self):
        """
        Load previously saved completion times.
        """

        try:
            with LEADERBOARD_FILE.open(
                "r", encoding="utf-8"
            ) as file:
                data = json.load(file)

            if not isinstance(data, list):
                return []

            valid = []

            for entry in data:

                if not isinstance(entry, dict):
                    continue

                difficulty = entry.get("difficulty")
                completion_time = entry.get("time")

                if difficulty not in DIFFICULTIES:
                    continue

                if (
                    not isinstance(completion_time, (int, float))
                    or isinstance(completion_time, bool)
                    or not 0 <= completion_time < float("inf")
                ):
                    continue

                valid.append({
                    "difficulty": difficulty,
                    "time": float(completion_time)
                })

            valid.sort(key=lambda e: e["time"])

            return valid[:5]

        except (OSError, ValueError, TypeError):
            return []

    def save_completion(self):
        """
        Save completion time and retain
        the five fastest records.
        """

        self.leaderboard.append({
            "difficulty": self.difficulty,
            "time": round(self.elapsed, 2)
        })

        # Fastest first
        self.leaderboard.sort(
            key=lambda entry: entry["time"]
        )

        # Keep top 5
        self.leaderboard = self.leaderboard[:5]

        try:
            with LEADERBOARD_FILE.open(
                "w", encoding="utf-8"
            ) as file:

                json.dump(
                    self.leaderboard,
                    file,
                    indent=2
                )

        except OSError as error:
            print(
                f"Could not save leaderboard: {error}"
            )

    def draw_leaderboard(self):
        width = self.screen.get_width()
        maze_height = self.rows * CELL

        # Dark win-screen overlay
        overlay = pygame.Surface(
            (width, maze_height),
            pygame.SRCALPHA
        )

        overlay.fill((0, 0, 0, 210))

        self.screen.blit(overlay, (0, 0))

        panel_height = 360

        top = max(
            18,
            (maze_height - panel_height) // 2
        )

        self.draw_text_center(
            f"Solved in {self.elapsed:.2f}s!",
            self.font,
            (110, 245, 135),
            top
        )

        self.draw_text_center(
            "TOP 5 TIMES",
            self.font,
            (255, 220, 110),
            top + 52
        )

        if not self.leaderboard:

            self.draw_text_center(
                "No scores yet",
                self.small_font,
                (235, 235, 235),
                top + 95
            )

        for index, entry in enumerate(
            self.leaderboard
        ):

            label = (
                f"{index + 1}. "
                f"{entry['difficulty']:<6} "
                f"{entry['time']:>7.2f}s"
            )

            self.draw_text_center(
                label,
                self.small_font,
                (235, 235, 235),
                top + 94 + index * 33
            )

        self.draw_text_center(
            "R = Retry  ESC = Menu",
            self.small_font,
            (210, 210, 220),
            top + 305
        )

    # ---------------- KEYBOARD AND MOUSE ----------------

    def handle_events(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                return False

            # Difficulty selection
            if self.state == "menu":

                if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                ):

                    for name, rect in self.menu_buttons.items():

                        if rect.collidepoint(event.pos):
                            self.start_game(name)
                            break

            # During gameplay
            elif event.type == pygame.KEYDOWN:

                # Return to difficulty menu
                if event.key == pygame.K_ESCAPE:

                    self.state = "menu"

                    self.screen = pygame.display.set_mode(
                        (800, 780)
                    )

                    self.build_menu_buttons()

                # Generate new maze
                elif event.key == pygame.K_r:
                    self.reset()

                # Toggle shortest path hint
                elif event.key == pygame.K_h:

                    self.show_hint = not self.show_hint

                    if (
                        self.show_hint
                        and not self.solution_path
                    ):

                        self.solution_path = (
                            self.bfs_shortest_path()
                        )

        return True

    # ---------------- GAME UPDATE ----------------

    def update(self):

        if self.state != "playing":
            return

        if self.won:
            return

        keys = pygame.key.get_pressed()

        self.player.move(
            keys,
            self.walls,
            self.rows,
            self.cols
        )

        self.elapsed = (
            time.monotonic() - self.start_time
        )

        # Detect maze completion
        if self.player.rect.colliderect(
            self.exit_rect
        ):

            self.won = True

            # Save score only once
            self.save_completion()

    # ---------------- MAZE DRAWING ----------------

    def draw_maze(self):

        wall_width = 3

        for r in range(self.rows):
            for c in range(self.cols):

                x = c * CELL
                y = r * CELL

                north, south, east, west = (
                    self.walls[r][c]
                )

                if north:
                    pygame.draw.line(
                        self.screen,
                        WALL_COLOR,
                        (x, y),
                        (x + CELL, y),
                        wall_width
                    )

                if south:
                    pygame.draw.line(
                        self.screen,
                        WALL_COLOR,
                        (x, y + CELL),
                        (x + CELL, y + CELL),
                        wall_width
                    )

                if east:
                    pygame.draw.line(
                        self.screen,
                        WALL_COLOR,
                        (x + CELL, y),
                        (x + CELL, y + CELL),
                        wall_width
                    )

                if west:
                    pygame.draw.line(
                        self.screen,
                        WALL_COLOR,
                        (x, y),
                        (x, y + CELL),
                        wall_width
                    )

    def draw_game(self):
        self.screen.fill(BG)

        # Task 1: Draw BFS path
        self.draw_hint()

        # Draw maze walls
        self.draw_maze()

        # Draw exit
        pygame.draw.rect(
            self.screen,
            EXIT_COLOR,
            self.exit_rect,
            border_radius=4
        )

        exit_label = self.small_font.render(
            "EXIT",
            True,
            (20, 80, 20)
        )

        self.screen.blit(
            exit_label,
            exit_label.get_rect(
                center=self.exit_rect.center
            )
        )

        # Draw player
        self.player.draw(self.screen)

        # Task 2: Apply fog after drawing maze
        if not self.won:
            self.draw_fog()

        # HUD
        hud = pygame.Rect(
            0,
            self.rows * CELL,
            self.cols * CELL,
            HUD_HEIGHT
        )

        pygame.draw.rect(
            self.screen,
            HUD_COLOR,
            hud
        )

        hud_text = (
            f"{self.elapsed:.1f}s  "
            "H:Hint  R:Reset  ESC:Menu"
        )

        label = self.small_font.render(
            hud_text,
            True,
            (230, 230, 230)
        )

        self.screen.blit(
            label,
            (8, self.rows * CELL + 20)
        )

        # Task 3: Leaderboard on win
        if self.won:
            self.draw_leaderboard()

    def draw(self):

        if self.state == "menu":
            self.draw_menu()
        else:
            self.draw_game()

        pygame.display.flip()

    # ---------------- MAIN GAME LOOP ----------------

    def run(self):

        running = True

        while running:

            running = self.handle_events()

            if not running:
                break

            self.update()
            self.draw()

            self.clock.tick(FPS)

        pygame.quit()
