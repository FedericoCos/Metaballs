import pygame as pg
import sys
import random
import math
import numpy as np
from collections import defaultdict
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
THRESHOLD = 2.5

# Colors
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)

class Spheres:
    def __init__(self):
        self.spheres = np.array([
            [random.random() * WIDTH, random.random() * HEIGHT, MIN_RADIUS + random.random() * (MAX_RADIUS - MIN_RADIUS)]
            for _ in range(NUM_SPHERES)
        ])
        self.velocities = np.array([
            [random.random() * MAX_VEL, random.random() * MAX_VEL]
            for _ in range(NUM_SPHERES)
        ])
        
        # Pre-calculate grid points for faster lookup
        x_points = np.arange(0, WIDTH + SQUARE_SIZE, SQUARE_SIZE)
        y_points = np.arange(0, HEIGHT + SQUARE_SIZE, SQUARE_SIZE)
        self.grid_points = np.array([(x, y) for x in x_points for y in y_points])
        
        # Cache for storing calculated values
        self.value_cache = {}
        self.last_positions = np.copy(self.spheres[:, 0:2])
        self.cache_valid = False

    def update(self, elapsed_time):
        # Update positions
        self.spheres[:, 0:2] += self.velocities * elapsed_time
        
        # Check for boundary collisions
        x_right_collision = (self.spheres[:, 0] >= WIDTH) & (self.velocities[:, 0] > 0)
        x_left_collision = (self.spheres[:, 0] <= 0) & (self.velocities[:, 0] < 0)
        self.velocities[x_right_collision | x_left_collision, 0] *= -1
        
        y_bottom_collision = (self.spheres[:, 1] >= HEIGHT) & (self.velocities[:, 1] > 0)
        y_top_collision = (self.spheres[:, 1] <= 0) & (self.velocities[:, 1] < 0)
        self.velocities[y_bottom_collision | y_top_collision, 1] *= -1
        
        # Invalidate cache if positions changed significantly
        position_diff = np.sum(np.abs(self.spheres[:, 0:2] - self.last_positions))
        if position_diff > 0.1:
            self.cache_valid = False
            self.last_positions = np.copy(self.spheres[:, 0:2])
        
    def calc_val(self, x, y):
        # Check cache first
        key = (x, y)
        if self.cache_valid and key in self.value_cache:
            return self.value_cache[key]
        
        # Vectorized calculation
        dx = self.spheres[:, 0] - x
        dy = self.spheres[:, 1] - y
        distances_sq = dx**2 + dy**2
        
        # Optimization: Only compute for spheres that might influence this point
        # Sphere can only influence up to (radius * THRESHOLD) distance
        max_influence_radius = np.max(self.spheres[:, 2]) * THRESHOLD
        relevant_indices = distances_sq < (max_influence_radius * max_influence_radius * 4)
        
        if not np.any(relevant_indices):
            self.value_cache[key] = 0.0
            return 0.0
        
        # Only compute for relevant spheres
        relevant_spheres = self.spheres[relevant_indices]
        dx = relevant_spheres[:, 0] - x
        dy = relevant_spheres[:, 1] - y
        distances = np.sqrt(dx**2 + dy**2) + 0.0001
        values = relevant_spheres[:, 2] / distances
        result = np.sum(values)
        
        # Cache the result
        self.value_cache[key] = result
        return result
    
    def calc_vals_batch(self, points):
        """Calculate values for multiple points at once"""
        if self.cache_valid:
            return np.array([self.value_cache.get(tuple(point), 0.0) for point in points])
        
        results = np.zeros(len(points))
        for i, point in enumerate(points):
            results[i] = self.calc_val(point[0], point[1])
        
        return results

