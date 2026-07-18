import os

import pymunk
import pygame

pygame.mixer.init()  # Initialize the mixer module for sound playback
explosion_sound = pygame.mixer.Sound(os.path.join(SOUNDS, "explosion.wav"))

from .bird import Bird


class ExploderBird(Bird):
    VARIANT = "exploder"
    PROPS = {
        "mass": 3,
        "radius": 18,
        "launch_boost": 11,
        "damage_multiplier": 0.8,
    }
    DAMAGE_SCALE = 0.0085
    KNOCKBACK_SCALE = 0.0075
    DAMAGE_RADIUS = 150
    KNOCKBACK_RADIUS = 350

    def __init__(self, space, sling_pos, variant="exploder", max_pull=100):
        super().__init__(space, sling_pos, variant=variant, max_pull=max_pull)
        self.exploded = False

    def get_variant_props(self):
        return self.PROPS

    def get_kinetic_energy(self):
        speed = (self.body.velocity.x ** 2 + self.body.velocity.y ** 2) ** 0.5
        return 0.5 * self.mass * speed * speed

    def explode(self):
        if self.exploded:
            return

        self.exploded = True
        explosion_sound.play()
        blast_x, blast_y = self.body.position.x, self.body.position.y
        self.body.velocity = (0, 0)
        self.body.angular_velocity = 0

        initial_energy = max(1.0, self.get_kinetic_energy())
        max_damage = 120.0 + initial_energy * self.DAMAGE_SCALE * self.damage_multiplier
        max_knockback = 350.0 + initial_energy * self.KNOCKBACK_SCALE * self.damage_multiplier

        for shape in list(getattr(self.space, "shapes", [])):
            body = getattr(shape, "body", None)
            if body is None or body is self.body:
                continue
            if body.body_type == pymunk.Body.STATIC:
                continue

            dx = body.position.x - blast_x
            dy = body.position.y - blast_y
            dist = (dx * dx + dy * dy) ** 0.5
            if dist <= 0:
                continue

            entity = getattr(shape, "entity", None)
            if dist <= self.DAMAGE_RADIUS:
                damage_falloff = 1.0 - (dist / self.DAMAGE_RADIUS)
                damage = max_damage * damage_falloff
                if entity is not None and hasattr(entity, "take_damage") and callable(getattr(entity, "take_damage")):
                    try:
                        entity.take_damage(damage * 7)
                    except Exception:
                        pass

            if dist <= self.KNOCKBACK_RADIUS:
                knockback_falloff = 1.0 - (dist / self.KNOCKBACK_RADIUS)
                knockback = max_knockback * knockback_falloff * 5
                nx = dx / dist
                ny = dy / dist
                if body.body_type == pymunk.Body.DYNAMIC:
                    body.apply_impulse_at_local_point((nx * knockback, ny * knockback), (0, 0))
                else:
                    body.velocity = (
                        body.velocity.x + nx * knockback,
                        body.velocity.y + ny * knockback,
                    )

        self.remove()