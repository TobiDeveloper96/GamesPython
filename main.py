# Snake Game by TobiDevelopment
# with modern neon aesthetics, glow effects, and smooth animations and enemy AI

import math
import random
import sys

import pygame

pygame.init()


# Settings
CELL_SIZE = 24
GRID_WIDTH = 28
GRID_HEIGHT = 18

BOARD_WIDTH = GRID_WIDTH * CELL_SIZE
BOARD_HEIGHT = GRID_HEIGHT * CELL_SIZE

WIDTH = 760
HEIGHT = 650

BOARD_X = (WIDTH - BOARD_WIDTH) // 2
BOARD_Y = 145

FPS = 60
BASE_SPEED = 8

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake-TobiDevelopment Edition")
clock = pygame.time.Clock()

TITLE_FONT = pygame.font.SysFont("helvetica", 64, bold=True)
BIG_FONT = pygame.font.SysFont("helvetica", 42, bold=True)
UI_FONT = pygame.font.SysFont("helvetica", 22, bold=True)
SMALL_FONT = pygame.font.SysFont("helvetica", 17)

# Colors
WHITE = (245, 248, 255)
MUTED = (145, 160, 190)
BLACK = (0, 0, 0)

BG_TOP = (7, 11, 28)
BG_BOTTOM = (2, 5, 13)
PANEL = (18, 27, 52)
PANEL_LIGHT = (45, 70, 125)

NEON_GREEN = (70, 255, 155)
GREEN = (35, 215, 120)
GREEN_DARK = (10, 95, 60)
CYAN = (75, 220, 255)
BLUE = (70, 130, 255)
BLUE_DARK = (28, 65, 145)
PINK = (255, 70, 170)
RED = (255, 75, 90)
RED_DARK = (145, 28, 45)
YELLOW = (255, 220, 100)
PURPLE = (150, 90, 255)


def clamp(value):
    return max(0, min(255, int(value)))


def shade(color, amount):
    return tuple(clamp(c + amount) for c in color)


def lerp_color(a, b, t):
    return (
        int(a[0] * (1 - t) + b[0] * t),
        int(a[1] * (1 - t) + b[1] * t),
        int(a[2] * (1 - t) + b[2] * t),
    )


def draw_neon_text(text, font, center, color, glow_color=None):
    if glow_color is None:
        glow_color = color

    for offset, alpha_like in [(5, 45), (3, 70), (1, 110)]:
        glow_surface = font.render(text, True, glow_color)
        glow_surface.set_alpha(alpha_like)
        glow_rect = glow_surface.get_rect(center=(center[0] + offset, center[1] + offset))
        screen.blit(glow_surface, glow_rect)

    surface = font.render(text, True, color)
    rect = surface.get_rect(center=center)
    screen.blit(surface, rect)


def draw_text(text, font, color, center):
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=center)
    screen.blit(surface, rect)


