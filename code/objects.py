import random
import re
import pygame.display

from timer import *
from settings import *
from pygame.math import Vector2 as vector
from random import randint, choice
import math
from sys import exit
# Basic Sprites ---------------------------------------------------------------
class General(pygame.sprite.Sprite):
    def __init__(self, groups, image, origin, draw='fixed',z = 'general'):
        self.z = LAYERS[z]
        super().__init__(groups)
        self.graphic = image
        self.draw = draw
        self.pos = vector(origin)
        self.image = image
        self.rect = self.image.get_rect(center = origin)
    def place_image(self, pos):
        self.pos = pos.copy()
        self.rect = self.image.get_rect(center = self.pos)
class BasicAnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, group, pos, graphics):
        self.z = LAYERS['sprites']
        # animation
        self.frames = graphics.copy()
        self.frame_index = 0

        # movement
        self.pos = vector(pos)
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center = pos)
        super().__init__(group)
    def animate(self,dt):
        self.frame_index += 14 * dt
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        self.image = self.frames[int(self.frame_index)]
    def update(self,dt):
        self.animate(dt)

# Advanced Sprites ------------------------------------------------------------------
class Player(pygame.sprite.Sprite):
    def __init__(self, groups, pos, graphics, draw='fixed'):
        super().__init__(groups['all_group'])
        self.z = LAYERS['sprites']
        self.draw = draw
        self.block_group = groups['block_group']
        self.graphic = {
            key: [surf.copy() for surf in value] for key,value in graphics.items()
        }



        # animation
        self.frames = graphics
        self.frame_index = 0
        self.orientation = 'right'
        self.status = 'idle'
        self.image = self.frames[f'{self.status}_{self.orientation}'][int(self.frame_index)]
        self.rect = self.image.get_rect(center=pos)

        # hitbox
        self.hitbox = self.rect.inflate(-10, 0)

        # movement
        self.pos = vector(self.rect.center)
        self.old_pos = vector()
        self.speed = 400
        self.direction = vector()
        self.gravity = 4
        self.drift_velocity = 1
        self.attack = False

        #Trail
        self.trail = Trail(groups,self)

        # boolean checks
        self.lock_status = False
        self.lock_input= False
        self.on_floor = False
    def input(self,dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT]:
            self.direction.x = 1
            self.orientation = 'right'
        elif keys[pygame.K_LEFT]:
            self.direction.x = -1
            self.orientation = 'left'
        else:
            self.direction.x = 0
        if keys[pygame.K_SPACE]:
            self.direction.y = -2 if self.on_floor else self.direction.y
    def check_on_floor(self):
        floor_rect = pygame.Rect((self.hitbox.left + 3, self.hitbox.bottom), (self.hitbox.width - 6, 2))
        floor_sprites = [sprite for sprite in self.block_group if sprite.rect.colliderect(floor_rect)]
        self.on_floor = True if floor_sprites else False
    def place_player(self, pos):
        self.pos = pos
        self.hitbox.center = (round(self.pos.x), round(self.pos.y))
        self.rect.center = (self.hitbox.centerx, self.hitbox.centery)
    def move(self,dt):
        self.old_pos = self.pos.copy()
        #apply gravity
        self.direction.y += self.gravity * dt if self.direction.y < self.drift_velocity else 0

        # horizontal movement
        self.pos.x += self.direction.x * self.speed * dt
        self.hitbox.centerx = round(self.pos.x)
        self.rect.centerx = self.hitbox.centerx
        self.collisions('horizontal')

        # vertical movement
        self.pos.y += self.direction.y * self.speed * dt
        self.hitbox.centery = round(self.pos.y)
        self.rect.centery = self.hitbox.centery

        self.collisions('vertical')
    def collisions(self,type):
        for sprite in self.block_group:
            if self.hitbox.colliderect(sprite.rect):
                if type == 'horizontal':
                    if self.direction.x > 0:
                        self.hitbox.right = sprite.rect.left
                    if self.direction.x < 0:
                        self.hitbox.left = sprite.rect.right
                    self.rect.centerx, self.pos.x = self.hitbox.centerx, self.hitbox.centerx
                if type == 'vertical':
                    if self.direction.y > 0:
                        self.hitbox.bottom = sprite.rect.top
                    if self.direction.y < 0:
                        self.hitbox.top = sprite.rect.bottom
                    self.rect.centery, self.pos.y = self.hitbox.centery, self.hitbox.centery
                    self.direction.y = 0
    def get_status(self):
        if self.on_floor and self.direction.x == 0:
            self.status = 'idle'
        elif self.on_floor:
            self.status = 'run'
        elif self.direction.y < 0:
            self.status = 'jump'
        else:
            self.status = 'fall'
        if self.attack:
            self.status = 'attack'
    def animate(self,dt):
        current_animation = self.frames[f'{self.status}_{self.orientation}']
        self.frame_index += PLAYER_ANIMATION[f'{self.status}'] * dt
        if self.frame_index >= len(current_animation)-0.5:
            self.frame_index = 0
            self.attack = False
        self.image = current_animation[int(self.frame_index)]
        self.rect = self.image.get_rect(center=self.pos)
    def update(self, dt):
        self.check_on_floor()
        if not self.lock_input:
            self.input(dt)
        if not self.lock_status:
            self.get_status()
        self.move(dt)
        self.animate(dt)
class Bird(BasicAnimatedSprite):
    def __init__(self, group, pos, graphics, speed, draw='fixed'):
        super().__init__(group['all_group'],pos,graphics)
        self.z = LAYERS['sprites']
        self.draw = draw

        # movement
        self.direction = vector(random.choice([-1,1]),0)
        self.speed = speed
    def animate(self,dt):
        self.frame_index += 20 * dt
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        self.image = self.frames[int(self.frame_index)]
    def move(self, dt):

        self.pos.y -= randint(self.speed[1][0],self.speed[1][1]) * dt
        self.rect.y = round(self.pos.y)

        self.pos.x += randint(self.speed[0][0],self.speed[0][1]) * self.direction.x * dt
        self.rect.x = round(self.pos.x)
    def update(self,dt):
        self.animate(dt)
        self.move(dt)
