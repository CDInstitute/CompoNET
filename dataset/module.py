import bpy, bmesh
from contextlib import redirect_stdout, redirect_stderr
from copy import copy
import io
import math
import numpy as np
import os
import random
import sys

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)

stdout = io.StringIO()
from config import *
from blender_utils import gancio, get_min_max
from shp2obj import Collection, deselect_all


class Connector:
	def __init__(self, module, volume, axis):
		self.module = module
		self.axis = axis
		self.volume = volume
		self._connect()

	def _connect(self):
		gancio(self.volume, self.module, self.axis, 0, 1)


class Module:
	def __init__(self, name='generic', scale=None):
		self.name = name
		self.connector = None
		self.scale = scale
		self.mesh = self._create()
		self.parent = self._nest()

	def __copy__(self):
		m = self.__class__(self.name, scale=self.scale)
		if self.connector:
			m.connect(self.connector.volume, self.connector.axis)
		return m

	def connect(self, volume, axis):
		self._connect(volume, axis)

	def position(self, position):
		assert isinstance(position, list) or isinstance(position, tuple) or \
		       isinstance(position, np.ndarray), "Expected position as a list or" \
		                                        " a tuple, got {}".format(type(position))
		assert len(position) == 3, "Position should have 3 values, " \
		                           "got {}".format(len(position))

		for i in range(len(position)):
			self.mesh.location[i] += position[i]

	def remove(self):
		deselect_all()
		bpy.data.objects[self.mesh.name].select_set(True)
		with redirect_stdout(stdout), redirect_stderr(stdout):
			bpy.ops.object.delete()

	def _connect(self, volume, axis):
		self.connector = self.ModuleConnector(self, volume, axis)

	def _create(self):
		# rule how connects to mesh
		raise NotImplementedError

	def _nest(self):
		names = [x.name for x in bpy.data.collections]
		if self.name not in names:
			bpy.data.collections.new(self.name)
			bpy.data.collections['Building'].children.link(
				bpy.data.collections[self.name])
		bpy.data.collections[self.name].objects.link(bpy.data.objects[self.mesh.name])
		return bpy.data.collections[self.name]

	class ModuleConnector(Connector):
		def __init__(self, module, volume, axis):
			Connector.__init__(self, module, volume, axis)


class Window(Module):
	def __init__(self, name='window', scale=(1.5, 0.05, 1.5)):
		Module.__init__(self, name, scale)

	def _create(self):
		bpy.ops.mesh.primitive_cube_add(size=1.0)
		bpy.ops.transform.resize(value=self.scale)
		bpy.context.selected_objects[0].name = self.name
		return bpy.context.selected_objects[0]

	class ModuleConnector(Connector):
		def __init__(self, module, volume, axis):
			Connector.__init__(self, module, volume, axis)

		def _connect(self):
			if self.axis == 0:
				self.module.mesh.rotation_euler = math.radians(90)
			gancio(self.volume, self.module, self.axis, 0, 1)


class ModuleFactory:
	"""
	Factory that produces volumes.
	"""
	def __init__(self):
		self.mapping = {'generic': Module,
		                'window': Window}

	def produce(self, name):
		"""
		Function that produces a module based on its name.
		:param name: name of the module to produce, str, should be in mapping
		:return: generated module, Module
		"""
		if name in list(self.mapping.keys()):
			return self.mapping[name]()
		else:
			return self.mapping['generic']()


class ModuleApplier:
	def __init__(self, module_type):
		self.module_type = module_type
		self.name = 'single'

	def apply(self, module, position):
		self._apply(module, position)

	def _apply(self, module, position):
		assert issubclass(module.__class__,
		                  self.module_type), "This ModuleApplier is applicable" \
		                                     " only to {], got {}".format(self.module_type,
		                                                                  type(module))
		module.position(position)


class GridApplier(ModuleApplier):
	"""
	Vertical Grid Applier.
	"""
	def __init__(self, module_type):
		ModuleApplier.__init__(self, module_type)
		self.name = 'grid'

	def apply(self, module, grid=None, offset=(1.0, 1.0, 1.0, 1.0), step=None):
		self._apply(module, grid, offset, step)

	def _apply(self, module, grid, offset, step):
		"""

		:param module: module to apply to the volume, Module
		:param grid: parameters of the grid for the module application, tuple
		(rows, cols), int. If step is given, not taken into account
		:param offset: offset from the borders of the volume, tuple
		(left, bottom, right, top), default = (1.0, 1.0, 1.0, 1.0)
		:param step: parameter of the grid, tuple (hor_step, vert_step),
		default=None
		:return:
		"""
		assert grid or step, "Please, provide either grid or step parameter"
		if grid:
			assert isinstance(grid, list) or isinstance(grid, tuple) or\
			       isinstance(grid, np.ndarray), "expected grid to be a list or a " \
			                                     "tuple, got {}".format(type(grid))
			assert len(grid) == 2, "Expected grid to have two elements, got" \
			                       " {}".format(len(grid))
		if step:
			assert isinstance(step, list) or isinstance(step, tuple) or\
			       isinstance(step, np.ndarray), "expected step to be a list or a " \
			                                     "tuple, got {}".format(type(step))
			assert len(step) == 2, "Expected step to have two elements, got" \
			                       " {}".format(len(step))

		assert isinstance(offset, list) or isinstance(offset, tuple) or isinstance(
			offset, np.ndarray), "expected offset to be a list or a " \
		                         "tuple, got {}".format(type(offset))
		assert len(offset) == 4, "Expected offset to have two elements, got " \
		                         "{}".format(len(offset))
		assert module.connector is not None, "Module should be connected to a volume"

		axis = module.connector.axis
		_start1 = int(offset[0] + module.scale[abs(1-axis)] / 2)
		_start2 = int(offset[1] + module.scale[2] / 2)
		_end1 = int(np.diff(get_min_max(module.connector.volume.mesh, abs(1-axis))) -
		               (int(offset[2] + module.scale[abs(1-axis)] / 2)))
		_end2 = int(module.connector.volume.height -
		           (int(offset[2] + module.scale[abs(1-axis)] / 2)))

		if step:
			step_x, step_h = step
		else:
			step_x, step_h = int((_end1 - _start1) / grid[0]),\
			                 int((_end2 - _start2) / grid[1])
			if step_x == 0:
				step_x = math.ceil((_end1 - _start1) / grid[0])
			if step_h == 0:
				step_h = math.ceil((_end2 - _start2) / grid[1])

		for x in range(_start1, _end1, step_x):
			for h in range(_start2, _end2, step_h):
				m = copy(module)
				position = np.array([0, 0, 0])
				position[abs(1-axis)] = x
				position[2] = h
				m.position(position)
		module.remove()


if __name__ == '__main__':
	f = ModuleFactory()


