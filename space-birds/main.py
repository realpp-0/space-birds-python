import json
import os
import pygame
import pymunk
import pymunk.pygame_util

WIDTH = 1024
HEIGHT = 760
WINDOW_SIZE = (WIDTH, HEIGHT)
FPS = 60


def main():
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Space Birds")
    clock = pygame.time.Clock()

    space = pymunk.Space()
    space.gravity = (0, 500)

    from entities.bird import Bird

    SLING_POS = (250, HEIGHT - 150)

    birds = []

    def spawn_bird():
        new_bird = Bird(space, SLING_POS)
        birds.append(new_bird)
        return new_bird

    active_bird = spawn_bird()
    BIRD_RESPAWN_SPEED = 100
    BIRD_REMOVE_SPEED = 5

    ground = pymunk.Segment(space.static_body, (0, HEIGHT - 50), (WIDTH, HEIGHT - 50), 5)
    ground.elasticity = 0.8
    ground.friction = 0.8
    space.add(ground)
    
    from entities.block import Block
    from entities.enemy import Enemy

    def load_level(path):
        blocks = []
        enemies = []
        with open(path, 'r', encoding='utf-8') as handle:
            data = json.load(handle)
        for block_data in data.get('blocks', []):
            position = tuple(block_data.get('position', [0, 0]))
            size = tuple(block_data.get('size', [50, 50]))
            variant = block_data.get('variant', 'wood')
            blocks.append(Block(space, position, size=size, variant=variant))
        for enemy_data in data.get('enemies', []):
            position = tuple(enemy_data.get('position', [0, 0]))
            radius = enemy_data.get('radius', 18)
            hp = enemy_data.get('hp', 20)
            enemies.append(Enemy(space, position, radius=radius, hp=hp))
        return blocks, enemies

    levels_dir = os.path.join(os.path.dirname(__file__), 'levels')
    level_path = os.path.join(levels_dir, 'level_1.json')
    blocks, enemies = load_level(level_path)

    # collision handler: apply damage = relative_velocity * 0.5
    def _post_solve_entity_collision(arbiter, space_, data):
        for shape in arbiter.shapes:
            entity = getattr(shape, 'entity', None)
            if entity is None:
                continue
            other = arbiter.shapes[0] if arbiter.shapes[1] is shape else arbiter.shapes[1]
            if other.body.body_type == pymunk.Body.STATIC:
                continue
            bx, by = shape.body.velocity
            ox, oy = other.body.velocity
            rvx = bx - ox
            rvy = by - oy
            rel_vel = (rvx * rvx + rvy * rvy) ** 0.5
            if rel_vel < 1:
                continue
            damage = rel_vel * entity.body.mass * 0.5
            entity.take_damage(damage)
        return True

    space.on_collision(Block.COLLISION_TYPE, 0, post_solve=_post_solve_entity_collision)
    space.on_collision(Enemy.COLLISION_TYPE, 0, post_solve=_post_solve_entity_collision)

    draw_options = pymunk.pygame_util.DrawOptions(screen)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                active_bird.try_grab(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                active_bird.release()
            elif event.type == pygame.MOUSEMOTION and active_bird.dragging:
                active_bird.update_drag(event.pos)
        
        screen.fill((0, 0, 0))

        space.debug_draw(draw_options)
            
        dt = clock.tick(FPS) / 1000.0
        space.step(dt)

        for bird in birds[:]:
            speed = (bird.body.velocity.x ** 2 + bird.body.velocity.y ** 2) ** 0.5
            if bird.launched and not bird.spawned_next and speed < BIRD_RESPAWN_SPEED:
                active_bird = spawn_bird()
                bird.spawned_next = True
            if bird.launched and speed <= BIRD_REMOVE_SPEED:
                bird.remove()
                birds.remove(bird)
                if bird is active_bird:
                    active_bird = spawn_bird()

        if active_bird not in birds:
            active_bird = spawn_bird()

        pygame.display.flip()

        

    pygame.quit()


if __name__ == "__main__":
    main()
