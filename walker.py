from enum import Enum, auto

from direct.actor.Actor import Actor
from panda3d.bullet import BulletCapsuleShape, ZUp
from panda3d.bullet import BulletSphereShape
from panda3d.bullet import BulletRigidBodyNode
from panda3d.core import PandaNode, NodePath, TransformState
from panda3d.core import Vec2, Vec3, BitMask32

from scene import Sensors


class Motions(Enum):

    FORWARD = auto()
    BACKWARD = auto()
    LEFT = auto()
    RIGHT = auto()
    TURN = auto()


class Status(Enum):

    FIND_HOLE = auto()
    FALLING = auto()
    MOVE = auto()
    IN_ROOM = auto()
    INTO_ROOM = auto()


class Walker(NodePath):

    RUN = 'run'
    WALK = 'walk'

    def __init__(self):
        super().__init__(BulletRigidBodyNode('wolker'))
        self.test_shape = BulletSphereShape(0.5)

        self.responded_sensor = None
        self.status = Status.MOVE

        h, w = 6, 1.2
        shape = BulletCapsuleShape(w, h - 2 * w, ZUp)
        self.node().add_shape(shape)
        self.node().set_kinematic(True)
        self.node().set_ccd_motion_threshold(1e-7)
        self.node().set_ccd_swept_sphere_radius(0.5)

        self.set_collide_mask(BitMask32.bit(6) | BitMask32.bit(7))
        self.set_scale(0.5)
        base.world.attach(self.node())

        self.direction_nd = NodePath(PandaNode('direction'))
        self.direction_nd.set_h(180)
        self.direction_nd.reparent_to(self)

        self.actor = Actor(
            'models/ralph/ralph.egg',
            {self.RUN: 'models/ralph/ralph-run.egg',
             self.WALK: 'models/ralph/ralph-walk.egg'}
        )
        self.actor.set_transform(TransformState.make_pos(Vec3(0, 0, -2.5)))
        self.actor.set_name('ralph')
        self.actor.reparent_to(self.direction_nd)

    def direction_relative_pos(self, pt):
        return self.get_relative_point(self.direction_nd, pt)

    def check_downward(self, from_pos, distance=-2.5):
        to_pos = from_pos + Vec3(0, 0, distance)
        mask = BitMask32.bit(1) | BitMask32.bit(3) | BitMask32.bit(6)

        if (hit := base.world.ray_test_closest(from_pos, to_pos, mask)).has_hit():
            return hit
        return None

    def predict_collision(self, current_pos, next_pos):
        ts_from = TransformState.make_pos(current_pos)
        ts_to = TransformState.make_pos(next_pos)
        mask = BitMask32.bit(2) | BitMask32.bit(3)

        if (result := base.world.sweep_test_closest(
                self.test_shape, ts_from, ts_to, mask, 0.0)).has_hit():
            return result

    def parse_args(self, key_inputs):
        direction = Vec2()
        motion = None

        if Motions.LEFT in key_inputs:
            direction.x += 1
            motion = Motions.TURN

        if Motions.RIGHT in key_inputs:
            direction.x -= 1
            motion = Motions.TURN

        if Motions.FORWARD in key_inputs:
            direction.y += -1
            motion = Motions.FORWARD

        if Motions.BACKWARD in key_inputs:
            direction.y += 1
            motion = Motions.BACKWARD

        return motion, direction

    def land(self, dt):
        if self.responded_sensor.dest_sensor.detect_collision(self.node()):
            self.responded_sensor = None
            return True

        self.set_z(self.get_z() - 20 * dt)

    def turn(self, direction, dt):
        if direction.x:
            angle = 100 * direction.x * dt
            self.direction_nd.set_h(self.direction_nd.get_h() + angle)

    def move(self, direction, dt):
        if not direction.y:
            return

        current_pos = self.get_pos()
        speed = 10 if direction.y < 0 else 5
        orientation = self.direction_nd.get_quat(base.render).get_forward()
        next_pos = current_pos + orientation * direction.y * speed * dt
        hit_z = None

        # Check a hole in the ground.
        if sensor := base.scene.check_sensors(current_pos, Sensors.HOLE.mask):
            # If a landing point is far, the character will fall into the hole.
            if not (sensor_hit := sensor.dest_sensor.respond(next_pos)):
                self.set_pos(next_pos)
                self.responded_sensor = sensor

                match self.responded_sensor.dest_sensor.location:
                    case Sensors.MID_GROUND.location:
                        self.status = Status.FALLING

                    case Sensors.STEPS.location:
                        self.status = Status.INTO_ROOM

                return

            hit_z = sensor_hit.get_hit_pos().z

        if not hit_z:
            if not (downward_hit := self.check_downward(next_pos)):
                return
            hit_z = downward_hit.get_hit_pos().z

        next_pos.z = hit_z + 1.5

        # Check whether the collision with terrain or other objects will occur or not.
        if self.predict_collision(current_pos, next_pos):
            # If no entrance or exit on the terrain, the character cannot move.
            if not base.scene.check_sensors(next_pos, Sensors.TUNNEL.mask):
                return

        self.set_pos(next_pos)

    def move_inside(self, direction, dt):
        if not direction.y:
            return

        current_pos = self.get_pos()
        speed = 10 if direction.y < 0 else 5
        orientation = self.direction_nd.get_quat(base.render).get_forward()
        next_pos = current_pos + orientation * direction.y * speed * dt

        if downward_hit := self.check_downward(next_pos):
            # Check whether the character will go outside or not.
            if base.scene.check_sensors(current_pos, Sensors.HOLE.mask):
                self.status = Status.MOVE

            hit_z = downward_hit.get_hit_pos().z
            next_pos.z = hit_z + 1.5

            # Check that the collision with walls or other objects in the room will occur.
            if self.predict_collision(current_pos, next_pos):
                return

            self.set_pos(next_pos)

    def play_anim(self, motion):
        match motion:

            case Motions.FORWARD:
                anim = Walker.RUN

            case Motions.BACKWARD:
                anim = Walker.WALK

            case Motions.TURN:
                anim = Walker.WALK

            case _:
                if self.actor.get_current_anim() is not None:
                    self.actor.stop()
                    self.actor.pose(Walker.WALK, 5)
                return

        if self.actor.get_current_anim() != anim:
            self.actor.loop(anim)

    def update(self, dt, key_inputs):
        motion, direction = self.parse_args(key_inputs)

        match self.status:

            case Status.FALLING:
                motion = None
                if self.land(dt):
                    self.status = Status.MOVE

            case Status.INTO_ROOM:
                motion = None
                if self.land(dt):
                    self.status = Status.IN_ROOM

            case Status.MOVE:
                self.turn(direction, dt)
                self.move(direction, dt)

            case Status.IN_ROOM:
                self.turn(direction, dt)
                self.move_inside(direction, dt)

        self.play_anim(motion)