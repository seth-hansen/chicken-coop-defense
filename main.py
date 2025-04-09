import pygame
import sys
import os # Needed for path joining
from tower import Tower
from enemy import Enemy
from map import get_path
from projectile import Projectile
import random # Needed for path generation call

# --- Constants ---
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60
ASSETS_DIR = "assets"

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
GRAY = (100, 100, 100)
PATH_COLOR = (101, 67, 33) # Dirt Brown

# Define game states
MENU = 'menu'
GAME = 'game'
GAME_OVER = 'game_over'

# --- Asset Loading Helper ---
def load_image(filename, default_color=(200, 200, 200), alpha=True):
    """Loads an image, returns a placeholder surface on error."""
    path = os.path.join(ASSETS_DIR, filename)
    try:
        image = pygame.image.load(path)
        if alpha:
             image = image.convert_alpha()
        else:
             image = image.convert()
        print(f"Loaded image: {path}")
        return image
    except pygame.error as e:
        print(f"Warning: Could not load image '{path}': {e}")
        # Return a simple colored square as a placeholder
        placeholder = pygame.Surface((30, 30)) # Adjust size as needed
        placeholder.fill(default_color)
        return placeholder

# --- Resizing Helper ---
def scale_image_aspect_ratio(image, target_width=None, target_height=None):
    """Scales an image to a target width OR height, maintaining aspect ratio."""
    original_width, original_height = image.get_size()
    aspect_ratio = original_height / original_width

    if target_width:
        new_width = target_width
        new_height = int(new_width * aspect_ratio)
    elif target_height:
        new_height = target_height
        new_width = int(new_height / aspect_ratio)
    else:
        # No target size specified, return original
        return image

    try:
        scaled_image = pygame.transform.smoothscale(image, (new_width, new_height))
        return scaled_image
    except Exception as e:
        print(f"Warning: Could not scale image: {e}. Returning original.")
        return image

# --- Game Setup ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Chicken Coop Defense') # Updated Title
clock = pygame.time.Clock()

# Fonts
ui_font = pygame.font.Font(None, 36)
game_font = pygame.font.Font(None, 90) # Larger font for larger screen

# Load Game Assets
background_tile = load_image("grass.png", default_color=GREEN, alpha=False)
path_tile = load_image("dirt.png", default_color=PATH_COLOR, alpha=False)

# Load and Scale Tower Image
raw_tower_img = load_image("tower.png", default_color=GREEN)
TOWER_TARGET_WIDTH = 64
tower_img = scale_image_aspect_ratio(raw_tower_img, target_width=TOWER_TARGET_WIDTH)

# Load and Scale Projectile Image
raw_projectile_img = load_image("egg.png", default_color=YELLOW)
PROJECTILE_TARGET_WIDTH = 12 # Make eggs much smaller
projectile_img = scale_image_aspect_ratio(raw_projectile_img, target_width=PROJECTILE_TARGET_WIDTH)

# Load and Scale Enemy Images
ENEMY_TARGET_WIDTH = 60
ENEMY_IMAGES = {}
for enemy_type, fallback_color in [('raccoon', GRAY), ('cat', (200, 150, 100))]:
    raw_img = load_image(f"{enemy_type}.png", default_color=fallback_color)
    ENEMY_IMAGES[enemy_type] = scale_image_aspect_ratio(raw_img, target_width=ENEMY_TARGET_WIDTH)

# --- Game Variables (initialized globally, reset in functions) ---
state = MENU
selected_option = 0
selected_difficulty = 'Easy'

# Difficulty settings
difficulty_health = {'Easy': 20, 'Medium': 10, 'Hard': 5}

# Game state variables (reset when game starts)
towers = []
enemies = []
projectiles = []
current_path = []
player_gold = 0
player_health = 0
score = 0
wave_number = 0
enemies_to_spawn_this_wave = 0
enemies_spawned_this_wave = 0
wave_timer = 0
spawn_timer = 0
time_scale = 1.0 # Add time scale variable, default to normal speed

build_mode = False
preview_tower = None

# Wave Settings
TIME_BETWEEN_WAVES = 10 * FPS
SPAWN_INTERVAL = 1.5 * FPS

# Menu options
menu_options = ['Easy', 'Medium', 'Hard']

