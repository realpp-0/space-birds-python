from .bird import Bird


class DefaultBird(Bird):
    VARIANT = "normal"
    PROPS = {
        "mass": 4,
        "radius": 20,
        "launch_boost": 10,
        "damage_multiplier": 1.0,
    }

    def get_variant_props(self):
        return self.PROPS
