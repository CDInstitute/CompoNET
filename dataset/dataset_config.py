MIN_HEIGHT = 3.0
MIN_WIDTH = 6.0
MIN_LENGTH = 6.0

MAX_HEIGHT = 30.0
MAX_WIDTH = 30.0
MAX_LENGTH = 30.0

MAX_VOLUMES = 4

# BUILDINGS = ['Patio', 'L', 'C', 'Single', 'Skyscraper', 'Closedpatio', 'Equalpatio']
# Choose building typologies to be produced
BUILDINGS = ['Patio', 'L', 'C', 'Single', 'Skyscraper', 'Closedpatio', 'Equalpatio']

SIZE = 2  # dataset size

use_materials = True  # apply materials to the facades of the buildings, bool

MATERIAL_PROB = 0.7  # Probability of all the volumes of one building to be of the same material

use_modules = True
MODULES = ['window']

MODEL_SAVE = 'Models'
IMG_SAVE = 'Images'
MASK_SAVE = 'Masks'

ENGINE = 'CYCLES'