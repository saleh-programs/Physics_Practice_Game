import math
import numbers
import random
import re
import time
import threading
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
load_dotenv()
api_key = os.getenv("API_KEY")

import pygame.draw

from objects import *
from functions import *
from timer import *
from settings import *
from random import randint
import sys
from Transition import *

class Title():
    def __init__(self, groups):
        self.groups = groups
        self.all_sprites = groups['all_group']
        self.updates_group = groups['updates_group']
        self.state = None
        self.start_button = None

        self.createTitleScreen()

        self.sprites = store_sprites(self.all_sprites)
    def createTitleScreen(self):
        title = Block(self.groups, (WIDTH *.5, HEIGHT * .33), 500, 200).blitText("Kinematics", 70)
        for i in range(randint(25,30)):
            pos = (randint(0,WIDTH),randint(0,HEIGHT))
            if not title.rect.collidepoint(pos):
                Circle(self.groups, pos, randint(20, 50))

        # Create start button
        self.start_button = Button(self.groups, (WIDTH * .5,HEIGHT * .66), 300,100).blitText("Enter Level Select",30)
    def eventLoop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.start_button.rect.collidepoint(pygame.mouse.get_pos()):
                    self.state[0] = 'levelselect'
                    self.state[1] = 1
    def run(self,dt):
        self.eventLoop()
        self.updates_group.update(dt)
        self.all_sprites.update(dt)
        self.all_sprites.draw(dt)
class LevelSelect():
    def __init__(self, groups):
        self.block_group = groups['block_group']
        self.button_group = groups['button_group']
        self.all_sprites = groups['all_group']
        self.updates_group = groups['updates_group']
        self.groups = groups
        self.state = None
        self.display_surface = pygame.display.get_surface()

        self.createLevelSelect()

        self.sprites = store_sprites(self.all_sprites)
    def createLevelSelect(self):
        columns = 3
        rows = 4
        horizontal_margin = 350
        vertical_margin = 30

        grid_width = WIDTH - horizontal_margin*2
        grid_height = HEIGHT - vertical_margin*2

        level_dimensions = vector(grid_width/columns,grid_height/rows)
        level = 0
        for i in range(rows-1):
            for j in range(columns):
                level += 1
                pos = vector(horizontal_margin + j * level_dimensions.x, vertical_margin + i*level_dimensions.y) + vector(level_dimensions.x/2,level_dimensions.y/2)
                width = level_dimensions.x / 2
                height = level_dimensions.y - 50
                button = Button(self.groups, pos, width, height)
                button.level = level
                button.blitText(f'{level}',70)
        pos = vector(WIDTH / 2, HEIGHT - (level_dimensions.y - 52))
        width = level_dimensions.x / 2
        height = level_dimensions.y - 50
        button = Button(self.groups, pos, width, height)
        button.level = 10
        button.blitText(f'{button.level}', 70)

        for i in range(randint(25,30)):
            pos = (randint(0,WIDTH),randint(0,HEIGHT))
            collisions = [1 for each in self.block_group if each.rect.collidepoint(pos)]
            if not collisions:
                Circle(self.groups, pos, randint(5, int(vertical_margin / 1.5)))
    def eventLoop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                level_block = [sprite for sprite in self.button_group if sprite.rect.collidepoint(pygame.mouse.get_pos())]
                if level_block:
                    self.state[0] = f'level{level_block[0].level}'
                    self.state[1] = True
    def run(self, dt):
        self.eventLoop()
        # updates
        self.updates_group.update(dt)
        self.all_sprites.update(dt)
        self.all_sprites.draw(dt)
class Level_General():
    def __init__(self, groups, graphics, actions):
        self.all_sprites = groups['all_group']
        self.block_group = groups['block_group']
        self.button_group = groups['button_group']
        self.updates_group = groups['updates_group']
        self.groups = groups
        self.graphics = graphics
        self.display_surface = pygame.display.get_surface()
        self.state = None

        # Willow
        self.willow = Player(self.groups, (0,0), self.graphics['player'],'camera')

        # Question
        self.question = Text(self.groups, 40, (0,0), 500)
        self.solved_willow = ProblemSolver()

        # Answer
        self.submissions = []
        self.correctAnswers = []
        self.user_input_box = TextBox(self.groups,(0,0),150,50)

        # Story Manager
        self.actions = actions
        self.manager = storyManager(self.actions)

        # Surfaces
        self.chalkboard = General(self.all_sprites, self.graphics['chalkboard'], (0,0),'camera')
        self.chalkboard.place_image(vector(WIDTH * .33, HEIGHT + 500))
        self.equations = ToggleImage(self.groups, (0,0),self.graphics['equations'])
        self.knowns = ToggleImage(self.groups, (0,0), self.graphics['knowns'],always_visible=None, linked_text=Text(self.groups, 15, (0,0), 300,animate=False,color="#565656",align='topleft'))
        self.ground_image = General(self.all_sprites,self.graphics['ground'],(WIDTH/2,HEIGHT),z='block')
        self.ground_platform = General([], pygame.Surface((self.ground_image.rect.width, self.ground_image.rect.height-25)),(WIDTH / 2, HEIGHT),z='scale')


        # Other
        self.saved_text = []
        self.camera = CameraDrone((WIDTH/2,HEIGHT/2))
        self.transition = Transition()


        # Save initialized sprites for repeated use
        self.sprites = store_sprites(self.all_sprites)
    def reinitialize(self):
        # Willow
        self.willow.lock_input = True
        self.willow.gravity = 4
        self.willow.direction = vector()
        self.willow.orientation = 'right'
        self.willow.speed = 400

        # Question
        self.solved_willow.clear()

        # Answer
        self.submissions = []
        self.correctAnswers = []
        self.user_input_box.blitText("")

        # Story manager
        self.manager.reset()

        # Surfaces
        self.equations.place_image(vector(5,5))
        self.knowns.place_image(vector(500,5))
        self.knowns.change_body("")
        self.ground_image.rect.center, self.ground_image.draw = vector(WIDTH / 2, HEIGHT), 'fixed'
        self.ground_platform.rect.center, self.ground_platform.draw = vector(WIDTH / 2,HEIGHT), 'fixed'

        # Miscellaneous
        self.saved_text = []
        self.camera.pos = vector(WIDTH / 2,HEIGHT / 2)
        self.all_sprites.enable_clouds = True
        self.transition.reset_transition()
    def clear_sprites(self):
        self.all_sprites.add(self.ground_image)
        self.all_sprites.add(self.ground_platform)
        self.all_sprites.scale_world(1) if self.all_sprites.scale != 1 else None

        # Kill sprites and make clouds
        for sprite in self.all_sprites:
            if not isinstance(sprite,Button):
                sprite.kill()
        self.all_sprites.create_clouds()
class Level1(Level_General):
    def __init__(self, groups, graphics):
        self.actions = [
            (self.sequence1, 1000),
            (self.sequence2, 6000),
            (self.sequence3, 11000),
            (self.sequence4, 2000),
            (self.sequence5, 1000),
            (self.sequence6, 1500),
            (self.sequence7, 500),
            (self.sequence8, 500),
            (self.sequence9, 500),
            (self.sequence10, 2000),
            (self.sequence11, 500),
            (self.sequence12, 500)
        ]

        # Variables
        self.cliffHeight = None

        # Surfaces
        self.cliff = None

        super().__init__(groups,graphics, self.actions)
    def reinitialize(self):
        super().reinitialize()

        # Player
        self.willow.place_player(vector(WIDTH / 2, HEIGHT / 2))

        # Question
        self.question.pos = (WIDTH * .20, HEIGHT * .66)
        self.cliffHeight = randint(1100, 10000)

        # Surfaces
        self.chalkboard.place_image(vector(WIDTH * .33, HEIGHT + 500))
        self.cliff = MovingTerrainHandler(self.groups, self.graphics['cliff'], (WIDTH, 0), 'up',overlap=50)

        super().clear_sprites()
    def sequence1(self):
        if not self.manager.called:
            self.all_sprites.add(self.willow, self.equations, self.knowns, self.ground_image)
            self.block_group.add(self.ground_platform)
            self.saved_text.extend([
                Text(self.groups, 40, (WIDTH / 2, 100),600).add_text("This is Willow."),
            ])
        self.manager.ready = True
    def sequence2(self):
        if not self.manager.called:
            self.saved_text.extend([
                Text(self.groups, 40, self.saved_text[0].pos + vector(0,200),600).add_text("Willow has volunteered to assist us today with learning one of the most important branches of physics, Kinematics!")
            ])
        self.manager.ready = True
    def sequence3(self):
        if not self.manager.called:
            [text.kill() for text in self.saved_text]
            self.saved_text.extend([
                Text(self.groups, 40, (WIDTH / 2, 250),600).add_text("You'll be asked 3 questions concerning his situation on each level. Type your answers, and press enter to submit. Questions are randomized, good luck!"),
                Text(self.groups, 20, self.equations.rect.topright + vector(-200,100),300).add_text("You can find the equations and given info here!")
            ])
        self.manager.ready = True
    def sequence4(self):
        if not self.manager.called:
            [text.kill() for text in self.saved_text]
            self.saved_text.extend([
                Text(self.groups, 40, (WIDTH/2, HEIGHT / 3),600).add_text("Ready to get started?")
            ])
        self.manager.ready = True
    def sequence5(self):
        if not self.manager.called:
            Button(self.groups, (WIDTH / 2, 460), 300, 100).blitText("Play", 30)
        button = [True for button in self.button_group if button.clicked]
        if button:
            button_platform = [block for block in self.block_group if (block in self.button_group)][0]
            self.all_sprites.remove(self.ground_image)
            Leaves.KillAnimation(self.all_sprites, button_platform, self.graphics['leaves'])
            Leaves.KillAnimation(self.all_sprites, self.ground_platform, self.graphics['leaves'])
            self.manager.ready = True
    def sequence6(self):
        if not self.manager.called:
            self.saved_text.extend([
                Text(self.groups, 30, (WIDTH / 2, HEIGHT / 2), 600).add_text("He signed a consent form.")
            ])
        self.manager.ready = True
    def sequence7(self):
        if not self.manager.called:
            [text.kill() for text in self.saved_text]
            self.all_sprites.add(self.cliff,self.cliff.terrains[0], self.question, self.user_input_box)
            self.all_sprites.player[0], self.all_sprites.player_offset = self.willow, vector(-300,0)  # set camera
            self.question.add_text(
                f"Willow has fallen off a {self.cliffHeight} m cliff, starting from rest. How long in seconds does he have to grow wings?")
            self.knowns.change_body(f"Cliff Height = {self.cliffHeight} m /skip a = -9.81 m/s\u00B2 /skip v0y = 0 m/s")
            self.solved_willow.v0 = 0
            self.solved_willow.a = -9.81
            self.solved_willow.y0 = 0
            self.solved_willow.yf = -self.cliffHeight
            self.solved_willow.find_t()
            self.correctAnswers.append(str(round(self.solved_willow.t, 2)))

        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)
    def sequence8(self):
        if not self.manager.called:
            self.all_sprites.add(self.question, self.user_input_box)

            self.question.add_text(
                f"In the event that he fails to grow wings, what will be his final velocity at the bottom of the cliff?")
            self.solved_willow.find_vf()
            self.correctAnswers.append(str(round(self.solved_willow.vf,2)))

        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)
    def sequence9(self):
        if not self.manager.called:
            self.all_sprites.add(self.question, self.user_input_box)

            self.question.add_text(
                f"Warming up to multiple dimensions. What value is equal to Willow's initial velocity, final velocity, and final position in the x direction if we set x = 0 m to be his initial position?")
            self.correctAnswers.append("0")
        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)
    def sequence10(self):
        if not self.manager.called:
            self.all_sprites.player[0], self.all_sprites.player_offset = None, vector() # Turn off camera
            self.willow.place_player(self.willow.pos + self.all_sprites.store_offset)
            self.cliff.speed.y /= 6

        if ((self.willow.pos.y > HEIGHT + 260) and self.willow in self.all_sprites):
            self.all_sprites.remove(self.willow)
            self.all_sprites.shake_effect()
            self.willow.place_player(vector(WIDTH/1.3,self.chalkboard.rect.top))
            self.manager.ready = True
    def sequence11(self):
        if not self.manager.called:
            self.all_sprites.add(self.willow, self.chalkboard,self.ground_image)
            self.block_group.add(self.ground_platform)
            self.all_sprites.player[0], self.all_sprites.player_offset, self.all_sprites.store_offset = self.camera, vector(), vector()

            self.ground_image.rect.center, self.ground_image.draw = vector(WIDTH/2,self.chalkboard.pos.y + 500), 'camera'
            self.ground_platform.rect.center, self.ground_platform.draw = vector(WIDTH/2,self.chalkboard.pos.y + 500), 'camera'

            self.cliff.speed, self.cliff.draw = vector(0,0), 'camera'
            for each in self.all_sprites:
                if isinstance(each, MovingTerrain):
                    each.draw = 'camera'

        camera_speed = (HEIGHT / 2 - (self.willow.pos.y + self.all_sprites.store_offset.y - 150))
        self.camera.pos.y -= camera_speed * self.dt
        if abs(self.willow.pos.y + self.all_sprites.store_offset.y - 200) < HEIGHT / 2:
            self.manager.purge = True
    def sequence12(self):
        if not self.manager.called:
            correct = [
                (float(self.correctAnswers[0])- 1) < float(self.submissions[0]) < (float(self.correctAnswers[0]) + 1),
                (float(self.correctAnswers[1])- 1) < float(self.submissions[1]) < (float(self.correctAnswers[1]) + 1),
                (int(self.correctAnswers[2])) == int(self.submissions[2])
            ]

            line1 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,65), 22,"Answer 1: " + self.submissions[0],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,95), 22, "Correct: " + self.correctAnswers[0],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[0] else self.graphics['wrong'],line1.rect.midleft + vector(-40,15), draw = 'camera')

            line2 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,140), 22,  "Answer 2: " + self.submissions[1],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140, 170), 22, "Correct: " + self.correctAnswers[1],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[1] else self.graphics['wrong'],line2.rect.midleft + vector(-40,15), draw = 'camera')

            line3 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,215), 22,  "Answer 3: " + self.submissions[2],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,245), 22,  "Correct: " + self.correctAnswers[2],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[2] else self.graphics['wrong'],line3.rect.midleft + vector(-40,15), draw = 'camera')
    def eventLoop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN and self.user_input_box in self.all_sprites:
                invalid = self.user_input_box.inputValidation(event)
                if not invalid and event.key == pygame.K_RETURN:
                    self.submissions.append(self.user_input_box.text)
                    Leaves.KillAnimation(self.all_sprites, self.user_input_box, self.graphics['leaves'])
                    Leaves.KillAnimation(self.all_sprites, self.question, self.graphics['leaves'])
                    self.user_input_box.blitText("")
                    self.manager.ready = True
    def run(self,dt):
        self.eventLoop()
        if pygame.key.get_pressed()[pygame.K_SPACE]:
            self.manager.progress_Timer.active = False
        self.manager.update()

        # updates
        self.updates_group.update(dt)
        self.all_sprites.update(dt)
        self.all_sprites.draw(dt)
