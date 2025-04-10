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
BASE_GAME_SPEED = 5.0 # New constant for overall speed increase

# UI Constants
# # SIDEBAR_WIDTH = 150 # Removed
# # SIDEBAR_X = SCREEN_WIDTH - SIDEBAR_WIDTH # Removed
# # SIDEBAR_COLOR = (40, 40, 60, 220) # Removed
BOTTOM_BAR_HEIGHT = 150 # Increased from 120
BOTTOM_BAR_Y = SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT
BOTTOM_BAR_COLOR = (40, 40, 60, 220) # Same color as old sidebar
PLAYABLE_HEIGHT = SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT # Define the area above the bottom bar

UPGRADE_PANEL_WIDTH = 300
UPGRADE_PANEL_X = SCREEN_WIDTH - UPGRADE_PANEL_WIDTH - 20 # Keep upgrade panel on right

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
ORANGE = (255, 165, 0) # Added for sell button color

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

# Fonts (Can be loaded after init)
ui_font = pygame.font.Font(None, 36)
game_font = pygame.font.Font(None, 90) # Larger font for larger screen

# --- Load Game Assets (AFTER display init) ---
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

# --- Load Coop Image (Moved Here) --- #
try:
    original_coop_image = pygame.image.load('assets/coop.png').convert_alpha()
    print("Loaded image: assets/coop.png")

    # --- Scale Coop Image (NEW) --- #
    target_coop_height = int(tower_img.get_height() * 1.2) # ~20% taller than tower
    coop_image = scale_image_aspect_ratio(original_coop_image, target_height=target_coop_height)
    coop_rect = coop_image.get_rect()
    print(f"Scaled coop to height: {coop_image.get_height()}")
    # --- End Scale Coop Image --- #

except pygame.error as e:
    print(f"Error loading coop.png: {e}")
    coop_image = pygame.Surface((50, 50)) # Keep placeholder size small
    coop_image.fill((139, 69, 19)) # Brown placeholder
    coop_rect = coop_image.get_rect()
    print("Using placeholder for coop image.")
# --- End Coop Image Load ---

# --- Define Tower Types (AFTER assets are loaded) ---
TOWER_TYPES = { # Store info about available tower types
    'basic': {'name': 'Basic Chicken', 'cost': Tower.BASE_STATS['basic']['cost'], 'icon': tower_img},
    'bomb':  {'name': 'Bomb Chicken',  'cost': Tower.BASE_STATS['bomb']['cost'],  'icon': tower_img},
    'fire':  {'name': 'Fire Chicken',  'cost': Tower.BASE_STATS['fire']['cost'],  'icon': tower_img},
    'minigun': {'name': 'MiniGun Chicken', 'cost': Tower.BASE_STATS['minigun']['cost'], 'icon': tower_img},
}

# --- Game Variables (initialized globally, reset in functions) ---
state = MENU
selected_option = 0
selected_difficulty = 'Easy'
difficulty_health = {'Easy': 20, 'Medium': 10, 'Hard': 5}
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
time_scale = 1.0
build_mode = False
preview_tower = None
selected_tower = None # Track the currently selected tower

# Upgrade Button Rects (will be calculated later)
upgrade_button_rects = {}
bottom_bar_button_rects = {} # New dictionary for bottom bar
menu_option_rects = {} # New dictionary for menu option rects

# Wave Settings
TIME_BETWEEN_WAVES = 10 * FPS
SPAWN_INTERVAL = 1.5 * FPS

# Menu options
menu_options = ['Easy', 'Medium', 'Hard']

# --- Game Variables ---
# ... (state, difficulty, lists, timers etc.)
# ...

