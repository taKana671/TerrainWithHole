import math
import numpy as np
from enum import Enum

from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletTriangleMeshShape, BulletHeightfieldShape, ZUp
from panda3d.bullet import BulletConvexHullShape, BulletTriangleMesh
from panda3d.core import NodePath, BitMask32, Point3, Vec3, PandaNode
from panda3d.core import Filename, PNMImage
from panda3d.core import Shader, TextureStage
from panda3d.core import GeoMipTerrain, TransformState
from panda3d.core import TransparencyAttrib

from shapes.src import Sphere, Cylinder, Plane, Box


class Sensors(Enum):

    HOLE = ('hole', 5)
    BASEMENT = ('basement', 5)
    TUNNEL = ('tunnel', 4)
    MID_GROUND = ('mid_ground', 6)
    STEPS = ('steps', 6)

    def __init__(self, location, mask):
        self.location = location
        self.mask = mask


class ModelRoot(NodePath):

    def __init__(self, name, mask):
        super().__init__(BulletRigidBodyNode(name))
        self.node().set_mass(0)
        self.set_collide_mask(mask)

    def add_trianglemesh_shape(self, model):
        mesh = BulletTriangleMesh()
        mesh.add_geom(model.node().get_geom(0))
        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        self.node().add_shape(shape)

    def add_convexhull_shape(self, model):
        shape = BulletConvexHullShape()
        shape.add_geom(model.node().get_geom(0))
        self.node().add_shape(shape)

    def add_texture(self, img_file, target=None):
        target = self if not target else target
        tex = base.loader.load_texture(f'textures/{img_file}')
        target.set_texture(tex)


class Sensor(ModelRoot):

    def __init__(self, name, sensor, width, depth):
        super().__init__(name, BitMask32.bit(sensor.mask))
        self.sensor = sensor
        self.location = sensor.location
        self.dest_sensor = None
        self.create_model(width, depth)
        self.set_shader_off()

    def create_model(self, width, depth):
        model = Plane(width, depth, segs_w=int(width), segs_d=int(depth)).create()
        model.set_transparency(TransparencyAttrib.MAlpha)
        model.set_color(1, 1, 1, 0)
        self.add_trianglemesh_shape(model)
        model.reparent_to(self)

    def detect_collision(self, target_nd):
        if base.world.contact_test_pair(
                self.node(), target_nd).get_num_contacts():
            return True

    def respond(self, from_pos, distance=-3):
        to_pos = from_pos + Vec3(0, 0, distance)

        if (hit := base.world.ray_test_closest(
                from_pos, to_pos, BitMask32.bit(self.sensor.mask))).has_hit():
            return hit


class WaterSurface(ModelRoot):

    def __init__(self, w=256, d=256, segs_w=16, segs_d=16, mask=9):
        super().__init__('water_surface', BitMask32.bit(mask))
        self.create_model(w, d, segs_w, segs_d)
        self.set_shader_off()

    def create_model(self, w, d, segs_w, segs_d):
        plane = Plane(w, d, segs_w, segs_d)
        self.stride = plane.stride

        self.model = plane.create()
        self.model.set_transparency(TransparencyAttrib.MAlpha)
        self.model.set_texture(base.loader.load_texture('textures/water.png'))
        self.model.set_pos(Point3(0, 0, 0))

        self.add_trianglemesh_shape(self.model)
        self.model.reparent_to(self)

    def wave(self, time, wave_h=1.0):
        geom_node = self.model.node()
        geom = geom_node.modify_geom(0)
        vdata = geom.modify_vertex_data()
        vdata_arr = vdata.modify_array(0)
        vdata_mem = memoryview(vdata_arr).cast('B').cast('f')

        for i in range(0, len(vdata_mem), self.stride):
            x, y = vdata_mem[i: i + 2]
            z = (math.sin(time + x / wave_h) + math.sin(time + y / wave_h)) * wave_h / 2
            vdata_mem[i + 2] = z


class AssembledModel(ModelRoot):

    def __init__(self, name, mask):
        super().__init__(name, mask)

    def setup_model(self, model, name, pos, hpr, parent=None):
        model.set_pos_hpr(pos, hpr)
        model.set_name(name)

        mesh = BulletTriangleMesh()
        mesh.add_geom(model.node().get_geom(0))
        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        self.node().add_shape(shape, TransformState.make_pos_hpr(pos, hpr))

        parent = self if not parent else parent
        model.reparent_to(parent)


