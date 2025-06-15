from projectile import Projectile
import pygame
import math # For upgrade cost calculation

class Tower:
    MAX_LEVEL = 5 # Maximum level for any stat
    SPECIAL_PATH_MAX_LEVEL = 3 # Max level for AoE/Duration paths

    # Define base stats per type
    BASE_STATS = {
        'basic': {'name':'Basic Chicken', 'range': 175, 'damage': 20, 'rate': 70, 'cost': 100, 'aoe': 0, 'dot_dmg': 0, 'dot_dur': 0},
        'bomb':  {'name':'Bomb Chicken',  'range': 140, 'damage': 30, 'rate': 120, 'cost': 150, 'aoe': 160, 'dot_dmg': 0, 'dot_dur': 0},
        'fire':  {'name':'Fire Chicken',  'range': 150, 'damage': 5, 'rate': 100, 'cost': 125, 'aoe': 5, 'dot_dmg': 8, 'dot_dur': 180},
        'minigun': {'name':'MiniGun Chicken', 'range': 150, 'damage': 5, 'rate': 35, 'cost': 200, 'aoe': 0, 'dot_dmg': 0, 'dot_dur': 20},
    }

    def __init__(self, x, y, image, tower_type='basic'):
        self.x = x
        self.y = y
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.tower_type = tower_type

        # Load base stats from dictionary
        stats = Tower.BASE_STATS.get(tower_type, Tower.BASE_STATS['basic']) # Default to basic if type unknown
        self.base_range = stats['range']
        self.base_damage = stats['damage']
        self.base_fire_rate = stats['rate']
        self.base_cost = stats['cost']
        self.base_aoe = stats['aoe'] # Base Area of Effect radius
        self.base_dot_damage = stats['dot_dmg'] # Base Damage Over Time per tick
        self.base_dot_duration = stats['dot_dur'] # Base DoT duration in frames

        # Upgrade Levels
        self.range_level = 1   # Used by Basic
        self.aoe_level = 1     # Used by Bomb
        self.duration_level = 1 # Used by Fire
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
        self.aoe_radius = 0 # Calculated AoE
        self.dot_damage = 0 # Calculated DoT damage
        self.dot_duration = 0 # Calculated DoT duration
        self._update_stats()

        self.fire_cooldown = 0
        self.cost = self.base_cost # Initial placement cost

    def _get_relevant_paths(self):
        """Returns the set of valid upgrade paths for this tower type."""
        if self.tower_type == 'basic':
            return {'range', 'damage', 'rate'}
        elif self.tower_type == 'bomb':
            return {'aoe', 'damage', 'rate'}
        elif self.tower_type == 'fire':
            return {'duration', 'damage', 'rate'}
        elif self.tower_type == 'minigun':
            return {'range', 'damage', 'rate'}
        else:
            return set() # Should not happen

    def _update_stats(self):
        """Recalculates current stats based on levels and type."""
        # Standard Stats (Damage and Fire Rate are universal)
        self.damage = self.base_damage + (self.damage_level - 1) * 10
        self.fire_rate = max(10, self.base_fire_rate - (self.rate_level - 1) * 8)

        # Type-Specific Stats & Upgrade Paths
        if self.tower_type == 'basic':
            self.range = self.base_range + (self.range_level - 1) * 25
            self.aoe_radius = 0
            self.dot_damage = 0
            self.dot_duration = 0
        elif self.tower_type == 'bomb':
            self.range = self.base_range # Fixed range
            # AoE increases by 5% multiplicatively per aoe_level
            self.aoe_radius = self.base_aoe * (1.05 ** (self.aoe_level - 1))
            self.aoe_radius += (self.damage_level - 1) * 5 # Keep minor damage boost?
            self.dot_damage = 0
            self.dot_duration = 0
        elif self.tower_type == 'fire':
            self.range = self.base_range # Fixed range
            self.aoe_radius = 0
            # DoT duration increases by 10% multiplicatively per duration_level
            self.dot_duration = int(self.base_dot_duration * (1.10 ** (self.duration_level - 1)))
            self.dot_damage = self.base_dot_damage + (self.damage_level - 1) * 2
        elif self.tower_type == 'minigun':
            self.range = self.base_range + (self.range_level - 1) * 25
            self.aoe_radius = 0
            self.dot_damage = 0
            self.dot_duration = 0

        # Ensure AoE is int
        self.aoe_radius = int(self.aoe_radius)

    def get_upgrade_cost(self, stat_type, level=None):
        """Calculates the cost. Returns -1 if max level, -2 if locked."""
        if stat_type not in self._get_relevant_paths():
             return -1
        current_level = level
        max_level_for_path = Tower.SPECIAL_PATH_MAX_LEVEL if stat_type in {'aoe', 'duration'} else Tower.MAX_LEVEL
        level_attr = stat_type + '_level'
        if current_level is None:
            if hasattr(self, level_attr):
                 current_level = getattr(self, level_attr)
            else:
                print(f"Error: Tower missing level attribute '{level_attr}'")
                return -1

        # --- Locking Logic (ONLY for Basic & Minigun Tower) --- #
        if self.tower_type == 'basic' or self.tower_type == 'minigun':
            # 1. Is this path explicitly locked?
            if stat_type in self.locked_paths:
                return -2 # Locked

            # 2. Is a primary path chosen? If yes, can only upgrade primary beyond secondary cap.
            #    Also applies to minigun
            # Removed this check - Now allowing two paths to max
            # if self.primary_path and stat_type != self.primary_path:
            #     if current_level >= Tower.SECONDARY_MAX_LEVEL:
            #         return -2 # Locked (Secondary path cap)
        # --- End Basic/Minigun Locking Logic --- #

        # --- Check Max Level (Applies to all types) --- #
        if stat_type == self.primary_path and current_level >= max_level_for_path:
             return -1 # Primary path max level reached
        elif current_level >= max_level_for_path:
             return -1 # Any path max level reached
        # --- End Max Level Check --- #

        # --- Cost Calculation (Applies to all types) --- #
        base_upgrade_cost = 30
        if stat_type == 'damage': base_upgrade_cost = 35
        elif stat_type == 'rate': base_upgrade_cost = 25
        elif stat_type == 'aoe': base_upgrade_cost = 30
        elif stat_type == 'duration': base_upgrade_cost = 25
        elif stat_type == 'range': base_upgrade_cost = 30 # Ensure range has a cost

        cost = int(base_upgrade_cost * math.pow(1.8, current_level - 1))
        return cost

    def get_total_spent(self):
        """Calculates the total gold spent on this tower (placement + upgrades)."""
        total_spent = self.base_cost
        paths = self._get_relevant_paths()

        for stat_type in paths:
            level_attr = stat_type + '_level'
            current_level = getattr(self, level_attr, 1)
            for level in range(1, current_level):
                cost_to_reach_next = self.get_upgrade_cost(stat_type, level)
                if cost_to_reach_next >= 0:
                    total_spent += cost_to_reach_next
        return total_spent

    def get_sell_value(self):
        """Calculates the sell value (75% of total spent)."""
        return int(self.get_total_spent() * 0.75)

    def upgrade(self, stat_type):
        """Attempts to upgrade, sets specialization on reaching max level."""
        cost = self.get_upgrade_cost(stat_type)
        if cost < 0:
            print(f"Cannot upgrade {stat_type}: {'Max level' if cost == -1 else 'Locked'}.")
            return False, 0

        level_attr = stat_type + '_level'
        if not hasattr(self, level_attr):
             print(f"Error: Cannot upgrade invalid stat '{stat_type}'")
             return False, 0
        current_level = getattr(self, level_attr)
        max_level_for_path = Tower.SPECIAL_PATH_MAX_LEVEL if stat_type in {'aoe', 'duration'} else Tower.MAX_LEVEL
        if current_level >= max_level_for_path:
            print(f"Cannot upgrade {stat_type}: Already at max level {max_level_for_path}.")
            return False, 0

        setattr(self, level_attr, current_level + 1)
        new_level = current_level + 1
        self._update_stats()
        print(f"Upgraded {stat_type} to level {new_level}. Cost: {cost}")

        # --- Set Primary Path (Applies to all types, used for headband) --- #
        available_paths = self._get_relevant_paths()
        paths_at_lvl_2_or_more = {st for st in available_paths if getattr(self, st + '_level', 1) >= 2}
        # Choose primary path at level 3, unless already chosen
        if new_level == 3 and not self.primary_path:
            # Ensure the stat being upgraded is a valid primary path for this tower
            if stat_type in available_paths:
                self.primary_path = stat_type
                print(f"Primary path chosen: {stat_type.upper()} (Determines headband)")

        # --- Locking Logic (ONLY for Basic & Minigun Tower) --- #
        # --- Generalized Locking Logic (Applies to all tower types with 3 paths) --- #
        # Lock the third path once two paths reach level 2
        if len(paths_at_lvl_2_or_more) == 2 and self.primary_path is None: # Check primary path ensures this only runs once
            # Check if there are exactly 3 available paths before locking
            if len(available_paths) == 3:
                third_path = list(available_paths - paths_at_lvl_2_or_more)[0]
                if third_path not in self.locked_paths:
                    self.locked_paths.add(third_path)
                    print(f"Locked third path: {third_path.upper()} at Level 1.")

            # 2. Lock secondary path when primary is chosen at level 3
            # Removed this section - locking happens when two paths hit L2
            # if self.primary_path == stat_type and new_level == 3:
            #     secondary_path_candidates = available_paths - {self.primary_path}
            #     for other_path in secondary_path_candidates:
            #         if other_path not in self.locked_paths:
            #             self.locked_paths.add(other_path)
            #             print(f"Locked secondary path: {other_path.upper()} at Level {Tower.SECONDARY_MAX_LEVEL}.")
        # --- End Basic/Minigun Locking Logic --- #
        # --- End Generalized Locking Logic --- #

        # --- Set Specialization (Applies to all types) --- #
        if new_level == max_level_for_path and self.specialization is None and self.primary_path == stat_type:
             self.specialization = stat_type
             print(f"Tower specialized in {stat_type.upper()}! (Headband set)")
        # --- End Set Specialization --- #

        return True, cost

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
                # Create projectile, passing its image and a reference to this tower
                if projectile_img:
                    # Pass self (the tower instance) as tower_ref
                    projectiles.append(Projectile(self.rect.centerx, self.rect.centery, target, self.damage, projectile_img, tower_ref=self))
                else: # Fallback if no image provided
                     # Pass self (the tower instance) as tower_ref
                    projectiles.append(Projectile(self.rect.centerx, self.rect.centery, target, self.damage, tower_ref=self))
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

        # --- Draw Headband (Consolidated Logic) --- #
        draw_headband = False
        headband_path = None
        max_level_for_primary = 0
        primary_level = 0
        if self.specialization:
            draw_headband = True
            headband_path = self.specialization
        elif self.primary_path:
            level_attr = self.primary_path + '_level'
            if hasattr(self, level_attr):
                primary_level = getattr(self, level_attr)
                max_level_for_primary = Tower.SPECIAL_PATH_MAX_LEVEL if self.primary_path in {'aoe', 'duration'} else Tower.MAX_LEVEL
                if primary_level >= max_level_for_primary:
                    draw_headband = True
                    headband_path = self.primary_path

        if draw_headband and headband_path:
            headband_color = (0, 0, 0)
            if headband_path == 'range' or headband_path == 'aoe': headband_color = (0, 0, 255)
            elif headband_path == 'damage': headband_color = (255, 0, 0)
            elif headband_path == 'rate' or headband_path == 'duration':
                # Special color for minigun rate path
                if self.tower_type == 'minigun' and headband_path == 'rate':
                    headband_color = (255, 255, 0) # Yellow
                else:
                    headband_color = (0, 255, 0) # Green

            # Draw a small rectangle near the top-center, lowered further
            headband_width = self.rect.width * 0.6
            headband_height = 6
            headband_x = self.rect.centerx - headband_width / 2
            headband_y = self.rect.top + 18 # Lowered further from +8
            headband_rect = pygame.Rect(headband_x, headband_y, headband_width, headband_height)
            pygame.draw.rect(screen, headband_color, headband_rect, border_radius=2)
            pygame.draw.rect(screen, (50, 50, 50), headband_rect, 1, border_radius=2) 