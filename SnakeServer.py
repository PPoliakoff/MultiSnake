import random

import websockets
import asyncio
from enum import Enum, auto
'''
detect if the same player logs in twice

'''

FRAME_DELAY=0.1
GAMEOVER_TIMEOUT=5/FRAME_DELAY
START_SOON_TIMEOUT=5/FRAME_DELAY
GRIDSIZE = 44
MAXPLAYER = 8
DIRECTIONS="UDLR"
STARTOFFSET=(GRIDSIZE-3)//4
grid=[]
playersConnected=[None]*MAXPLAYER  # this is used to assign a unique fixed identifying number to the player. The client uses this number to assign a color to each player

class PLAYERSTATE(Enum):
    NOT_LOGGED_IN=auto() # name==none  : wait for player to communicate their name -> Message "please log in"
    #receive login message
    IN_LOBBY=auto() #   ready==False     : wait for the player to notify it is ready to play -> Message "score history"
    #we get a ready notification
    READY=auto() #  ready==True          : player has notified the server that they will participate to the next game -> message "Waiting for player"
    #we are accepted in a game
    IN_GAME=auto() # the Server has notified the player they are in the current game -> message "Game will start in xx s"
    #we have won or lost
    GAME_OVER=auto() # message : game score

class GAMESTATE(Enum):
    WAITING_PLAYERS=auto()  # no game is running: we wait for players to become ready
    #2 players (or more) are ready to play
    START_SOON=auto() # we wait to see if more players become ready
    #transition: timeout
    IN_GAME=auto()   # at least 2 players are playing
    # transition we have a winner
    GAME_OVER=auto() #diplay score
    #transition: timeout

class PLAYER:
    def __init__(self,index,websocket):
        self.name:str =None
        self.score:str =""
        self.index:int =index
        self.state=PLAYERSTATE.NOT_LOGGED_IN
        self.x:int =0
        self.y:int =0
        self.dx:int =0
        self.dy:int =0
        self.dir: str ="U"
        self.websocket:websockets.WebSocketServerProtocol =websocket

    def handleMessage(self,message):
        # messages:
        # Lplayer name  : Login (max name len: 8 )
        # R             :ready
        # TU TD TL TR   : turn Up, Down Left, Right
        action=message[0]
        if (self.state==PLAYERSTATE.READY or self.state==PLAYERSTATE.IN_GAME) and action=="T" and len(message)>1:
            self.turn(message[1])

        elif self.state==PLAYERSTATE.NOT_LOGGED_IN and action=="L" and len(message)>1:
            self.name=message[1:min(9,len(message))]
            print(f"Player{self.index+1} Loggen in as {self.name}")
            self.state=PLAYERSTATE.IN_LOBBY

        elif self.state==PLAYERSTATE.IN_LOBBY and action=="R":
            self.state=PLAYERSTATE.READY

    def turn(self,dir):
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

    #move player and return False if lost
    def play(self):
        tmpx=self.x+self.dx
        tmpy=self.y+self.dy
        if grid[tmpy][tmpx]==0:
            self.x=tmpx
            self.y=tmpy
            grid[tmpy][tmpx]=self.index+1 #we must add 1 because 0 is reserved for empty tiles
            return True
        else:
            return False #player lost
