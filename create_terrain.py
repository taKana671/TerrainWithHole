import sys

from panda3d.bullet import BulletWorld, BulletDebugNode
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from direct.showbase.InputStateGlobal import inputState
from panda3d.core import load_prc_file_data
from panda3d.core import NodePath, Point3, Vec3, Vec2, BitMask32, Quat
from panda3d.core import TransparencyAttrib
from direct.interval.IntervalGlobal import Sequence, Func


IS_RALPH = True

if IS_RALPH:
    from walker import Walker, Motions, Status
else:
    from seeker import Seeker, Motions

from scene import Scene
# from scene_git import Scene
from lights import BasicAmbientLight, BasicDayLight, BasicSpotLight


load_prc_file_data("", """
    textures-power-2 none
    gl-coordinate-system default
    window-title Panda3D Test Terrain
    filled-wireframe-apply-shader true
    stm-max-views 8
    stm-max-chunk-count 2048""")


class TestTerrain(ShowBase):

    def __init__(self):
        super().__init__()
        self.disable_mouse()

        self.world = BulletWorld()
        self.world.set_gravity(Vec3(0, 0, -9.81))

        self.debug = self.render.attach_new_node(BulletDebugNode('debug'))
        self.world.set_debug_node(self.debug.node())

        self.scene = Scene()
        self.scene.root.reparent_to(self.render)

        if IS_RALPH:
            self.walker = Walker(self.world)
            self.walker.reparent_to(self.render)
            
            self.walker.set_pos(Point3(-18.0243, 14.9644, -9.21977))
            
            self.floater = NodePath('floater')
            self.floater.set_z(3.0)
            self.floater.reparent_to(self.walker)

            # ***************parent to walker****************
            # self.camera.reparent_to(self.walker)
            # self.camera.set_pos(self.walker.navigate())
            # self.camera.look_at(self.floater)
            # self.camLens.set_near_far(0.5, 10000)
            # self.camLens.set_fov(90)
            # ***************parent to walker****************

            # ***************parent to render****************
            self.camNode.set_active(False)

            self.room_camera = None
            self.change_camera = False

            self.camera = self.create_camera()
            self.camera.reparent_to(self.render)
            self.cam_distance = Vec3(0, -5, 1)
            self.camera.set_pos(self.walker.get_pos() + self.cam_distance)

            self.camera.look_at(self.floater)
            # ***************parent to render****************
        else:
            self.walker = Seeker(self.world)
            self.walker.reparent_to(self.render)
            self.floater = NodePath('floater')
            self.floater.set_z(0)
            self.camera.set_p(-0.7)
            self.floater.reparent_to(self.walker)

            self.camera.reparent_to(self.walker)
            self.camera.set_pos(self.walker.navigate())
            self.camera.look_at(self.floater)
            self.camLens.set_near_far(0.2, 10000)
            self.camLens.set_fov(60)

        # self.ambient_light = BasicAmbientLight()
        # self.basic_light = BasicDayLight()

        # self.spot_light = BasicSpotLight()
        # self.spot_light.set_pos_hpr(self.walker.actor, Point3(0, 0.3, 1), Vec3(0, 0, 0))
        # self.spot_light.reparent_to(self.walker.direction_nd)

        self.state = False
        self.is_falling = False

        inputState.watch_with_modifiers('forward', 'arrow_up')
        inputState.watch_with_modifiers('backward', 'arrow_down')
        inputState.watch_with_modifiers('left', 'arrow_left')
        inputState.watch_with_modifiers('right', 'arrow_right')

        inputState.watch_with_modifiers('up', 'b')
        inputState.watch_with_modifiers('down', 'n')

        # inputState.watch_with_modifiers('forward', 'w')
        # inputState.watch_with_modifiers('backward', 's')
        # inputState.watch_with_modifiers('left', 'a')
        # inputState.watch_with_modifiers('right', 'd')
        # inputState.watch_with_modifiers('up', 'arrow_up')
        # inputState.watch_with_modifiers('down', 'arrow_down')

        self.accept('x', self.positioning, ['x', True])
        self.accept('shift-x', self.positioning, ['x', False])
        self.accept('y', self.positioning, ['y', True])
        self.accept('shift-y', self.positioning, ['y', False])
        self.accept('z', self.positioning, ['z', True])
        self.accept('shift-z', self.positioning, ['z', False])
        self.accept('h', self.positioning, ['h', True])
        self.accept('shift-h', self.positioning, ['h', False])
        self.accept('p', self.positioning, ['p', True])
        self.accept('shift-p', self.positioning, ['p', False])
        self.accept('r', self.positioning, ['r', True])
        self.accept('shift-r', self.positioning, ['r', False])

        self.accept('u', self.go_down, [True])
        self.accept('shift-u', self.go_down, [False])

        self.accept('i', self.print_info)
        self.accept('escape', sys.exit)
        self.accept('m', self.toggle_debug)
        self.taskMgr.add(self.update, 'update')

    def go_down(self, is_down):
        direction = 1
        if is_down:
            direction *= -1
        z = self.walker.get_z() + direction
        self.walker.set_z(z)

    def positioning(self, target, increment):
        pos = Point3()
        hpr = Vec3()

        match target:
            case 'x':
                x = 0.1 if increment else -0.1
                pos.x = x
            case 'y':
                y = 0.1 if increment else -0.1
                pos.y = y
            case 'z':
                z = 0.1 if increment else -0.1
                pos.z = z
            case 'h':
                h = 0.1 if increment else -0.1
                hpr.x = h
            case 'p':
                p = 0.1 if increment else -0.1
                hpr.y = p
            case 'r':
                r = 0.1 if increment else -0.1
                hpr.z = r

        # pos = self.scene.basement.slope.get_pos() + pos
        # hpr = self.scene.basement.slope.get_hpr() + hpr
        # print(pos, hpr)
        # self.scene.basement.slope.set_pos_hpr(pos, hpr)

        pos = self.scene.sensor.get_pos() + pos
        hpr = self.scene.sensor.get_hpr() + hpr
        print(pos, hpr)
        self.scene.sensor.set_pos_hpr(pos, hpr)

    def print_info(self):
        print(self.walker.get_pos())

    def toggle_debug(self):
        # self.toggle_wireframe()
        if self.debug.is_hidden():
            self.debug.show()
        else:
            self.debug.hide()

    def ray_cast(self, from_pos, to_pos):
        if (result := self.world.ray_test_closest(
                from_pos, to_pos, BitMask32.bit(2) | BitMask32.bit(3) | BitMask32.bit(7))).has_hit():
            # print('ray cast for camera', result.get_node().get_name())
            return result.get_node()

        return None

    def create_camera(self):
        camera = self.make_camera(self.win)
        camera.node().get_lens().set_fov(90)
        camera.node().get_lens().set_near_far(0.1, 10000)
        return camera

    def fade_camera(self, pos, look_at, duration=2.0):
        self.cam_faded = False

        props = self.win.get_properties()
        size = props.get_size()
        buffer = self.win.make_texture_buffer('tex_buffer', *size)
        buffer.set_clear_color_active(True)
        buffer.set_clear_color((0.5, 0.5, 0.5, 1))

        temp_cam = self.make_camera(buffer)
        temp_cam.node().get_lens().set_fov(90)
        temp_cam.set_pos(pos)
        temp_cam.look_at(look_at)

        card = buffer.get_texture_card()
        card.reparent_to(self.render2d)

        # Screens slowly changes, having afterimage.
        card.set_transparency(TransparencyAttrib.M_alpha)
        # Screen quckly changes, having no afterimage.
        # card.set_transparency(TransparencyAttrib.M_multisample)
        self.camera.detach_node()
        self.camera.reparent_to(self.render)

        Sequence(
            card.colorScaleInterval(duration, 1, 0, blendType='easeInOut'),
            Func(self.camera.set_pos, pos),
            Func(self.camera.look_at, look_at),
            Func(card.remove_node),
            Func(temp_cam.remove_node),
            Func(self.graphics_engine.remove_window, buffer),
            Func(self.end_fade)
        ).start()

    def end_fade(self):
        self.cam_faded = True

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
        if inputState.is_set('up'):
            motions.append(Motions.UP)
        if inputState.is_set('down'):
            motions.append(Motions.DOWN)

        self.walker.update(dt, motions)

    def find_walker_start_pos(self):
        for hit in self.world.rayTestAll(
                Point3(-23, 11, 30), Point3(-23, 11, -30), mask=BitMask32.bit(1)).get_hits():

            if hit.get_node() == self.walker.node():
                continue

            pos = hit.get_hit_pos()
            return pos + Vec3(0, 0, 1.5)

    def update(self, task):
        dt = globalClock.get_dt()

        self.control_walker(dt)
        self.control_camera(dt)
        self.scene.mid_water.wave(task.time)

        self.world.do_physics(dt)
        return task.cont


if __name__ == '__main__':
    app = TestTerrain()
    app.run()