class SquareTunnel(AssembledModel):

    def __init__(self, mask=3):
        super().__init__('square_tunnel', BitMask32.bit(mask))
        self.assemble_model()

    def assemble_model(self):
        # tunnel
        model = Box(width=4.5, depth=31, height=5, segs_w=5, segs_d=30, segs_z=5,
                    open_bottom=True, open_front=True, open_back=True).create()
        model.set_tex_scale(TextureStage.get_default(), 5, 1)
        self.setup_model(model, 'tunnel', Point3(0.2, -0.8, -0.1), Vec3(51, 5, 0))

        # hollow rectangular prism that overlaps the hole in the mountain.
        maker = Box(width=6, depth=4, height=6, segs_w=6, segs_d=4, segs_z=6,
                    thickness=2, open_bottom=True, open_front=True, open_back=True)

        self.setup_model(maker.create(), 'gate_1', Point3(13.0778, -10.635, -0.5477), Vec3(64, 0, 0))
        self.setup_model(maker.create(), 'gate_2', Point3(-10.9222, 9.36504, 1.45235), Vec3(31, 0, 0))

        # set texture.
        self.add_texture('tile2.jpg')


class RoundTunnel(AssembledModel):

    def __init__(self, mask=3):
        super().__init__('round_tunnel', BitMask32.bit(mask))
        self.assemble_model()

    def assemble_model(self):
        # hollow rectangular prism that overlaps the hole in the top ground.
        model = Box(width=3, depth=3.2, height=2, segs_w=4, segs_d=4, segs_z=2,
                    thickness=0.5, open_bottom=True, open_top=True).create()
        self.setup_model(model, 'hole_1', Point3(0, 0, 0.1), Vec3(180, 12.6, -7.5))

        # tunnel
        model = Cylinder(radius=1.5, height=43.5, segs_top_cap=0, segs_bottom_cap=0).create()
        self.setup_model(model, 'tunnel', Point3(0, 0, 0), Vec3(0, 180, 0))

        # hollow rectangular prism that overlaps the hole in the bottom ground.
        model = Box(width=4, depth=4, height=4, segs_w=4, segs_d=4, segs_z=4,
                    thickness=1, open_bottom=True, open_top=True).create()
        self.setup_model(model, 'hole_2', Point3(0, 0, -42.5), Vec3(0, 0, 0))

        # walls
        model = Box(width=4, depth=4, height=6, segs_w=4, segs_d=4, segs_z=6,
                    thickness=1, open_bottom=True, open_top=True, open_left=True, open_back=True).create()
        self.setup_model(model, 'wall', Point3(0, 0, -47.5), Vec3(0, 0, 0))

        # set texture.
        self.add_texture('metalboard.jpg')


class Basement(AssembledModel):

    def __init__(self):
        super().__init__('underground_room', BitMask32.bit(3))
        self.assemble_model()
        self.flatten_strong()

    def assemble_model(self):
        basement = NodePath('room')
        basement.reparent_to(self)
        steps = NodePath('steps')
        steps.reparent_to(self)

        # hollow rectangular prism that overlaps the hole.
        model = Box(width=5, depth=5, height=2, segs_w=3, segs_d=3, thickness=1.0,
                    open_bottom=True, open_top=True).create()
        self.setup_model(model, 'hole', Point3(0, 0, 0), Vec3(180, 0, 0), basement)

        # room
        model = Box(width=13.5, depth=13.5, height=8, segs_w=5, segs_d=5, segs_z=8, thickness=0.5,
                    open_top=True).create()
        self.setup_model(model, 'room', Point3(-4.5, -4.5, -5), Vec3(180, 0, 0), basement)

        # roofs
        model = Box(width=9, depth=13.5, height=0.5, segs_w=9, segs_d=5, thickness=0.5, open_top=True).create()
        self.setup_model(model, 'roof_1', Point3(-6.75, -4.5, -0.75), Vec3(0, 0, 0), parent=basement)
        model = Box(width=4.5, depth=9, height=0.5, segs_w=3, segs_d=9, thickness=0.5, open_top=True).create()
        self.setup_model(model, 'roof_2', Point3(0, -6.75, -0.75), Vec3(0, 0, 0), parent=basement)

        # steps
        maker = Box(width=3.5, depth=1, height=1.5)
        start_z, start_y = -1.25, 1.25
        hpr = Vec3(0, 0, 0)

        for i in range(6):
            model = maker.create()
            pos = Point3(0, start_y - i, start_z - i * 1.5)
            name = f'steps_{i}'
            self.setup_model(model, name, pos, hpr, parent=steps)

        # set_texture
        for img_file, target in [('tile2.jpg', basement), ('concrete_01.jpg', steps)]:
            self.add_texture(img_file, target)

        # room camera
        self.room_camera = NodePath('underground_room_camera')
        self.room_camera.reparent_to(self)
        self.room_camera.set_pos(Point3(-4.5, -4.5, -2))


