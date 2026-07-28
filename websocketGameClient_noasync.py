import pygame
from websockets.sync.client import connect

quit=False
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

#connect to server
uri = "ws://localhost:8765"
with connect(uri) as websocket:
    while not quit:
        msg=""
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                quit = True
            if e.type == pygame.KEYDOWN: 
                if e.key == pygame.K_UP:
                    msg='u'
                elif e.key == pygame.K_DOWN:
                    msg='d'
                elif e.key == pygame.K_LEFT:
                    msg='l'
                elif e.key == pygame.K_RIGHT:
                    msg='r'
        if len(msg)>0:
            websocket.send(msg)
        reply = websocket.recv()
        if len(reply)>300: # we assume the message is never 300 chars long
            grid=reply
        else:
            message=reply[1:]
            playerColor=ord(reply[0])-48
        screen.fill(colors[playerColor])
        if grid !=None:
            for y in range(GRIDSIZE):
                for x in range(GRIDSIZE):
                    pygame.draw.rect(screen,colors[ord(grid[x+y*GRIDSIZE])-48],(DRAWOFFSET+x*SQUARESIZE,DRAWOFFSET+y*SQUARESIZE,SQUARESIZE,SQUARESIZE))
        text = font.render(message, True, colors[playerColor], (0, 0, 0, 0))
        test_rect=text.get_rect(center=(WINDOWSIZE//2,WINDOWSIZE//2))
        screen.blit(text, test_rect)
        pygame.display.flip()



