import pygame
from SnakeClient import Client

class Player(Client):
    def play(self,key):
        if key==pygame.K_UP and self.dir!="D":
            self.setDir("U")
        elif key==pygame.K_DOWN and self.dir!="U":
            self.setDir("D")
        elif key==pygame.K_LEFT and self.dir!="R":
            self.setDir("L")
        elif key==pygame.K_RIGHT and self.dir!="L":
            self.setDir("R")

player=Player(autoStart=False)
player.run()
