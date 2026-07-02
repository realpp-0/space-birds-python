import pymunk


class Block:
    # collision type for blocks
    COLLISION_TYPE = 1

    VARIANTS = {
        'wood': {'mass': 2, 'elasticity': 0.05, 'friction': 0.8, 'hp': 300},
        'glass': {'mass': 1, 'elasticity': 0.2, 'friction': 0.3, 'hp': 100},
        'stone': {'mass': 4, 'elasticity': 0.01, 'friction': 1.0, 'hp': 600},
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
        self.hp = props.get('hp', 10)

        space.add(self.body, self.shape)

    def remove(self):
        try:
            self.space.remove(self.body, self.shape)
        except Exception:
            pass

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
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
