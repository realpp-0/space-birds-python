import pygame

class Particle:
    def __init__(self, position, velocity, lifetime, radius, color, gravity):
        self.position = position
        self.velocity = velocity
        self.lifetime = lifetime
        self.radius = radius
        self.color = color
        self.gravity = gravity

    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            return False  # Particle has expired

        # Update position based on velocity
        self.position = (self.position[0] + self.velocity[0] * dt,
                         self.position[1] + self.velocity[1] * dt)

        # Shrink the particle's radius over time
        self.radius = max(0, self.radius - dt * 5)  # Adjust the shrink rate as needed

        if self.radius <= 0:
            return False  # Particle has shrunk to nothing

        # Apply gravity to the velocity
        self.velocity = (self.velocity[0],
                         self.velocity[1] + self.gravity * dt)

        return True  # Particle is still alive

    def draw(self, screen, camera):
        if self.radius > 0:
            pos = camera.world_to_screen(self.position)
            pygame.draw.circle(screen, self.color, (int(pos[0]), int(pos[1])), int(self.radius))