class Ball(pygame.sprite.Sprite):
    def __init__(self,groups, pos, graphics, draw='fixed'):
        self.block_group = groups['block_group']
        super().__init__(groups['all_group'])
        self.z= LAYERS['sprites']
        self.draw = draw
        self.asset = graphics
        self.image = graphics
        self.rect = self.image.get_rect(center = pos)

        self.pos = vector(pos)
        self.direction = vector()
        self.speed = 50
        self.gravity = 5
        self.elasticity = .5
    def place_ball(self, pos):
        self.pos = pos
        self.rect.centerx = round(self.pos.x)
        self.rect.centery = round(self.pos.y)
    def move(self,dt):
        #apply gravity
        self.direction.y += self.gravity * dt

        # horizontal movement
        self.pos.x += self.direction.x * self.speed * dt
        self.rect.centerx = round(self.pos.x)
        self.collisions('horizontal')

        # vertical movement
        self.pos.y += self.direction.y * self.speed * dt
        self.rect.centery = round(self.pos.y)

        self.collisions('vertical')
    def collisions(self,type):
        for sprite in self.block_group:
            if self.rect.colliderect(sprite.rect):
                if type == 'horizontal':
                    if self.direction.x > 0:
                        self.rect.right = sprite.rect.left
                    if self.direction.x < 0:
                        self.rect.left = sprite.rect.right
                    self.pos.x = self.rect.centerx
                if type == 'vertical':
                    if self.direction.y > 0:
                        self.rect.bottom = sprite.rect.top
                    if self.direction.y < 0:
                        self.rect.top = sprite.rect.bottom
                    self.pos.y = self.rect.centery
                    self.direction.x *= self.elasticity
                    self.direction.y *= -1 * self.elasticity
    def update(self, dt):
        self.move(dt)
class Cloud(pygame.sprite.Sprite):
    def __init__(self, group, image, origin,speed,camera_link = None, draw='fixed',z = 'general'):
        super().__init__(group)
        self.all_sprites = group
        self.z = LAYERS[z]
        self.draw = draw
        self.speed = speed
        self.camera_link = camera_link
        self.camera_link_old_pos = camera_link[0].pos if camera_link[0] else vector()
        self.camera_turned_on = False

        self.direction = choice([-1,1])
        self.pos = vector(origin)
        self.image = image
        self.rect = self.image.get_rect(center = origin)
    def move(self,dt):
        # Base movement
        increment = self.speed * self.direction * dt
        self.pos.x += self.speed * self.direction * dt
        self.rect.x = round(self.pos.x)

        if self.camera_link[0] and not self.camera_turned_on:
            self.camera_link_old_pos = self.camera_link[0].pos.copy()
            self.camera_turned_on = True

        # camera adjusted movement
        if self.camera_link[0]:
            increment += (self.camera_link[0].pos.x - self.camera_link_old_pos.x) * dt * 4
            self.pos.x -= (self.camera_link[0].pos.x - self.camera_link_old_pos.x) * dt * 4
            self.rect.x = round(self.pos.x)
            self.pos.y -= (self.camera_link[0].pos.y - self.camera_link_old_pos.y) * dt * 3
            self.rect.y = round(self.pos.y)
            self.camera_link_old_pos = self.camera_link[0].pos.copy()
        else:
            self.camera_turned_on = False

        perspective_direction = 1 if increment > 0 else -1
        too_far = self.pos.y < -10000
        if too_far:
            self.kill()
        if (self.pos.x > WIDTH + 400 and perspective_direction == 1):
            self.kill()
        if (self.pos.x < - 400 and perspective_direction == -1):
            self.kill()
    def update(self,dt):
        self.move(dt)

# For particle effect/ kill animation
class Leaves(BasicAnimatedSprite):
    def __init__(self, group, pos, graphics, draw='fixed'):
        super().__init__(group, pos, graphics)
        self.z = LAYERS['leaves']
        self.draw = draw

        self.direction = vector(random.choice([-1,1]),random.choice([-1,1]))
        self.speed = vector(randint(-100,100),randint(-100,100))
        self.lifetime = Timer(1000)
        self.lifetime.activate()
    def move(self,dt):
        self.pos.y -= self.speed.y * self.direction.y * dt
        self.rect.y = round(self.pos.y)

        self.pos.x += self.speed.x * self.direction.x * dt
        self.rect.x = round(self.pos.x)
    @staticmethod
    def KillAnimation(group, sprite, graphics):
        ParticleQuantity = int(((sprite.rect.width / 65) * (sprite.rect.height / 65)))
        for i in range(ParticleQuantity):
            Leaves(group, (randint(sprite.rect.left, sprite.rect.right), randint(sprite.rect.top, sprite.rect.bottom)),graphics, sprite.draw)
        sprite.kill()
    def update(self,dt):
        self.kill() if not self.lifetime.active else None
        self.image.set_alpha(255 - (self.lifetime.elapsed / 1000)*255)
        self.lifetime.update()
        self.move(dt)
        super().animate(dt)
class Trail(pygame.sprite.Sprite):
    def __init__(self, group, sprite):
        self.all_sprites = group['all_group']
        super().__init__(group['updates_group'])
        self.z = LAYERS['general']
        self.image = None
        self.sprite = sprite

        self.trail_timer = Timer(40)
    def create_Trail(self):
        player_direction = [self.sprite.direction.x,round(self.sprite.direction.y)]
        if not self.trail_timer.active and player_direction != [0,0] :
            direction = (self.sprite.pos - self.sprite.old_pos)
            direction = -1 * direction.normalize() if direction.magnitude() > 0 else vector()
            direction = direction.rotate(randint(-15,15))
            TrailCircle(self.all_sprites, self.sprite.pos, direction * 300, self.sprite.draw)
            self.trail_timer.activate()
    def update(self, dt):
        if self.sprite.groups():
            self.trail_timer.update()
            self.create_Trail()
