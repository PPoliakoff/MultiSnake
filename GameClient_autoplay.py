import pygame
import sys
from websockets.sync.client import connect

quit=False
NPLAYERS=4
colors=[(0,0,0),(255,0,0),(0,255,0),(0,0,255),(127,127,0),(127,127,127)]
GRIDSIZE=42
WINDOWSIZE=700
SQUARESIZE=WINDOWSIZE//GRIDSIZE
DRAWOFFSET=(WINDOWSIZE-GRIDSIZE*SQUARESIZE)//2
#create the window
pygame.init()
pygame.font.init()
font = pygame.font.SysFont("Courier", 25, bold=True, )
grid=None
message="Waiting for connection to server"
playerColor=5 # undefined color
screen = pygame.display.set_mode((WINDOWSIZE, WINDOWSIZE))


class Player:
    def __init__(self,px,py,dx,dy):
        self.px=px
        self.py=py 
        self.dx=dx
        self.dy=dy

    def getSquare(self,x,y):
        sx=self.px+ x*self.dx- y*self.dy
        sy=self.py+ x*self.dy+ y*self.dx

        if sx<0 or sy<0 or sx>=GRIDSIZE or sy >=GRIDSIZE or grid==None:
            retval= NPLAYERS+1
        else:
            retval=grid[sx+sy*GRIDSIZE]
        print(self.px,self.py,self.dx,self.dy,x,y, sx,sy,retval)
        return retval

    def turnRight(self):
        tmp=self.dy
        self.dy=self.dx
        self.dx=-tmp
        self.sendNewDir()

    def turnLeft(self):
        tmp=self.dy
        self.dy=-self.dx
        self.dx=tmp
        self.sendNewDir()

    def sendNewDir(self):
        msg=str(self.dx)+"|"+str(self.dy)
        print(">>>>",msg)
        websocket.send(msg)

    def robotPlay(self):
        if self.getSquare(1,0)=="0":
            pass #no colision: continue
        elif self.getSquare(0,-1)=="0":
            self.turnLeft()
        else:
            self.turnRight()

player=Player(0,0,0,0)

#connect to server
uri = "ws://"+sys.argv[1]+":8765" #"ws://192.168.0.22:8765"
with connect(uri) as websocket:
    while not quit:
        msg=""
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                quit = True
            if e.type == pygame.KEYDOWN: 
                if e.key == pygame.K_UP and player.dy==0:
                    msg='0|-1'
                elif e.key == pygame.K_DOWN and player.dy==0:
                    msg='0|1'
                elif e.key == pygame.K_LEFT and player.dx==0:
                    msg='-1|0'
                elif e.key == pygame.K_RIGHT  and player.dx==0:
                    msg='1|0'
        if len(msg)>0:
            websocket.send(msg)

        reply = websocket.recv()
        playerdata=reply.split("|")
        playerColor=ord(playerdata[0])-48
        player.px=int(playerdata[1])
        player.py=int(playerdata[2])
        player.dx=int(playerdata[3])
        player.dy=int(playerdata[4])
        message=playerdata[5]
        grid=playerdata[6]
        player.robotPlay()
        screen.fill(colors[playerColor])
        if grid !=None:
            for y in range(GRIDSIZE):
                for x in range(GRIDSIZE):
                    pygame.draw.rect(screen,colors[ord(grid[x+y*GRIDSIZE])-48],(DRAWOFFSET+x*SQUARESIZE,DRAWOFFSET+y*SQUARESIZE,SQUARESIZE,SQUARESIZE))
        text = font.render(message, True, colors[playerColor], (0, 0, 0, 0))
        test_rect=text.get_rect(center=(WINDOWSIZE//2,WINDOWSIZE//2))
        screen.blit(text, test_rect)
        pygame.display.flip()



