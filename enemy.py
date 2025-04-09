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

        # Base stats for Raccoon (default)
        raccoon_base_speed = 0.5
        raccoon_base_max_health = 90
        raccoon_reward = 12
        raccoon_points_value = 6

        # Assign stats based on type
        if enemy_type == 'cat':
            self.base_speed = raccoon_base_speed * 1.2 # Cats are faster
            self.base_max_health = int(raccoon_base_max_health * 1.5) # Cats have 1.5x health
            self.reward = int(raccoon_reward * 0.8) # Cats give less reward
            self.points_value = int(raccoon_points_value * 1.2) # Cats worth more points
        else: # Raccoon stats
            self.base_speed = raccoon_base_speed
            self.base_max_health = raccoon_base_max_health
            self.reward = raccoon_reward
            self.points_value = raccoon_points_value

        # Apply wave scaling
        self.speed = self.base_speed + (wave_number - 1) * 0.03
        self.max_health = self.base_max_health + (wave_number - 1) * 15 # Keep wave scaling same for both for now
        self.health = self.max_health
        self.path_index = 0
        self.is_dead = False
        self.damage_taken_timer = 0
        self.damage_flash_duration = 10
        self.reward += (wave_number // 5)
        self.points_value += (wave_number - 1)

        # Status Effects
        self.dot_effects = [] # List of tuples: (damage_per_second, remaining_seconds, original_duration)
        self.is_burning = False # For visual indicator

    def apply_dot(self, damage_per_second, duration_seconds):
        """Adds a new DoT effect or refreshes the strongest one."""
        # Find if an existing effect has the same source/type (optional)
        # For now, just add or refresh based on damage strength

        # Check if there's an existing stronger or equal DoT
        # if any(existing_dps >= damage_per_second for existing_dps, _, _ in self.dot_effects):
        #     print("  Existing stronger DoT effect present, not applying new one.")
        #     return # Don't apply weaker or equal DoT

        # Simple approach: Add new effect, let update handle it (allows stacking)
        # OR: Keep only the strongest (prevents stacking)
        # Let's try keeping the strongest for simplicity:
        if not self.dot_effects or damage_per_second > self.dot_effects[0][0]:
            self.dot_effects = [(damage_per_second, duration_seconds, duration_seconds)]
            self.is_burning = True
            print(f"  Applying new strongest DoT ({damage_per_second:.1f} dps)")
        elif damage_per_second == self.dot_effects[0][0]:
            # Refresh duration of the current strongest effect
            self.dot_effects[0] = (damage_per_second, duration_seconds, duration_seconds)
            self.is_burning = True
            print(f"  Refreshing DoT duration ({damage_per_second:.1f} dps)")
        # Else: Weaker DoT, ignore

    def update_effects(self, dt_seconds):
        """Updates timers and applies damage for active DoT effects."""
        if not self.dot_effects:
            self.is_burning = False
            return

        remaining_effects = []
        total_dot_this_frame = 0

        for dps, remaining_sec, original_dur in self.dot_effects:
            damage_this_tick = dps * dt_seconds
            total_dot_this_frame += damage_this_tick
            new_remaining_sec = remaining_sec - dt_seconds

            if new_remaining_sec > 0:
                remaining_effects.append((dps, new_remaining_sec, original_dur))
            # else: Effect expired

        self.dot_effects = remaining_effects
        self.is_burning = bool(self.dot_effects)

        if total_dot_this_frame > 0:
            # Apply damage as float
            self.health -= total_dot_this_frame
            if self.health <= 0:
                self.is_dead = True

    def move(self, time_scale=1.0):
        # Call update_effects first
        self.update_effects((1/60) * time_scale)
        if self.is_dead: return False # Check if DoT killed it

        # Damage flash timer
        if self.damage_taken_timer > 0:
            self.damage_taken_timer -= 1 # Flash always ticks at normal rate?

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
            self.is_dead = True
            self.is_burning = False # Stop burning effect on death
            self.dot_effects.clear() # Clear DoTs on death
            if killed_by_player:
                print(f"{self.enemy_type.capitalize()} defeated! (Wave Scaled)")

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)
        # Draw health bar
        health_bar_width = self.rect.width
        health_bar_height = 5
        health_bar_x = self.rect.x
        health_bar_y = self.rect.y - health_bar_height - 2
        current_health_ratio = max(0, self.health / self.max_health)
        pygame.draw.rect(screen, (255,0,0), (health_bar_x, health_bar_y, health_bar_width, health_bar_height))
        pygame.draw.rect(screen, (0,255,0), (health_bar_x, health_bar_y, int(health_bar_width * current_health_ratio), health_bar_height))

        # Draw burning effect if applicable
        if self.is_burning:
            # Simple tint: Make the enemy orange-ish
            burn_surface = self.image.copy()
            burn_surface.fill((255, 100, 0, 150), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(burn_surface, self.rect.topleft)
        elif self.damage_taken_timer > 0:
            flash_surface = self.image.copy()
            flash_surface.fill((255, 255, 255, 100), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(flash_surface, self.rect.topleft) 