import pygame
import os

# Helper to load enemy images (similar to main.py)
ASSETS_DIR = "assets"
def load_enemy_image(filename):
    path = os.path.join(ASSETS_DIR, filename)
    try:
        image = pygame.image.load(path).convert_alpha()
        return image
    except pygame.error as e:
        print(f"Error loading enemy image '{path}': {e}. Using fallback.")
        placeholder = pygame.Surface((30, 30))
        placeholder.fill((100, 100, 100)) # Gray fallback
        return placeholder

# Load enemy images once
ENEMY_IMAGES = {
    'raccoon': load_enemy_image("raccoon.png"),
    'cat': load_enemy_image("cat.png")
}

class Enemy:
    def __init__(self, path, wave_number, image, enemy_type='unknown'):
        self.path = path
        self.image = image
        self.enemy_type = enemy_type
        self.float_x, self.float_y = path[0]
        self.rect = self.image.get_rect(center=(self.float_x, self.float_y))
        if enemy_type == 'cat':
            self.base_speed = 0.7
            self.base_max_health = 70
            self.reward = 8
            self.points_value = 4
        else:
            self.base_speed = 0.5
            self.base_max_health = 90
            self.reward = 12
            self.points_value = 6
        self.speed = self.base_speed + (wave_number - 1) * 0.03
        self.max_health = self.base_max_health + (wave_number - 1) * 15
        self.health = self.max_health
        self.path_index = 0
        self.is_dead = False
        self.damage_taken_timer = 0
        self.damage_flash_duration = 10
        self.reward += (wave_number // 5)
        self.points_value += (wave_number - 1)

    def move(self, time_scale=1.0):
        if self.is_dead: return False
        if self.damage_taken_timer > 0:
            self.damage_taken_timer -= 1

        reached_end = False
        move_distance = self.speed * time_scale

        if self.path_index < len(self.path) - 1:
            target_x, target_y = self.path[self.path_index + 1]
            direction_x = target_x - self.float_x
            direction_y = target_y - self.float_y
            distance_to_target = (direction_x ** 2 + direction_y ** 2) ** 0.5

            if distance_to_target < move_distance:
                self.float_x, self.float_y = target_x, target_y
                self.path_index += 1
                if self.path_index == len(self.path) - 1:
                    reached_end = True
            elif distance_to_target > 0:
                self.float_x += move_distance * direction_x / distance_to_target
                self.float_y += move_distance * direction_y / distance_to_target
            self.rect.center = (self.float_x, self.float_y)
        else:
             reached_end = True

        if reached_end:
            self.die(killed_by_player=False)
        return reached_end

    def take_damage(self, damage):
        if self.is_dead: return
        self.health -= damage
        self.damage_taken_timer = self.damage_flash_duration
        if self.health <= 0:
            self.die(killed_by_player=True)

    def die(self, killed_by_player=True):
        if not self.is_dead:
            if killed_by_player:
                print(f"{self.enemy_type.capitalize()} defeated! (Wave Scaled)")
            self.is_dead = True

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        if self.health < self.max_health:
            bar_width = self.rect.width * 0.8
            bar_height = 5
            health_pct = self.health / self.max_health
            fill_width = bar_width * health_pct
            health_bar_rect = pygame.Rect(0, 0, bar_width, bar_height)
            health_bar_rect.midbottom = self.rect.midtop - pygame.Vector2(0, 5)
            fill_rect = pygame.Rect(health_bar_rect.left, health_bar_rect.top, fill_width, bar_height)
            pygame.draw.rect(screen, (255,0,0), health_bar_rect)
            pygame.draw.rect(screen, (0,255,0), fill_rect)
        if self.damage_taken_timer > 0:
            flash_surface = self.image.copy()
            flash_surface.fill((255, 255, 255, 100), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(flash_surface, self.rect) 