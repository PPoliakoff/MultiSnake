from SnakeClient import Client

class Player(Client):
    def play(self,key):
        if self.getSquare(1,0)=="0":
            pass #no collision: continue straight
        elif self.getSquare(0,1)=="0":
            self.turnRight() 
        else: 
            # Wall ahead and to the right. Go to the left
            self.turnLeft()

player=Player(autoStart=True)
player.run()