# --- Helper Functions ---
def reset_game_state():
    """Resets all variables for a new game."""
    global towers, enemies, projectiles, current_path, player_gold, player_health
    global score, wave_number, enemies_to_spawn_this_wave, enemies_spawned_this_wave
    global wave_timer, spawn_timer, build_mode, preview_tower, time_scale

    towers = []
    enemies = []
    projectiles = []
    # Pass new screen dimensions to path generation
    current_path = get_path(SCREEN_WIDTH, SCREEN_HEIGHT)
    player_gold = 100
    player_health = difficulty_health[selected_difficulty]
    score = 0
    wave_number = 0 # Start at wave 0, will increment to 1 immediately
    enemies_to_spawn_this_wave = 0
    enemies_spawned_this_wave = 0
    wave_timer = 0 # Start first wave immediately
    spawn_timer = 0
    time_scale = 1.0 # Reset time scale on new game
    build_mode = False
    preview_tower = None
    start_next_wave() # Prepare the first wave

def start_next_wave():
    """Sets up variables for the next wave."""
    global wave_number, enemies_to_spawn_this_wave, enemies_spawned_this_wave, wave_timer
    wave_number += 1
    enemies_to_spawn_this_wave = 5 + wave_number * 2 # Example: Increase enemies per wave
    enemies_spawned_this_wave = 0
    # Ensure wave timer uses the base time, time_scale applied during countdown
    wave_timer = TIME_BETWEEN_WAVES
    spawn_timer = 0 # Reset within-wave spawn timer
    print(f"Starting Wave {wave_number} with {enemies_to_spawn_this_wave} enemies.")

def draw_menu():
    # Tile background (optional for menu, could just be solid color)
    for y in range(0, SCREEN_HEIGHT, background_tile.get_height()):
        for x in range(0, SCREEN_WIDTH, background_tile.get_width()):
            screen.blit(background_tile, (x, y))

    title_text = game_font.render('Chicken Coop Defense', True, WHITE)
    title_bg = pygame.Surface((title_text.get_width() + 40, title_text.get_height() + 20))
    title_bg.set_alpha(180)
    title_bg.fill(BLACK)
    # Adjust positioning for larger screen
    screen.blit(title_bg, (SCREEN_WIDTH // 2 - title_bg.get_width() // 2, 150 - 10))
    screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 150))

    for i, option in enumerate(menu_options):
        color = WHITE if i == selected_option else GRAY
        text = game_font.render(option, True, color)
        # Adjust positioning
        screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 400 + i * 120))

def draw_game_over():
    # Tile background
    for y in range(0, SCREEN_HEIGHT, background_tile.get_height()):
        for x in range(0, SCREEN_WIDTH, background_tile.get_width()):
            screen.blit(background_tile, (x, y))

    game_over_text = game_font.render('Game Over - Coop Overrun!', True, RED)
    score_text = ui_font.render(f'Final Score: {score}', True, WHITE)
    restart_text = ui_font.render('Press Enter to return to Menu', True, WHITE)
    # Adjust positioning
    screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 300))
    screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 450))
    screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 500))

def is_on_path(pos, path_segments, buffer=25): # Increased buffer slightly
    mouse_pos_vec = pygame.Vector2(pos)
    for i in range(len(path_segments) - 1):
        p1 = pygame.Vector2(path_segments[i])
        p2 = pygame.Vector2(path_segments[i+1])
        # Simple bounding box check first
        if not (min(p1.x, p2.x) - buffer <= mouse_pos_vec.x <= max(p1.x, p2.x) + buffer and
                min(p1.y, p2.y) - buffer <= mouse_pos_vec.y <= max(p1.y, p2.y) + buffer):
            continue
        # Line segment distance check
        d = p2 - p1
        if d.length_squared() == 0:
            if (mouse_pos_vec - p1).length_squared() < buffer**2:
                return True
            continue
        t = ((mouse_pos_vec.x - p1.x) * d.x + (mouse_pos_vec.y - p1.y) * d.y) / d.length_squared()
        t = max(0, min(1, t))
        closest_point = p1 + t * d
        if (mouse_pos_vec - closest_point).length_squared() < buffer**2:
            return True
    return False

