from panda3d.core import NodePath, PandaNode, BitMask32, Point3, Vec3
from panda3d.core import Filename, PNMImage
from panda3d.core import ShaderTerrainMesh, Shader
from panda3d.core import SamplerState, TextureStage

from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletTriangleMeshShape, BulletHeightfieldShape, ZUp
from panda3d.bullet import BulletConvexHullShape, BulletTriangleMesh, BulletTriangleMeshShape
from panda3d.core import GeoMipTerrain, TransformState, SamplerState
from panda3d.core import RenderAttrib, AlphaTestAttrib, TransparencyAttrib

from shapes.src import Sphere, Cylinder, Torus


class Cave(NodePath):

    def __init__(self, radius=6.0, inner_radius=5.0, length=10):
        super().__init__(BulletRigidBodyNode('terrain_root'))
        self.radius = radius
        self.inner_radius = inner_radius
        self.length = length
        self.model = self.create_model()
        self.model.reparent_to(self)
        self.set_collide_mask(BitMask32.bit(3))

    def create_model(self):
        cylinder_geom_nd = Cylinder(
            radius=self.radius,
            inner_radius=self.inner_radius,
            height=self.length
        ).get_geom_node()

        maker = Sphere(
            radius=self.radius,
            inner_radius=self.inner_radius,
            slice_deg=180
        )

        # Connect hemisphere to cylinder
        hemishere_geom_nd = maker.get_geom_node()
        hemi_geom = hemishere_geom_nd.modify_geom(0)

        vdata = hemi_geom.modify_vertex_data()
        maker.tranform_vertices(vdata, Vec3(0, 1, 0), Point3(0, 0, 0), 180)
        vert_cnt = vdata.get_num_rows()
        vdata_mem = memoryview(vdata.modify_array(0)).cast('B').cast('f')
        prim = hemi_geom.modify_primitive(0)
        prim_array = prim.modify_vertices()
        prim_mem = memoryview(prim_array).cast('B').cast('H')
        maker.add(cylinder_geom_nd, vdata_mem, vert_cnt, prim_mem)

        model = maker.modeling(cylinder_geom_nd)
        mesh = BulletTriangleMesh()
        mesh.add_geom(model.node().get_geom(0))
        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        self.node().add_shape(shape)

        tex = base.loader.load_texture('textures/concrete_01.jpg')
        self.set_texture(tex)
        return model


class Tunnel(NodePath):

    def __init__(self):
        super().__init__(BulletRigidBodyNode('tunnel'))
        maker = Cylinder(
            radius=4,
            inner_radius=3,
            height=36,
        )
        model = maker.create()

        mesh = BulletTriangleMesh()
        mesh.add_geom(model.node().get_geom(0))
        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        self.node().add_shape(shape)
        self.set_collide_mask(BitMask32.bit(3))

        tex = base.loader.load_texture('textures/concrete_01.jpg')
        self.set_texture(tex)

        model.reparent_to(self)


class CurvedTunnel(NodePath):

    def __init__(self):
        super().__init__(BulletRigidBodyNode('curved_tunnel'))
        maker = Torus(
            ring_radius=20,
            section_radius=8,
            section_inner_radius=5,
            ring_slice_deg=180
        )
        model = maker.create()

        mesh = BulletTriangleMesh()
        mesh.add_geom(model.node().get_geom(0))
        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        self.node().add_shape(shape)
        self.set_collide_mask(BitMask32.bit(3))

        tex = base.loader.load_texture('textures/concrete_01.jpg')
        self.set_texture(tex)

        model.reparent_to(self)


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
        # self.root.set_scale(scale)
        self.root.set_sz(self.height)

        self.root.set_pos(pos)

        self.terrain.generate()
        self.root.reparent_to(self)
        # self.root.set_attrib(greater_filter)

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


class Scene(NodePath):

    def __init__(self):
        super().__init__(PandaNode('scene'))

        tex_files = [
            ('stones_01.jpg', 20),
            ('grass_02.png', 10),
        ]
        # self.terrain = Terrain('image8_voronoi.png', 50, tex_files)
        # # self.terrain = Terrain('cave_terrain2.png', 100, tex_files)
        # self.terrain.reparent_to(self)
        # base.world.attach(self.terrain.node())
        # center_x: 75, center_y: 118



        self.base_terrain = Terrain('ground.png', 10, tex_files)  
        self.base_terrain.reparent_to(self)
        base.world.attach(self.base_terrain.node())
        self.base_terrain.set_z(-12)

        tex_files = [
            ('grass_04.jpg', 10),
            ('grass_03.jpg', 10),
        ]
        self.terrain2 = Terrain('cliff_terrain6.png', 100, tex_files, mask=2)
        self.terrain2.root.setTwoSided(True)
        self.terrain2.reparent_to(self)
        base.world.attach(self.terrain2.node())
        self.terrain2.set_z(0)  #-12


        self.tunnel = Tunnel()
        self.tunnel.set_pos_hpr(Point3(-23.9903, 2.8243, -10.6965), Vec3(51, 92, 0))
        self.tunnel.reparent_to(self)
        base.world.attach(self.tunnel.node())

        self.cave = Cave()
        self.cave.reparent_to(self)
        base.world.attach(self.cave.node())
        self.cave.set_pos_hpr(Point3(34.8145, 8.42185, -11.7908), Vec3(-16, 90, 0))
       