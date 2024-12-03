import math

from panda3d.core import NodePath, PandaNode, BitMask32, Point3, Vec3
from panda3d.core import Filename, PNMImage
from panda3d.core import ShaderTerrainMesh, Shader
from panda3d.core import SamplerState, TextureStage

from panda3d.bullet import BulletRigidBodyNode, BulletBoxShape
from panda3d.bullet import BulletTriangleMeshShape, BulletHeightfieldShape, ZUp
from panda3d.bullet import BulletConvexHullShape, BulletTriangleMesh, BulletTriangleMeshShape, BulletBoxShape
from panda3d.core import GeoMipTerrain, TransformState, SamplerState
from panda3d.core import RenderAttrib, AlphaTestAttrib, TransparencyAttrib

from shapes.src import Sphere, Cylinder, Torus, Plane, Box, Cone, RightTriangularPrism


class Cave(NodePath):

    def __init__(self, width, depth, wall_height, thickness, mask=3):
        super().__init__(BulletRigidBodyNode('terrain_root'))
        self.width = width
        self.depth = depth
        self.wall_height = wall_height
        self.thickness = thickness

        self.model = self.create_model()
        self.model.reparent_to(self)

        mesh = BulletTriangleMesh()
        mesh.add_geom(self.model.node().get_geom(0))
        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        self.node().add_shape(shape)
        self.set_collide_mask(BitMask32.bit(mask))

        tex = base.loader.load_texture('textures/concrete_01.jpg')
        self.set_texture(tex)
        # self.flatten_strong()

    def create_model(self):
        # side walls
        maker = Box(
            width=self.width,
            depth=self.depth,
            height=self.wall_height,
            thickness=self.thickness,
            open_bottom=True,
            open_front=True,
            open_top=True,
            open_back=True
        )

        radius = self.width / 2
        inner_radius = self.width / 2 - self.thickness
        half_h = self.wall_height / 2
        half_d = self.depth / 2

        # rear wall
        rear_wall = Cylinder(
            radius=radius,
            inner_radius=inner_radius,
            height=self.wall_height,
            segs_a=self.wall_height,
            ring_slice_deg=180)

        # round_roof
        round_roof = Cylinder(
            radius=radius,
            inner_radius=inner_radius,
            height=self.depth,
            segs_a=self.depth,
            ring_slice_deg=180)

        # rear round roof
        rear_roof = Sphere(
            radius=radius,
            inner_radius=inner_radius,
            slice_deg=270)

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


class Tunnel(NodePath):

    def __init__(self, name, mask):
        super().__init__(BulletRigidBodyNode(name))
        self.set_collide_mask(BitMask32.bit(mask))
        self.build_tunnel()

    def setup_model(self, model, name, pos, hpr):
        model.set_pos_hpr(pos, hpr)
        model.set_name(name)
        model.reparent_to(self)

        mesh = BulletTriangleMesh()
        mesh.add_geom(model.node().get_geom(0))
        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        self.node().add_shape(shape, TransformState.make_pos_hpr(pos, hpr))


class SquareTunnel(Tunnel):

    def __init__(self, mask=3):
        super().__init__('square_tunnel', mask)

    def build_tunnel(self):
        tunnel_maker = Box(width=5, depth=30, height=5, segs_w=5, segs_d=30, segs_z=5,
                           open_bottom=True, open_front=True, open_back=True)

        gate_maker = Box(width=6, depth=4, height=6, segs_w=6, segs_d=4, segs_z=6,
                         thickness=2, open_bottom=True, open_front=True, open_back=True)

        parts = [
            [tunnel_maker, Point3(0, 0, 0), Vec3(51, 5, 0)],
            [gate_maker, Point3(13.0778, -10.635, -0.5477), Vec3(64, 0, 0)],
            [gate_maker, Point3(-10.9222, 9.36504, 1.45235), Vec3(31, 0, 0)]
        ]

        for i, (parts_maker, pos, hpr) in enumerate(parts):
            model = parts_maker.create()
            self.setup_model(model, f'parts_{i}', pos, hpr)

        tex = base.loader.load_texture('textures/tile2.jpg')
        self.set_texture(tex)


