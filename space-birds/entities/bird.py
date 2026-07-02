import pymunk


class Bird:
    def __init__(self, space, sling_pos, radius=20, mass=4, max_pull=100, launch_speed=6):
        self.space = space
        self.sling_pos = sling_pos
        self.radius = radius
        self.mass = mass
        self.max_pull = max_pull
        self.launch_speed = launch_speed

        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = sling_pos
        self.shape = pymunk.Circle(self.body, radius)
        self.shape.mass = mass
        self.shape.elasticity = 0.5
        self.shape.friction = 0.9

        space.add(self.body, self.shape)

        self.dragging = False
        self.launched = False
        self.spawned_next = False

    def remove(self):
        try:
            self.space.remove(self.body, self.shape)
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
        vel = (-drag_vec[0] * self.launch_speed, -drag_vec[1] * self.launch_speed)
        self.body.body_type = pymunk.Body.DYNAMIC
        self.body.velocity = vel
        self.body.angular_velocity = 0
        self.dragging = False
        self.launched = True
        self.spawned_next = False

    def reset(self):
        # remove old body and create a fresh kinematic one at sling_pos
        try:
            self.space.remove(self.body, self.shape)
        except Exception:
            pass
        self.__init__(self.space, self.sling_pos, self.radius, self.mass, self.max_pull, self.launch_speed)