# --- Helper Functions ---
def reset_game_state():
    """Resets all variables for a new game."""
    global towers, enemies, projectiles, current_path, player_gold, player_health
    global score, wave_number, enemies_to_spawn_this_wave, enemies_spawned_this_wave
    global wave_timer, spawn_timer, build_mode, preview_tower, time_scale, selected_tower, coop_rect

    towers = []
    enemies = []
    projectiles = []
    current_path = get_path(SCREEN_WIDTH, PLAYABLE_HEIGHT)
    player_gold = 200
    player_health = difficulty_health[selected_difficulty]
    score = 0
    wave_number = 0 # Start at wave 0, will increment to 1 immediately
    enemies_to_spawn_this_wave = 0
    enemies_spawned_this_wave = 0
    wave_timer = 0 # Start first wave immediately
    spawn_timer = 0 # Reset within-wave spawn timer
    time_scale = 1.0 # Reset time scale on new game
    build_mode = False
    preview_tower = None
    selected_tower = None # Reset selected tower
    start_next_wave() # Prepare the first wave

    # --- Position the Coop --- #
    if current_path and coop_rect: # Check if path (list) and coop exist
        end_point = current_path[-1] # Access last element of the list
        end_x, end_y = int(end_point[0]), int(end_point[1])
        # Align bottom-center with path end, then move down slightly (1/8 height)
        coop_rect.midbottom = (end_x, end_y + coop_rect.height // 8)
    # --- End Coop Position --- #

    print("Game reset.")

def start_next_wave():
    """Sets up variables for the next wave and awards end-of-wave gold."""
    global wave_number, enemies_to_spawn_this_wave, enemies_spawned_this_wave, wave_timer, player_gold

    # Award gold for completing the previous wave (if wave_number > 0)
    if wave_number > 0:
        end_of_wave_bonus = 50
        player_gold += end_of_wave_bonus
        print(f"Wave {wave_number} cleared! +${end_of_wave_bonus} gold.")

    # Prepare next wave
    wave_number += 1
    enemies_to_spawn_this_wave = 5 + wave_number * 2 # Example: Increase enemies per wave
    enemies_spawned_this_wave = 0
    # Ensure wave timer uses the base time, time_scale applied during countdown
    wave_timer = TIME_BETWEEN_WAVES
    spawn_timer = 0 # Reset within-wave spawn timer
    print(f"Starting Wave {wave_number} with {enemies_to_spawn_this_wave} enemies.")

def draw_menu():
    global menu_option_rects # Allow modification of the global dict
    menu_option_rects = {} # Clear rects each time menu is drawn

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

    # Draw menu options
    option_font = pygame.font.Font(None, 74) # Slightly smaller than title
    start_y = 350
    for i, option in enumerate(menu_options):
        color = YELLOW if i == selected_option else WHITE
        text = option_font.render(option, True, color)
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * 80))
        screen.blit(text, rect)
        menu_option_rects[i] = rect # Store the rect with its index

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

def is_placement_valid(new_pos_tuple, existing_towers, min_separation):
    """Checks if a new tower position is far enough from existing towers."""
    new_pos = pygame.Vector2(new_pos_tuple)
    for tower in existing_towers:
        dist_sq = new_pos.distance_squared_to(tower.rect.center)
        if dist_sq < min_separation ** 2:
            print(f"Placement failed: Too close to existing tower at {tower.rect.center}. Dist sq: {dist_sq:.1f} < Min sq: {min_separation**2:.1f}")
            return False # Too close
    return True # Position is valid

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

    # Draw Upgrade Panel if a tower is selected
    if selected_tower:
        draw_upgrade_panel(selected_tower)

