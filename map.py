import random
import pygame

def get_path(screen_width=1920, screen_height=1080, num_major_points=5, points_between=2, border_margin=75):
    """Generates a more meandering path covering more screen area."""
    waypoints = []
    min_dist_sq = 75**2 # Minimum squared distance between any points

    def is_too_close(new_point, existing_points):
        np = pygame.Vector2(new_point)
        for p in existing_points:
            if (np - pygame.Vector2(p)).length_squared() < min_dist_sq:
                return True
        return False

    # 1. Starting Point
    start_x = border_margin
    start_y = random.randint(border_margin, screen_height - border_margin)
    waypoints.append((start_x, start_y))

    # 2. Major Waypoints across screen bands
    last_major_x = start_x
    last_major_y = start_y
    band_width = (screen_width - 2 * border_margin) / num_major_points

    for i in range(num_major_points):
        # Determine X bounds for this band
        band_start_x = border_margin + i * band_width
        band_end_x = border_margin + (i + 1) * band_width

        # Target X somewhere in the band, ensuring progress from last major point
        major_x = random.randint(int(max(band_start_x, last_major_x + 50)), int(band_end_x))

        # Target Y with significant vertical freedom
        major_y = random.randint(border_margin, screen_height - border_margin)

        major_point = (major_x, major_y)

        # 3. Add Intermediate points between last point and this major point
        last_point = waypoints[-1]
        for j in range(points_between):
            t = (j + 1) / (points_between + 1) # Interpolation factor (0..1)
            inter_x_base = last_point[0] + (major_point[0] - last_point[0]) * t
            inter_y_base = last_point[1] + (major_point[1] - last_point[1]) * t

            # Add significant random offset
            offset_range_x = band_width / 2
            offset_range_y = screen_height / 4
            inter_x = int(inter_x_base + random.uniform(-offset_range_x, offset_range_x))
            inter_y = int(inter_y_base + random.uniform(-offset_range_y, offset_range_y))

            # Clamp to screen bounds (minus margin)
            inter_x = max(border_margin, min(screen_width - border_margin, inter_x))
            inter_y = max(border_margin, min(screen_height - border_margin, inter_y))

            intermediate_point = (inter_x, inter_y)

            # Add if not too close to the previous point
            if not is_too_close(intermediate_point, waypoints):
                waypoints.append(intermediate_point)
            else:
                print(f"Skipping intermediate point {intermediate_point} - too close to {waypoints[-1]}")

        # 4. Add the Major waypoint itself (if not too close)
        if not is_too_close(major_point, waypoints):
            waypoints.append(major_point)
            last_major_x, last_major_y = major_point
        else:
            print(f"Skipping major point {major_point} - too close to {waypoints[-1]}")
            # If we skipped the major point, update last_major anyway to keep bands progressing
            last_major_x = major_x
            last_major_y = major_y

    # 5. Final Cleanup - Ensure last point is near the right edge
    final_point = waypoints[-1]
    if final_point[0] < screen_width - border_margin * 2: # If last point isn't far right enough
        end_x = screen_width - border_margin
        end_y = random.randint(border_margin, screen_height - border_margin)
        if not is_too_close((end_x, end_y), waypoints):
            waypoints.append((end_x, end_y))

    # Ensure there are at least 2 points
    if len(waypoints) < 2:
        print("Warning: Path generation resulted in < 2 points. Using default.")
        return [(border_margin, screen_height // 2), (screen_width - border_margin, screen_height // 2)]

    print(f"Generated Path ({len(waypoints)} points): {waypoints}")
    return waypoints 