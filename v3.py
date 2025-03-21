import pygame as pg
from pygame.locals import *
import sys
import random
import numpy as np
import time


# Global variables
WIDTH = 1280
HEIGHT = 720
FPS = 300

# Sphere variables
NUM_SPHERES = 15
MIN_RADIUS = 15
MAX_RADIUS = 45
MAX_VEL = 150

# Voxel variables
SQUARE_SIZE = 20
HALF_SQUARE_SIZE = SQUARE_SIZE // 2
THRESHOLD = 2


# colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (125, 125, 125)
GREEN = (0, 255, 0)

class Spheres:
    def __init__(self):
        spheres = []
        velocities = []
        
        for _ in range(NUM_SPHERES):
            spheres.append([random.random() * WIDTH, random.random() * HEIGHT, MIN_RADIUS + random.random() * (MAX_RADIUS - MIN_RADIUS)])
            velocities.append([random.random() * MAX_VEL, random.random() * MAX_VEL])
        
        self.spheres = np.array(spheres)
        self.velocities = np.array(velocities)

    def update(self, elapsed_time):
        self.spheres[:, 0:2] += self.velocities * elapsed_time
        
        
        x_right_collision = (self.spheres[:, 0] >= WIDTH) & (self.velocities[:, 0] > 0)
        x_left_collision = (self.spheres[:, 0] <= 0) & (self.velocities[:, 0] < 0)
        self.velocities[x_right_collision | x_left_collision, 0] *= -1
        
        
        y_bottom_collision = (self.spheres[:, 1] >= HEIGHT) & (self.velocities[:, 1] > 0)
        y_top_collision = (self.spheres[:, 1] <= 0) & (self.velocities[:, 1] < 0)
        self.velocities[y_bottom_collision | y_top_collision, 1] *= -1
    
    def calc_val(self, x_vals, y_vals):
        dx = self.spheres[:, 0] - x_vals[:, None] 
        dy = self.spheres[:, 1] - y_vals[:, None]  
        distances = np.sqrt(dx**2 + dy**2) + 0.0001  
        
        values = self.spheres[:, 2] / distances
        return np.sum(values, axis=1)
    
