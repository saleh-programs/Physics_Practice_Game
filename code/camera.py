import pygame
from pygame.math import Vector2 as vector
from random import randint
from functions import *
from objects import *
class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = vector()
        self.shake = False
        self.shake_time = 0
        self.shake_offset = vector()

        self.player = [None]
        self.player_offset = vector()
        self.store_offset = vector()
        self.scale = 1

        # clouds
        self.sky = pygame.image.load('../graphics/miscellaneous/sky.png')
        self.clouds = import_folder(f'../graphics/clouds')
        self.cloud_timer = Timer(1000)
        self.cloud_offset = vector()
        self.enable_clouds = False
    def create_clouds(self):
        for i in range(15):
            cloud_size = choice([randint(2,8),randint(2,13)]) / 10
            cloud_image = pygame.transform.scale_by(self.clouds[randint(0,3)], cloud_size)
            cloud_image = choice([cloud_image,pygame.transform.flip(cloud_image,True,False)])
            dimensions = (round(cloud_image.get_width()),round(cloud_image.get_height()))

            mapped_scalar = (cloud_size - .2) * ((.9-.3)/(1.3-.2)) + .3
            cloud_speed = 50 * mapped_scalar
            cloud_pos = vector(randint(-dimensions[0], WIDTH + dimensions[0]),randint(-dimensions[1],HEIGHT + dimensions[1]))

            Cloud(self,cloud_image,cloud_pos,cloud_speed,camera_link=self.player, z='clouds')
    def update_clouds(self):
        if (not self.cloud_timer.active):

            cloud_size = choice([randint(2,8),randint(2,13)]) / 10
            cloud_image = pygame.transform.scale_by(self.clouds[randint(0,3)], cloud_size)
            cloud_image = choice([cloud_image,pygame.transform.flip(cloud_image,True,False)])
            dimensions = (round(cloud_image.get_width()),round(cloud_image.get_height()))

            mapped_scalar = (cloud_size - .2) * ((.9-.3)/(1.3-.2)) + .3
            cloud_speed = 50 * mapped_scalar
            cloud_pos = vector(choice([randint(-dimensions[0] - 100, -dimensions[0]),randint(WIDTH+dimensions[0],WIDTH+dimensions[0]+100)]),randint(-dimensions[1], HEIGHT + dimensions[1] + 100))

            Cloud(self,cloud_image,cloud_pos,cloud_speed,camera_link=self.player, z='clouds')
            self.cloud_timer.activate()

    def shake_effect(self):
        self.shake = True
        self.shake_time = 1
    def scale_world(self, scale):
        self.scale = scale
        for sprite in self:
            if sprite.draw == 'camera' and (isinstance(sprite, Player) or isinstance(sprite, General)):
                if hasattr(sprite,'frames'):
                    for key, surf_list in sprite.graphic.items():
                        for i in range(len(surf_list)):
                            sprite.frames[key][i] = pygame.transform.scale_by(sprite.graphic[key][i].copy(),scale)
                    sprite.rect = sprite.frames[f'{sprite.status}_{sprite.orientation}'][int(sprite.frame_index)].get_rect(center = sprite.pos)
                    sprite.hitbox = sprite.rect.inflate(-10, 0)
                else:
                    sprite.image = pygame.transform.scale_by(sprite.graphic,scale)
                    sprite.rect = sprite.image.get_rect(center = sprite.pos)
    def draw(self, dt):
        if self.player[0]:
            focus = self.player[0].pos + self.player_offset
            self.offset = vector(round(WIDTH/2 - focus[0]), round(HEIGHT/2 - focus[1]))
            self.store_offset = self.offset.copy()
        if self.shake:
            if self.shake_time > 0:
                self.shake_offset = vector(randint(-80,80) * self.shake_time,randint(-80,80) * self.shake_time)
                self.offset += self.shake_offset
                self.shake_time -= 3 * dt
            else:
                self.shake = False
        if self.enable_clouds:
            self.display_surface.blit(self.sky,(0,0))
            self.update_clouds()
            self.cloud_timer.update()

        all_sprites = self.sprites()
        all_sprites.sort(key = lambda sprite: sprite.z)


        for sprite in all_sprites:
            if sprite.z == LAYERS['scale']:
                continue
            if isinstance(sprite, Circle):
                sprite.drawCircles(self.offset)
                continue
            if isinstance(sprite, TrailCircle):
                sprite.draw_circle(self.offset)
                continue
            if sprite.image:
                if isinstance(sprite, Balloon):
                    self.display_surface.blit(sprite.image, sprite.rect.topleft + self.offset)
                    sprite.draw_balloonstrings(self.offset)
                    continue
                if sprite.draw == 'fixed':
                    self.display_surface.blit(sprite.image, sprite.rect.topleft + self.shake_offset)
                if sprite.draw == 'camera':
                    self.display_surface.blit(sprite.image, sprite.rect.topleft + self.offset)


        self.offset = vector()