def draw_upgrade_panel(tower):
    """Draws the upgrade panel, adapting for different tower type paths."""
    global upgrade_button_rects
    upgrade_button_rects = {}
    panel_width = 350 # Increased from 300
    panel_height = 320 # Keep height for now
    panel_x = SCREEN_WIDTH - panel_width - 20 # Adjust X based on new width
    panel_y = 20
    panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
    panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel_surf.fill((50, 50, 50, 210))
    screen.blit(panel_surf, panel_rect.topleft)
    pygame.draw.rect(screen, WHITE, panel_rect, 2)
    panel_font = pygame.font.Font(None, 36) # Decreased from 40
    button_font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 28)

    # Tower Type Name
    type_name = TOWER_TYPES.get(tower.tower_type, {}).get('name', 'Unknown Tower')
    type_surf = small_font.render(type_name, True, CYAN)
    type_rect = type_surf.get_rect(centerx=panel_rect.centerx, top=panel_rect.top + 8)
    screen.blit(type_surf, type_rect)

    y_offset = panel_y + 40

    # Determine stats to display based on tower type
    stats_to_display = []
    if tower.tower_type == 'basic':
        stats_to_display = [
            (f"Range: {tower.range}", f"Lvl {tower.range_level}", 'range'),
            (f"Damage: {tower.damage}", f"Lvl {tower.damage_level}", 'damage'),
            (f"Rate: {60 / tower.fire_rate:.1f}/s", f"Lvl {tower.rate_level}", 'rate')
        ]
    elif tower.tower_type == 'bomb':
        stats_to_display = [
            (f"AoE: {tower.aoe_radius}", f"Lvl {tower.aoe_level}", 'aoe'), # Changed path
            (f"Damage: {tower.damage}", f"Lvl {tower.damage_level}", 'damage'),
            (f"Rate: {60 / tower.fire_rate:.1f}/s", f"Lvl {tower.rate_level}", 'rate')
        ]
    elif tower.tower_type == 'fire':
        dot_duration_sec = tower.dot_duration / FPS # Convert duration frames to seconds
        stats_to_display = [
            (f"Duration: {dot_duration_sec:.1f}s", f"Lvl {tower.duration_level}", 'duration'), # Changed path
            (f"Damage: {tower.damage}", f"Lvl {tower.damage_level}", 'damage'),
            (f"Rate: {60 / tower.fire_rate:.1f}/s", f"Lvl {tower.rate_level}", 'rate')
        ]
    elif tower.tower_type == 'minigun':
        stats_to_display = [
            (f"Range: {tower.range}", f"Lvl {tower.range_level}", 'range'),
            (f"Damage: {tower.damage}", f"Lvl {tower.damage_level}", 'damage'),
            (f"Rate: {60 / tower.fire_rate:.1f}/s", f"Lvl {tower.rate_level}", 'rate')
        ]

    button_width = 90
    button_height = 40
    button_x = panel_x + panel_width - button_width - 15 # Adjust button X for wider panel
    label_x = panel_x + 15 # Keep label X same?
    level_text_offset = 160 # Increased offset for level text (from 140)

    for i, (stat_text, level_text, stat_type) in enumerate(stats_to_display):
        text = panel_font.render(stat_text, True, WHITE)
        screen.blit(text, (label_x, y_offset))
        level_t = panel_font.render(level_text, True, GRAY)
        screen.blit(level_t, (label_x + level_text_offset, y_offset)) # Use new offset

        cost = tower.get_upgrade_cost(stat_type)
        button_y = y_offset + text.get_height() // 2 - button_height // 2 + 5
        btn_rect = pygame.Rect(button_x, button_y, button_width, button_height)
        upgrade_button_rects[stat_type] = btn_rect

        # --- Determine button state (Max/Locked/Cost) ---
        max_level_for_path = Tower.SPECIAL_PATH_MAX_LEVEL if stat_type in {'aoe', 'duration'} else Tower.MAX_LEVEL
        current_level = getattr(tower, stat_type + '_level', 0)

        if cost == -1 or current_level >= max_level_for_path:
            btn_color = GRAY; button_text = "MAX"
        elif cost == -2:
            btn_color = (40, 40, 40); button_text = "Locked"
        else:
            can_afford = player_gold >= cost
            btn_color = GREEN if can_afford else RED
            button_text = f"${cost}"
        # --- Render Button --- 
        pygame.draw.rect(screen, btn_color, btn_rect, border_radius=5)
        button_surf = button_font.render(button_text, True, BLACK if cost >= 0 and cost != -2 else WHITE) # White text for MAX/Locked
        button_text_rect = button_surf.get_rect(center=btn_rect.center)
        screen.blit(button_surf, button_text_rect)
        y_offset += 50

    # Sell Button
    y_offset += 15
    sell_value = tower.get_sell_value()
    sell_button_text = f"Sell ${sell_value}"
    sell_button_width = panel_width - 30 # Adjust width to fit new panel size
    sell_button_height = 45
    sell_button_x = panel_x + 15
    sell_button_y = y_offset
    sell_btn_rect = pygame.Rect(sell_button_x, sell_button_y, sell_button_width, sell_button_height)
    upgrade_button_rects['sell'] = sell_btn_rect
    pygame.draw.rect(screen, ORANGE, sell_btn_rect, border_radius=5)
    sell_surf = button_font.render(sell_button_text, True, BLACK)
    sell_rect = sell_surf.get_rect(center=sell_btn_rect.center)
    screen.blit(sell_surf, sell_rect)

