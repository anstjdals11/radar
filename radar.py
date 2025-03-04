import tkinter as tk
import math
import serial
import time

def btcmd():
    print("ㅎㅇ월드")


WIDTH = 640
HEIGHT = 480
angle = 0
direction = 0
sendingAngle = 0
objects = [[0, 0],[10,0],[20, 70],[30,0],[40,0],[50,0],[60,0],[70,0],
           [80,0],[90,0],[100,0],[110,0],[120, 0],[130,0],[140,30],[150,0],
           [160,0],[170,150],[180,0]]

ser = serial.Serial("COM6", 115200)

# 개체 호출
root = tk.Tk()
root.title("Ultrasonic Radar")
canvas = tk.Canvas(root, width = WIDTH, height = HEIGHT, bg = "black")
button = tk.Button(root, text = "ㅎㅇ월드", command = btcmd)
button.pack()

# 그리기
canvas.pack()

def drawObject(angle, distance):
    radius = WIDTH / 2
    x = radius + math.cos(angle * math.pi / 180) * distance
    y = radius - math.sin(angle * math.pi / 180) * distance
    canvas.create_oval(x-5, y-5, x+5, y+5, fill = 'green')
    # 동그라미 그리는 명령어

def updateScan():
    global angle
    global direction
    global objects
    global sendingAngle
    receiveDistance = 0
    # 각도 전송
    if angle % 10 == 0:
        sendingAngle = angle
        mask = b'\x7f' # 0x80 마스크오프를 위함
        ser.write(bytes(bytearray([0x02, 0x52]))) # 0x52 : 'R'
        angleH = (angle >> 7) + 128
        angleL = (angle & mask[0]) + 128
        crc = (0x02 + 0x52 + angleH + angleL) % 256
        ser.write(bytes(bytearray([angleH, angleL, crc, 0x03])))
        # 거리 수신
        if  ser.in_waiting > 0:
            data = ser.read()
            if data == b'\x02':
                # 두번째 byte 수신 대기
                timeout = time.time() + 0.002 # 2ms 더한 값을 저장
                lostData = False
                while ser.in_waiting < 5:
                    # 5글자 될 때까지 루프
                    # timeout 처리
                    if time.time() > timeout:
                        lostData = True
                        break
                if lostData == False:
                    data = ser.read(5)
                    if data[0] == 65:
                        # crc 검사
                        crc = (2 + data[0] + data[1] + data[2]) % 256
                        if crc == data[3]: # crc 통과
                            if data[4] == 3: # ETX 통과
                                # 데이터 파싱
                                mask = b'\x7f'
                                data_one = bytes([data[1] & mask[0]])
                                receiveDistance = int.from_bytes(data_one) << 7
                                data_one = bytes([data[2] & mask[0]])
                                receiveDistance += int.from_bytes(data_one)
                                # 물체 업데이트
                                for obj in objects:
                                    if obj[0] == sendingAngle:
                                        obj[1] = receiveDistance
                                    
        
    # 화면 지우기
    canvas.delete('all')
    # 레이더 선 그리기
    radius = WIDTH / 2
    length = radius
    x = radius + math.cos(angle * math.pi / 180) * length
    y = radius - math.sin(angle * math.pi / 180) * length
    canvas.create_line(x, y, radius, radius, fill = 'green', width = 4)
    # 물체 그리기
    for obj in objects:
        drawObject(obj[0], obj[1])
    # objects 안에 있는 배열을 하나씩 가져옴
    # obj : 2차원 배열. 0 : 각도 1 : 거리
       
    # 각도 업데이트
    if direction == 0:
        angle += 1
        if angle == 181:
            direction = 1
    else:
        angle -= 1
        if angle == -1:
            direction = 0        
    """
    angle = angle + 1
    if angle > 359:
        angle = 0
    x = 320 + math.cos(angle * math.pi / 180) * 200
    y = 240 - math.sin(angle * math.pi / 180) * 200
    canvas.create_line(320, 240, x, y, fill='red', width=2)
    """
    # 재귀 호출
    canvas.after(50, updateScan) # 50ms 뒤에 다시 함수 호출
    

# 화면 표시
updateScan()
root.mainloop()
