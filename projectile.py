import pygame

class Projectile:
    def __init__(self, start_x, start_y, target_enemy, damage):
        self.x = start_x
        self.y = start_y
        self.target = target_enemy
        self.damage = damage
        self.speed = 5
        self.is_active = True

    def move(self):
        if not self.target or self.target.is_dead:
            self.is_active = False
            return

        # Move towards the target
        target_x, target_y = self.target.x, self.target.y
        direction_x = target_x - self.x
        direction_y = target_y - self.y
        distance = (direction_x ** 2 + direction_y ** 2) ** 0.5

        if distance < self.speed:
            # Hit the target
            self.target.take_damage(self.damage)
            self.is_active = False
        else:
            self.x += self.speed * direction_x / distance
            self.y += self.speed * direction_y / distance

    def draw(self, screen):
        if self.is_active:
            pygame.draw.circle(screen, (255, 255, 0), (int(self.x), int(self.y)), 4) # Yellow projectile 