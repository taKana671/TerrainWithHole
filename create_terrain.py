import sys

from panda3d.bullet import BulletWorld, BulletDebugNode
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from direct.showbase.InputStateGlobal import inputState
from panda3d.core import load_prc_file_data
# from panda3d.core import Filename, PNMImage
# from panda3d.core import ShaderTerrainMesh, Shader
# from panda3d.core import SamplerState, TextureStage
from panda3d.core import NodePath, Point3, Vec3, Vec2, BitMask32, Quat

# from panda3d.bullet import BulletRigidBodyNode
# from panda3d.bullet import BulletTriangleMeshShape, BulletHeightfieldShape, ZUp
# from panda3d.bullet import BulletConvexHullShape, BulletTriangleMesh
# from panda3d.core import GeoMipTerrain
# from panda3d.core import RenderAttrib, AlphaTestAttrib

from walker import Walker, Motions
from constants import Mask
from scene import Scene


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

        # self.camera.set_pos(Point3(-128, -128, 100))
        # self.camera.set_pos(Point3(0, 0, 100))
        # self.camera.look_at(Point3(0, 0, 10))

        self.dragging = False
        self.before_mouse_pos = Vec2()

        
        # self.generate_terrain()
        # self.world.attach(self.terrain_root.node())

        self.scene = Scene()
        self.scene.reparent_to(self.render)

        self.walker = Walker(self.world)
        self.walker.reparent_to(self.render)

        self.floater = NodePath('floater')
        self.floater.set_z(3.0)
        self.floater.reparent_to(self.walker)

        self.camera.reparent_to(self.walker)
        self.camera.set_pos(self.walker.navigate())
        # self.camera.set_z(50)
        self.camera.look_at(self.floater)
        self.camLens.set_fov(90)

        self.state = False

        inputState.watch_with_modifiers('forward', 'arrow_up')
        inputState.watch_with_modifiers('backward', 'arrow_down')
        inputState.watch_with_modifiers('left', 'arrow_left')
        inputState.watch_with_modifiers('right', 'arrow_right')

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

        self.accept('i', self.print_info)
        self.accept('escape', sys.exit)
        self.accept('d', self.toggle_debug)
        self.accept('mouse1', self.mouse_click)
        self.accept('mouse1-up', self.mouse_release)
        self.taskMgr.add(self.update, 'update')

    def positioning(self, target, increment):
        pos = Point3()
        hpr = Vec3()

        match target:
            case 'x':
                x = 1 if increment else -1
                pos.x = x
            case 'y':
                y = 1 if increment else -1
                pos.y = y
            case 'z':
                z = 1 if increment else -1
                pos.z = z
            case 'h':
                h = 1 if increment else -1
                hpr.x = h
            case 'p':
                p = 1 if increment else -1
                hpr.y = p
            case 'r':
                r = 1 if increment else -1
                hpr.z = r

        pos = self.scene.cave.get_pos() + pos
        hpr = self.scene.cave.get_hpr() + hpr
        print(pos, hpr)  

        self.scene.cave.set_pos_hpr(pos, hpr)

    def print_info(self):
        print(self.walker.get_pos())

    def toggle_debug(self):
        # self.toggle_wireframe()
        if self.debug.is_hidden():
            self.debug.show()
        else:
            self.debug.hide()

    def mouse_click(self):
        self.dragging = True
        self.dragging_start_time = globalClock.get_frame_time()

    def mouse_release(self):
        self.dragging = False
        self.before_mouse_pos.x = 0
        self.before_mouse_pos.y = 0

    # def generate_terrain(self):
    #     self.terrain_root = NodePath(BulletRigidBodyNode('terrain_root'))
    #     self.terrain_root.node().set_mass(0)
    #     self.terrain_root.set_collide_mask(BitMask32.bit(1))
    #     self.terrain_root.reparent_to(self.render)
    #     heightmap = 'output3.png'
    #     height = 100

    #     # greater_filter = AlphaTestAttrib.make(RenderAttrib.M_greater, 0.5)
    #     # self.terrain_root.set_attrib(greater_filter)

    #     img = PNMImage(Filename(heightmap))
    #     shape = BulletHeightfieldShape(self.loader.load_texture(heightmap), height, ZUp)
    #     shape = BulletHeightfieldShape(img, height, ZUp)
    #     shape.set_use_diamond_subdivision(True)
    #     self.terrain_root.node().add_shape(shape)

    #     self.terrain = GeoMipTerrain('geomip_terrain')
    #     self.terrain.set_heightfield(heightmap)
    #     self.terrain.set_border_stitching(True)
    #     self.terrain.set_block_size(8)
    #     self.terrain.set_min_level(2)
    #     self.terrain.set_focal_point(self.camera)

    #     size_x, size_y = img.get_size()
    #     x = (size_x - 1) / 2
    #     y = (size_y - 1) / 2

    #     pos = Point3(-x, -y, -(height / 2))
    #     scale = Vec3(1, 1, height)
    #     self.root = self.terrain.get_root()
    #     self.root.set_scale(scale)
    #     self.root.set_pos(pos)

    #     self.terrain.generate()
    #     self.root.reparent_to(self.terrain_root)
    #     # self.root.set_attrib(greater_filter)

    #     # import pdb; pdb.set_trace()
    #     # np = self.terrain.getBlockNodePath(0, 0)
    #     # geom = np.node().modifyGeom(0)
    #     # vdata = geom.modifyVertexData()
    #     # old_count = vdata.get_num_rows()
    #     # v_array = vdata.modify_array(0)
    #     # size = 100 * 8
    #     # start = 5 * size
    #     # view = memoryview(v_array).cast('B')
    #     # view[start:-size] = view[start + size:]
    #     # vdata.set_num_rows(old_count - 10)
    #     # tris_prim = geom.modify_primitive(0)
    #     # old_count = tris_prim.get_num_vertices()
    #     # start = 5 * 6
    #     # tris_prim.offset_vertices(-10, start + 6, old_count)
    #     # tris_array = tris_prim.modify_vertices()
    #     # view = memoryview(tris_array).cast('B').cast('H')
    #     # view[start:-6] = view[start + 6:]
    #     # tris_array.set_num_rows(old_count - 6)

    #     # shapeをつくるタイミングを変えても、何の影響もない。一番最後にしても影響ない。
    #     # shape = BulletHeightfieldShape(self.loader.load_texture(heightmap), height, ZUp)
    #     # shape = BulletHeightfieldShape(img, height, ZUp)
    #     # shape.set_use_diamond_subdivision(True)
    #     # self.terrain_root.node().add_shape(shape)



    #     shader = Shader.load(Shader.SL_GLSL, 'shaders/terrain_v.glsl', 'shaders/terrain_f.glsl')
    #     self.root.set_shader(shader)

    #     tex_files = [
    #         ('stones_01.jpg', 20),
    #         ('grass_02.png', 10),
    #     ]

    #     for i, (file_name, tex_scale) in enumerate(tex_files):
    #         ts = TextureStage(f'ts{i}')
    #         ts.set_sort(i)
    #         self.root.set_shader_input(f'tex_ScaleFactor{i}', tex_scale)
    #         tex = self.loader.load_texture(f'textures/{file_name}')
    #         self.root.set_texture(ts, tex)

    #     # i = 2
    #     # ts = TextureStage(f'ts{i}')
    #     # ts.set_sort(i)
    #     self.root.set_shader_input('heightmap', self.loader.load_texture(heightmap))

    def rotate_camera(self, mouse_pos, dt):
        angle = Vec3()

        if (delta := mouse_pos.x - self.before_mouse_pos.x) < 0:
            angle.x -= 90
        elif delta > 0:
            angle.x += 90

        if (delta := mouse_pos.y - self.before_mouse_pos.y) < -0.01:
            angle.y += 90
        elif delta > 0.01:
            angle.y -= 90

        angle *= dt
        self.camera.set_hpr(self.camera.get_hpr() + angle)

        self.before_mouse_pos.x = mouse_pos.x
        self.before_mouse_pos.y = mouse_pos.y

    def ray_cast(self, from_pos, to_pos):
        # if (result := self.world.ray_test_closest(
        #         from_pos, to_pos, Mask.environment)).has_hit():
        if (result := self.world.ray_test_closest(
                from_pos, to_pos, BitMask32.bit(1) | BitMask32.bit(3) | BitMask32.bit(2))).has_hit():
            return result.get_node()

        return None

    def find_camera_pos(self, walker_pos, next_pos):
        q = Quat()
        point = Point3(0, 0, 0)
        start = self.camera.get_pos()
        angle = r = None

        for i in range(36):
            camera_pos = next_pos + walker_pos
            if self.ray_cast(camera_pos, walker_pos) == self.walker.node():
                return next_pos

            times = i // 2 + 1
            angle = 10 * times if i % 2 == 0 else -10 * times
            q.set_from_axis_angle(angle, Vec3.up())
            r = q.xform(start - point)
            next_pos = point + r

        return None

    def control_camera(self):
        """Reposition the camera if the camera's view is blocked
           by other objects like terrain, rocks, trees.
        """
        walker_pos = self.walker.get_pos()
        camera_pos = self.camera.get_pos() + walker_pos

        if self.ray_cast(camera_pos, walker_pos) != self.walker.node():
            if next_pos := self.find_camera_pos(walker_pos, self.walker.navigate()):
                self.camera.set_pos(next_pos)
                # self.camera.set_z(50)
                self.camera.look_at(self.floater)

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

    def find_walker_start_pos(self):
        for hit in self.world.rayTestAll(
                Point3(-23, 11, 30), Point3(-23, 11, -30), mask=Mask.terrain).get_hits():

            if hit.get_node() == self.walker.node():
                continue

            pos = hit.get_hit_pos()
            return pos + Vec3(0, 0, 1.5)

    def update(self, task):
        dt = globalClock.get_dt()

        if not self.state:
            pos = self.find_walker_start_pos()
            # self.walker.set_pos(pos)
            self.walker.set_pos(Point3(14.0097, -19.1757, -11.6965))
            # self.walker.set_pos(Point3(6.05444, 18.5463, 2.06921))

            self.state = True

        self.control_walker(dt)
        self.control_camera()

        if self.mouseWatcherNode.has_mouse():
            mouse_pos = self.mouseWatcherNode.get_mouse()
            if self.dragging:
                if globalClock.get_frame_time() - self.dragging_start_time >= 0.2:
                    self.rotate_camera(mouse_pos, dt)

        self.world.do_physics(dt)
        return task.cont


if __name__ == '__main__':
    app = TestTerrain()
    app.run()
 