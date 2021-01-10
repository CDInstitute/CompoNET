import bpy, bmesh
from math import radians
import numpy as np
import os
import random
import sys

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)

from dataset_config import ENGINE


class Renderer:
	"""
	Class that manages the scene rendering. Incomplete.
	"""
	def __init__(self):
		self.engine = ENGINE
		self._scene_name = bpy.data.scenes[-1].name

	def render(self):
		self._render()

	def _render(self, filename='test'):
		"""
		Function that renders the scene.
		:return:
		"""
		bpy.data.scenes[-1].render.engine = self.engine
		bpy.ops.render.render()
		if not IMG_SAVE in os.listdir(file_dir):
			os.mkdir(file_dir + '/' + IMG_SAVE)
		bpy.data.images["Render Result"].save_render(
			'{}/{}.png'.format(IMG_SAVE, filename))

	def _render_mask(self):
		"""
		Function that renders the scene as a one-channel mask.
		:return:
		"""
		# update materials
		bpy.data.scenes["Scene"].render.engine = 'BLENDER_RENDER'
		bpy.ops.render.render()
		if not MASK_SAVE in os.listdir(file_dir):
			os.mkdir(file_dir + '/' + MASK_SAVE)
		bpy.data.images["Render Result"].save_render(
			'{}/{}.png'.format(MASK_SAVE, filename))
		raise NotImplementedError

	def _render_keypoints(self):
		"""
		Function that renders the scene as a one-channel mask of predefined
		keypoints.
		:return:
		"""
		raise NotImplementedError


if __name__ == '__main__':

	from generator import *
	from material import MaterialFactory
	from volume import CollectionFactory

	f = CollectionFactory()
	collection = f.produce(number=1)
	building = ComposedBuilding(collection.collection)
	building.make()
	for v in building.volumes:
		v.apply(MaterialFactory().produce())
	r = Renderer()
	r.render()


