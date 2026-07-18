import random


class Camera:

    def __init__(self, width, height, idle_position):
        self.x = 0
        self.y = 0

        self.width = width
        self.height = height

        self.zoom = 1

        self.target_x = 0
        self.target_y = 0
        self.target_zoom = 0.8

        self.state = "idle"

        self.idle_x, self.idle_y = idle_position
        self.follow_target = None
        self.last_focus_x = self.idle_x
        self.last_focus_y = self.idle_y
        
        # Deadzone settings (in world units)
        self.deadzone_x = 80
        self.deadzone_y = 60
        
        # Destruction view timer (seconds)
        self.destruction_timer = 0.0
        self.destruction_duration = 0.0
        self.return_timer = 0.0
        self.return_delay = 0.5
        # Screen shake state
        self.shake_timer = 0.0
        self.shake_duration = 0.0
        # magnitude in world units (stored); converted to pixels each frame
        self.shake_magnitude_world = 0.0
        # per-frame screen-space shake offsets (pixels)
        self.screen_shake_x = 0.0
        self.screen_shake_y = 0.0

    def world_to_screen(self, pos):
        sx = (pos[0] - self.x) * self.zoom + self.width / 2
        sy = (pos[1] - self.y) * self.zoom + self.height / 2
        # apply screen-space shake offset so it's visible regardless of camera movement
        sx += self.screen_shake_x
        sy += self.screen_shake_y
        return sx, sy

    def screen_to_world(self, pos):
        wx = (pos[0] - self.width / 2) / self.zoom + self.x
        wy = (pos[1] - self.height / 2) / self.zoom + self.y
        return wx, wy
    
    def update_idle(self):
        self.target_x = self.idle_x
        self.target_y = self.idle_y
        self.target_zoom = 1

    def update_follow(self):
        if self.follow_target is None:
            self.begin_destruction(duration=1.5)
            return
        
        try:
            bird = self.follow_target
            x = bird.body.position.x
            y = bird.body.position.y
            vx = bird.body.velocity.x
            vy = bird.body.velocity.y
            speed = (vx ** 2 + vy ** 2) ** 0.5
        except (AttributeError, TypeError):
            self.begin_destruction(duration=1.5)
            return

        if speed <= 300:
            # When a followed bird slows, transition into a focused destruction view
            # if a level-provided destruction focus is available; otherwise go idle.
            if hasattr(self, 'destruction_focus') and self.destruction_focus is not None:
                self.begin_destruction(duration=1.5, focus=self.destruction_focus)
            else:
                self.state = "idle"
            return
        
        zoom = 1.3 - speed / 1200
        zoom = max(0.75, min(1.3, zoom))

        # Calculate predictive position
        pred_x = x + vx * 0.25
        pred_y = y + vy * 0.25
        
        # Deadzone: only update target if outside deadzone
        dx = abs(pred_x - self.target_x)
        dy = abs(pred_y - self.target_y)
        
        if dx > self.deadzone_x or dy > self.deadzone_y:
            self.target_x = pred_x
            self.target_y = pred_y
            self.last_focus_x = pred_x
            self.last_focus_y = pred_y
        
        self.target_zoom = zoom

    def begin_destruction(self, duration=1.5, focus=None):
        """Show the destruction area before easing back to the sling."""
        if focus is not None:
            try:
                self.last_focus_x = focus[0]
                self.last_focus_y = focus[1]
            except (TypeError, IndexError):
                pass
        self.follow_target = None
        self.state = "destruction"
        self.destruction_timer = 0.0
        self.destruction_duration = duration
        self.return_timer = 0.0

    def update_destruction(self, dt):
        """Linger to show destruction aftermath before returning."""
        self.destruction_timer += dt
        self.target_x = self.last_focus_x
        self.target_y = self.last_focus_y
        self.target_zoom = 1.0  # Zoom out to 1x to see the full destruction
        
        if self.destruction_timer >= self.destruction_duration:
            self.state = "return"
    
    def update_return(self, dt):
        """Smoothly return to idle position."""
        self.follow_target = None
        self.return_timer += dt

        if self.return_timer < self.return_delay:
            self.target_x = self.last_focus_x
            self.target_y = self.last_focus_y
            self.target_zoom = 1.0
            return

        self.target_x = self.idle_x
        self.target_y = self.idle_y
        self.target_zoom = 1.0
        
        # Check if we've reached idle state (within threshold)
        dx = abs(self.x - self.idle_x)
        dy = abs(self.y - self.idle_y)
        dz = abs(self.zoom - 1.0)
        if dx < 5 and dy < 5 and dz < 0.01:
            self.state = "idle"
            self.x = self.idle_x
            self.y = self.idle_y
            self.zoom = 1.0
            self.return_timer = 0.0
        
    
    def update(self, dt):

        if self.state == "idle":
            self.update_idle()
        
        elif self.state == "follow":
            self.update_follow()
        
        elif self.state == "destruction":
            self.update_destruction(dt)
        
        elif self.state == "return":
            self.update_return(dt)
        
        elif self.state == "cinematic":
            self.update_cinematic()

        
        self.x += (self.target_x - self.x) * 5 * dt
        self.y += (self.target_y - self.y) * 5 * dt
        self.zoom += (self.target_zoom - self.zoom) * 5 * dt

        # Update screen-space shake
        if self.shake_timer > 0:
            self.shake_timer = max(0.0, self.shake_timer - dt)
            if self.shake_duration > 0:
                progress = self.shake_timer / max(1e-6, self.shake_duration)
            else:
                progress = 0.0
            # convert stored world-unit magnitude to pixels at current zoom
            magnitude_pixels = self.shake_magnitude_world * self.zoom
            current = magnitude_pixels * progress
            # random jitter each frame in screen pixels
            self.screen_shake_x = random.uniform(-1.0, 1.0) * current
            self.screen_shake_y = random.uniform(-1.0, 1.0) * current
            if self.shake_timer == 0.0:
                self.shake_magnitude_world = 0.0
                self.screen_shake_x = 0.0
                self.screen_shake_y = 0.0
        else:
            self.screen_shake_x = 0.0
            self.screen_shake_y = 0.0

    def shake(self, magnitude, duration=0.25):
        """Trigger a screen shake. Magnitude in world units, duration in seconds."""
        try:
            # store magnitude in world units; combine by taking max, extend duration
            self.shake_magnitude_world = max(self.shake_magnitude_world, magnitude)
            self.shake_duration = max(self.shake_duration, duration)
            self.shake_timer = max(self.shake_timer, duration)
        except Exception:
            pass

    def set_target(self, pos):
        """Set camera target position, safely handling None values."""
        if pos is not None:
            try:
                self.target_x = pos[0]
                self.target_y = pos[1]
                self.last_focus_x = pos[0]
                self.last_focus_y = pos[1]
            except (TypeError, IndexError):
                pass
    
    def set_follow_target(self, bird):
        """Set a bird to follow. Handles None gracefully."""
        if bird is not None:
            try:
                # Validate the bird has required attributes
                _ = bird.body.position
                self.follow_target = bird
                self.state = "follow"
                self.last_focus_x = bird.body.position.x
                self.last_focus_y = bird.body.position.y
            except (AttributeError, TypeError):
                self.begin_destruction()
        else:
            self.begin_destruction()