class RoundTunnel(Tunnel):

    def __init__(self, mask=3):
        super().__init__('round_tunnel', mask)

    def build_tunnel(self):
        model = Box(width=4, depth=4, height=2, segs_w=4, segs_d=4, segs_z=2,
                    thickness=1, open_bottom=True, open_top=True).create()
        self.setup_model(model, 'parts_1', Point3(0, 0, 0), Vec3(180, 5, -8))

        model = Cylinder(radius=1.5, height=43.5, segs_top_cap=0, segs_bottom_cap=0).create()
        self.setup_model(model, 'parts_2', Point3(0, 0, 0), Vec3(0, 180, 0))

        model = Box(width=4, depth=4, height=4, segs_w=4, segs_d=4, segs_z=4,
                    thickness=1, open_bottom=True, open_top=True).create()
        self.setup_model(model, 'parts_3', Point3(0, 0, -42.5), Vec3(0, 0, 0))

        model = Box(width=4, depth=4, height=6, segs_w=4, segs_d=4, segs_z=6,
                    thickness=1, open_bottom=True, open_top=True, open_left=True, open_back=True).create()
        self.setup_model(model, 'parts_4', Point3(0, 0, -47.5), Vec3(0, 0, 0))

        tex = base.loader.load_texture('textures/metalboard.jpg')
        self.set_texture(tex)


class Terrain(NodePath):

    def __init__(self, heightmap, height, tex_files, mask=1):
        super().__init__(BulletRigidBodyNode('terrain_root'))
        self.heightmap = heightmap
        self.height = height

        # self.set_transparency(TransparencyAttrib.MAlpha)

        self.node().set_mass(0)
        self.set_collide_mask(BitMask32.bit(mask))
        # shape = BulletHeightfieldShape(base.loader.load_texture(self.heightmap), self.height, ZUp)
        img = PNMImage(Filename(self.heightmap))
        shape = BulletHeightfieldShape(img, self.height, ZUp)
        shape.set_use_diamond_subdivision(True)
        self.node().add_shape(shape)
        self.generate_terrain(tex_files)

    def generate_terrain(self, tex_files):
        # greater_filter = AlphaTestAttrib.make(RenderAttrib.M_greater, 0.5)
        # self.terrain_root.set_attrib(greater_filter)

        img = PNMImage(Filename(self.heightmap))
        self.terrain = GeoMipTerrain('geomip_terrain')
        self.terrain.set_heightfield(self.heightmap)
        self.terrain.set_border_stitching(True)
        self.terrain.set_block_size(8)
        self.terrain.set_min_level(2)
        self.terrain.set_focal_point(base.camera)


        size_x, size_y = img.get_size()
        x = (size_x - 1) / 2
        y = (size_y - 1) / 2
        # x = size_x / 2 - 0.5
        # y = size_y / 2 - 0.5
       
        pos = Point3(-x, -y, -(self.height / 2))
        scale = Vec3(1, 1, self.height)
        self.root = self.terrain.get_root()
        self.root.set_sz(self.height)

        self.root.set_pos(pos)

        self.terrain.generate()
        self.root.reparent_to(self)


        shader = Shader.load(Shader.SL_GLSL, 'shaders/terrain_v.glsl', 'shaders/terrain_f.glsl')
        self.root.set_shader(shader)

        # tex_files = [
        #     ('stones_01.jpg', 20),
        #     ('grass_02.png', 10),
        # ]

        for i, (file_name, tex_scale) in enumerate(tex_files):
            ts = TextureStage(f'ts{i}')
            ts.set_sort(i)
            self.root.set_shader_input(f'tex_ScaleFactor{i}', tex_scale)
            tex = base.loader.load_texture(f'textures/{file_name}')
            self.root.set_texture(ts, tex)

        # i = 2
        # ts = TextureStage(f'ts{i}')
        # ts.set_sort(i)
        self.root.set_shader_input('heightmap', base.loader.load_texture(self.heightmap))

    def make_hole(self):
        pass
        # import pdb; pdb.set_trace()
        # np = self.terrain.getBlockNodePath(0, 0)
        # geom = np.node().modifyGeom(0)
        # vdata = geom.modifyVertexData()
        # old_count = vdata.get_num_rows()
        # v_array = vdata.modify_array(0)
        # size = 100 * 8
        # start = 5 * size
        # view = memoryview(v_array).cast('B')
        # view[start:-size] = view[start + size:]
        # vdata.set_num_rows(old_count - 10)
        # tris_prim = geom.modify_primitive(0)
        # old_count = tris_prim.get_num_vertices()
        # start = 5 * 6
        # tris_prim.offset_vertices(-10, start + 6, old_count)
        # tris_array = tris_prim.modify_vertices()
        # view = memoryview(tris_array).cast('B').cast('H')
        # view[start:-6] = view[start + 6:]
        # tris_array.set_num_rows(old_count - 6)

        # shapeをつくるタイミングを変えても、何の影響もない。一番最後にしても影響ない。
        # shape = BulletHeightfieldShape(self.loader.load_texture(heightmap), height, ZUp)
        # shape = BulletHeightfieldShape(img, height, ZUp)
        # shape.set_use_diamond_subdivision(True)
        # self.terrain_root.node().add_shape(shape)


