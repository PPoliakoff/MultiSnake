import asyncio
from websockets.asyncio.server import serve,broadcast

GRIDSIZE=42
MAXPLAYER=4

#game states
WAIT_FOR_PLAYERS=0
WAIT_FOR_GAME_START=1
IN_GAME=2
GAME_OVER=3
gamestatemessages=["Waiting for players to connect","Game will start soon","","Game Over"]
STARTPOS=[[GRIDSIZE//4,GRIDSIZE//3],[2*GRIDSIZE//4,GRIDSIZE//3],[3*GRIDSIZE//4,GRIDSIZE//3],[GRIDSIZE//4,2*GRIDSIZE//3]]
grid=[]
players = [None] *MAXPLAYER
class Player:
    def __init__(self,index,websocket):
        self.color=chr(49+index)
        self.index=index
        self.dead=True
        self.websocket=websocket

    def reset(self):
        self.px=STARTPOS[self.index][0]
        self.py=STARTPOS[self.index][1]
        self.dx=0
        self.dy=1
        grid[self.py][self.px]=self.color
        self.dead=False

    def turn(self,dir):
        if dir=='l':
            self.dx=-1
            self.dy=0
        elif dir=="r":
            self.dx=1
            self.dy=0
        elif dir=="d":
            self.dx=0
            self.dy=1
        elif dir=="u":
            self.dx=0
            self.dy=-1

    def move(self):
        if self.dead==False:
            self.px+=self.dx
            self.py+=self.dy
            if grid[self.py][self.px]=='0':
                grid[self.py][self.px]=self.color
            else:
                self.die()

    def die(self):
        self.dead=True
        for y in range(GRIDSIZE):
            for x in range(GRIDSIZE):
                if grid[y][x]==self.color:
                    grid[y][x]='0'

async def hello(websocket):
    print ("========client connected 🙋‍♀️====== ")
    connected=True
    index=0
    while index<MAXPLAYER and players[index]!=None:
        index+=1
    if index==MAXPLAYER:
        print("lobby full: cannot connect")
        connected=False
    else:
        players[index]=Player(index,websocket)
    while connected:
        try:
            msg = await websocket.recv()
            print(f"{index}<<< {msg}")
            players[index].turn(msg)
        except:
            connected=False
    players[index].die     
    players[index]=None
    print(f"========{index} disconnected 🚫====== ")

async def BroadcastStatus(server):
    gameState=WAIT_FOR_PLAYERS
    while True:
        playersCount=0
        playeralive=0
        for p in players:
            if p!=None:
                playersCount+=1
                if gameState==IN_GAME:
                    if p.dead==False:
                        p.move()
                        playeralive+=1
                        message =""
                    else:
                        message="You lost"
                elif gameState==GAME_OVER:
                    if p.dead==False:
                        message="YOU WON"
                    else: 
                        message="You lost"
                else:
                    message=gamestatemessages[gameState]
                await p.websocket.send(p.color+message)
        if playersCount<2:
            gameState=WAIT_FOR_PLAYERS
        elif gameState==WAIT_FOR_PLAYERS:
            timer=10
            gameState=WAIT_FOR_GAME_START
            game_reset()
            for p in players:
                if p!=None:
                    p.reset()
        elif (gameState==WAIT_FOR_GAME_START or gameState==GAME_OVER) and timer>0:
            timer-=1
        elif gameState==WAIT_FOR_GAME_START:
            gameState=IN_GAME
        elif gameState==IN_GAME and playeralive<=1:
            gameState=GAME_OVER
            timer=10
        elif gameState==GAME_OVER:

            gameState=WAIT_FOR_PLAYERS

        print(gamestatemessages[gameState])
        message="".join(str(item) for row in grid for item in row)

        broadcast(server.connections,message)
        await asyncio.sleep(0.5)


def game_reset():
    grid.clear()
    for y in range(GRIDSIZE):
        grid.append([])
        for x in range(GRIDSIZE):
            grid[y].append('0')
    for g in range(GRIDSIZE):
        grid[g][0]='5'
        grid[g][GRIDSIZE-1]='5'
        grid[0][g]='5'
        grid[GRIDSIZE-1][g]='5'

async def main():
    print ("=======Server started ✅======")
    game_reset()

    async with serve(hello, "localhost", 8765) as server:
        await BroadcastStatus(server)

if __name__ == "__main__":
    asyncio.run(main())