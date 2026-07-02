import pymunk


class Enemy:
    COLLISION_TYPE = 2

    def __init__(self, space, position, radius=18, mass=3, hp=200, elasticity=0.2, friction=0.6):
        self.space = space
        self.position = position
        self.radius = radius
        self.mass = mass
        self.hp = hp
        self.elasticity = elasticity
        self.friction = friction

        self.body = pymunk.Body()
        self.body.position = position

        self.shape = pymunk.Circle(self.body, radius)
        self.shape.mass = mass
        self.shape.elasticity = elasticity
        self.shape.friction = friction
        self.shape.entity = self
        self.shape.collision_type = self.COLLISION_TYPE

        self.space.add(self.body, self.shape)

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