class Sensor(NodePath):

    def __init__(self, name, width, depth, mask=4):
        super().__init__(BulletRigidBodyNode(f'sensor_{name}'))
        self.create_sensor(width, depth)
        self.node().set_mass(0)
        self.set_collide_mask(BitMask32.bit(mask))
        self.set_shader_off()

    def create_sensor(self, width, depth):
        model = Plane(width, depth, segs_w=4, segs_d=4).create()
        model.set_transparency(TransparencyAttrib.MAlpha)
        # model.set_color(1, 1, 1, 1)
        model.set_color(1, 1, 1, 0)
        model.reparent_to(self)

        mesh = BulletTriangleMesh()
        mesh.add_geom(model.node().get_geom(0))
        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        self.node().add_shape(shape)


class WaterSurface(NodePath):

    def __init__(self, w=256, d=256, segs_w=16, segs_d=16, mask=1):
        super().__init__(BulletRigidBodyNode('water_surface'))
        self.create_surface(w, d, segs_w, segs_d)
        self.node().set_mass(0)
        self.set_collide_mask(BitMask32.bit(mask))
        self.set_shader_off()

    def create_surface(self, w, d, segs_w, segs_d):
        plane = Plane(w, d, segs_w, segs_d)
        self.stride = plane.stride

        self.model = plane.create()
        self.model.set_transparency(TransparencyAttrib.MAlpha)
        self.model.set_texture(base.loader.load_texture('textures/water.png'))
        self.model.set_pos(Point3(0, 0, 0))
        self.model.reparent_to(self)

        mesh = BulletTriangleMesh()
        mesh.add_geom(self.model.node().get_geom(0))
        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        self.node().add_shape(shape)

    def wave(self, time, wave_h=2.0):
        geom_node = self.model.node()
        geom = geom_node.modify_geom(0)
        vdata = geom.modify_vertex_data()
        vdata_arr = vdata.modify_array(0)
        vdata_mem = memoryview(vdata_arr).cast('B').cast('f')

        for i in range(0, len(vdata_mem), self.stride):
            x, y = vdata_mem[i: i + 2]
            z = (math.sin(time + x / wave_h) + math.sin(time + y / wave_h)) * wave_h / 2
            vdata_mem[i + 2] = z


class Rock(NodePath):

    def __init__(self, adjacent, opposite, height, name, tex_path, mask=3):
        super().__init__(BulletRigidBodyNode(f'rock_{name}'))
        self.create_model(adjacent, opposite, height)
        self.set_collide_mask(BitMask32.bit(mask))

        tex = base.loader.load_texture(tex_path)
        self.set_texture(tex)

    def create_model(self, adjacent, opposite, height):
        model = RightTriangularPrism(
            adjacent=adjacent,
            opposite=opposite,
            height=height,
            slice_caps_radial=4
        ).create()

        shape = BulletConvexHullShape()
        shape.add_geom(model.node().get_geom(0))
        self.node().add_shape(shape)
        model.reparent_to(self)


