import pymunk

class Ground:
    COLLISION_TYPE = 3

    def __init__(self, space, a, b):

        self.space = space        
        self.body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.a = a
        self.b = b

        self.shape = pymunk.Segment(self.body, a, b, 5)

        self.shape.elasticity = 0.6
        self.shape.friction = 0.6
        self.shape.collision_type = self.COLLISION_TYPE

        space.add(self.body, self.shape)

