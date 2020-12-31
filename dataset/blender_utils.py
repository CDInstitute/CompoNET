import bpy, bmesh


def get_min_max(volume, axis):
	"""
	Function that returns limits of a mesh on the indicated axis
	:param volume: volume to get the dims of, mesh
	:param axis: int, 0 - width; 1 - length; 2 - height
	:return: min, max, float
	"""

	return min([x[axis:axis+1][0] for x in volume.bound_box]),\
	       max([x[axis:axis+1][0] for x in volume.bound_box])
