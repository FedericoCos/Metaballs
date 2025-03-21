import pygame as pg
from pygame.locals import *
import sys
import random
import numpy as np
import time

# Global constants
WIDTH = 1280
HEIGHT = 720
FPS = 165
NUM_SPHERES, MIN_RADIUS, MAX_RADIUS, MAX_VEL = 15, 15, 45, 150
SQUARE_SIZE, HALF_SQUARE_SIZE, THRESHOLD = 10, 5, 2.5
BLACK, GREEN = (0, 0, 0), (0, 255, 0)

class Spheres:
    def __init__(self):
        self.spheres = np.column_stack((
            np.random.rand(NUM_SPHERES) * WIDTH,
            np.random.rand(NUM_SPHERES) * HEIGHT,
            MIN_RADIUS + np.random.rand(NUM_SPHERES) * (MAX_RADIUS - MIN_RADIUS)
        ))
        self.velocities = (np.random.rand(NUM_SPHERES, 2) - 0.5) * MAX_VEL
    
    def update(self, elapsed_time):
        self.spheres[:, :2] += self.velocities * elapsed_time
        self.velocities[:, 0] *= ((self.spheres[:, 0] > 0) & (self.spheres[:, 0] < WIDTH)) * 2 - 1
        self.velocities[:, 1] *= ((self.spheres[:, 1] > 0) & (self.spheres[:, 1] < HEIGHT)) * 2 - 1
    
    def calc_val(self, x, y):
        dx, dy = self.spheres[:, 0] - x, self.spheres[:, 1] - y
        distances = np.hypot(dx, dy) + 1e-4
        return np.sum(self.spheres[:, 2] / distances)

class Squares:
    def __init__(self):
        self.vertices = {}
        self.edges = {}
        for x in range(0, WIDTH, SQUARE_SIZE):
            for y in range(0, HEIGHT, SQUARE_SIZE):
                self.vertices[(x, y)] = 0.0
                self.edges[(x + HALF_SQUARE_SIZE, y)] = [False, (0, 0)]
                self.edges[(x, y + HALF_SQUARE_SIZE)] = [False, (0, 0)]
    
    def update(self, spheres):
        changed_vertices = []
        for v in self.vertices:
            new_val = spheres.calc_val(v[0], v[1])
            if abs(self.vertices[v] - new_val) > 0.01:
                self.vertices[v] = new_val
                changed_vertices.append(v)
        
        for x, y in changed_vertices:
            for dx, dy in [(HALF_SQUARE_SIZE, 0), (0, HALF_SQUARE_SIZE)]:
                edge = (x + dx, y + dy)
                if edge in self.edges:
                    self.edges[edge][0] = (self.vertices[(x, y)] >= THRESHOLD) != (self.vertices.get((x + dx * 2, y + dy * 2), 0) >= THRESHOLD)
    
    def draw(self, surface):
        for (x, y), (active, pos) in self.edges.items():
            if active:
                pg.draw.line(surface, GREEN, (x - HALF_SQUARE_SIZE, y), (x + HALF_SQUARE_SIZE, y), 2)

class MarchingSquares:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        self.clock = pg.time.Clock()
        self.spheres = Spheres()
        self.squares = Squares()
    
    def run(self):
        while True:
            elapsed_time = self.clock.tick(FPS) / 1000
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
            self.screen.fill(BLACK)
            self.spheres.update(elapsed_time)
            update_start_time = time.time()
            self.squares.update(self.spheres)
            update_end_time = time.time()

            draw_start_time = time.time()
            self.squares.draw(self.screen)
            draw_end_time = time.time()

            # Calculate the computation time for both operations
            update_time = (update_end_time - update_start_time) * 1000  # Convert to milliseconds
            draw_time = (draw_end_time - draw_start_time) * 1000  # Convert to milliseconds

            # Update the window caption with the FPS and times for update and draw
            pg.display.set_caption(f"Simulation - FPS: {self.clock.get_fps():.1f} - Update Time: {update_time:.2f}ms - Draw Time: {draw_time:.2f}ms")
            pg.display.flip()

MarchingSquares().run()
