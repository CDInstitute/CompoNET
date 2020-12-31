import bpy
import numpy as np
import os


filename = 'test.gltf'


class Building:
	def __init__(self, mesh):
		# assert mesh.parent.name == 'test1'
		if mesh.parent:
			print(mesh.parent.name)
		self.building = mesh

	def save(self, filename='test.obj'):
		deselect_all()
		self.building.select_set(True)
		bpy.ops.export_scene.obj(filepath=filename, use_selection=True)


class Collection:
	# TESTED: collection_test.py
	def __init__(self, class_type):
		self.collection = []
		self.class_type = class_type

	def __iter__(self):
		return Iterator(self.collection, self.class_type)

	def __len__(self):
		return len(self.collection)

	def add(self, obj):
		if obj.__class__ == type:
			if issubclass(obj, self.class_type):
				self.collection.append(obj)
		else:
			if isinstance(obj, self.class_type):
				self.collection.append(obj)
			elif issubclass(obj.__class__, self.class_type):
				self.collection.append(obj)
			elif isinstance(obj, list):
				for _object in obj:
					assert isinstance(_object, self.class_type), "Expected a list of {}," \
													" got {}".format(self.class_type, type(_object))
					self.collection.append(_object)
			else:
				raise TypeError


class Iterator:
	def __init__(self, collection, class_type):
		self.collection = collection
		self.index = 0
		self.class_type = class_type
		assert isinstance(self.collection, list), "Wrong iteration input."

	def __next__(self):
		try:
			_object = self.collection[self.index]
		except IndexError:
			raise StopIteration()
		self.index += 1
		assert isinstance(_object, self.class_type)
		return _object

	def __iter__(self):
		return self

	def has_next(self):
		return self.index < len(self.collection)



class BlenderReader:
	def __init__(self, filename):
		self.filename = filename
		self._import()
		self.filename = self.filename.split('.')[-2]
		self.obj = bpy.data.objects
		self._clean()
		self.obj = bpy.data.objects

	def _clean(self):
		to_clean = [x for x in self.obj if
		            x.parent and x.parent.name != 'test1']
		deselect_all()
		for mesh in to_clean:
			try:
				mesh.select_set(True)
				bpy.ops.object.delete()
			except Exception:
				pass

	def _import(self):
		bpy.ops.import_scene.gltf(filepath=self.filename)

	def read(self):
		return self.obj

	def export(self, filename='test.obj'):
		deselect_all(True)
		bpy.ops.export_scene.obj(filepath=filename)
		print('length', len(self.obj))
		for i in self.obj:
			print(i.name)
		print('File has been successfully saved as {}'.format(filename))


def deselect_all(value=False):
	"""
	Function that deselects all the objects in the scene.
	:return: None
	"""
	for obj in bpy.data.objects:
		obj.select_set(value)


if __name__ == '__main__':
	reader = BlenderReader(filename)
	building_collection = Collection(Building)
	for b in reader.obj:
		building_collection.add(Building(b))
	for i, b in enumerate(building_collection):
		b.save('{}.obj'.format(i))