# Circles used for trail
class TrailCircle(pygame.sprite.Sprite):
    def __init__(self, group, pos, speed, draw='fixed'):
        super().__init__(group)
        self.z = LAYERS['trail']
        self.draw = draw

        self.colorval = randint(160,210)
        self.color = (self.colorval,self.colorval,self.colorval)
        self.radius = randint(10,15)
        self.pos = vector(pos)
        self.speed = speed
        self.speed.x
        self.image = None
    def draw_circle(self, offset):
        if self.draw == 'camera':
            pygame.draw.circle(pygame.display.get_surface(),self.color,self.pos + offset,self.radius)
        if self.draw == 'fixed':
            pygame.draw.circle(pygame.display.get_surface(),self.color,self.pos,self.radius)
    def update(self, dt):
        self.radius -= 20*dt
        self.colorval += 250*dt
        if self.colorval > 255:
            self.colorval = 255
        self.color = (self.colorval,self.colorval,self.colorval)

        self.pos.y += self.speed.y * dt
        self.pos.x += self.speed.x * dt
        if self.radius < 1:
            self.kill()
#Create balloons
class Balloon(pygame.sprite.Sprite):
    def __init__(self, group, pos, graphics, sprite, draw='fixed'):
        self.all_sprites = group
        super().__init__(group)
        self.z = LAYERS['balloon']
        self.draw = draw
        self.color = randint(0,4)

        self.image = graphics[self.color]
        self.rect = self.image.get_rect(center = pos)

        self.direction = random.choice([-1,1])
        self.pos = vector(pos)
        self.length = randint(80,150)
        self.domain = int(30 * ((self.length-80) / 70))
        self.pos.x = randint(sprite.pos.x - self.domain, sprite.pos.x + self.domain)

        self.popped = False

        self.sway_x_dist = 0
        self.sway_x_dir = random.choice([-1,1])
        self.sway_y_dist = 0
        self.sway_y_dir = random.choice([-1,1])

        self.sprite = sprite
        self.connection = sprite.pos
        self.display_surface = pygame.display.get_surface()
    def draw_balloonstrings(self, offset):
        self.draw = 'camera'

        if self.draw == 'camera':
            pygame.draw.line(self.display_surface,'black',self.rect.midbottom + offset, self.connection + offset,1)
        if self.draw == 'fixed':
            pygame.draw.line(self.display_surface,'black',self.rect.midbottom, self.connection,1)
    def pop(self, dt):
        if self.popped:
            self.pos.y -= 700 * dt
            self.rect.centery = round(self.pos.y)

            self.connection = vector(self.pos.x, self.pos.y + self.length)

            if self.pos.y < -50:
                self.kill()
    def move(self, dt):
        self.connection = self.sprite.pos.copy()
        speed = randint(0,30)
        if self.pos.x > self.connection.x + self.domain:
            self.direction = -1
            speed = (self.pos.x - (self.connection.x)) *5 * (1 - (self.length-100)/170)
        if self.pos.x < self.connection.x - self.domain:
            self.direction = 1
            speed = ((self.connection.x) - self.pos.x)*5 * (1 - (self.length-100)/170)

        self.sway_x_dist += randint(10,20) * self.sway_x_dir * dt
        if abs(self.sway_x_dist) > 5:
            self.sway_x_dir *= -1
        self.sway_y_dist += randint(10, 20) * self.sway_y_dir * dt
        if abs(self.sway_y_dist) > 5:
            self.sway_y_dir *= -1


        self.pos.x += speed * self.direction * dt
        self.rect.centerx = round(self.pos.x  + self.sway_x_dist)
        try:
            y = math.sqrt(self.length**2 - (self.pos.x - self.connection.x)**2)
        except ValueError:
            y = math.sqrt(self.length**2 - 1**2)
        self.pos.y = self.sprite.pos.y - y
        self.rect.centery = round(self.pos.y + self.sway_y_dist)
    def update(self, dt):

        if self.popped:
            self.pop(dt)
        else:
            self.move(dt)


    @staticmethod
    def create_balloons(group, graphics, sprite, quantity):
        for i in range(quantity):
            Balloon(group, sprite.pos, graphics, sprite)
    @staticmethod
    def pop_balloons(group, number_to_pop, connection):
        count = number_to_pop
        for sprite in group:
            if isinstance(sprite,Balloon) and sprite.sprite == connection:
                sprite.popped = True
                count -= 1
            if not count:
                break

# TEXT / BUTTON ----------------------------------------------------------------------
# TextBox input
class TextBox(pygame.sprite.Sprite):
    def __init__(self,group,origin,width,height, draw='fixed'):
        self.all_sprites = group['all_group']
        super().__init__(group['all_group'])
        self.z = LAYERS['text']
        self.draw = draw

        self.official_width = width
        self.width = width
        self.height = height

        # Create initial TextBox
        self.pos = vector(origin)
        self.image = pygame.Surface((width,height))
        self.image.fill("white")
        pygame.draw.rect(self.image, "black", self.image.get_rect(), 1)
        self.rect = self.image.get_rect(center = origin)

        self.error_text = Text(group,10, (0,0), 200)
        self.error_text.add_text("Please enter a number. (max 10 characters)")
        self.all_sprites.remove(self.error_text)

        self.text = ""
    def blitText(self, text, fontsize = 25):
        self.text = text
        font = pygame.font.Font('../fonts/sigmar.ttf', fontsize)
        text_width = font.size(text)[0]

        if text_width > self.official_width-8:
            self.width = font.size(text)[0] + 8
        if text_width < self.official_width - 8:
            self.width = self.official_width - 8
        self.image = pygame.Surface((self.width,self.height))
        self.rect = self.image.get_rect(center = self.pos)

        text_surf = font.render(text, True, 'Black')
        text_rect = text_surf.get_rect(center=(self.rect.width / 2, self.rect.height / 2))

        self.image.fill("white")
        pygame.draw.rect(self.image, "black", self.image.get_rect(), 1)
        self.image.blit(text_surf, text_rect)
    def inputValidation(self, event):
        if (event.key == pygame.K_BACKSPACE):
            self.text = self.text[:-1]
        else:
            try:
                self.text += chr(event.key) if (len(self.text) < 11) and (event.key != pygame.K_RETURN) else ""
            except ValueError:
                pass
        self.blitText(self.text)

        # is a valid decimal number
        invalid = False
        if not (bool(re.match(r'^(-?\d+)?(\.)?(\d+)?$', self.text))):
            invalid = True
        else:
            invalid = False if self.text != "" else True
        if invalid and self.text != "":
            self.all_sprites.add(self.error_text)
        else:
            self.all_sprites.remove(self.error_text)
        return invalid
    def update(self, dt):
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self.error_text.pos = self.rect.midbottom + vector(0, 30)
        self.error_text.rect.center = (round(self.error_text.pos.x), round(self.error_text.pos.y))
