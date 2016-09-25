import sys
import pygame
from pygame.locals import *

#========================================================
# Player Class--------------
# 	Encapsulates player sprite image and location
#========================================================
class Player(pygame.sprite.Sprite):
	def __init__(self, gs=None):
		"""Player Constructor"""
		pygame.sprite.Sprite.__init__(self)

		self.gs = gs

		self.image = pygame.image.load("guy.png")
		self.rect = self.image.get_rect()
		self.rect.center = (100, 100)

	def move(self, x, y):
		"""Method to update player sprite position"""
		self.rect = self.rect.move(x, y)
#========================================================


#========================================================
# GameSpace Class-----------
#	Manages PyGame initialization, window creation, game loop
#	    and game logic
#========================================================
class GameSpace:
	def __init__(self):
		"""GameSpace Constructor"""
		pygame.init();

		self.size = self.width, self.height = 640, 480
		self.grey = 90, 90, 90

		self.screen = pygame.display.set_mode(self.size)
		pygame.display.set_caption('My Cool Game')

		pygame.mixer.init()
		self.clock = pygame.time.Clock()

		self.player = Player(self)
		
	def run(self):
		"""Method to start main game loop, start gameplay"""
		# Game loop
		while 1:
			# Tick-rate regulation
			self.clock.tick(60)
	
			# Handle input
			for event in pygame.event.get():
				if event.type == QUIT:
					sys.exit()		
			keystate = pygame.key.get_pressed()
			
			# "Tick" objects
			if keystate[pygame.K_w]:
				self.player.move(0, -3)
			elif keystate[pygame.K_s]:
				self.player.move(0, 3)
			elif keystate[pygame.K_a]:
				self.player.move(-3, 0)		
			elif keystate[pygame.K_d]:
				self.player.move(3, 0)		

			# Render
			self.screen.fill(self.grey)
			self.screen.blit(self.player.image, self.player.rect)
			pygame.display.flip()
#========================================================

# Main Function
if __name__ == '__main__':
	# Initialize Game Loop
	gs = GameSpace()
	gs.run()	
