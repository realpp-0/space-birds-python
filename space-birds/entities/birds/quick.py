from .bird import Bird


class QuickBird(Bird):
    VARIANT = "quick"
    # Restore original (higher) speed thresholds — debugging values were lowered
    METEOR_SPEED = 1400
    COMET_SPEED = 1700
    METEOR_EXIT_SPEED = 1350
    COMET_EXIT_SPEED = 1650
    # Reduce damage multipliers so meteor/comet are powerful but not game-breaking
    METEOR_DAMAGE_MULTIPLIER = 2.0
    COMET_DAMAGE_MULTIPLIER = 3.0
    # Nerfed mode multipliers (less shredding) and slightly buffed base damage
    METEOR_STRUCTURE_MULTIPLIER = 1.2
    COMET_STRUCTURE_MULTIPLIER = 1.6
    PROPS = {
        "mass": 1.5,
        "radius": 16,
        "launch_boost": 15,
        "damage_multiplier": 1.40,
    }

    def get_variant_props(self):
        return self.PROPS

    def get_speed(self):
        if self.body is None:
            return 0.0
        return (self.body.velocity.x ** 2 + self.body.velocity.y ** 2) ** 0.5

    def get_mode_speed(self):
        # Use the larger of the current body speed and the pre-step snapshot
        # so collisions processed after a physics step still see the high
        # incoming speed for mode detection.
        speed = self.get_speed()
        pre = getattr(self, '_pre_step_speed', None)
        if pre is not None:
            return max(speed, pre)
        return speed

    def get_mode(self):
        speed = self.get_mode_speed()
        current_mode = getattr(self, "mode_state", None)

        # If we are touching ground, force-comet to end immediately
        if getattr(self, 'on_ground', False) and current_mode == 'comet':
            current_mode = None

        if current_mode == "comet":
            if speed <= self.COMET_EXIT_SPEED:
                current_mode = "meteor" if speed >= self.METEOR_SPEED else None
        elif current_mode == "meteor":
            if speed >= self.COMET_SPEED:
                current_mode = "comet"
            elif speed <= self.METEOR_EXIT_SPEED:
                current_mode = None
        else:
            if speed >= self.COMET_SPEED:
                current_mode = "comet"
            elif speed >= self.METEOR_SPEED:
                current_mode = "meteor"

        self.mode_state = current_mode
        return current_mode

    def get_collision_damage_multiplier(self):
        mode = self.get_mode()
        if mode == "meteor":
            return self.damage_multiplier * self.METEOR_DAMAGE_MULTIPLIER
        if mode == "comet":
            return self.damage_multiplier * self.COMET_DAMAGE_MULTIPLIER
        return self.damage_multiplier

    def get_structure_damage_multiplier(self):
        mode = self.get_mode()
        if mode == "meteor":
            return self.METEOR_STRUCTURE_MULTIPLIER
        if mode == "comet":
            return self.COMET_STRUCTURE_MULTIPLIER
        return 1.0

    def get_border_color(self):
        mode = self.get_mode()
        if mode == "meteor":
            return (255, 150, 0)
        if mode == "comet":
            return (70, 190, 255)
        return None

    def should_ignore_air_drag(self):
        return self.get_mode() == "comet"
