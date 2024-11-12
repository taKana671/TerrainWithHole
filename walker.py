from enum import Enum, auto

from panda3d.core import BitMask32
from direct.actor.Actor import Actor
from panda3d.bullet import BulletCapsuleShape, ZUp
from panda3d.bullet import BulletSphereShape
from panda3d.bullet import BulletRigidBodyNode
from panda3d.core import PandaNode, NodePath, TransformState
from panda3d.core import Vec3

from constants import Config, Mask


class Motions(Enum):

    FORWARD = auto()
    BACKWARD = auto()
    LEFT = auto()
    RIGHT = auto()
    TURN = auto()


class Walker(NodePath):

    RUN = 'run'
    WALK = 'walk'

    def __init__(self, world):
        super().__init__(BulletRigidBodyNode('wolker'))
        self.world = world
        self.test_shape = BulletSphereShape(0.5)
        self.moving_direction = 0

        h, w = 6, 1.2
        shape = BulletCapsuleShape(w, h - 2 * w, ZUp)
        self.node().add_shape(shape)
        self.node().set_kinematic(True)
        self.node().set_ccd_motion_threshold(1e-7)
        self.node().set_ccd_swept_sphere_radius(0.5)

        self.set_collide_mask(Mask.terrain | Mask.sensor)
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

    def navigate(self):
        """Return a relative point to enable camera to follow a character
           when camera's view is blocked by an object like walls.
        """
        return self.get_relative_point(self.direction_nd, Vec3(0, 10, 2))

    def get_terrain_contact_pos(self, pos=None, mask=1):
        if not pos:
            pos = self.get_pos()

        below = pos - Vec3(0, 0, 30)
        # if (hit := self.world.ray_test_closest(
        #         pos, below, Mask.environment)).has_hit():
        if (hit := self.world.ray_test_closest(
                pos, below, BitMask32.bit(mask))).has_hit():
            return hit.get_hit_pos()

        return None

    def get_orientation(self):
        return self.direction_nd.get_quat(base.render).get_forward()

    def predict_collision(self, next_pos):
        ts_from = TransformState.make_pos(self.get_pos())
        ts_to = TransformState.make_pos(next_pos)
        # result = self.world.sweep_test_closest(self.test_shape, ts_from, ts_to, Mask.nature, 0.0)
        # result = self.world.sweep_test_closest(
        #     self.test_shape, ts_from, ts_to, BitMask32.bit(2) | BitMask32.bit(3), 0.0)
        result = self.world.sweep_test_closest(
            self.test_shape, ts_from, ts_to, BitMask32.bit(3), 0.0)

        if result.has_hit():
            return result

        # return result.has_hit()

    def detect_collision(self, np):
        if (result := self.world.contact_test_pair(self.node(), np.node())).get_num_contacts():
            for con in result.get_contacts():
                print(con.get_node1())
            return True

    def update(self, dt, motions):
        direction = 0
        angle = 0
        motion = None

        if Motions.LEFT in motions:
            angle += Config.angle * dt
            motion = Motions.TURN
        if Motions.RIGHT in motions:
            angle -= Config.angle * dt
            motion = Motions.TURN
        if Motions.FORWARD in motions:
            direction += Config.forward
            motion = Motions.FORWARD
        if Motions.BACKWARD in motions:
            direction += Config.backward
            motion = Motions.BACKWARD

        self.turn(angle)
        self.move(direction, dt)
        self.play_anim(motion)
        self.moving_direction = direction

    def turn(self, angle):
        if angle:
            self.direction_nd.set_h(self.direction_nd.get_h() + angle)

    def move(self, direction, dt):
        # Not move, if direction is 0.
        if not direction:
            return

        speed = 10 if direction < 0 else 5
        to_pos = self.get_pos() + self.get_orientation() * direction * speed * dt

        if contact_pos := self.get_terrain_contact_pos(to_pos):
            next_pos = contact_pos + Vec3(0, 0, 1.5)

            if result := self.predict_collision(next_pos):
                if result.get_node() == base.scene.terrain2.node(): 
                    if self.get_terrain_contact_pos(to_pos, mask=3):
                        self.set_pos(next_pos)
            else:
                self.set_pos(next_pos)

        # if contact_pos := self.get_terrain_contact_pos(to_pos):
        #     next_pos = contact_pos + Vec3(0, 0, 1.5)
        #     self.set_pos(next_pos)


            # if not self.predict_collision(next_pos):
            #     self.set_pos(next_pos)
        #     else:
        #         if self.get_terrain_contact_pos(to_pos, mask=3):
        #             self.set_pos(next_pos)

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
            self.actor.set_play_rate(rate, anim)