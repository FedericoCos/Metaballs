import pygame
import numpy as np
import random
import time

# Global variables
WIDTH = 1280
HEIGHT = 720
FPS = 165
# Sphere variables
NUM_SPHERES = 15
MIN_RADIUS = 15
MAX_RADIUS = 45
MAX_VEL = 150
# Voxel variables
SQUARE_SIZE = 10
HALF_SQUARE_SIZE = SQUARE_SIZE // 2
THRESHOLD = 0.05

# Colors
WHITE = (255, 255, 255)
BACKGROUND = (20, 20, 30)
METABALL_OUTLINE = (0, 255, 200)
DEBUG_GRID = (50, 50, 70)
DEBUG_POINT_ABOVE = (0, 255, 0)
DEBUG_POINT_BELOW = (50, 50, 70)

class Metaball:
    def __init__(self):
        self.radius = random.uniform(MIN_RADIUS, MAX_RADIUS)
        self.x = random.uniform(self.radius, WIDTH - self.radius)
        self.y = random.uniform(self.radius, HEIGHT - self.radius)
        self.vel_x = random.uniform(-MAX_VEL, MAX_VEL)
        self.vel_y = random.uniform(-MAX_VEL, MAX_VEL)
        # Strength proportional to radius for more natural look
        self.strength = self.radius * 0.8

    def update(self, dt):
        # Update position with velocity and time delta
        self.x += self.vel_x * dt
        self.y += self.vel_y * dt

        # Bounce off walls
        if self.x - self.radius < 0:
            self.x = self.radius
            self.vel_x = abs(self.vel_x)
        elif self.x + self.radius > WIDTH:
            self.x = WIDTH - self.radius
            self.vel_x = -abs(self.vel_x)

        if self.y - self.radius < 0:
            self.y = self.radius
            self.vel_y = abs(self.vel_y)
        elif self.y + self.radius > HEIGHT:
            self.y = HEIGHT - self.radius
            self.vel_y = -abs(self.vel_y)
    
    def get_field_value(self, x, y):
        # Fast inverse square distance field
        dx = x - self.x
        dy = y - self.y
        squared_distance = max(dx*dx + dy*dy, 1)  # Avoid division by zero
        return self.strength / squared_distance


def get_total_field(metaballs, x, y):
    # Fast sum of field values from all metaballs
    total = 0
    for ball in metaballs:
        total += ball.get_field_value(x, y)
    return total


