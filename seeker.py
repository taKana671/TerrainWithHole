from enum import Enum, auto

from panda3d.core import BitMask32
from direct.actor.Actor import Actor
from panda3d.bullet import BulletCapsuleShape, ZUp
from panda3d.bullet import BulletSphereShape
from panda3d.bullet import BulletRigidBodyNode
from panda3d.core import PandaNode, NodePath, TransformState
from panda3d.core import Vec3, Point3
from direct.interval.IntervalGlobal import Sequence

from panda3d.core import RenderAttrib, AlphaTestAttrib, TransparencyAttrib


from constants import Config, Mask
from shapes.src import Sphere

class Motions(Enum):

    FORWARD = auto()
    BACKWARD = auto()
    LEFT = auto()
    RIGHT = auto()
    TURN = auto()

    UP = auto()
    DOWN = auto()


class Seeker(NodePath):

    RUN = 'run'
    WALK = 'walk'

    def __init__(self, world):
        super().__init__(BulletRigidBodyNode('wolker'))
        self.world = world
        self.test_shape = BulletSphereShape(0.5)
        self.moving_direction = 0
        self.vertical_direction = 0

        self.node().set_kinematic(True)
        self.node().set_ccd_motion_threshold(1e-7)
        self.node().set_ccd_swept_sphere_radius(0.5)

        self.set_collide_mask(BitMask32.bit(1))
       
        self.world.attach(self.node())

        self.direction_nd = NodePath(PandaNode('direction'))
        self.direction_nd.set_h(10)
        self.direction_nd.reparent_to(self)

        self.actor = base.loader.load_model('models/seeker/seeker')
        self.actor.set_scale(0.5)

        end, tip = self.actor.get_tight_bounds()
        size = tip - end  # size: LVector3f(0.994418, 0.999902, 1)
        # import pdb; pdb.set_trace()s
        shape = BulletSphereShape(size.z / 2)
        self.node().add_shape(shape)

        sphere_np = NodePath('sphere')
        sphere = Sphere(radius=0.2, segs_h=20, segs_v=20).create()
        sphere.reparent_to(sphere_np)
        sphere_np.set_color((0.68, 0.13, 0.13, 1))
        sphere.set_transparency(TransparencyAttrib.MAlpha)
        sphere_np.reparent_to(self.actor)
        # sphere_np.set_pos(0.2, 0.5, 0.8)
        sphere_np.set_pos(0, 0.5, 0.8)

        self.actor.reparent_to(self.direction_nd)
        self.speed = 8
        # Sequence(
        #     self.actor.posInterval(5, Point3(self.actor.get_x(), self.actor.get_y(), self.actor.get_z() + 0.1)),
        #     self.actor.posInterval(5, Point3(self.actor.get_x(), self.actor.get_y(), self.actor.get_z())),
        #     self.actor.posInterval(5, Point3(self.actor.get_x(), self.actor.get_y(), self.actor.get_z() - 0.1)),
        #     self.actor.posInterval(5, Point3(self.actor.get_x(), self.actor.get_y(), self.actor.get_z())),
        # ).loop()

    def navigate(self):
        """Return a relative point to enable camera to follow a character
           when camera's view is blocked by an object like walls.
        """
        return self.get_relative_point(self.direction_nd, Vec3(0, 8, 0))

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

    def predict_collision(self, current_pos, next_pos):
        ts_from = TransformState.make_pos(current_pos)
        ts_to = TransformState.make_pos(next_pos)

        if (result := self.world.sweep_test_closest(
                self.test_shape, ts_from, ts_to, BitMask32.bit(2) | BitMask32.bit(3), 0.0)).has_hit():

            return result

        # return result.has_hit()

    def check_upward(self, from_pos, mask=3):
        to_pos = from_pos + Vec3(0, 0, 1)

        if (hit := self.world.ray_test_closest(
                from_pos, to_pos, BitMask32.bit(mask))).has_hit():
            print(hit.get_node().get_name())
            hit_pos = hit.get_hit_pos()
            z = hit_pos.z - 1
            return z

        return None

    def check_downward(self, from_pos, distance=-1, mask=1):
        to_pos = from_pos + Vec3(0, 0, distance)

        if (hit := self.world.ray_test_closest(
                from_pos, to_pos, BitMask32.bit(mask))).has_hit():
            print(hit.get_node().get_name())
            hit_pos = hit.get_hit_pos()
            z = hit_pos.z + 1
            return z

        return None

    def detect_collision(self, np):
        if (result := self.world.contact_test_pair(self.node(), np.node())).get_num_contacts():
            for con in result.get_contacts():
                print(con.get_node1())
            return True

    def update(self, dt, motions):
        direction = Vec3()

        if Motions.LEFT in motions:
            direction.x += 1

        if Motions.RIGHT in motions:
            direction.x -= 1

        if Motions.FORWARD in motions:
            direction.y += 1

        if Motions.BACKWARD in motions:
            direction.y -= 1

        if Motions.UP in motions:
            direction.z += 1

        if Motions.DOWN in motions:
            direction.z -= 1

        self.turn(direction, dt)
        self.move(direction, dt)

    def turn(self, direction, dt):
        if direction.x:
            angle = 100 * direction.x * dt
            self.direction_nd.set_h(self.direction_nd.get_h() + angle)

    def move(self, direction, dt):
        # Not move, if direction is 0.
        if direction.yz == 0:
            return

        current_pos = self.get_pos()
        next_pos = current_pos + self.get_orientation() * direction.y * self.speed * dt
        next_pos.z += direction.z * self.speed * dt

        if z := self.check_upward(next_pos):
            next_pos.z = z

        if z := self.check_downward(next_pos):
            next_pos.z = z

        if result := self.predict_collision(current_pos, next_pos):
            print(result.get_node().get_name())

            if not result.get_node().get_name().startswith('terrain'):
                return
            
            if not self.check_downward(next_pos, distance=-10, mask=4):
                return

            




        speed = 8 if direction.y > 0 else 4
        speed = 10 if direction.z > 0 else 5
        # next_pos.z += direction.z * speed * dt

        z_diff = 1.5 if direction.z > 0 else -1.5
        # if self.vertical_check(next_pos, BitMask32.bit(1), z_diff):
        #     next_pos.z = current_pos.z


        self.set_pos(next_pos)


        # if not direction:
        #     return

        # speed = 10 if direction < 0 else 5
        # to_pos = self.get_pos() + self.get_orientation() * direction * speed * dt

        # if contact_pos := self.get_terrain_contact_pos(to_pos):
        #     next_pos = contact_pos + Vec3(0, 0, 1.5)

        #     if result := self.predict_collision(next_pos):
        #         if result.get_node() == base.scene.top_mountains.node():
        #             if self.get_terrain_contact_pos(to_pos, mask=3):
        #                 self.set_pos(next_pos)
        #     else:
        #         self.set_pos(next_pos)

        # #####################################################

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