class Squares:
    def __init__(self):
        self.vertices = {}
        self.edges = {}
        
        for x in range(0, WIDTH + SQUARE_SIZE, SQUARE_SIZE):
            for y in range(0, HEIGHT + SQUARE_SIZE, SQUARE_SIZE):
                self.vertices[(x, y)] = [False, 0.0]
                
        
        for x in range(0, WIDTH, SQUARE_SIZE):
            for y in range(0, HEIGHT + SQUARE_SIZE, SQUARE_SIZE):
                self.edges[(x + HALF_SQUARE_SIZE, y)] = [False, [0, 0], False, True]
        
        for x in range(0, WIDTH + SQUARE_SIZE, SQUARE_SIZE):
            for y in range(0, HEIGHT, SQUARE_SIZE):
                self.edges[(x, y + HALF_SQUARE_SIZE)] = [False, [0, 0], False, False]
                
        self.movement_y = (
            (HALF_SQUARE_SIZE, -HALF_SQUARE_SIZE),
            (SQUARE_SIZE, 0),
            (HALF_SQUARE_SIZE, HALF_SQUARE_SIZE),
            (-HALF_SQUARE_SIZE, HALF_SQUARE_SIZE),
        )
        
        self.movement_x = (
            (HALF_SQUARE_SIZE, HALF_SQUARE_SIZE),
            (0, SQUARE_SIZE)
        )
        
        self.x_vals = np.array([v[0] for v in self.vertices.keys()])
        self.y_vals = np.array([v[1] for v in self.vertices.keys()])
                
    def update(self, spheres):
        
        for v in self.vertices.keys():
            self.vertices[v][0], self.vertices[v][1] = False, 0.0
            
        for e in self.edges.keys():
            self.edges[e][0], self.edges[e][1], self.edges[e][2], self.edges[e][3] = False, [0, 0], False, self.edges[e][3]
        

        
        values = spheres.calc_val(self.x_vals, self.y_vals)
        

        for i, v in enumerate(self.vertices.keys()):
            self.vertices[v][1] = values[i]
            if self.vertices[v][1] >= THRESHOLD:
                self.vertices[v][0] = True
        
        
        for x in range(0, WIDTH, SQUARE_SIZE):
            for y in range(0, HEIGHT, SQUARE_SIZE):
                
                if self.vertices[(x, y)][0] != self.vertices[(x + SQUARE_SIZE, y)][0]:
                    self.edges[(x + HALF_SQUARE_SIZE, y)][0] = True
                
                
                if self.vertices[(x, y)][0] != self.vertices[(x, y + SQUARE_SIZE)][0]:
                    self.edges[(x, y + HALF_SQUARE_SIZE)][0] = True
        

        for y in range(0, HEIGHT, SQUARE_SIZE):
            if self.vertices[(WIDTH, y)][0] != self.vertices[(WIDTH, y + SQUARE_SIZE)][0]:
                self.edges[(WIDTH, y + HALF_SQUARE_SIZE)][0] = True
        

        for x in range(0, WIDTH, SQUARE_SIZE):
            if self.vertices[(x, HEIGHT)][0] != self.vertices[(x + SQUARE_SIZE, HEIGHT)][0]:
                self.edges[(x + HALF_SQUARE_SIZE, HEIGHT)][0] = True
                
    
    def draw(self, surface):
        for edge in self.edges.keys():
            if not self.edges[edge][0]:
                continue
                
            if not self.edges[edge][2]:
                if self.edges[edge][3]:  
                    key1, key2 = (edge[0] - HALF_SQUARE_SIZE, edge[1]), (edge[0] + HALF_SQUARE_SIZE, edge[1])
                else:  
                    key1, key2 = (edge[0], edge[1] - HALF_SQUARE_SIZE), (edge[0], edge[1] + HALF_SQUARE_SIZE)
                    
                
                if self.vertices[key1][0]:
                    active1, off1 = key1, key2
                    active_val, off_val = self.vertices[key1][1], self.vertices[key2][1]
                else:
                    active1, off1 = key2, key1
                    active_val, off_val = self.vertices[key2][1], self.vertices[key1][1]
                    
                
                t = (THRESHOLD - off_val) / (active_val - off_val)
                t = max(0.0, min(1.0, t))
                self.edges[edge][1][0], self.edges[edge][1][1] = int(off1[0] + (active1[0] - off1[0]) * t), int(off1[1] + (active1[1] - off1[1]) * t)
                
                
                self.edges[edge][2] = True 
            
            
            movements = self.movement_x if self.edges[edge][3] else self.movement_y
            
            for mov in movements:
                edge2 = (edge[0] + mov[0], edge[1] + mov[1])
                if edge2 in self.edges and self.edges[edge2][0]:
                    if not self.edges[edge2][2]:
                        if self.edges[edge2][3]:  
                            key1, key2 = (edge2[0] - HALF_SQUARE_SIZE, edge2[1]), (edge2[0] + HALF_SQUARE_SIZE, edge2[1])
                        else:  
                            key1, key2 = (edge2[0], edge2[1] - HALF_SQUARE_SIZE), (edge2[0], edge2[1] + HALF_SQUARE_SIZE)
                        
                        
                        if self.vertices[key1][0]:
                            active1, off1 = key1, key2
                            active_val, off_val = self.vertices[key1][1], self.vertices[key2][1]
                        else:
                            active1, off1 = key2, key1
                            active_val, off_val = self.vertices[key2][1], self.vertices[key1][1]
                        
                        
                        t = (THRESHOLD - off_val) / (active_val - off_val)
                        t = max(0.0, min(1.0, t))
                        self.edges[edge2][1][0], self.edges[edge2][1][1] = int(off1[0] + (active1[0] - off1[0]) * t), int(off1[1] + (active1[1] - off1[1]) * t)
                        
                        self.edges[edge2][2] = True 
                    
                    pg.draw.line(surface, GREEN, self.edges[edge][1], self.edges[edge2][1], 3)
                    
                        
                        
        

class MarchinSquare:
    def __init__(self):
        pg.init()
        pg.mixer.init()
        
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        self.clock = pg.time.Clock()
        self.surface = pg.display.get_surface()
                
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
            self.squares.draw(self.surface)
            draw_end_time = time.time()

            # Calculate the computation time for both operations
            update_time = (update_end_time - update_start_time) * 1000  # Convert to milliseconds
            draw_time = (draw_end_time - draw_start_time) * 1000  # Convert to milliseconds

            # Update the window caption with the FPS and times for update and draw
            pg.display.set_caption(f"Simulation - FPS: {self.clock.get_fps():.1f} - Update Time: {update_time:.2f}ms - Draw Time: {draw_time:.2f}ms")
            
        
        
            pg.display.flip()
        

              
marchinSquare = MarchinSquare()
marchinSquare.run()