class TextBoxPlus(pygame.sprite.Sprite):
    def __init__(self,group,origin,width,height,fontsize=25, draw='fixed',margin=0):
        self.all_sprites = group['all_group']
        super().__init__(group['all_group'])
        self.z = LAYERS['text']
        self.draw = draw

        self.official_width = width
        self.width = width
        self.height = height
        self.fontsize = fontsize
        self.font = pygame.font.Font('../fonts/sigmar.ttf', self.fontsize)
        self.fontpadding = ((self.font.render("test",True, 'black').get_height() - fontsize) / 2)
        margin_of_error = int(.25 * self.fontpadding)
        self.fontpadding -= margin_of_error

        # increase spacing between lines
        self.margin = margin

        # Create initial TextBox
        self.pos = vector(origin)
        self.image = pygame.Surface((self.width + 8 * self.font.size(" ")[0], (self.font.render(" ", True, 'black').get_height() - 2 * self.fontpadding) + self.margin),pygame.SRCALPHA)
        # self.image.fill((0,0,0,0))
        pygame.draw.rect(self.image, (255, 255, 255, 150), self.image.get_rect(), border_radius=20)
        pygame.draw.rect(self.image, 'black', self.image.get_rect(), width=2,border_radius=20)

        self.rect = self.image.get_rect(center = origin)

        self.text = ""
    def blitText(self, text, fontsize = 25):
        text = text.split()
        text_surf_list = []
        if text:
            textbox_width = self.width + 8 * self.font.size(" ")[0]
            sum_row_width = 0
            sum_row_text = ""
            # Create rows and find TextBox height/width
            for index, word in enumerate(text):
                sum_row_width += self.font.size(word + " ")[0]
                if sum_row_width > self.width:
                    within_margin = sum_row_width < self.width + 8*self.font.size(" ")[0]

                    if within_margin:
                        sum_row_text += word + " "
                    else:
                        sum_row_width -= self.font.size(word + " ")[0]
                    text_surf_list.append(self.font.render(sum_row_text, True, 'black'))
                    if within_margin:
                        sum_row_text = ""
                        sum_row_width = 0
                    else:
                        sum_row_text = word + " "
                        sum_row_width = self.font.size(word + " ")[0]
                else:
                    sum_row_text += word + " "
            if sum_row_text:
                text_surf_list.append(self.font.render(sum_row_text, True, 'black'))

            text_surf_list = [surf.subsurface(pygame.Rect(0, self.fontpadding, surf.get_width(), surf.get_height() - 2 * self.fontpadding)) for surf in text_surf_list]
            textbox_height = len(text_surf_list) * ((text_surf_list[0].get_height()) + self.margin)

            # Blit rows onto TextBox
            textbox = pygame.Surface((textbox_width, textbox_height), pygame.SRCALPHA)
            pygame.draw.rect(textbox, (255, 255, 255, 150), textbox.get_rect(), border_radius=20)

            for index, row in enumerate(text_surf_list):
                row_rect = row.get_rect(midtop=(textbox_width / 2, (self.fontsize + self.margin) * index))
                textbox.blit(row, row_rect)
            pygame.draw.rect(textbox,'black',textbox.get_rect(),2, border_radius=20)
            self.image = textbox
            self.rect = self.image.get_rect(midtop=self.pos)
        else:
            self.image = pygame.Surface((self.width + 8 * self.font.size(" ")[0],(self.font.render(" ",True,'black').get_height() - 2*self.fontpadding) + self.margin),pygame.SRCALPHA)
            self.image.fill((0, 0, 0, 0))
            pygame.draw.rect(self.image, (255, 255, 255, 150), self.image.get_rect(), border_radius=20)
            pygame.draw.rect(self.image, 'black', self.image.get_rect(), width=2, border_radius=20)

            self.rect = self.image.get_rect(midtop=self.pos)
    def inputValidation(self, event):
        if event.type == pygame.KEYDOWN:

            if (event.key == pygame.K_BACKSPACE):
                self.text = self.text[:-1]
            else:
                try:
                    self.text += event.unicode if (event.key != pygame.K_RETURN) else " "
                except ValueError:
                    pass
            self.blitText(self.text)
        return self.text
    def update(self, dt):
        self.rect.midtop = (round(self.pos.x), round(self.pos.y))
        rect = self.rect.move(self.all_sprites.store_offset.x, self.all_sprites.store_offset.y)

