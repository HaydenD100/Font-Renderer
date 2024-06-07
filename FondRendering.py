import pygame
import time
import math
import random
from pathlib import Path
import struct
import numpy as np


class Reader():
    def __init__(self,file):
        self.f = open(file, 'rb')
        self.array = np.fromfile(self.f, dtype=np.uint8)
        self.pos = 0
    
    def skipBytes(self, bytes):
        self.pos += bytes
    def readByte(self):
        byte = self.array[self.pos]
        self.pos += 1
        return byte
    def readByteAt(self,pos,byte):
        currentPos = self.pos
        self.pos = pos
        data = 0
        for i in range(byte):
            data = data << 8
            data += self.array[self.pos] 
            self.pos += 1
        self.pos = currentPos
        return data

    def readBytes(self, byte):
        data = 0
        for i in range(byte):
            data = data << 8
            data += self.array[self.pos] 
            self.pos += 1
        return data
        
    def readInts(self, byte):
        data = 0
        for i in range(byte):
            data = data << 8
            data += self.array[self.pos] 
            self.pos += 1
        return data


SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800

points = [(100,100), (500,100),(800,300)]
reader =  Reader('JetBrainsMono-Bold.ttf')
#reader =  Reader('Envy Code R.ttf')


cCode = {}
loca = []
abcDict = {}
tables = {}
        
def CheckFlag(byte, index):
    return ((byte >> index) & 1) == 1

def DrawGlpyhFromChar(character,glpyhTableAddr,x,y,size):
    addr = loca[cCode[ord(character)]]
    reader.pos = glpyhTableAddr + addr
    Gdata = ReadGlpyph()
    if(Gdata == False):
        addr = loca[0]
        reader.pos = glpyhTableAddr + addr
        Gdata = ReadGlpyph()
    DrawCords(Gdata[0],Gdata[1],Gdata[2],-size,x,y)

def GetCords(flags, readingx):
    OffsetsizeFlag  = 1 if readingx == True else 2
    OffsetSignOrSkip  = 4 if readingx == True else 5
    cords = [0] * len(flags)
    
    for i in range(len(flags)):
        #cause the cords are offsets in file
        cords[i] = cords[max(0, i - 1)]
        flag = flags[i]
        onCurve = CheckFlag(flag,0)
        
        if(CheckFlag(flag,OffsetsizeFlag)):
            offset = reader.readByte()
            sign = 1 if CheckFlag(flag,OffsetSignOrSkip) == True else -1
            cords[i] +=offset * sign
        
        
        elif(not CheckFlag(flag,OffsetSignOrSkip)):
            cords[i] +=np.int16(reader.readBytes(2))
    return cords

def readLocaTable(addr):
    reader.pos = addr
    loca = []
    for i in range(10000):
        loca.append(reader.readBytes(4))
    return loca

def readFormat4():
    global loca
    format = reader.readBytes(2)
    lenght = reader.readBytes(2)
    language = reader.readBytes(2)
    segCountX2 = reader.readBytes(2)
    searchRange = reader.readBytes(2)
    entrySelector = reader.readBytes(2)
    rangeShift = reader.readBytes(2)
    
    mGTrue = False
    
    endcode = []
    startcode = []
    IDdelta = []
    idrangeOffSet = []
    idrangeOffSetAddr = []
    
    print("Format: " + str(format))
    for i in range(int(segCountX2/2)):
        endcode.append(reader.readBytes(2))
        
    print("ReservedPad: " + str(reader.readBytes(2)))
    
    for i in range(int(segCountX2/2)):
        startcode.append(reader.readBytes(2))
    for i in range(int(segCountX2/2)):
        IDdelta.append(reader.readBytes(2))
        
    IDRangeOffset = []
    for i in range(int(segCountX2/2)):
        idrangeOffSetAddr.append(reader.pos)
        idrangeOffSet.append(reader.readBytes(2))
        print(idrangeOffSet[-1])
    
    for i in range(len(startcode)):
        endcodeVar = endcode[i]
        currCodeVar = startcode[i]
        
        if(currCodeVar == 65535): break
        
        while (currCodeVar <= endcodeVar):
            glyphindex = ""
            
            if(idrangeOffSet[i] == 0):
                glyphindex = (currCodeVar + IDdelta[i]) % 65536
            else:
                readerLoc = reader.pos
                rangeOffsetLoc = idrangeOffSetAddr[i] + idrangeOffSet[i]
                glyphindexarrayloc = 2 * (currCodeVar - startcode[i]) + rangeOffsetLoc
                
                reader.pos = glyphindexarrayloc
                glyphindex = reader.readBytes(2)
                
                if(not glyphindex == 0):
                    glyphindex = (glyphindex + IDdelta[i]) % 65536
                
                reader.pos = readerLoc  
        
            cCode[currCodeVar] = glyphindex
            currCodeVar += 1
            if(globals == 0):
                mGTrue = True
    if(not mGTrue):
        cCode[65535] = 0    
        
    loca = readLocaTable(28460)
     
