import pymunk

class TNT:

    COLLISION_TYPE = 1

    VARIANTS = {
        'small': {'mass': 1, 'elasticity': 0.2, 'friction': 0.8, 'hp': 90, 'multiplier': 0.75},
        'medium': {'mass': 2, 'elasticity': 0.1, 'friction': 0.85, 'hp': 180, 'multiplier': 1.0},
    }

    def __init__(self, space, position, size=(30, 30), variant='small'):
        self.space = space
        self.position = position
        self.size = size
        self.variant = variant if variant in self.VARIANTS else 'small'

        props = self.VARIANTS[self.variant]

        self.body = pymunk.Body()
        self.body.position = position

        self.shape = pymunk.Poly.create_box(self.body, size)
        self.shape.mass = props['mass']
        self.shape.elasticity = props['elasticity']
        self.shape.friction = props['friction']
        self.shape.entity = self
        self.shape.collision_type = self.COLLISION_TYPE

        self.hp = props.get('hp', 10)

        self.removed = False
        self.exploded = False
        space.add(self.body, self.shape)
        self.on_ground = False
        self.ground_contacts = 0

    
    

    def remove(self):
        try:
            self.space.remove(self.body, self.shape)
        except Exception:
            pass
        self.removed = True

    def explode(self):
        if self.removed or self.exploded:
            return
        
        self.exploded = True

        blast_x, blast_y = self.body.position.x, self.body.position.y
        self.body.velocity = (0, 0)
        self.body.angular_velocity = 0

        max_damage = 140.0 * self.VARIANTS[self.variant]['multiplier']
        max_knockback = 350.0 * self.VARIANTS[self.variant]['multiplier']
        damage_radius = 140.0 * self.VARIANTS[self.variant]['multiplier']
        knockback_radius = 350.0 * self.VARIANTS[self.variant]['multiplier']

        for shape in list(getattr(self.space, "shapes", [])):
            body = getattr(shape, "body", None)
            if body is None or body is self.body:
                continue
            if body.body_type == pymunk.Body.STATIC:
                continue

            dx = body.position.x - blast_x
            dy = body.position.y - blast_y
            dist = (dx * dx + dy * dy) ** 0.5
            if dist <= 0:
                continue

            entity = getattr(shape, "entity", None)
            if dist <= damage_radius:
                damage_falloff = 1.0 - (dist / damage_radius)
                damage = max_damage * damage_falloff
                if entity is not None and hasattr(entity, "take_damage") and callable(getattr(entity, "take_damage")):
                    try:
                        entity.take_damage(damage)
                    except Exception:
                        pass

            if dist <= knockback_radius:  # Knockback radius
                knockback_falloff = 1.0 - (dist / knockback_radius)
                knockback = max_knockback * knockback_falloff
                nx = dx / dist
                ny = dy / dist
                if body.body_type == pymunk.Body.DYNAMIC:
                    body.apply_impulse_at_local_point((nx * knockback, ny * knockback), (0, 0))
                else:
                    body.velocity = (
                        body.velocity.x + nx * knockback,
                        body.velocity.y + ny * knockback,
                    )

        self.remove()

    def explode(self):
        if self.removed or self.exploded:
            return
        
        self.exploded = True

        blast_x, blast_y = self.body.position.x, self.body.position.y
        self.body.velocity = (0, 0)
        self.body.angular_velocity = 0

        max_damage = 175.0 * self.VARIANTS[self.variant]['multiplier']
        max_knockback = 260.0 * self.VARIANTS[self.variant]['multiplier']
        damage_radius = 130.0 * self.VARIANTS[self.variant]['multiplier']
        knockback_radius = 260.0 * self.VARIANTS[self.variant]['multiplier']

        for shape in list(getattr(self.space, "shapes", [])):
            body = getattr(shape, "body", None)
            if body is None or body is self.body:
                continue
            if body.body_type == pymunk.Body.STATIC:
                continue

            dx = body.position.x - blast_x
            dy = body.position.y - blast_y
            dist = (dx * dx + dy * dy) ** 0.5
            if dist <= 0:
                continue

            entity = getattr(shape, "entity", None)
            if dist <= damage_radius:
                damage_falloff = 1.0 - (dist / damage_radius)
                damage = max_damage * damage_falloff
                if entity is not None and hasattr(entity, "take_damage") and callable(getattr(entity, "take_damage")):
                    try:
                        entity.take_damage(damage * 7)
                    except Exception:
                        pass

            if dist <= knockback_radius:  # Knockback radius
                knockback_falloff = 1.0 - (dist / knockback_radius)
                knockback = max_knockback * knockback_falloff * 5
                nx = dx / dist
                ny = dy / dist
                if body.body_type == pymunk.Body.DYNAMIC:
                    body.apply_impulse_at_local_point((nx * knockback, ny * knockback), (0, 0))
                else:
                    body.velocity = (
                        body.velocity.x + nx * knockback,
                        body.velocity.y + ny * knockback,
                    )

        self.remove()


    def take_damage(self, amount):
        self.hp -= amount
        
        if self.hp <= 0:
            
            self.explode()
            return True
        return False
    
    def set_variant_props(self, mass=None, elasticity=None, friction=None):
        if mass is not None:
            self.shape.mass = mass
        if elasticity is not None:
            self.shape.elasticity = elasticity
        if friction is not None:
            self.shape.friction = friction

    