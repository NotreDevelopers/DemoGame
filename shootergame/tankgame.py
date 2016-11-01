# Kurt Davis and Bill Gowans
# 5/4/16
# PyGame and Twisted Milestone
# tankgame_server.py

# Main file for TankGame
# Includes networking structures, game state, and main game loop

#---------------------------------------------------------------
from twisted.internet.protocol import ClientFactory
from twisted.internet.protocol import Factory
from twisted.internet.protocol import Protocol
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from twisted.internet.task import LoopingCall

import sys
import os
import pygame
import pickle
import zlib

from pygame.locals import *

from math import *
from copy import deepcopy

from tankgameclasses import *
#----------------------------------------------------------------

CLIENT_1_PORT = 40054		# Assigned port for Kurt Davis

class ClientConnection(LineReceiver):
	"""Connection object for host to connect to client computer."""
	def __init__(self, addr, parent):
		"""Basic Constuctor, requires parent game state as argument."""
		self.addr = addr
		# Connection and gamestate are aware of each other
		self.parent = parent
		self.parent.con1 = self

		self.delimiter = 'potato'	

	def lineReceived(self, line):
		"""Process incoming line (decompress, depickle, and interpret)"""
		pick = self.pick_decompress(line)
		pick_dict = self.dict_unpickle(pick)
		self.parent.assign_from_dict(pick_dict)

	def connectionMade(self):
		print 'Client connected from ', str(self.transport.getPeer())
		self.parent.client_connected = True
	def connectionLost(self, reason):	
		print 'Client disconnected from ', str(self.transport.getPeer())

	#-----------------------------------------
	# Utility functions for sending and unpacking lines
	def dict_pickle(self, dict_line):
		pick_line = pickle.dumps(dict_line)
		return pick_line
	def dict_unpickle(self, pick_line):
		dict_line = pickle.loads(pick_line)
		return dict_line
	def pick_compress(self, pick_line):
		compressed_message = zlib.compress(pick_line)
		return compressed_message
	def pick_decompress(self,pick_line):
		decompressed_message = zlib.decompress(pick_line)
		return decompressed_message
	def exit_connection(self):
		self.transport.loseConnection()
	#-----------------------------------------
	
	def send_dict(self):
		"""For periodic update; Pickle, compress, and send game state data"""
		pick_send = self.dict_pickle(self.parent.get_dict())
		pick_compressed = self.pick_compress(pick_send)
		self.sendLine(pick_compressed)

class ClientConnectionFactory(Factory):
	"""Factory for Host->Client connections."""
	protocol = ClientConnection

	def __init__(self, parent):
		self.parent = parent

	def buildProtocol(self, addr):
		return ClientConnection(addr, self.parent)

class ServerConnection(LineReceiver):
	"""Connection object for client to connect to host computer."""
	def __init__(self, addr, parent):
		self.addr = addr
		# Connection and gamestate are aware of each other
		self.parent = parent
		self.parent.con1 = self

		self.delimiter = 'potato'

	def lineReceived(self, line):
		"""Process incoming line (decompress, depickle, and interpret), then immediately create gamestate dict to respond to host."""
		# Process inbound
		pick = self.pick_decompress(line)
		pick_dict = self.dict_unpickle(pick)
		self.parent.assign_from_dict(pick_dict)
		
		# Create and send response
		pick_send = self.dict_pickle(self.parent.get_dict())
		pick_compressed = self.pick_compress(pick_send)
		self.transport.write(pick_compressed + self.delimiter)

	def connectionMade(self):
		print 'Connected to server: ', str(self.transport.getPeer())
		self.parent.server_connected = True
	def connectionLost(self, reason):	
		print 'Disconnected from server: ', str(self.transport.getPeer())
		#reactor.stop()
	
	#-----------------------------------------
	# Utility functions for sending and unpacking lines
	def dict_pickle(self, dict_line):
		pick_line = pickle.dumps(dict_line)
		return pick_line
	def dict_unpickle(self, pick_line):
		dict_line = pickle.loads(pick_line)
		return dict_line
	def pick_compress(self, pick_line):
		compressed_message = zlib.compress(pick_line)
		return compressed_message
	def pick_decompress(self,pick_line):
		decompressed_message = zlib.decompress(pick_line)
		return decompressed_message
	def exit_connection(self):
		self.transport.loseConnection()
	#-----------------------------------------

