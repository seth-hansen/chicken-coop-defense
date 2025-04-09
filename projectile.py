import pygame

class Projectile:
    def __init__(self, start_x, start_y, target_enemy, damage, image=None):
        self.image = image
        self.float_x = start_x
        self.float_y = start_y
        if self.image:
            self.rect = self.image.get_rect(center=(self.float_x, self.float_y))
        else:
            self.rect = pygame.Rect(start_x - 2, start_y - 2, 4, 4)

        self.target = target_enemy
        self.damage = damage
        self.base_speed = 5
        self.is_active = True

    def move(self, time_scale=1.0):
        if not self.is_active:
            return # Skip if already inactive
        if not self.target or self.target.is_dead:
            self.is_active = False
            return

        # Calculate actual speed based on time scale
        current_speed = self.base_speed * time_scale

        # Move towards the target
        target_x, target_y = self.target.rect.centerx, self.target.rect.centery
        direction_x = target_x - self.float_x
        direction_y = target_y - self.float_y
        distance = (direction_x ** 2 + direction_y ** 2) ** 0.5

        if distance < current_speed:
            # Hit the target
            self.target.take_damage(self.damage)
            self.is_active = False
        elif distance > 0: # Avoid division by zero
            self.float_x += current_speed * direction_x / distance
            self.float_y += current_speed * direction_y / distance
            # Update rect position
            self.rect.center = (self.float_x, self.float_y)
        else:
            # Projectile is exactly at target, consider it a hit
            self.target.take_damage(self.damage)
            self.is_active = False

    def draw(self, screen):
        if self.is_active:
            if self.image:
                screen.blit(self.image, self.rect)
            else:
                pygame.draw.rect(screen, (255, 255, 0), self.rect) 