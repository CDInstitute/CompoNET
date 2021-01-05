import bpy, bmesh
from math import radians
import numpy as np
import os
import random
import sys

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)

from config import *
from blender_utils import extrude, gancio, get_min_max
from module import *
from shp2obj import Collection, deselect_all

MIN_HEIGHT = 3.0
MIN_WIDTH = 6.0
MIN_LENGTH = 6.0

MAX_HEIGHT = 30.0
MAX_WIDTH = 30.0
MAX_LENGTH = 30.0


class Factory:
	"""
	Factory that produces volumes.
	"""
	def __init__(self):
		self.min_width = MIN_WIDTH
		self.min_length = MIN_LENGTH
		self.min_height = MIN_HEIGHT
		self.max_width = MAX_WIDTH
		self.max_length = MAX_LENGTH
		self.max_height = MAX_HEIGHT

	def produce(self, scale=None):
		"""
		Function that produces a volume based on the given scale.
		:param scale: tuple (width, length, height)
		:return: generated volume, Volume
		"""
		if scale is None:
			return self._produce_random()
		v = Volume(scale)
		v.create()
		return v

	def _produce_random(self):
		"""
		Function that produces a volume based on random parameters.
		:return: generated volume, Volume
		"""
		v = Volume(scale=(np.random.randint(self.min_length, self.max_length),
		                  np.random.randint(self.min_width, self.max_width),
		                  np.random.randint(self.min_height, self.max_height)))
		return v


class CollectionFactory:
	"""
	Class that generates a collection of volumes based on their number.
	"""
	def __init__(self):
		self.volume_factory = Factory()

	def produce(self, number=None):
		"""
		Function that produces a collection of volumes
		:param number: number of volumes to compose the building of, int
		:return: building, Collection of Volumes
		"""
		return self._produce(number)

	def _produce(self, number):
		"""
		Function that produces a collection of volumes
		:param number: number of volumes to compose the building of, int
		if None will be chosen randomly from 1 to the MAX_VOLUMES in config.py
		:return: building, Collection of Volumes
		"""
		c = Collection(Volume)
		if not number:
			number = np.random.randint(1, MAX_VOLUMES+1)

		for _ in range(number):
			c.add(self.volume_factory.produce())

		return c


class ComposedBuilding:
	"""
	Class that represents a building composed of one or several volumes.
	"""
	def __init__(self, volumes):
		assert isinstance(volumes, list), "Expected volumes as list," \
		                                  " got {}".format(type(volumes))
		self.volumes = volumes

	def make(self):
		"""
		Function that composes the building based on its typology.
		:return:
		"""
		self._correct_volumes()
		return self.volumes

	def _correct_volumes(self):
		for v in self.volumes:
			v.create()


class LBuilding(ComposedBuilding):
	"""
	Class that represents an L-shaped building.
	"""
	def __init__(self, volumes):
		ComposedBuilding.__init__(self, volumes)

	def make(self):
		# add rotation if len > width (or vice versa)
		self._correct_volumes()
		gancio(self.volumes[0], self.volumes[1], 0, 0, 0)
		return self.volumes

	def _correct_volumes(self):

		if np.random.random() < 0.5:  # same height
			_height = max(min(self.volumes[0].height,
			                  min(self.volumes[0].width * 3, MAX_HEIGHT)),
			              MIN_HEIGHT)
			for v in self.volumes:
				v.height = _height

		for v in self.volumes:
			v.create()
		self.volumes = sorted(self.volumes, key=lambda x: x.length,
		                      reverse=True)


class CBuilding(LBuilding):
	def __init__(self, volumes):
		LBuilding.__init__(self, volumes)
		assert len(
			volumes) == 3, "C-shaped bulding can be composed of 3 volumes" \
		                   "only, got {}".format(len(volumes))

	def make(self):
		self._correct_volumes()
		for v in self.volumes[1:]:
			if v.width < v.length:
				v.mesh.rotation_euler[2] = radians(90)

		gancio(self.volumes[0], self.volumes[1], 0, 1, 0)
		gancio(self.volumes[0], self.volumes[2], 0, 0, 0)
		return self.volumes


class Patio(ComposedBuilding):
	"""
	Class that represents an L-shaped building.
	"""
	def __init__(self, volumes):
		ComposedBuilding.__init__(self, volumes)
		assert len(volumes) in [2, 4], "Patio bulding can be composed of 4 " \
		                               "volumes only, got {}".format(len(volumes))
		self.width = [3, 12]
		self.length = [6, 20]

	def make(self):

		self._correct_volumes()
		if np.random.random() < 0.5:
			# circular linkage between buildings
			for i, _v in enumerate(self.volumes[:-1]):
				if i % 2 == 0:
					self.volumes[i + 1].mesh.rotation_euler[2] = radians(90)
				if i == 0:
					gancio(_v, self.volumes[i + 1], 0, 1, 1)
				elif i == 1:
					gancio(_v, self.volumes[i + 1], 1, 1, 0)
				elif i == 2:
					gancio(_v, self.volumes[i + 1], 0, 0, 0)
		else:
			# cap linkage between buildings
			for i, _v in enumerate(self.volumes[:-1]):
				if i % 2 == 0:
					self.volumes[i + 1].mesh.rotation_euler[2] = radians(90)
				if i == 0:
					gancio(_v, self.volumes[i + 1], 1, 1, 0)
				elif i == 1:
					gancio(_v, self.volumes[i + 1], 1, 1, 0)
				elif i == 2:
					gancio(_v, self.volumes[i + 1], 1, 0, 1)

		return self.volumes

	def _correct_volumes(self):
		for v in self.volumes:
			v.width = min(max(v.width, self.width[0]), self.width[1])
			v.length = v.width * (np.random.random() + 1.5)
			v.height = max(min(v.height, min(v.width * 3, MAX_HEIGHT)), MIN_HEIGHT)
			v.create()
		self.volumes = sorted(self.volumes, key=lambda x: x.length)