class Level2(Level_General):
    def __init__(self, groups, graphics):
        self.actions = [
            (self.sequence1, 2000),
            (self.sequence2,6000),
            (self.sequence3,8000),
            (self.sequence4,2000),
            (self.sequence5, 0),
            (self.sequence6,1500),
            (self.sequence7,2000),
            (self.sequence8,500),
            (self.sequence9,500),
            (self.sequence10,500),
            (self.sequence11,500),
            (self.sequence12,500),
            (self.sequence13,500)]

        # Enemy
        self.enemy = Player(groups, (0,0), graphics['player'])

        # Variables
        self.cliffHeight = None
        self.v0x = None

        super().__init__(groups,graphics, self.actions)
    def reinitialize(self):
        super().reinitialize()
        # Player
        self.willow.place_player(vector(WIDTH - 370, HEIGHT/2))
        self.willow.orientation = 'left'

        # Enemy
        self.enemy.place_player((vector(WIDTH + 50, HEIGHT / 2)))
        self.enemy.direction = vector(-1, 0)
        self.enemy.orientation = 'left'
        self.enemy.lock_input = True

        # Question
        self.question.pos = (WIDTH * .20, HEIGHT * .66)
        self.cliffHeight = randint(1100, 10000)
        self.v0x = randint(-55,-15)

        # Surfaces
        self.ground_image.place_image(vector(WIDTH + 300,HEIGHT))
        self.ground_platform.place_image(vector(WIDTH + 300,HEIGHT))

        super().clear_sprites()
    def sequence1(self):
        if not self.manager.called:
            self.all_sprites.add(self.willow, self.equations, self.ground_image, self.knowns)
            self.block_group.add(self.ground_platform)
            self.saved_text.extend([
                Text(self.groups, 40, (400, 200),600).add_text("Willow please calm down, the cliff was in the agreement you signed and your safety has always been a priority")
            ])
        pygame.draw.rect(self.display_surface,'red',self.ground_platform,2)
        self.manager.ready = True
    def sequence2(self):
        if not self.manager.called:
            self.saved_text.extend([
                Text(self.groups, 60, self.willow.pos + vector(0,-100),600, color = "blue").add_text("I FELL THOUSANDS OF METERS!!")
            ])
        self.manager.ready = True
    def sequence3(self):
        if not self.manager.called:
            [text.kill() for text in self.saved_text]
            self.saved_text.extend([
                Text(self.groups, 40, (400, 200), 60).add_text("..."),
                Text(self.groups, 40,  self.willow.pos + vector(0,-100), 600, color="blue").add_text("I'm taking my $20 Amazon gift card and I'm getting out of here.")
            ])
        self.manager.ready = True
    def sequence4(self):
        if not self.manager.called:
            [text.kill() for text in self.saved_text]
            self.saved_text.extend([
                Text(self.groups, 40, (400, 200), 600).add_text("I'm afraid I can't let you do that. We still have 9 more levels.")
            ])
        self.manager.ready = True
    def sequence5(self):
        if not self.manager.called:
            self.all_sprites.add(self.enemy)
            self.saved_text.extend([
                Text(self.groups, 40,  self.willow.pos + vector(0,-100), 600, color="blue").add_text("Fine, I guess I can stay.")
            ])
        if self.enemy.rect.colliderect(self.willow.rect):
            self.enemy.direction.x = 0
            self.willow.direction.x = -1
            self.manager.ready = True
    def sequence6(self):
        if not self.manager.called:
            [text.kill() for text in self.saved_text]
            self.saved_text.clear()
            self.saved_text.extend([
                Text(self.groups, 60,  self.willow.pos + vector(0,-100), 600, speed = 300,color = 'blue').add_text("WHA- NOT COOL!")
            ])
        self.saved_text[0].pos = vector(self.willow.pos.x,self.willow.pos.y - 200)

        self.manager.ready = True
    def sequence7(self):
        if not self.manager.called:
            [text.kill() for text in self.saved_text]
            self.saved_text.extend([
                Text(self.groups, 40, (400, 200), 400).add_text("Time for kinematics in 2 dimensions!")
            ])
        self.manager.ready = True
    def sequence8(self):
        if not self.manager.called:
            [text.kill() for text in self.saved_text]
            [block.kill() for block in self.block_group]
            self.all_sprites.remove(self.enemy, self.ground_image)
            self.all_sprites.add(self.question, self.user_input_box)
            self.all_sprites.player[0], self.all_sprites.player_offset = self.willow, vector(-300,0)  # set camera

            self.question.add_text(
                f"Willow has fallen off a {self.cliffHeight} meter cliff, starting from vertical rest and a horizontal velocity of {self.v0x} m/s. How long will it take him to be x = -200 m away from the cliff?"
            )
            self.knowns.change_body(f"Cliff Height = {self.cliffHeight} m /skip v0y = 0 m/s /skip v0x = {self.v0x} m/s")
            self.solved_willow.t = round(-200 / self.v0x, 2)
            self.correctAnswers.append(str(self.solved_willow.t))

        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)
    def sequence9(self):
        if not self.manager.called:
            self.all_sprites.add(self.question, self.user_input_box)
            self.question.add_text(
                f"What will the magnitude of the TOTAL velocity be at x = -200 meters away from the cliff?")
            self.solved_willow.v0 = 0
            self.solved_willow.y0 = 0
            self.solved_willow.a = -9.81
            self.solved_willow.find_vf()
            total_velocity = round(math.sqrt(self.solved_willow.vf**2 + self.v0x**2), 2)
            self.correctAnswers.append(str(total_velocity))

        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)
    def sequence10(self):
        if not self.manager.called:
            self.all_sprites.add(self.question, self.user_input_box)
            self.question.add_text(f"How many meters has Willow traversed in the vertical direction at x = -200 meters?")
            self.solved_willow.find_yf()
            self.correctAnswers.append(str(round(self.solved_willow.yf, 2)))
        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)
    def sequence11(self):
        if not self.manager.called:
            self.all_sprites.player[0], self.all_sprites.player_offset = None, vector() # Turn off camera
            self.willow.place_player(self.willow.pos + self.all_sprites.store_offset)

        if ((self.willow.pos.y > HEIGHT + 260) and self.willow in self.all_sprites):
            self.all_sprites.remove(self.willow)
            self.willow.direction.x = 0
            self.all_sprites.shake_effect()
            self.willow.place_player(vector(WIDTH/1.3,self.chalkboard.rect.top))
            self.manager.ready = True
    def sequence12(self):
        if not self.manager.called:
            self.all_sprites.add(self.willow, self.chalkboard, self.ground_image)
            self.block_group.add(self.ground_platform)
            self.all_sprites.player[0], self.all_sprites.player_offset, self.all_sprites.store_offset = self.camera, vector(), vector()

            self.ground_image.rect.center, self.ground_image.draw = vector(WIDTH / 2,self.chalkboard.pos.y + 500), 'camera'
            self.ground_platform.rect.center, self.ground_platform.draw = vector(WIDTH / 2,self.chalkboard.pos.y + 500), 'camera'

        camera_speed = (HEIGHT / 2 - (self.willow.pos.y + self.all_sprites.store_offset.y - 150))
        self.camera.pos.y -= camera_speed * self.dt
        if abs(self.willow.pos.y + self.all_sprites.store_offset.y - 200) < HEIGHT / 2:
            self.manager.purge = True
    def sequence13(self):
        if not self.manager.called:
            correct = [
                (float(self.correctAnswers[0])- 1) < float(self.submissions[0]) < (float(self.correctAnswers[0]) + 1),
                (float(self.correctAnswers[1])- 1) < float(self.submissions[1]) < (float(self.correctAnswers[1]) + 1),
                (float(self.correctAnswers[2])- 1) < float(self.submissions[2]) < (float(self.correctAnswers[2]) + 1),
            ]

            line1 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,65), 22,"Answer 1: " + self.submissions[0],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,95), 22, "Correct: " + self.correctAnswers[0],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[0] else self.graphics['wrong'],line1.rect.midleft + vector(-40,15), draw = 'camera')

            line2 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,140), 22,  "Answer 2: " + self.submissions[1],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140, 170), 22, "Correct: " + self.correctAnswers[1],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[1] else self.graphics['wrong'],line2.rect.midleft + vector(-40,15), draw = 'camera')

            line3 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,215), 22,  "Answer 3: " + self.submissions[2],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,245), 22,  "Correct: " + self.correctAnswers[2],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[2] else self.graphics['wrong'],line3.rect.midleft + vector(-40,15), draw = 'camera')
    def eventLoop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN and len(self.user_input_box.groups()) != 0:
                invalid = self.user_input_box.inputValidation(event)
                if not invalid and event.key == pygame.K_RETURN:
                    self.submissions.append(self.user_input_box.text)
                    Leaves.KillAnimation(self.all_sprites, self.user_input_box, self.graphics['leaves'])
                    Leaves.KillAnimation(self.all_sprites, self.question, self.graphics['leaves'])
                    self.user_input_box.blitText("")
                    self.manager.ready = True
    def run(self,dt):
        self.eventLoop()
        if pygame.key.get_pressed()[pygame.K_SPACE]:
            self.manager.progress_Timer.active = False
        self.manager.update()
        # updates
        self.updates_group.update(dt)
        self.all_sprites.update(dt)
        self.all_sprites.draw(dt)