# Animated box of text
class Text(pygame.sprite.Sprite):
    def __init__(self, group, fontsize, pos, width, speed = 100, animate=True,color = 'black', align = 'center', padding=10, draw='fixed'):
        super().__init__(group['all_group'])
        self.z = LAYERS['text']
        self.group = group
        self.pos = vector(pos)

        self.draw = draw
        self.animate = animate
        self.align = align
        self.text = ""

        self.fontsize = fontsize
        self.width = width
        self.total_height = 0
        self.speed = speed

        self.font = pygame.font.Font('../fonts/sigmar.ttf', fontsize)

        # The reason I do this step is font heights vary wildly, and this margin_of_error works for my font "Sigmar"
        self.fontpadding = ((self.font.render("test",True, color).get_height() - fontsize) / 2)
        margin_of_error = int(.25 * self.fontpadding)
        self.fontpadding -= margin_of_error


        self.portion = pygame.Rect(0, 0, width, 0)
        self.textbox = pygame.Surface((width, 0), pygame.SRCALPHA)
        self.boxpadding = padding


        self.margin = 0
        self.image = None
        self.color = color
        self.view_height = 0
    def add_text(self, text):
        self.text = text
        text = text.split()
        text_surf_list = []

        textbox_width = 0
        sum_row_width = 0
        sum_row_text = ""
        # Create rows and find TextBox height/width
        for index, word in enumerate(text):

            sum_row_width += self.font.size(word + " ")[0]

            if sum_row_width > self.width or (index == len(text) - 1) or word == "/skip":
                within_margin_or_lastword = sum_row_width < self.width + 8*self.font.size(" ")[0] or (index == len(text) - 1)
                if word == "/skip":
                    sum_row_width -= self.font.size(word + " ")[0]
                    text_surf_list.append(self.font.render(sum_row_text, True, self.color))
                    textbox_width = max(textbox_width, sum_row_width)
                    sum_row_text = ""
                    sum_row_width = 0
                    continue

                if within_margin_or_lastword:
                    sum_row_text += word + " "
                else:
                    sum_row_width -= self.font.size(word + " ")[0]
                text_surf_list.append(self.font.render(sum_row_text, True, self.color))
                textbox_width = max(textbox_width, sum_row_width)

                if within_margin_or_lastword:
                    sum_row_text = ""
                    sum_row_width = 0
                else:
                    sum_row_text = word + " "
                    sum_row_width = self.font.size(word + " ")[0]
            else:
                sum_row_text += word + " "

        text_surf_list = [surf.subsurface(pygame.Rect(0, self.fontpadding, surf.get_width(), surf.get_height() - 2 * self.fontpadding)) for surf in text_surf_list]
        textbox_height = len(text_surf_list) * (text_surf_list[0].get_height()) + self.margin * len(text_surf_list) if len(text_surf_list) > 0 else 0

        # Blit rows onto TextBox
        unpadded_textbox = pygame.Surface((textbox_width, textbox_height), pygame.SRCALPHA)
        for index, row in enumerate(text_surf_list):
            if self.align == 'center':
                row_rect = row.get_rect(midtop=(textbox_width / 2, (self.fontsize + self.margin) * index))
            else:
                row_rect = row.get_rect(topleft=(0, (self.fontsize + self.margin) * index))
            unpadded_textbox.blit(row, row_rect)
        self.textbox = pygame.Surface((textbox_width + self.boxpadding*2,textbox_height+self.boxpadding*2),pygame.SRCALPHA)
        pygame.draw.rect(self.textbox, (255,255,255,100), self.textbox.get_rect(), border_radius=20)
        self.textbox.blit(unpadded_textbox,(self.boxpadding,self.boxpadding))

        self.view_height = 0
        self.portion = pygame.Rect(0, 0, self.textbox.get_width(), 0)
        self.total_height = self.textbox.get_height()
        self.image = self.textbox.subsurface(self.portion)
        self.rect = self.image.get_rect(center=self.pos)

        return self
    def change_fontsize(self, size):
        self.fontsize = size
        self.font = pygame.font.Font('../fonts/sigmar.ttf', size)

        # Murad: The reason I do this step is because font heights vary wildly, and this margin of error works for my font "Sigmar"
        self.fontpadding = ((self.font.render("test",True, self.color).get_height() - size) / 2)
        margin_of_error = int(.25 * self.fontpadding)
        self.fontpadding -= margin_of_error
    def draw_mask(self, dt):
        if self.animate:
            self.view_height += self.speed * dt

            if self.view_height <= self.total_height:
                self.portion.height = round(self.view_height)
            else:
                self.view_height = self.total_height + 1
                self.portion.height = round(self.total_height)
            self.image = self.textbox.subsurface(self.portion)
            self.rect = self.image.get_rect(center=self.pos)
        else:
            self.image = self.textbox
            self.rect = self.image.get_rect(center=self.pos)
    def update(self,dt):
        self.draw_mask(dt)

# blit basic text line anywhere
class BasicText(pygame.sprite.Sprite):
    def __init__(self, group, origin, fontsize, text,color='black', draw='fixed'):
        super().__init__(group['all_group'])
        self.z = LAYERS['text']
        self.draw = draw

        font = pygame.font.Font('../fonts/sigmar.ttf', fontsize)
        text_surf = font.render(text, True, color)
        self.image = text_surf
        self.rect = text_surf.get_rect(topleft = origin)
# Button with text and click
class Button(pygame.sprite.Sprite):
    def __init__(self,groups,origin,width=10,height=10, image = None,draw='fixed'):
        super().__init__([groups['block_group'], groups['button_group'],groups['all_group']])
        self.z = LAYERS['button']
        self.draw = draw

        self.pos = vector(origin)
        self.image = pygame.Surface((width,height),pygame.SRCALPHA) if not image else image
        self.image.fill((255, 184, 89)) if not image else image
        self.rect = self.image.get_rect(center = origin)

        self.width = width
        self.height = height
        self.clicked = False
        self.level = None

    def blitText(self, text, fontsize):
        self.image.fill((0,0,0,0))
        pygame.draw.rect(self.image, (255, 184, 89), self.image.get_rect(), border_radius=20)
        font = pygame.font.Font('../fonts/sigmar.ttf', fontsize)
        text_surf = font.render(text, True, 'Black')
        text_rect = text_surf.get_rect(center=(self.rect.width / 2, self.rect.height / 2))
        self.image.blit(text_surf, text_rect)
        return self
    def update(self,dt):
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            self.image.set_alpha(128)
            self.clicked = True if pygame.mouse.get_pressed()[0] else False
        else:
            self.image.set_alpha(255)


# Basic Shapes ----------------------------------------------------------------
class Block(pygame.sprite.Sprite):
    def __init__(self,groups,origin,width=10,length=10,image = None,draw='fixed'):
        self.z = LAYERS['block']
        self.draw = draw

        self.block_group = groups['block_group']
        self.all_group = groups['all_group']

        super().__init__([self.block_group, self.all_group])

        self.pos = vector(origin)
        self.image = pygame.Surface((width,length),pygame.SRCALPHA) if not image else image
        self.image.fill((255, 184, 89)) if not image else None
        self.rect = self.image.get_rect(center = origin)

        self.width = width
        self.length = length
    def blitText(self, text, fontsize,transparent = False, color = "black"):
        self.image.fill((0,0,0,0))
        pygame.draw.rect(self.image, (255, 184, 89), self.image.get_rect(), border_radius=20)
        font = pygame.font.Font('../fonts/sigmar.ttf', fontsize)
        text_surf = font.render(text, True, color)
        text_rect = text_surf.get_rect(center=(self.rect.width / 2, self.rect.height / 2))
        if transparent:
            self.image = text_surf
            self.rect = text_surf.get_rect(center = self.pos)
        self.image.blit(text_surf, text_rect)
        return self
