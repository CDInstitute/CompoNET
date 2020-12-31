import bpy
import json
import numpy as np


class Annotation:
	"""
	Class that writes an annotation based on Pix3D dataset structure from an
	active 3D scene.

	"""
	def __init__(self):
		self.content = {}
		self.full = []
		self._clean()

	def add(self, name, model, bb=None):
		"""
		Function that adds a model's annotation to the full dataset annotation.
		:param name: name of the image file, str
		:param model: name of the model .obj file, str
		:param bb: bounding box of the model, list or tuple or np.array
		[width_from, height_from, width_to, height_to]
		:return:
		"""
		assert isinstance(name, str)

		if bb:
			assert isinstance(bb, list) or isinstance(bb, tuple) or \
			       isinstance(bb, np.ndarray), "Expected bounding box as an " \
			                                   "array, got {}".format(type(bb))
			assert len(bb) == 4, "Expected bounding box to have 4 elements, " \
			                     "got {}".format(len(bb))

		self.content['img'] = name
		self.content['mask'] += name.split('/')[-1]
		self.content['model'] = model

		try:
			self.content['cam_position'] = list(bpy.data.objects['Camera'].location)
		except Exception:
			pass
		try:
			self.content['focal_length'] = bpy.data.cameras['Camera'].lens
		except Exception:
			pass

		self.content['img_size'] = (bpy.data.scenes[0].render.resolution_y,
		                            bpy.data.scenes[0].render.resolution_x)
		self.content['bbox'] = list(bb)
		self.full.append(self.content)
		self._clean()

	def write(self, filename='test.json'):
		"""
		Function that writes the full json annotation to the provided location.
		:param filename: name of the file to write, str, default='test.json'
		:return:
		"""
		assert isinstance(filename, str), 'Expected filename to be str, got {}'.format(type(filename))
		with open(filename, 'w') as f:
			json.dump(self.full, f)

		print('Annotation successfully written as {}'.format(filename))

	def _clean(self):
		"""
		Function that returns the annotation template to its default form.
		:return:
		"""
		self.content = {'img': '',
		                'category': 'building',
		                'img_size': (256, 256),
		                '2d_keypoints': [],
		                'mask': 'masks/',
		                'img_source': 'synthetic',
		                'model': '',
		                'model_raw': 0,
		                'model_source': 'synthetic',
		                'trans_mat': 0,
		                'focal_length': 35.0,
		                'cam_position': (0.0, 0.0, 0.0),
		                'inplane_rotation': 0,
		                'truncated': False,
		                'occluded': False,
		                'slightly_occluded': False,
		                'bbox': [0.0, 0.0, 0.0, 0.0]}