def draw_game_ui():
    # Gold
    gold_text = ui_font.render(f'Gold: {player_gold}', True, YELLOW)
    screen.blit(gold_text, (10, 10))
    # Health
    health_text = ui_font.render(f'Health: {player_health}', True, RED)
    screen.blit(health_text, (10, 40))
    # Score
    score_text = ui_font.render(f'Score: {score}', True, WHITE)
    screen.blit(score_text, (10, 70))
    # Wave Info
    wave_info_y = 100
    wave_num_text = ui_font.render(f'Wave: {wave_number}', True, WHITE)
    screen.blit(wave_num_text, (10, wave_info_y))
    # Show timer or wave progress
    if enemies_spawned_this_wave < enemies_to_spawn_this_wave or len(enemies) > 0:
        # Wave in progress
        remaining_text = ui_font.render(f'Enemies: {len(enemies)}/{enemies_spawned_this_wave}/{enemies_to_spawn_this_wave}', True, WHITE)
        screen.blit(remaining_text, (10, wave_info_y + 30))
    else:
        # Between waves
        timer_seconds = max(0, wave_timer // FPS) # Ensure timer doesn't show negative
        next_wave_text = ui_font.render(f'Next wave in: {timer_seconds}s', True, CYAN)
        screen.blit(next_wave_text, (10, wave_info_y + 30))

    # Build Mode indicator
    ui_build_mode_y = wave_info_y + 60
    if build_mode:
        build_mode_text = ui_font.render('Build Mode (B)', True, CYAN)
        screen.blit(build_mode_text, (10, ui_build_mode_y))

    # Time Scale Display
    speed_text = f'Speed: {time_scale:.1f}x (S/F)'
    time_scale_text = ui_font.render(speed_text, True, WHITE)
    screen.blit(time_scale_text, (10, ui_build_mode_y + 30))

def draw_tiled_background_and_path(path_width=40): # Width of the dirt path
    """Tiles the background and draws the path using path_tile."""
    # Tile the main background
    bg_w, bg_h = background_tile.get_size()
    for y in range(0, SCREEN_HEIGHT, bg_h):
        for x in range(0, SCREEN_WIDTH, bg_w):
            screen.blit(background_tile, (x, y))

    # Draw the path - Simplified: Use thick lines for now to verify path logic
    if len(current_path) > 1:
        pygame.draw.lines(screen, PATH_COLOR, False, current_path, path_width * 2) # Draw wide path lines
        # TODO: Re-implement path tiling if needed, ensuring correct texture coords and blending

# --- Main Game Loop ---
running = True
while running:
    dt = clock.tick(FPS)
    mouse_pos = pygame.mouse.get_pos()

    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            pygame.quit()
            sys.exit()

        # Keyboard Input
        if event.type == pygame.KEYDOWN:
            if state == MENU:
                if event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(menu_options)
                elif event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(menu_options)
                elif event.key == pygame.K_RETURN:
                    selected_difficulty = menu_options[selected_option]
                    state = GAME
                    reset_game_state()

            elif state == GAME:
                if event.key == pygame.K_b: # Toggle build mode
                    build_mode = not build_mode
                    if build_mode:
                        preview_tower = Tower(mouse_pos[0], mouse_pos[1], tower_img)
                    else:
                        preview_tower = None
                elif event.key == pygame.K_f: # Increase speed
                    time_scale = min(time_scale * 2, 16.0) # Cap at 16x
                    print(f"Time Scale set to: {time_scale}x")
                elif event.key == pygame.K_s: # Decrease speed (or reset to 1x)
                    if time_scale > 1.0:
                        # Halve speed, ensuring it doesn't go below 1.0 due to floating point
                        time_scale = max(1.0, time_scale / 2)
                    else:
                        time_scale = 1.0
                    print(f"Time Scale set to: {time_scale}x")

            elif state == GAME_OVER:
                if event.key == pygame.K_RETURN:
                    state = MENU

        # Mouse Input
        if event.type == pygame.MOUSEBUTTONDOWN:
            if state == GAME and build_mode and preview_tower:
                if event.button == 1:
                    can_place = player_gold >= preview_tower.cost and not is_on_path(mouse_pos, current_path)
                    if can_place:
                        towers.append(Tower(mouse_pos[0], mouse_pos[1], tower_img))
                        player_gold -= preview_tower.cost
                    else:
                        print("Cannot place tower: Invalid location or insufficient gold.")

    # --- State Logic & Updates ---
    if state == GAME:
        # Wave Management (Spawn with correct images)
        if enemies_spawned_this_wave < enemies_to_spawn_this_wave:
            spawn_timer -= time_scale
            if spawn_timer <= 0:
                enemy_type_to_spawn = 'cat' if wave_number % 3 == 0 else 'raccoon'
                if random.random() < 0.3 and wave_number > 2:
                     enemy_type_to_spawn = 'cat' if enemy_type_to_spawn == 'raccoon' else 'raccoon'
                # Pass the corresponding pre-loaded image
                enemy_image_to_use = ENEMY_IMAGES[enemy_type_to_spawn]
                enemies.append(Enemy(current_path, wave_number, enemy_image_to_use))
                enemies_spawned_this_wave += 1
                spawn_timer += SPAWN_INTERVAL
        elif len(enemies) == 0:
            # Between waves phase (all spawned and all defeated)
            wave_timer -= time_scale # Use time_scale
            if wave_timer <= 0:
                start_next_wave()

        # Update Enemies
        for enemy in enemies[:]:
            reached_end = enemy.move(time_scale) # Check if enemy moved to the end this frame

            # Reduce health FIRST if enemy reached the end this frame
            if reached_end:
                player_health -= 1
                print(f"Enemy reached end! Health: {player_health}")
                # enemy.die(killed_by_player=False) was called inside move()
                # So the enemy IS dead now, but we process the health loss immediately.

            # NOW check if the enemy is dead (either by tower or reaching end)
            if enemy.is_dead:
                if not reached_end: # Only award points/gold if killed by player/tower
                    player_gold += enemy.reward
                    score += enemy.points_value
                # Always remove the enemy if it's dead, regardless of how
                enemies.remove(enemy)
                # No continue needed here, loop will naturally proceed after removal

        # Check for Game Over
        if player_health <= 0:
            state = GAME_OVER
            print("Game Over! Health reached zero.")
            continue # Skip rest of GAME updates/drawing

        # Update Towers
        for tower in towers:
            # Pass the loaded projectile image when creating
            tower.update(enemies, projectiles, time_scale, projectile_img)

        # Update Projectiles
        for proj in projectiles[:]:
            proj.move(time_scale)
            if not proj.is_active:
                projectiles.remove(proj)

        # Update Preview Tower
        if build_mode and preview_tower:
            # Update position using mouse_pos, image is already set
            preview_tower.x, preview_tower.y = mouse_pos
            preview_tower.rect.center = mouse_pos

    # --- Drawing --- #
    screen.blit(background_tile, (0, 0))

    if state == MENU:
        draw_menu()
    elif state == GAME:
        # Draw tiled background and path first
        draw_tiled_background_and_path()

        # Draw Towers, Enemies, Projectiles
        for tower in towers:
            tower.draw(screen)
        for enemy in enemies:
            enemy.draw(screen)
        for proj in projectiles:
            proj.draw(screen)

        # Draw Preview Tower
        if build_mode and preview_tower:
            can_place = player_gold >= preview_tower.cost and not is_on_path(mouse_pos, current_path)
            color = GREEN if can_place else RED
            # Draw semi-transparent range
            range_surface = pygame.Surface((preview_tower.range * 2, preview_tower.range * 2), pygame.SRCALPHA)
            pygame.draw.circle(range_surface, (*color, 50), (preview_tower.range, preview_tower.range), preview_tower.range)
            screen.blit(range_surface, (preview_tower.rect.centerx - preview_tower.range, preview_tower.rect.centery - preview_tower.range))
            # Draw tower image preview (centered)
            img_rect = preview_tower.image.get_rect(center=preview_tower.rect.center)
            # Optional: tint the image red/green based on validity
            preview_img_copy = preview_tower.image.copy()
            tint_color = (*color, 150) # Add alpha for tinting effect
            preview_img_copy.fill(tint_color, special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(preview_img_copy, img_rect)

        # Draw UI
        draw_game_ui()

    elif state == GAME_OVER:
        draw_game_over()

    pygame.display.flip()

pygame.quit()
sys.exit() 