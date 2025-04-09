from projectile import Projectile
import pygame

class Tower:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.range = 100
        self.damage = 30 # Adjusted damage
        self.fire_rate = 60 # Frames between shots (1 second at 60 FPS)
        self.fire_cooldown = 0

    def update(self, enemies, projectiles):
        # Cooldown timer
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1

        # Find target and shoot if cooldown is ready
        if self.fire_cooldown <= 0:
            target = self.find_target(enemies)
            if target:
                projectiles.append(Projectile(self.x, self.y, target, self.damage))
                self.fire_cooldown = self.fire_rate # Reset cooldown

    def find_target(self, enemies):
        # Simple logic to find the first enemy in range
        for enemy in enemies:
            if self.in_range(enemy):
                return enemy
        return None

    def in_range(self, enemy):
        # Check if an enemy is within range
        return ((self.x - enemy.x) ** 2 + (self.y - enemy.y) ** 2) ** 0.5 <= self.range

    def draw(self, screen):
        # Draw the tower
        pygame.draw.circle(screen, (0, 255, 0), (self.x, self.y), 15) # Slightly larger tower
        # Draw the tower's range (optional visualization)
        pygame.draw.circle(screen, (0, 100, 0), (self.x, self.y), self.range, 1) 