class Level3(Level_General):
    def __init__(self, groups, graphics):

        self.actions = [(self.sequence1, 4000),
                        (self.sequence2, 6000),
                        (self.sequence3, 0),
                        (self.sequence4, 0),
                        (self.sequence5, 0),
                        (self.sequence6, 500),
                        (self.sequence7, 500),
                        (self.sequence8, 500)]

        # Variables
        self.cliffHeight = None
        self.balloon_quantity = None
        self.balloons_popped = None
        self.balloon_acceleration = None

        # Surfaces
        self.cliff = None

        super().__init__(groups, graphics, self.actions)
    def reinitialize(self):
        super().reinitialize()

        self.willow.place_player(vector(WIDTH - 770, -10))
        self.willow.gravity = .5

        # Question
        self.question.pos = (WIDTH * .20, HEIGHT * .66)
        self.balloon_quantity = randint(15,25)
        self.balloon_acceleration = round(randint(5, 30) / 100, 2)
        self.balloons_popped = randint(5,9)
        self.cliffHeight = randint(1100, 10000)

        # Surfaces
        self.chalkboard.place_image(vector(WIDTH / 3, HEIGHT + 500))
        self.cliff = MovingTerrainHandler(self.groups, self.graphics['cliff'], (WIDTH, 0), 'up',overlap=50)
        self.cliff.speed.y = -500

        super().clear_sprites()
    def sequence1(self):
        if not self.manager.called:
            self.all_sprites.add(self.willow, self.equations, self.knowns)
            Block(self.groups,(WIDTH + 300,HEIGHT), WIDTH,100,self.graphics['ground'])
            Balloon.create_balloons(self.all_sprites,self.graphics['balloons'],self.willow, self.balloon_quantity)

            self.saved_text.extend([
                Text(self.groups, 40, self.willow.pos + vector(0,-100),600, color = 'blue').add_text("WHEEEEEEEE!!!!")
            ])
        self.saved_text[0].pos = vector(self.willow.pos.x, self.willow.pos.y - 100)
        self.manager.ready = True
    def sequence2(self):
        if not self.manager.called:
            self.saved_text.extend([
                Text(self.groups, 40, (500, 300),600).add_text("We gave him some balloons as an apology. He's cool now.")
            ])
        self.manager.ready = True
    def sequence3(self):
        if not self.manager.called:
            [text.kill() for text in self.saved_text]
            [block.kill() for block in self.block_group]
            self.block_group.add(self.cliff.terrains[0])
            self.all_sprites.add(self.cliff,self.cliff.terrains[0], self.question, self.user_input_box)
            self.all_sprites.player[0], self.all_sprites.player_offset = self.willow, vector(-300,0)  # set camera
            self.question.add_text(
                f"Willow is {self.cliffHeight} meters above the ground, descending straight down with {self.balloon_quantity} balloons in hand. Each balloon counters earth's downward acceleration (a=-9.81) with a = +{self.balloon_acceleration} m/s\u00B2. What is his vertical acceleration?"
            )
            self.knowns.change_body(f"Cliff Height = {self.cliffHeight} m /skip Initial # of Balloons = {self.balloon_quantity} /skip Balloon Acceleration = +{self.balloon_acceleration} m/s\u00B2 /skip v0y = 0 m/s")
            self.correctAnswers.append(str(round(-9.81 + (self.balloon_quantity * self.balloon_acceleration),2)))
        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)

    def sequence4(self):
        if not self.manager.called:
            self.all_sprites.add(self.question, self.user_input_box)
            Balloon.pop_balloons(self.all_sprites, self.balloons_popped, self.willow)

            self.question.add_text(
                f"Oh no, {self.balloons_popped} out of his {self.balloon_quantity} balloons popped! Assuming this event occurred at the height of his descent, how long will it take him to land on the ground?"
            )
            self.knowns.change_body(f"Cliff Height = {self.cliffHeight} m /skip Initial # of Balloons = {self.balloon_quantity} /skip # of Popped Balloons = {self.balloons_popped} /skip Balloon Acceleration = +{self.balloon_acceleration} m/s\u00B2 /skip v0y = 0 m/s")
            self.balloon_quantity -= self.balloons_popped
            self.solved_willow.a = -9.81 + (self.balloon_quantity * self.balloon_acceleration)
            self.solved_willow.y0 = 0
            self.solved_willow.yf = -self.cliffHeight
            self.solved_willow.v0 = 0
            self.solved_willow.find_t()
            self.correctAnswers.append(str(round(self.solved_willow.t, 2)))
        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)
    def sequence5(self):
        if not self.manager.called:
            self.all_sprites.add(self.question, self.user_input_box)
            self.question.add_text(f"What will be the magnitude of his velocity upon landing?")
            self.solved_willow.find_vf()
            self.correctAnswers.append(str(round(self.solved_willow.vf, 2)))
        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)
    def sequence6(self):
        if not self.manager.called:
            self.all_sprites.player[0], self.all_sprites.player_offset = None, vector() # Turn off camera
            self.willow.place_player(self.willow.pos + self.all_sprites.store_offset)

            for sprite in self.all_sprites:
                if isinstance(sprite, Balloon):
                    sprite.pos += self.all_sprites.store_offset
            self.cliff.speed.y /= 3

        if ((self.willow.pos.y > HEIGHT + 260) and self.willow in self.all_sprites):
            self.all_sprites.remove(self.willow)
            self.willow.direction.x = 0
            self.all_sprites.shake_effect()
            self.willow.place_player(vector(WIDTH/1.3,self.chalkboard.rect.top))
            self.manager.ready = True
    def sequence7(self):
        if not self.manager.called:
            self.all_sprites.add(self.willow, self.chalkboard, self.ground_image)
            self.block_group.add(self.ground_platform)
            self.all_sprites.player[0], self.all_sprites.player_offset, self.all_sprites.store_offset = self.camera, vector(), vector()

            self.ground_image.rect.center, self.ground_image.draw = vector(WIDTH / 2,self.chalkboard.pos.y + 500), 'camera'
            self.ground_platform.rect.center, self.ground_platform.draw = vector(WIDTH / 2,self.chalkboard.pos.y + 500), 'camera'

            self.cliff.speed, self.cliff.draw = vector(0,0), 'camera'
            for each in self.all_sprites:
                if isinstance(each, MovingTerrain):
                    each.draw = 'camera'

        camera_speed = (HEIGHT / 2 - (self.willow.pos.y + self.all_sprites.store_offset.y - 150))
        self.camera.pos.y -= camera_speed * self.dt
        if abs(self.willow.pos.y + self.all_sprites.store_offset.y - 200) < HEIGHT / 2:
            self.manager.purge = True
    def sequence8(self):
        if not self.manager.called:
            correct = [
                (float(self.correctAnswers[0])- 1) < float(self.submissions[0]) < (float(self.correctAnswers[0]) + 1),
                (float(self.correctAnswers[1])- 1) < float(self.submissions[1]) < (float(self.correctAnswers[1]) + 1),
                (float(self.correctAnswers[2])- 1) < float(self.submissions[2]) < (float(self.correctAnswers[2]) + 1),
            ]

            line1 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,65), 22,"Answer 1: " + self.submissions[0],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,95), 22, "Correct: " + self.correctAnswers[0],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[0] else self.graphics['wrong'],line1.rect.midleft + vector(-40,15), draw = 'camera')

            line2 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,140), 22,  "Answer 2: " + self.submissions[1],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140, 170), 22, "Correct: " + self.correctAnswers[1],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[1] else self.graphics['wrong'],line2.rect.midleft + vector(-40,15), draw = 'camera')

            line3 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,215), 22,  "Answer 3: " + self.submissions[2],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,245), 22,  "Correct: " + self.correctAnswers[2],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[2] else self.graphics['wrong'],line3.rect.midleft + vector(-40,15), draw = 'camera')
    def eventLoop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN and len(self.user_input_box.groups()) != 0:
                invalid = self.user_input_box.inputValidation(event)
                if not invalid and event.key == pygame.K_RETURN:
                    self.submissions.append(self.user_input_box.text)
                    Leaves.KillAnimation(self.all_sprites, self.user_input_box, self.graphics['leaves'])
                    Leaves.KillAnimation(self.all_sprites, self.question, self.graphics['leaves'])
                    self.user_input_box.blitText("")
                    self.manager.ready = True
    def run(self,dt):
        self.eventLoop()
        if pygame.key.get_pressed()[pygame.K_SPACE]:
            self.manager.progress_Timer.active = False
        self.manager.update()
        # updates
        self.updates_group.update(dt)
        self.all_sprites.update(dt)
        self.all_sprites.draw(dt)
