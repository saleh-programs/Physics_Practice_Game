import pygame
from pygame.math import Vector2 as vector
from os import walk
from objects import *

# This code is specifically for SAT collisions
# def isCollision(a,b):
#     cond1 = checkCollisionHelper(a,b)
#     cond2 = checkCollisionHelper(b,a)
#     collides = cond1[0] <= 0 and cond2[0] <= 0
#     if collides:
#         choice = cond1 if max(cond1[0],cond2[0]) == cond1[0] else cond2
#         return choice
#     else:
#         return 0
# def checkCollisionHelper(a,b):
#     separation = -100000000
#     contact_point = vector(0,0)
#     for i in range(len(a.points)):
#
#         minsep = 100000000
#         va = a.points[i].copy()
#         edge = a.points[(i+1) % len(a.points)].copy() - a.points[i].copy()
#         edgeMidpoint = va + edge/2
#
#         edgeNormal = edgeMidpoint - a.pos
#         if edgeNormal.magnitude() != 0:
#             edgeNormal /= edgeNormal.magnitude()
#
#         # pygame.draw.line(pygame.display.get_surface(),"red",edgeMidpoint,edgeMidpoint + edgeNormal*100)
#         for j in range(len(b.points)):
#             vb = b.points[j].copy()
#             vbvector = vb - va
#             projection = vbvector.dot(edgeNormal)
#             if projection < minsep:
#                 minsep = projection
#                 contact_pointTemp = vb.copy()
#         if (minsep > separation):
#             contact_point = contact_pointTemp.copy()
#             collisionNormal = edgeNormal.copy()
#             separation = minsep
#     return [separation,contact_point,collisionNormal]

#Create assets

# creates list of surfaces for animations
def import_folder(path):
    surface_list = []
    for folder_name, sub_folders, img_files in walk(path):
        for image_name in img_files:
            full_path = path + '/' + image_name
            image_surf = pygame.image.load(full_path).convert_alpha()
            # add image surface to surface list
            surface_list.append(image_surf)
    return surface_list

def store_sprites(all_sprites):
    sprites = [(sprite, sprite.groups()) for sprite in all_sprites]
    [sprite[0].kill() for sprite in sprites]
    return sprites
