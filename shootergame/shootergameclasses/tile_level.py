# Kurt Davis
# 11/1/16
# tile_level.py

import sys
import pygame
from pygame.locals import *

GLOBAL_TILE_WIDTH = 32
GLOBAL_TILE_HEIGHT = 32

images_directory = 'images/'
levels_directory = 'levels/'

# Set of all tile types
TileSet = {
		0: ('default', False, 'default.png')
	}

class Tile(pygame.sprite.Sprite):
	def __init__(self, tiletype, posX, posY):
		self.tiletype = int(tiletype)

		self.typeName = TileSet[self.tiletype][0]
		self.isCollidable = TileSet[self.tiletype][1]
		self.texFile = TileSet[self.tiletype][2]

		self.image = pygame.image.load(images_directory + self.texFile)
		self.rect = self.image.get_rect()
		self.posX = posX
		self.posY = posY
		self.rect.center = ((GLOBAL_TILE_WIDTH/2 + (GLOBAL_TILE_WIDTH * self.posX)), (GLOBAL_TILE_HEIGHT/2 + (GLOBAL_TILE_HEIGHT * self.posY)))

	def __str__(self):
		return str(self.tiletype)

	def __repr__(self):
		return str(self.tiletype)

class Level(object):
	def __init__(self, target_file, gs=None):
		self.gs = gs
		self.target_file = target_file

		self.data = []
		self.colliders = []
		self.load_file()

	def load_file(self):
		x = 0
		y = 0
		level_path = levels_directory + self.target_file
		self.data = []
		infile = open(level_path, 'r')
		for line in infile:
			dataline = []
			x = 0
			for tiledata in (line.strip()).split(' '):
				dataline.append(Tile(tiledata, x, y))
				x = x + 1
			self.data.append(dataline[:])
			y = y + 1
		infile.close()

		self.colliders = []
		for line in self.data:
			for tile in line:
				if tile.isCollidable:
					self.colliders.append(tile)

	def print_data(self):
		for line in self.data:
			print " ".join(str(x) for x in line)