class Level4(Level_General):
    def __init__(self, groups, graphics):
        self.actions = [(self.sequence1, 4000),
                        (self.sequence2,6000),
                        (self.sequence3,0),
                        (self.sequence4,0),
                        (self.sequence5,0),
                        (self.sequence6,0),
                        (self.sequence7,500),
                        (self.sequence8,500)]

        # Variables
        self.cliffHeight = None
        self.balloon_quantity = None
        self.balloons_popped = None
        self.balloon_acceleration = None
        self.time_falling = None
        self.distance_from_cliff = None
        self.time_final = None

        super().__init__(groups, graphics, self.actions)
    def reinitialize(self):
        super().reinitialize()
        # Willow
        self.willow.place_player(vector(WIDTH+500, HEIGHT/2))
        self.willow.direction = vector(-1.5, 0)
        self.willow.gravity = .5
        self.willow.orientation = "left"

        # Question
        self.question.pos = (WIDTH * .20, HEIGHT * .66)
        self.cliffHeight = randint(1100, 10000)
        self.balloon_quantity = randint(15,25)
        self.balloon_acceleration = round(randint(5, 30) / 100, 2)
        self.balloons_popped = randint(5, 9)
        self.time_falling = randint(5,20)
        self.distance_from_cliff = randint(500,3500)

        # find time final
        self.solved_willow.feed_knowns(y0=0, yf=-self.cliffHeight, v0=0, a=-9.81 + self.balloon_acceleration * self.balloon_quantity)
        self.solved_willow.find_t()
        self.time_final = round(self.solved_willow.t + randint(-3,3))
        self.solved_willow.clear()

        # Surfaces
        self.ground_image.place_image(vector(WIDTH - 300, HEIGHT))
        self.ground_platform.place_image(vector(WIDTH - 300, HEIGHT))

        super().clear_sprites()
    def sequence1(self):
        if not self.manager.called:
            self.all_sprites.add(self.willow, self.equations, self.ground_image, self.knowns)
            self.block_group.add(self.ground_platform)
            Balloon.create_balloons(self.all_sprites,self.graphics['balloons'],self.willow, self.balloon_quantity)
            self.saved_text.extend([
                Text(self.groups, 40, (400, 200),600, color = 'blue').add_text("WHEEEEEEEE!!!!")
            ])
        self.saved_text[0].pos = vector(self.willow.pos.x, self.willow.pos.y - 100)
        self.manager.ready = True
    def sequence2(self):
        if not self.manager.called:
            self.saved_text.extend([
                Text(self.groups, 40, (500, 300), 600).add_text("Really likes those balloons...")
            ])
        self.saved_text[0].pos = vector(self.willow.pos.x, self.willow.pos.y - 100)

        self.manager.ready = True
    def sequence3(self):
        if not self.manager.called:
            self.ground_image.kill()
            self.ground_platform.kill()
            [text.kill() for text in self.saved_text]
            for sprite in self.block_group:
                if isinstance(sprite,Block) and not isinstance(sprite, Button):
                    sprite.kill()
            self.all_sprites.player[0], self.all_sprites.player_offset = self.willow, vector(-300,0)  # set camera
            self.all_sprites.add(self.question, self.user_input_box)

            self.question.add_text(
                f"Willow has just run off of a {self.cliffHeight} meter cliff with {self.balloon_quantity} balloons attached, with each one adding a vertical acceleration of +{self.balloon_acceleration}. After falling for {self.time_falling} seconds, how far above the ground is he?"
            )
            self.knowns.change_body(f"Cliff Height = {self.cliffHeight} m /skip Initial # of Balloons = {self.balloon_quantity} /skip Balloon Acceleration = +{self.balloon_acceleration} m/s\u00B2 /skip v0y = 0 m/s /skip Time Falling = {self.time_falling} s")

            self.solved_willow.feed_knowns(a=-9.81 + self.balloon_acceleration * self.balloon_quantity, t=self.time_falling,y0=0,v0=0)
            self.solved_willow.find_yf()
            self.correctAnswers.append(str(round(self.cliffHeight + self.solved_willow.yf,2)))

        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)
    def sequence4(self):
        if not self.manager.called:
            self.all_sprites.add(self.question, self.user_input_box)
            self.question.add_text(f"After falling for {self.time_falling} seconds, he is {self.distance_from_cliff} meters from the cliff, horizontally. What is his horizontal velocity?")
            self.knowns.change_body(f"Cliff Height = {self.cliffHeight} m /skip Horizontal Cliff Distance = {self.distance_from_cliff} m /skip Initial # of Balloons = {self.balloon_quantity} /skip Balloon Acceleration = +{self.balloon_acceleration} m/s\u00B2 /skip v0y = 0 m/s /skip Time Falling = {self.time_falling} s")
            self.correctAnswers.append(str(round(-self.distance_from_cliff / self.solved_willow.t, 2)))
        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)
    def sequence5(self):
        if not self.manager.called:
            self.all_sprites.add(self.question, self.user_input_box)
            self.question.add_text(f"Has he hit the ground by {self.time_final} seconds? Type -1 for no, and 1 for yes.")
            self.knowns.change_body(f"Cliff Height = {self.cliffHeight} m /skip Horizontal Cliff Distance = {self.distance_from_cliff} m /skip Initial # of Balloons = {self.balloon_quantity} /skip Balloon Acceleration = +{self.balloon_acceleration} m/s\u00B2 /skip v0y = 0 m/s /skip t = {self.time_final} s")

            self.solved_willow.clear()
            self.solved_willow.feed_knowns(y0=0, v0=0,a=-9.81 + self.balloon_acceleration * self.balloon_quantity)

            self.solved_willow.t = self.time_final
            self.solved_willow.find_yf()
            self.correctAnswers.append('1' if self.solved_willow.yf < -self.cliffHeight else '-1')
        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)
    def sequence6(self):
        if not self.manager.called:
            self.all_sprites.player[0], self.all_sprites.player_offset = None, vector() # Turn off camera
            for sprite in self.all_sprites:
                if isinstance(sprite, Balloon):
                    sprite.pos += self.all_sprites.store_offset
            self.willow.place_player(self.willow.pos + self.all_sprites.store_offset)

        if ((self.willow.pos.y > HEIGHT + 260) and self.willow in self.all_sprites):
            self.all_sprites.remove(self.willow)
            self.all_sprites.shake_effect()
            self.willow.place_player(vector(WIDTH/1.3,self.chalkboard.rect.top))
            self.willow.direction.x = 0
            self.manager.ready = True
    def sequence7(self):
        if not self.manager.called:
            self.all_sprites.add(self.willow, self.chalkboard, self.ground_image)
            self.block_group.add(self.ground_platform)
            self.all_sprites.player[0], self.all_sprites.player_offset, self.all_sprites.store_offset = self.camera, vector(), vector()

            self.ground_image.rect.center, self.ground_image.draw = vector(WIDTH / 2,self.chalkboard.pos.y + 500), 'camera'
            self.ground_platform.rect.center, self.ground_platform.draw = vector(WIDTH / 2,self.chalkboard.pos.y + 500), 'camera'

        camera_speed = (HEIGHT / 2 - (self.willow.pos.y + self.all_sprites.store_offset.y - 150))
        self.camera.pos.y -= camera_speed * self.dt
        if abs(self.willow.pos.y + self.all_sprites.store_offset.y - 200) < HEIGHT / 2:
            self.manager.purge = True
    def sequence8(self):
        if not self.manager.called:
            correct = [
                (float(self.correctAnswers[0])- 1) < float(self.submissions[0]) < (float(self.correctAnswers[0]) + 1),
                (float(self.correctAnswers[1])- 1) < float(self.submissions[1]) < (float(self.correctAnswers[1]) + 1),
                (int(self.correctAnswers[2]) == int(self.submissions[2])),
            ]

            line1 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,65), 22,"Answer 1: " + self.submissions[0],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,95), 22, "Correct: " + self.correctAnswers[0],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[0] else self.graphics['wrong'],line1.rect.midleft + vector(-40,15), draw = 'camera')

            line2 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,140), 22,  "Answer 2: " + self.submissions[1],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140, 170), 22, "Correct: " + self.correctAnswers[1],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[1] else self.graphics['wrong'],line2.rect.midleft + vector(-40,15), draw = 'camera')

            line3 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,215), 22,  "Answer 3: " + self.submissions[2],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,245), 22,  "Correct: " + self.correctAnswers[2],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[2] else self.graphics['wrong'],line3.rect.midleft + vector(-40,15), draw = 'camera')
    def eventLoop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN and len(self.user_input_box.groups()) != 0:
                invalid = self.user_input_box.inputValidation(event)
                if not invalid and event.key == pygame.K_RETURN:
                    self.submissions.append(self.user_input_box.text)
                    Leaves.KillAnimation(self.all_sprites, self.user_input_box, self.graphics['leaves'])
                    Leaves.KillAnimation(self.all_sprites, self.question, self.graphics['leaves'])
                    self.user_input_box.blitText("")
                    self.manager.ready = True
    def run(self,dt):
        self.eventLoop()
        if pygame.key.get_pressed()[pygame.K_SPACE]:
            self.manager.progress_Timer.active = False
        self.manager.update()
        # updates
        self.updates_group.update(dt)
        self.all_sprites.update(dt)
        self.all_sprites.draw(dt)
class Level5(Level_General):
    def __init__(self, groups, graphics):
        self.actions = [
            (self.sequence1, 4000),
            (self.sequence2, 2000),
            (self.sequence3,0),
            (self.sequence4,0),
            (self.sequence5,0),
            (self.sequence6,0),
            (self.sequence7,0),
            (self.sequence8,500)]

        # Robber
        self.robber = Player(groups, (WIDTH / 2, HEIGHT / 2), graphics['player'], draw = 'camera')

        # Variables
        self.robber_vx = None
        self.willow_vx =  None
        self.distance_between = None
        self.proposed_meters = None

        # Surfaces
        self.ground = None

        super().__init__(groups, graphics, self.actions)
        # Changes
        self.question.width = 700
        self.chalkboard.place_image(vector(WIDTH / 3, HEIGHT * .4))

    def reinitialize(self):
        super().reinitialize()
        # Willow
        self.willow.place_player(vector(1000,HEIGHT/2))

        # Robber
        self.robber.place_player(vector(WIDTH - 300,HEIGHT/2))
        self.robber.direction = vector()
        self.robber.speed = 400
        self.robber.lock_input = True

        # Question
        self.question.pos = (WIDTH * .65, HEIGHT * .25)

        self.robber_vx = randint(50,90)
        self.willow_vx = self.robber_vx + randint(10,20)
        self.distance_between = randint(100,300)

        # finding proposed meters
        t_until_caught = self.distance_between / (self.willow_vx - self.robber_vx)
        distance_caught = t_until_caught * self.willow_vx
        self.proposed_meters = round(distance_caught + randint(-200,200))
        #

        # Surfaces
        self.ground = MovingTerrainHandler(self.groups, self.graphics['ground'], (WIDTH/2, HEIGHT), 'left',overlap=300,draw='camera')
        self.ground_platform = General([], pygame.Surface((WIDTH, HEIGHT-25)),(WIDTH / 2, HEIGHT+100))

        super().clear_sprites()
    def sequence1(self):
        if not self.manager.called:
            self.all_sprites.add(self.willow, self.robber, self.equations,self.ground,self.ground.terrains[0],self.knowns)
            self.block_group.add(self.ground_platform)
            self.willow.direction.x, self.robber.direction.x = 1, 1
            self.all_sprites.player[0], self.all_sprites.player_offset = self.robber, vector(-400,-150)
            self.saved_text.extend([
                Text(self.groups, 30, self.willow.pos + vector(0,-100),100,color='blue',draw='camera').add_text("GIVE ME BACK THE TI-84!")
            ])
        self.saved_text[0].pos = self.willow.pos + vector(0,-100)
        self.manager.ready = True
    def sequence2(self):
        if not self.manager.called:
            Leaves.KillAnimation(self.all_sprites,self.saved_text[0],self.graphics['leaves'])
            self.saved_text.clear()
            self.saved_text.extend([
                Text(self.groups, 30, self.robber.pos + vector(0,-100),100,color='maroon',draw='camera').add_text("Bro you can't even use it on the exam")
            ])
        self.saved_text[0].pos = self.robber.pos + vector(0,-100)
        self.manager.ready = True
    def sequence3(self):
        if not self.manager.called:
            self.all_sprites.add(self.question, self.user_input_box)
            Leaves.KillAnimation(self.all_sprites,self.saved_text[0],self.graphics['leaves'])
            self.saved_text.clear()
            self.question.add_text(
                f"Willow has just been robbed and is in hot pursuit of the evil doer, just {self.distance_between} meters behind. Willow is running at {self.willow_vx} m/s and the robber is running at {self.robber_vx} m/s.  Will Willow catch the robber by the time the robber has run {self.proposed_meters} meters? Type -1 for no and 1 for yes."
            )
            self.knowns.change_body(f"Distance Between = {self.distance_between} m /skip Willow vx = {self.willow_vx} m/s /skip Robber vx = {self.robber_vx} m/s /skip Robber runs {self.proposed_meters} m")

            t_UntilCaught = self.distance_between / (self.willow_vx - self.robber_vx)
            t_RobberDistance = ((self.proposed_meters -263) / self.robber_vx)
            self.correctAnswers.append('1' if t_RobberDistance >= t_UntilCaught else '-1')
        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)
    def sequence4(self):
        if not self.manager.called:
            self.all_sprites.add(self.question, self.user_input_box)
            self.question.add_text(f"What time t does Willow catch the robber?")
            t = self.distance_between / (self.willow_vx - self.robber_vx)
            self.correctAnswers.append(str(round(t,2)))
        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)
    def sequence5(self):
        if not self.manager.called:
            self.all_sprites.add(self.question, self.user_input_box)
            t_percentage = float((randint(10,100)/100) * float(self.correctAnswers[1]))
            self.question.add_text(f"What is the distance between them at {t_percentage} seconds?")
            xw = self.willow_vx * t_percentage
            xr = self.robber_vx * t_percentage + self.distance_between
            self.correctAnswers.append(str(round(xr - xw,2)))
        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)
    def sequence6(self):
        if not self.manager.called:
            if self.correctAnswers[0] == '1':
                self.all_sprites.shake_effect()
                self.willow.speed *= 1.5
                self.saved_text.extend([
                    Text(self.groups, 30, self.willow.pos + vector(0, -100), 400,speed=200, color='blue', draw='camera').add_text("RAAAAAGGHHHHHHHH")
                ])
                self.saved_text.extend([
                    Text(self.groups, 30, self.robber.pos + vector(0, -100), 400, speed=200, color='maroon', draw='camera').add_text("You don't understand I'm just in a bad place right- NOOOOOOO!!!")
                ])
            if self.correctAnswers[0] == '-1':
                self.robber.speed *= 1.8
                self.all_sprites.player[0], self.all_sprites.player_offset = self.willow, vector(100,-150)
                self.saved_text.extend([
                    Text(self.groups, 30, self.willow.pos + vector(0, -100),400, speed=200, color='blue', draw='camera').add_text("THIS ISN'T OVER!")
                ])
                self.saved_text.extend([
                    Text(self.groups, 30, self.willow.pos + vector(0, -100), 400, speed=200, color='maroon', draw='camera').add_text("Snooze ya lose buster!")
                ])
        self.saved_text[0].pos = self.willow.pos + vector(0,-200)
        self.saved_text[1].pos = self.robber.pos + vector(0,-100)
        if self.transition.dark:
            self.manager.purge = True
            return
        if self.correctAnswers[0] == '1':
            if self.willow.pos.distance_to(self.robber.pos) < 600:
                self.transition.active = True
        if self.correctAnswers[0] == '-1':
            if self.robber.rect.left + self.all_sprites.store_offset.x > WIDTH+200:
                self.all_sprites.remove(self.robber)
                self.saved_text[1].kill()
                self.transition.active = True
        self.transition.center = self.willow.pos.copy() + self.all_sprites.store_offset
    def sequence7(self):
        if not self.manager.called:
            self.all_sprites.add(self.chalkboard, self.ground_image)
            self.willow.direction.x = 0
            self.all_sprites.player[0], self.all_sprites.player_offset, self.all_sprites.store_offset = None, vector(), vector()

            self.ground_image.place_image(vector(WIDTH / 2, HEIGHT))
            self.ground_platform.place_image(vector(WIDTH / 2, HEIGHT + 100))
            self.ground_image.draw, self.ground_platform.draw = 'fixed', 'fixed'

            self.ground.kill()
            self.willow.place_player(vector(self.chalkboard.pos.x + 800, HEIGHT / 2))
            for sprite in self.all_sprites:
                if isinstance(sprite,MovingTerrain):
                    sprite.kill()
        self.manager.ready = True
    def sequence8(self):
        if not self.manager.called:
            correct = [
                (float(self.correctAnswers[0])- 1) < float(self.submissions[0]) < (float(self.correctAnswers[0]) + 1),
                (float(self.correctAnswers[1])- 1) < float(self.submissions[1]) < (float(self.correctAnswers[1]) + 1),
                (float(self.correctAnswers[2])- 1) < float(self.submissions[2]) < (float(self.correctAnswers[2]) + 1),
            ]

            line1 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,65), 22,"Answer 1: " + self.submissions[0],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,95), 22, "Correct: " + self.correctAnswers[0],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[0] else self.graphics['wrong'],line1.rect.midleft + vector(-40,15), draw = 'camera')

            line2 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,140), 22,  "Answer 2: " + self.submissions[1],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140, 170), 22, "Correct: " + self.correctAnswers[1],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[1] else self.graphics['wrong'],line2.rect.midleft + vector(-40,15), draw = 'camera')

            line3 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,215), 22,  "Answer 3: " + self.submissions[2],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,245), 22,  "Correct: " + self.correctAnswers[2],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[2] else self.graphics['wrong'],line3.rect.midleft + vector(-40,15), draw = 'camera')
    def eventLoop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN and len(self.user_input_box.groups()) != 0:
                invalid = self.user_input_box.inputValidation(event)
                if not invalid and event.key == pygame.K_RETURN:
                    self.submissions.append(self.user_input_box.text)
                    Leaves.KillAnimation(self.all_sprites, self.user_input_box, self.graphics['leaves'])
                    Leaves.KillAnimation(self.all_sprites, self.question, self.graphics['leaves'])
                    self.user_input_box.blitText("")
                    self.manager.ready = True
    def run(self,dt):
        self.eventLoop()
        self.ground_platform.place_image(vector(self.willow.pos.x + WIDTH/2,self.ground_platform.pos.y))

        if pygame.key.get_pressed()[pygame.K_SPACE]:
            self.manager.progress_Timer.active = False
        self.manager.update()

        # updates
        self.updates_group.update(dt)
        self.all_sprites.update(dt)
        self.all_sprites.draw(dt)
        self.transition.display(dt)
