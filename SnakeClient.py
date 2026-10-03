import pygame
import websockets
from websockets.sync.client import connect
import sys

'''
 V display window
 V receive messages
 V Connect
 display game
 display message, state
 send direction
 Disconnect
 display score
 V bot API (turnLeft, turnRight,getSquare )
 
'''
#constants
GRIDSIZE=44
WINDOWSIZE=700
SQUARESIZE=WINDOWSIZE//GRIDSIZE
DRAWOFFSET=(WINDOWSIZE-GRIDSIZE*SQUARESIZE)//2
WALL=100
COLORS=[(0,0,0),(220,20,60),(0,200,70),(30,90,255),(255,200,0),(220,0,180),(0,200,200),(255,120,0),(140,60,255),(255,255,255)]
DIRECTIONS="URDL"
class Client:
    def __init__(self,autoStart):
        self.autoStart=autoStart

    def setInfo(self,info):
        data=info.split(';')
        self.px=int(data[0])
        self.py=int(data[1])
        self.saveDir(data[2])

    def saveDir(self,dir):
        self.dir=dir
        if dir =="U":
            self.dx=0
            self.dy=-1
        elif dir =="D":
            self.dx=0
            self.dy=1
        elif dir =="L":
            self.dx=-1
            self.dy=0
        else: #right  
            self.dx=1
            self.dy=0

    def setDir(self,dir):
        self.saveDir(dir)
        msg=str("T"+self.dir)
        self.websocket.send(msg)

    def getSquare(self,x,y):
        sx=self.px+ x*self.dx- y*self.dy
        sy=self.py+ x*self.dy+ y*self.dx
        if sx<0 or sy<0 or sx>=GRIDSIZE or sy >=GRIDSIZE or self.grid==None:
            retval= WALL
        else:
            retval=self.grid[sx+sy*GRIDSIZE]
        return retval

    def turnRight(self):
        dirindex=DIRECTIONS.index(self.dir)
        self.setDir(DIRECTIONS[(dirindex+1)%4])

    def turnLeft(self):
        dirindex=DIRECTIONS.index(self.dir)
        self.setDir(DIRECTIONS[(dirindex-1)%4])


    def run(self):
        # Main function
        if len(sys.argv) !=3:
            print("Usage: SnakeClient <server IP Address>  <PlayerName>")
            print("")
            print("Example:")
            print("      python SnakeClient 192.168.0.42 player1")
            print("")
            sys.exit(1)
        uri=f"ws://{sys.argv[1]}:8765"
        pygame.init()
        pygame.font.init()
        font=pygame.font.SysFont("Courier",25)
        screen=pygame.display.set_mode((WINDOWSIZE,WINDOWSIZE)) 
        try:
            with connect(uri) as websocket:
                self.websocket=websocket
                websocket.send(f"L{sys.argv[2]}")
                quit=False
                key=pygame.K_UNKNOWN

                while not quit:
                    for e in pygame.event.get():
                        if e.type == pygame.QUIT:
                            quit = True
                        elif e.type==pygame.KEYDOWN:
                            key=e.key
                    data="W"
                    try:                        
                        data=websocket.recv(timeout=0.1).split('|')
                    except TimeoutError as e:
                        pass
                    state=data[0]
                    localMessage=None
                    self.grid=None
                    if state=='N': # Not logged in
                        raise RuntimeError("Server refused login")
                    elif state=='L': # Lobby
                        localMessage="You are in the lobby Press X to Play"
                        if key==pygame.K_x or self.autoStart:
                            websocket.send("R") #notify we are Ready
                    elif state=='R': # Ready
                        localMessage="Waiting for Players"
                    elif state=='O': # Game Over
                        self.grid=data[2]
                        localMessage=data[3]
                    elif state=="G": #we are in game
                        self.grid=data[2]
                        self.setInfo(data[3])
                        self.play(key)
                        key=pygame.K_UNKNOWN
                    else:
                        state="W"
                    # update the display
                    if state!="W":
                        screen.fill(COLORS[int(data[1])+1])
                        if state=="G" or state=="O":
                            for y in range(GRIDSIZE):
                                for x in range(GRIDSIZE):
                                    pygame.draw.rect(screen,COLORS[ord(self.grid[x+y*GRIDSIZE])-48],
                                                    (DRAWOFFSET+x*SQUARESIZE,DRAWOFFSET+y*SQUARESIZE,SQUARESIZE,SQUARESIZE))
                        if localMessage!=None:
                            text = font.render(localMessage, True,(255,255,255))
                            test_rect=text.get_rect(center=(WINDOWSIZE//2,80))
                            screen.blit(text, test_rect)
                        pygame.display.flip()

        except OSError:
            print(f"Unable to connect to {sys.argv[1]}")
        except websockets.ConnectionClosed as e:
            print(f"Server closed connection: {e}")
        except websockets.WebSocketException as e:
            print(f"Websocket exception: {e}") 
        except RuntimeError as e:
            print(f"Error: {e}")
