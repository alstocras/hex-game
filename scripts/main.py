import pygame
import pygame.freetype
import math
import os
import random

BASE_DIR = os.path.dirname(__file__)

pygame.init()
pygame.mixer.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("2π/3")

HEX_SIZE = 40
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (80, 80, 80)
DARK_GRAY = (40, 40, 40)

PALETTE = [
    (0, 51, 160),
    (180, 0, 0),
    (0, 140, 0),
    (180, 100, 0),
    (120, 0, 180),
    (0, 160, 160),
    (200, 200, 0),
    (200, 200, 200),
]

fontFace = "assets/fonts/font.ttf"
font_large = pygame.freetype.Font(fontFace, 64)
font_med = pygame.freetype.Font(fontFace, 36)
font_small = pygame.freetype.Font(fontFace, 28)
font_title = pygame.freetype.Font("assets/fonts/cmunrm.ttf", 64)

MUSIC_MENU = "assets/audio/music/menu.ogg"
MUSIC_GAME = "assets/audio/music/game.ogg"
MUSIC_WINNER = "assets/audio/music/winner.ogg"

current_music = None

def play_music(path):
    global current_music
    if current_music == path:
        return
    pygame.mixer.music.load(path)
    pygame.mixer.music.play(-1)
    current_music = path

def roll_dice():
    a = random.randint(1, 6)
    b = random.randint(1, 6)
    return a, b

def is_trapped(painted, color):
    owned = [k for k, v in painted.items() if v == color]
    if len(owned) == 0:
        return False
    for h in owned:
        for n in hex_neighbors(*h):
            if n not in painted:
                return False
    return True

def check_eliminations(painted, player_colors, active_players):
    still_active = []
    for i in active_players:
        color = player_colors[i]
        owned = [k for k, v in painted.items() if v == color]
        if len(owned) == 0 or not is_trapped(painted, color):
            still_active.append(i)
    return still_active

def get_winner_by_score(painted, player_colors, active_players):
    best = max(active_players, key=lambda i: sum(1 for v in painted.values() if v == player_colors[i]))
    return best

def ai_move(painted, ai_color, human_color):
    ai_hexes = [k for k, v in painted.items() if v == ai_color]
    human_hexes = set(k for k, v in painted.items() if v == human_color)
    if len(ai_hexes) == 0:
        if human_hexes:
            start = random.choice(list(human_hexes))
            nearby = [n for n in hex_neighbors(*start) if n not in painted]
            if nearby:
                return random.choice(nearby)
        return (0, 0)
    candidates = set()
    for h in ai_hexes:
        for n in hex_neighbors(*h):
            if n not in painted:
                candidates.add(n)
    if not candidates:
        return None
    def score(h):
        neighbors = hex_neighbors(*h)
        blocking = sum(1 for n in neighbors if n in human_hexes)
        expanding = sum(1 for n in neighbors if n not in painted)
        return blocking * 2 + expanding
    return max(candidates, key=score)

def render_text(font, text, color):
    surf, _ = font.render(text, color)
    return surf

def hex_corners(cx, cy, size):
    corners = []
    for i in range(6):
        angle = 2 * math.pi / 6 * i
        corners.append((cx + size * math.cos(angle), cy + size * math.sin(angle)))
    return corners

def axial_to_pixel(q, r, size):
    x = size * (3/2 * q)
    y = size * (math.sqrt(3)/2 * q + math.sqrt(3) * r)
    return x, y

def pixel_to_axial(px, py, size):
    q = (2/3 * px) / size
    r = (-1/3 * px + math.sqrt(3)/3 * py) / size
    return cube_round(q, r)

def cube_round(q, r):
    s = -q - r
    rq, rr, rs = round(q), round(r), round(s)
    dq, dr, ds = abs(rq - q), abs(rr - r), abs(rs - s)
    if dq > dr and dq > ds:
        rq = -rr - rs
    elif dr > ds:
        rr = -rq - rs
    return (rq, rr)

def hex_neighbors(q, r):
    return [(q+1,r), (q-1,r), (q,r+1), (q,r-1), (q+1,r-1), (q-1,r+1)]

def get_visible_hexes(offset_x, offset_y, width, height, hex_size):
    margin = 2
    corners = [
        pixel_to_axial(-offset_x, -offset_y, hex_size),
        pixel_to_axial(width - offset_x, -offset_y, hex_size),
        pixel_to_axial(-offset_x, height - offset_y, hex_size),
        pixel_to_axial(width - offset_x, height - offset_y, hex_size),
    ]
    min_q = min(c[0] for c in corners) - margin
    max_q = max(c[0] for c in corners) + margin
    min_r = min(c[1] for c in corners) - margin
    max_r = max(c[1] for c in corners) + margin
    hexes = []
    for q in range(min_q, max_q + 1):
        for r in range(min_r, max_r + 1):
            hexes.append((q, r))
    return hexes

