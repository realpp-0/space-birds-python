import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(BASE_DIR, "assets")
SOUNDS = os.path.join(ASSETS, "sounds")
LEVELS = os.path.join(BASE_DIR, "levels")

WIDTH, HEIGHT = 1280, 760
FPS = 60

BIRD_REMOVE_SPEED = 5
TRAIL_MAX_POINTS = 40
TRAJECTORY_DT = 0.05

# Delay before auto-spawning the next bird (seconds)
SPAWN_DELAY = 1.5

# Small grace periods to avoid immediate spawn/camera changes right after launch
SPAWN_GRACE = 0.25

CAMERA_LAUNCH_GRACE = 0.35

MIN_LAUNCH_DISTANCE = 25
OFFSCREEN_MARGIN = 400

ROLLING_FRICTION = 0.786  # Tweak here: lower = stronger rolling friction, higher = less friction

AIR_DRAG = 0.992  # Tweak here: lower = stronger air drag, higher = less drag

WIND_STRENGTH = 18.0  # Tweak here: larger = stronger horizontal wind

NON_BIRD_COLLISION_DAMAGE = 0.05  # Tweak here: lower = weaker pig/block damage against each other

NON_BIRD_TARGET_DAMAGE = 0.03  # Tweak here: lower = weaker pig/block damage taken on impact

BIRD_TARGET_DAMAGE = 0.08  # Tweak here: higher = birds break blocks easier without changing bird-to-bird damage

GLASS_SCORE = 2500
WOOD_SCORE = 1000
STONE_SCORE = 5000
WEAK_PIG_SCORE = 10000
MEDIUM_PIG_SCORE = 15000
STRONG_PIG_SCORE = 20000
BIRD_SCORE = 50000
