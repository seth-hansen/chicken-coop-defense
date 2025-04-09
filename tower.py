from projectile import Projectile
import pygame
import math # For upgrade cost calculation

class Tower:
    MAX_LEVEL = 5 # Maximum level for any stat
    SECONDARY_MAX_LEVEL = 2 # Max level for the secondary chosen path

    def __init__(self, x, y, image):
        self.x = x
        self.y = y
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))

        # Base Stats
        self.base_range = 150
        self.base_damage = 30
        self.base_fire_rate = 60 # Cooldown frames at 60 FPS (1 second)
        self.base_cost = 100

        # Upgrade Levels
        self.range_level = 1
        self.damage_level = 1
        self.rate_level = 1

        # Specialization
        self.specialization = None # None, 'range', 'damage', 'rate'

        # Primary and locked paths
        self.primary_path = None # The main path chosen after level 3
        self.locked_paths = set() # Paths locked at Lvl 1 or Lvl 2

        # Calculate initial stats based on level 1
        self.range = 0
        self.damage = 0
        self.fire_rate = 0
        self._update_stats()

        self.fire_cooldown = 0
        self.cost = self.base_cost # Initial placement cost

    def _update_stats(self):
        """Recalculates current stats based on levels."""
        self.range = self.base_range + (self.range_level - 1) * 25 # +25 range per level
        self.damage = self.base_damage + (self.damage_level - 1) * 10 # +10 damage per level
        # Fire rate increase: Reduce cooldown frames (e.g., by 5 frames per level)
        # Ensure fire_rate doesn't go too low (e.g., minimum 10 frames)
        self.fire_rate = max(10, self.base_fire_rate - (self.rate_level - 1) * 8)
        # Don't print every time, only on upgrade
        # print(f"Tower Stats Updated: R:{self.range_level}({self.range}) D:{self.damage_level}({self.damage}) F:{self.rate_level}({self.fire_rate})")

    def get_upgrade_cost(self, stat_type, level=None):
        """Calculates the cost. Returns -1 if max level, -2 if locked."""
        # Check if locked into a different specialization
        if self.specialization and self.specialization != stat_type:
            return -2 # Locked

        current_level = level
        if current_level is None:
            if stat_type == 'range': current_level = self.range_level
            elif stat_type == 'damage': current_level = self.damage_level
            elif stat_type == 'rate': current_level = self.rate_level
            else: return -1 # Unknown type (treat as max)

        # --- Locking Logic --- #
        # 1. Is this path explicitly locked?
        if stat_type in self.locked_paths:
            return -2 # Locked

        # 2. Is a primary path chosen? If yes, can only upgrade primary beyond secondary cap.
        if self.primary_path and stat_type != self.primary_path:
            if current_level >= Tower.SECONDARY_MAX_LEVEL:
                 return -2 # Locked (Secondary path cap)

        # 3. Is the primary path maxed?
        if stat_type == self.primary_path and current_level >= Tower.MAX_LEVEL:
             return -1 # Max level reached

        # 4. Is a non-primary, non-locked path maxed (shouldn't happen if primary logic is correct)?
        if current_level >= Tower.MAX_LEVEL:
             return -1 # Max level reached
        # --- End Locking Logic --- #

        base_upgrade_cost = 30
        # Cost to reach level (current_level + 1)
        cost = int(base_upgrade_cost * math.pow(1.8, current_level - 1))
        return cost

    def get_total_spent(self):
        """Calculates the total gold spent on this tower (placement + upgrades)."""
        total_spent = self.base_cost
        # Calculate cost of upgrades purchased
        for level in range(1, self.range_level): # Levels 1 to current-1
            total_spent += self.get_upgrade_cost('range', level) # Cost to reach level+1
        for level in range(1, self.damage_level):
            total_spent += self.get_upgrade_cost('damage', level)
        for level in range(1, self.rate_level):
            total_spent += self.get_upgrade_cost('rate', level)
        return total_spent

    def get_sell_value(self):
        """Calculates the sell value (75% of total spent)."""
        return int(self.get_total_spent() * 0.75)

    def upgrade(self, stat_type):
        """Attempts to upgrade, sets specialization on reaching max level."""
        cost = self.get_upgrade_cost(stat_type)
        if cost < 0: # Covers max (-1) and locked (-2)
            print(f"Cannot upgrade {stat_type}: {'Max level' if cost == -1 else 'Locked'}.")
            return False, 0

        upgraded = False
        new_level = -1
        if stat_type == 'range' and self.range_level < Tower.MAX_LEVEL:
            self.range_level += 1
            new_level = self.range_level
            upgraded = True
        elif stat_type == 'damage' and self.damage_level < Tower.MAX_LEVEL:
            self.damage_level += 1
            new_level = self.damage_level
            upgraded = True
        elif stat_type == 'rate' and self.rate_level < Tower.MAX_LEVEL:
            self.rate_level += 1
            new_level = self.rate_level
            upgraded = True

        if upgraded:
            self._update_stats()
            print(f"Upgraded {stat_type} to level {new_level}. Cost: {cost}")
            # Check if specialization should be set
            if new_level == Tower.MAX_LEVEL and self.specialization is None:
                self.specialization = stat_type
                print(f"Tower specialized in {stat_type.upper()}!")

            # --- Apply Locking Logic --- #
            all_stats = {'range', 'damage', 'rate'}
            paths_at_lvl_2_or_more = {st for st in all_stats if getattr(self, st + '_level') >= 2}

            # 1. Lock third path when two paths reach level 2
            if len(paths_at_lvl_2_or_more) == 2 and not self.primary_path:
                third_path = list(all_stats - paths_at_lvl_2_or_more)[0]
                if third_path not in self.locked_paths:
                    self.locked_paths.add(third_path)
                    print(f"Locked third path: {third_path.upper()} at Level 1.")

            # 2. Set primary/secondary when one path reaches level 3
            if new_level == 3 and not self.primary_path:
                self.primary_path = stat_type
                print(f"Primary path chosen: {stat_type.upper()}")
                # Lock the other chosen path at level 2
                for other_path in paths_at_lvl_2_or_more:
                    if other_path != self.primary_path and other_path not in self.locked_paths:
                        self.locked_paths.add(other_path)
                        print(f"Locked secondary path: {other_path.upper()} at Level {Tower.SECONDARY_MAX_LEVEL}.")
            # --- End Locking Logic --- #

            return True, cost
        else:
            print(f"Upgrade failed for {stat_type} (Should not happen if cost check passed)")
            return False, 0

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

    def draw(self, screen, is_selected=False):
        screen.blit(self.image, self.rect)
        if is_selected:
            pygame.draw.circle(screen, (255, 255, 255, 100), self.rect.center, self.range, 2)

        # Draw Headband if specialized
        if self.specialization:
            headband_color = (0, 0, 0)
            if self.specialization == 'range': headband_color = (0, 0, 255) # Blue
            elif self.specialization == 'damage': headband_color = (255, 0, 0) # Red
            elif self.specialization == 'rate': headband_color = (0, 255, 0) # Green

            # Draw a small rectangle near the top-center
            headband_width = self.rect.width * 0.6
            headband_height = 6
            headband_x = self.rect.centerx - headband_width / 2
            headband_y = self.rect.top + 3 # Position near top
            headband_rect = pygame.Rect(headband_x, headband_y, headband_width, headband_height)

            pygame.draw.rect(screen, headband_color, headband_rect, border_radius=2)
            pygame.draw.rect(screen, (50, 50, 50), headband_rect, 1, border_radius=2) # Dark outline 

        # Draw Headband if primary path is MAXED
        primary_level = 0
        if self.primary_path == 'range': primary_level = self.range_level
        elif self.primary_path == 'damage': primary_level = self.damage_level
        elif self.primary_path == 'rate': primary_level = self.rate_level

        # Check if primary path exists AND is at max level
        if self.primary_path and primary_level >= Tower.MAX_LEVEL:
            headband_color = (0, 0, 0)
            if self.primary_path == 'range': headband_color = (0, 0, 255) # Blue
            elif self.primary_path == 'damage': headband_color = (255, 0, 0) # Red
            elif self.primary_path == 'rate': headband_color = (0, 255, 0) # Green

            headband_width = self.rect.width * 0.6
            headband_height = 6
            headband_x = self.rect.centerx - headband_width / 2
            headband_y = self.rect.top + 3
            headband_rect = pygame.Rect(headband_x, headband_y, headband_width, headband_height)
            pygame.draw.rect(screen, headband_color, headband_rect, border_radius=2)
            pygame.draw.rect(screen, (50, 50, 50), headband_rect, 1, border_radius=2) 