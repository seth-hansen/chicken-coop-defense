import random
import pygame

def get_path(screen_width=1920, playable_height=930, num_major_points=5, points_between=2, border_margin=75):
    """Generates a path within the specified screen_width and playable_height,
       with the end point forced into the lower-right quadrant.
    """
    waypoints = []
    min_dist_sq = 75**2 # Minimum squared distance between any points

    # Adjust vertical border margin if playable height is small
    effective_border_margin_y = min(border_margin, playable_height // 4)

    def is_too_close(new_point, existing_points):
        np = pygame.Vector2(new_point)
        for p in existing_points:
            if (np - pygame.Vector2(p)).length_squared() < min_dist_sq:
                return True
        return False

    # 1. Starting Point (use playable_height for Y)
    start_x = border_margin
    start_y = random.randint(effective_border_margin_y, playable_height - effective_border_margin_y)
    waypoints.append((start_x, start_y))

    # 2. Major Waypoints across screen bands (use playable_height for Y)
    last_major_x = start_x
    last_major_y = start_y
    band_width = (screen_width - 2 * border_margin) / num_major_points

    # --- Loop through all but the last major point --- #
    for i in range(num_major_points - 1):
        band_start_x = border_margin + i * band_width
        band_end_x = border_margin + (i + 1) * band_width
        major_x = random.randint(int(max(band_start_x, last_major_x + 50)), int(band_end_x))
        major_y = random.randint(effective_border_margin_y, playable_height - effective_border_margin_y) # Use playable_height
        major_point = (major_x, major_y)

        # 3. Add Intermediate points (use playable_height for Y calculation and clamping)
        last_point = waypoints[-1]
        for j in range(points_between):
            t = (j + 1) / (points_between + 1)
            inter_x_base = last_point[0] + (major_point[0] - last_point[0]) * t
            inter_y_base = last_point[1] + (major_point[1] - last_point[1]) * t
            offset_range_x = band_width / 2
            offset_range_y = playable_height / 4 # Offset relative to playable height
            inter_x = int(inter_x_base + random.uniform(-offset_range_x, offset_range_x))
            inter_y = int(inter_y_base + random.uniform(-offset_range_y, offset_range_y))
            inter_x = max(border_margin, min(screen_width - border_margin, inter_x))
            inter_y = max(effective_border_margin_y, min(playable_height - effective_border_margin_y, inter_y)) # Clamp Y to playable area
            intermediate_point = (inter_x, inter_y)
            if not is_too_close(intermediate_point, waypoints):
                waypoints.append(intermediate_point)
            # else: print(f"Skipping intermediate point {intermediate_point} - too close")

        # 4. Add the Major waypoint (if not too close)
        if not is_too_close(major_point, waypoints):
            waypoints.append(major_point)
            last_major_x, last_major_y = major_point
        # else: print(f"Skipping major point {major_point} - too close")

    # --- Handle the LAST major point separately to force lower-right --- #
    last_band_start_x = border_margin + (num_major_points - 1) * band_width
    last_band_end_x = screen_width - border_margin # Extend to right edge

    # Force X coordinate towards the right half/third of the screen
    final_major_x_min = max(last_band_start_x, screen_width * 0.6) # Ensure it's in the right ~40%
    final_major_x = random.randint(int(final_major_x_min), int(last_band_end_x))

    # Force Y coordinate into the lower half of the playable area
    final_major_y_min = playable_height // 2
    final_major_y_max = playable_height - effective_border_margin_y
    final_major_y = random.randint(int(final_major_y_min), int(final_major_y_max))

    final_major_point = (final_major_x, final_major_y)

    # Add intermediate points leading to the final forced major point
    last_point = waypoints[-1]
    for j in range(points_between):
        t = (j + 1) / (points_between + 1)
        inter_x_base = last_point[0] + (final_major_point[0] - last_point[0]) * t
        inter_y_base = last_point[1] + (final_major_point[1] - last_point[1]) * t
        offset_range_x = band_width / 2
        offset_range_y = playable_height / 4
        inter_x = int(inter_x_base + random.uniform(-offset_range_x, offset_range_x))
        inter_y = int(inter_y_base + random.uniform(-offset_range_y, offset_range_y))
        inter_x = max(border_margin, min(screen_width - border_margin, inter_x))
        inter_y = max(effective_border_margin_y, min(playable_height - effective_border_margin_y, inter_y))
        intermediate_point = (inter_x, inter_y)
        if not is_too_close(intermediate_point, waypoints):
            waypoints.append(intermediate_point)
        # else: print(f"Skipping final intermediate point {intermediate_point} - too close")

    # Add the final major point (if not too close)
    if not is_too_close(final_major_point, waypoints):
        waypoints.append(final_major_point)
    # else: print(f"Skipping final forced major point {final_major_point} - too close")

    # --- End Lower-Right Forcing --- #

    # Final Cleanup (mostly redundant now but good safety)
    final_point = waypoints[-1]
    if final_point[0] < screen_width - border_margin * 2 or final_point[1] < playable_height / 2:
        end_x = screen_width - border_margin
        end_y = random.randint(int(playable_height / 2), int(playable_height - effective_border_margin_y))
        print(f"Cleanup: Adjusting final point to ({end_x}, {end_y})")
        if not is_too_close((end_x, end_y), waypoints):
            # Replace last point if too far left/too high after forcing logic
            waypoints[-1] = (end_x, end_y)

    # Ensure at least 2 points
    if len(waypoints) < 2:
        print("Warning: Path generation resulted in < 2 points. Using default.")
        # Default path ending lower right
        return [(border_margin, playable_height // 2), (screen_width - border_margin, playable_height * 3 // 4)]

    print(f"Generated Path ({len(waypoints)} points, ending lower-right): {waypoints[-1]}")
    return waypoints 