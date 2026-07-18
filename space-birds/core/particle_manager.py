from core.particle import Particle
import random

particles = []


def spawn_particles(position, lifetime, radius, color, gravity, particle_count=10):

    for _ in range(particle_count):  # Create the specified number of particles for each break
        # Randomize the velocity for each particle
        rand_vel = (random.uniform(-100, 100), random.uniform(-100, 100))
        particle = Particle(position, rand_vel, lifetime, radius, color, gravity)
        particles.append(particle)

def update_particles(dt, screen, camera):

    for particle in particles[:]:

        alive = particle.update(dt)

        if not alive:
            particles.remove(particle)
        else:
            particle.draw(screen, camera)  # Assuming you have a camera object to convert world to screen coordinates

def glass_particles(position):
    spawn_particles(position, lifetime=1.5, radius=2, color=(0, 255, 255), gravity=200, particle_count=25)

def wood_particles(position):
    spawn_particles(position, lifetime=1.0, radius=3, color=(139, 69, 19), gravity=200, particle_count=15)

def stone_particles(position):
    spawn_particles(position, lifetime=2.0, radius=5, color=(128, 128, 128), gravity=200, particle_count=20)

def tnt_particles(position):
    color = random.choice([(255, 0, 0), (255, 165, 0), (255, 255, 0)])  # Randomly choose between red, orange, and yellow
    spawn_particles(position, lifetime=1.0, radius=4, color=color, gravity=300, particle_count=30)

def pig_particles(position):
    color = random.choice([(80, 220, 80), (40, 182, 40), (200, 255, 200)])  # Randomly choose between shades of green
    spawn_particles(position, lifetime=1.5, radius=6, color=color, gravity=200, particle_count=20)