import json
import math
import os
import random
import sys
from array import array

import pygame


pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

WIDTH, HEIGHT = 1040, 750
FPS = 60
WIN_SCORE = 7

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neon Pong Deluxe")
clock = pygame.time.Clock()

SAVE_FILE = os.path.join(os.path.dirname(__file__), "neon_pong_save.json")

# Colors
BLACK = (7, 8, 18)
WHITE = (245, 245, 245)
MUTED = (142, 146, 170)
PANEL = (24, 27, 48)
PANEL_HOVER = (36, 40, 72)
BORDER = (79, 87, 126)
BLUE = (68, 190, 255)
RED = (255, 78, 118)
GREEN = (91, 255, 165)
YELLOW = (255, 220, 92)
PURPLE = (185, 120, 255)
ORANGE = (255, 154, 83)

font_title = pygame.font.Font(None, 96)
font_h1 = pygame.font.Font(None, 72)
font_h2 = pygame.font.Font(None, 48)
font_body = pygame.font.Font(None, 32)
font_small = pygame.font.Font(None, 24)

DIFFICULTIES = [
    {"name": "Easy", "enemy_speed": 4.2, "ball_speed": 5.5},
    {"name": "Normal", "enemy_speed": 5.6, "ball_speed": 6.4},
    {"name": "Hard", "enemy_speed": 6.9, "ball_speed": 7.3},
    {"name": "Insane", "enemy_speed": 8.2, "ball_speed": 8.1},
]

SKINS = [
    {
        "name": "Classic Neon",
        "cost": 0,
        "p1": (68, 190, 255),
        "p2": (255, 78, 118),
        "ball": (245, 245, 245),
        "accent": (68, 190, 255),
    },
    {
        "name": "Cyber Mint",
        "cost": 30,
        "p1": (91, 255, 165),
        "p2": (255, 120, 215),
        "ball": (255, 240, 120),
        "accent": (91, 255, 165),
    },
    {
        "name": "Sunset Drive",
        "cost": 55,
        "p1": (255, 154, 83),
        "p2": (190, 120, 255),
        "ball": (255, 226, 102),
        "accent": (255, 154, 83),
    },
    {
        "name": "Ice & Fire",
        "cost": 80,
        "p1": (105, 225, 255),
        "p2": (255, 95, 60),
        "ball": (220, 250, 255),
        "accent": (105, 225, 255),
    },
    {
        "name": "Arcade Gold",
        "cost": 120,
        "p1": (255, 220, 92),
        "p2": (255, 255, 255),
        "ball": (255, 234, 140),
        "accent": (255, 220, 92),
    },
]

POWERUPS = [
    {"id": "big", "label": "BIG", "color": GREEN, "description": "větší pálka"},
    {"id": "slow", "label": "SLOW", "color": YELLOW, "description": "pomalejší míček"},
    {"id": "ice", "label": "ICE", "color": PURPLE, "description": "zpomalí soupeře"},
    {"id": "boost", "label": "BOOST", "color": ORANGE, "description": "rychlejší střela"},
]

PADDLE_WIDTH = 18
PADDLE_HEIGHT = 112
BIG_PADDLE_HEIGHT = 172
BALL_SIZE = 24
PLAYER_SPEED = 7.5

# Game data loaded from save
coins = 0
unlocked_skins = {"Classic Neon"}
selected_skin_index = 0
sounds_enabled = True

# Menu choices
screen_state = "menu"
game_mode = "Solo vs AI"
difficulty_index = 1
shop_cursor = 0

