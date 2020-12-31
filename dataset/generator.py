import bpy, bmesh
import numpy as np
import os
import random
import sys

sys.path.append('D:/Google Drive/Portfolio/references_for_portfolio/WORK/##/CompoNET')
from config import *
from shp2obj import *

filename = 'test.gltf'


def get_min_max(volume, axis):
	"""
	Function that returns limits of a Volume on the indicated axis
	:param volume: volume to get the dims of, class Volume
	:param axis: int, 0 - width; 1 - length; 2 - height
	:return: min, max, float
	"""

	return min([x[axis:axis+1][0] for x in volume.mesh.bound_box]),\
	       max([x[axis:axis+1][0] for x in volume.mesh.bound_box])


class Factory:
	def __init__(self):
		0

	def produce(self, scale=(MIN_WIDTH, MIN_LENGTH, MIN_HEIGHT)):
		v = Volume(scale)
		v.create()
		return v

	def produce_random(self):
		v = Volume(scale=(np.random.randint(MIN_LENGTH, MAX_LENGTH),
		                  np.random.randint(MIN_WIDTH, MAX_WIDTH),
		                  np.random.randint(MIN_HEIGHT, MAX_HEIGHT)))
		v.create()
		return v


class CollectionFactory:
	def __init__(self):
		self.volume_factory = Factory()

	def produce(self, number=None):
		return self._produce(number)

	def _produce(self, number):
		c = Collection(Volume)
		if not number:
			number = np.random.randint(1, MAX_VOLUMES+1)

		for _ in range(number):
			c.add(self.volume_factory.produce_random())

		return c


class ComposedBuilding:
	def __init__(self, volumes):
		assert isinstance(volumes, list), "Expected volumes as list," \
		                                  " got {}".format(type(volumes))
		self.volumes = volumes

	def make(self):
		return self.volumes


class LBuilding(ComposedBuilding):
	def __init__(self, volumes):
		ComposedBuilding.__init__(self, volumes)
		assert len(volumes) == 2, "L-shaped bulding can be composed of 2 volumes" \
		                          "only, got {}".format(len(volumes))

	def make(self):

		x_min, x_max = get_min_max(self.volumes[0], 0)  # width
		y_min, y_max = get_min_max(self.volumes[0], 1)  # length

		self.volumes[1].mesh.location[0] = x_min + (self.volumes[1].length)
		self.volumes[1].mesh.location[1] = y_min + (self.volumes[1].width)

		return self.volumes


class TBuilding(ComposedBuilding):
	def __init__(self, volumes):
		ComposedBuilding.__init__(self, volumes)
		assert len(volumes) == 2, "L-shaped bulding can be composed of 2 volumes" \
		                          "only, got {}".format(len(volumes))

	def make(self):

		x_min, x_max = get_min_max(self.volumes[0], 0)  # width
		y_min, y_max = get_min_max(self.volumes[0], 1)  # length

		if random.random() < 0.5:
			self.volumes[1].mesh.location[0] = random.choice(np.linspace(int(x_min + (self.volumes[1].length)),
				      int(x_max - (self.volumes[1].length)), 10))
			self.volumes[1].mesh.location[1] = y_min - self.volumes[1].width

		else:
			self.volumes[1].mesh.location[1] = random.choice(np.linspace(
				int(y_min + (self.volumes[1].width)),
				int(y_max - (self.volumes[1].width)), 10))
			self.volumes[1].mesh.location[0] = x_min - self.volumes[1].length

		return self.volumes


class EBuilding(ComposedBuilding):
	def __init__(self, volumes):
		ComposedBuilding.__init__(self, volumes)

	def make(self):

		x_min, x_max = get_min_max(self.volumes[0], 0)  # width
		y_min, y_max = get_min_max(self.volumes[0], 1)  # length

		if random.random() < 0.5:
			for _volume in self.volumes[1:]:
				_volume.mesh.location[0] = random.choice(np.linspace(int(x_min + (_volume.length)),
					      int(x_max - (_volume.length)), 10))
				_volume.mesh.location[1] = y_min - _volume.width

		else:
			for _volume in self.volumes[1:]:
				_volume.mesh.location[1] = random.choice(np.linspace(
					int(y_min + (_volume.width)),
					int(y_max - (_volume.width)), 10))
				_volume.mesh.location[0] = x_min - _volume.length

		return self.volumes


class Volume:
	def __init__(self, scale=(1.0, 1.0, 1.0), location=(0.0, 0.0, 0.0)):
		assert len(location) == 3, "Expected 3 location coordinates," \
		                           " got {}".format(len(location))
		assert len(scale) == 3, "Expected 3 scale coordinates," \
		                        " got {}".format(len(scale))

		assert max([1 if (issubclass(x.__class__, int) or
		                  issubclass(x.__class__, float)) else 0 for x in
		            scale+location]) == 1, "Expected numeric tuples scale and location"

		##############################################

		self.height = float(max(MIN_HEIGHT, scale[2]))
		self.width = float(max(MIN_WIDTH, scale[0]))
		self.length = float(max(MIN_LENGTH, scale[1]))
		self.position = location
		self.name = ''
		self.mesh = None

	def create(self):
		bpy.ops.mesh.primitive_plane_add(enter_editmode=True, location=self.position)
		bpy.ops.transform.resize(value=(self.length, self.width, 1.0))
		self.name = bpy.data.objects[-1].name
		self.mesh = bpy.data.objects[self.name]
		self._extrude()

	def _extrude(self):
		deselect_all()
		if self.mesh:
			self.mesh.select_set(True)
			bpy.ops.object.mode_set(mode='EDIT')
			bpy.ops.mesh.select_mode(type='FACE')  # Change to face selection
			bpy.ops.mesh.select_all(action='SELECT')  # Select all faces

			bm = bmesh.new()
			bm = bmesh.from_edit_mesh(bpy.context.object.data)

			# Extude Bmesh
			for f in bm.faces:
				face = f.normal
			r = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
			verts = [e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)]
			TranslateDirection = face * -self.height  # Extrude Strength/Length
			bmesh.ops.translate(bm, vec=TranslateDirection, verts=verts)

			# Update & Destroy Bmesh
			bmesh.update_edit_mesh(
				bpy.context.object.data)  # Write the bmesh back to the mesh
			bm.free()  # free and prevent further access

			# Flip normals
			bpy.ops.mesh.select_all(action='SELECT')
			bpy.ops.mesh.flip_normals()

			# At end recalculate UV
			bpy.ops.mesh.select_all(action='SELECT')
			bpy.ops.uv.smart_project()

			# Switch back to Object at end
			bpy.ops.object.mode_set(mode='OBJECT')

			# Origin to center
			bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')


class Renderer:
	def __init__(self):
		0

	def render(self):
		self._render()

	def _render(self):
		bpy.data.scenes[self._scene_name].render.engine = 'CYCLES'
		bpy.ops.render.render()


if __name__ == '__main__':
	f = CollectionFactory()
	collection = f.produce()
	building = EBuilding(collection.collection)
	building.make()