def draw_build_bar():
    """Draws the build bar with multiple tower types."""
    global bottom_bar_button_rects
    bottom_bar_button_rects = {}
    bar_rect = pygame.Rect(0, BOTTOM_BAR_Y, SCREEN_WIDTH, BOTTOM_BAR_HEIGHT)
    bar_surf = pygame.Surface(bar_rect.size, pygame.SRCALPHA)
    bar_surf.fill(BOTTOM_BAR_COLOR)
    screen.blit(bar_surf, bar_rect.topleft)
    pygame.draw.rect(screen, WHITE, bar_rect, 1)

    target_icon_size = 70 # The maximum dimension for the icon
    padding = (BOTTOM_BAR_HEIGHT - target_icon_size - 25) // 2 # Keep overall padding
    slot_y = BOTTOM_BAR_Y + padding # Top position for the icon slot
    current_slot_x = padding # Left position for the current icon slot
    cost_font = pygame.font.Font(None, 24)
    name_font = pygame.font.Font(None, 20)

    for tower_key, info in TOWER_TYPES.items():
        tower_icon = info['icon']
        tower_cost = info['cost']
        tower_name = info['name']

        # --- Aspect Ratio Scaling --- #
        original_w, original_h = tower_icon.get_size()
        if original_w == 0 or original_h == 0: continue # Skip if image invalid
        ratio = min(target_icon_size / original_w, target_icon_size / original_h)
        new_w = int(original_w * ratio)
        new_h = int(original_h * ratio)
        icon_display = pygame.transform.smoothscale(tower_icon, (new_w, new_h))
        # --- End Scaling --- #

        # --- Positioning --- #
        # Center the scaled icon within the conceptual square slot
        slot_center_x = current_slot_x + target_icon_size / 2
        slot_center_y = slot_y + target_icon_size / 2
        icon_rect = icon_display.get_rect(center=(slot_center_x, slot_center_y))
        # --- End Positioning --- #

        # Store the rect of the actual displayed icon for click detection
        bottom_bar_button_rects[tower_key] = icon_rect

        # Draw selection highlight around the slot
        is_previewing_this = (preview_tower is not None and preview_tower.tower_type == tower_key)
        if is_previewing_this:
            # Draw highlight around the conceptual slot boundary
            highlight_rect = pygame.Rect(current_slot_x, slot_y, target_icon_size, target_icon_size)
            pygame.draw.rect(screen, YELLOW, highlight_rect.inflate(6, 6), 3, border_radius=5)

        screen.blit(icon_display, icon_rect) # Blit the potentially non-square icon

        # Position Name/Cost relative to the displayed icon's bottom-center
        name_surf = name_font.render(tower_name, True, WHITE)
        name_rect = name_surf.get_rect(midtop=(icon_rect.centerx, icon_rect.bottom + 2))
        screen.blit(name_surf, name_rect)
        cost_text = f"${tower_cost}"
        cost_surf = cost_font.render(cost_text, True, YELLOW if player_gold >= tower_cost else GRAY)
        cost_rect = cost_surf.get_rect(midtop=(icon_rect.centerx, name_rect.bottom + 1))
        screen.blit(cost_surf, cost_rect)

        # Move to the next slot position
        current_slot_x += target_icon_size + padding + 10 # Use target size for spacing

