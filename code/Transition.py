import pygame
from settings import *
from pygame.math import Vector2 as vector
class Transition:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.dark = False
        self.active = False
        self.border_width = 0
        self.direction = 1
        self.center = (WIDTH/2,HEIGHT/2)
        self.radius = vector(self.center).magnitude() * 2
        self.threshold = self.radius + 300
        self.speed = 900
    def reset_transition(self):
        self.active = False
        self.border_width = 0
        self.direction = 1
        self.dark = False
    def display(self,dt):
        if self.active:
            self.border_width += self.speed * dt * self.direction
            if self.border_width > self.threshold:
                self.border_width = self.threshold
                self.direction = -1
                self.dark = True
            if self.border_width < 0:
                self.active = False
                self.border_width = 1
                self.direction = 1
                self.dark = False
            pygame.draw.circle(self.display_surface,'black',self.center,self.radius,int(self.border_width))