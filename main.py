import pygame
import sys

# Inicializar Pygame
pygame.init()

# ----------- Configuración básica -----------
WIDTH, HEIGHT = 900, 500
is_fullscreen = False
window_size = (WIDTH, HEIGHT)
WINDOW = None
SCREEN = pygame.Surface((WIDTH, HEIGHT))

def apply_window_mode(size=None):
    global WINDOW, window_size
    if size is None:
        size = window_size
    else:
        window_size = size
    WINDOW = pygame.display.set_mode(size, pygame.RESIZABLE)

def refresh_window_mode():
    apply_window_mode()

def toggle_fullscreen():
    global is_fullscreen, WINDOW
    is_fullscreen = not is_fullscreen
    if is_fullscreen:
        WINDOW = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        refresh_window_mode()

refresh_window_mode()
pygame.display.set_caption("La gran piedra - Trabajando en equipo")

CLOCK = pygame.time.Clock()
FPS = 60

# Colores
WHITE   = (255, 255, 255)
BLACK   = (0, 0, 0)
GRAY    = (180, 180, 180)
DARK_GRAY = (100, 100, 100)
GREEN   = (80, 200, 120)
BLUE    = (80, 140, 220)
BROWN   = (160, 120, 60)
YELLOW  = (250, 220, 100)
RED     = (220, 80, 80)
SKY_TOP = (120, 180, 255)
SKY_BOTTOM = (200, 235, 255)
GROUND_TOP = (140, 210, 140)
GROUND_BOTTOM = (90, 150, 90)
SUN_COLOR = (255, 245, 180)
CLOUD_COLOR = (245, 245, 245)
PIXEL_SIZE = 8

FONT = pygame.font.SysFont("arial", 24)
FONT_SMALL = pygame.font.SysFont("arial", 18)
FONT_BIG = pygame.font.SysFont("arial", 32)

# ----------- Objetos del juego -----------

# Personaje principal
player_width, player_height = 40, 60
PLAYER_START_X = 150
PLAYER_START_Y = HEIGHT - player_height - 40
player_x = PLAYER_START_X
player_y = PLAYER_START_Y
player_speed = 4

# Piedra
stone_width, stone_height = 120, 90
STONE_START_X = 350
stone_x = STONE_START_X
stone_y = HEIGHT - stone_height - 40
stone_base_x = STONE_START_X  # para animaciÃ³n de "temblor"

# Aldea (casita)
village_rect = pygame.Rect(20, HEIGHT - 220, 130, 160)

# Suelo
ground_y = HEIGHT - 40

# Amigos
friends = []
friend_spacing = 45
has_team = False

# Estados lÃ³gicos
show_heavy_message = False
heavy_message_timer = 0
HEAVY_MESSAGE_DURATION = 3000  # ms

show_village_dialog = False
village_dialog_accepted = False
village_visible = False

stone_can_move = False
stone_moved = False
game_completed = False
smooth_push_active = False

# Para animaciÃ³n de empuje
push_animation = False
push_timer = 0
PUSH_DURATION = 400  # ms

# Para mover la piedra cuando ya hay equipo
stone_push_progress = 0
STONE_PUSH_TARGET = 200  # distancia total a empujar
STONE_PUSH_SPEED = 140  # pixeles por segundo cuando el equipo empuja

# ----------- Funciones auxiliares -----------

def draw_text(text, x, y, font, color=BLACK, center=False):
    surface = font.render(text, True, color)
    rect = surface.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    SCREEN.blit(surface, rect)

def quantize_color(color, step=16):
    quantized = []
    for c in color:
        value = int(step * round(c / step))
        if value < 0:
            value = 0
        elif value > 255:
            value = 255
        quantized.append(value)
    return tuple(quantized)

