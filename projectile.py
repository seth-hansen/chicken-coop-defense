import pygame
# import random # Removed random import

# Constants
DEFAULT_SPEED = 500 # Pixels per second
# Define constants for DoT effects (if not defined elsewhere)
DOT_TICK_RATE = 60 # How often DoT damage is applied per second (matches FPS)

class Projectile:
    def __init__(self, start_x, start_y, target_enemy, damage, image=None,
                 projectile_type='basic', aoe_radius=0, dot_damage=0, dot_duration=0, tower_ref=None):
        self.image = image
        self.float_x = start_x
        self.float_y = start_y
        if self.image:
            self.rect = self.image.get_rect(center=(self.float_x, self.float_y))
        else:
            self.rect = pygame.Rect(start_x - 2, start_y - 2, 4, 4)

        self.target = target_enemy
        self.damage = damage # Direct hit damage
        self.base_speed = 8
        self.is_active = True

        # Store type-specific properties
        self.projectile_type = projectile_type
        self.aoe_radius = aoe_radius
        self.dot_damage = dot_damage
        self.dot_duration = dot_duration

        # Bomb specific visual effect timer
        self.explosion_timer = 0
        self.explosion_duration = 8 # Frames for explosion visual (Halved from 15)
        self.explosion_pos = None

        # --- Type-Specific Attributes (Calculated from tower) ---
        self.base_damage = 0
        self.dot_damage_per_second = 0 # New: Store damage per second
        self.dot_duration_seconds = 0 # New: Store duration in seconds
        self.tower_ref = tower_ref # Keep a reference to the tower for stats
        self._derive_stats_from_tower()

    def _derive_stats_from_tower(self):
        """Gets damage, AoE, DoT stats from the referenced tower."""
        if not self.tower_ref:
            print("Warning: Projectile created without tower reference!")
            return

        self.base_damage = self.tower_ref.damage # Use tower's current damage
        self.projectile_type = self.tower_ref.tower_type

        if self.projectile_type == 'bomb':
            self.aoe_radius = self.tower_ref.aoe_radius
        elif self.projectile_type == 'fire':
            # Get DoT stats from tower
            tower_dot_damage = self.tower_ref.dot_damage # This is damage per tick in tower
            tower_dot_duration_frames = self.tower_ref.dot_duration # Duration in frames

            # Convert to per-second and duration in seconds for clarity
            self.dot_duration_seconds = tower_dot_duration_frames / DOT_TICK_RATE # e.g., 120 frames / 60 fps = 2 seconds
            if self.dot_duration_seconds > 0:
                total_dot_damage = tower_dot_damage * tower_dot_duration_frames
                self.dot_damage_per_second = total_dot_damage / self.dot_duration_seconds
            else:
                 self.dot_damage_per_second = 0

            # Override with requested values: 10 damage/sec for 5 seconds
            self.dot_damage_per_second = 10
            self.dot_duration_seconds = 5

    def move(self, time_scale=1.0, enemies_list=None):
        if not self.is_active: return
        if self.explosion_timer > 0: # Handle explosion visual countdown
            self.explosion_timer -= time_scale # Reverted: Scales with game speed
            if self.explosion_timer <= 0:
                self.is_active = False # Deactivate after explosion visual ends
            return # Don't move during explosion visual

        if not self.target or self.target.is_dead:
            # If target gone, deactivate (bomb could optionally explode here)
            self.is_active = False
            return

        current_speed = self.base_speed * time_scale
        target_x, target_y = self.target.rect.centerx, self.target.rect.centery
        direction_x = target_x - self.float_x
        direction_y = target_y - self.float_y
        distance = (direction_x ** 2 + direction_y ** 2) ** 0.5

        hit_target = False
        if distance < current_speed:
            hit_target = True
            # Ensure projectile visually reaches target center before impact logic
            self.float_x, self.float_y = target_x, target_y
            self.rect.center = (self.float_x, self.float_y)
        elif distance > 0:
            self.float_x += current_speed * direction_x / distance
            self.float_y += current_speed * direction_y / distance
            self.rect.center = (self.float_x, self.float_y)
        else: # Exactly on target
            hit_target = True

        if hit_target:
            self.handle_impact(enemies_list)

    def handle_impact(self, enemies_list):
        """Handles damage application based on projectile type."""
        impact_pos = pygame.Vector2(self.rect.center) # Use projectile pos at impact

        if self.projectile_type == 'basic':
            if self.target and not self.target.is_dead:
                self.target.take_damage(self.base_damage)
            self.is_active = False # Basic projectile disappears on hit

        elif self.projectile_type == 'bomb':
            print(f"Bomb impacted at {impact_pos}! AoE: {self.aoe_radius}")
            if enemies_list:
                 for enemy in enemies_list:
                      if not enemy.is_dead:
                          enemy_pos = pygame.Vector2(enemy.rect.center)
                          dist_sq = (impact_pos - enemy_pos).length_squared()
                          if dist_sq <= self.aoe_radius ** 2:
                               print(f"  Hitting enemy {enemy.enemy_type} in AoE.")
                               enemy.take_damage(self.base_damage)
            # Start explosion visual, don't deactivate immediately
            self.explosion_timer = self.explosion_duration
            self.explosion_pos = impact_pos
            # Stop rendering the projectile image itself during explosion
            self.image = None # Or set a flag

        elif self.projectile_type == 'fire':
            if self.target and not self.target.is_dead:
                self.target.take_damage(self.base_damage)
                self.target.apply_dot(self.dot_damage_per_second, self.dot_duration_seconds)
                print(f"Applied Fire DoT: {self.dot_damage_per_second:.1f} dmg/sec for {self.dot_duration_seconds} sec.")
            self.is_active = False # Fire projectile disappears on hit
        elif self.projectile_type == 'minigun': # Added handling for minigun
             if self.target and not self.target.is_dead:
                 self.target.take_damage(self.base_damage)
             self.is_active = False # Minigun projectile disappears on hit

    def draw(self, screen):
        if not self.is_active: return

        if self.explosion_timer > 0 and self.explosion_pos: # Draw explosion visual
            progress = 1.0 - (self.explosion_timer / self.explosion_duration)
            current_radius = int(self.aoe_radius * progress)
            alpha = int(200 * (1.0 - progress)) # Fade out
            if current_radius > 0 and alpha > 0:
                # Draw expanding orange circle
                explosion_surf = pygame.Surface((current_radius*2, current_radius*2), pygame.SRCALPHA)
                pygame.draw.circle(explosion_surf, (255, 150, 0, alpha), (current_radius, current_radius), current_radius)
                screen.blit(explosion_surf, self.explosion_pos - pygame.Vector2(current_radius, current_radius))

        elif self.image: # Draw projectile image if not exploding
            screen.blit(self.image, self.rect)
        elif self.projectile_type != 'bomb': # Fallback draw if no image and not bomb explosion
            pygame.draw.rect(screen, (255, 255, 0), self.rect) 