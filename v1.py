import pygame as pg
from pygame.locals import *
import sys
import random
import math


# global variables
WIDTH = 1280
HEIGHT = 720
FPS = 165

# SPHERE VARIABLES
NUM_SPHERES = 15
MIN_RADIUS = 15
MAX_RADIUS = 45
MAX_VEL = 150

# VOXEL VARIABLE
SQUARE_SIZE = 10
HALF_SQUARE_SIZE = SQUARE_SIZE // 2
THRESHOLD = 2.5


# colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (125, 125, 125)
GREEN = (0, 255, 0)

class Sphere:
    def __init__(self):
        self.radius = MIN_RADIUS + random.random() * (MAX_RADIUS - MIN_RADIUS)
        self.x = random.random() * WIDTH
        self.y = random.random() * HEIGHT
        
        self.vel_x = random.random() * MAX_VEL
        self.vel_y = random.random() * MAX_VEL
        
    def update(self, elapsed_time):
        self.x += self.vel_x * elapsed_time
        
        if (self.x >= WIDTH and self.vel_x > 0) or (self.x <= 0 and self.vel_x < 0):
            self.vel_x *= -1
            
        
        self.y += self.vel_y * elapsed_time
        
        if (self.y >= HEIGHT and self.vel_y > 0) or (self.y <= 0 and self.vel_y < 0):
            self.vel_y *= -1
            
    def draw(self, surface):
        pg.draw.circle(surface, WHITE, (self.x, self.y), self.radius, 1)
        
    def is_inside(self, x, y):
        distance = math.sqrt((self.x - x) ** 2 + (self.y - y) ** 2)
        if distance <= self.radius:
            return (True, distance / self.radius)
        return (False, 0.0)
    
    def calc_val(self, x, y):
        return self.radius / (math.sqrt((self.x - x) ** 2 + (self.y - y) ** 2) + 0.0001)