class Level6(Level_General):
    def __init__(self, groups, graphics):
        self.actions = [
            (self.sequence1, 4000),
            (self.sequence2, 8000),
            (self.sequence3, 0),
            (self.sequence4, 4000),
            (self.sequence5,4000),
            (self.sequence6,4000),
            (self.sequence7,500),
            (self.sequence8,500),
            (self.sequence9,500),
            (self.sequence10,1000),
            (self.sequence11,0),
            (self.sequence12,500)]

        # Robber
        self.robber = Player(groups, (WIDTH / 2, HEIGHT / 2), graphics['player'], draw = 'camera')
        self.solved_robber = ProblemSolver()

        # Variables
        self.willow_v =  None
        self.robber_v = None
        self.distance = None
        self.balloon_quantity = None
        self.balloon_acceleration = None
        self.balloons_popped = None

        super().__init__(groups, graphics, self.actions)
        # Changes
        self.chalkboard.place_image(vector(WIDTH / 3, HEIGHT * .4))

    def reinitialize(self):
        super().reinitialize()
        # Willow
        self.willow.place_player(vector(1000,HEIGHT/3.3))
        self.willow.drift_velocity = 1

        # Robber
        self.robber.place_player(vector(WIDTH,HEIGHT/1.3))
        self.robber.direction = vector()
        self.robber.speed = 400
        self.robber.lock_input = True
        self.robber.drift_velocity = 1

        # Question
        self.solved_robber.clear()

        self.question.pos = (WIDTH * .20, HEIGHT * .66)
        self.robber_v = vector(randint(50,90),randint(50,90))
        self.willow_v = vector(self.robber_v.x + randint(10,20),self.robber_v.y + randint(10,20))
        self.distance = vector(randint(100,300),0)
        self.balloon_quantity = randint(15,25)
        self.balloon_acceleration = round(randint(5, 30) / 100, 2)
        self.balloons_popped = randint(5,10)

        # find self.distance.y
        t_until_caughtX = self.distance.x / (self.willow_v.x - self.robber_v.x)
        t_until_caughtY = t_until_caughtX + randint(-2,2)
        self.distance.y = round(t_until_caughtY * (self.willow_v.y - self.robber_v.y))
        #
        super().clear_sprites()
    def sequence1(self):
        if not self.manager.called:
            self.saved_text.extend([
                Text(self.groups, 50, (WIDTH/2, 200),400).add_text("Willow got robbed again.")
            ])
        self.manager.ready = True
    def sequence2(self):
        if not self.manager.called:
            self.saved_text.extend([
                Text(self.groups, 50, (WIDTH/2, HEIGHT/1.5),800,150).add_text("Sigh. He's been chasing this guy for like 4 days now......airborne. Let's just turn it into a problem we can solve or something.")
            ])
        self.manager.ready = True
    def sequence3(self):
        if not self.manager.called:
            self.all_sprites.add(self.willow, self.robber, self.equations, self.knowns)
            [Leaves.KillAnimation(self.all_sprites,text,self.graphics['leaves']) for text in self.saved_text]
            self.saved_text.clear()
            self.willow.drift_velocity, self.robber.drift_velocity = 1,1
            self.willow.direction, self.robber.direction = vector(1,1), vector(1,1)
            self.all_sprites.player[0], self.all_sprites.player_offset = self.camera, vector()
            self.camera.pos = (self.robber.pos + vector(-500,-250)) + vector(1500,750)
            Balloon.create_balloons(self.all_sprites,self.graphics['balloons'],self.willow,self.balloon_quantity)
            Balloon.create_balloons(self.all_sprites,self.graphics['balloons'],self.robber,self.balloon_quantity)
        difference = (self.robber.pos + vector(-500,-250)) - (self.camera.pos)
        camera_direction = difference.normalize()
        self.camera.pos += camera_direction * (1400*((difference.magnitude()+100)/1670)) * self.dt + (self.willow.pos - self.willow.old_pos)
        if (self.camera.pos.distance_to(self.robber.pos + vector(-500,-250)) < 10):
            self.all_sprites.player[0], self.all_sprites.player_offset = self.robber, vector(-500,-250)
            self.manager.purge = True
    def sequence4(self):
        if not self.manager.called:
            self.saved_text.extend([
                Text(self.groups, 30, self.willow.pos + vector(0,-100),200,color='blue',draw='camera').add_text("What is your OBSESSION with my calculator?!")
            ])
        self.saved_text[0].pos = self.willow.pos + vector(0,-100)
        self.manager.ready = True
    def sequence5(self):
        if not self.manager.called:
            self.saved_text.extend([
                Text(self.groups, 30, self.robber.pos + vector(0,-100),200,color='maroon',draw='camera').add_text("TI-84 is expensive these days man!! BACK OFF!")
            ])
        self.saved_text[0].pos = self.willow.pos + vector(0,-100)
        self.saved_text[1].pos = self.robber.pos + vector(0,-100)

        self.manager.ready = True
    def sequence6(self):
        if not self.manager.called:
            [text.kill() for text in self.saved_text]

            self.saved_text.clear()
            self.saved_text.extend([
                Text(self.groups, 30, self.robber.pos + vector(0,-100),100,color='blue',draw='camera').add_text("NO YOU CAN'T JUST TAKE MY THINGS")
            ])
        self.saved_text[0].pos = self.willow.pos + vector(0,-100)
        self.manager.ready = True
    def sequence7(self):
        if not self.manager.called:
            self.all_sprites.add(self.question, self.user_input_box)
            [text.kill() for text in self.saved_text]
            self.saved_text.clear()

            self.question.change_fontsize(30)
            self.question.add_text(
                f'''Willow and the robber each have {self.balloon_quantity} balloons attached to them, each adding a = +{self.balloon_acceleration} m/s^2.
                    Willow's horizontal and vertical velocity is {self.willow_v.x} and {self.willow_v.y} m/s, respectively. The robber's horizontal and vertical
                    velocity is {self.robber_v.x} and {self.robber_v.y} m/s, respectively. Willow is just {self.distance.x} meters behind him and {self.distance.y} 
                    meters above him. How long until he catches up with the robber in the x direction?'''
            )
            self.knowns.change_body(f"Initial # of Balloons = {self.balloon_quantity} /skip Balloon Acceleration = +{self.balloon_acceleration} m/s\u00B2 /skip Willow v0x = {self.willow_v.x} m/s /skip Willow v0y = {self.willow_v.y} m/s /skip Robber v0x = {self.robber_v.x} m/s /skip Robber v0y = {self.robber_v.y} m/s /skip Horizontal Distance = {self.distance.x} m /skip Vertical Distance = {self.distance.y} m")
            t = round(self.distance.x / (self.willow_v.x - self.robber_v.x), 2)
            self.correctAnswers.append(str(t))
        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)
        if self.willow.pos.x + self.all_sprites.store_offset.x < WIDTH/2:
            self.all_sprites.player_offset.x -= 100 * self.dt
    def sequence8(self):
        if not self.manager.called:
            self.all_sprites.add(self.question, self.user_input_box)
            self.question.change_fontsize(40)
            self.question.add_text(
                f"Will Willow catch him in the x direction before the y direction?"
            )
            tx = float(self.correctAnswers[0])
            ty = round(self.distance.y / (self.willow_v.y - self.robber_v.y), 2)
            self.correctAnswers.append('1' if tx < ty else '-1')

        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)
    def sequence9(self):
        if not self.manager.called:
            self.all_sprites.add(self.question, self.user_input_box)
            Balloon.pop_balloons(self.all_sprites, self.balloons_popped, self.willow)
            self.question.add_text(
                f"How long until Willow catches up with the robber in the y direction, if {self.balloons_popped} of his balloons pop?"
            )
            self.knowns.change_body(f"Initial # of Balloons (Willow) = {self.balloon_quantity} /skip Initial # of Balloons (Robber) = {self.balloon_quantity}  /skip # of Popped Balloons (Willow) = {self.balloons_popped} /skip Balloon Acceleration = +{self.balloon_acceleration} m/s\u00B2 /skip Willow v0x = {self.willow_v.x} m/s /skip Willow v0y = {self.willow_v.y} m/s /skip Robber v0x = {self.robber_v.x} m/s /skip Robber v0y = {self.robber_v.y} m/s /skip Horizontal Distance = {self.distance.x} m /skip Vertical Distance = {self.distance.y} m")

            aw = -9.81 + ((self.balloon_quantity - self.balloons_popped) * self.balloon_acceleration)
            ar = -9.81 + (self.balloon_quantity * self.balloon_acceleration)

            A = (aw - ar) / 2
            B = self.willow_v.y - self.robber_v.y
            C = self.distance.y
            quadraticplus = (-B + math.sqrt(B**2 - 4*A*C)) / 2*A
            quadraticminus = (-B - math.sqrt(B**2 - 4*A*C)) / 2*A
            t = round(max(quadraticplus, quadraticminus),2)
            self.correctAnswers.append(str(t))

        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)
    def sequence10(self):
        if not self.manager.called:
            self.saved_text.extend([
                Text(self.groups, 30, self.willow.pos + vector(0, -100), 200, color='blue', draw='camera').add_text("I DEFY NEWTONIAN PHYSICS"),
                Text(self.groups, 50, self.willow.pos + vector(0, -150), 200, color='maroon', draw='camera').add_text("AGGGGGHHHHHHH")
            ])
            self.transition.active = True
            self.transition.speed = 1100
        direction = (self.robber.pos - self.willow.pos).normalize()
        self.willow.pos += direction * 400 * self.dt

        self.saved_text[0].pos = self.willow.pos + vector(0,-100)
        self.saved_text[1].pos = self.robber.pos + vector(0,-150)
        self.transition.center = self.willow.pos.copy() + self.all_sprites.store_offset

        if self.transition.dark:
            self.manager.purge = True
            self.transition.speed = 900
            return
    def sequence11(self):
        if not self.manager.called:
            self.all_sprites.add(self.chalkboard,self.ground_image)
            self.block_group.add(self.ground_platform)
            self.willow.direction = vector()
            self.all_sprites.player[0], self.all_sprites.player_offset, self.all_sprites.store_offset = None, vector(), vector()

            self.ground_image.place_image(vector(WIDTH / 2,HEIGHT))
            self.ground_platform.place_image(vector(WIDTH / 2,HEIGHT))

            self.willow.place_player(vector(WIDTH/1.3,self.ground_platform.rect.top))
            for sprite in self.all_sprites:
                if isinstance(sprite,Balloon):
                    sprite.pos += (self.willow.pos - sprite.pos)

        self.manager.ready = True
    def sequence12(self):
        if not self.manager.called:
            correct = [
                (float(self.correctAnswers[0])- 1) < float(self.submissions[0]) < (float(self.correctAnswers[0]) + 1),
                (float(self.correctAnswers[1])- 1) < float(self.submissions[1]) < (float(self.correctAnswers[1]) + 1),
                (float(self.correctAnswers[2])- 1) < float(self.submissions[2]) < (float(self.correctAnswers[2]) + 1),
            ]

            line1 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,65), 22,"Answer 1: " + self.submissions[0],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,95), 22, "Correct: " + self.correctAnswers[0],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[0] else self.graphics['wrong'],line1.rect.midleft + vector(-40,15), draw = 'camera')

            line2 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,140), 22,  "Answer 2: " + self.submissions[1],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140, 170), 22, "Correct: " + self.correctAnswers[1],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[1] else self.graphics['wrong'],line2.rect.midleft + vector(-40,15), draw = 'camera')

            line3 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,215), 22,  "Answer 3: " + self.submissions[2],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,245), 22,  "Correct: " + self.correctAnswers[2],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[2] else self.graphics['wrong'],line3.rect.midleft + vector(-40,15), draw = 'camera')
    def eventLoop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN and len(self.user_input_box.groups()) != 0:
                invalid = self.user_input_box.inputValidation(event)
                if not invalid and event.key == pygame.K_RETURN:
                    self.submissions.append(self.user_input_box.text)
                    Leaves.KillAnimation(self.all_sprites, self.user_input_box, self.graphics['leaves'])
                    Leaves.KillAnimation(self.all_sprites, self.question, self.graphics['leaves'])
                    self.user_input_box.blitText("")
                    self.manager.ready = True
    def run(self,dt):
        self.eventLoop()
        if pygame.key.get_pressed()[pygame.K_SPACE]:
            self.manager.progress_Timer.active = False
        self.manager.update()
        # updates
        self.updates_group.update(dt)
        self.all_sprites.update(dt)
        self.all_sprites.draw(dt)
        self.transition.display(dt)