def draw_palette_picker(surface, palette, taken_colors, current_color=None):
    swatch_size = 40
    padding = 12
    cols = 4
    start_x = WIDTH // 2 - (cols * (swatch_size + padding)) // 2
    start_y = HEIGHT // 2 - 40
    rects = []
    for i, color in enumerate(palette):
        col = i % cols
        row = i // cols
        x = start_x + col * (swatch_size + padding)
        y = start_y + row * (swatch_size + padding)
        rect = pygame.Rect(x, y, swatch_size, swatch_size)
        if color in taken_colors:
            pygame.draw.rect(surface, (20, 20, 20), rect, border_radius=6)
            pygame.draw.line(surface, GRAY, rect.topleft, rect.bottomright, 2)
            pygame.draw.line(surface, GRAY, rect.topright, rect.bottomleft, 2)
        else:
            pygame.draw.rect(surface, color, rect, border_radius=6)
            if color == current_color:
                pygame.draw.rect(surface, WHITE, rect, 3, border_radius=6)
            rects.append((rect, color))
    return rects

def draw_palette(surface, palette, player_colors, current_player):
    swatch_size = 30
    padding = 8
    margin = 10
    total_width = len(palette) * (swatch_size + padding) - padding + 20
    panel_x = margin
    panel_y = surface.get_height() - swatch_size - padding * 2 - margin
    panel_w = total_width
    panel_h = swatch_size + padding * 2
    pygame.draw.rect(surface, (30, 30, 30), (panel_x, panel_y, panel_w, panel_h), border_radius=8)
    select_color = player_colors[current_player]
    rects = []
    for i, color in enumerate(palette):
        x = panel_x + 10 + i * (swatch_size + padding)
        y = panel_y + padding
        rect = pygame.Rect(x, y, swatch_size, swatch_size)
        if color == select_color:
            small = swatch_size // 2
            off = (swatch_size - small) // 2
            small_rect = pygame.Rect(x + off, y + off, small, small)
            pygame.draw.rect(surface, color, small_rect, border_radius=2)
        elif color in player_colors:
            pygame.draw.rect(surface, (20, 20, 20), rect, border_radius=4)
        else:
            pygame.draw.rect(surface, color, rect, border_radius=4)
            rects.append((rect, color))
    return rects

def draw_score(surface, player_colors, painted, ai_enabled, current_player, active_players):
    padding = 10
    swatch_size = 16
    line_height = 28
    num_players = len(player_colors)
    panel_h = num_players * line_height + padding * 2
    panel_w = 160
    panel_x = surface.get_width() - panel_w - 10
    panel_y = 50
    pygame.draw.rect(surface, (30, 30, 30), (panel_x, panel_y, panel_w, panel_h), border_radius=8)
    for i, color in enumerate(player_colors):
        count = sum(1 for v in painted.values() if v == color)
        if ai_enabled and i == 1:
            name = "AI"
        else:
            name = f"P{i}"
        y = panel_y + padding + i * line_height
        eliminated = i not in active_players
        draw_color = (40, 40, 40) if eliminated else color
        pygame.draw.rect(surface, draw_color, (panel_x + padding, y, swatch_size, swatch_size), border_radius=3)
        if i == current_player and not eliminated:
            pygame.draw.rect(surface, WHITE, (panel_x + padding, y, swatch_size, swatch_size), 2, border_radius=3)
        text_color = DARK_GRAY if eliminated else WHITE
        label = render_text(font_small, f"{name}: {count}", text_color)
        surface.blit(label, (panel_x + padding + swatch_size + 8, y))