# Runtime game objects
left_paddle = pygame.Rect(58, HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
right_paddle = pygame.Rect(WIDTH - 76, HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
ball = pygame.Rect(WIDTH // 2 - BALL_SIZE // 2, HEIGHT // 2 - BALL_SIZE // 2, BALL_SIZE, BALL_SIZE)

left_direction = 0
right_direction = 0
ball_vx = 0.0
ball_vy = 0.0
left_score = 0
right_score = 0
last_touch = "left"
winner = None
match_reward_given = False

powerup = None
next_powerup_time = 0
active_effects = {}
particles = []
notifications = []

# ------------------------------------------------------------
# Save / load
# ------------------------------------------------------------


def load_save():
    global coins, unlocked_skins, selected_skin_index, sounds_enabled

    if not os.path.exists(SAVE_FILE):
        return

    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        coins = int(data.get("coins", 0))
        unlocked_skins = set(data.get("unlocked_skins", ["Classic Neon"]))
        selected_name = data.get("selected_skin", "Classic Neon")
        sounds_enabled = bool(data.get("sounds_enabled", True))

        for index, skin in enumerate(SKINS):
            if skin["name"] == selected_name:
                selected_skin_index = index
                break

    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        coins = 0
        unlocked_skins = {"Classic Neon"}
        selected_skin_index = 0
        sounds_enabled = True


def save_game():
    data = {
        "coins": coins,
        "unlocked_skins": sorted(unlocked_skins),
        "selected_skin": SKINS[selected_skin_index]["name"],
        "sounds_enabled": sounds_enabled,
    }

    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)
    except OSError:
        pass


# ------------------------------------------------------------
# Procedural sounds
# ------------------------------------------------------------


def make_sound(frequency, duration=0.1, volume=0.3, wave="sine"):
    sample_rate = 44100
    sample_count = int(sample_rate * duration)
    buffer = array("h")
    amplitude = int(32767 * volume)

    for i in range(sample_count):
        t = i / sample_rate
        phase = 2 * math.pi * frequency * t

        if wave == "square":
            raw = 1 if math.sin(phase) >= 0 else -1
        else:
            raw = math.sin(phase)

        fade_in = min(1, i / max(1, sample_rate * 0.01))
        fade_out = min(1, (sample_count - i) / max(1, sample_rate * 0.03))
        fade = min(fade_in, fade_out)
        buffer.append(int(amplitude * raw * fade))

    return pygame.mixer.Sound(buffer=buffer)


try:
    SOUNDS = {
        "click": make_sound(520, 0.06, 0.22),
        "hit": make_sound(760, 0.05, 0.28, "square"),
        "wall": make_sound(330, 0.05, 0.20),
        "score": make_sound(210, 0.18, 0.33),
        "power": make_sound(980, 0.18, 0.34),
        "buy": make_sound(680, 0.22, 0.30),
        "win": make_sound(820, 0.32, 0.35),
        "lose": make_sound(150, 0.38, 0.35),
    }
except pygame.error:
    SOUNDS = {}


def play_sound(name):
    if sounds_enabled and name in SOUNDS:
        SOUNDS[name].play()


# ------------------------------------------------------------
# UI helpers
# ------------------------------------------------------------


def get_skin():
    return SKINS[selected_skin_index]


def current_difficulty():
    return DIFFICULTIES[difficulty_index]


def draw_text(text, font, color, x, y, center=True):
    image = font.render(str(text), True, color)
    rect = image.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(image, rect)
    return rect


def rounded_rect(rect, color, radius=18, width=0):
    pygame.draw.rect(screen, color, rect, width, border_radius=radius)


def draw_glow_rect(rect, color, radius=18):
    outer = rect.inflate(10, 10)
    pygame.draw.rect(screen, (*color[:3],), outer, 1, border_radius=radius + 5)
    pygame.draw.rect(screen, color, rect, border_radius=radius)


class Button:
    def __init__(self, key, text, rect, accent=BLUE, small=False, disabled=False):
        self.key = key
        self.text = text
        self.rect = pygame.Rect(rect)
        self.accent = accent
        self.small = small
        self.disabled = disabled

    def is_hovered(self):
        return (not self.disabled) and self.rect.collidepoint(pygame.mouse.get_pos())

    def draw(self):
        hovered = self.is_hovered()
        bg = PANEL_HOVER if hovered else PANEL
        border = self.accent if hovered else BORDER
        text_color = WHITE if not self.disabled else (95, 98, 120)

        rounded_rect(self.rect, bg, 16)
        rounded_rect(self.rect, border, 16, 2)

        if hovered:
            shine = pygame.Rect(self.rect.x + 8, self.rect.y + 6, self.rect.width - 16, 2)
            pygame.draw.rect(screen, self.accent, shine, border_radius=4)

        font = font_small if self.small else font_body
        draw_text(self.text, font, text_color, self.rect.centerx, self.rect.centery)

    def clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and not self.disabled
            and self.rect.collidepoint(event.pos)
        )


def add_notification(text, color=WHITE):
    notifications.append({"text": text, "color": color, "life": 150})


def draw_notifications():
    y = 94
    for note in notifications[:]:
        alpha_life = min(1, note["life"] / 40)
        color = tuple(int(c * alpha_life + BLACK[i] * (1 - alpha_life)) for i, c in enumerate(note["color"]))
        draw_text(note["text"], font_small, color, WIDTH // 2, y)
        y += 25
        note["life"] -= 1
        if note["life"] <= 0:
            notifications.remove(note)


def draw_background():
    screen.fill(BLACK)
    t = pygame.time.get_ticks() / 1000

    # Animated neon grid
    for y in range(0, HEIGHT, 40):
        offset = int(math.sin(t + y * 0.02) * 6)
        pygame.draw.line(screen, (17, 19, 38), (0, y + offset), (WIDTH, y + offset))

    for x in range(0, WIDTH, 40):
        offset = int(math.cos(t + x * 0.02) * 6)
        pygame.draw.line(screen, (17, 19, 38), (x + offset, 0), (x + offset, HEIGHT))

    # Soft decorative orbs
    for i, color in enumerate([BLUE, RED, PURPLE]):
        cx = int(WIDTH * (0.2 + i * 0.28) + math.sin(t * 0.7 + i) * 25)
        cy = int(120 + math.cos(t * 0.8 + i * 1.7) * 28)
        for radius in range(68, 18, -14):
            faded = tuple(max(0, c // (radius // 12 + 2)) for c in color)
            pygame.draw.circle(screen, faded, (cx, cy), radius, 1)


def draw_top_bar(title):
    skin = get_skin()
    rounded_rect((28, 22, WIDTH - 56, 58), (17, 19, 36), 18)
    rounded_rect((28, 22, WIDTH - 56, 58), BORDER, 18, 2)
    draw_text(title, font_body, WHITE, 55, 51, center=False)
    draw_text(f"Coins: {coins}", font_body, YELLOW, WIDTH - 185, 51)
    draw_text(f"Skin: {skin['name']}", font_small, MUTED, WIDTH // 2, 52)


def draw_card(rect, title=None, accent=BLUE):
    rounded_rect(rect, PANEL, 22)
    rounded_rect(rect, BORDER, 22, 2)
    pygame.draw.rect(screen, accent, (rect.x + 18, rect.y + 14, 64, 4), border_radius=4)
    if title:
        draw_text(title, font_body, WHITE, rect.x + 22, rect.y + 32, center=False)


# ------------------------------------------------------------
# Particle system
# ------------------------------------------------------------


def add_particles(x, y, color, count=18, speed=3.0):
    for _ in range(count):
        angle = random.uniform(0, math.tau)
        velocity = random.uniform(0.8, speed)
        particles.append(
            {
                "x": float(x),
                "y": float(y),
                "vx": math.cos(angle) * velocity,
                "vy": math.sin(angle) * velocity,
                "life": random.randint(22, 45),
                "max_life": 45,
                "radius": random.randint(2, 5),
                "color": color,
            }
        )


def update_and_draw_particles():
    for p in particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vx"] *= 0.97
        p["vy"] *= 0.97
        p["life"] -= 1

        if p["life"] <= 0:
            particles.remove(p)
            continue

        fade = p["life"] / p["max_life"]
        color = tuple(max(0, min(255, int(c * fade))) for c in p["color"])
        pygame.draw.circle(screen, color, (int(p["x"]), int(p["y"])), max(1, int(p["radius"] * fade)))


# ------------------------------------------------------------
# Game logic
# ------------------------------------------------------------


def has_effect(name):
    return name in active_effects and active_effects[name] > pygame.time.get_ticks()


def clamp_paddle(paddle):
    if paddle.top < 0:
        paddle.top = 0
    if paddle.bottom > HEIGHT:
        paddle.bottom = HEIGHT


def resize_paddle(paddle, height):
    center_y = paddle.centery
    paddle.height = height
    paddle.centery = center_y
    clamp_paddle(paddle)


def reset_ball(direction=None):
    global ball_vx, ball_vy

    ball.center = (WIDTH // 2, HEIGHT // 2)
    speed = current_difficulty()["ball_speed"]

    if game_mode == "Local 2P":
        speed = 6.6

    if direction is None:
        direction = random.choice([-1, 1])

    ball_vx = speed * direction
    ball_vy = random.choice([-4.6, -3.4, 3.4, 4.6])


def reset_positions():
    resize_paddle(left_paddle, PADDLE_HEIGHT)
    resize_paddle(right_paddle, PADDLE_HEIGHT)
    left_paddle.centery = HEIGHT // 2
    right_paddle.centery = HEIGHT // 2
    reset_ball()


def start_match():
    global screen_state, left_score, right_score, last_touch, powerup, next_powerup_time
    global active_effects, particles, winner, match_reward_given, left_direction, right_direction

    left_score = 0
    right_score = 0
    left_direction = 0
    right_direction = 0
    last_touch = "left"
    powerup = None
    active_effects = {}
    particles = []
    winner = None
    match_reward_given = False
    reset_positions()
    next_powerup_time = pygame.time.get_ticks() + 3000
    screen_state = "game"
    play_sound("click")


def finish_match(match_winner):
    global screen_state, winner, coins, match_reward_given

    winner = match_winner
    screen_state = "game_over"

    if not match_reward_given:
        if game_mode == "Solo vs AI":
            reward = 25 if match_winner == "left" else 8
        else:
            reward = 14

        coins += reward
        match_reward_given = True
        save_game()
        add_notification(f"+{reward} coins", YELLOW)

    if match_winner == "left":
        play_sound("win")
    else:
        play_sound("lose")


def get_left_speed():
    speed = PLAYER_SPEED
    if has_effect("ice_left"):
        speed *= 0.52
    return speed


def get_right_speed():
    if game_mode == "Solo vs AI":
        speed = current_difficulty()["enemy_speed"]
    else:
        speed = PLAYER_SPEED

    if has_effect("ice_right"):
        speed *= 0.52

    return speed


def move_paddles():
    left_paddle.y += int(left_direction * get_left_speed())
    clamp_paddle(left_paddle)

    if game_mode == "Solo vs AI":
        speed = get_right_speed()
        prediction_error = 0

        if current_difficulty()["name"] == "Easy":
            prediction_error = math.sin(pygame.time.get_ticks() / 260) * 25
        elif current_difficulty()["name"] == "Normal":
            prediction_error = math.sin(pygame.time.get_ticks() / 350) * 14

        target = ball.centery + prediction_error
        if right_paddle.centery < target - 11:
            right_paddle.y += int(speed)
        elif right_paddle.centery > target + 11:
            right_paddle.y -= int(speed)
    else:
        right_paddle.y += int(right_direction * get_right_speed())

    clamp_paddle(right_paddle)


def bounce_from_paddle(paddle, side):
    global ball_vx, ball_vy, last_touch

    skin = get_skin()
    color = skin["p1"] if side == "left" else skin["p2"]

    if side == "left":
        ball.left = paddle.right
        ball_vx = abs(ball_vx) * 1.045
    else:
        ball.right = paddle.left
        ball_vx = -abs(ball_vx) * 1.045

    offset = (ball.centery - paddle.centery) / (paddle.height / 2)
    ball_vy = offset * 8.4
    last_touch = side

    add_particles(ball.centerx, ball.centery, color, 18, 4.0)
    play_sound("hit")


def move_ball():
    global ball_vx, ball_vy, left_score, right_score

    ball.x += int(ball_vx)
    ball.y += int(ball_vy)

    if ball.top <= 0:
        ball.top = 0
        ball_vy *= -1
        add_particles(ball.centerx, ball.top + 5, WHITE, 10, 2.4)
        play_sound("wall")

    if ball.bottom >= HEIGHT:
        ball.bottom = HEIGHT
        ball_vy *= -1
        add_particles(ball.centerx, ball.bottom - 5, WHITE, 10, 2.4)
        play_sound("wall")

    if ball.colliderect(left_paddle) and ball_vx < 0:
        bounce_from_paddle(left_paddle, "left")

    if ball.colliderect(right_paddle) and ball_vx > 0:
        bounce_from_paddle(right_paddle, "right")

    if ball.left <= -40:
        right_score += 1
        play_sound("score")
        add_particles(28, ball.centery, RED, 24, 4.6)
        reset_ball(direction=1)

    if ball.right >= WIDTH + 40:
        left_score += 1
        play_sound("score")
        add_particles(WIDTH - 28, ball.centery, BLUE, 24, 4.6)
        reset_ball(direction=-1)

    if left_score >= WIN_SCORE:
        finish_match("left")

    if right_score >= WIN_SCORE:
        finish_match("right")


def spawn_powerup():
    global powerup

    size = 56
    power = random.choice(POWERUPS)
    powerup = {
        "type": power,
        "rect": pygame.Rect(
            random.randint(WIDTH // 2 - 250, WIDTH // 2 + 250),
            random.randint(125, HEIGHT - 125),
            size,
            size,
        ),
        "spawn_time": pygame.time.get_ticks(),
    }


def collect_powerup():
    global powerup, next_powerup_time, ball_vx, ball_vy

    if powerup is None:
        return

    power_id = powerup["type"]["id"]
    now = pygame.time.get_ticks()

    if power_id == "big":
        if last_touch == "left":
            resize_paddle(left_paddle, BIG_PADDLE_HEIGHT)
            active_effects["big_left"] = now + 6500
            add_notification("BIG paddle for Player 1", GREEN)
        else:
            resize_paddle(right_paddle, BIG_PADDLE_HEIGHT)
            active_effects["big_right"] = now + 6500
            add_notification("BIG paddle for Player 2", GREEN)

    elif power_id == "slow":
        if not has_effect("slow_ball"):
            ball_vx *= 0.64
            ball_vy *= 0.64
        active_effects["slow_ball"] = now + 4600
        add_notification("SLOW ball", YELLOW)

    elif power_id == "ice":
        if last_touch == "left":
            active_effects["ice_right"] = now + 5200
            add_notification("ICE on Player 2", PURPLE)
        else:
            active_effects["ice_left"] = now + 5200
            add_notification("ICE on Player 1", PURPLE)

    elif power_id == "boost":
        ball_vx *= 1.35
        ball_vy *= 1.20
        add_notification("BOOST shot", ORANGE)

    add_particles(powerup["rect"].centerx, powerup["rect"].centery, powerup["type"]["color"], 36, 5.0)
    powerup = None
    next_powerup_time = now + random.randint(5500, 9000)
    play_sound("power")


def update_powerups():
    global powerup, next_powerup_time

    now = pygame.time.get_ticks()

    if powerup is None and now >= next_powerup_time:
        spawn_powerup()

    if powerup is not None:
        if now - powerup["spawn_time"] > 8500:
            powerup = None
            next_powerup_time = now + random.randint(4000, 7000)
        elif ball.colliderect(powerup["rect"]):
            collect_powerup()


def update_effects():
    global ball_vx, ball_vy

    now = pygame.time.get_ticks()
    expired = [name for name, end in active_effects.items() if now >= end]

    for name in expired:
        active_effects.pop(name, None)

        if name == "big_left":
            resize_paddle(left_paddle, PADDLE_HEIGHT)
        elif name == "big_right":
            resize_paddle(right_paddle, PADDLE_HEIGHT)
        elif name == "slow_ball":
            ball_vx /= 0.64
            ball_vy /= 0.64


def update_game():
    update_effects()
    update_powerups()
    move_paddles()
    move_ball()


# ------------------------------------------------------------
# Drawing game
# ------------------------------------------------------------


def draw_powerup():
    if powerup is None:
        return

    rect = powerup["rect"]
    power = powerup["type"]
    pulse = 1 + math.sin(pygame.time.get_ticks() / 130) * 0.08
    draw_rect = rect.inflate(int(rect.width * (pulse - 1)), int(rect.height * (pulse - 1)))

    rounded_rect(draw_rect, power["color"], 16)
    rounded_rect(draw_rect, WHITE, 16, 3)
    draw_text(power["label"], font_small, BLACK, draw_rect.centerx, draw_rect.centery)


def active_effect_labels():
    labels = []
    if has_effect("big_left"):
        labels.append("P1 BIG")
    if has_effect("big_right"):
        labels.append("P2 BIG")
    if has_effect("slow_ball"):
        labels.append("SLOW")
    if has_effect("ice_left"):
        labels.append("P1 ICE")
    if has_effect("ice_right"):
        labels.append("P2 ICE")
    return labels


def draw_game():
    skin = get_skin()
    draw_background()

    # Center line
    for y in range(0, HEIGHT, 36):
        pygame.draw.rect(screen, (85, 89, 120), (WIDTH // 2 - 2, y, 4, 18), border_radius=3)

    # Paddles and ball
    rounded_rect(left_paddle, skin["p1"], 8)
    rounded_rect(right_paddle, skin["p2"], 8)
    pygame.draw.ellipse(screen, skin["ball"], ball)
    pygame.draw.ellipse(screen, skin["p1"] if last_touch == "left" else skin["p2"], ball, 3)

    draw_powerup()
    update_and_draw_particles()

    # HUD
    draw_text(left_score, font_h1, skin["p1"], WIDTH // 4, 56)
    draw_text(right_score, font_h1, skin["p2"], WIDTH * 3 // 4, 56)

    draw_text(game_mode, font_small, MUTED, WIDTH // 2, 28)
    if game_mode == "Solo vs AI":
        draw_text(f"Difficulty: {current_difficulty()['name']}", font_small, MUTED, WIDTH // 2, 54)

    controls = "P1: W/S   |   P2: ↑/↓" if game_mode == "Local 2P" else "W/S = move   |   P = pause   |   ESC = quit"
    draw_text(controls, font_small, MUTED, WIDTH // 2, HEIGHT - 26)

    labels = active_effect_labels()
    if labels:
        draw_text("Effects: " + "  •  ".join(labels), font_small, WHITE, WIDTH // 2, HEIGHT - 56)

    draw_notifications()


# ------------------------------------------------------------
# Screen drawing
# ------------------------------------------------------------


def menu_buttons():
    x = 74
    y = 175
    w = 310
    h = 58
    gap = 18
    return [
        Button("play", "Play", (x, y, w, h), get_skin()["accent"]),
        Button("mode", f"Mode: {game_mode}", (x, y + (h + gap), w, h), GREEN),
        Button("difficulty", f"Difficulty: {current_difficulty()['name']}", (x, y + 2 * (h + gap), w, h), YELLOW, disabled=(game_mode == "Local 2P")),
        Button("shop", "Skin Shop", (x, y + 3 * (h + gap), w, h), PURPLE),
        Button("settings", "Settings", (x, y + 4 * (h + gap), w, h), BLUE),
        Button("quit", "Quit", (x, y + 5 * (h + gap), w, h), RED),
    ]


def draw_menu():
    draw_background()
    draw_top_bar("Main Menu")

    draw_text("NEON PONG", font_title, WHITE, WIDTH // 2, 123)
    draw_text("ARCADE DELUXE", font_h2, get_skin()["accent"], WIDTH // 2, 185)

    for button in menu_buttons():
        button.draw()

    # Big preview card
    card = pygame.Rect(440, 235, 520, 310)
    draw_card(card, "Game Preview", get_skin()["accent"])

    preview_area = pygame.Rect(card.x + 30, card.y + 72, card.width - 60, 160)
    rounded_rect(preview_area, (11, 13, 29), 18)
    rounded_rect(preview_area, BORDER, 18, 2)

    # Mini pong preview
    skin = get_skin()
    mini_left = pygame.Rect(preview_area.x + 48, preview_area.centery - 35, 10, 70)
    mini_right = pygame.Rect(preview_area.right - 58, preview_area.centery - 35, 10, 70)
    mini_ball_x = int(preview_area.centerx + math.sin(pygame.time.get_ticks() / 420) * 130)
    mini_ball_y = int(preview_area.centery + math.cos(pygame.time.get_ticks() / 530) * 48)

    rounded_rect(mini_left, skin["p1"], 5)
    rounded_rect(mini_right, skin["p2"], 5)
    pygame.draw.circle(screen, skin["ball"], (mini_ball_x, mini_ball_y), 11)

    draw_text("Power-ups, particles, coins, skins and 2-player mode.", font_small, MUTED, card.centerx, card.y + 255)
    draw_text("Tip: play matches to earn coins for skins.", font_small, YELLOW, card.centerx, card.y + 283)

    draw_notifications()


def shop_buttons():
    return [
        Button("prev", "‹", (72, 552, 72, 52), BLUE),
        Button("next", "›", (156, 552, 72, 52), BLUE),
        Button("buy_select", "Buy / Select", (250, 552, 240, 52), GREEN),
        Button("back", "Back", (800, 552, 160, 52), RED),
    ]


def draw_shop():
    draw_background()
    draw_top_bar("Skin Shop")

    draw_text("SKIN SHOP", font_h1, WHITE, WIDTH // 2, 125)
    draw_text("Unlock skins with coins earned from matches.", font_body, MUTED, WIDTH // 2, 172)

    skin = SKINS[shop_cursor]
    is_unlocked = skin["name"] in unlocked_skins
    is_selected = shop_cursor == selected_skin_index

    card = pygame.Rect(110, 220, 820, 280)
    draw_card(card, skin["name"], skin["accent"])

    preview = pygame.Rect(card.x + 40, card.y + 74, 330, 150)
    rounded_rect(preview, (10, 12, 29), 18)
    rounded_rect(preview, skin["accent"], 18, 2)

    rounded_rect((preview.x + 48, preview.centery - 48, 18, 96), skin["p1"], 8)
    rounded_rect((preview.right - 66, preview.centery - 48, 18, 96), skin["p2"], 8)
    pygame.draw.circle(screen, skin["ball"], preview.center, 15)

    status = "Selected" if is_selected else "Unlocked" if is_unlocked else f"Price: {skin['cost']} coins"
    status_color = GREEN if is_unlocked else YELLOW

    draw_text(status, font_h2, status_color, card.x + 515, card.y + 105)
    draw_text(f"Skin {shop_cursor + 1} / {len(SKINS)}", font_body, MUTED, card.x + 515, card.y + 155)

    if not is_unlocked:
        missing = max(0, skin["cost"] - coins)
        draw_text(f"Missing: {missing} coins", font_small, MUTED, card.x + 515, card.y + 202)
    else:
        draw_text("Ready to use in every mode.", font_small, MUTED, card.x + 515, card.y + 202)

    for button in shop_buttons():
        button.draw()

    draw_notifications()


def settings_buttons():
    sound_text = "Sound: ON" if sounds_enabled else "Sound: OFF"
    return [
        Button("sound", sound_text, (WIDTH // 2 - 160, 250, 320, 58), GREEN),
        Button("reset", "Reset Save", (WIDTH // 2 - 160, 326, 320, 58), YELLOW),
        Button("back", "Back", (WIDTH // 2 - 160, 456, 320, 58), RED),
    ]


def draw_settings():
    draw_background()
    draw_top_bar("Settings")

    draw_text("SETTINGS", font_h1, WHITE, WIDTH // 2, 130)
    draw_text("Simple options for the arcade experience.", font_body, MUTED, WIDTH // 2, 178)

    for button in settings_buttons():
        button.draw()

    draw_text("Reset Save removes coins and locked skins.", font_small, MUTED, WIDTH // 2, 410)
    draw_notifications()


def pause_buttons():
    return [
        Button("resume", "Resume", (WIDTH // 2 - 155, 260, 310, 56), GREEN),
        Button("restart", "Restart", (WIDTH // 2 - 155, 332, 310, 56), BLUE),
        Button("menu", "Main Menu", (WIDTH // 2 - 155, 404, 310, 56), RED),
    ]


def draw_pause():
    draw_game()
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(190)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))

    draw_text("PAUSED", font_title, WHITE, WIDTH // 2, 168)
    for button in pause_buttons():
        button.draw()


def game_over_buttons():
    return [
        Button("restart", "Play Again", (WIDTH // 2 - 155, 342, 310, 58), GREEN),
        Button("shop", "Open Shop", (WIDTH // 2 - 155, 418, 310, 58), PURPLE),
        Button("menu", "Main Menu", (WIDTH // 2 - 155, 494, 310, 58), RED),
    ]


def draw_game_over():
    draw_background()
    draw_top_bar("Match Finished")

    if winner == "left":
        title = "PLAYER 1 WINS!"
        color = get_skin()["p1"]
    else:
        title = "PLAYER 2 WINS!" if game_mode == "Local 2P" else "AI WINS!"
        color = get_skin()["p2"]

    draw_text(title, font_title, color, WIDTH // 2, 150)
    draw_text(f"{left_score} : {right_score}", font_h1, WHITE, WIDTH // 2, 245)
    draw_text("Coins were saved automatically.", font_body, MUTED, WIDTH // 2, 296)

    for button in game_over_buttons():
        button.draw()

    draw_notifications()


# ------------------------------------------------------------
# Actions
# ------------------------------------------------------------


def toggle_mode():
    global game_mode
    game_mode = "Local 2P" if game_mode == "Solo vs AI" else "Solo vs AI"
    add_notification(f"Mode changed to {game_mode}", GREEN)
    play_sound("click")


def next_difficulty():
    global difficulty_index
    difficulty_index = (difficulty_index + 1) % len(DIFFICULTIES)
    add_notification(f"Difficulty: {current_difficulty()['name']}", YELLOW)
    play_sound("click")


def toggle_sound():
    global sounds_enabled
    sounds_enabled = not sounds_enabled
    save_game()
    if sounds_enabled:
        play_sound("click")
    add_notification("Sound ON" if sounds_enabled else "Sound OFF", GREEN if sounds_enabled else MUTED)


def buy_or_select_skin():
    global coins, selected_skin_index

    skin = SKINS[shop_cursor]

    if skin["name"] in unlocked_skins:
        selected_skin_index = shop_cursor
        save_game()
        add_notification(f"Selected: {skin['name']}", GREEN)
        play_sound("click")
        return

    if coins >= skin["cost"]:
        coins -= skin["cost"]
        unlocked_skins.add(skin["name"])
        selected_skin_index = shop_cursor
        save_game()
        add_notification(f"Unlocked: {skin['name']}", GREEN)
        play_sound("buy")
    else:
        add_notification("Not enough coins", RED)
        play_sound("score")


def reset_save():
    global coins, unlocked_skins, selected_skin_index
    coins = 0
    unlocked_skins = {"Classic Neon"}
    selected_skin_index = 0
    save_game()
    add_notification("Save reset", YELLOW)
    play_sound("score")


# ------------------------------------------------------------
# Event handling
# ------------------------------------------------------------


def handle_mouse(event):
    global screen_state, shop_cursor

    if screen_state == "menu":
        for button in menu_buttons():
            if button.clicked(event):
                if button.key == "play":
                    start_match()
                elif button.key == "mode":
                    toggle_mode()
                elif button.key == "difficulty":
                    next_difficulty()
                elif button.key == "shop":
                    screen_state = "shop"
                    play_sound("click")
                elif button.key == "settings":
                    screen_state = "settings"
                    play_sound("click")
                elif button.key == "quit":
                    pygame.quit()
                    sys.exit()

    elif screen_state == "shop":
        for button in shop_buttons():
            if button.clicked(event):
                if button.key == "prev":
                    shop_cursor = (shop_cursor - 1) % len(SKINS)
                    play_sound("click")
                elif button.key == "next":
                    shop_cursor = (shop_cursor + 1) % len(SKINS)
                    play_sound("click")
                elif button.key == "buy_select":
                    buy_or_select_skin()
                elif button.key == "back":
                    screen_state = "menu"
                    play_sound("click")

    elif screen_state == "settings":
        for button in settings_buttons():
            if button.clicked(event):
                if button.key == "sound":
                    toggle_sound()
                elif button.key == "reset":
                    reset_save()
                elif button.key == "back":
                    screen_state = "menu"
                    play_sound("click")

    elif screen_state == "pause":
        for button in pause_buttons():
            if button.clicked(event):
                if button.key == "resume":
                    screen_state = "game"
                    play_sound("click")
                elif button.key == "restart":
                    start_match()
                elif button.key == "menu":
                    screen_state = "menu"
                    play_sound("click")

    elif screen_state == "game_over":
        for button in game_over_buttons():
            if button.clicked(event):
                if button.key == "restart":
                    start_match()
                elif button.key == "shop":
                    screen_state = "shop"
                    play_sound("click")
                elif button.key == "menu":
                    screen_state = "menu"
                    play_sound("click")


def handle_keydown(event):
    global screen_state, left_direction, right_direction, shop_cursor

    if event.key == pygame.K_ESCAPE:
        if screen_state in {"shop", "settings", "game_over"}:
            screen_state = "menu"
            play_sound("click")
        elif screen_state == "game":
            screen_state = "pause"
            play_sound("click")
        elif screen_state == "pause":
            screen_state = "game"
            play_sound("click")
        else:
            pygame.quit()
            sys.exit()

    if screen_state == "menu":
        if event.key == pygame.K_SPACE:
            start_match()
        elif event.key == pygame.K_m:
            toggle_mode()
        elif event.key == pygame.K_d and game_mode == "Solo vs AI":
            next_difficulty()
        elif event.key == pygame.K_s:
            screen_state = "shop"
            play_sound("click")

    elif screen_state == "shop":
        if event.key in {pygame.K_LEFT, pygame.K_a}:
            shop_cursor = (shop_cursor - 1) % len(SKINS)
            play_sound("click")
        elif event.key in {pygame.K_RIGHT, pygame.K_d}:
            shop_cursor = (shop_cursor + 1) % len(SKINS)
            play_sound("click")
        elif event.key in {pygame.K_RETURN, pygame.K_SPACE}:
            buy_or_select_skin()

    elif screen_state == "settings":
        if event.key == pygame.K_m:
            toggle_sound()

    elif screen_state == "game":
        if event.key == pygame.K_w:
            left_direction = -1
        elif event.key == pygame.K_s:
            left_direction = 1
        elif event.key == pygame.K_UP:
            right_direction = -1
        elif event.key == pygame.K_DOWN:
            right_direction = 1
        elif event.key == pygame.K_p:
            screen_state = "pause"
            play_sound("click")

    elif screen_state == "pause":
        if event.key == pygame.K_p:
            screen_state = "game"
            play_sound("click")
        elif event.key == pygame.K_r:
            start_match()
        elif event.key == pygame.K_m:
            screen_state = "menu"
            play_sound("click")

    elif screen_state == "game_over":
        if event.key == pygame.K_r:
            start_match()
        elif event.key == pygame.K_s:
            screen_state = "shop"
            play_sound("click")
        elif event.key == pygame.K_m:
            screen_state = "menu"
            play_sound("click")


def handle_keyup(event):
    global left_direction, right_direction

    if event.key == pygame.K_w and left_direction == -1:
        left_direction = 0
    elif event.key == pygame.K_s and left_direction == 1:
        left_direction = 0
    elif event.key == pygame.K_UP and right_direction == -1:
        right_direction = 0
    elif event.key == pygame.K_DOWN and right_direction == 1:
        right_direction = 0


# ------------------------------------------------------------
# Main loop
# ------------------------------------------------------------


def main():
    global screen_state

    load_save()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                handle_mouse(event)
            elif event.type == pygame.KEYDOWN:
                handle_keydown(event)
            elif event.type == pygame.KEYUP:
                handle_keyup(event)

        if screen_state == "menu":
            draw_menu()
        elif screen_state == "shop":
            draw_shop()
        elif screen_state == "settings":
            draw_settings()
        elif screen_state == "game":
            update_game()
            draw_game()
        elif screen_state == "pause":
            draw_pause()
        elif screen_state == "game_over":
            draw_game_over()

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