class ServerConnectionFactory(ClientFactory):
	"""Factory for Client->Host connections."""
	protocol = ServerConnection

	def __init__(self, parent):
		self.parent = parent

	def buildProtocol(self, addr):
		return ServerConnection(addr, self.parent)

class GameSpace:
	def __init__(self):
		# Initialize Game Space=============================
		pygame.init()

		self.size = self.width, self.height = 1280, 800
		self.black = 0, 0, 0

		self.screen = pygame.display.set_mode(self.size)
		pygame.display.set_caption('Tank Game!')

		# Initialize Sound=================================
		pygame.mixer.init()
		self.clock = pygame.time.Clock()

		# Initialize Game Objects==========================
		self.level_file_dir = 'levels/'

		# Player 1----------------------------------
		self.player1 = Player(1, self)
		self.player1.setPosition(100, 100)		

		self.player1group = [self.player1]	# Sprite group for collision detection, only member is player1
		self.exp1 = -1				# Player 1's explosion

		# Player 2----------------------------------
		self.player2 = Player(2, self)
		self.player2.setPosition(self.width-100, self.height-100)

		self.player2group = [self.player2]	# Sprite group for collision detection, only member is player1
		self.exp2 = -1				# Player 2's explosion

		# Projectile list containers----------------
		# One for each player
		self.bullet_list1 = []
		self.bullet_list2 = []

		# Misc.-------------------------------------		

		# Player number; 1 = Host/Red, 2 = Client/Blue
		self.number = 2

		# Initialize level --> ***LEVEL IS RELOADED ON FIRST ITERATION OF MAIN LOOP***
		self.level_name = 'leveltest.dat'	# This is NOT the level that is played on
		self.level = Level(self.level_file_dir + self.level_name, self)

		# Declaration of connection object, *as seen in connection constructors*
		self.con1 = 'error'

		
		self.host_address = -1
		
		# Logic Flags-------------------------------
		self.level_loaded = False
		self.level_received = False

		self.server_connected = False
		self.client_connected = False

		self.redwins = False
		self.bluewins = False

	def assign_from_dict(self, d):
		"""For processing network input. Unpickled gamestate dictionary is used to update opposing player's gamestate variables. Effectively opponent.tick()"""
		
		# Host/Red player -> Update Client/Blue Player
		if self.number is 1:
			# Update tank position
			self.player2.setPosition(d["tank"][0],d["tank"][1],d["tank"][2],d["tank"][3])

			# Emit sound if bullets have been added
			if len(d["bullets"]) > len(self.bullet_list2):
				self.player2.emit_fire_noise()

			# Reset bullet container
			self.bullet_list2 = []

			# Update health and alive flag
			self.player2.update_opponent_health(d["health"])
			self.player2.alive = d["alive"]

			# Use list of tuples to recreate list of bullets
			for bullet in d["bullets"]:
				self.bullet_list2.append(Bullet(bullet[0],bullet[1],bullet[2],2,self))
		else:
			# Update tank position
			self.player1.setPosition(d["tank"][0],d["tank"][1],d["tank"][2],d["tank"][3])

			# Emit sound if bullets have been added
			if len(d["bullets"]) > len(self.bullet_list1):
				self.player1.emit_fire_noise()

			# Reset bullet container
			self.bullet_list1 = []
			
			# Update health and alive flag
			self.player1.update_opponent_health(d["health"])
			self.player1.alive = d["alive"]
			
			# Use list of tuples to recreate list of bullets
			for bullet in d["bullets"]:
				self.bullet_list1.append(Bullet(bullet[0],bullet[1],bullet[2],1,self))
			
			# *** CLIENT ONLY ***
			# Set level to load ONLY ONCE
			if not self.level_loaded:
				self.level_name = d["level"]
				self.level_received = True

	def get_dict(self):
		"""Opposite of assign_from_dict. Creates dictionary to pickle that contains relevant game state information for the other player to update."""
		# Dictionary sent back and forth is as follows:
		# d 	{
		#		'tank': <tuple representing position and direction of tank sprites>
		#		'bullets': <list of tuples with the position and direction of each bullet>
		#				Each player 'owns' only their bullet list, although both lists are ticked for interpolation purposes
		#		'level': Valid value only sent by host; indicates what level the client should load
		#		'player': indication of what player (1(host) or 2(client)) is sending the current dict
		#		'health': Health of player's respective tank; only the player owning the tank can change health
		#		'alive': Flag indicating if player is alive or not; for victory conditions
		#	}


		# Player 1----------------------------------------
		if self.number is 1:
			d = {}

			# 'tank': (x, y, body_angle, turret_angle)
			d["tank"] = (self.player1.rect.center[0],self.player1.rect.center[1],self.player1.direction_angle,self.player1.turret_direction_angle)
			
			# Create list of bullet tuples
			d["bullets"] = []
			for bullet in self.bullet_list1:
				# bullet = (x, y, angle)
				d["bullets"].append((bullet.x,bullet.y,bullet.angle))

			d["level"] = self.level_name
			d["player"] = 1
			d["health"] = self.player1.health
			d["alive"] = self.player1.alive
			return d
	
		# Player 2----------------------------------------	
		else:
			d = {}

			# 'tank': (x, y, body_angle, turret_angle)
			d["tank"] = (self.player2.rect.center[0],self.player2.rect.center[1],self.player2.direction_angle,self.player2.turret_direction_angle)

			# Create list of bullet tuples
			d["bullets"] = []
			for bullet in self.bullet_list2:
				# bullet = (x, y, angle)
				d["bullets"].append((bullet.x,bullet.y,bullet.angle))
	
			d["level"] = "client"
			d["player"] = 2
			d["health"] = self.player2.health
			d["alive"] = self.player2.alive
			return d


	def start_exchange(self):
		"""Function used in host to initiate host/client synchronization/update. Called on each iteration of Host update looping call lc2."""

		#############################################
		#+*+*+*+*+*+*+*+*IMPORTANT*+*+*+*+*+*+*+*+*+#
		#############################################
		# Host/Client synchronization works as follows:
		#
		# Every 1/20th of a second, the host uses this method to dispatch a line
		# to the host containing a compressed, pickled version of the dictionary
		# assembled in the preceeding method.
		#
		# Upon receiving the dictionary, the client immediately uncompresses and 
		# unpickles it, then uses its values via assign_from_dict to update the 
		# state of its copies of objects owned by the host, which it does not 
		# tick (e.g. the red tank).
		#
		# The client then creates its own dictionary using the above function,
		# pickles and compresses it, then sends it to the host, which uses it to
		# perform the same updates of client-owned objects.
		#
		# This process is repeated every time lc2 is activated, with the host initiating
		# the exchange with this function.

		if self.client_connected:
			self.con1.send_dict()

	def main(self):
			# Load level if needed================================
			if not self.level_loaded:
				# Host is initialized with default level; this loads the level specified on the command line.
				if self.number is 1:
					self.level = Level(self.level_file_dir + self.level_name, self)
					self.level_loaded = True
				
				# Client loads level as soon as it receives a line from the host
				else:
					if self.level_received:
						self.level = Level(self.level_file_dir + self.level_name, self)
						self.level_loaded = True
						
			# Handle Input========================================
			for event in pygame.event.get():
				if event.type == QUIT:
					if not self.con1 == "error":
						self.con1.exit_connection()
					reactor.stop()			
			
			keystate = pygame.key.get_pressed()
				


			# Tick Objects=======================================
			if self.number is 1:
				# Host ticks player 1
				self.player1.tick(keystate)
			else:
				# Client ticks player 2
				self.player2.tick(keystate)

			# Update projectile lists============================
			#	(also hit detection)
		
			# Player 1's (Host) bullets
			temp_list1 = []
			for bullet in self.bullet_list1:
				if bullet.rect.center[0] > 0 and bullet.rect.center[0] < self.width:	
					if bullet.rect.center[1] > 0 and bullet.rect.center[1] < self.height:
						if not pygame.sprite.spritecollide(bullet, self.level.colliders, False):
							if not pygame.sprite.spritecollide(bullet, self.player2group, False):
								temp_list1.append(bullet)
								bullet.tick()
							elif not self.player2.alive:	
								temp_list1.append(bullet)
								bullet.tick()
							else:
								if self.player2.health > 0 and self.number is 2 and self.server_connected:
									#print 'P2 hit.'
									self.player2.got_hit()
		
			self.bullet_list1 = temp_list1
						
			
			# Player 2's (Client) bullets
			temp_list2 = []
			for bullet in self.bullet_list2:
				if bullet.rect.center[0] > 0 and bullet.rect.center[0] < self.width:	
					if bullet.rect.center[1] > 0 and bullet.rect.center[1] < self.height:
						if not pygame.sprite.spritecollide(bullet, self.level.colliders, False):
							if not pygame.sprite.spritecollide(bullet, self.player1group, False):
								temp_list2.append(bullet)
								bullet.tick()
							elif not self.player1.alive:	
								temp_list2.append(bullet)
								bullet.tick()
							else:
								if self.player1.health > 0 and self.number is 1 and self.client_connected:
									#print 'P1 hit.'
									self.player1.got_hit()
		
			self.bullet_list2 = temp_list2

			# Create or tick explosions as appropriate==============================
			if not self.player1.alive:
				if self.exp1 is -1:
					self.exp1 = Explosion(self.player1.rect.center[0],self.player1.rect.center[1],5,self)
					self.exp1.start()
				else:
					self.exp1.tick()

			if not self.player2.alive:
				if self.exp2 is -1:
					self.exp2 = Explosion(self.player2.rect.center[0],self.player2.rect.center[1],5,self)
					self.exp2.start()
				else:
					self.exp2.tick()

			# Render================================================================
			self.screen.fill(self.black)	# Background

			for line in self.level.data:	# Tile Map
				for tile in line:
					self.screen.blit(tile.image, tile.rect)

			# Player 1
			if self.player1.alive:
				self.screen.blit(self.player1.image, self.player1.rect)
				self.screen.blit(self.player1.turret_image, self.player1.turret_rect)
			else:
				if self.exp1.running:
					self.screen.blit(self.exp1.image,self.exp1.rect)

			# Player 2
			if self.player2.alive:
				self.screen.blit(self.player2.image, self.player2.rect)
				self.screen.blit(self.player2.turret_image, self.player2.turret_rect)
			else:
				if self.exp2.running:
					self.screen.blit(self.exp2.image,self.exp2.rect)

			# Player 1 bullets
			for bullet in self.bullet_list1:
				self.screen.blit(bullet.image, bullet.rect)		

			# Player 2 bullets
			for bullet in self.bullet_list2:
				self.screen.blit(bullet.image, bullet.rect)		

			# Health bars
			self.screen.blit(self.player1.current_health_img, self.player1.health_rect)
			self.screen.blit(self.player2.current_health_img, self.player2.health_rect)

			# Game over text
			if self.redwins:
				self.screen.blit(self.player1.victory_img, self.player1.victory_rect)
			elif self.bluewins:
				self.screen.blit(self.player2.victory_img, self.player2.victory_rect)

			pygame.display.flip()


# Main program flow
if __name__ == '__main__':

	if len(sys.argv) < 3:
		print "Incorrect usage: python tankgame.py host|client <level name|host address>"
		exit(1)
	
	gs = GameSpace()

	if sys.argv[1] == "host":
		gs.number = 1
		gs.level_name = sys.argv[2]
	elif sys.argv[1] == "client":
		gs.number = 2
		gs.host_address = sys.argv[2]
	else:
		print "Incorrect usage: python tankgame.py host|client <level name|host address>"
		exit(1)

	# Framerate / Main game loop
	lc = LoopingCall(gs.main)
	lc.start(1.0/60.0)

	if gs.number is 1:
		# Host
		print 'Hosting...'
		# Synch loop
		lc2 = LoopingCall(gs.start_exchange)
		lc2.start(1.0/20.0)
		reactor.listenTCP(CLIENT_1_PORT, ClientConnectionFactory(gs))
	else:
		# Client
		print 'Connecting...'
		reactor.connectTCP(gs.host_address, CLIENT_1_PORT, ServerConnectionFactory(gs))
	reactor.run()