class Squares:
    def __init__(self):
        # Use numpy arrays for vertices and edges
        x_grid = np.arange(0, WIDTH + SQUARE_SIZE, SQUARE_SIZE)
        y_grid = np.arange(0, HEIGHT + SQUARE_SIZE, SQUARE_SIZE)
        
        # Create lookup tables for faster referencing
        self.vertices = {}
        self.vertex_coords = []
        for x in x_grid:
            for y in y_grid:
                self.vertices[(x, y)] = [False, 0.0]
                self.vertex_coords.append((x, y))
        
        self.vertex_coords = np.array(self.vertex_coords)
        
        # Create edges with optimized data structure
        self.edges = {}
        self.active_edges = set()  # Track only active edges
        
        # Horizontal edges
        for x in range(0, WIDTH, SQUARE_SIZE):
            for y in range(0, HEIGHT + SQUARE_SIZE, SQUARE_SIZE):
                self.edges[(x + HALF_SQUARE_SIZE, y)] = [False, [0, 0], False, True]
        
        # Vertical edges
        for x in range(0, WIDTH + SQUARE_SIZE, SQUARE_SIZE):
            for y in range(0, HEIGHT, SQUARE_SIZE):
                self.edges[(x, y + HALF_SQUARE_SIZE)] = [False, [0, 0], False, False]
        
        # Precompute movement patterns for faster lookup
        self.movement_x = (
            (-HALF_SQUARE_SIZE, -HALF_SQUARE_SIZE),
            (0, -SQUARE_SIZE),
            (HALF_SQUARE_SIZE, -HALF_SQUARE_SIZE),
            (-HALF_SQUARE_SIZE, HALF_SQUARE_SIZE),
            (0, SQUARE_SIZE),
            (HALF_SQUARE_SIZE, HALF_SQUARE_SIZE),
        )
        
        self.movement_y = (
            (-HALF_SQUARE_SIZE, -HALF_SQUARE_SIZE),
            (HALF_SQUARE_SIZE, -HALF_SQUARE_SIZE),
            (SQUARE_SIZE, 0),
            (HALF_SQUARE_SIZE, HALF_SQUARE_SIZE),
            (-HALF_SQUARE_SIZE, HALF_SQUARE_SIZE),
            (-SQUARE_SIZE, 0),
        )
        
        # Pre-calculate edge neighbors for faster lookup
        self.edge_neighbors = {}
        for edge in self.edges.keys():
            is_horizontal = self.edges[edge][3]
            movements = self.movement_x if is_horizontal else self.movement_y
            
            neighbors = []
            for mov in movements:
                edge2 = (edge[0] + mov[0], edge[1] + mov[1])
                if edge2 in self.edges:
                    neighbors.append(edge2)
            
            self.edge_neighbors[edge] = neighbors
                
    def update(self, spheres):
        # Reset vertex and edge state
        self.active_edges.clear()
        
        # Update vertex values in batch for better performance
        values = spheres.calc_vals_batch(self.vertex_coords)
        
        for i, coord in enumerate(self.vertex_coords):
            vertex = self.vertices[tuple(coord)]
            vertex[1] = values[i]
            vertex[0] = values[i] >= THRESHOLD
        
        # Check horizontal edges
        for x in range(0, WIDTH, SQUARE_SIZE):
            for y in range(0, HEIGHT + SQUARE_SIZE, SQUARE_SIZE):
                edge_key = (x + HALF_SQUARE_SIZE, y)
                if self.vertices[(x, y)][0] != self.vertices[(x + SQUARE_SIZE, y)][0]:
                    self.edges[edge_key][0] = True
                    self.active_edges.add(edge_key)
                else:
                    self.edges[edge_key][0] = False
                
                # Reset calculation state
                self.edges[edge_key][2] = False
        
        # Check vertical edges
        for x in range(0, WIDTH + SQUARE_SIZE, SQUARE_SIZE):
            for y in range(0, HEIGHT, SQUARE_SIZE):
                edge_key = (x, y + HALF_SQUARE_SIZE)
                if self.vertices[(x, y)][0] != self.vertices[(x, y + SQUARE_SIZE)][0]:
                    self.edges[edge_key][0] = True
                    self.active_edges.add(edge_key)
                else:
                    self.edges[edge_key][0] = False
                
                # Reset calculation state
                self.edges[edge_key][2] = False
    
    def draw(self, surface):
        # Use a surface for drawing all lines at once
        line_points = []
        
        # Only process active edges
        for edge in self.active_edges:
            # Calculate intersection point if not already done
            if not self.edges[edge][2]:
                is_horizontal = self.edges[edge][3]
                
                if is_horizontal:  
                    key1, key2 = (edge[0] - HALF_SQUARE_SIZE, edge[1]), (edge[0] + HALF_SQUARE_SIZE, edge[1])
                else:  
                    key1, key2 = (edge[0], edge[1] - HALF_SQUARE_SIZE), (edge[0], edge[1] + HALF_SQUARE_SIZE)
                
                if self.vertices[key1][0]:
                    active1, off1 = key1, key2
                    active_val, off_val = self.vertices[key1][1], self.vertices[key2][1]
                else:
                    active1, off1 = key2, key1
                    active_val, off_val = self.vertices[key2][1], self.vertices[key1][1]
                
                # Avoid division by zero
                if active_val != off_val:
                    t = (THRESHOLD - off_val) / (active_val - off_val)
                    self.edges[edge][1][0] = off1[0] + (active1[0] - off1[0]) * t
                    self.edges[edge][1][1] = off1[1] + (active1[1] - off1[1]) * t
                else:
                    # Fallback if values are equal
                    self.edges[edge][1][0] = edge[0]
                    self.edges[edge][1][1] = edge[1]
                
                self.edges[edge][2] = True
            
            # Draw lines between connected edges
            edge_pt = self.edges[edge][1]
            
            for neighbor in self.edge_neighbors[edge]:
                if neighbor in self.active_edges:
                    # Calculate intersection for neighbor if needed
                    if not self.edges[neighbor][2]:
                        is_horizontal = self.edges[neighbor][3]
                        
                        if is_horizontal:  
                            key1, key2 = (neighbor[0] - HALF_SQUARE_SIZE, neighbor[1]), (neighbor[0] + HALF_SQUARE_SIZE, neighbor[1])
                        else:  
                            key1, key2 = (neighbor[0], neighbor[1] - HALF_SQUARE_SIZE), (neighbor[0], neighbor[1] + HALF_SQUARE_SIZE)
                        
                        if self.vertices[key1][0]:
                            active1, off1 = key1, key2
                            active_val, off_val = self.vertices[key1][1], self.vertices[key2][1]
                        else:
                            active1, off1 = key2, key1
                            active_val, off_val = self.vertices[key2][1], self.vertices[key1][1]
                        
                        # Avoid division by zero
                        if active_val != off_val:
                            t = (THRESHOLD - off_val) / (active_val - off_val)
                            self.edges[neighbor][1][0] = off1[0] + (active1[0] - off1[0]) * t
                            self.edges[neighbor][1][1] = off1[1] + (active1[1] - off1[1]) * t
                        else:
                            self.edges[neighbor][1][0] = neighbor[0]
                            self.edges[neighbor][1][1] = neighbor[1]
                        
                        self.edges[neighbor][2] = True
                    
                    # Add line points to batch
                    neighbor_pt = self.edges[neighbor][1]
                    line_points.append((edge_pt, neighbor_pt))
        
        # Draw all lines at once
        for start, end in line_points:
            pg.draw.line(surface, GREEN, start, end, 2)

