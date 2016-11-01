# Kurt Davis
# 11/1/16
# ShooterGame.py

import sys
import pygame

from pygame.locals import *

from shootergameclasses import *

GLOBAL_SCREEN_WIDTH = 32 * GLOBAL_TILE_WIDTH
GLOBAL_SCREEN_HEIGHT = 20 * GLOBAL_TILE_HEIGHT
GLOBAL_WINDOW_TITLE = 'Shooter Game'

class GameSpace:
	def __init__(self):
		# Initialize game space and screen
		pygame.init()

		self.size = self.width, self.height = GLOBAL_SCREEN_WIDTH, GLOBAL_SCREEN_HEIGHT
		self.color_black = 0, 0, 0

		self.screen = pygame.display.set_mode(self.size)
		pygame.display.set_caption(GLOBAL_WINDOW_TITLE)

		# Initialize Sound and timer subsystems
		pygame.mixer.init()
		self.clock = pygame.time.Clock()
		
		# Instantiate level
		self.level = None

	def loadLevel(self, levelName):
		self.level = Level(levelName, self)
		self.level.load_file()

	def GameLoop(self):
		self.running = True
		while(self.running):
			
			# Handle Input
			for event in pygame.event.get():
				if event.type == QUIT:
					self.running = False
			keystate = pygame.key.get_pressed()

			# Update Objects

			# Render
			self.screen.fill(self.color_black)

			for line in self.level.data:
				for tile in line:
					self.screen.blit(tile.image, tile.rect)

			pygame.display.flip()	# Switch screen buffers

if __name__ == '__main__':
	gs = GameSpace()
	gs.loadLevel('leveltest.dat')
	gs.GameLoop()
