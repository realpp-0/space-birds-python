import pygame
import pymunk
import random
import json
import os
import math
import sys

from core.camera import Camera
from ui.hud import draw_hud
from ui.end_screen import draw_end_screen
from core.score_manager import ScoreManager
from core.constants import *
import core.particle_manager as particle_manager





def main():
    # Set up the game window
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Space Birds")
    clock = pygame.time.Clock()
    gradient = pygame.Surface((WIDTH, HEIGHT))
    score_manager = ScoreManager()  # Initialize the ScoreManager
    
    for y in range(HEIGHT):

        t = y / HEIGHT

        r = int((1 - t) * 25 + t * 5)
        g = int((1 - t) * 15 + t * 5)
        b = int((1 - t) * 55 + t * 15)
        color = (r, g, b)
        pygame.draw.line(gradient, color, (0, y), (WIDTH, y))

    # Set up the physics space
    space = pymunk.Space()
    space.gravity = (0, 500)  # Gravity pointing downwards

    debug_font = pygame.font.SysFont('consolas', 16)

    
    win_sound = pygame.mixer.Sound(os.path.join("space-birds", "assets", "sounds", "win.wav"))
    lose_sound = pygame.mixer.Sound(os.path.join("space-birds", "assets", "sounds", "lose.wav"))


    from entities.birds.bird import create_bird

    birds = []

    def spawn_bird(count):
        if count > 0:

            variant = random.choice(['normal', 'quick', 'heavy', 'exploder'])
            #variant = 'quick'  # For testing, always spawn quick birds
            new_bird = create_bird(space, sling_pos, variant=variant)
            birds.append(new_bird)
            count -= 1
            print(count, bird_count)
            return new_bird, count
        return None, count

    def schedule_spawn():
        nonlocal spawn_reserved, spawn_timer, bird_count
        # reserve one bird now (don't create it yet) to avoid double-spawn
        if bird_count <= 0:
            return
        bird_count -= 1
        spawn_reserved += 1
        spawn_timer = SPAWN_DELAY
    
    
    spawn_reserved = 0
    spawn_timer = 0.0
    

    def attempt_launch(bird):
        if not bird.dragging:
            return
        drag_vec = (bird.body.position.x - bird.sling_pos[0], bird.body.position.y - bird.sling_pos[1])
        drag_dist = (drag_vec[0] ** 2 + drag_vec[1] ** 2) ** 0.5
        invalid_direction = (
            (launch_direction == 'right' and drag_vec[0] >= 0)
            or (launch_direction == 'left' and drag_vec[0] <= 0)
        )
        if drag_dist < MIN_LAUNCH_DISTANCE or invalid_direction:
            bird.body.position = bird.sling_pos
            bird.dragging = False
            return
        bird.release()
        # mark launch grace so spawn/camera logic won't react immediately
        try:
            bird.launched_time = motion_time
            bird.launch_grace_remaining = CAMERA_LAUNCH_GRACE
        except Exception:
            pass

    def _begin_ground_contact(arbiter, space_, data):
        for shape in arbiter.shapes:
            entity = getattr(shape, 'entity', None)
            if entity is None or not hasattr(entity, 'ground_contacts'):
                continue
            entity.ground_contacts += 1
            entity.on_ground = entity.ground_contacts > 0
        return True

    def _end_ground_contact(arbiter, space_, data):
        for shape in arbiter.shapes:
            entity = getattr(shape, 'entity', None)
            if entity is None or not hasattr(entity, 'ground_contacts'):
                continue
            entity.ground_contacts = max(0, entity.ground_contacts - 1)
            entity.on_ground = entity.ground_contacts > 0
        return True

    from entities.block import Block
    from entities.enemy import Enemy
    from entities.tnt import TNT
    from entities.ground import Ground

    def load_level(path):
        blocks = []
        enemies = []
        tnts = []
        ground_segments = []
        with open(path, 'r', encoding='utf-8') as handle:
            data = json.load(handle)
        for block_data in data.get('blocks', []):
            position = tuple(block_data.get('position', [0, 0]))
            size = tuple(block_data.get('size', [50, 50]))
            variant = block_data.get('variant', 'wood')
            blocks.append(Block(space, position, size=size, variant=variant))
        for enemy_data in data.get('enemies', []):
            position = tuple(enemy_data.get('position', [0, 0]))
            variant = enemy_data.get('variant', 'weak')
            enemies.append(Enemy(space, position, variant=variant))
        for tnt_data in data.get('tnts', []):
            position = tuple(tnt_data.get('position', [0, 0]))
            size = tuple(tnt_data.get('size', [30, 30]))
            variant = tnt_data.get('variant', 'small')
            tnts.append(TNT(space, position, size=size, variant=variant))
        for ground_data in data.get('ground_segments', []):
            a = tuple(ground_data.get('a', [-10000, 718]))
            b = tuple(ground_data.get('b', [10000, 718]))
            ground_segments.append(Ground(space, a, b))
        launch_direction = data.get('launch_direction', 'right')
        bird_count = data.get('bird_count', 5)
        sling_pos = data.get('sling_pos', [150, 460])
        idle_position = data.get('idle_position', [500, 500])
        idle_zoom = data.get('idle_zoom', 1.0)
        # Optional destruction focus for camera (near structure center)
        destruction_focus = data.get('destruction_focus', None)
        if destruction_focus is None:
            # compute a sensible default: average position of blocks/enemies/tnts
            pts = []
            for b in blocks:
                try:
                    pts.append(b.body.position)
                except Exception:
                    pass
            for e in enemies:
                try:
                    pts.append(e.body.position)
                except Exception:
                    pass
            for t in tnts:
                try:
                    pts.append(t.body.position)
                except Exception:
                    pass
            if pts:
                avgx = sum(p.x for p in pts) / len(pts)
                avgy = sum(p.y for p in pts) / len(pts)
                # bias slightly upward so destruction focus sits a bit above structure
                destruction_focus = (avgx, avgy - 40)
            else:
                destruction_focus = None
        return blocks, enemies, tnts, launch_direction, bird_count, sling_pos, idle_position, ground_segments, destruction_focus, idle_zoom

    # Level progression: read optional level index from argv
    LEVEL_COUNT = 8
    start_level = 1
    try:
        if len(sys.argv) > 1:
            start_level = max(1, min(LEVEL_COUNT, int(sys.argv[1])))
    except Exception:
        start_level = 1

    current_level = start_level
    levels_dir = os.path.join(os.path.dirname(__file__), 'levels')
    def load_level_index(idx):
        path = os.path.join(levels_dir, f'level_{idx}.json')
        return load_level(path)

    blocks, enemies, tnts, launch_direction, bird_count, sling_pos, idle_position, ground_segments, destruction_focus, idle_zoom = load_level_index(current_level)
    camera = Camera(WIDTH, HEIGHT, idle_position, idle_zoom)
    # provide the camera with the level's preferred destruction focus point
    try:
        camera.destruction_focus = destruction_focus
    except Exception:
        camera.destruction_focus = None
    active_bird, bird_count = spawn_bird(bird_count)
    enemies_destroyed = 0
    
    # Win/loss detection delay (seconds)
    winloss_check_delay = 0.0
    winloss_check_duration = 0.0
    game_ended = False
    resolution_pending = False
    resolution_focus = None
    # Level progression state
    awaiting_next_level = False
    level_lost = False
    level_won = False
    motion_time = 0.0

    def draw_entity_shape(shape):
        entity = getattr(shape, 'entity', None)
        body = getattr(shape, 'body', None)
        if body is None:
            return

        if entity is None:
            return

        if getattr(entity, 'variant', None) in {'normal', 'quick', 'heavy', 'exploder'}:
            colors = {
                'normal': (220, 20, 60),
                'quick': (255, 215, 0),
                'heavy': (120, 0, 0),
                'exploder': (70, 70, 70),
            }

            screen_pos = camera.world_to_screen(body.position)
            color = colors.get(entity.variant, (255, 255, 255))
            border_color = None
            if entity.variant == 'quick' and hasattr(entity, 'get_border_color'):
                border_color = entity.get_border_color()
            pygame.draw.circle(
                screen,
                color,
                (int(screen_pos[0]), int(screen_pos[1])),
                int(shape.radius * camera.zoom),
            )
            if border_color is not None:
                pygame.draw.circle(
                    screen,
                    border_color,
                    (int(screen_pos[0]), int(screen_pos[1])),
                    int(shape.radius * camera.zoom) + 4,
                    4,
                )
            pygame.draw.circle(
                screen,
                (255, 255, 255),
                (int(screen_pos[0]), int(screen_pos[1])),
                int(shape.radius * camera.zoom),
                2,
            )
            return

        if isinstance(entity, Block):
            if entity.variant == 'glass':
                color = (110, 180, 255)
            elif entity.variant == 'stone':
                color = (140, 140, 140)
            else:
                color = (120, 80, 40)
            if hasattr(shape, 'get_vertices'):
                try:
                    points = [body.local_to_world(v) for v in shape.get_vertices()]
                    points = [camera.world_to_screen(p) for p in points]
                    points = [(int(p[0]), int(p[1])) for p in points]
                    pygame.draw.polygon(screen, color, points)
                    pygame.draw.polygon(screen, (30, 30, 30), points, 2)
                except Exception:
                    pass
            else:
                screen_pos = camera.world_to_screen(body.position)
                rect = pygame.Rect(
                    int(screen_pos[0] - entity.size[0] / 2),
                    int(screen_pos[1] - entity.size[1] / 2),
                    int(entity.size[0]),
                    int(entity.size[1]),
                )
                pygame.draw.rect(screen, color, rect)
            return

        if isinstance(entity, Enemy):
            screen_pos = camera.world_to_screen(body.position)

            if entity.variant == 'weak':
                color = (140, 235, 140)
            elif entity.variant == 'medium':
                color = (80, 200, 80)
            else:
                color = (30, 150, 30)
            pygame.draw.circle(screen, color, (int(screen_pos[0]), int(screen_pos[1])), int(shape.radius * camera.zoom))
            pygame.draw.circle(screen, (255, 255, 255), (int(screen_pos[0]), int(screen_pos[1])), int(shape.radius * camera.zoom), 2)
        
        if isinstance(entity, TNT):
            
            if entity.variant == 'small':
                color = (255, 100, 100)
            elif entity.variant == 'medium':
                color = (200, 50, 50)
            else:
                color = (150, 0, 0)
            if hasattr(shape, 'get_vertices'):
                try:
                    points = [body.local_to_world(v) for v in shape.get_vertices()]
                    points = [camera.world_to_screen(p) for p in points]
                    points = [(int(p[0]), int(p[1])) for p in points]
                    pygame.draw.polygon(screen, color, points)
                    pygame.draw.polygon(screen, (30, 30, 30), points, 2)
                except Exception:
                    pass
            else:
                rect = pygame.Rect(
                    int(body.position.x - entity.size[0] / 2),
                    int(body.position.y - entity.size[1] / 2),
                    int(entity.size[0]),
                    int(entity.size[1]),
                )
                pygame.draw.rect(screen, color, rect)

        
        
        

    def draw_world():
        
        for ground in ground_segments:
            a = camera.world_to_screen(ground.a)
            b = camera.world_to_screen(ground.b)
            pygame.draw.line(screen, (80, 80, 80), (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), 5)

        particle_manager.update_particles(1 / FPS, screen, camera)  # Update and draw particles
            
        # draw trails for birds first (so trails sit behind entities)
        for b in birds:
            if getattr(b, 'trail_points', None) and getattr(b, 'removed', False) is False:
                pts = [camera.world_to_screen(p) for p in b.trail_points]
                if len(pts) >= 2:
                    # draw fading circles from oldest to newest
                    total = len(pts)
                    for i, p in enumerate(pts):
                        alpha_factor = (i + 1) / total
                        radius = max(1, int(3 * alpha_factor))
                        # choose color: quick mode overrides
                        color = (255, 255, 255)
                        if getattr(b, 'variant', None) == 'quick' and hasattr(b, 'get_border_color'):
                            bc = b.get_border_color()
                            if bc is not None:
                                color = bc
                            else:
                                color = (255, 215, 0)
                        else:
                            mapping = {
                                'normal': (220, 20, 60),
                                'quick': (255, 215, 0),
                                'heavy': (120, 0, 0),
                                'exploder': (70, 70, 70),
                            }
                            color = mapping.get(getattr(b, 'variant', None), (255, 255, 255))
                        pygame.draw.circle(screen, color, (int(p[0]), int(p[1])), radius)

        for shape in list(getattr(space, 'shapes', [])):
            if getattr(shape, 'body', None) is None:
                continue
            entity = getattr(shape, 'entity', None)
            if entity is None:
                continue
            if getattr(entity, 'removed', False) or getattr(entity, 'exploded', False):
                continue
            draw_entity_shape(shape)

        # Draw launch trajectory for the active bird while dragging
        try:
            if active_bird is not None and getattr(active_bird, 'dragging', False):
                # simulate simple trajectory up to 1 second using launch vector
                start = active_bird.body.position
                dx = start.x - active_bird.sling_pos[0]
                dy = start.y - active_bird.sling_pos[1]
                init_vx = -dx * active_bird.launch_boost
                init_vy = -dy * active_bird.launch_boost
                # gravity from space
                gx, gy = space.gravity
                t = 0.0
                pts = []
                while t <= 1.0:
                    x = start.x + init_vx * t + 0.5 * gx * t * t
                    y = start.y + init_vy * t + 0.5 * gy * t * t
                    pts.append((x, y))
                    t += TRAJECTORY_DT
                for p in pts:
                    sp = camera.world_to_screen(p)
                    pygame.draw.circle(screen, (200, 200, 200), (int(sp[0]), int(sp[1])), 3)
        except Exception:
            pass


    def draw_debug_overlay():
        # Show debug info even if no active bird exists
        DEBUG = False
        if DEBUG:
            bird = active_bird
            if bird is not None:
                try:
                    speed = (bird.body.velocity.x ** 2 + bird.body.velocity.y ** 2) ** 0.5
                except Exception:
                    speed = 0.0
                stats = [
                    f"Bird: {bird.variant}",
                    f"Mass: {bird.mass:.2f}",
                    f"Radius: {bird.radius}",
                    f"Launch boost: {bird.launch_boost}",
                    f"Speed: {speed:.1f} px/s",
                ]
            else:
                stats = [
                    f"Bird: (none)",
                    f"Mass: -",
                    f"Radius: -",
                    f"Launch boost: -",
                    f"Speed: 0.0 px/s",
                ]
            # Add birds left and enemies destroyed to debug stats
            stats.append(f"Birds left: {bird_count}")
            stats.append(f"Enemies destroyed: {enemies_destroyed}")
            panel_x = WIDTH - 240
            panel_y = 20
            pygame.draw.rect(screen, (20, 20, 20), (panel_x, panel_y, 220, 95), border_radius=8)
            pygame.draw.rect(screen, (255, 255, 255), (panel_x, panel_y, 220, 95), 1, border_radius=8)
            for index, line in enumerate(stats):
                text = debug_font.render(line, True, (255, 255, 255))
                screen.blit(text, (panel_x + 10, panel_y + 10 + index * 15))

    def begin_destruction_view(focus_pos=None):
        # default hold for 2.5s so destruction and shake are visible
        camera.begin_destruction(duration=2.5, focus=focus_pos)

    def start_resolution_delay(focus_pos=None):
        nonlocal resolution_pending, resolution_focus, winloss_check_delay, winloss_check_duration
        if resolution_pending or game_ended:
            return
        resolution_pending = True
        resolution_focus = focus_pos
        winloss_check_delay = 0.0
        winloss_check_duration = 2.0
        begin_destruction_view(focus_pos)

    def finish_level(is_win):
        nonlocal game_ended, running, awaiting_next_level, level_won, level_lost
        if game_ended:
            return
        
        game_ended = True
        if is_win:
            awaiting_next_level = True
            level_won = True
            score_manager.add_score(bird_count * BIRD_SCORE)  # Add bonus score for remaining birds
            win_sound.play()
            
        else:
            lose_sound.play()
            level_lost = True

    # collision handler: apply damage = relative_velocity * 0.5
    def _post_solve_entity_collision(arbiter, space_, data):
        for shape in arbiter.shapes: 
            entity = getattr(shape, 'entity', None)
            if entity is None: 
                continue 
            other = arbiter.shapes[0] if arbiter.shapes[1] is shape else arbiter.shapes[1] 
            other_entity = getattr(other, 'entity', None)
            if other.body.body_type == pymunk.Body.STATIC:
                continue
            bx, by = shape.body.velocity 
            ox, oy = other.body.velocity
            rvx = bx - ox 
            rvy = by - oy 
            rel_vel = (rvx * rvx + rvy * rvy) ** 0.5 
            if rel_vel < 1: 
                continue

            bird_variant = getattr(entity, 'variant', None)
            bird_mass = getattr(entity, 'body', None).mass if getattr(entity, 'body', None) is not None else 1.0
            damage_multiplier = getattr(entity, 'damage_multiplier', 1.0)
            
            # Bird collision damage (higher)
            is_bird = bird_variant in {'normal', 'quick', 'heavy', 'exploder'}
            if is_bird:
                damage = (rel_vel / 4) * bird_mass * damage_multiplier * 0.42 * 5
            else:
                # Non-bird collision damage (lower, for enemies/blocks hitting things)
                damage = (rel_vel / 4) * bird_mass * NON_BIRD_COLLISION_DAMAGE

            if bird_variant == 'heavy' and other_entity is not None and hasattr(other_entity, 'take_damage') and callable(getattr(other_entity, 'take_damage')):

                vx, vy = entity.body.velocity
                speed = (vx**2 + vy**2) ** 0.5
                other.body.velocity *= 0.4

                if speed > 0:
                    nx = vx / speed
                    ny = vy / speed

                    entity.body.apply_impulse_at_world_point(
                        (nx * 200, ny * 200),
                        entity.body.position
                    )

                    damage *= 2

            if bird_variant == 'quick' and hasattr(entity, 'get_collision_damage_multiplier'):
                # scale the bird-side damage according to quick mode multiplier
                collision_mult = entity.get_collision_damage_multiplier() / max(getattr(entity, 'damage_multiplier', 1.0), 0.0001)
                damage *= collision_mult

            # Apply damage to the colliding entity (e.g., bird)
            if hasattr(entity, 'take_damage') and callable(getattr(entity, 'take_damage')):
                try:
                    entity.take_damage(damage, score_manager)
                except Exception:
                    pass

            # Apply damage to the other entity (block/enemy) at reduced rate
            if other_entity is not None and hasattr(other_entity, 'take_damage') and callable(getattr(other_entity, 'take_damage')):
                if is_bird:
                    other_damage = (rel_vel / 4) * bird_mass * BIRD_TARGET_DAMAGE * damage_multiplier
                    if bird_variant == 'quick' and hasattr(entity, 'get_structure_damage_multiplier'):
                        structure_mult = entity.get_structure_damage_multiplier()
                        other_damage *= structure_mult
                else:
                    # Reduced damage for blocks/enemies being hit by other non-bird bodies
                    other_damage = (rel_vel / 4) * shape.body.mass * NON_BIRD_TARGET_DAMAGE
                try:
                    other_entity.take_damage(other_damage, score_manager)
                except Exception:
                    pass

            if bird_variant == 'exploder' and rel_vel > 300 and not getattr(entity, 'exploded', False):
                try:
                    entity.explode()
                except Exception:
                    pass
                try:
                    # exploder explosion has a noticeable shake
                    camera.shake(24.0, 0.6)
                except Exception:
                    pass
                if entity in birds:
                    birds.remove(entity)

        return True

    space.on_collision(Block.COLLISION_TYPE, 0, post_solve=_post_solve_entity_collision)
    space.on_collision(Enemy.COLLISION_TYPE, 0, post_solve=_post_solve_entity_collision)
    space.on_collision(Block.COLLISION_TYPE, Enemy.COLLISION_TYPE, post_solve=_post_solve_entity_collision)
    space.on_collision(Ground.COLLISION_TYPE, 0, begin=_begin_ground_contact, separate=_end_ground_contact)
    space.on_collision(Ground.COLLISION_TYPE, Block.COLLISION_TYPE, begin=_begin_ground_contact, separate=_end_ground_contact)
    space.on_collision(Ground.COLLISION_TYPE, Enemy.COLLISION_TYPE, begin=_begin_ground_contact, separate=_end_ground_contact)

    # Game loop
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 1 / 30.0)  # Limit the maximum delta time to avoid instability
        

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_world = camera.screen_to_world(event.pos)
                if active_bird is None:
                    # try to pick up an unlaunched bird at the sling
                    picked = None
                    for b in birds:
                        if getattr(b, 'launched', False):
                            continue
                        try:
                            dx = mouse_world[0] - b.body.position.x
                            dy = mouse_world[1] - b.body.position.y
                            dist = (dx * dx + dy * dy) ** 0.5
                            if dist <= getattr(b, 'radius', 20):
                                picked = b
                                break
                        except Exception:
                            continue
                    if picked is not None:
                        active_bird = picked
                        active_bird.try_grab(mouse_world)
                else:
                    active_bird.try_grab(mouse_world)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if active_bird is not None:
                    attempt_launch(active_bird)
                    camera.set_follow_target(active_bird)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                if active_bird is not None and getattr(active_bird, 'variant', None) == 'exploder' and active_bird.launched and not getattr(active_bird, 'exploded', False):
                    blast_focus = None
                    if active_bird.body is not None:
                        blast_focus = (active_bird.body.position.x, active_bird.body.position.y)
                    active_bird.explode()
                    begin_destruction_view(blast_focus)
                    if active_bird in birds:
                        birds.remove(active_bird)
                    active_bird = None

                    if bird_count > 0:
                        schedule_spawn()
                # If awaiting next level, render a persistent overlay and skip updates
            # Advance to next level when Enter is pressed after winning
            elif event.type == pygame.KEYDOWN and (event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER):
                if awaiting_next_level and level_won:
                    # compute next level index
                    try:
                        next_level = current_level + 1
                    except Exception:
                        next_level = 2
                    if next_level > LEVEL_COUNT:
                        # no more levels; quit
                        running = False
                    else:
                        # restart the process with next level index to get a clean state
                        python = sys.executable
                        os.execv(python, [python, __file__, str(next_level)])

            
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                # restart the current level
                python = sys.executable
                os.execv(python, [python, __file__, str(current_level)])

        # If awaiting next level, render a persistent overlay and skip updates
        if awaiting_next_level:
            
            screen.fill((0, 0, 0))
            screen.blit(gradient, (0, 0))
            
            draw_world()
            draw_hud(screen, current_level, bird_count, len(enemies), score_manager.score)
            draw_end_screen(screen, level_won, bird_count, score_manager.score)

            pygame.display.flip()
            # Skip the rest of the frame, keep waiting for Enter
            continue

        if not awaiting_next_level and level_lost:
            # Level lost, show end screen and wait for exit

            screen.fill((0, 0, 0))
            screen.blit(gradient, (0, 0))
            draw_world()
            draw_hud(screen, current_level, bird_count, len(enemies), score_manager.score)
            draw_end_screen(screen, level_won, bird_count, score_manager.score)

            pygame.display.flip()
            continue

        # Update birds and spawn new ones when allowed
        for current_bird in birds[:]:
            speed = (current_bird.body.velocity.x ** 2 + current_bird.body.velocity.y ** 2) ** 0.5
            x, y = current_bird.body.position
            offscreen = (
                x < -OFFSCREEN_MARGIN
                or x > WIDTH + OFFSCREEN_MARGIN
                or y < -OFFSCREEN_MARGIN
                or y > HEIGHT + OFFSCREEN_MARGIN
            )
                # Previously we auto-scheduled spawns when bird slowed; that logic
                # is removed to avoid spawning during destruction. Spawns are now
                # reserved and only created after the destruction camera completes.
            if current_bird.launched and (offscreen or speed <= BIRD_REMOVE_SPEED):
                removed_focus = None
                if current_bird.body is not None:
                    removed_focus = (current_bird.body.position.x, current_bird.body.position.y)
                # focus camera on level-defined destruction focus point and hold
                begin_destruction_view(destruction_focus)
                current_bird.remove()
                birds.remove(current_bird)
                if current_bird is active_bird:
                    active_bird = None
                    if bird_count > 0:
                        # reserve a spawn but do not create it until destruction cam ends
                        schedule_spawn()
                    else:
                        start_resolution_delay(removed_focus)

        if active_bird is not None and active_bird not in birds and bird_count > 0:
            # delay spawn when recovering active_bird to avoid snapping camera
            schedule_spawn()

        # remove destroyed blocks and enemies from lists before drawing
        for b in blocks[:]:
            if getattr(b, 'removed', False):
                try:
                    # subtle shake on block destruction
                    camera.shake(6.0, 0.18)
                except Exception:
                    pass
                blocks.remove(b)
        for e in enemies[:]:
            if getattr(e, 'removed', False):
                try:
                    # slightly stronger shake on enemy destruction
                    camera.shake(8.0, 0.22)
                except Exception:
                    pass
                enemies.remove(e)
                enemies_destroyed += 1
                
        for t in tnts[:]:
            if getattr(t, 'removed', False):
                try:
                    # TNT explosion stronger shake if it exploded
                    if getattr(t, 'exploded', False):
                        camera.shake(18.0, 0.45)
                    else:
                        camera.shake(10.0, 0.25)
                except Exception:
                    pass
                tnts.remove(t)

        if not resolution_pending and bird_count <= 0 and not birds:
            start_resolution_delay(resolution_focus or (camera.last_focus_x, camera.last_focus_y))

        if not resolution_pending and len(enemies) == 0:
            start_resolution_delay(resolution_focus or (camera.last_focus_x, camera.last_focus_y))

        if resolution_pending:
            winloss_check_delay += dt
            if winloss_check_delay >= winloss_check_duration:
                finish_level(len(enemies) == 0)

        # Update dragging state for the active bird
        if active_bird is not None and active_bird.dragging:
            mouse_pos = camera.screen_to_world(pygame.mouse.get_pos())
            active_bird.update_drag(mouse_pos)

        # Snapshot bird speed before physics runs so quick bird can preserve momentum in special modes.
        for entity in birds:
            body = getattr(entity, 'body', None)
            if body is None:
                continue
            entity._pre_step_speed = (body.velocity.x ** 2 + body.velocity.y ** 2) ** 0.5

        # decrement any per-bird launch grace timers
        for b in birds:
            if hasattr(b, 'launch_grace_remaining'):
                try:
                    b.launch_grace_remaining = max(0.0, b.launch_grace_remaining - dt)
                except Exception:
                    b.launch_grace_remaining = 0.0

        # Update physics
        space.step(dt)
        motion_time += dt

        # Fake rolling friction: only damp entities while they are actually touching ground.
        for entity_list in (birds, blocks, enemies, tnts):
            for entity in entity_list:
                body = getattr(entity, 'body', None)
                if body is None or body.body_type != pymunk.Body.DYNAMIC:
                    continue
                if not getattr(entity, 'on_ground', False):
                    continue

                vx, vy = body.velocity
                body.velocity = (vx * ROLLING_FRICTION, vy)
                body.angular_velocity *= ROLLING_FRICTION

                if abs(body.velocity.x) < 1.0:
                    body.velocity = (0, body.velocity.y)
                if abs(body.angular_velocity) < 0.5:
                    body.angular_velocity = 0

        # Air drag and wind: only apply while airborne, and normal birds ignore both.
        wind_x = math.sin(motion_time * 0.7) * WIND_STRENGTH
        for entity_list in (birds, blocks, enemies, tnts):
            for entity in entity_list:
                body = getattr(entity, 'body', None)
                if body is None or body.body_type != pymunk.Body.DYNAMIC:
                    continue
                if getattr(entity, 'on_ground', False):
                    continue

                if getattr(entity, 'variant', None) == 'normal':
                    continue

                if getattr(entity, 'variant', None) == 'quick' and hasattr(entity, 'should_ignore_air_drag') and entity.should_ignore_air_drag():
                    continue

                vx, vy = body.velocity
                body.velocity = ((vx * AIR_DRAG) + (wind_x * dt), vy * AIR_DRAG)

        # Quick bird momentum preservation: in meteor/comet mode, collisions should not bleed speed much.
        for entity in birds:
            body = getattr(entity, 'body', None)
            if body is None or getattr(entity, 'variant', None) != 'quick':
                continue
            if not hasattr(entity, 'get_mode'):
                continue
            mode = entity.get_mode()
            if mode not in {'meteor', 'comet'}:
                continue
            pre_speed = getattr(entity, '_pre_step_speed', None)
            if pre_speed is None:
                continue
            current_vx = body.velocity.x
            current_vy = body.velocity.y
            current_speed = (current_vx ** 2 + current_vy ** 2) ** 0.5
            if current_speed <= 0:
                continue
            target_speed = max(current_speed, pre_speed * 0.985)
            scale = target_speed / current_speed
            body.velocity = (current_vx * scale, current_vy * scale)

        # Record trails for birds (after physics adjustments)
        for b in birds:
            body = getattr(b, 'body', None)
            if body is None or getattr(b, 'removed', False):
                continue
            try:
                b.trail_points.append((body.position.x, body.position.y))
                if len(b.trail_points) > TRAIL_MAX_POINTS:
                    b.trail_points.pop(0)
            except Exception:
                pass

        # Handle delayed spawns
        # Handle delayed reserved spawns, but only create them once camera finished destruction
        if spawn_reserved > 0:
            # only count down the timer when camera is idle (not showing destruction)
            if getattr(camera, 'state', None) == 'idle':
                spawn_timer -= dt
            if spawn_timer <= 0:
                for _ in range(spawn_reserved):
                    variant = random.choice(['normal', 'quick', 'heavy', 'exploder'])
                    new_bird = create_bird(space, sling_pos, variant=variant)
                    birds.append(new_bird)
                    # only auto-assign active_bird if camera is not holding a destruction view
                    if active_bird is None and getattr(camera, 'state', None) != 'destruction':
                        active_bird = new_bird
                spawn_reserved = 0

        # Only keep following launched birds; idle birds should let the camera settle back naturally
        if active_bird is not None and active_bird.launched and getattr(active_bird, 'body', None) is not None:
            if camera.follow_target is not active_bird:
                camera.set_follow_target(active_bird)
        elif active_bird is None:
            camera.follow_target = None
        camera.update(dt)

        # Clear the screen
        screen.fill((0, 0, 0))
        screen.blit(gradient, (0, 0))

        draw_world()
        draw_debug_overlay()
        draw_hud(screen, current_level, bird_count, len(enemies), score_manager.score)

        # Update the display
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()