def ReadCmap():
    version = reader.readBytes(2)
    numberSubtables = reader.readBytes(2)
    
    platform = []
    for i in range(numberSubtables):
        platform.append([reader.readBytes(2),reader.readBytes(2),reader.readBytes(4)])
    print(platform)
    readFormat4()
        
def ReadGlpyph():
    endIndices = []
    endIncicesCount = reader.readBytes(2)
    print("endcount" + str(endIncicesCount))
    if(endIncicesCount < 0 or endIncicesCount > 20):
        return False
    reader.skipBytes(8) #skips bounding boxes
    
    for i in range(endIncicesCount):
        endIndices.append(reader.readBytes(2))
    
    skipped = reader.readBytes(2)
    #print("Skipped: " + str(skipped))
    reader.skipBytes(skipped)
    numPoints = endIndices[-1] + 1
    allFlags = []
    for i in range(numPoints):
        
        flag = reader.readByte()
        allFlags.append(flag)
        #print(flag)
        if(CheckFlag(flag,3)):
            #print("flag" + str(i))
            for i in range(reader.readByte()):
                allFlags.append(flag)
                
    cordX = GetCords(allFlags,True)
    cordY = GetCords(allFlags,False)
    
    return (cordX,cordY,endIndices)
    
def DrawCords(cordX, cordY, endIndices, size, x, y):
    showPoints = False
    #colors = [(255,255,255),(0,255,0),(0,0,255),(255,0,255),(255,0,255)]
    
    if(showPoints):
        for i in range(len(cordX)):
            pygame.draw.circle(screen,(255,0,0),(cordX[i] * -size + x,cordY[i] * size + y),5,5)
        
    currentPoint = (cordX[0],cordY[0])
    
    startIndex = 0
    for e in range(len(endIndices)):
        points = []
        for i in range(len(cordX)):

            if(i >= startIndex and i <= endIndices[e]   ):
                points.append((cordX[i]* -size + x,cordY[i] * size + y))
           
        points.append((cordX[startIndex] * -size + x,cordY[startIndex] * size + y))
        startIndex = endIndices[e] + 1
        
        #print(points)
        currentPoint = points[0]
        for point in points:
            pygame.draw.line(screen,(255,255,255),currentPoint,point,1)
            currentPoint = point



    pygame.display.update()

def ReadFont():
    reader.skipBytes(4)
    numTables = reader.readBytes(2)
    print("NumTables:" + str(numTables))
    reader.skipBytes(6)
    for b in range(numTables):
        tag = []
        for i in range(4):
            tag.append(reader.readByte())
        checksum = reader.readBytes(4)
        offset = reader.readBytes(4)
        lenght = reader.readBytes(4)
        tables[str(bytes(tag).decode())] = offset
        print("Tag:  " + bytes(tag).decode() + "   location:"+str(offset))
    reader.pos = tables["cmap"]
    ReadCmap()
    



pygame.init()   
screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
pygame.display.set_caption('Font Renderer')
running = False
ReadFont()
running = True
while running:
    #sets p1 to the moues pos
    points[1] = pygame.mouse.get_pos()
    for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False  
    #Draw()
    word = "Font test v1.0.0\n1234567890qwerty\nasdfghklzxcvbnm\n!@#$%^&*()_+{}:'<>?-=[];',./|\nQWERTYUIOPASDFGHJKL\nZXCVM"
    size = 0.05
    x = 0
    y = 1000 * size
    for c in word:
        if(c == " "):
            x += 400 * size
            continue
        if(c == "\n"):
            y += 1000 * size
            x = 0
            continue
        DrawGlpyhFromChar(c,tables["glyf"],x,y,size)
        x += 600 * size

    