class Circle(pygame.sprite.Sprite):
    def __init__(self,groups,origin,radius, draw='fixed'):
        self.z = LAYERS['block']
        self.draw = draw

        self.block_group = groups['block_group']
        self.circle_group = groups['circle_group']
        self.all_group = groups['all_group']

        super().__init__([self.circle_group,self.all_group])
        self.image = None
        # circle properties
        self.pos = vector(origin)
        random_number = random.choice([-1.5,1.5])
        self.pastpos = vector(origin[0]+random_number,origin[1]+random_number)
        self.currentpos = vector(origin)
        self.acceleration = vector((0,0))
        self.elasticity = 1
        self.radius = radius
        self.mass = self.radius / 50
        self.color = (randint(0,255),randint(0,255),randint(0,255))
        self.savedImage = None
        self.angle = 0
        self.rotationSpeed = randint(5,30)

        self.display_surface = pygame.display.get_surface()
    def moveLinear(self, dt):
        self.currentpos = self.pos.copy()

        self.pos.x += (self.pos.x - self.pastpos.x) + self.acceleration.x * dt*dt
        self.pos.y += (self.pos.y - self.pastpos.y) + self.acceleration.y * dt*dt
        self.blockCollisions(dt)

        self.pastpos = self.currentpos.copy()
    def blockCollisions(self,dt):
        # blocks
        for block in self.block_group:
            collides = False
            betweenTandB = True if (self.pos.y + self.radius > block.rect.top) and (self.pos.y - self.radius < block.rect.bottom) else False
            betweenRandL = True if (self.pos.x + self.radius > block.rect.left) and (self.pos.x - self.radius < block.rect.right) else False

            if (betweenTandB and betweenRandL):
                collides = True
                if (self.pos.y < block.rect.top or self.pos.y > block.rect.bottom) and (self.pos.x > block.rect.right or self.pos.x < block.rect.left):
                    closestCorner = ""
                    closestCorner += "top" if self.pos.y < block.rect.top else "bottom"
                    closestCorner += "right" if self.pos.x > block.rect.right else "left"
                    corner = getattr(block.rect, closestCorner)
                    collides = True if self.pos.distance_to(corner) < self.radius else False
            #collision resolution
            if collides:
                diff = vector(self.pos.x - self.currentpos.x, self.pos.y - self.currentpos.y)
                if self.pos.y < block.rect.top:
                    self.pos.y -= 400*dt
                    self.currentpos.y = self.pos.y + diff.y * self.elasticity
                if self.pos.y > block.rect.bottom:
                    self.pos.y +=400*dt
                    self.currentpos.y = self.pos.y + diff.y * self.elasticity
                if self.pos.x < block.rect.left:
                    self.pos.x -= 400*dt
                    self.currentpos.x = self.pos.x + diff.x * self.elasticity
                if self.pos.x > block.rect.right:
                    self.pos.x += 400*dt
                    self.currentpos.x = self.pos.x + diff.x * self.elasticity
        #bounds of display
        diff = vector(self.pos.x - self.currentpos.x,self.pos.y - self.currentpos.y)
        if (self.pos.x > WIDTH - self.radius):
            #right
            self.pos.x = WIDTH - self.radius
            self.currentpos.x = self.pos.x + diff.x * self.elasticity
        if (self.pos.x < self.radius):
            #left
            self.pos.x = self.radius
            self.currentpos.x = self.pos.x + diff.x * self.elasticity
        if (self.pos.y > HEIGHT - self.radius):
            #down
            self.pos.y = HEIGHT - self.radius
            self.currentpos.y = self.pos.y + diff.y * self.elasticity
        if (self.pos.y < self.radius):
            #up
            self.pos.y = self.radius
            self.currentpos.y = self.pos.y + diff.y * self.elasticity
    def circleCollisions(self):
        #circle collisions
        for circle in self.circle_group:
            if self != circle:
                collision = circle.pos.distance_to(self.pos) < (self.radius+circle.radius)
                if (collision):
                    collisionNormal = (circle.pos - self.pos).normalize()
                    separation = (self.radius+circle.radius) - self.pos.distance_to(circle.pos)
                    VA = (self.pos - self.pastpos)
                    VB = (circle.pos - circle.pastpos)
                    Vrelative = VB - VA

                    approaching = Vrelative.dot(collisionNormal)
                    elasticity = 1

                    self.pos -= collisionNormal * separation/2
                    self.pastpos -= collisionNormal * separation / 2

                    circle.pos += collisionNormal * separation / 2
                    circle.pastpos += collisionNormal * separation / 2
                    j = (-1 * (1 + elasticity) * approaching) / ((1 / self.mass) + (1 / circle.mass))

                    self.pos -= j * collisionNormal / self.mass
                    circle.pos += j * collisionNormal / circle.mass
    def drawCircles(self,offset):
        if self.draw == 'camera':
            pygame.draw.circle(self.display_surface, self.color, self.pos + offset, self.radius)
        if self.draw == 'fixed':
            pygame.draw.circle(self.display_surface, self.color, self.pos, self.radius)
    def update(self,dt):
        self.circleCollisions()
        self.moveLinear(dt)


# Miscellaneous ----------------------------------------------------------------
# Toggles Kinematic Equations
class ToggleImage(pygame.sprite.Sprite):
    def __init__(self, group, pos,image,always_visible=60,linked_text=None, draw='fixed'):
        super().__init__(group['all_group'])
        self.z = LAYERS['general']
        self.draw = draw

        self.pos = vector(pos)
        self.image = image
        self.always_visible = always_visible if always_visible else image.get_height()

        self.optional_image_body = None
        self.rect = self.image.get_rect(topleft = self.pos)

        portion = pygame.Rect(0,0,self.rect.width, self.always_visible)
        self.saved = self.image.subsurface(portion)
        self.top_image = image
        self.text_object = linked_text
        self.toggle_timer = Timer(500)
        self.toggle()
    def change_body(self, text):
        self.text_object.add_text(text)
        self.custom_body(self.text_object.textbox.copy())
    def custom_body(self,body):
        surf = pygame.Surface((max(self.top_image.get_width(),body.get_width()),self.top_image.get_height() + body.get_height()),flags=pygame.SRCALPHA)
        surf.blit(self.top_image, (0,0))
        surf.blit(body,(0,self.top_image.get_height()))
        self.image = surf
        self.rect = self.image.get_rect(topleft = self.pos)

        portion = pygame.Rect(0,0,self.rect.width, self.always_visible)
        self.saved = self.image.subsurface(portion)
        self.toggle()

    def place_image(self,pos):
        self.pos = pos.copy()
        self.rect = self.image.get_rect(topleft = self.pos)
    def toggle(self):
        self.toggle_timer.activate()
        temp = self.image.copy()
        self.image = self.saved.copy()
        self.saved = temp
        self.rect = self.image.get_rect(topleft=self.pos)
    def update(self, dt):
        self.toggle_timer.update()
        if self.rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0] and not self.toggle_timer.active:
            self.toggle()