class Cave(AssembledModel):

    def __init__(self, width, depth, wall_height, thickness, mask=3):
        super().__init__('cave', BitMask32.bit(mask))
        self.assemble_model(width, depth, wall_height, thickness)

    def create_model(self, width, depth, wall_height, thickness):
        # side walls
        maker = Box(width=width, depth=depth, height=wall_height, thickness=thickness,
                    open_bottom=True, open_front=True, open_top=True, open_back=True)

        radius = width / 2
        inner_radius = width / 2 - thickness
        half_h = wall_height / 2
        half_d = depth / 2

        # rear wall
        rear_wall = Cylinder(radius=radius, inner_radius=inner_radius, height=wall_height,
                             segs_a=int(wall_height), ring_slice_deg=180)
        # round_roof
        round_roof = Cylinder(radius=radius, inner_radius=inner_radius, height=depth,
                              segs_a=int(depth), ring_slice_deg=180)
        # rear round roof
        rear_roof = Sphere(radius=radius, inner_radius=inner_radius, slice_deg=270)

        parts = [
            [rear_wall, Vec3(0, 0, 1), Point3(0, half_d, -half_h), -180],
            [round_roof, Vec3(0, 1, 0), Point3(0, -half_d, half_h), 0],
            [rear_roof, Vec3(1, 0, 0), Point3(0, half_d, half_h), 180]
        ]

        # cave wall
        base_nd = maker.get_geom_node()

        for parts_maker, axis_vec, bottom_center, rotation_deg in parts:
            geom_nd = parts_maker.get_geom_node()
            geom = geom_nd.modify_geom(0)
            vdata = geom.modify_vertex_data()
            maker.tranform_vertices(vdata, axis_vec, bottom_center, rotation_deg)
            vert_cnt = vdata.get_num_rows()
            vdata_mem = memoryview(vdata.modify_array(0)).cast('B').cast('f')
            prim = geom.modify_primitive(0)
            prim_array = prim.modify_vertices()
            prim_mem = memoryview(prim_array).cast('B').cast('H')
            maker.add(base_nd, vdata_mem, vert_cnt, prim_mem)

        model = maker.modeling(base_nd)
        return model

    def assemble_model(self, width, depth, wall_height, thickness):
        cave = NodePath('cave_body')
        cave.reparent_to(self)
        gate = NodePath('gate')
        gate.reparent_to(self)

        # cave
        model = self.create_model(width, depth, wall_height, thickness)
        self.setup_model(model, 'cave', Point3(0, 0, 0), Vec3(0, 0, 0), parent=cave)

        # gate
        w = width + 2
        h = wall_height + 5
        model = Box(width=w, depth=6, height=h, segs_w=int(w), segs_d=6, segs_z=int(h),
                    thickness=2, open_bottom=True, open_front=True, open_back=True).create()

        pos = Point3(0, -depth / 2 + 3.1, 2)
        self.setup_model(model, 'gate', pos, Vec3(0, 0, 0), parent=gate)

        for img_file, target in [('concrete_01.jpg', cave), ('tile2.jpg', gate)]:
            self.add_texture(img_file, target)