def draw_dice(surface, dice, hexes_left):
    if dice is None:
        return
    a, b = dice
    d1 = render_text(font_large, str(a), WHITE)
    d2 = render_text(font_large, str(b), WHITE)
    times = render_text(font_large, "·", GRAY)
    remaining = render_text(font_small, f"{hexes_left} left", GRAY)
    dice_row_h = d1.get_height()
    panel_w = 160
    panel_h = dice_row_h + remaining.get_height() + 30
    panel_x = 10
    panel_y = 10
    pygame.draw.rect(surface, (30, 30, 30), (panel_x, panel_y, panel_w, panel_h), border_radius=8)
    total_w = d1.get_width() + times.get_width() + d2.get_width() + 16
    x = panel_x + (panel_w - total_w) // 2
    y = panel_y + 10
    surface.blit(d1, (x, y))
    x += d1.get_width() + 8
    surface.blit(times, (x, y + (d1.get_height() - times.get_height()) // 2))
    x += times.get_width() + 8
    surface.blit(d2, (x, y))
    rem_y = panel_y + 10 + dice_row_h + 6
    surface.blit(remaining, (panel_x + (panel_w - remaining.get_width()) // 2, rem_y))

def draw_end_game_button(surface):
    btn_w = 170
    btn_h = 30
    btn_x = surface.get_width() // 2 - btn_w // 2
    btn_y = 10
    rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
    pygame.draw.rect(surface, (60, 20, 20), rect, border_radius=6)
    pygame.draw.rect(surface, (120, 40, 40), rect, 2, border_radius=6)
    label = render_text(font_small, "end game", WHITE)
    surface.blit(label, (btn_x + (btn_w - label.get_width()) // 2, btn_y + (btn_h - label.get_height()) // 2))
    return rect

def end_turn(current_player, active_players):
    idx = active_players.index(current_player)
    next_idx = (idx + 1) % len(active_players)
    next_player = active_players[next_idx]
    a, b = roll_dice()
    return next_player, (a, b), a * b

painted = {}
offset_x, offset_y = WIDTH // 2, HEIGHT // 2
zoom = 1.0
MIN_ZOOM = 0.2
MAX_ZOOM = 3.0

panning = False
pan_start_mouse = (0, 0)
pan_start_offset = (0, 0)

state = "choose_players"
num_players = None
player_colors = []
active_players = []
setup_picking_player = 0
current_player = 0
ai_enabled = False
current_dice = None
hexes_left = 0
winner = None
winner_time = 0

clock = pygame.time.Clock()
running = True

while running:
    screen.fill(BLACK)
    hex_size = HEX_SIZE * zoom

    if state in ("choose_players", "choose_colors"):
        play_music(MUSIC_MENU)
    elif state == "game":
        play_music(MUSIC_GAME)
    elif state == "winner":
        play_music(MUSIC_WINNER)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.w, event.h

        if state == "game":
            if event.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                old_zoom = zoom
                zoom *= 1.1 ** event.y
                zoom = max(MIN_ZOOM, min(MAX_ZOOM, zoom))
                offset_x = mx - (mx - offset_x) * (zoom / old_zoom)
                offset_y = my - (my - offset_y) * (zoom / old_zoom)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                panning = True
                pan_start_mouse = event.pos
                pan_start_offset = (offset_x, offset_y)
            if event.type == pygame.MOUSEBUTTONUP and event.button == 3:
                panning = False
            if event.type == pygame.MOUSEMOTION and panning:
                dx = event.pos[0] - pan_start_mouse[0]
                dy = event.pos[1] - pan_start_mouse[1]
                offset_x = pan_start_offset[0] + dx
                offset_y = pan_start_offset[1] + dy
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                end_btn = pygame.Rect(WIDTH // 2 - 85, 10, 170, 30)
                if end_btn.collidepoint(mx, my):
                    winner = get_winner_by_score(painted, player_colors, active_players)
                    winner_time = pygame.time.get_ticks()
                    state = "winner"
                else:
                    select_color = player_colors[current_player]
                    hex_coord = pixel_to_axial(mx - offset_x, my - offset_y, hex_size)
                    already_painted = [k for k, v in painted.items() if v == select_color]
                    placed = False
                    if hexes_left > 0 and hex_coord not in painted:
                        if len(already_painted) == 0:
                            painted[hex_coord] = select_color
                            placed = True
                        elif any(n in already_painted for n in hex_neighbors(*hex_coord)):
                            painted[hex_coord] = select_color
                            placed = True
                    if placed:
                        hexes_left -= 1
                        active_players = check_eliminations(painted, player_colors, active_players)
                        if len(active_players) == 1:
                            winner = active_players[0]
                            winner_time = pygame.time.get_ticks()
                            state = "winner"
                        elif hexes_left == 0:
                            current_player, current_dice, hexes_left = end_turn(current_player, active_players)
                            if ai_enabled and current_player == 1:
                                ai_color = player_colors[1]
                                human_color = player_colors[0]
                                for _ in range(hexes_left):
                                    move = ai_move(painted, ai_color, human_color)
                                    if move:
                                        painted[move] = ai_color
                                active_players = check_eliminations(painted, player_colors, active_players)
                                if len(active_players) == 1:
                                    winner = active_players[0]
                                    winner_time = pygame.time.get_ticks()
                                    state = "winner"
                                else:
                                    current_player, current_dice, hexes_left = end_turn(current_player, active_players)

        elif state == "choose_players":
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                for i, n in enumerate([1, 2, 3, 4]):
                    btn = pygame.Rect(WIDTH//2 - 200 + i * 110, HEIGHT//2, 80, 50)
                    if btn.collidepoint(mx, my):
                        num_players = n
                        ai_enabled = num_players == 1
                        if ai_enabled:
                            num_players = 2
                        player_colors = [None] * num_players
                        state = "choose_colors"

        elif state == "choose_colors":
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                taken = [c for c in player_colors if c is not None]
                picker_rects = draw_palette_picker(screen, PALETTE, taken)
                for rect, color in picker_rects:
                    if rect.collidepoint(mx, my):
                        player_colors[setup_picking_player] = color
                        setup_picking_player += 1
                        if ai_enabled and setup_picking_player == 1:
                            remaining = [c for c in PALETTE if c not in player_colors]
                            player_colors[1] = random.choice(remaining)
                            setup_picking_player += 1
                        if setup_picking_player >= num_players:
                            current_player = 0
                            active_players = list(range(num_players))
                            offset_x, offset_y = WIDTH // 2, HEIGHT // 2
                            a, b = roll_dice()
                            current_dice = (a, b)
                            hexes_left = a * b
                            state = "game"
                        break

        elif state == "winner":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.time.get_ticks() - winner_time > 500:
                    painted = {}
                    player_colors = []
                    active_players = []
                    setup_picking_player = 0
                    current_player = 0
                    ai_enabled = False
                    current_dice = None
                    hexes_left = 0
                    winner = None
                    winner_time = 0
                    num_players = None
                    zoom = 1.0
                    offset_x, offset_y = WIDTH // 2, HEIGHT // 2
                    state = "choose_players"

    if state == "choose_players":
        title = render_text(font_title, "2π/3", WHITE)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 120))
        sub = render_text(font_med, "How many players?", GRAY)
        screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 - 40))
        for i, n in enumerate([1, 2, 3, 4]):
            btn = pygame.Rect(WIDTH//2 - 200 + i * 110, HEIGHT//2, 80, 50)
            pygame.draw.rect(screen, DARK_GRAY, btn, border_radius=8)
            label = render_text(font_med, str(n), WHITE)
            screen.blit(label, (btn.centerx - label.get_width()//2, btn.centery - label.get_height()//2))

    elif state == "choose_colors":
        taken = [c for c in player_colors if c is not None]
        title = render_text(font_med, f"Player {setup_picking_player}: pick your colour", WHITE)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 120))
        for i, c in enumerate(player_colors):
            if c is not None:
                swatch = pygame.Rect(WIDTH//2 - (num_players * 30)//2 + i*34, HEIGHT//2 - 70, 26, 26)
                pygame.draw.rect(screen, c, swatch, border_radius=4)
        draw_palette_picker(screen, PALETTE, taken)

    elif state == "game":
        for (q, r) in get_visible_hexes(offset_x, offset_y, WIDTH, HEIGHT, hex_size):
            px, py = axial_to_pixel(q, r, hex_size)
            cx, cy = px + offset_x, py + offset_y
            corners = hex_corners(cx, cy, hex_size - 2)
            COLORS = [BLACK, DARK_GRAY, GRAY]
            color = painted.get((q, r), COLORS[(q - r) % 3])
            pygame.draw.polygon(screen, color, corners)
            pygame.draw.polygon(screen, BLACK, corners, 2)
        draw_palette(screen, PALETTE, player_colors, current_player)
        draw_score(screen, player_colors, painted, ai_enabled, current_player, active_players)
        draw_dice(screen, current_dice, hexes_left)
        draw_end_game_button(screen)
        select_color = player_colors[current_player]
        label = render_text(font_small, f"Player {current_player}'s turn", WHITE)
        swatch_x = WIDTH - label.get_width() - 50
        swatch_y = 16
        pygame.draw.rect(screen, select_color, (swatch_x - 28, swatch_y, 20, 20), border_radius=4)
        screen.blit(label, (swatch_x, swatch_y))

    elif state == "winner":
        for (q, r) in get_visible_hexes(offset_x, offset_y, WIDTH, HEIGHT, hex_size):
            px, py = axial_to_pixel(q, r, hex_size)
            cx, cy = px + offset_x, py + offset_y
            corners = hex_corners(cx, cy, hex_size - 2)
            COLORS = [BLACK, DARK_GRAY, GRAY]
            color = painted.get((q, r), COLORS[(q - r) % 3])
            pygame.draw.polygon(screen, color, corners)
            pygame.draw.polygon(screen, BLACK, corners, 2)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        winner_color = player_colors[winner]
        if ai_enabled and winner == 1:
            winner_name = "AI"
        else:
            winner_name = f"Player {winner}"
        title = render_text(font_large, f"{winner_name} wins!", winner_color)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 60))
        sub = render_text(font_med, "click to play again", GRAY)
        screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 20))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()