import pymunk
import os
import pygame
from core.constants import *
import core.particle_manager as particle_manager

pygame.mixer.init()  # Initialize the mixer module for sound playback
wood_break_sound = pygame.mixer.Sound(os.path.join(SOUNDS, "wood_break.wav"))
glass_break_sound = pygame.mixer.Sound(os.path.join(SOUNDS, "glass_break.wav"))
stone_break_sound = pygame.mixer.Sound(os.path.join(SOUNDS, "stone_break.wav"))


class Block:
    # collision type for blocks
    COLLISION_TYPE = 1
    
    VARIANTS = {
        # tuned for power scaling: wood < stone, glass breaks easily
        'wood': {'mass': 2, 'elasticity': 0.05, 'friction': 0.8, 'hp': 160},
        'glass': {'mass': 1, 'elasticity': 0.2, 'friction': 0.3, 'hp': 60},
        'stone': {'mass': 4, 'elasticity': 0.01, 'friction': 1.0, 'hp': 280},
    }

    def __init__(self, space, position, size=(50, 50), variant='wood'):
        self.space = space
        self.position = position
        self.size = size
        self.variant = variant if variant in self.VARIANTS else 'wood'

        props = self.VARIANTS[self.variant]

        self.body = pymunk.Body()
        self.body.position = position

        self.shape = pymunk.Poly.create_box(self.body, size)
        self.shape.mass = props['mass']
        self.shape.elasticity = props['elasticity']
        self.shape.friction = props['friction']
        # attach back-reference for collision handling
        self.shape.entity = self
        self.shape.collision_type = self.COLLISION_TYPE

        # hit points
        self.hp = props.get('hp', 10) * (self.size[0] * self.size[1]) / 3200

        self.glass_score = GLASS_SCORE
        self.wood_score = WOOD_SCORE
        self.stone_score = STONE_SCORE

        self.removed = False
        space.add(self.body, self.shape)
        self.on_ground = False
        self.ground_contacts = 0

    def remove(self):
        try:
            self.space.remove(self.body, self.shape)
        except Exception:
            pass
        self.removed = True

    def take_damage(self, amount, score_manager = None):
        self.hp -= amount
        if self.hp <= 0:
            if self.variant == 'wood':
                wood_break_sound.play()
                particle_manager.wood_particles(self.body.position)
                if score_manager is not None:
                    score_manager.add_score(self.wood_score)
            if self.variant == 'glass':
                particle_manager.glass_particles(self.body.position)
                glass_break_sound.play()
                if score_manager is not None:
                    score_manager.add_score(self.glass_score)
            if self.variant == 'stone':
                particle_manager.stone_particles(self.body.position)
                stone_break_sound.play()
                if score_manager is not None:
                    score_manager.add_score(self.stone_score)
            self.remove()
            return True
        return False

    def set_variant_props(self, mass=None, elasticity=None, friction=None):
        if mass is not None:
            self.shape.mass = mass
        if elasticity is not None:
            self.shape.elasticity = elasticity
        if friction is not None:
            self.shape.friction = friction