class Level7(Level_General):
    def __init__(self, groups, graphics):
        self.actions = [
            (self.sequence1, 1000),
            (self.sequence2,2000),
            (self.sequence3, 4000),
            (self.sequence4,2000),
            (self.sequence5,2000),
            (self.sequence6, 1000),
            (self.sequence7,1500),
             (self.sequence8,500)]
        self.ball = None

        self.robber = Player(groups, (WIDTH / 2, HEIGHT / 2), graphics['player'], draw = 'camera')

        # Variables
        self.puddle_distance = None
        self.robber_distance = None
        self.v0x = None
        self.block_height = None
        self.throw_timer = None

        super().__init__(groups,graphics, self.actions)
        # Changes
        self.chalkboard.place_image(vector(WIDTH / 3, HEIGHT * .4))
        self.question.width = 700
    def reinitialize(self):
        super().reinitialize()
        self.willow.place_player(vector(WIDTH/2.5,HEIGHT*.58))

        self.robber.place_player(vector(WIDTH+200,100))
        self.robber.direction = vector()
        self.robber.gravity = 4
        self.robber.orientation = 'left'
        self.robber.lock_input = True

        self.ball = Ball(self.groups, self.willow.pos, self.graphics['ball'])


        # Question
        self.question.pos = vector(WIDTH * .65, HEIGHT * .25)
        self.question.width = 700

        self.v0x = randint(10,30)
        self.puddle_distance = randint(150,250)
        self.robber_distance = self.puddle_distance + randint(30,70)

        # Find block height
        t = (self.robber_distance / self.v0x) / 2
        v0y = round((t * 9.81), 2)
        self.block_height = round(v0y*t - (9.81 * t**2)/2) + randint(-10,10)
        #

        # Other
        self.throw_timer = Timer(3000)
        super().clear_sprites()
    def sequence1(self):
        if not self.manager.called:
            self.all_sprites.add(self.willow, self.equations, self.question, self.user_input_box, self.ground_image, self.knowns)
            self.block_group.add(self.ground_platform)
            General(self.all_sprites,pygame.transform.scale_by(self.graphics['puddle'],4),(WIDTH - 500, self.ground_platform.rect.top+3),z='leaves')
            self.question.change_fontsize(30)
            self.question.add_text(
                f'''Willow is trying to throw a ball into the puddle on the other side of the floating land mass.
                    Treat the puddle as a point {self.puddle_distance} meters away at ground level. Say Willow is throwing the ball from ground level.
                    What initial vertical velocity does Willow need to throw the ball to ensure it hits the puddle if he insists on 
                    a initial horizontal velocity of {self.v0x} m/s?'''
            )
            self.knowns.change_body(f"Puddle Distance = {self.puddle_distance} m /skip v0x = {self.v0x} m/s /skip Ball is thrown from ground level")
            t = self.puddle_distance / self.v0x
            v0y = round((t * 9.81) / 2, 2)
            self.correctAnswers.append(str(v0y))
        if not self.throw_timer.active:
            self.throw_ball()
            self.throw_timer.activate()
        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)
    def sequence2(self):
        if not self.manager.called:
            self.all_sprites.add(self.robber, self.question, self.user_input_box)
            Balloon.create_balloons(self.all_sprites,self.graphics['balloons'],self.robber,3)
            self.robber.direction.x = -1
            self.robber.gravity = 1
            self.saved_text.extend([
                Text(self.groups, 30, (WIDTH/2, 200),400,color='blue').add_text("Seriously?"),
                Text(self.groups, 30, (WIDTH / 2, 200), 400, color='maroon').add_text("Seriously. Give it now."),
            ])
            self.question.add_text(
                f'''The robber has come for Willow's expensive TI-84 calculator despite numerous failed attempts!
                    Treat the robber as a point {self.robber_distance} meters away at ground level. What initial vertical velocity does 
                    Willow need to throw the ball to ensure it hits the puddle if he insists on 
                    a initial horizontal velocity of {self.v0x} m/s? '''
            )
            self.knowns.change_body(f"Robber Distance = {self.robber_distance} m /skip v0x = {self.v0x} m/s /skip Ball is thrown from ground level")
            t = self.robber_distance / self.v0x
            v0y = round((t * 9.81) / 2, 2)
            self.correctAnswers.append(str(v0y))

        self.saved_text[0].pos = self.willow.pos + vector(0,-100)
        self.saved_text[1].pos = self.robber.pos + vector(0,-100)
        if (self.robber.status == 'run'):
            self.robber.direction = vector()
        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)
    def sequence3(self):
        if not self.manager.called:
            [text.kill() for text in self.saved_text]
            self.saved_text.clear()
            Block(self.groups,(self.willow.pos.x + (self.robber.pos.x-self.willow.pos.x)/2,0),100,745)
            self.saved_text.extend([
                Text(self.groups, 30, (WIDTH/2, 200),400,color='blue').add_text("Is that thing blocking my shot?"),
                Text(self.groups, 30, (WIDTH / 2, 200), 400, color='maroon').add_text("Yes hahaha. I calculated the exact placement needed with my TI-83. Not sure if it's right though I need the TI-84 to check."),
            ])

        self.saved_text[0].pos = self.willow.pos + vector(0,-100)
        self.saved_text[1].pos = self.robber.pos + vector(0,-100)
        if (self.robber.status == 'run'):
            self.robber.direction = vector()
        if (self.robber.direction == vector()):
            self.manager.ready = True
    def sequence4(self):
        if not self.manager.called:
            self.all_sprites.add(self.question, self.user_input_box)
            [text.kill() for text in self.saved_text]
            self.saved_text.clear()
            self.question.add_text(
                f'''The robber has placed a large block with its bottom {self.block_height} meters up potentially shielding him from Willow's blows!
                    If Willow still insists on a initial horizontal velocity of {self.v0x} m/s,
                    is it still possible to hit the robber? If so, type 1.
                    Otherwise, enter how far up in meters to move the block so that it is out of the way.'''
            )
            self.knowns.change_body(f"Robber Distance = {self.robber_distance} m /skip v0x = {self.v0x} m/s /skip Block Height = {self.block_height} m /skip Ball is thrown from ground level")

            v0y = float(self.correctAnswers[1])
            t = (self.robber_distance / self.v0x) / 2
            yf = v0y*t - (9.81 * t**2 / 2)
            self.correctAnswers.append(str('1' if yf < self.block_height else round(yf - self.block_height,2)))

        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)
    def sequence5(self):
        if not self.manager.called:
            [text.kill() for text in self.saved_text]
            self.saved_text.clear()
            self.saved_text.extend([
                Text(self.groups, 30, (WIDTH/2, 200),400,speed=200,color='blue').add_text("This is called the 0 vertical velocity attack."),
                Text(self.groups, 30, (WIDTH / 2, 200), 400, color='maroon').add_text("Wha-?")
            ])
            self.throw_ball(True)
        self.saved_text[0].pos = self.willow.pos + vector(0,-100)
        self.saved_text[1].pos = self.robber.pos + vector(0,-100)

        if self.ball.rect.colliderect(self.robber.rect):
            self.robber.direction.y = -3
            self.robber.direction.x = 3
            self.ball.gravity = 5
            self.ball.direction.x = -.5
            self.manager.ready = True
    def sequence6(self):
        if not self.manager.called:
            [text.kill() for text in self.saved_text]
            self.saved_text.clear()
            self.transition.active = True
        self.transition.center = self.willow.pos.copy() + self.all_sprites.store_offset
        if self.transition.dark:
            self.manager.purge = True
            self.all_sprites.remove(self.robber)
            for sprite in self.all_sprites:
                [block.kill() for block in self.block_group]
                if isinstance(sprite,Balloon):
                    sprite.kill()
    def sequence7(self):
        if not self.manager.called:
            self.all_sprites.add(self.chalkboard, self.ground_image)
            self.block_group.add(self.ground_platform)
            self.ground_platform.rect.y += 15
            self.willow.place_player(self.ground_image.rect.topright + vector(-300,50))
        self.manager.ready = True
    def sequence8(self):
        if not self.manager.called:
            correct = [
                (float(self.correctAnswers[0])- 1) < float(self.submissions[0]) < (float(self.correctAnswers[0]) + 1),
                (float(self.correctAnswers[1])- 1) < float(self.submissions[1]) < (float(self.correctAnswers[1]) + 1),
                (float(self.correctAnswers[2])- 1) < float(self.submissions[2]) < (float(self.correctAnswers[2]) + 1),
            ]

            line1 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,65), 22,"Answer 1: " + self.submissions[0],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,95), 22, "Correct: " + self.correctAnswers[0],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[0] else self.graphics['wrong'],line1.rect.midleft + vector(-40,15), draw = 'camera')

            line2 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,140), 22,  "Answer 2: " + self.submissions[1],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140, 170), 22, "Correct: " + self.correctAnswers[1],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[1] else self.graphics['wrong'],line2.rect.midleft + vector(-40,15), draw = 'camera')

            line3 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,215), 22,  "Answer 3: " + self.submissions[2],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,245), 22,  "Correct: " + self.correctAnswers[2],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[2] else self.graphics['wrong'],line3.rect.midleft + vector(-40,15), draw = 'camera')
    def eventLoop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN and len(self.user_input_box.groups()) != 0:
                invalid = self.user_input_box.inputValidation(event)
                if not invalid and event.key == pygame.K_RETURN:
                    self.submissions.append(self.user_input_box.text)
                    Leaves.KillAnimation(self.all_sprites, self.user_input_box, self.graphics['leaves'])
                    Leaves.KillAnimation(self.all_sprites, self.question, self.graphics['leaves'])
                    self.user_input_box.blitText("")
                    self.manager.ready = True
    def throw_ball(self,beam=False):
        self.willow.frame_index = 0
        self.willow.attack = True
        self.all_sprites.add(self.ball)
        self.ball.place_ball(vector(self.willow.rect.bottomright + vector(0,-12)))
        self.ball.direction.y = -2
        self.ball.direction.x = 10
        if beam:
            self.ball.place_ball(vector(self.willow.rect.bottomright + vector(0, -50)))
            self.ball.image = pygame.transform.scale_by(self.ball.asset,3)
            self.ball.direction = vector(15,0)
            self.ball.gravity = 0

    def run(self,dt):
        self.throw_timer.update()
        self.eventLoop()
        if pygame.key.get_pressed()[pygame.K_SPACE]:
            self.manager.progress_Timer.active = False
        self.manager.update()
        # updates
        self.updates_group.update(dt)
        self.all_sprites.update(dt)
        self.all_sprites.draw(dt)
        self.transition.display(dt)
