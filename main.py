import pygame
from tower import Tower
from enemy import Enemy
from map import get_path
from projectile import Projectile

# Initialize Pygame
pygame.init()

# Set up display
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption('Tower Defense Game')

# Define game states
MENU = 'menu'
GAME = 'game'

# Set initial state
state = MENU

# Define font
font = pygame.font.Font(None, 74)

# Define menu options
menu_options = ['Easy', 'Medium', 'Hard']
selected_option = 0

# Initialize game elements
towers = [Tower(200, 200)]
enemies = [] # Start with no enemies
projectiles = [] # List to store active projectiles
path = get_path()

# Enemy spawning timer
enemy_spawn_timer = 0
enemy_spawn_interval = 120 # Spawn every 120 frames (2 seconds at 60 FPS)

# Clock for controlling frame rate
clock = pygame.time.Clock()

# Function to draw menu
def draw_menu():
    screen.fill((0, 0, 0))
    for i, option in enumerate(menu_options):
        color = (255, 255, 255) if i == selected_option else (100, 100, 100)
        text = font.render(option, True, color)
        screen.blit(text, (350, 200 + i * 100))

# Main game loop
running = True
while running:
    dt = clock.tick(60) # Limit frame rate to 60 FPS and get delta time

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if state == MENU:
                if event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(menu_options)
                    print(f'Selected option index (UP): {selected_option}')
                elif event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(menu_options)
                    print(f'Selected option index (DOWN): {selected_option}')
                elif event.key == pygame.K_RETURN:
                    state = GAME
                    enemies = [Enemy(path)] # Spawn the first enemy when game starts
                    projectiles = [] # Clear projectiles when starting game

    if state == MENU:
        draw_menu()
    else:
        # Update game elements

        # Spawn new enemies
        enemy_spawn_timer += 1
        if enemy_spawn_timer >= enemy_spawn_interval:
            enemies.append(Enemy(path))
            enemy_spawn_timer = 0

        # Update enemies
        for enemy in enemies[:]: # Iterate over a copy
            enemy.move()
            if enemy.is_dead:
                enemies.remove(enemy)
                continue

        # Update towers and create projectiles
        for tower in towers:
            tower.update(enemies, projectiles)

        # Update projectiles
        for proj in projectiles[:]: # Iterate over a copy
            proj.move()
            if not proj.is_active:
                projectiles.remove(proj)

        # --- Drawing --- #
        screen.fill((0, 0, 0))

        # Draw the path
        for i in range(len(path) - 1):
            pygame.draw.line(screen, (50, 50, 50), path[i], path[i+1], 3)

        # Draw towers
        for tower in towers:
            tower.draw(screen)

        # Draw enemies
        for enemy in enemies:
            enemy.draw(screen)

        # Draw projectiles
        for proj in projectiles:
            proj.draw(screen)

    # Update the display
    pygame.display.flip()

# Quit Pygame
pygame.quit() 