# Acts as the camera focus
class CameraDrone():
    def __init__(self, origin):
        self.pos = vector(origin)
# Moving ground/wall
class MovingTerrainHandler(pygame.sprite.Sprite):
    def __init__(self, groups, image, pos, direction, overlap=600, draw='fixed'):
        self.all_sprites = groups['all_group']
        self.group = groups
        super().__init__(self.all_sprites)
        self.z = LAYERS['cliff']
        self.draw = draw
        self.asset = image
        self.pos = vector(pos)
        self.image = None
        if direction == 'right':
            self.speed = vector(1000,0)
        if direction == 'left':
            self.speed = vector(-1000,0)
        if direction == 'up':
            self.speed = vector(0, -1000)
        if direction == 'down':
            self.speed = vector(0, 1000)
        self.direction = direction
        self.overlap = overlap

        self.terrains = []
        self.terrains.append(MovingTerrain(self.group, self.asset, pos,self.direction,self.draw))
    def move(self, dt):
        for terrain in self.terrains:
            terrain.pos.x += self.speed.x * dt
            terrain.rect.centerx = round(terrain.pos.x)

            terrain.pos.y += self.speed.y * dt
            terrain.rect.centery = round(terrain.pos.y)
            if self.draw == 'fixed':
                if self.direction == 'right':
                    if terrain.rect.left > WIDTH:
                        terrain.kill()
                        self.terrains.remove(terrain)
                    if terrain.rect.left > -100 and not terrain.called:
                        self.terrains.append(MovingTerrain(self.group, self.asset, terrain.pos - vector(terrain.rect.width-self.overlap,0),self.direction, self.draw))
                        terrain.called = True
                if self.direction == 'left':
                    if terrain.rect.right < 0:
                        terrain.kill()
                        self.terrains.remove(terrain)
                    if terrain.rect.right < WIDTH + 100 and not terrain.called:
                        self.terrains.append(MovingTerrain(self.group, self.asset, terrain.pos + vector(terrain.rect.width-self.overlap,0),self.direction, self.draw))
                        terrain.called = True
                if self.direction == 'up':
                    if terrain.rect.bottom < 0:
                        terrain.kill()
                        self.terrains.remove(terrain)
                    if terrain.rect.bottom < HEIGHT + 100 and not terrain.called:
                        self.terrains.append(MovingTerrain(self.group, self.asset, terrain.pos + vector(0,terrain.rect.height-self.overlap),self.direction, self.draw))
                        terrain.called = True
                if terrain.direction == 'down':
                    if terrain.rect.top > HEIGHT:
                        terrain.kill()
                        self.terrains.remove(terrain)
                    if terrain.rect.top > -100 and not terrain.called:
                        self.terrains.append(MovingTerrain(self.group, self.asset, terrain.pos - vector(0,terrain.rect.height-self.overlap),self.direction, self.draw))
                        terrain.called = True
            else:
                offset = self.all_sprites.store_offset
                if self.direction == 'right':
                    if terrain.rect.left + offset.x > WIDTH:
                        terrain.kill()
                        self.terrains.remove(terrain)
                    if terrain.rect.left + offset.x > -100 and not terrain.called:
                        self.terrains.append(MovingTerrain(self.group, self.asset, terrain.pos - vector(terrain.rect.width-self.overlap,0),self.direction, self.draw))
                        terrain.called = True
                if self.direction == 'left':
                    if terrain.rect.right + offset.x < 0:
                        terrain.kill()
                        self.terrains.remove(terrain)
                    if terrain.rect.right + offset.x < WIDTH + 500 and not terrain.called:
                        self.terrains.append(MovingTerrain(self.group, self.asset, terrain.pos + vector(terrain.rect.width-self.overlap,0),self.direction, self.draw))
                        terrain.called = True
                if self.direction == 'up':
                    if terrain.rect.bottom + offset.y < 0:
                        terrain.kill()
                        self.terrains.remove(terrain)
                    if terrain.rect.bottom + offset.y < HEIGHT + 100 and not terrain.called:
                        self.terrains.append(MovingTerrain(self.group, self.asset, terrain.pos + vector(0,terrain.rect.height-self.overlap),self.direction, self.draw))
                        terrain.called = True
                if terrain.direction == 'down':
                    if terrain.rect.top + offset.y > HEIGHT:
                        terrain.kill()
                        self.terrains.remove(terrain)
                    if terrain.rect.top + offset.y > -100 and not terrain.called:
                        self.terrains.append(MovingTerrain(self.group, self.asset, terrain.pos - vector(0,terrain.rect.height-self.overlap),self.direction, self.draw))
                        terrain.called = True
    def update(self, dt):
        self.move(dt)
class MovingTerrain(pygame.sprite.Sprite):
    def __init__(self, groups, image, pos, direction, draw='fixed'):
        self.group = groups
        super().__init__(groups['all_group'])
        self.z = LAYERS['cliff']
        self.draw = draw

        self.pos = vector(pos)
        self.image = image
        self.rect = self.image.get_rect(center = pos)

        if direction == 'right':
            self.speed = vector(1000,0)
        if direction == 'left':
            self.speed = vector(-1000,0)
        if direction == 'up':
            self.speed = vector(0, -1000)
        if direction == 'down':
            self.speed = vector(0, 1000)
        self.direction = direction
        self.overlap = 200
        self.called = False