class Terrain(NodePath):

    def __init__(self, name, heightmap, height, tex_files, block_size=8, mask=1, discard=True):
        super().__init__(BulletRigidBodyNode(f'terrain_{name}'))
        self.heightmap = f'terrains/{heightmap}'
        self.height = height
        self.block_size = block_size
        self.discard = discard

        self.node().set_mass(0)
        self.set_collide_mask(BitMask32.bit(mask))
        shape = BulletHeightfieldShape(base.loader.load_texture(self.heightmap), self.height, ZUp)
        shape.set_use_diamond_subdivision(True)
        self.node().add_shape(shape)
        self.generate_terrain(tex_files)

        self.name = name

    def generate_terrain(self, tex_files):
        img = PNMImage(Filename(self.heightmap))
        self.terrain = GeoMipTerrain('geomip_terrain')
        self.terrain.set_heightfield(self.heightmap)
        self.terrain.set_border_stitching(True)
        self.terrain.set_block_size(self.block_size)
        self.terrain.set_min_level(2)
        self.terrain.set_focal_point(base.camera)
        self.terrain.setBruteforce("True")

        size_x, size_y = img.get_size()
        x = (size_x - 1) / 2
        y = (size_y - 1) / 2
        # x = size_x / 2 - 0.4
        # y = size_y / 2 - 0.4

        pos = Point3(-x, -y, -(self.height / 2))
        self.root = self.terrain.get_root()
        self.root.set_sz(self.height)
        self.root.set_pos(pos)
        self.terrain.generate()
        self.root.reparent_to(self)

        f_name = 'terrain_f' if self.discard else 'terrain_no_discard_f'
        shader = Shader.load(Shader.SL_GLSL, 'shaders/terrain_v.glsl', f'shaders/{f_name}.glsl')
        self.root.set_shader(shader)
        if self.discard:
            self.root.set_shader_input('heightmap', base.loader.load_texture(self.heightmap))

        for i, (file_name, tex_scale) in enumerate(tex_files):
            ts = TextureStage(f'ts{i}')
            ts.set_sort(i)
            self.root.set_shader_input(f'tex_ScaleFactor{i}', tex_scale)
            tex = base.loader.load_texture(f'textures/{file_name}')
            self.root.set_texture(ts, tex)

    def make_hole(self, mx, my):
        # get the vertex data for an individual block in where hole is made.
        # check the value of mx and my by self.root.ls().
        block_np = self.terrain.getBlockNodePath(mx, my)
        geom = block_np.node().modifyGeom(0)
        vdata = geom.modify_vertex_data()
        v_array = vdata.modify_array(0)

        # set the vertex data to 0 for all the sides of the triangle to make it not visible.
        view = memoryview(v_array).cast('B').cast('f')
        view[:] = np.zeros(len(view), dtype=np.float32)


class Sky(NodePath):

    def __init__(self):
        super().__init__(PandaNode('sky'))
        self.blue_sky = base.loader.load_model('models/blue-sky/blue-sky-sphere')
        self.blue_sky.reparent_to(self)
        self.set_shader_off()
        self.model = None