class Scene(NodePath):

    def __init__(self):
        super().__init__(PandaNode('scene'))
        self.create_top_layer()
        self.create_middle_layer()

    def attach_nature(self, model):
        model.reparent_to(self)
        base.world.attach(model.node())

    def create_top_layer(self):
        tex_files = [
            ('grass_05.jpg', 10),
            ('grass_02.png', 20),
        ]
        self.top_ground = Terrain('top_ground.png', 10, tex_files)
        self.attach_nature(self.top_ground)
        self.top_ground.set_z(-12)

        tex_files = [
            ('stone_01.jpg', 10),
            ('grass_03.jpg', 10),
        ]
        self.top_mountains = Terrain('top_terrain.png', 100, tex_files, mask=2)
        self.top_mountains.root.set_two_sided(True)
        self.attach_nature(self.top_mountains)
        self.top_mountains.set_z(0)

        self.tunnel = SquareTunnel()
        self.attach_nature(self.tunnel)
        self.tunnel.set_pos(Point3(-7.8244, -7.0682, -10.6803))

        self.cave = Cave(width=8, depth=10, wall_height=10, thickness=1.5)
        self.attach_nature(self.cave)
        self.cave.set_pos_hpr(Point3(32.8145, 5.4219, -13.7908), Vec3(-11, 0, 0))

        self.small_cave = Cave(width=6, depth=8, wall_height=4, thickness=1.5)
        self.attach_nature(self.small_cave)
        self.small_cave.set_pos_hpr(Point3(-18.5, 20.8, -12), Vec3(-7, -24, 0))

        self.passage = RoundTunnel()
        self.attach_nature(self.passage)
        self.passage.set_pos(Point3(-19.05, 17.6, -12))

        rocks = [
            [6, 8, 1.5, Point3(35.4, -2.83341, -12.0633), Vec3(171, 30, 89)],
            [6, 9, 1.5, Point3(29, -1.8, -11.8), Vec3(173, 30, 90)],
        ]
        for i, (adjacent, opposite, height, pos, hpr) in enumerate(rocks):
            rock = Rock(adjacent, opposite, height, f'rock_{i}', 'textures/stone_01.jpg')
            rock.set_pos_hpr(pos, hpr)
            self.attach_nature(rock)

        sensors = [
            [1.5, 1.5, 5, Point3(-19.05, 17.6, -11), Vec3(-1.0, 0, 0)],
            [3, 4, 4, Point3(-18.8616, 17.5443, -11.5), Vec3(-8, 0, 0)],
            [4, 6, 4, Point3(31.179, -2.85926, -15.7665), Vec3(-22, 0, 0)],
            [2, 6, 4, Point3(5.4917, -17.8313, -14.3056), Vec3(64, 0, 0)],
            [2, 4, 4, Point3(-19.2, 3.09684, -11.728), Vec3(31, 0, 0)],
        ]

        self.sensors = NodePath('sensors')
        self.sensors.reparent_to(self)

        for i, (width, depth, mask, pos, hpr) in enumerate(sensors):
            if i == 0:
                self.sensor = Sensor(i, width, depth, mask=mask)
                self.sensor.set_pos_hpr(pos, hpr)
                self.attach_nature(self.sensor)
                continue

            sensor = Sensor(i, width, depth, mask=mask)
            sensor.set_pos_hpr(pos, hpr)
            self.attach_nature(sensor)


    def create_middle_layer(self):
        tex_files = [
            ('stone_01.jpg', 10),
            ('grass_03.jpg', 10),
        ]
        # self.mid_mountains = Terrain('mid_terrain.png', 100, tex_files, mask=2)
        self.mid_mountains = Terrain('mid_terrain.png', 100, tex_files, mask=1)
        self.mid_mountains.root.setTwoSided(True)
        self.attach_nature(self.mid_mountains)
        self.mid_mountains.set_z(-48)  #-50

        tex_files = [
            ('stone_01.jpg', 20),
            ('stones_01.jpg', 20),
        ]

        self.mid_ground = Terrain('mid_ground.png', 20, tex_files)
        self.attach_nature(self.mid_ground)
        self.mid_ground.set_z(-56)   # -58

        self.mid_water = WaterSurface(d=129, w=129)
        self.attach_nature(self.mid_water)
        self.mid_water.set_z(-60)  # -62

    def get_layer(self, nd):
        if nd == self.top_ground.node():
            return self.mid_ground.node()