# Plug in the kinematic variables, amd it'll do the rest
class ProblemSolver():
    def __init__(self, yf = None, y0 = None, vf = None, v0 = None, a = None, t = None, vx = None, xf = None, x0 = None, tx = None):
        self.yf = yf
        self.y0 = y0
        self.vf = vf
        self.v0 = v0
        self.a = a
        self.t = t

        # horizontal only
        self.vx = vx
        self.xf = xf
        self.x0 = x0
        self.tx = tx
    def find_t(self):
        if self.given([self.vf, self.v0, self.a]):
            self.t =  (self.vf - self.v0) / self.a
        elif self.given([self.yf, self.y0, self.vf, self.v0]):
            self.t = (2 * (self.yf - self.y0)) / (self.vf + self.v0)
        elif self.given([self.v0, self.yf, self.y0, self.a]):
            #could provide inaccurate results. be sure.
            t1 = (-1 * self.v0 + math.sqrt(self.v0**2 + 2 * self.a * (self.yf - self.y0))) / self.a
            t2 = (-1 * self.v0 - math.sqrt(self.v0 ** 2 + 2 * self.a * (self.yf - self.y0))) / self.a
            self.t = max(t1,t2)
    def find_v0(self):
        if self.given([self.yf, self.y0, self.t, self.a]):
            self.v0 = ((self.yf - self.y0) - ((self.a * self.t**2) / 2)) / self.t
        elif self.given([self.vf, self.yf, self.y0, self.t]):
            self.v0 = ((2 * (self.yf - self.y0)) / self.t) - self.vf
        elif self.given([self.vf, self.t, self.a]):
            self.v0 = self.vf - self.a * self.t
        elif self.given([self.vf, self.yf, self.y0, self.a]):
            #problematic one, technically +/-
            self.v0 = math.sqrt(self.vf**2 - (2*self.a * (self.yf - self.y0)))
    def find_vf(self):
        if self.given([self.v0, self.yf, self.y0, self.t]):
            self.vf = ((2 * (self.yf - self.y0)) / self.t) - self.v0
        elif self.given([self.v0, self.t, self.a]):
            self.vf = self.v0 + self.a * self.t
        elif self.given([self.v0, self.yf, self.y0, self.a]):
            #problematic one, technically +/-
            self.vf = math.sqrt(self.v0**2 + (2*self.a * (self.yf - self.y0)))
    def find_y0(self):
        if self.given([self.yf, self.v0, self.t, self.a]):
            self.y0 = self.yf - self.v0 * self.t - ((self.a * self.t**2)/2)
        elif self.given([self.yf, self.v0, self.vf, self.t]):
            self.y0 = self.yf - ((self.v0 + self.vf) / 2) * self.t
        elif self.given([self.yf, self.vf, self.v0, self.a]):
            self.y0 = self.yf - ((self.vf**2 - self.v0**2) / (2 * self.a))
    def find_yf(self):
        if self.given([self.y0, self.v0, self.t, self.a]):
            self.yf = self.y0 + self.v0 * self.t + ((self.a * self.t**2)/2)
        elif self.given([self.y0, self.v0, self.vf, self.t]):
            self.yf = self.y0 + ((self.v0 + self.vf) / 2) * self.t
        elif self.given([self.y0, self.vf, self.v0, self.a]):
            self.yf = self.y0 + ((self.vf**2 - self.v0**2) / (2 * self.a))
    def find_a(self):
        if self.given([self.yf, self.y0, self.v0, self.t]):
            self.a = (2 * ((self.yf - self.y0) - self.v0 * self.t)) / self.t**2
        elif self.given([self.vf, self.v0, self.yf, self.y0]):
            self.a = (self.vf**2 - self.v0**2) / (2 * (self.yf - self.y0))
        elif self.given([self.vf, self.v0, self.t]):
            self.a = (self.vf - self.v0) / self.t
    def find_vx(self):
        if self.given([self.xf, self.x0, self.tx]):
            self.vx = (self.xf - self.x0) / self.tx
    def find_xf(self):
        if self.given([self.x0, self.vx, self.tx]):
            self.xf = self.x0 + (self.vx * self.tx)
    def find_x0(self):
        if self.given([self.xf, self.vx, self.tx]):
            self.x0 = self.xf - (self.vx * self.tx)
    def find_tx(self):
        if self.given([self.xf, self.x0, self.vx]):
            self.tx = (self.xf - self.x0) / self.vx
    def feed_knowns(self, yf = None, y0 = None, vf = None, v0 = None, a = None, t = None, vx = None, xf = None, x0 = None, tx = None):
        self.yf = yf if self.yf is None else self.yf
        self.y0 = y0 if self.y0 is None else self.y0
        self.vf = vf if self.vf is None else self.vf
        self.v0 = v0 if self.v0 is None else self.v0
        self.a = a if self.a is None else self.a
        self.t = t if self.t is None else self.t

        # horizontal only
        self.vx = vx if self.vx is None else self.vx
        self.xf = xf if self.xf is None else self.xf
        self.x0 = x0 if self.x0 is None else self.x0
        self.tx = tx if self.tx is None else self.tx
    def given(self,values):
        return all(value is not None for value in values)
    def clear(self):
        self.y0 = None
        self.yf = None
        self.v0 = None
        self.vf = None
        self.a = None
        self.t = None

        self.vx = None
        self.xf = None
        self.x0 = None
        self.tx = None

# Progresses the story / game
class storyManager():
    def __init__(self, actions):
        self.actions = actions
        self.actions_index = 0
        self.progress_Timer = Timer(0)
        self.purge = False
        self.called = False
        self.ready = False
        self.calledTimer = False
    def reset(self):
        self.actions_index = 0
        self.progress_Timer = Timer(0)
        self.purge = False
        self.called = False
        self.ready = False
        self.calledTimer = False
    def update(self):
        self.progress_Timer.update()
        if self.actions_index < len(self.actions):
           self.actions[self.actions_index][0]() # calls function
           self.called = True
        if self.ready and not self.calledTimer:
            self.progress_Timer = Timer(self.actions[self.actions_index][1])  # sets up timer
            self.progress_Timer.activate()
            self.calledTimer = True
        if (self.calledTimer and not self.progress_Timer.active) or self.purge:
            self.actions_index += 1
            self.called = False
            self.calledTimer = False
            self.purge = False
        else:
            self.called = True
        self.ready = False