def draw_glow_rect(rect, color, radius=16, intensity=42):
    glow = pygame.Surface((rect.width + 80, rect.height + 80), pygame.SRCALPHA)
    glow_rect = pygame.Rect(40, 40, rect.width, rect.height)

    for i in range(7, 0, -1):
        expanded = glow_rect.inflate(i * 9, i * 9)
        alpha = max(3, intensity // i)
        pygame.draw.rect(glow, (*color, alpha), expanded, border_radius=radius + i * 5)

    screen.blit(glow, (rect.x - 40, rect.y - 40))


def draw_glow_circle(center, radius, color, pulse=0):
    max_radius = int(radius + 26 + pulse)
    glow = pygame.Surface((max_radius * 2, max_radius * 2), pygame.SRCALPHA)

    for i in range(8, 0, -1):
        r = radius + i * 4 + pulse
        alpha = max(4, 58 - i * 6)
        pygame.draw.circle(glow, (*color, alpha), (max_radius, max_radius), int(r))

    screen.blit(glow, (center[0] - max_radius, center[1] - max_radius))


def draw_beveled_rect(rect, color, radius=10, depth=6, glow_color=None):
    if glow_color:
        draw_glow_rect(rect, glow_color, radius=radius, intensity=24)

    shadow_rect = rect.move(depth, depth)
    pygame.draw.rect(screen, (0, 0, 0), shadow_rect, border_radius=radius)

    side_rect = rect.move(depth // 2, depth // 2)
    pygame.draw.rect(screen, shade(color, -65), side_rect, border_radius=radius)

    pygame.draw.rect(screen, color, rect, border_radius=radius)

    top = pygame.Rect(rect.x + 4, rect.y + 4, rect.width - 8, max(5, rect.height // 3))
    pygame.draw.rect(screen, shade(color, 42), top, border_radius=radius)

    left = pygame.Rect(rect.x + 4, rect.y + 8, max(4, rect.width // 6), rect.height - 14)
    pygame.draw.rect(screen, shade(color, 24), left, border_radius=radius)

    bottom = pygame.Rect(rect.x + 5, rect.bottom - 8, rect.width - 10, 4)
    pygame.draw.rect(screen, shade(color, -45), bottom, border_radius=radius)

    pygame.draw.rect(screen, shade(color, -35), rect, 2, border_radius=radius)


def draw_background(time_ms):
    # Modern gradient background with multiple layers
    for y in range(HEIGHT):
        t = y / HEIGHT
        # Base gradient
        base_color = lerp_color(BG_TOP, BG_BOTTOM, t)
        
        # Add animated gradient shift
        shift = math.sin(time_ms * 0.0008) * 0.1
        accent_t = (t + shift) % 1.0
        accent_color = lerp_color((15, 25, 60), (5, 15, 35), accent_t)
        
        # Blend colors
        blended = (
            int(base_color[0] * 0.7 + accent_color[0] * 0.3),
            int(base_color[1] * 0.7 + accent_color[1] * 0.3),
            int(base_color[2] * 0.7 + accent_color[2] * 0.3),
        )
        pygame.draw.line(screen, blended, (0, y), (WIDTH, y))

    # Modern grid pattern
    grid_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    grid_spacing = 60
    grid_alpha = 8
    
    for x in range(0, WIDTH + grid_spacing, grid_spacing):
        pygame.draw.line(grid_layer, (100, 150, 255, grid_alpha), (x, 0), (x, HEIGHT), 1)
    
    for y in range(0, HEIGHT + grid_spacing, grid_spacing):
        pygame.draw.line(grid_layer, (100, 150, 255, grid_alpha), (0, y), (WIDTH, y), 1)
    
    screen.blit(grid_layer, (0, 0))

    # Animated neon horizon lines with modern styling
    for i in range(11):
        y = 95 + i * 52 + int(math.sin(time_ms * 0.0012 + i) * 4)
        alpha = max(20, 80 - i * 5)
        line = pygame.Surface((WIDTH, 2), pygame.SRCALPHA)
        pygame.draw.line(line, (*CYAN, alpha), (0, 1), (WIDTH, 1))
        screen.blit(line, (0, y))

    # Modern animated diagonal beams with gradient effect
    beam = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for i in range(-WIDTH, WIDTH, 90):
        x = i + int((time_ms * 0.035) % 90)
        # Create gradient beam effect
        beam_color = (
            int(90 + math.sin(time_ms * 0.0015 + i) * 30),
            int(80 + math.cos(time_ms * 0.0012 + i) * 40),
            255
        )
        pygame.draw.line(beam, (*beam_color, 18), (x, 0), (x + 260, HEIGHT), 2)
    screen.blit(beam, (0, 0))

    # Modern accent circles (glassmorphism style)
    accent_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    
    # Animated circles at key positions
    for i in range(3):
        offset = (time_ms * 0.0008 + i * 2) % (2 * math.pi)
        cx = WIDTH // 2 + int(math.cos(offset) * 150)
        cy = HEIGHT // 2 + int(math.sin(offset) * 120)
        
        radius = 80 + int(math.sin(time_ms * 0.001 + i) * 20)
        alpha = int(15 + math.sin(time_ms * 0.002 + i) * 8)
        
        pygame.draw.circle(accent_layer, (100, 200, 255, alpha), (cx, cy), radius, 2)
    
    screen.blit(accent_layer, (0, 0))


def draw_vignette():
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for i in range(22):
        alpha = i * 3
        pygame.draw.rect(overlay, (0, 0, 0, alpha), (i, i, WIDTH - i * 2, HEIGHT - i * 2), 1)
    screen.blit(overlay, (0, 0))


def draw_scanlines():
    scan = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for y in range(0, HEIGHT, 4):
        pygame.draw.line(scan, (255, 255, 255, 9), (0, y), (WIDTH, y))
    screen.blit(scan, (0, 0))



# Particles
background_particles = []

for _ in range(90):
    background_particles.append({
        "x": random.uniform(0, WIDTH),
        "y": random.uniform(0, HEIGHT),
        "speed": random.uniform(0.12, 0.55),
        "size": random.choice([1, 1, 1, 2]),
        "phase": random.uniform(0, math.tau),
    })

burst_particles = []


def update_and_draw_background_particles(time_ms):
    for p in background_particles:
        p["y"] += p["speed"]
        p["x"] += math.sin(time_ms * 0.001 + p["phase"]) * 0.18

        if p["y"] > HEIGHT + 5:
            p["y"] = -5
            p["x"] = random.uniform(0, WIDTH)

        twinkle = 80 + int(math.sin(time_ms * 0.004 + p["phase"]) * 55)
        pygame.draw.circle(
            screen,
            (120, 210, 255, twinkle),
            (int(p["x"]), int(p["y"])),
            p["size"]
        )


def spawn_burst(grid_position):
    center = grid_to_pixel_center(grid_position)

    for _ in range(24):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1.2, 4.2)

        burst_particles.append({
            "x": center[0],
            "y": center[1],
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "life": random.randint(22, 42),
            "max_life": 42,
            "size": random.randint(2, 5),
            "color": random.choice([RED, PINK, YELLOW, CYAN]),
        })


def update_and_draw_bursts():
    for p in burst_particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vy"] += 0.035
        p["life"] -= 1

        if p["life"] <= 0:
            burst_particles.remove(p)
            continue

        alpha = int(255 * (p["life"] / p["max_life"]))
        surf = pygame.Surface((p["size"] * 4, p["size"] * 4), pygame.SRCALPHA)

        pygame.draw.circle(
            surf,
            (*p["color"], alpha),
            (p["size"] * 2, p["size"] * 2),
            p["size"],
        )

        screen.blit(surf, (p["x"] - p["size"] * 2, p["y"] - p["size"] * 2))


# UI

class Button:
    def __init__(self, text, x, y, width, height, action, accent=BLUE):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.action = action
        self.accent = accent

    def draw(self, mouse_pos):
        hovered = self.rect.collidepoint(mouse_pos)

        color = shade(self.accent, 20) if hovered else shade(self.accent, -35)
        glow = self.accent if hovered else None
        rect = self.rect.inflate(8, 6) if hovered else self.rect

        draw_beveled_rect(rect, color, radius=14, depth=5, glow_color=glow)
        draw_text(self.text, UI_FONT, WHITE, rect.center)

    def is_clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )

# Define buttons
nav_buttons = [
    Button("PLAY", 178, 25, 88, 42, "play", NEON_GREEN),
    Button("PAUSE", 280, 25, 104, 42, "pause", CYAN),
    Button("RESTART", 398, 25, 126, 42, "restart", PURPLE),
    Button("QUIT", 538, 25, 88, 42, "quit", RED),
]

menu_buttons = [
    Button("START GAME", WIDTH // 2 - 135, 342, 270, 58, "play", NEON_GREEN),
    Button("QUIT", WIDTH // 2 - 135, 418, 270, 58, "quit", RED),
]

game_over_buttons = [
    Button("PLAY AGAIN", WIDTH // 2 - 135, 350, 270, 58, "restart", NEON_GREEN),
    Button("QUIT", WIDTH // 2 - 135, 426, 270, 58, "quit", RED),
]


# Utility functions

def grid_to_rect(position):
    x, y = position

    return pygame.Rect(
        BOARD_X + x * CELL_SIZE + 2,
        BOARD_Y + y * CELL_SIZE + 2,
        CELL_SIZE - 4,
        CELL_SIZE - 4,
    )


def grid_to_pixel_center(position):
    x, y = position

    return (
        BOARD_X + x * CELL_SIZE + CELL_SIZE // 2,
        BOARD_Y + y * CELL_SIZE + CELL_SIZE // 2,
    )


def create_food(snake):
    while True:
        position = (
            random.randint(0, GRID_WIDTH - 1),
            random.randint(0, GRID_HEIGHT - 1),
        )

        if position not in snake:
            return position


def reset_game():
    snake = [(13, 9), (12, 9), (11, 9), (10, 9)]
    direction = (1, 0)
    next_direction = direction
    food = create_food(snake)
    score = 0
    enemy = None
    enemy_move_timer = 0

    return snake, direction, next_direction, food, score, enemy, enemy_move_timer


def get_level(score):
    return score // 5 + 1


def spawn_enemy():
    """Spawn enemy at a random position away from snake head"""
    while True:
        position = (
            random.randint(0, GRID_WIDTH - 1),
            random.randint(0, GRID_HEIGHT - 1),
        )
        # Make sure enemy doesn't spawn on snake
        if position not in snake and position != food:
            return position


def move_enemy_towards_food(enemy, food):
    """Simple AI: move enemy towards food"""
    ex, ey = enemy
    fx, fy = food
    
    dx = fx - ex
    dy = fy - ey
    
    # Move towards food (Manhattan distance)
    if abs(dx) > abs(dy):
        return (ex + (1 if dx > 0 else -1), ey)
    else:
        return (ex, ey + (1 if dy > 0 else -1))


snake, direction, next_direction, food, score, enemy, enemy_move_timer = reset_game()
game_state = "menu"
last_move_time = 0


def start_game():
    global snake, direction, next_direction, food, score, game_state, burst_particles, enemy, enemy_move_timer

    snake, direction, next_direction, food, score, enemy, enemy_move_timer = reset_game()
    burst_particles = []
    game_state = "playing"


def pause_game():
    global game_state

    if game_state == "playing":
        game_state = "paused"
    elif game_state == "paused":
        game_state = "playing"


def restart_game():
    start_game()


def quit_game():
    pygame.quit()
    sys.exit()


def handle_button_action(action):
    if action == "play":
        if game_state in ["menu", "game_over"]:
            start_game()
        elif game_state == "paused":
            pause_game()

    elif action == "pause":
        pause_game()

    elif action == "restart":
        restart_game()

    elif action == "quit":
        quit_game()



# Drawing game objects

def draw_navbar(mouse_pos, time_ms):
    nav_rect = pygame.Rect(22, 16, WIDTH - 44, 64)

    draw_glow_rect(nav_rect, BLUE, radius=20, intensity=20)

    pygame.draw.rect(screen, (7, 11, 25), nav_rect.move(7, 7), border_radius=20)
    pygame.draw.rect(screen, (17, 27, 54), nav_rect, border_radius=20)
    pygame.draw.rect(screen, (70, 105, 185), nav_rect, 2, border_radius=20)

    pulse = int(math.sin(time_ms * 0.004) * 20)
    draw_neon_text("SNAKE", UI_FONT, (90, 48), shade(NEON_GREEN, pulse), NEON_GREEN)

    for button in nav_buttons:
        button.draw(mouse_pos)


def draw_score_panel():
    panel = pygame.Rect(BOARD_X, 92, BOARD_WIDTH, 38)

    pygame.draw.rect(screen, (8, 13, 28), panel.move(4, 4), border_radius=14)
    pygame.draw.rect(screen, (20, 30, 58), panel, border_radius=14)
    pygame.draw.rect(screen, (55, 85, 145), panel, 2, border_radius=14)

    speed = BASE_SPEED + score // 4
    level = get_level(score)

    draw_text(f"Level: {level}", UI_FONT, WHITE, (BOARD_X + 80, 111))
    draw_text(f"Score: {score}", UI_FONT, WHITE, (BOARD_X + 220, 111))
    draw_text(f"Speed: {speed}", UI_FONT, MUTED, (BOARD_X + 360, 111))
    draw_text(
        "Arrows = move | ESC = pause | SPACE = start/restart",
        SMALL_FONT,
        MUTED,
        (BOARD_X + 535, 111)
    )


def draw_board(time_ms):
    board_outer = pygame.Rect(
        BOARD_X - 14,
        BOARD_Y - 14,
        BOARD_WIDTH + 28,
        BOARD_HEIGHT + 28
    )

    draw_glow_rect(board_outer, CYAN, radius=24, intensity=24)

    pygame.draw.rect(screen, (0, 0, 0), board_outer.move(10, 10), border_radius=24)
    pygame.draw.rect(screen, (13, 20, 42), board_outer, border_radius=24)
    pygame.draw.rect(screen, (70, 105, 180), board_outer, 3, border_radius=24)

    inner = pygame.Rect(BOARD_X, BOARD_Y, BOARD_WIDTH, BOARD_HEIGHT)
    pygame.draw.rect(screen, (10, 16, 32), inner)

    # Subtle checkerboard cells
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            rect = pygame.Rect(
                BOARD_X + x * CELL_SIZE,
                BOARD_Y + y * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )

            if (x + y) % 2 == 0:
                pygame.draw.rect(screen, (13, 22, 42), rect)

    # Neon grid
    grid_surface = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)

    for x in range(GRID_WIDTH + 1):
        px = x * CELL_SIZE
        alpha = 42 if x % 4 == 0 else 22
        pygame.draw.line(grid_surface, (75, 220, 255, alpha), (px, 0), (px, BOARD_HEIGHT), 1)

    for y in range(GRID_HEIGHT + 1):
        py = y * CELL_SIZE
        alpha = 42 if y % 4 == 0 else 22
        pygame.draw.line(grid_surface, (75, 220, 255, alpha), (0, py), (BOARD_WIDTH, py), 1)

    # Moving scan glow inside board
    scan_y = int((time_ms * 0.07) % BOARD_HEIGHT)
    pygame.draw.line(grid_surface, (120, 255, 210, 60), (0, scan_y), (BOARD_WIDTH, scan_y), 2)

    screen.blit(grid_surface, (BOARD_X, BOARD_Y))


def draw_snake(time_ms):
    for index in range(len(snake) - 1, -1, -1):
        part = snake[index]
        rect = grid_to_rect(part)

        is_head = index == 0
        wave = math.sin(time_ms * 0.008 + index * 0.7)

        if is_head:
            color = shade(NEON_GREEN, int(wave * 15))

            draw_beveled_rect(
                rect.inflate(5, 5),
                color,
                radius=11,
                depth=7,
                glow_color=NEON_GREEN
            )

            # Eyes following direction
            cx, cy = rect.center
            dx, dy = direction

            if dx != 0:
                eye1 = (cx + dx * 5, cy - 5)
                eye2 = (cx + dx * 5, cy + 5)
            else:
                eye1 = (cx - 5, cy + dy * 5)
                eye2 = (cx + 5, cy + dy * 5)

            pygame.draw.circle(screen, WHITE, eye1, 4)
            pygame.draw.circle(screen, WHITE, eye2, 4)
            pygame.draw.circle(screen, (5, 20, 15), (eye1[0] + dx * 1, eye1[1] + dy * 1), 2)
            pygame.draw.circle(screen, (5, 20, 15), (eye2[0] + dx * 1, eye2[1] + dy * 1), 2)

        else:
            fade = max(0.42, 1 - index / (len(snake) + 5))

            color = (
                int(GREEN[0] * fade + GREEN_DARK[0] * (1 - fade)),
                int(GREEN[1] * fade + GREEN_DARK[1] * (1 - fade)),
                int(GREEN[2] * fade + GREEN_DARK[2] * (1 - fade)),
            )

            size_pulse = int(wave * 1.5)
            draw_beveled_rect(
                rect.inflate(size_pulse, size_pulse),
                color,
                radius=9,
                depth=5
            )


def draw_food(time_ms):
    center = grid_to_pixel_center(food)
    pulse = int(math.sin(time_ms * 0.01) * 3)

    draw_glow_circle(center, 12, PINK, pulse=pulse)

    pygame.draw.circle(screen, RED_DARK, (center[0] + 5, center[1] + 5), 12 + pulse)
    pygame.draw.circle(screen, RED, center, 12 + pulse)
    pygame.draw.circle(screen, PINK, (center[0] - 4, center[1] - 4), 6)
    pygame.draw.circle(screen, WHITE, (center[0] - 6, center[1] - 6), 2)

    # Small orbit sparkles around food
    for i in range(3):
        angle = time_ms * 0.004 + i * math.tau / 3
        x = center[0] + math.cos(angle) * 20
        y = center[1] + math.sin(angle) * 20
        pygame.draw.circle(screen, YELLOW, (int(x), int(y)), 2)


def draw_enemy(enemy, time_ms):
    """Draw the enemy that eats food"""
    if enemy is None:
        return
    
    center = grid_to_pixel_center(enemy)
    pulse = int(math.sin(time_ms * 0.012) * 4)
    
    # Draw glowing enemy
    draw_glow_circle(center, 11, PURPLE, pulse=pulse)
    
    pygame.draw.circle(screen, (100, 40, 200), (center[0] + 4, center[1] + 4), 11 + pulse)
    pygame.draw.circle(screen, PURPLE, center, 11 + pulse)
    pygame.draw.circle(screen, (200, 100, 255), (center[0] - 3, center[1] - 3), 5)
    
    # Angry eyes
    eye_offset = 6
    pygame.draw.circle(screen, WHITE, (center[0] - eye_offset, center[1] - 4), 3)
    pygame.draw.circle(screen, WHITE, (center[0] + eye_offset, center[1] - 4), 3)
    pygame.draw.circle(screen, (50, 20, 100), (center[0] - eye_offset, center[1] - 4), 2)
    pygame.draw.circle(screen, (50, 20, 100), (center[0] + eye_offset, center[1] - 4), 2)


def draw_menu(mouse_pos, time_ms):
    draw_background(time_ms)
    update_and_draw_background_particles(time_ms)

    card = pygame.Rect(WIDTH // 2 - 230, 128, 460, 390)

    draw_glow_rect(card, PURPLE, radius=28, intensity=28)

    pygame.draw.rect(screen, (0, 0, 0), card.move(10, 10), border_radius=28)
    pygame.draw.rect(screen, (15, 23, 48), card, border_radius=28)
    pygame.draw.rect(screen, (90, 115, 215), card, 3, border_radius=28)

    pulse = int(math.sin(time_ms * 0.004) * 22)

    draw_neon_text("SNAKE", TITLE_FONT, (WIDTH // 2, 205), shade(NEON_GREEN, pulse), NEON_GREEN)
    draw_text("Press SPACE to start", UI_FONT, CYAN, (WIDTH // 2, 260))
    draw_text("Glow, particles, beveled blocks and animated board", SMALL_FONT, MUTED, (WIDTH // 2, 293))

    for button in menu_buttons:
        button.draw(mouse_pos)

    draw_text(
        "Tip: The game gets faster as you score more!",
        SMALL_FONT,
        MUTED,
        (WIDTH // 2, 548)
    )

    draw_scanlines()
    draw_vignette()


def draw_game_scene(mouse_pos, time_ms):
    draw_background(time_ms)
    update_and_draw_background_particles(time_ms)
    draw_navbar(mouse_pos, time_ms)
    draw_score_panel()
    draw_board(time_ms)
    draw_food(time_ms)
    draw_enemy(enemy, time_ms)
    update_and_draw_bursts()
    draw_snake(time_ms)
    draw_scanlines()
    draw_vignette()


def draw_pause_overlay():
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 145))
    screen.blit(overlay, (0, 0))

    box = pygame.Rect(WIDTH // 2 - 170, HEIGHT // 2 - 92, 340, 184)

    draw_glow_rect(box, CYAN, radius=24, intensity=30)

    pygame.draw.rect(screen, (15, 23, 48), box, border_radius=24)
    pygame.draw.rect(screen, CYAN, box, 3, border_radius=24)

    draw_neon_text("PAUSED", BIG_FONT, (WIDTH // 2, HEIGHT // 2 - 24), WHITE, CYAN)
    draw_text("SPACE or ESC = continue", UI_FONT, MUTED, (WIDTH // 2, HEIGHT // 2 + 28))


def draw_game_over(mouse_pos, time_ms):
    draw_game_scene(mouse_pos, time_ms)

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 165))
    screen.blit(overlay, (0, 0))

    panel = pygame.Rect(WIDTH // 2 - 220, 205, 440, 315)

    draw_glow_rect(panel, RED, radius=28, intensity=35)

    pygame.draw.rect(screen, (15, 18, 35), panel, border_radius=28)
    pygame.draw.rect(screen, RED, panel, 3, border_radius=28)

    draw_neon_text("GAME OVER", BIG_FONT, (WIDTH // 2, 270), RED, RED)
    draw_text(f"Final score: {score}", UI_FONT, WHITE, (WIDTH // 2, 315))

    for button in game_over_buttons:
        button.draw(mouse_pos)



# Game update

def update_game():
    global snake, direction, next_direction, food, score, game_state, enemy, enemy_move_timer

    direction = next_direction

    head_x, head_y = snake[0]
    move_x, move_y = direction
    new_head = (head_x + move_x, head_y + move_y)

    outside_board = (
        new_head[0] < 0
        or new_head[0] >= GRID_WIDTH
        or new_head[1] < 0
        or new_head[1] >= GRID_HEIGHT
    )

    if outside_board:
        game_state = "game_over"
        return

    will_eat = new_head == food
    body_to_check = snake if will_eat else snake[:-1]

    if new_head in body_to_check:
        game_state = "game_over"
        return

    # Check collision with enemy
    if score >= 6 and enemy is not None and new_head == enemy:
        game_state = "game_over"
        return

    snake.insert(0, new_head)

    if will_eat:
        score += 1
        spawn_burst(food)
        food = create_food(snake)
    else:
        snake.pop()
    
    # Enemy logic - spawns at score 6
    if score >= 6:
        if enemy is None:
            enemy = spawn_enemy()
            enemy_move_timer = 0
        else:
            # Enemy moves towards food every 2 snake moves
            enemy_move_timer += 1
            if enemy_move_timer >= 2:
                new_enemy_pos = move_enemy_towards_food(enemy, food)
                
                # Keep enemy in bounds
                new_enemy_pos = (
                    max(0, min(GRID_WIDTH - 1, new_enemy_pos[0])),
                    max(0, min(GRID_HEIGHT - 1, new_enemy_pos[1]))
                )
                
                enemy = new_enemy_pos
                enemy_move_timer = 0
            
            # Enemy eats food
            if enemy == food:
                food = create_food(snake + [enemy])
    else:
        enemy = None
        enemy_move_timer = 0



# Main loop

while True:
    clock.tick(FPS)

    time_ms = pygame.time.get_ticks()
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quit_game()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if game_state == "playing":
                    game_state = "paused"
                elif game_state == "paused":
                    game_state = "playing"

            if event.key == pygame.K_SPACE:
                if game_state == "menu":
                    start_game()
                elif game_state == "paused":
                    game_state = "playing"
                elif game_state == "game_over":
                    restart_game()

            if game_state == "playing":
                if event.key == pygame.K_UP and direction != (0, 1):
                    next_direction = (0, -1)
                elif event.key == pygame.K_DOWN and direction != (0, -1):
                    next_direction = (0, 1)
                elif event.key == pygame.K_LEFT and direction != (1, 0):
                    next_direction = (-1, 0)
                elif event.key == pygame.K_RIGHT and direction != (-1, 0):
                    next_direction = (1, 0)

        active_buttons = []

        if game_state == "menu":
            active_buttons = menu_buttons
        elif game_state in ["playing", "paused"]:
            active_buttons = nav_buttons
        elif game_state == "game_over":
            active_buttons = nav_buttons + game_over_buttons

        for button in active_buttons:
            if button.is_clicked(event):
                handle_button_action(button.action)

    if game_state == "playing":
        speed = BASE_SPEED + score // 4

        if time_ms - last_move_time > 1000 // speed:
            update_game()
            last_move_time = time_ms

    if game_state == "menu":
        draw_menu(mouse_pos, time_ms)

    elif game_state == "playing":
        draw_game_scene(mouse_pos, time_ms)

    elif game_state == "paused":
        draw_game_scene(mouse_pos, time_ms)
        draw_pause_overlay()

    elif game_state == "game_over":
        draw_game_over(mouse_pos, time_ms)

    pygame.display.flip()