class Level8(Level_General):
    def __init__(self, groups, graphics):
        self.actions = [
            (self.sequence1, 500),
            (self.sequence2,500),
            (self.sequence3,500),
            (self.sequence4,500),
            (self.sequence5, 1000),
            (self.sequence6,1500),
            (self.sequence7,500)]

        self.slope = None

        # Variables
        self.v = None
        self.distance = None
        self.balloon_quantity = None
        self.balloon_acceleration = None

        super().__init__(groups,graphics, self.actions)
        # Changes
        self.chalkboard.place_image(vector(WIDTH / 3, HEIGHT * .4))
    def reinitialize(self):
        super().reinitialize()
        self.willow.place_player(vector(WIDTH/2 - 240,HEIGHT/2 - 85))

        # Question
        self.v = randint(10,20)
        self.distance = vector(randint(20,30),0)
        self.balloon_quantity = randint(6,11)
        self.balloon_acceleration = round(randint(5, 30) / 100, 2)
        self.question.pos = vector(WIDTH * .6, HEIGHT * .3)
        self.question.change_fontsize(40)

        # find distance.y
        a = -9.81 + self.balloon_quantity * self.balloon_acceleration
        vx = round(self.v * math.cos(math.radians(30)),2)
        vy = round(self.v * math.sin(math.radians(30)), 2)
        t = self.distance.x / vx
        self.distance.y = round(-1*(-vy*t + (a * t**2)/2) + randint(-6,6))
        #

        # Surfaces
        self.equations.place_image(vector(WIDTH - 440, 5))
        self.slope = General(self.all_sprites, self.graphics['slope'],(WIDTH/2,HEIGHT/2))
        self.ground_platform.place_image(vector(WIDTH - 70, HEIGHT + 90))
        super().clear_sprites()
    def sequence1(self):
        if not self.manager.called:
            self.all_sprites.add(self.willow, self.slope, self.equations, self.question, self.user_input_box,self.knowns)
            self.block_group.add(self.ground_platform)
            Balloon.create_balloons(self.all_sprites,self.graphics['balloons'],self.willow,8)
            [text.kill() for text in self.saved_text]
            self.saved_text.clear()
            self.willow.gravity = 0
            self.question.change_fontsize(30)
            self.question.add_text(
                f'''Willow is frozen in time at the edge of a cliff and faces a large gap. His velocity
                    is exactly aligned with the direction 30 degrees above the horizontal
                    (the general slope of the cliff). He has {self.balloon_quantity} balloons attached, each giving an acceleration of
                     +{self.balloon_acceleration} m/s\u00B2. His total velocity is {self.v} m/s. The ground on the other side of
                    the gap is {self.distance.x} m ahead and {self.distance.y} m below. What is his horizontal velocity?'''
            )
            self.knowns.change_body(f"Angle of Incline = 30\u00B0 /skip # of Balloons = {self.balloon_quantity} /skip Balloon Acceleration = +{self.balloon_acceleration} m/s\u00B2 /skip Vertical Distance = {self.distance.y} m /skip Horizontal Distance = {self.distance.x} m /skip v = {self.v} m/s")
            v0x = round(self.v * math.cos(math.radians(30)),2)
            self.correctAnswers.append(str(v0x))
        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)
    def sequence2(self):
        if not self.manager.called:
            self.all_sprites.add( self.question, self.user_input_box)
            [text.kill() for text in self.saved_text]
            self.saved_text.clear()
            self.question.add_text(
                f'''What is his vertical velocity?'''
            )
            v0y = round(self.v * math.sin(math.radians(30)),2)
            self.correctAnswers.append(str(v0y))
        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)
    def sequence3(self):
        if not self.manager.called:
            self.all_sprites.add( self.question, self.user_input_box)
            [text.kill() for text in self.saved_text]
            self.saved_text.clear()
            self.question.add_text(
                f'''Will he make it to the other side?'''
            )
            a = -9.81 + self.balloon_quantity * self.balloon_acceleration
            vx = round(self.v * math.cos(math.radians(30)), 2)
            vy = round(self.v * math.sin(math.radians(30)), 2)
            t = self.distance.x / vx
            yf = -1*(-vy*t + (a * t**2)/2)

            self.correctAnswers.append('1' if yf <= self.distance.y else '-1')
        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)
    def sequence4(self):
        if not self.manager.called:
            choice = self.correctAnswers[2]
            if choice == '-1':
                self.willow.direction.x = 1
                self.willow.gravity = 4
            if choice == '1':
                self.willow.direction.x = 2
                self.willow.gravity = 3
        self.manager.ready = True
    def sequence5(self):
        if not self.manager.called:
            [text.kill() for text in self.saved_text]
            self.saved_text.clear()
            self.transition.active = True
        if self.transition.dark:
            self.manager.purge = True
            return
    def sequence6(self):
        if not self.manager.called:
            self.all_sprites.add(self.chalkboard, self.ground_image)
            self.block_group.add(self.ground_platform)
            self.slope.kill()
            self.willow.direction = vector()
            self.willow.gravity = 4
            self.ground_platform.place_image(vector(WIDTH /2, HEIGHT))
            self.willow.place_player(self.ground_image.rect.topright + vector(-300,50))
        self.manager.ready = True
    def sequence7(self):
        if not self.manager.called:
            correct = [
                (float(self.correctAnswers[0])- 1) < float(self.submissions[0]) < (float(self.correctAnswers[0]) + 1),
                (float(self.correctAnswers[1])- 1) < float(self.submissions[1]) < (float(self.correctAnswers[1]) + 1),
                (float(self.correctAnswers[2])- 1) < float(self.submissions[2]) < (float(self.correctAnswers[2]) + 1),
            ]

            line1 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,65), 22,"Answer 1: " + self.submissions[0],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,95), 22, "Correct: " + self.correctAnswers[0],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[0] else self.graphics['wrong'],line1.rect.midleft + vector(-40,15), draw = 'camera')

            line2 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,140), 22,  "Answer 2: " + self.submissions[1],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140, 170), 22, "Correct: " + self.correctAnswers[1],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[1] else self.graphics['wrong'],line2.rect.midleft + vector(-40,15), draw = 'camera')

            line3 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,215), 22,  "Answer 3: " + self.submissions[2],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,245), 22,  "Correct: " + self.correctAnswers[2],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[2] else self.graphics['wrong'],line3.rect.midleft + vector(-40,15), draw = 'camera')
    def eventLoop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN and len(self.user_input_box.groups()) != 0:
                invalid = self.user_input_box.inputValidation(event)
                if not invalid and event.key == pygame.K_RETURN:
                    self.submissions.append(self.user_input_box.text)
                    Leaves.KillAnimation(self.all_sprites, self.user_input_box, self.graphics['leaves'])
                    Leaves.KillAnimation(self.all_sprites, self.question, self.graphics['leaves'])
                    self.user_input_box.blitText("")
                    self.manager.ready = True
    def run(self,dt):
        self.eventLoop()
        if pygame.key.get_pressed()[pygame.K_SPACE]:
            self.manager.progress_Timer.active = False
        self.manager.update()
        # updates
        self.updates_group.update(dt)
        self.all_sprites.update(dt)
        self.all_sprites.draw(dt)
        self.transition.display(dt)
