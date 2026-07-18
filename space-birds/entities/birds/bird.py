import pymunk
import os
import pygame

pygame.mixer.init()  # Initialize the mixer module for sound playback
launch_sound = pygame.mixer.Sound(os.path.join("space-birds", "assets", "sounds", "launch.wav"))


class Bird:
    VARIANTS = {
        "normal": "default",
        "heavy": "heavy",
        "quick": "quick",
        "exploder": "exploder",
    }

    VARIANT = "normal"
    PROPS = {
        "mass": 4,
        "radius": 20,
        "launch_boost": 8,
    }
    DAMAGE_MULTIPLIER = 1.0

    def __init__(self, space, sling_pos, variant="normal", max_pull=100):
        self.space = space
        self.sling_pos = sling_pos
        self.variant = variant if variant in self.VARIANTS else "normal"
        self.max_pull = max_pull
        self._apply_variant_props()

        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = sling_pos
        self.body.moment = pymunk.moment_for_circle(self.mass, 0, self.radius)
        self.shape = pymunk.Circle(self.body, self.radius)
        self.shape.mass = self.mass
        if variant == 'heavy':
            self.shape.elasticity = 0.1
        else:
            self.shape.elasticity = 0.5
        self.shape.friction = 0.9

        try:
            self.shape.entity = self
        except Exception:
            pass

        space.add(self.body, self.shape)
        self.dragging = False
        self.launched = False
        self.spawned_next = False
        self.removed = False
        self.on_ground = False
        self.ground_contacts = 0
        # trail points for rendering (list of (x,y) tuples)
        self.trail_points = []

    def _apply_variant_props(self):
        props = self.get_variant_props()
        self.mass = props["mass"]
        self.radius = props["radius"]
        self.launch_boost = props["launch_boost"]
        self.damage_multiplier = props.get("damage_multiplier", self.DAMAGE_MULTIPLIER)

    def get_variant_props(self):
        return self.PROPS

    def remove(self):
        if getattr(self, 'removed', False) and self.body is None and self.shape is None:
            return
        self.removed = True
        body = self.body
        shape = self.shape
        try:
            if body is not None or shape is not None:
                self.space.remove(body, shape)
        except Exception:
            pass
        try:
            if shape is not None and shape in getattr(self.space, 'shapes', []):
                self.space.remove(shape)
        except Exception:
            pass
        try:
            if body is not None and body in getattr(self.space, 'bodies', []):
                self.space.remove(body)
        except Exception:
            pass
        try:
            if shape is not None:
                shape.entity = None
        except Exception:
            pass
        self.body = None
        self.shape = None
        # clear any trail data
        try:
            self.trail_points = []
        except Exception:
            pass

    def try_grab(self, mouse_pos):
        if self.launched:
            return False

        dx = mouse_pos[0] - self.body.position.x
        dy = mouse_pos[1] - self.body.position.y
        dist = (dx * dx + dy * dy) ** 0.5

        if dist <= self.shape.radius:
            self.dragging = True
            self.body.body_type = pymunk.Body.KINEMATIC
            self.body.velocity = (0, 0)
            self.body.angular_velocity = 0
            return True
        return False

    def update_drag(self, mouse_pos):
        if not self.dragging:
            return

        dx = mouse_pos[0] - self.sling_pos[0]
        dy = mouse_pos[1] - self.sling_pos[1]
        dist = (dx * dx + dy * dy) ** 0.5
        if dist > self.max_pull:
            scale = self.max_pull / dist
            dx *= scale
            dy *= scale
        self.body.position = (self.sling_pos[0] + dx, self.sling_pos[1] + dy)

    def release(self):
        if not self.dragging:
            return

        drag_vec = (self.body.position.x - self.sling_pos[0], self.body.position.y - self.sling_pos[1])
        vel = (-drag_vec[0] * self.launch_boost, -drag_vec[1] * self.launch_boost)
        self.body.body_type = pymunk.Body.DYNAMIC
        self.body.velocity = vel
        self.body.angular_velocity = 0
        self.dragging = False
        self.launched = True
        self.spawned_next = False
        launch_sound.play()
    def reset(self):
        try:
            self.space.remove(self.body, self.shape)
        except Exception:
            pass
        self.__init__(self.space, self.sling_pos, variant=self.variant, max_pull=self.max_pull)


def create_bird(space, sling_pos, variant="normal", max_pull=100):
    variant_name = variant if variant in Bird.VARIANTS else "normal"
    if variant_name == "quick":
        from .quick import QuickBird
        return QuickBird(space, sling_pos, variant=variant_name, max_pull=max_pull)
    if variant_name == "heavy":
        from .heavy import HeavyBird
        return HeavyBird(space, sling_pos, variant=variant_name, max_pull=max_pull)
    if variant_name == "exploder":
        from .exploder import ExploderBird
        return ExploderBird(space, sling_pos, variant=variant_name, max_pull=max_pull)
    from .default import DefaultBird
    return DefaultBird(space, sling_pos, variant=variant_name, max_pull=max_pull)
            