class GAME:
    def __init__(self):
        self.gotoWaitingForPlayers()
        self.numberOfPlayer:int =0


    def gotoWaitingForPlayers(self):
        for player in playersConnected:
            if player!=None:
                if player.state==PLAYERSTATE.GAME_OVER:
                    player.state=PLAYERSTATE.IN_LOBBY
                    player.score=""
        self.state=GAMESTATE.WAITING_PLAYERS
        print("Waiting for Players")
    def gotoStartSoon(self):
        global grid
        self.numberOfPlayer=0
        self.state=GAMESTATE.START_SOON
        self.timeout=START_SOON_TIMEOUT
        print("Game will start Soon")
        #fill the grid with empty space ( 0 )
        grid=[[0 for _ in range(GRIDSIZE)] for _ in range(GRIDSIZE)]
        #draw a border around the grid
        for g in range(GRIDSIZE):
            grid[g][0] = MAXPLAYER+1
            grid[g][GRIDSIZE-1] = MAXPLAYER+1
            grid[0][g] = MAXPLAYER+1
            grid[GRIDSIZE-1][g] = MAXPLAYER+1      
    def gotoInGame(self):
        self.state=GAMESTATE.IN_GAME
        print("In Game")
    def gotoGameOver(self):
        self.state=GAMESTATE.GAME_OVER
        self.timeout=GAMEOVER_TIMEOUT
        print("Game Over")

    def appendPlayer(self,player: PLAYER):
        #set origin and direction
        OK=False
        while not OK:
            x=random.randint(1,3)*STARTOFFSET+1
            y=random.randint(1,3)*STARTOFFSET+1
            OK= grid[y][x]==0 # the Start place is not already in use
        grid[y][x]=player.index+1 # reserve the start place
        player.x=x
        player.y=y
        player.turn(random.choice(DIRECTIONS))
        #change player state
        player.state=PLAYERSTATE.IN_GAME
        self.numberOfPlayer+=1

    def WaitingForPlayers(self):
        playerReady=0
        for player in playersConnected:
            if player!=None:
                if player.state==PLAYERSTATE.READY:
                    playerReady+=1
        if playerReady>=2:
            self.gotoStartSoon()
    def gameStartSoon(self):
        self.timeout-=1
        for player in playersConnected:
            if player!=None:
                if player.state==PLAYERSTATE.READY:
                    self.appendPlayer(player)
        if self.timeout<=0:
            self.gotoInGame()
    def inGame(self):
        playerInGame=0
        losingPlayers=[]
        # bonus=1
        for player in playersConnected:
            if player!=None:
                if player.state==PLAYERSTATE.IN_GAME:
                    if player.play():
                        playerInGame+=1
                    else:
                        player.state=PLAYERSTATE.GAME_OVER
                        player.score=f"{player.name} Terminated #{self.numberOfPlayer}"
                        self.numberOfPlayer-=1
                        losingPlayers.append(player.index+1)
                        #bonus=100
        if len(losingPlayers)>0:
            for x in range(GRIDSIZE):
                for y in range(GRIDSIZE):
                    if grid[y][x] in losingPlayers:
                        grid[y][x]=0

        # if playerInGame==1: #we have a winner 
        #     bonus=200

        for player in playersConnected:
            if player!=None:
                if player.state==PLAYERSTATE.IN_GAME:
                    #player.score+=bonus
                    if playerInGame<=1: 
                        player.state=PLAYERSTATE.GAME_OVER
                        player.score="Victory!!"

        if playerInGame<=1: #game is finished
            self.gotoGameOver()
    def GameOver(self):
        self.timeout-=1
        if self.timeout<=0:
            self.gotoWaitingForPlayers()

    async def NotifyPlayers(self):
        tasks=[]
        if self.state==GAMESTATE.IN_GAME or self.state==GAMESTATE.START_SOON or self.state==GAMESTATE.GAME_OVER:
             gridMessage="".join("".join(str(n) for n in row) for row in grid)
        for player in playersConnected:
            if player!=None: 
                try:
                    message=""
                    index=str(player.index)
                    if player.state==PLAYERSTATE.NOT_LOGGED_IN:
                        message="|".join(("N",index))
                    elif player.state==PLAYERSTATE.IN_LOBBY:
                        message="|".join(("L",index)) # send score history
                    elif player.state==PLAYERSTATE.READY:
                        message="|".join(("R",index))
                    elif player.state==PLAYERSTATE.IN_GAME:
                        playerInfo=";".join((str(player.x),str(player.y),player.dir))
                        message="|".join(("G",index,gridMessage,playerInfo)) # send game status (and timer if start soon)
                    else: # player GameOver
                        message="|".join(("O",index,gridMessage,player.score)) # send game results
                    tasks.append(asyncio.create_task( player.websocket.send(message)))
                    
                except websockets.ConnectionClosed as e:
                    print(f"Send message failed: closed connection for player {player.index+1}")
                    playersConnected[player.index]=None #release the slot in the players list
        try:            
            await asyncio.gather(*tasks)
        except websockets.ConnectionClosed as e:
            print(f"Send message failed: closed connection for one player ")

    async def gameLoop(self):
        while True:
            if self.state==GAMESTATE.WAITING_PLAYERS:
                self.WaitingForPlayers()
            elif self.state==GAMESTATE.START_SOON:
                self.gameStartSoon()
            elif self.state==GAMESTATE.IN_GAME:
                self.inGame()
            else: 
                self.GameOver()
            await self.NotifyPlayers()
            await asyncio.sleep(FRAME_DELAY)

#called each time a new client connects
async def newClient(websocket):
    try:
        index=playersConnected.index(None)
    except:
        # no more player slot available
        websockets.Close(1000,"Server is full")
        print("Server is full, player connection refused")
        return
    playersConnected[index]=player=PLAYER(index,websocket)
    print(f"Player {index+1} connected")
    try:
        async for msg in websocket:
            player.handleMessage(msg)
    finally:
        #client disconnected
        print(f"Player {index} disconnected")
        playersConnected[index]=None #release the slot in the players list

async def main():
    print("=======Start game Server======")
    game=GAME()
    async with websockets.serve(newClient, "", 8765) as server:
        await game.gameLoop()

if __name__ == "__main__":
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("Shutting down...") 