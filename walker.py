from enum import Enum, auto

from panda3d.core import BitMask32
from direct.actor.Actor import Actor
from panda3d.bullet import BulletCapsuleShape, ZUp
from panda3d.bullet import BulletSphereShape
from panda3d.bullet import BulletRigidBodyNode
from panda3d.core import PandaNode, NodePath, TransformState
from panda3d.core import Vec2, Vec3, Point3

# from constants import Config, Mask


class Motions(Enum):

    FORWARD = auto()
    BACKWARD = auto()
    LEFT = auto()
    RIGHT = auto()
    TURN = auto()


class Status(Enum):

    FIND_HOLE = auto()
    INTO_HOLE = auto()
    FALLING = auto()
    MOVE = auto()




class Walker(NodePath):

    RUN = 'run'
    WALK = 'walk'

    def __init__(self, world):
        super().__init__(BulletRigidBodyNode('wolker'))
        self.world = world
        self.test_shape = BulletSphereShape(0.5)
        self.destination_nd = None
        self.responded_sensor = None
        self.status = Status.MOVE

        h, w = 6, 1.2
        shape = BulletCapsuleShape(w, h - 2 * w, ZUp)
        self.node().add_shape(shape)
        self.node().set_kinematic(True)
        self.node().set_ccd_motion_threshold(1e-7)
        self.node().set_ccd_swept_sphere_radius(0.5)

        self.set_collide_mask(BitMask32.bit(1) | BitMask32.bit(5))
        self.set_scale(0.5)
        self.world.attach(self.node())

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
        # self.actor.set_scale(0.5)

        # mid terrain の待機場所
        # LPoint3f(-17.6692, 15.4803, -55.3163)

    def navigate(self):
        """Return a relative point to enable camera to follow a character
           when camera's view is blocked by an object like walls.
        """
        return self.get_relative_point(self.direction_nd, Vec3(0, 10, 2))
        # return self.get_relative_point(self.direction_nd, Vec3(0, 0, 5))

    def check_downward(self, from_pos, distance=-5, mask=1):
        to_pos = from_pos + Vec3(0, 0, distance)

        if (hit := self.world.ray_test_closest(
                from_pos, to_pos, BitMask32.bit(mask))).has_hit():
            # print(hit.get_node())
            return hit
        return None

    def get_orientation(self):
        return self.direction_nd.get_quat(base.render).get_forward()

    def predict_collision(self, current_pos, next_pos):
        ts_from = TransformState.make_pos(current_pos)
        ts_to = TransformState.make_pos(next_pos)

        if (result := self.world.sweep_test_closest(
                self.test_shape, ts_from, ts_to, BitMask32.bit(2) | BitMask32.bit(3), 0.0)).has_hit():

            return result

    def detect_collision(self, target_nd):
        if (result := self.world.contact_test_pair(
                self.node(), target_nd)).get_num_contacts():
            for con in result.get_contacts():
                # print(con.get_node1())
                return True

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

    def go_into_hole(self, dt):
        self.set_z(self.get_z() - 10 * dt)

        if self.detect_collision(self.responded_sensor.node()):
            return True

    def land(self, dt):
        current_pos = self.get_pos()
        next_pos = Point3(current_pos.xy, current_pos.z - 30 * dt)
        to_pos = next_pos + Vec3(0, 0, -3)

        if (hit := self.world.ray_test_closest(
                next_pos, to_pos, BitMask32.bit(1))).has_hit():
            self.set_z(hit.get_hit_pos().z + 1.5)
            return True

        self.set_pos(next_pos)

    def update(self, dt, key_inputs):
        motion = None
        match self.status:

            case Status.INTO_HOLE:
                if self.go_into_hole(dt):
                    self.status = Status.FALLING

            case Status.FALLING:
                if self.land(dt):
                    self.status = Status.MOVE

            case Status.MOVE:
                motion, direction = self.parse_args(key_inputs)
                self.turn(direction, dt)
                self.move(direction, dt)

        self.play_anim(motion)

    def turn(self, direction, dt):
        if direction.x:
            angle = 100 * direction.x * dt
            self.direction_nd.set_h(self.direction_nd.get_h() + angle)


    def move(self, direction, dt):
        if not direction.y:
            return

        speed = 10 if direction.y < 0 else 5
        current_pos = self.get_pos()
        next_pos = current_pos + self.get_orientation() * direction.y * speed * dt

        if hit := self.check_downward(next_pos):
            # if self.check_downward(next_pos, mask=5):
            if sensor := base.scene.check_terrain_hole(next_pos, -5):
                self.responded_sensor = sensor
                self.status = Status.INTO_HOLE


            next_pos.z = hit.get_hit_pos().z + 1.5

            if result := self.predict_collision(current_pos, next_pos):
                if not (result.get_node().get_name().startswith('terrain') and
                        self.check_downward(next_pos, distance=-10, mask=4)):
                    return

            self.set_pos(next_pos)

    def play_anim(self, motion):
        match motion:
            case Motions.FORWARD:
                anim = Walker.RUN
                rate = 1
            case Motions.BACKWARD:
                anim = Walker.WALK
                rate = -1
            case Motions.TURN:
                anim = Walker.WALK
                rate = 1
            case _:
                if self.actor.get_current_anim() is not None:
                    self.actor.stop()
                    self.actor.pose(Walker.WALK, 5)
                return

        if self.actor.get_current_anim() != anim:
            self.actor.loop(anim)

    def move2(self, direction, dt):
        if self.responded_sensor:

            self.set_z(self.get_z() - 20 * dt)

            # if self.detect_collision(self.destination_nd):
            # if self.detect_collision(self.responded_sensor):
            #     # import pdb; pdb.set_trace()
            #     self.responded_sensor = None
            return

        if not direction.y:
            return

        speed = 10 if direction.y < 0 else 5
        current_pos = self.get_pos()
        next_pos = current_pos + self.get_orientation() * direction.y * speed * dt

        if hit := self.check_downward(next_pos):
            if sensor := base.scene.check_terrain_hole(next_pos, -5):
                self.responded_sensor = sensor
                self.status = Status.SENSOR_RESPOND
                # walkerがsensorの高さより下になったらpassageに入ったとする。
                # censorクラスのインスタンスがリターンされるように、check_terrain_holeを修正した。
                # 落ちたら、カメラは穴の上まで動かし、

            next_pos.z = hit.get_hit_pos().z + 1.5

            if result := self.predict_collision(current_pos, next_pos):
                if not (result.get_node().get_name().startswith('terrain') and
                        self.check_downward(next_pos, distance=-10, mask=4)):
                    return

            self.set_pos(next_pos)
            self.actor.set_play_rate(rate, anim)