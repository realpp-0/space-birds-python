import pymunk
import os
import pygame
from core.constants import *
import core.particle_manager as particle_manager

pygame.mixer.init()  # Initialize the mixer module for sound playback
pig_died_sound = pygame.mixer.Sound(os.path.join("space-birds", "assets", "sounds", "pig_death.wav"))


class Enemy:
    COLLISION_TYPE = 2
    

    VARIANTS = {
        'weak': {'radius': 18, 'mass': 3, 'hp': 150, 'elasticity': 0.2, 'friction': 0.6},
        'medium': {'radius': 22, 'mass': 4, 'hp': 230, 'elasticity': 0.18, 'friction': 0.6},
        'strong': {'radius': 28, 'mass': 5.5, 'hp': 340, 'elasticity': 0.15, 'friction': 0.6},
    }

    def __init__(self, space, position, variant='weak'):
        self.space = space
        self.position = position
        self.variant = variant if variant in self.VARIANTS else 'weak'
        props = self.VARIANTS[self.variant]

        self.weak_score = WEAK_PIG_SCORE
        self.medium_score = MEDIUM_PIG_SCORE
        self.strong_score = STRONG_PIG_SCORE

        self.radius = props['radius']
        self.mass = props['mass']
        self.hp = props['hp']
        self.elasticity = props['elasticity']
        self.friction = props['friction']

        self.body = pymunk.Body()
        self.body.position = position

        self.shape = pymunk.Circle(self.body, self.radius)
        self.shape.mass = self.mass
        self.shape.elasticity = self.elasticity
        self.shape.friction = self.friction
        self.shape.entity = self
        self.shape.collision_type = self.COLLISION_TYPE

        self.removed = False
        self.space.add(self.body, self.shape)
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
            pig_died_sound.play()
            particle_manager.pig_particles(self.body.position)
            if score_manager is not None:
                score_manager.add_score(getattr(self, f'{self.variant}_score'))  # Add score based on the variant of the enemy
            self.remove()
            return True
        return False