def interpolate(p1, v1, p2, v2, threshold):
    """Linear interpolation to find precise crossing point"""
    # If the values are very close, return midpoint to avoid division issues
    if abs(v1 - v2) < 0.0001:
        return (int((p1[0] + p2[0]) / 2), int((p1[1] + p2[1]) / 2))
    
    # Calculate interpolation factor
    t = (threshold - v1) / (v2 - v1)
    
    # Clamp to [0,1] range for safety
    t = max(0.0, min(1.0, t))
    
    # Interpolate coordinates and convert to integers
    x = int(p1[0] + t * (p2[0] - p1[0]))
    y = int(p1[1] + t * (p2[1] - p1[1]))
    
    return (x, y)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Metaballs with Marching Squares")
    clock = pygame.time.Clock()
    
    # Create metaballs
    metaballs = [Metaball() for _ in range(NUM_SPHERES)]
    
    # Grid dimensions (add 1 to include right/bottom edge)
    grid_width = WIDTH // SQUARE_SIZE + 1
    grid_height = HEIGHT // SQUARE_SIZE + 1

    # Pre-allocate grid as numpy array for speed
    grid = np.zeros((grid_height, grid_width), dtype=np.float32)
    
    
    # Program state
    running = True
    show_debug = False
    show_fps = True
    last_time = time.time()
    
    # Main game loop
    while running:
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_d:
                    show_debug = not show_debug
        
        # Update metaballs
        for ball in metaballs:
            ball.update(dt)
        
        # Clear the screen
        screen.fill(BACKGROUND)
        
        update_start_time = 0.0
        update_tot = 0.0
        # Calculate field values at grid points
        for y in range(grid_height):
            for x in range(grid_width):
                update_start_time = time.time_ns()
                grid[y, x] = get_total_field(metaballs, x * SQUARE_SIZE, y * SQUARE_SIZE)
                update_tot += time.time_ns() - update_start_time
        
        
        draw_start_time = 0.0
        draw_tot = 0.0
        
        # Process each cell in the grid
        for y in range(grid_height - 1):
            for x in range(grid_width - 1):
                draw_start_time = time.time_ns()
                # Cell corner coordinates
                x_pos = x * SQUARE_SIZE
                y_pos = y * SQUARE_SIZE
                
                # Get field values at the four corners
                val_tl = grid[y, x]
                val_tr = grid[y, x + 1]
                val_br = grid[y + 1, x + 1]
                val_bl = grid[y + 1, x]
                
                # Skip cells entirely inside or outside the threshold
                if ((val_tl > THRESHOLD and val_tr > THRESHOLD and 
                     val_br > THRESHOLD and val_bl > THRESHOLD) or
                    (val_tl < THRESHOLD and val_tr < THRESHOLD and 
                     val_br < THRESHOLD and val_bl < THRESHOLD)):
                    continue
                
                # Cell corner positions
                p_tl = (x_pos, y_pos)
                p_tr = (x_pos + SQUARE_SIZE, y_pos)
                p_br = (x_pos + SQUARE_SIZE, y_pos + SQUARE_SIZE)
                p_bl = (x_pos, y_pos + SQUARE_SIZE)
                
                # Debug visualization
                if show_debug:
                    # Draw cell grid
                    pygame.draw.rect(screen, DEBUG_GRID, (x_pos, y_pos, SQUARE_SIZE, SQUARE_SIZE), 1)
                    
                    # Draw corner points with field values
                    def draw_corner(pos, val):
                        color = DEBUG_POINT_ABOVE if val > THRESHOLD else DEBUG_POINT_BELOW
                        pygame.draw.circle(screen, color, (int(pos[0]), int(pos[1])), 2)
                    
                    draw_corner(p_tl, val_tl)
                    draw_corner(p_tr, val_tr)
                    draw_corner(p_br, val_br)
                    draw_corner(p_bl, val_bl)
                    
                # Find intersection points (where field value crosses threshold)
                points = []
                
                # Check each edge for crossings
                # Top edge
                if (val_tl > THRESHOLD) != (val_tr > THRESHOLD):
                    points.append(interpolate(p_tl, val_tl, p_tr, val_tr, THRESHOLD))
                
                # Right edge
                if (val_tr > THRESHOLD) != (val_br > THRESHOLD):
                    points.append(interpolate(p_tr, val_tr, p_br, val_br, THRESHOLD))
                
                # Bottom edge
                if (val_br > THRESHOLD) != (val_bl > THRESHOLD):
                    points.append(interpolate(p_br, val_br, p_bl, val_bl, THRESHOLD))
                
                # Left edge
                if (val_bl > THRESHOLD) != (val_tl > THRESHOLD):
                    points.append(interpolate(p_bl, val_bl, p_tl, val_tl, THRESHOLD))
                
                # Connect points to form line segments
                if len(points) == 2:
                    # Simple case: one line segment through the cell
                    pygame.draw.line(screen, METABALL_OUTLINE, points[0], points[1], 2)
                
                elif len(points) == 4:
                    # Ambiguous case (saddle point)
                    # Use average value at center to determine how to connect
                    center_val = (val_tl + val_tr + val_br + val_bl) / 4
                    
                    if center_val > THRESHOLD:
                        # Connect points 0-3 and 1-2
                        pygame.draw.line(screen, METABALL_OUTLINE, points[0], points[3], 2)
                        pygame.draw.line(screen, METABALL_OUTLINE, points[1], points[2], 2)
                    else:
                        # Connect points 0-1 and 2-3
                        pygame.draw.line(screen, METABALL_OUTLINE, points[0], points[1], 2)
                        pygame.draw.line(screen, METABALL_OUTLINE, points[2], points[3], 2)
                draw_tot += time.time_ns() - draw_start_time
        
        # Debug: show metaball centers and radiuses
        if show_debug:
            for ball in metaballs:
                # Draw center point
                pygame.draw.circle(screen, (255, 0, 0), (int(ball.x), int(ball.y)), 3)
                # Draw radius circle
                pygame.draw.circle(screen, WHITE, (int(ball.x), int(ball.y)), int(ball.radius), 1)
        
        
        pygame.display.set_caption(f"Simulation - FPS: {clock.get_fps():.1f} - Update Time: {update_tot / 1000000:.2f}ms - Draw Time: {draw_tot / 1000000:.2f}ms")

        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()

if __name__ == "__main__":
    main()