def draw_pixel_star(cx, cy, size, color):
    pattern = [
        (0, -2), (-1, -1), (0, -1), (1, -1),
        (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0),
        (0, 1), (-1, 1), (1, 1),
        (0, 2)
    ]
    for px, py in pattern:
        rect = pygame.Rect(cx + px * size, cy + py * size, size, size)
        pygame.draw.rect(SCREEN, color, rect)

def lerp_color(color_a, color_b, t):
    return tuple(int(color_a[i] + (color_b[i] - color_a[i]) * t) for i in range(3))

def draw_background():
    tile = PIXEL_SIZE
    for y in range(0, ground_y, tile):
        t = y / max(1, ground_y)
        base_color = lerp_color(SKY_TOP, SKY_BOTTOM, t)
        color = quantize_color(base_color, 24)
        pygame.draw.rect(SCREEN, color, (0, y, WIDTH, tile))

    sun_rect = pygame.Rect(WIDTH - 180, 30, 64, 64)
    for i in range(4):
        color = quantize_color((255, 230 - i * 15, 140 + i * 5), 16)
        pygame.draw.rect(SCREEN, color, sun_rect.inflate(-i * 8, -i * 8))

    cloud_blocks = [
        (120, 70, 64, 24),
        (150, 60, 32, 16),
        (280, 60, 64, 24),
        (320, 50, 32, 16),
        (420, 80, 72, 24),
        (460, 70, 32, 16),
    ]
    for x, y, w, h in cloud_blocks:
        pygame.draw.rect(SCREEN, CLOUD_COLOR, (x, y, w, h))
        pygame.draw.rect(SCREEN, WHITE, (x, y, w, h), 2)

    mountains = [
        (160, ground_y - 60, 200, (100, 130, 180)),
        (320, ground_y - 80, 260, (90, 120, 150)),
        (560, ground_y - 70, 220, (110, 140, 180)),
    ]
    for base_x, peak_y, width, color in mountains:
        height = ground_y - peak_y
        for layer_y in range(0, height, tile):
            span = width - layer_y * 2
            if span <= 0:
                continue
            y = ground_y - layer_y - tile
            x = base_x - span // 2
            pygame.draw.rect(SCREEN, color, (x, y, span, tile))

    for y in range(ground_y, HEIGHT, tile):
        t = (y - ground_y) / max(1, HEIGHT - ground_y)
        base_color = lerp_color(GROUND_TOP, GROUND_BOTTOM, t)
        color = quantize_color(base_color, 16)
        pygame.draw.rect(SCREEN, color, (0, y, WIDTH, tile))
    draw_grass_tufts()

