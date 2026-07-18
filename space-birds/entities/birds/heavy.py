from .bird import Bird


class HeavyBird(Bird):
    VARIANT = "heavy"
    PROPS = {
        "mass": 16,
        "radius": 26,
        "launch_boost": 12,
        "damage_multiplier": 1.75,
    }

    def get_variant_props(self):
        return self.PROPS