class Square:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
        self.vertices = {(self.x, self.y): [False, 0.0], 
                         (self.x + SQUARE_SIZE, self.y): [False, 0.0],
                         (self.x + SQUARE_SIZE, self.y + SQUARE_SIZE): [False, 0.0],
                         (self.x, self.y + SQUARE_SIZE): [False, 0.0]} 
        
        self.vertices_array = [(self.x, self.y),
                         (self.x + SQUARE_SIZE, self.y),
                         (self.x + SQUARE_SIZE, self.y + SQUARE_SIZE),
                         (self.x, self.y + SQUARE_SIZE)]
        
        self.edges = {(self.x + HALF_SQUARE_SIZE, self.y): [False, [0, 0], False],
                      (self.x + SQUARE_SIZE, self.y + HALF_SQUARE_SIZE): [False, [0, 0], False],
                      (self.x + HALF_SQUARE_SIZE, self.y + SQUARE_SIZE): [False, [0, 0], False],
                      (self.x, self.y + HALF_SQUARE_SIZE): [False, [0, 0], False]}
        
        self.edges_array = [(self.x + HALF_SQUARE_SIZE, self.y),
                      (self.x + SQUARE_SIZE, self.y + HALF_SQUARE_SIZE),
                      (self.x + HALF_SQUARE_SIZE, self.y + SQUARE_SIZE),
                      (self.x, self.y + HALF_SQUARE_SIZE)]
        
        self.useless = True
        
        
    def update(self, spheres):
        self.useless = True
        for v in self.vertices.keys():
            self.vertices[v] = [False, 0.0]
            
        for e in self.edges.keys():
            self.edges[e] = [False, [0, 0], False]
        
        for v in self.vertices.keys():
            for s in spheres:
                self.vertices[v][1] += s.calc_val(v[0], v[1])
            if self.vertices[v][1] >= THRESHOLD:
                self.vertices[v][0] = True
           
        for index in range(4):
            if self.vertices[self.vertices_array[index]][0] and not self.vertices[self.vertices_array[(index + 1) % 4]][0]:
                self.edges[self.edges_array[index]][0] = True
                self.useless = False
        
        for index in range(4, 0, -1):
            if self.vertices[self.vertices_array[index % 4]][0] and not self.vertices[self.vertices_array[index - 1]][0]:
                self.edges[self.edges_array[index - 1]][0] = True
                self.useless = False
                
        
                
    def draw(self, surface):
        """ for v in self.vertices.keys():
            if self.vertices[v][0]:
                pg.draw.circle(surface, GRAY, v, 2, 1) """
                
        if self.useless:
            return
                
        for i in range(3):
            if self.edges[self.edges_array[i]][0]:
                for j in range(i+1, 4):
                    if self.edges[self.edges_array[j]][0]:
                        if not self.edges[self.edges_array[i]][2]:
                            active1, off1 = None, None
                            
                            if self.vertices[self.vertices_array[i]][0]:
                                active1, off1 = [[self.vertices_array[i], self.vertices[self.vertices_array[i]][1]],
                                            [self.vertices_array[(i+1)%4], self.vertices[self.vertices_array[(i+1)%4]][1]]]
                            else:
                                off1, active1 = [[self.vertices_array[i], self.vertices[self.vertices_array[i]][1]],
                                            [self.vertices_array[(i+1)%4], self.vertices[self.vertices_array[(i+1)%4]][1]]]
                                
                            self.edges[self.edges_array[i]][1] = [
                                off1[0][0] + (active1[0][0] - off1[0][0]) * (THRESHOLD - off1[1]) / (active1[1] - off1[1]),
                                off1[0][1] + (active1[0][1] - off1[0][1]) * (THRESHOLD - off1[1]) / (active1[1] - off1[1]),
                            ]
                            
                            self.edges[self.edges_array[i]][2] = True
                        
                        if not self.edges[self.edges_array[j]][2]:
                            active2, off2 = None, None
                            
                            if self.vertices[self.vertices_array[j]][0]:
                                active2, off2 = [[self.vertices_array[j], self.vertices[self.vertices_array[j]][1]],
                                            [self.vertices_array[(j+1)%4], self.vertices[self.vertices_array[(j+1)%4]][1]]]
                            else:
                                off2, active2 = [[self.vertices_array[j], self.vertices[self.vertices_array[j]][1]],
                                            [self.vertices_array[(j+1)%4], self.vertices[self.vertices_array[(j+1)%4]][1]]]
                                
                            
                            self.edges[self.edges_array[j]][1] = [
                                off2[0][0] + (active2[0][0] - off2[0][0]) * (THRESHOLD - off2[1]) / (active2[1] - off2[1]),
                                off2[0][1] + (active2[0][1] - off2[0][1]) * (THRESHOLD - off2[1]) / (active2[1] - off2[1]),
                            ]
                            
                            self.edges[self.edges_array[j]][2] = True
                        
                        
                        pg.draw.line(surface, GREEN, self.edges[self.edges_array[i]][1], self.edges[self.edges_array[j]][1])
                        

class MarchingSquares:
    def __init__(self):
        pg.init()
        pg.mixer.init()
        
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        self.clock = pg.time.Clock()
        self.surface = pg.display.get_surface()
        
        self.spheres = []
        
        self.current_time = 0
        
        for _ in range(NUM_SPHERES):
            temp = Sphere()
            self.spheres.append(temp)
            
        self.grid = []
        for x in range(0, WIDTH + SQUARE_SIZE, SQUARE_SIZE):
            for y in range(0, HEIGHT + SQUARE_SIZE, SQUARE_SIZE):
                self.grid.append(Square(x, y))
        
        
    
    def run(self):
        while True:
            self.clock.tick(FPS)
            
            
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
                    
            
            self.screen.fill(BLACK)
            
            for s in self.spheres:
                s.update(self.clock.get_time() / 1000)
                # s.draw(self.surface)
                
            for square in self.grid:
                square.update(self.spheres)
                square.draw(self.surface)
            
            pg.display.set_caption(f"Simulation - FPS: {self.clock.get_fps():.1f}")
            
        
        
            pg.display.flip()
        

              
                
            
            


ms = MarchingSquares()
ms.run()