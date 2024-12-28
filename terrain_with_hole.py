import sys

from panda3d.bullet import BulletWorld, BulletDebugNode
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from direct.showbase.InputStateGlobal import inputState
from panda3d.core import load_prc_file_data
from panda3d.core import NodePath, Point3, Vec3, BitMask32, Quat

from walker import Walker, Motions, Status
from scene import Scene


load_prc_file_data("", """
    textures-power-2 none
    gl-coordinate-system default
    window-title Panda3D Test Terrain
    filled-wireframe-apply-shader true
    stm-max-views 8
    stm-max-chunk-count 2048""")


class TerrainWithHole(ShowBase):

    def __init__(self):
        super().__init__()
        self.disable_mouse()

        self.world = BulletWorld()
        self.world.set_gravity(Vec3(0, 0, -9.81))

        self.debug = self.render.attach_new_node(BulletDebugNode('debug'))
        self.world.set_debug_node(self.debug.node())

        self.scene = Scene()
        self.scene.root.reparent_to(self.render)

        self.walker = Walker()
        self.walker.reparent_to(self.render)
        self.walker.set_pos(Point3(-18.0243, 14.9644, -9.21977))
        self.floater = NodePath('floater')
        self.floater.set_z(3.0)
        self.floater.reparent_to(self.walker)

        self.camera.reparent_to(self.render)
        self.cam_distance = Vec3(0, -5, 1)
        self.camera.set_pos(self.walker.get_pos() + self.cam_distance)
        self.camera.look_at(self.floater)
        self.camLens.set_near_far(0.1, 10000)
        self.camLens.set_fov(90)

        self.state = False
        self.is_falling = False

        inputState.watch_with_modifiers('forward', 'arrow_up')
        inputState.watch_with_modifiers('backward', 'arrow_down')
        inputState.watch_with_modifiers('left', 'arrow_left')
        inputState.watch_with_modifiers('right', 'arrow_right')

        self.accept('u', self.go_down, [True])
        self.accept('shift-u', self.go_down, [False])
        self.accept('i', self.print_info)
        self.accept('escape', sys.exit)
        self.accept('d', self.toggle_debug)
        self.taskMgr.add(self.update, 'update')

    def go_down(self, is_down):
        direction = 1
        if is_down:
            direction *= -1
        z = self.walker.get_z() + direction
        self.walker.set_z(z)

    def print_info(self):
        print(self.walker.get_pos())

    def toggle_debug(self):
        # self.toggle_wireframe()
        if self.debug.is_hidden():
            self.debug.show()
        else:
            self.debug.hide()

    def ray_cast(self, from_pos, to_pos):
        mask = BitMask32.bit(2) | BitMask32.bit(3) | BitMask32.bit(7)

        if (result := self.world.ray_test_closest(from_pos, to_pos, mask)).has_hit():
            return result.get_node()

        return None

    def rotate_camera(self, walker_pos, camera_pos):
        q = Quat()
        next_pos = walker_pos + self.walker.direction_relative_pos(Vec3(0, 5, 1))

        for i in range(36):
            if node := self.ray_cast(next_pos, walker_pos):
                if node == self.walker.node():
                    return next_pos

            n = i // 2 + 1
            angle = 10 * n if i % 2 == 0 else -10 * n
            q.set_from_axis_angle(angle, Vec3.up())
            next_pos = q.xform(camera_pos - walker_pos) + walker_pos

    def watch_falling(self, walker_pos, camera_pos, dt):
        next_pos = Point3()
        xy_diff = camera_pos.xy - walker_pos.xy
        next_pos.xy = camera_pos.xy + xy_diff * -1 * dt * 10
        next_pos.z = camera_pos.z
        self.camera.set_pos(next_pos)
        self.camera.look_at(self.floater)

    def camera_outside(self, walker_pos, camera_pos):
        """Reposition the camera if the camera's view is blocked
           by other objects like terrain.
        """
        if (node := self.ray_cast(camera_pos, walker_pos)) is not None \
                and node != self.walker.node():
            if next_pos := self.rotate_camera(walker_pos, camera_pos):
                self.camera.set_pos(next_pos)
                self.camera.look_at(self.floater)
                self.cam_distance = next_pos - walker_pos
                return

        self.camera.set_pos(walker_pos + self.cam_distance)
        self.camera.look_at(self.floater)

    def camera_in_room(self, walker_pos, camera_pos):
        """Once the character get inside the room, do not move the camera.
           If camera's view is blocked, position the camera at the center of the roof.
        """
        if (node := self.ray_cast(camera_pos, walker_pos)) is not None \
                and node != self.walker.node():
            self.camera.set_pos(self.scene.basement.room_camera.get_pos(self.render))
            self.change_camera = True

        self.camera.look_at(self.floater)

    def control_camera(self, dt):
        walker_pos = self.walker.get_pos()
        camera_pos = self.camera.get_pos()

        match self.walker.status:

            case Status.FALLING:
                self.watch_falling(walker_pos, camera_pos, dt)

            case Status.INTO_ROOM | Status.IN_ROOM:
                self.camera_in_room(walker_pos, camera_pos)

            case _:
                self.camera_outside(walker_pos, camera_pos)

    def control_walker(self, dt):
        motions = []

        if inputState.is_set('forward'):
            motions.append(Motions.FORWARD)
        if inputState.is_set('backward'):
            motions.append(Motions.BACKWARD)
        if inputState.is_set('left'):
            motions.append(Motions.LEFT)
        if inputState.is_set('right'):
            motions.append(Motions.RIGHT)

        self.walker.update(dt, motions)

    def update(self, task):
        dt = globalClock.get_dt()

        self.control_walker(dt)
        self.control_camera(dt)
        self.scene.mid_water.wave(task.time)

        self.world.do_physics(dt)
        return task.cont


if __name__ == '__main__':
    app = TerrainWithHole()
    app.run()