class MarchingSquare:
    def __init__(self):
        pg.init()
        
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        self.clock = pg.time.Clock()
        self.surface = pg.display.get_surface()
        
        self.spheres = Spheres()
        self.squares = Squares()
        
        # Performance tracking
        self.frame_times = []
        self.update_times = []
        self.draw_times = []
    
    def run(self):
        while True:
            # Start frame timing
            frame_start = pg.time.get_ticks()
            
            elapsed_time = self.clock.tick(FPS) / 1000
            
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
            
            self.screen.fill(BLACK)
            
            # Update spheres
            self.spheres.update(elapsed_time)
            
            # Update and draw squares with timing
            update_start = pg.time.get_ticks()
            self.squares.update(self.spheres)
            update_end = pg.time.get_ticks()
            
            draw_start = pg.time.get_ticks()
            self.squares.draw(self.surface)
            draw_end = pg.time.get_ticks()
            
            # Track performance
            self.update_times.append(update_end - update_start)
            self.draw_times.append(draw_end - draw_start)
            
            # Display FPS and timing info
            fps = self.clock.get_fps()
            
            pg.display.set_caption(f"Simulation - FPS: {self.clock.get_fps():.1f} - Update Time: {self.update_times[-1]:.2f}ms - Draw Time: {self.draw_times[-1]:.2f}ms")
            
            # Finish frame
            pg.display.flip()
            
            # Calculate total frame time
            frame_end = pg.time.get_ticks()
            self.frame_times.append(frame_end - frame_start)
            
            # Every 60 frames, check if we need to optimize further
            if len(self.frame_times) >= 60:
                # Clear old data
                self.frame_times = self.frame_times[-60:]
                
                # Enable/disable value caching based on performance
                avg_frame_time = sum(self.frame_times) / 60
                self.spheres.cache_valid = avg_frame_time > 16  # Only use cache if FPS is below target

if __name__ == "__main__":
    marchingSquare = MarchingSquare()
    marchingSquare.run()