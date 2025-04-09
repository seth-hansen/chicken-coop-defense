import pygame

class Enemy:
    def __init__(self, path):
        self.path = path
        self.x, self.y = path[0]
        self.speed = 0.5  # Reduced speed
        self.max_health = 150 # Increased max health
        self.health = self.max_health
        self.path_index = 0
        self.is_dead = False # Flag to check if enemy is dead
        self.damage_taken_timer = 0
        self.damage_flash_duration = 10 # Frames to flash white

    def move(self):
        if self.is_dead: return # Stop moving if dead
        # Update damage flash timer
        if self.damage_taken_timer > 0:
            self.damage_taken_timer -= 1

        # Move the enemy along the path
        if self.path_index < len(self.path) - 1:
            target_x, target_y = self.path[self.path_index + 1]
            direction_x = target_x - self.x
            direction_y = target_y - self.y
            distance = (direction_x ** 2 + direction_y ** 2) ** 0.5
            if distance < self.speed:
                self.x, self.y = target_x, target_y
                self.path_index += 1
            else:
                self.x += self.speed * direction_x / distance
                self.y += self.speed * direction_y / distance

    def take_damage(self, damage):
        if self.is_dead: return # Cannot take damage if already dead
        self.health -= damage
        self.damage_taken_timer = self.damage_flash_duration # Start flash timer
        if self.health <= 0:
            self.die()

    def die(self):
        # Logic for when the enemy dies
        if not self.is_dead:
            print("Enemy defeated!")
            self.is_dead = True # Set the flag

    def draw(self, screen):
        # Determine color based on damage taken
        color = (255, 255, 255) if self.damage_taken_timer > 0 else (255, 0, 0) # Flash white
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), 10) 