def draw_tiled_background_and_path(path_width=40):
    """Tiles the background and draws the path only within the playable area."""
    # Tile the main background up to PLAYABLE_HEIGHT
    bg_w, bg_h = background_tile.get_size()
    for y in range(0, PLAYABLE_HEIGHT, bg_h):
        for x in range(0, SCREEN_WIDTH, bg_w):
            # Check if tile bottom is above PLAYABLE_HEIGHT before blitting
            if y + bg_h <= PLAYABLE_HEIGHT:
                 screen.blit(background_tile, (x, y))
            else:
                 # Draw partial tile if it overlaps the boundary
                 clip_height = PLAYABLE_HEIGHT - y
                 if clip_height > 0:
                      screen.blit(background_tile, (x, y), (0, 0, bg_w, clip_height))

    # Draw the path (path points are already constrained to playable area)
    if len(current_path) > 1:
        pygame.draw.lines(screen, PATH_COLOR, False, current_path, path_width)

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

        if event.type == pygame.KEYDOWN:
            if state == GAME:
                if event.key == pygame.K_f: time_scale = min(time_scale * 2, 16.0)
                elif event.key == pygame.K_s: time_scale = max(1.0, time_scale / 2)
                elif event.key == pygame.K_ESCAPE:
                     if preview_tower: # If actively placing a tower
                         preview_tower = None
                         print("Build cancelled.")
                     elif selected_tower: # If a tower is selected (showing upgrade panel)
                         selected_tower = None
                         print("Tower deselected.")
                     else: # Otherwise, go back to the main menu
                         state = MENU
                         print("Returning to Main Menu.")
            elif state == GAME_OVER and event.key == pygame.K_RETURN: state = MENU
            elif state == MENU:
                if event.key == pygame.K_w or event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(menu_options)
                elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(menu_options)
                elif event.key == pygame.K_RETURN:
                    selected_difficulty = menu_options[selected_option]
                    state = GAME
                    reset_game_state()

        if event.type == pygame.MOUSEBUTTONDOWN:
            clicked_handled = False
            if event.button == 1: # Left Click
                # --- Menu State Click Handling --- #
                if state == MENU:
                    for index, rect in menu_option_rects.items():
                        if rect.collidepoint(mouse_pos):
                            selected_option = index
                            selected_difficulty = menu_options[selected_option]
                            state = GAME
                            reset_game_state()
                            clicked_handled = True # Mark handled so game state logic isn\'t triggered
                            break # Exit loop once an option is clicked
                # --- End Menu State Click Handling --- #

                # --- Game State Click Handling --- #
                if state == GAME and not clicked_handled: # Only process if not handled by menu
                    # 1. Check Bottom Bar Buttons
                    current_preview_type = preview_tower.tower_type if preview_tower else None
                    for tower_key, rect in bottom_bar_button_rects.items():
                        if rect.collidepoint(mouse_pos):
                            clicked_handled = True
                            cost = TOWER_TYPES[tower_key]['cost']
                            icon_img = TOWER_TYPES[tower_key]['icon']
                            if player_gold >= cost:
                                if current_preview_type == tower_key:
                                    preview_tower = None
                                else:
                                    # Pass correct tower_type when creating preview
                                    preview_tower = Tower(mouse_pos[0], mouse_pos[1], icon_img, tower_key)
                                    selected_tower = None
                            else:
                                print(f"Not enough gold for {tower_key} (${cost})")
                            break
                    # 2. Check Upgrade Panel Buttons
                    if not clicked_handled and selected_tower:
                        for button_type, rect in upgrade_button_rects.items():
                            if rect.collidepoint(mouse_pos):
                                clicked_handled = True
                                if button_type == 'sell':
                                    # Sell the tower
                                    sell_value = selected_tower.get_sell_value()
                                    player_gold += sell_value
                                    towers.remove(selected_tower)
                                    print(f"Sold tower for ${sell_value}. Gold: {player_gold}")
                                    selected_tower = None
                                else: # It's an upgrade button
                                    stat_type = button_type
                                    cost = selected_tower.get_upgrade_cost(stat_type)
                                    # Corrected Check: cost >= 0 means it's possible and not max/locked
                                    if cost >= 0:
                                        if player_gold >= cost:
                                            # Attempt upgrade
                                            success, actual_cost = selected_tower.upgrade(stat_type)
                                            if success:
                                                player_gold -= actual_cost
                                                print(f"Upgraded {stat_type}! Gold left: {player_gold}")
                                            # else: No need for internal fail message here
                                        else:
                                            print("Not enough gold!")
                                    elif cost == -1:
                                        print("Already at max level!")
                                    elif cost == -2:
                                        print(f"Cannot upgrade {stat_type}: Locked by specialization!")
                                    # else: Should not happen
                                break # Stop checking buttons
                    # 3. Check Game Area Clicks
                    if not clicked_handled and state == GAME:
                        if preview_tower: # If building
                            if mouse_pos[1] < BOTTOM_BAR_Y:
                                # --- Proximity Check --- #
                                min_tower_separation = preview_tower.rect.width * 0.75 # Min dist based on tower width
                                placement_ok = is_placement_valid(mouse_pos, towers, min_tower_separation)
                                # --- Original Checks --- #
                                gold_ok = player_gold >= preview_tower.cost
                                path_ok = not is_on_path(mouse_pos, current_path)

                                if gold_ok and path_ok and placement_ok:
                                    towers.append(Tower(mouse_pos[0], mouse_pos[1], preview_tower.image, preview_tower.tower_type))
                                    player_gold -= preview_tower.cost
                                    preview_tower = None
                                else:
                                    # Give specific feedback
                                    reason = []
                                    if not gold_ok: reason.append("insufficient gold")
                                    if not path_ok: reason.append("on path")
                                    if not placement_ok: reason.append("too close to another tower")
                                    print(f"Cannot place tower here ({', '.join(reason)}).")
                            else:
                                 print("Cannot place tower in UI area.")
                        # If not building, try selecting existing tower
                        else:
                            # Check if click is outside the bottom bar area
                            if mouse_pos[1] < BOTTOM_BAR_Y:
                                clicked_tower = None
                                for tower in towers:
                                    if tower.rect.collidepoint(mouse_pos):
                                        clicked_tower = tower
                                        break
                                # Toggle selection
                                if clicked_tower and clicked_tower == selected_tower:
                                    selected_tower = None # Deselect if clicking selected tower again
                                else:
                                    selected_tower = clicked_tower # Select new or different tower
                                if selected_tower:
                                    print(f"Selected Tower at {selected_tower.rect.center}")
                            else:
                                selected_tower = None # Clicking UI deselects tower
            # --- Right Click --- #
            elif event.button == 3:
                 if preview_tower: preview_tower = None; print("Build cancelled.")
                 elif selected_tower: selected_tower = None; print("Tower deselected.")

    # --- State Logic & Updates (Apply time_scale * BASE_GAME_SPEED) ---
    if state == GAME:
        effective_time_scale = time_scale * BASE_GAME_SPEED

        # Wave Management (apply effective time scale)
        if enemies_spawned_this_wave < enemies_to_spawn_this_wave:
            spawn_timer -= effective_time_scale # Use effective time scale
            if spawn_timer <= 0:
                enemy_type = 'cat' if random.random() < 0.4 else 'raccoon'
                # Need enemy image from ENEMY_IMAGES dict
                enemy_img_to_use = ENEMY_IMAGES[enemy_type]
                enemies.append(Enemy(current_path, wave_number, enemy_img_to_use, enemy_type=enemy_type))
                enemies_spawned_this_wave += 1
                spawn_timer += SPAWN_INTERVAL
        elif len(enemies) == 0:
            wave_timer -= effective_time_scale # Use effective time scale
            if wave_timer <= 0:
                start_next_wave()

        # Update Enemies (pass effective time scale)
        for enemy in enemies[:]:
            reached_end = enemy.move(effective_time_scale)
            if reached_end:
                player_health -= 1
            if enemy.is_dead:
                if not reached_end:
                    player_gold += enemy.reward
                    score += enemy.points_value
                enemies.remove(enemy)

        # Check for Game Over
        if player_health <= 0:
            state = GAME_OVER
            continue

        # Update Towers (pass effective time scale)
        for tower in towers:
            tower.update(enemies, projectiles, effective_time_scale, projectile_img)

        # Update Projectiles (Pass enemies list)
        for proj in projectiles[:]:
            proj.move(effective_time_scale, enemies_list=enemies)
            if not proj.is_active:
                projectiles.remove(proj)

        # Update Preview Tower (unchanged)
        if build_mode and preview_tower:
            preview_tower.x, preview_tower.y = mouse_pos
            preview_tower.rect.center = mouse_pos

    # --- Drawing --- #
    screen.blit(background_tile, (0, 0))

    if state == MENU:
        draw_menu()
    elif state == GAME:
        # Draw tiled background and path first
        draw_tiled_background_and_path()

        # --- Draw Coop Here --- #
        if coop_image and coop_rect:
            screen.blit(coop_image, coop_rect)
        # --- End Coop Draw --- #

        # Draw Towers, Enemies, Projectiles
        for tower in towers:
            tower.draw(screen, is_selected=(tower == selected_tower))
        for enemy in enemies:
            enemy.draw(screen)
        for proj in projectiles:
            proj.draw(screen)

        # Draw Build Bottom Bar (Call the new function)
        draw_build_bar()

        # Draw Preview Tower (if building - UPDATED VISUALS)
        if preview_tower:
            # Update preview tower position to follow mouse
            preview_tower.x, preview_tower.y = mouse_pos
            preview_tower.rect.center = mouse_pos

            # --- Determine full placement validity for visual feedback --- #
            gold_ok = player_gold >= preview_tower.cost
            path_ok = not is_on_path(mouse_pos, current_path)
            min_tower_separation = preview_tower.rect.width * 0.75
            placement_proximity_ok = is_placement_valid(mouse_pos, towers, min_tower_separation)
            is_valid_placement = gold_ok and path_ok and placement_proximity_ok
            # --- End Validity Check --- #

            # Determine tint color based on overall validity
            tint_color = (0, 100, 255, 150) if is_valid_placement else (255, 0, 0, 150) # Blue or Red

            # Draw semi-transparent range circle using the tint color
            range_surface = pygame.Surface((preview_tower.range * 2, preview_tower.range * 2), pygame.SRCALPHA)
            range_circle_color = (tint_color[0], tint_color[1], tint_color[2], 50) # Lighter alpha for range
            pygame.draw.circle(range_surface, range_circle_color, (preview_tower.range, preview_tower.range), preview_tower.range)
            screen.blit(range_surface, (preview_tower.rect.centerx - preview_tower.range, preview_tower.rect.centery - preview_tower.range))

            # Draw tinted tower image preview using the tint color
            preview_img_copy = preview_tower.image.copy()
            preview_img_copy.fill(tint_color, special_flags=pygame.BLEND_RGBA_MULT)
            img_rect = preview_img_copy.get_rect(center=preview_tower.rect.center)
            screen.blit(preview_img_copy, img_rect)

        # Draw UI
        draw_game_ui()

    elif state == GAME_OVER:
        draw_game_over()

    pygame.display.flip()

pygame.quit()
sys.exit() 