class Level9(Level_General):
    def __init__(self, groups, graphics):
        self.actions = [
            (self.sequence1, 3000),
            (self.sequence2,3000),
            (self.sequence3,3000),
            (self.sequence4,3000),
            (self.sequence5, 3000),
            (self.sequence6,1500),
            (self.sequence7,500),
            (self.sequence8,500),
            (self.sequence9,500),
            (self.sequence10,2000),
            (self.sequence11,0),
            (self.sequence12,500),
            (self.sequence13,500)]

        self.scale_by = 1
        self.offset = vector()

        # Variables
        self.jump_distance = None
        self.crouch_distance = None
        self.new_a = None

        super().__init__(groups,graphics, self.actions)
    def reinitialize(self):
        super().reinitialize()

        self.willow.place_player(vector(WIDTH/2, HEIGHT/2))

        # Question
        self.solved_willow.clear()
        self.question.pos = vector(WIDTH*.2, HEIGHT*.3)
        self.question.change_fontsize(40)
        self.jump_distance = randint(10,30)
        self.crouch_distance = .3 + round(random.random(),2)
        self.new_a = randint(10,20)

        # Surfaces
        self.chalkboard.place_image(vector(WIDTH / 3, HEIGHT + 510))
        self.equations.place_image(vector(WIDTH - 440, 5))
        self.ground_image.draw = 'camera'
        self.ground_platform.draw = 'camera'

        # Other
        self.scale_by = 1
        self.offset = vector()

        super().clear_sprites()
    def sequence1(self):
        if not self.manager.called:
            self.all_sprites.add(self.willow, self.equations, self.knowns,self.ground_platform,self.ground_image)#, self.ground_image,self.ground_platform)
            self.block_group.add(self.ground_platform)
            self.all_sprites.player[0] = self.willow
            self.saved_text.extend([
                Text(self.groups,35, (WIDTH/5, HEIGHT/3), 500).add_text("Let's take a closer look at our friend Willow here.")
            ])

        self.manager.ready = True
    def sequence2(self):
        if not self.manager.called:
            [text.kill() for text in self.saved_text]
            self.saved_text.clear()
            self.saved_text.extend([
                Text(self.groups,35, (WIDTH/5, HEIGHT/2), 500).add_text("...")
            ])
        if self.scale_by < 5:
            self.scale_by += self.dt * 1.5
            self.all_sprites.scale_world(self.scale_by)
        else:
            self.manager.ready = True
    def sequence3(self):
        if not self.manager.called:
            [text.kill() for text in self.saved_text]
            self.saved_text.clear()
            self.saved_text.extend([
                Text(self.groups,30, (WIDTH/2, HEIGHT/3.1), 500,color='blue').add_text("You're uncomfortably close.")
            ])
        self.manager.ready = True
    def sequence4(self):
        if not self.manager.called:
            [text.kill() for text in self.saved_text]
            self.saved_text.extend([
                Text(self.groups,30, (WIDTH/5, HEIGHT/3), 500).add_text("Pssssstt Willow. Do the thing now.")
            ])
        self.manager.ready = True
    def sequence5(self):
        if not self.manager.called:
            self.willow.lock_status = True
            self.willow.status = 'prejump'
            self.saved_text.extend([
                Text(self.groups,30, (WIDTH/2, HEIGHT/3.1), 500,color='blue').add_text("oh, right. sorry.")
            ])
        self.manager.ready = True
    def sequence6(self):
        if not self.manager.called:
            self.all_sprites.add(self.question, self.user_input_box)
            [text.kill() for text in self.saved_text]
            self.saved_text.clear()
            self.question.change_fontsize(30)
            self.question.add_text(f'''
            Ahem- Willow has moved into a crouched position by lowering his body {self.crouch_distance} meters. If he was to accelerate
            upwards from this position, what would be the vertical velocity required to lift him {self.jump_distance} meters in the air?''')
            self.knowns.change_body(f"Distance Stand to Crouch = {self.crouch_distance} m /skip Jump Distance = {self.jump_distance} m")
            v0y = round(math.sqrt(2 * 9.81 * self.jump_distance),2)
            self.correctAnswers.append(str(v0y))
        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)
    def sequence7(self):
        if not self.manager.called:
            self.all_sprites.add(self.question, self.user_input_box)
            self.question.add_text('''
            What was the acceleration getting from the crouched position to the standing position?''')
            a = round(float(self.correctAnswers[0])**2 / (2*self.crouch_distance),2)
            self.correctAnswers.append(str(a))
        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)
    def sequence8(self):
        if not self.manager.called:
            self.all_sprites.add(self.question, self.user_input_box)
            [text.kill() for text in self.saved_text]
            self.saved_text.clear()
            self.question.add_text(f'''
            How high up could he jump if his acceleration standing up was {self.new_a} m/s\u00B2?''')
            self.knowns.change_body(f"Distance Stand to Crouch = {self.crouch_distance} m /skip Original Jump Distance = {self.jump_distance} m /skip New Acceleration = {self.new_a} m/s\u00B2")

            vf = math.sqrt(2 * self.new_a * self.crouch_distance)
            yf = round(-vf**2 / (2 * -9.81),2)
            self.correctAnswers.append(str(yf))
        self.user_input_box.pos = self.question.rect.midbottom + vector(0, 30)
    def sequence9(self):
        if not self.manager.called:
            self.willow.lock_status = False
            self.willow.direction.y = -6
            self.all_sprites.player[0] = self.camera
            self.camera.pos = self.willow.pos.copy()
            self.transition.active = True

        if self.transition.dark:
            self.manager.purge = True
    def sequence10(self):
        if not self.manager.called:
            self.all_sprites.add(self.chalkboard)
            self.all_sprites.scale_world(self.scale_by)
            self.willow.place_player(vector(WIDTH/2,HEIGHT/2))
            self.saved_text.extend([
                Text(self.groups,30, self.willow.pos + vector(0,-200), 500,color='blue').add_text("DUDE BACK UP")
            ])
        self.manager.ready = True
    def sequence11(self):
        if not self.manager.called:
            [text.kill() for text in self.saved_text]
            self.saved_text.clear()
            self.all_sprites.player[0] = self.willow
        if self.scale_by > 1:
            self.scale_by -= self.dt * 2
            self.all_sprites.scale_world(self.scale_by)
        else:
            self.all_sprites.scale_world(1)
            self.manager.ready = True
        self.willow.place_player(self.ground_image.rect.topright + vector(-self.ground_image.rect.width*.2, 0))
        self.chalkboard.place_image(self.ground_image.rect.topleft + vector(.4* self.ground_image.rect.width,-self.chalkboard.rect.height/2+50))
    def sequence12(self):
        if not self.manager.called:
            self.all_sprites.player[0] = self.camera
            self.camera.pos = self.willow.pos.copy()
        self.camera.pos += (vector(WIDTH/2, HEIGHT/2) - self.camera.pos) * self.dt * 7
        if (self.camera.pos.distance_to(vector(WIDTH/2,HEIGHT/2)) < 3):
            self.manager.ready = True
    def sequence13(self):
        if not self.manager.called:
            correct = [
                (float(self.correctAnswers[0])- 1) < float(self.submissions[0]) < (float(self.correctAnswers[0]) + 1),
                (float(self.correctAnswers[1])- 1) < float(self.submissions[1]) < (float(self.correctAnswers[1]) + 1),
                (float(self.correctAnswers[2])- 1) < float(self.submissions[2]) < (float(self.correctAnswers[2]) + 1),
            ]

            line1 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,65), 22,"Answer 1: " + self.submissions[0],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,95), 22, "Correct: " + self.correctAnswers[0],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[0] else self.graphics['wrong'],line1.rect.midleft + vector(-40,15), draw = 'camera')

            line2 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,140), 22,  "Answer 2: " + self.submissions[1],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140, 170), 22, "Correct: " + self.correctAnswers[1],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[1] else self.graphics['wrong'],line2.rect.midleft + vector(-40,15), draw = 'camera')

            line3 = BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,215), 22,  "Answer 3: " + self.submissions[2],color = 'white', draw = 'camera')
            BasicText(self.groups, self.chalkboard.rect.topleft + vector(140,245), 22,  "Correct: " + self.correctAnswers[2],color = 'white', draw = 'camera')
            General(self.all_sprites, self.graphics['correct'] if correct[2] else self.graphics['wrong'],line3.rect.midleft + vector(-40,15), draw = 'camera')
    def eventLoop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN and len(self.user_input_box.groups()) != 0:
                invalid = self.user_input_box.inputValidation(event)
                if not invalid and event.key == pygame.K_RETURN:
                    self.submissions.append(self.user_input_box.text)
                    Leaves.KillAnimation(self.all_sprites, self.user_input_box, self.graphics['leaves'])
                    Leaves.KillAnimation(self.all_sprites, self.question, self.graphics['leaves'])
                    self.user_input_box.blitText("")
                    self.manager.ready = True
    def run(self,dt):
        self.eventLoop()
        if pygame.key.get_pressed()[pygame.K_SPACE]:
            self.manager.progress_Timer.active = False
        self.manager.update()
        # updates
        self.updates_group.update(dt)
        self.all_sprites.update(dt)
        self.all_sprites.draw(dt)
        self.transition.display(dt)
class Level10(Level_General):
    def __init__(self, groups, graphics):
        self.actions = [(self.sequence1, 3000), (self.sequence2,1000), (self.sequence3,1000),(self.sequence4,1000),(self.sequence5, 1000)]

        self.scale_by = 1
        self.offset = vector()

        self.AI_query = None
        self.willow_response = None
        self.chat_history = []

        super().__init__(groups,graphics, self.actions)

    def reinitialize(self):
        super().reinitialize()
        # Player / Enemy
        self.willow.place_player(vector(WIDTH/2 ,HEIGHT/2))
        self.willow_response = Text(self.groups, 25, (WIDTH/2,HEIGHT/2),600)
        self.chat_history = []

        # Other
        self.scale_by = 1
        self.offset = vector()
        self.AI_query = TextBoxPlus(self.groups,(0,0),500,28,margin=3)
        self.ground_image.draw, self.ground_platform.draw = 'camera','camera'

        super().clear_sprites()
    def sequence1(self):
        if not self.manager.called:
            self.all_sprites.add(self.willow, self.ground_image, self.ground_platform)
            self.block_group.add(self.ground_platform)
            self.saved_text.extend([
                Text(self.groups,35, (WIDTH/2, 0), 500,draw='camera').add_text("Congrats! You made it to the last level. You've done enough physics, how about you just talk to Willow?")
            ])
            self.all_sprites.player[0] = self.camera
        self.camera.pos = self.saved_text[0].pos.copy()

        self.manager.ready = True
    def sequence2(self):
        if not self.manager.called:
            pass
        self.camera.pos += (self.willow.pos - self.camera.pos) * self.dt * 10
        if self.camera.pos.distance_to(self.willow.pos) < 3:
            self.manager.ready = True
    def sequence3(self):
        if not self.manager.called:
            [text.kill() for text in self.saved_text]
            self.saved_text.clear()
            self.all_sprites.player[0] = self.willow
        if self.scale_by < 4:
            self.scale_by += self.dt * 1.5
            self.all_sprites.scale_world(self.scale_by)
        else:
            self.manager.ready = True
    def sequence4(self):
        if not self.manager.called:
            pass
        self.all_sprites.player_offset.x += ((self.willow.pos.x - 200) - (self.willow.pos.x + self.all_sprites.player_offset.x)) * self.dt * 10
        if (self.all_sprites.player_offset.x < -195):
            self.manager.ready = True
    def sequence5(self):
        if not self.manager.called:
            self.all_sprites.add(self.question,self.AI_query, self.willow_response)
            self.saved_text.extend([
                BasicText(self.groups, (WIDTH/4, 30),30,"You:"),
                BasicText(self.groups, (WIDTH / 2, 500), 30, "Willow:"),
            ])
            self.AI_query.pos = self.saved_text[0].rect.midbottom + vector(0, 30)
            self.willow_response.pos = self.AI_query.pos + vector(0,300)
            self.saved_text[1].rect.x = WIDTH/4 - 10
        self.saved_text[1].rect.y =  round(self.willow_response.pos.y  -self.willow_response.view_height/2 - 50)
    def eventLoop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN and len(self.user_input_box.groups()) != 0:
                invalid = self.user_input_box.inputValidation(event)
                if not invalid and event.key == pygame.K_RETURN:
                    self.submissions.append(self.user_input_box.text)
                    Leaves.KillAnimation(self.all_sprites, self.user_input_box, self.graphics['leaves'])
                    Leaves.KillAnimation(self.all_sprites, self.question, self.graphics['leaves'])
                    self.user_input_box.blitText("")
                    self.manager.ready = True
            if event.type == pygame.KEYDOWN and self.AI_query in self.all_sprites:
                query = self.AI_query.inputValidation(event)
                if event.key == pygame.K_RETURN:
                    threading.Thread(target=self.Get_AI_response, daemon=True).start()
    def Get_AI_response(self):
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "chat_history": self.chat_history,
            "user_query": self.AI_query.text
        }
        try:
            response = requests.post("https://car-maintenance-app.onrender.com/willow", headers=headers, json=data)
            json_data = response.json()
            response_text = json_data.get("response", "Unexpected response format.")
        except Exception as e:
            print("ERROR:", e)
            response_text = "Something went wrong! Check your internet."
        self.willow_response.add_text(response_text)

        self.chat_history.extend([
            {"role": "user", "content": self.AI_query.text},
            {"role": "assistant", "content": response_text}
        ])
        if len(self.chat_history) > 6:
            self.chat_history = self.chat_history[2:]
    def run(self,dt):
        self.eventLoop()
        if pygame.key.get_pressed()[pygame.K_SPACE]:
            self.manager.progress_Timer.active = False
        self.manager.update()
        # updates
        self.updates_group.update(dt)
        self.all_sprites.update(dt)
        self.all_sprites.draw(dt)
        self.transition.display(dt)