class Scene:

    def __init__(self):
        self.root = NodePath('scene')
        self.create_terrains()
        self.setup_environments()
        self.create_sensor()

    def attach_nature(self, model, parent=None):
        parent = self.root if parent is None else parent
        model.reparent_to(parent)
        base.world.attach(model.node())

    def create_terrains(self):
        tex_files = [
            ('grass_05.jpg', 20),
            ('grass_05.jpg', 20),
        ]

        self.top_ground = Terrain('top_gd', 'top_ground.png', 10, tex_files)
        # self.top_ground.root.set_two_sided(True)
        self.attach_nature(self.top_ground)
        self.top_ground.set_z(-12)

        tex_files = [
            ('stone_01.jpg', 20),
            ('grass_04.jpg', 20),
        ]
        self.top_mountains = Terrain('top_mt', 'top_terrain.png', 100, tex_files, mask=2)
        self.top_mountains.root.set_two_sided(True)
        self.attach_nature(self.top_mountains)
        self.top_mountains.set_z(0)

        tex_files = [
            ('stone_01.jpg', 20),
            ('stones_01.jpg', 20),
        ]

        self.mid_ground = Terrain('mid_gd', 'mid_ground.png', 20, tex_files, block_size=4, discard=False)
        self.mid_ground.make_hole(6, 10)
        # block_np = self.terrain.getBlockNodePath(2, 5)  # blocksize=8
        self.attach_nature(self.mid_ground)
        self.mid_ground.set_z(-56)   # -58

        tex_files = [
            ('rock_02.jpg', 20),
            ('stone_01.jpg', 10),
        ]
        self.mid_mountains = Terrain('mid_mt', 'mid_terrain.png', 100, tex_files, mask=2)
        self.mid_mountains.root.setTwoSided(True)
        self.attach_nature(self.mid_mountains)
        self.mid_mountains.set_z(-48)

    def setup_environments(self):
        self.sky = Sky()
        self.sky.reparent_to(self.root)

        # tunnel on the top ground
        self.tunnel = SquareTunnel()
        self.attach_nature(self.tunnel)
        self.tunnel.set_pos(Point3(-7.8244, -7.0682, -10.6803))

        # big cave on the top ground
        self.cave = Cave(width=8, depth=15, wall_height=10, thickness=1.5)
        self.attach_nature(self.cave)
        self.cave.set_pos_hpr(Point3(32.8145, 3.5, -13.7908), Vec3(-11, 0, 0))

        # small cave on the top ground
        self.small_cave = Cave(width=6, depth=3, wall_height=4, thickness=1.5)
        self.attach_nature(self.small_cave)
        self.small_cave.set_pos_hpr(Point3(-18.9, 18.2, -10.3), Vec3(-7, 0, 0))

        # tunnel from top ground to mig ground
        self.passage = RoundTunnel()
        self.attach_nature(self.passage)
        self.passage.set_pos(Point3(-19.05, 17.7, -12))

        # water surface on the mid ground
        self.mid_water = WaterSurface(w=64.5, d=129)
        self.attach_nature(self.mid_water)
        self.mid_water.set_pos(Point3(32.25, 0, -60))

        # room under the mid ground
        self.basement = Basement()
        self.attach_nature(self.basement)
        self.basement.set_pos(-38.1466, -21.9663, -54.3114)

    def create_sensor(self):
        self.sensors = {}

        sensors = [
            [None, 4, 6, Sensors.TUNNEL, Point3(32.179, -3.35926, -15.7665), Vec3(-11, 0, 0)],    # big cave
            [None, 3, 4, Sensors.TUNNEL, Point3(-18.8616, 17.5443, -11.5), Vec3(-8, 0, 0)],       # small cave
            [None, 2, 6, Sensors.TUNNEL, Point3(5.4917, -17.8313, -14.3056), Vec3(64, 0, 0)],     # tunnel in the side of the bit cave
            [None, 2, 4, Sensors.TUNNEL, Point3(-19.2, 3.09684, -11.728), Vec3(31, 0, 0)],        # tunnel in the side of the small cave
            ['passage', 1.5, 1.5, Sensors.HOLE, Point3(-19.05, 17.6, -12), Vec3(-1.0, 0, 0)],     # hole to enter passage
            ['basement', 3, 3, Sensors.HOLE, Point3(-38.1466, -21.9663, -53.4), Vec3(0, 0, 0)],   # hole to enter basement
        ]

        for i, (name, width, depth, sensor, pos, hpr) in enumerate(sensors):
            nm = f'sensor_{i}' if not name else name
            underground_sensor = Sensor(nm, sensor, width, depth)
            underground_sensor.set_pos_hpr(pos, hpr)
            self.attach_nature(underground_sensor)
            self.sensors[nm] = underground_sensor

        sensors = [
            ['basement_', 3.5, 12, Sensors.STEPS, Point3(-38.1466, -23.5, -58.26), Vec3(0, 55.5, 0)],  # steps in the basement
            ['passage_', 1.5, 1.5, Sensors.MID_GROUND, Point3(-19.05, 17.6, -59.7), Vec3(0, 0, 0)],    # landing place of passage
        ]

        for i, (name, width, depth, sensor, pos, hpr) in enumerate(sensors):
            underground_sensor = Sensor(name, sensor, width, depth)
            underground_sensor.set_pos_hpr(pos, hpr)
            self.attach_nature(underground_sensor)
            parent_sensor = self.sensors[name[:-1]]
            parent_sensor.dest_sensor = underground_sensor

    def check_sensors(self, from_pos, mask, distance=-5):
        to_pos = from_pos + Vec3(0, 0, distance)

        if (hit := base.world.ray_test_closest(
                from_pos, to_pos, BitMask32.bit(mask))).has_hit():
            key = hit.get_node().get_name()
            sensor = self.sensors[key]
            return sensor