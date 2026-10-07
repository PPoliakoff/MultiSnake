from SnakeClient import Client

class Player(Client):
    def play(self,key):
        if self.getSquare(0,1)=="0":
            self.turnRight()
        elif self.getSquare(1,0)=="0":
            pass #no collision: continue
        else:
            self.turnLeft()

player=Player(autoStart=True)
player.run()
