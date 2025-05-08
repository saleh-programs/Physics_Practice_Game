import sys

import pygame.image
import time

from camera import *
from scenes import *
from functions import *
import cProfile, pstats

class Main():
    def __init__(self):
        pygame.init()
        pygame.key.set_repeat(300, 30)

        self.display_surface = pygame.display.set_mode((WIDTH,HEIGHT))
        self.clock = pygame.time.Clock()

        # groups
        self.all_sprites = CameraGroup()
        self.block_group = pygame.sprite.Group()
        self.circle_group = pygame.sprite.Group()
        self.button_group = pygame.sprite.Group()
        self.updates_group = pygame.sprite.Group()

        self.groups = {
            'all_group': self.all_sprites,
            'block_group': self.block_group,
            'circle_group': self.circle_group,
            'button_group': self.button_group,
            'updates_group': self.updates_group,
        }
        self.graphics = {
            'player': {folder: import_folder(f'../graphics/player/{folder}') for folder in list(walk('../graphics/player'))[0][1]},
            'bird' : import_folder(f'../graphics/fly'),
            'trail' : import_folder(f'../graphics/trail_effect'),
            'leaves': import_folder(f'../graphics/leaves'),
            'balloons': import_folder(f'../graphics/balloons'),
            'equations': pygame.image.load('../graphics/miscellaneous/equations.png').convert_alpha(),
            'cliff': pygame.image.load('../tiled/cliff_edge.png').convert_alpha(),
            'chalkboard': pygame.image.load('../graphics/miscellaneous/chalkboard.png').convert_alpha(),
            'correct': pygame.image.load('../graphics/miscellaneous/correct.png').convert_alpha(),
            'wrong' :  pygame.image.load('../graphics/miscellaneous/wrong.png').convert_alpha(),
            'ground':  pygame.image.load('../tiled/ground.png').convert_alpha(),
            'home': pygame.image.load('../graphics/miscellaneous/home.png').convert_alpha(),
            'ball': pygame.image.load('../graphics/miscellaneous/baseball2.png').convert_alpha(),
            'puddle': pygame.image.load('../graphics/miscellaneous/puddle.png').convert_alpha(),
            'slope': pygame.image.load('../tiled/slope2.png').convert_alpha(),
            'knowns':pygame.image.load('../graphics/miscellaneous/knowns2.png'),
            'sky': pygame.image.load('../graphics/miscellaneous/sky.png')

        }
        self.all_states = {
            'title': Title(self.groups),
            'levelselect': LevelSelect(self.groups),
            'level1': Level1(self.groups, self.graphics),
            'level2': Level2(self.groups, self.graphics),
            'level3': Level3(self.groups, self.graphics),
            'level4': Level4(self.groups, self.graphics),
            'level5': Level5(self.groups, self.graphics),
            'level6': Level6(self.groups, self.graphics),
            'level7': Level7(self.groups, self.graphics),
            'level8': Level8(self.groups, self.graphics),
            'level9': Level9(self.groups, self.graphics),
            'level10': Level10(self.groups, self.graphics)
        }
        self.home_button = Button(self.groups,(WIDTH - 50, 50), image=self.graphics['home'])
        self.home_button.remove([self.all_sprites, self.block_group])


        self.state = ['title', False]   # [game state, change game state]
        for each in self.all_states.values():
            each.state = self.state

        self.current_state = self.all_states[self.state[0]]
        for sprite in self.current_state.sprites:
            sprite[0].add(sprite[1])
    def change_state(self):
        if self.home_button.clicked and self.state[0] != 'title':
            self.state[0] = 'title'
            self.state[1] = True
            self.home_button.clicked = False
            self.all_sprites.remove(self.home_button)
        if self.state[1]:
            self.current_state = self.all_states[self.state[0]]
            [sprite.kill() for sprite in self.all_sprites]
            [sprite.kill() for sprite in self.block_group]
            [sprite[0].add(sprite[1]) for sprite in self.current_state.sprites]

            self.all_sprites.add(self.home_button) if self.state[0] != 'title' else None
            self.all_sprites.enable_clouds = False
            if hasattr(self.current_state, 'reinitialize'):
                self.current_state.reinitialize()
            self.all_sprites.player[0] = None
            self.state[1] = False
    def run(self):
        while True:
            dt = self.clock.tick(80) / 1000

            self.display_surface.fill('white')

            self.current_state.dt = dt
            self.current_state.run(dt)
            self.change_state()

            pygame.display.update()

if '__main__':
    instance = Main()
    instance.run()