def draw_grass_tufts():
    tile = PIXEL_SIZE
    colors = [(70, 140, 80), (90, 160, 100)]
    for x in range(0, WIDTH, tile * 3):
        for i, color in enumerate(colors):
            rect = pygame.Rect(x + i * tile // 2, ground_y + 2 - i * tile // 2, tile // 2, tile)
            pygame.draw.rect(SCREEN, color, rect)

def draw_speech_cloud(rect, direction="left", color=WHITE):
    bubble = rect.inflate(30, 20)
    pygame.draw.ellipse(SCREEN, color, bubble)
    pygame.draw.ellipse(SCREEN, BLACK, bubble, 3)

    tail = None
    if direction == "left":
        tail = [
            (bubble.left + 20, bubble.bottom - 12),
            (bubble.left - 10, bubble.bottom + 12),
            (bubble.left + 40, bubble.bottom),
        ]
    elif direction == "right":
        tail = [
            (bubble.right - 20, bubble.bottom - 12),
            (bubble.right + 12, bubble.bottom + 10),
            (bubble.right - 40, bubble.bottom),
        ]
    elif direction == "down":
        tail = [
            (bubble.centerx - 15, bubble.bottom - 6),
            (bubble.centerx, bubble.bottom + 20),
            (bubble.centerx + 15, bubble.bottom - 6),
        ]
    elif direction == "up":
        tail = [
            (bubble.centerx - 15, bubble.top + 6),
            (bubble.centerx, bubble.top - 18),
            (bubble.centerx + 15, bubble.top + 6),
        ]

    if tail:
        pygame.draw.polygon(SCREEN, color, tail)
        pygame.draw.polygon(SCREEN, BLACK, tail, 3)

def draw_player(x, y, color=BLUE):
    base_color = quantize_color(color, 16)
    darker = tuple(max(0, c - 40) for c in base_color)
    outline = (30, 30, 30)

    shadow = pygame.Rect(x - 8, y + player_height + 6, player_width + 16, 6)
    pygame.draw.rect(SCREEN, (20, 30, 20), shadow)

    torso = pygame.Rect(x, y + 8, player_width, player_height - 8)
    pygame.draw.rect(SCREEN, base_color, torso)
    pygame.draw.rect(SCREEN, outline, torso, 3)
    shading = torso.copy()
    shading.width = player_width // 2
    pygame.draw.rect(SCREEN, darker, shading)

    belt = pygame.Rect(x, y + player_height - 22, player_width, 8)
    pygame.draw.rect(SCREEN, (80, 60, 40), belt)
    pygame.draw.rect(SCREEN, outline, belt, 2)

    arm_width = 8
    left_arm = pygame.Rect(x - arm_width + 2, y + 18, arm_width, 20)
    right_arm = pygame.Rect(x + player_width - 2, y + 18, arm_width, 20)
    for arm in (left_arm, right_arm):
        pygame.draw.rect(SCREEN, base_color, arm)
        pygame.draw.rect(SCREEN, outline, arm, 2)

    head = pygame.Rect(x + player_width // 2 - 14, y - 24, 28, 24)
    pygame.draw.rect(SCREEN, YELLOW, head)
    pygame.draw.rect(SCREEN, outline, head, 3)

    eye_rect = pygame.Rect(head.x + 6, head.y + 8, 4, 4)
    pygame.draw.rect(SCREEN, BLACK, eye_rect)
    pygame.draw.rect(SCREEN, BLACK, eye_rect.move(12, 0))
    mouth = pygame.Rect(head.x + 6, head.bottom - 8, 16, 4)
    pygame.draw.rect(SCREEN, (150, 60, 60), mouth)

    cap = pygame.Rect(head.x + 2, head.y - 6, 24, 8)
    pygame.draw.rect(SCREEN, base_color, cap)
    pygame.draw.rect(SCREEN, outline, cap, 2)

def draw_friend(x, y, index):
    # amigos en otro color
    friend_colors = [GREEN, RED, (200, 100, 200), (100, 200, 200)]
    color = friend_colors[index % len(friend_colors)]
    draw_player(x, y, color)

def draw_stone(offset_x=0):
    rect = pygame.Rect(stone_x + offset_x, stone_y, stone_width, stone_height)
    shadow = pygame.Rect(rect.x - 18, rect.bottom - 8, rect.width + 36, 12)
    pygame.draw.rect(SCREEN, (25, 25, 25), shadow)

    for row in range(0, stone_height, PIXEL_SIZE):
        row_color = quantize_color((130 + row, 130 + row // 2, 130 + row // 3), 16)
        row_height = min(PIXEL_SIZE, stone_height - row)
        row_rect = pygame.Rect(rect.x, rect.y + row, rect.width, row_height)
        pygame.draw.rect(SCREEN, row_color, row_rect)

    pygame.draw.rect(SCREEN, BLACK, rect, 3)

    chip_color = (180, 180, 190)
    cracks = [
        pygame.Rect(rect.x + 12, rect.y + 24, 18, PIXEL_SIZE),
        pygame.Rect(rect.x + 40, rect.y + 40, 24, PIXEL_SIZE),
        pygame.Rect(rect.x + 72, rect.y + 18, 18, PIXEL_SIZE),
    ]
    for crack in cracks:
        pygame.draw.rect(SCREEN, chip_color, crack)

def draw_village():
    base_rect = pygame.Rect(village_rect.x, village_rect.y + 20, village_rect.width, village_rect.height - 20)
    pygame.draw.rect(SCREEN, (170, 120, 90), base_rect)
    pygame.draw.rect(SCREEN, BLACK, base_rect, 3)

    roof_height = 30
    for step in range(roof_height // PIXEL_SIZE):
        width = base_rect.width + step * PIXEL_SIZE * 2
        x = base_rect.x - step * PIXEL_SIZE
        y = base_rect.y - (step + 1) * PIXEL_SIZE
        pygame.draw.rect(SCREEN, RED, (x, y, width, PIXEL_SIZE))
        pygame.draw.rect(SCREEN, BLACK, (x, y, width, PIXEL_SIZE), 1)

    window_color = (240, 246, 255)
    window_size = 20
    for offset in (-30, 30):
        win = pygame.Rect(base_rect.centerx + offset - window_size // 2,
                          base_rect.y + 20,
                          window_size,
                          window_size)
        pygame.draw.rect(SCREEN, window_color, win)
        pygame.draw.rect(SCREEN, BLACK, win, 2)
        pygame.draw.line(SCREEN, BLACK, (win.centerx, win.top + 2), (win.centerx, win.bottom - 2), 2)
        pygame.draw.line(SCREEN, BLACK, (win.left + 2, win.centery), (win.right - 2, win.centery), 2)

    door = pygame.Rect(base_rect.centerx - 12, base_rect.bottom - 34, 24, 34)
    pygame.draw.rect(SCREEN, (110, 80, 60), door)
    pygame.draw.rect(SCREEN, BLACK, door, 2)
    pygame.draw.rect(SCREEN, (200, 170, 120), (door.right - 8, door.centery - 2, 4, 4))

    path = pygame.Rect(base_rect.centerx - 18, base_rect.bottom, 36, 24)
    pygame.draw.rect(SCREEN, (210, 190, 150), path)
    pygame.draw.rect(SCREEN, BLACK, path, 2)

    draw_text("Aldea", village_rect.centerx, village_rect.y + 8, FONT_SMALL, BLACK, center=True)

def draw_victory_panel():
    panel = pygame.Rect(WIDTH // 2 - 260, 140, 520, 170)
    pygame.draw.rect(SCREEN, (248, 240, 215), panel)
    border_colors = [(120, 80, 60), (200, 180, 140)]
    for i, color in enumerate(border_colors):
        pygame.draw.rect(SCREEN, color, panel.inflate(-i * 6, -i * 6), 3)

    banner = pygame.Rect(panel.x + 40, panel.y + 18, panel.width - 80, 48)
    pygame.draw.rect(SCREEN, (210, 70, 80), banner)
    pygame.draw.rect(SCREEN, BLACK, banner, 3)
    draw_text("¡Lo logramos!", banner.centerx, banner.centery, FONT_BIG, WHITE, center=True)

    stars = [
        (panel.x + 60, panel.y + 40, (255, 230, 120)),
        (panel.right - 80, panel.y + 40, (255, 210, 140)),
    ]
    for x, y, color in stars:
        draw_pixel_star(x, y, 4, color)

    lines = [
        "Juntos movimos la gran piedra.",
        "Como equipo somos imparables.",
    ]
    base_y = banner.bottom + 28
    for i, text in enumerate(lines):
        draw_text(text, panel.centerx, base_y + i * 28, FONT_SMALL, BLACK, center=True)

    confetti = [
        (panel.x + 20, panel.y + 20, (255, 180, 120)),
        (panel.x + 90, panel.y + 110, (160, 200, 255)),
        (panel.right - 60, panel.bottom - 30, (200, 250, 180)),
        (panel.right - 120, panel.y + 70, (255, 210, 160)),
    ]
    for x, y, color in confetti:
        pygame.draw.rect(SCREEN, color, (x, y, PIXEL_SIZE, PIXEL_SIZE))
        pygame.draw.rect(SCREEN, BLACK, (x, y, PIXEL_SIZE, PIXEL_SIZE), 1)

def get_village_dialog_rect():
    width, height = 230, 160
    x = village_rect.right + 20
    y = village_rect.top - 10
    return pygame.Rect(x, y, width, height)

def get_button_yes_rect():
    dialog_rect = get_village_dialog_rect()
    return pygame.Rect(dialog_rect.centerx - 60, dialog_rect.bottom - 55, 120, 40)

def is_near_stone(px, py):
    player_rect = pygame.Rect(px, py, player_width, player_height)
    stone_rect = pygame.Rect(stone_x, stone_y, stone_width, stone_height)
    # un pequeÃ±o margen
    stone_rect.inflate_ip(40, 40)
    return player_rect.colliderect(stone_rect)

def is_in_village(px, py):
    player_rect = pygame.Rect(px, py, player_width, player_height)
    return player_rect.colliderect(village_rect)

def handle_push_attempt():
    global show_heavy_message, heavy_message_timer
    global push_animation, push_timer
    global stone_can_move, stone_push_progress, stone_moved, game_completed
    global smooth_push_active, village_visible

    if not stone_can_move:
        # Primera fase: no se mueve, solo tiembla
        show_heavy_message = True
        heavy_message_timer = pygame.time.get_ticks()
        push_animation = True
        push_timer = pygame.time.get_ticks()
        village_visible = True
    else:
        # Segunda fase: la piedra sÃ­ se mueve
        push_animation = True
        push_timer = pygame.time.get_ticks()
        smooth_push_active = True

def stone_move(dx):
    global stone_x
    stone_x += dx

def reset_game():
    global player_x, player_y, friends, has_team
    global show_heavy_message, heavy_message_timer
    global show_village_dialog, village_dialog_accepted, village_visible
    global stone_can_move, stone_moved, game_completed, smooth_push_active
    global push_animation, push_timer
    global stone_push_progress, stone_x

    player_x = PLAYER_START_X
    player_y = PLAYER_START_Y
    friends = []
    has_team = False

    show_heavy_message = False
    heavy_message_timer = 0
    show_village_dialog = False
    village_dialog_accepted = False
    village_visible = False

    stone_can_move = False
    stone_moved = False
    game_completed = False
    smooth_push_active = False

    push_animation = False
    push_timer = 0
    stone_push_progress = 0
    stone_x = stone_base_x

# ----------- Bucle principal -----------

def main():
    global player_x, player_y
    global show_heavy_message, stone_can_move
    global show_village_dialog, village_dialog_accepted, has_team
    global push_animation, push_timer
    global stone_x, stone_base_x
    global game_completed, smooth_push_active, stone_moved
    global stone_push_progress, village_visible

    reset_game()
    running = True

    while running:
        dt = CLOCK.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.VIDEORESIZE and not is_fullscreen:
                apply_window_mode(event.size)
                continue

            # Clics del mouse
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos

                # Clic sobre la piedra = intento de empujar
                stone_rect = pygame.Rect(stone_x, stone_y, stone_width, stone_height)
                if stone_rect.collidepoint(mx, my) and is_near_stone(player_x, player_y) and not game_completed:
                    handle_push_attempt()


            # Teclas
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    reset_game()
                elif event.key == pygame.K_f:
                    toggle_fullscreen()
                elif event.key == pygame.K_SPACE:
                    player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
                    if show_village_dialog and not village_dialog_accepted:
                        village_dialog_accepted = True
                        has_team = True
                        show_village_dialog = False
                        friends.clear()
                        for i in range(3):
                            fx = player_x - (i + 1) * friend_spacing
                            fy = player_y
                            friends.append([fx, fy])
                    elif (not village_dialog_accepted and village_visible
                          and player_rect.colliderect(village_rect)):
                        show_village_dialog = True
                    elif is_near_stone(player_x, player_y) and not game_completed:
                        handle_push_attempt()

        # Movimiento del personaje
        keys = pygame.key.get_pressed()
        dx = 0
        dy = 0

        if keys[pygame.K_LEFT]:
            dx = -player_speed
        if keys[pygame.K_RIGHT]:
            dx = player_speed
        if keys[pygame.K_DOWN]:
            dy = player_speed

        stone_rect = pygame.Rect(stone_x, stone_y, stone_width, stone_height)

        # Movimiento horizontal con colisiÃ³n frente a la piedra
        next_x = player_x + dx
        player_rect = pygame.Rect(next_x, player_y, player_width, player_height)
        if player_rect.colliderect(stone_rect):
            if dx > 0:
                next_x = stone_rect.left - player_width
            elif dx < 0:
                next_x = stone_rect.right
        player_x = next_x

        # Movimiento vertical con colisiÃ³n frente a la piedra
        next_y = player_y + dy
        player_rect = pygame.Rect(player_x, next_y, player_width, player_height)
        if player_rect.colliderect(stone_rect):
            if dy > 0:
                next_y = stone_rect.top - player_height
            elif dy < 0:
                next_y = stone_rect.bottom
        player_y = next_y

        # Limitar a la pantalla y el suelo
        if player_x < 0:
            player_x = 0
        if player_x + player_width > WIDTH:
            player_x = WIDTH - player_width
        if player_y < ground_y - player_height:
            # puede subir un poco, pero no salir arriba de todo
            if player_y < 80:
                player_y = 80
        if player_y > ground_y - player_height:
            player_y = ground_y - player_height

        # Actualizar la posiciÃ³n de los amigos para que se alineen detrÃ¡s y se muevan sincronizados
        if has_team:
            # Los amigos siguen al jugador con offsets fijos
            for i, friend in enumerate(friends):
                target_x = player_x - (i + 1) * friend_spacing
                target_y = player_y

                # InterpolaciÃ³n suave
                lerp_factor = 0.2
                friend[0] += (target_x - friend[0]) * lerp_factor
                friend[1] += (target_y - friend[1]) * lerp_factor

        # Mantener el diálogo de la aldea sólo mientras el jugador permanezca allí
        player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
        if (show_village_dialog and not village_dialog_accepted
                and not player_rect.colliderect(village_rect)):
            show_village_dialog = False

        # Si ya tiene equipo y vuelve a la piedra, activar la posibilidad de moverla
        if has_team and is_near_stone(player_x, player_y):
            stone_can_move = True

        # Manejo del temporizador del mensaje de piedra pesada
        if show_heavy_message:
            now = pygame.time.get_ticks()
            if now - heavy_message_timer > HEAVY_MESSAGE_DURATION:
                show_heavy_message = False

        # AnimaciÃ³n de empuje (hacer temblar la piedra)
        stone_shake_offset = 0
        if push_animation:
            now = pygame.time.get_ticks()
            elapsed = now - push_timer
            if elapsed < PUSH_DURATION:
                # PequeÃ±a oscilaciÃ³n
                if (elapsed // 60) % 2 == 0:
                    stone_shake_offset = 3
                else:
                    stone_shake_offset = -3
            else:
                push_animation = False
                stone_shake_offset = 0
        if smooth_push_active and stone_push_progress < STONE_PUSH_TARGET:
            move_step = STONE_PUSH_SPEED * (dt / 1000)
            remaining = STONE_PUSH_TARGET - stone_push_progress
            actual_move = min(remaining, move_step)
            stone_move(actual_move)
            stone_push_progress += actual_move
            if stone_push_progress >= STONE_PUSH_TARGET and not stone_moved:
                stone_moved = True
                game_completed = True
                smooth_push_active = False

        # ----------- DIBUJO EN PANTALLA -----------

        draw_background()

        # Aldea
        if village_visible:
            draw_village()

        # Camino desbloqueado (aparece mÃ¡s claro si la piedra ya se moviÃ³)
        if stone_moved:
            pygame.draw.rect(SCREEN, (210, 190, 150), (stone_base_x + STONE_PUSH_TARGET, ground_y, 300, 40))

        # Piedra
        draw_stone(stone_shake_offset)

        # Personaje principal
        draw_player(player_x, player_y)

        # Amigos (si existen)
        if has_team:
            for i, friend in enumerate(friends):
                draw_friend(friend[0], friend[1], i)

        # Mensajes en pantalla
        draw_text("Usa las flechas para moverte.", 20, 10, FONT_SMALL)
        draw_text("Pulsa ESPACIO o haz clic sobre la piedra para intentar moverla.", 20, 35, FONT_SMALL)
        #draw_text("Cuando llegues a la aldea, presiona ESPACIO para pedir ayuda.", 20, 60, FONT_SMALL)
        # Mensaje de esfuerzo / piedra pesada
        if show_heavy_message:
            bubble_rect = pygame.Rect(player_x + player_width + 20, player_y - 90, 260, 70)
            clamp_zone = pygame.Rect(20, 20, WIDTH - 40, ground_y - 60)
            bubble_rect.clamp_ip(clamp_zone)
            direction = "left" if bubble_rect.centerx >= player_x else "right"
            draw_speech_cloud(bubble_rect, direction)
            heavy_lines = ["Es muy pesada...", "No puedo solo."]
            for i, text in enumerate(heavy_lines):
                draw_text(text, bubble_rect.centerx, bubble_rect.y + 22 + i * 22, FONT_SMALL, BLACK, center=True)

        # Diálogo en la aldea
        if show_village_dialog and not village_dialog_accepted:
            dialog_bg = get_village_dialog_rect()
            button_yes_rect = get_button_yes_rect()
            draw_speech_cloud(dialog_bg, direction="left")
            draw_text("¿Nosotros te ayudamos?", dialog_bg.centerx, dialog_bg.y + 20, FONT_SMALL, BLACK, center=True)
            draw_text("¿Vamos juntos?", dialog_bg.centerx, dialog_bg.y + 55, FONT_SMALL, BLACK, center=True)

            pygame.draw.rect(SCREEN, GREEN, button_yes_rect, border_radius=6)
            pygame.draw.rect(SCREEN, BLACK, button_yes_rect, 2, border_radius=6)
            # draw_text("Pulsa ESPACIO", button_yes_rect.centerx, button_yes_rect.centery - 6, FONT_SMALL, BLACK, center=True)
            draw_text("Sí, vamos", button_yes_rect.centerx, button_yes_rect.centery - 6, FONT_SMALL, BLACK, center=True)
            #draw_text("para decir \"Sí, vamos\"", button_yes_rect.centerx, button_yes_rect.centery + 16, FONT_SMALL, BLACK, center=True)


        # Indicador de equipo cerca de la piedra
        if stone_can_move and not game_completed:
            draw_text("Ahora intentemos juntos empujar la piedra.", WIDTH // 2, 120, FONT_SMALL, BLACK, center=True)

        draw_text("R: Reiniciar | F: Pantalla completa", WIDTH // 2, HEIGHT - 15, FONT_SMALL, BLACK, center=True)

        # Mensaje final de celebraciA3n
        if game_completed:
            draw_victory_panel()

        window_surface = pygame.display.get_surface()
        if window_surface:
            window_size_current = window_surface.get_size()
            if window_size_current != SCREEN.get_size():
                scaled_surface = pygame.transform.smoothscale(SCREEN, window_size_current)
                window_surface.blit(scaled_surface, (0, 0))
            else:
                window_surface.blit(SCREEN, (0, 0))
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
