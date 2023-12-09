import asyncio # 비동기 프로그래밍 지원 (여러 클라이언트의 연결)
import websockets # 웹소켓 프로토콜 지원  
import copy # 깊은 복사를 위함         

# 군집주행 차들의 위치
global location

# 위치가 벗어나 있으면 (서로 겹치는 꼭지점이 없으면) -> 군집주행 종료
def PlatooningCheck():
    global location
    if((location[0][0]+1 < location[1][0]) or 
       (location[0][0]-1 > location[1][0]) or 
       (location[0][1]+1 < location[1][1]) or 
       (location[0][1]-1 > location[1][1])):
        return 1
    return 0

# 위치가 바뀌었을 경우 체크
def LocationChange(prelocation):
    global location
    if((location[0][0] != prelocation[0][0]) or 
       (location[0][1] != prelocation[0][1]) or 
       (location[1][0] != prelocation[1][0]) or 
       (location[1][1] != prelocation[1][1])):
        return 1
    return 0

async def accept(websocket, path):
    # 위치 초기화
    global location
    location=[[0, 0], [0, 0]]
    prelocation = [[0, 0], [0, 0]]
    while True: # 지속적으로
        try: # client의 메세지를 받는다 (이때 연결이 끊어진 상태를 지속적으로 확인하기 위해 timer를 이용)
            data = await asyncio.wait_for(websocket.recv(), timeout=1.0)
        except asyncio.TimeoutError:
            # 커넥팅 체크 -> 위치가 벗어나면 해제
            if(PlatooningCheck()):
                if(location[0][0]!=9): # Sentinel Value(Disconnect 버튼 클릭시 아래 메세지 안보내고 즉시 종료)
                    await websocket.send("Disconnect "+str(location))
                await websocket.close()
                break
            # 군집주행 유지 중 서로간의 위치 변경시 체크
            if(LocationChange(prelocation)):
                await websocket.send("Connect "+str(location))
                prelocation = copy.deepcopy(location)
            continue
        carnum = int(data[0])
        carlocation = [int(data[2]), int(data[4])]
        location[carnum-1]=carlocation
        # 위치 정보 변경을 하고나서 한번더 커넥팅 체크  
        if(PlatooningCheck()): # 서로 멀어지면 연결 해제 및 군집주행 종료
                if(location[0][0]!=9): # Sentinel Value
                    await websocket.send("Disconnect "+str(location))
                await websocket.close()
                break
        
start_server = websockets.serve(accept, "172.30.1.4", 8888) # 서버를 생성 (IP/Port)
asyncio.get_event_loop().run_until_complete(start_server) # 서버를 실행하고 client부터의 accept를 실행
asyncio.get_event_loop().run_forever()                    # 이때 비동기로 2개의 car의 accept를 받을 수 있음