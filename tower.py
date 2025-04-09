from projectile import Projectile
import pygame

class Tower:
    def __init__(self, x, y, image):
        self.x = x
        self.y = y
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.range = 150 # Increased range
        self.damage = 30 # Adjusted damage
        self.fire_rate = 60 # Base cooldown in frames (at normal speed)
        self.fire_cooldown = 0
        self.cost = 50 # Cost to place the tower

    def update(self, enemies, projectiles, time_scale=1.0, projectile_img=None):
        # Cooldown timer - decrease by time_scale
        if self.fire_cooldown > 0:
            self.fire_cooldown -= time_scale
            # Ensure cooldown doesn't go significantly negative
            if self.fire_cooldown < 0: self.fire_cooldown = 0

        # Find target and shoot if cooldown is ready
        if self.fire_cooldown <= 0:
            target = self.find_target(enemies)
            if target:
                # Create projectile, passing its image
                if projectile_img:
                    projectiles.append(Projectile(self.rect.centerx, self.rect.centery, target, self.damage, projectile_img))
                else: # Fallback if no image provided (shouldn't happen with main.py changes)
                    projectiles.append(Projectile(self.rect.centerx, self.rect.centery, target, self.damage))
                self.fire_cooldown = self.fire_rate # Reset cooldown fully

    def find_target(self, enemies):
        # Find the enemy closest to the end of the path within range
        target = None
        max_path_index = -1

        for enemy in enemies:
            if self.in_range(enemy):
                # Prioritize enemy further along the path
                if enemy.path_index > max_path_index:
                    max_path_index = enemy.path_index
                    target = enemy
                # Optional: If same path index, target closest to tower?
                # elif enemy.path_index == max_path_index:
                #     dist_sq = (self.x - enemy.x)**2 + (self.y - enemy.y)**2
                #     if dist_sq < min_dist_sq_to_end:
                #         min_dist_sq_to_end = dist_sq
                #         target = enemy
        return target

    def in_range(self, enemy):
        # Use rect center for distance calculation
        enemy_pos = pygame.Vector2(enemy.rect.center)
        tower_pos = pygame.Vector2(self.rect.center)
        return (tower_pos - enemy_pos).length_squared() <= self.range**2

    def draw(self, screen):
        # Draw the tower image centered at its position
        screen.blit(self.image, self.rect)
        # Draw the tower's range (optional visualization)
        pygame.draw.circle(screen, (0, 100, 0, 100), self.rect.center, self.range, 1) 