class PatioEqual(Patio):
	"""
	Class that represents a Patio building with equal height volumes.
	"""

	def __init__(self, volumes):
		Patio.__init__(self, volumes)

	def _correct_volumes(self):
		_height = max(min(self.volumes[0].height, min(self.volumes[0].width * 3,
		                                              MAX_HEIGHT)), MIN_HEIGHT)
		for v in self.volumes:
			v.width = min(max(v.width, self.width[0]), self.width[1])
			v.length = v.width * (np.random.random() + 1.5)
			v.height = _height
			v.create()
		self.volumes = sorted(self.volumes, key=lambda x: x.length)


class ClosedPatio(Patio):
	"""
	Class that represents a Patio building with equal height volumes.
	"""

	def __init__(self, volumes):
		Patio.__init__(self, volumes)
		assert len(self.volumes) == 2, "Expected 2 volumes for Closed Patio, " \
		                               "got {}".format(len(self.volumes))

	def _correct_volumes(self):
		for v in self.volumes:
			v.width = min(max(v.width, self.width[0]), self.width[1])
			v.length = v.width * (np.random.random() + 1.5)
			v.height = max(min(v.height, min(v.width * 3, MAX_HEIGHT)),
		              MIN_HEIGHT)
			v.create()

		for v in self.volumes[:2]:
			v1 = Factory().produce(scale=(v.width, v.length, v.height))
			self.volumes.append(v1)


class TBuilding(ComposedBuilding):
	"""
	Class that represents a T-shaped building with random location of the
	second volume along the side of the first volume.
	"""
	def __init__(self, volumes):
		ComposedBuilding.__init__(self, volumes)
		assert len(volumes) == 2, "L-shaped bulding can be composed of 2 volumes" \
		                          "only, got {}".format(len(volumes))

	def make(self):
		self._correct_volumes()
		x_min, x_max = get_min_max(self.volumes[0].mesh, 0)  # width
		y_min, y_max = get_min_max(self.volumes[0].mesh, 1)  # length

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


class Skyscraper(ComposedBuilding):
	"""
	Class that represents a Skyscraper building with height significantly larger
	than width or length of the building.
	"""

	def __init__(self, volumes):
		ComposedBuilding.__init__(self, volumes)

	def _correct_volumes(self):
		for _v in self.volumes:
			_v.height = np.random.randint(100, 200)
			_v.length = max(30, _v.length)
			_v.width = max(30, _v.width)
			_v.create()


class EBuilding(ComposedBuilding):
	"""
	Class that represents a E-shaped building with random locations of the
	volumes along the side of the first volume.
	"""
	def __init__(self, volumes):
		ComposedBuilding.__init__(self, volumes)

	def make(self):

		self._correct_volumes()
		x_min, x_max = get_min_max(self.volumes[0].mesh, 0)  # width
		y_min, y_max = get_min_max(self.volumes[0].mesh, 1)  # length

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
	"""
	Class that represents one volume of a building.
	"""
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
		"""
		Function that creates a mesh based on the input parameters.
		:return:
		"""

		bpy.ops.mesh.primitive_plane_add(location=self.position)
		bpy.ops.transform.resize(value=(self.length, self.width, 1.0))
		bpy.context.selected_objects[0].name = 'volume'
		self.name = bpy.context.selected_objects[0].name
		self.mesh = bpy.data.objects[self.name]
		self._nest()
		self._extrude()
		deselect_all()

	def _extrude(self):
		"""
		Function that extrudes the plane in order to create a mesh.
		:return:
		"""
		deselect_all()
		if self.mesh:
			extrude(self.mesh, self.height)

	def _nest(self):
		if not self.name in bpy.data.collections['Building'].objects:
			bpy.data.collections['Building'].objects.link(
					bpy.data.objects[self.name])


class Renderer:
	"""
	Class that manages the scene rendering. Incomplete.
	"""
	def __init__(self):
		0

	def render(self):
		self._render()

	def _render(self):
		"""
		Function that renders the scene.
		:return:
		"""
		bpy.data.scenes[self._scene_name].render.engine = 'CYCLES'
		bpy.ops.render.render()

	def _render_mask(self):
		"""
		Function that renders the scene as a one-channel mask.
		:return:
		"""
		raise NotImplementedError

	def _render_keypoints(self):
		"""
		Function that renders the scene as a one-channel mask of predefined
		keypoints.
		:return:
		"""
		raise NotImplementedError


if __name__ == '__main__':
	f = CollectionFactory()
	collection = f.produce(number=3)
	building = CBuilding(collection.collection)
	building.make()

	axis = 1

	for j, v in enumerate(collection.collection):

		mod = GridApplier(Window)
		w = Window()
		w.connect(v, 1)
		if j==0:
			mod.apply(w, step=(3, 3), offset=(3.0, 10.0, 3.0, 1.0))
		else:
			mod.apply(w, step=(3, 3))


