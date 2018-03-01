# Space race, inspired by Omega race
import sys, pygame
import time
import math
import pdb

class XY:
    def __init__( self, x, y):
        self.list = [ x, y]
    @property
    def x( self):
        return self.list[0]
    @x.setter
    def x( self, x):
        self.list[0] = x
    @property
    def y( self):
        return self.list[1]
    @y.setter
    def y( self, y):
        self.list[1] = y
    def distance( self, p):
        return Distance( self, p)
    def copy( self):
        return XY( self.x, self.y)
    def __getitem__( self, idx):
        if idx >= len( self.list):
            raise IndexError()
        else:
            return self.list[idx]
    def __eq__( self, arg):
        if arg == None:
            return False
        elif self.x == arg.x and self.y == arg.y:
            return True
        else:
            return False
    def __str__( self):
        return 'x: %.1f; y: %.1f' % ( self.x, self.y)
    
# Display stuff
DisplaySize = ScreenWidth, ScreenHeight = 900, 700
ScreenRect = pygame.Rect( 0, 0, ScreenWidth, ScreenHeight)
InnerBorderOffset = 200
InnerBorderRect = pygame.Rect( InnerBorderOffset, InnerBorderOffset,
                               ScreenWidth - 2*InnerBorderOffset, ScreenHeight - 2*InnerBorderOffset)
TextRect = pygame.Rect( InnerBorderOffset + 50, InnerBorderOffset + 50,
                       200, 100)
PlayerStartLoc = XY( 100, 100)
ComputerStartLoc = XY( 100, 100)
TrackCorners = ( XY( InnerBorderOffset // 2, InnerBorderOffset // 2),
    XY( ScreenWidth - InnerBorderOffset // 2, InnerBorderOffset // 2),
    XY( ScreenWidth - InnerBorderOffset // 2, ScreenHeight - InnerBorderOffset // 2),
    XY( InnerBorderOffset // 2, ScreenHeight - InnerBorderOffset // 2))
Black = 0, 0, 0
White = pygame.Color('White')

# Create screen
screen = pygame.display.set_mode( DisplaySize)
#screen = pygame.transform.scale( screen, DisplaySize)

# init font
pygame.font.init() # you have to call this at the start, 
                   # if you want to use this module.
GameFont = pygame.font.SysFont('Comic Sans MS', 20)
    
# Critical spaceship params
MaxRotationRate = 2
PlayerSpaceshipAcc = 70
PlayerSpaceshipDec = 70
AISpaceshipAcc = 70
AISpaceshipDec = 70
AITargetSpeed = 500
MaxSpeed = 500

# Misc
BounceVelLoss = .8

AITargetSpeedThreshold = 50
TrackPointListVertCount = 5
TrackPointListHorzCount = 10

# AI tuning
CornerApproachAdjust = 1.1 # Increase threshold by some factor
CornerApproachMaxThresholdX = (ScreenWidth - 2*InnerBorderOffset) // 2 *\
    CornerApproachAdjust
CornerApproachMaxThresholdY = (ScreenHeight - 2*InnerBorderOffset) // 2 *\
    CornerApproachAdjust                              
CornerApproachMinThreshold = 50
CornerApproachSpeed = MaxSpeed*.3

# Thrust mode enum
ACCELLERATE = 1
BRAKE = -1
COAST = 0

# Takes two XY args
def Distance( p1, p2):
    return math.sqrt( (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)

class Report:
    def __init__( self, interval):
        self.interval = interval
        self.startTime = time.clock()
        self.lastTime = time.clock()
        self.elapsed = 0
    def report( self, s):
        self.elapsed += ( time.clock() - self.lastTime)
        if self.elapsed > self.interval:
            print( s)
            self.elapsed = 0
        self.lastTime = time.clock()
report1 = Report( .5)
report2 = Report( .5)
report3 = Report( .5)
report4 = Report( .5)
report5 = Report( .5)
report6 = Report( .1)
            
class StartFinishLine:
    def __init__( self):
        self.startLine = pygame.Rect( ScreenWidth // 2, 0, 2, InnerBorderOffset)
        self.checkpoint = pygame.Rect( ScreenWidth // 2, ScreenHeight - InnerBorderOffset,
            2, InnerBorderOffset)
        self.crossedCheckpoint = False
    def checkPointCollision( self, shipRect):
        if self.checkpoint.colliderect( shipRect):
            return True
        else:
            return False
    def startFinishLineCollision( self, shipRect):
        if self.startLine.colliderect( shipRect):
            return True
        else:
            return False        
    def draw( self):
        pygame.draw.rect( screen, White, self.startLine, 1)

class LapCounter():
    def __init__( self, startFinishLineArg):
        self.startFinishLine = startFinishLineArg
        self.counter = 0
        self.crossedCheckpoint = False
    def update( self, shipRect):
        if self.crossedCheckpoint == False:
            if self.startFinishLine.checkPointCollision( shipRect):
                self.crossedCheckpoint = True
        else:
            if self.startFinishLine.startFinishLineCollision( shipRect):
                self.crossedCheckpoint = False
                self.counter += 1
             
class Velocity( XY):
    def __init__( self, x, y):
        super().__init__( x, y)
    def bouncex( self):
        self.x = -self.x * BounceVelLoss
    def bouncey( self):
        self.y = -self.y * BounceVelLoss
    def accelerate( self, acc, angle):
        oldVel = self.copy()
        self.x += acc * math.cos( angle)
        self.y -= acc * math.sin( angle)
        # Speed limiter, for playability
        if self.speed() >= MaxSpeed:
            self.list = oldVel.list
    def speed( self):
        return math.sqrt( self.x ** 2 + self.y ** 2)
    def copy( self):
        return Velocity( self.x, self.y)
    
    def __str__( self):
        return str( self.list)
    
class Spaceship:
    def __init__(self, bitmapFile, initPos, angle, vel, startFinishLine):
        self.vel = vel
        self.pos = initPos
        self.image = pygame.image.load( bitmapFile)
        self.imageCopy = self.image.copy()
        self.rect = self.image.get_rect()
        self.rect = self.rect.move( initPos.x, initPos.y)
        self.originAngle = math.pi / 2 # Angle in radians, with 0 being positive x axis; counterclockwise rotation
        self.angle = angle
        self.lastAngle = angle
        self.acceleration = 0
        self.rotationRate = 0
        self._initialRotate()
        self.lapCounter = LapCounter( startFinishLine)
        self.elapsedLapTime = 0
        self.lastLapTime = 0
        
    def _updateVel( self, delta):
        self.vel.accelerate( self.acceleration * delta, self.angle)
        
    def _updateAngle( self, delta):
        self.angle += self.rotationRate * delta
        if self.angle < -math.pi:
            self.angle += math.pi * 2
        elif self.angle > math.pi:
            self.angle -= math.pi * 2

    def computeNewPos( self, delta):
        newX = self.pos.x + self.vel.x * delta
        newY = self.pos.y + self.vel.y * delta
        return XY( newX, newY)
    
    def _updatePos( self, delta):
        newX, newY = self.computeNewPos( delta)
        
        # Check for outside collision with x move
        tempRect = self.rect.move( newX - self.rect.centerx, 0)
        if not screen.get_rect().contains( tempRect):
            if tempRect.x < 0:
                newX = self.rect.width // 2 + 1
            else:
                newX = ScreenWidth - self.rect.width // 2 - 1
            self.vel.bouncex()
                    
        # Check for outside collision with y move
        tempRect = self.rect.move( 0, newY - self.rect.centery)
        if not screen.get_rect().contains( tempRect):
            if tempRect.y < 0:
                newY = self.rect.height // 2 + 1
            else:
                newY = ScreenHeight - self.rect.height // 2 - 1
            self.vel.bouncey()
            
        tempRect = self.rect.move( newX - self.rect.centerx, 0)
        if tempRect.colliderect( InnerBorderRect):
            self.vel.bouncex()
        else:
            self.rect = tempRect
            self.pos.x = newX
        tempRect = self.rect.move( 0, newY - self.rect.centery)
        if tempRect.colliderect( InnerBorderRect):
            self.vel.bouncey()
        else:
            self.rect = tempRect
            self.pos.y = newY
        
    def move( self, delta):
        prevPos = self.pos.copy()
        self._updateVel( delta)
        self._updatePos( delta)
        self.lapCounter.update( self.rect)
        
    def _initialRotate( self):
        rotationAngle = math.degrees( self.angle - self.originAngle)
        self.image = pygame.transform.rotate( self.imageCopy, rotationAngle)
        self.rect = self.image.get_rect( center=self.rect.center)
        
    def rotate( self, delta):
        self._updateAngle( delta)
        # Rotate image
        rotationAngle = math.degrees( self.angle - self.originAngle)
        tempImage = pygame.transform.rotate( self.imageCopy, rotationAngle)
        tempRect = tempImage.get_rect( center=self.rect.center)
        collided = False
        if not screen.get_rect().contains( tempRect):
            collided = True
        if tempRect.colliderect( InnerBorderRect):
            collided = True
        if collided:
            self.angle = self.lastAngle
        else:
            self.image = tempImage
            self.rect = tempRect
            self.lastAngle = self.angle

    def update( self, delta):
        oldLapCounter = self.lapCounter.counter
        self.move( delta)
        self.rotate( delta)
        if self.lapCounter.counter > oldLapCounter:
            self.lastLapTime = self.elapsedLapTime
            self.elapsedLapTime = 0
        else:
            self.elapsedLapTime += delta
                                       
    def draw( self):                    
        # Update screen
        screen.blit( self.image, self.rect)
    
class PlayerSpaceship( Spaceship):
    def __init__( self, bitmapFile, initPos, angle, vel, startFinishLine):
        Spaceship.__init__( self, bitmapFile, initPos, angle, vel, startFinishLine)
        
    def keyDown( self, key):
        if key == ord('w'):
            self.acceleration = PlayerSpaceshipAcc
        elif key == ord('s'):
            self.acceleration = -PlayerSpaceshipAcc
        elif key == ord('a'):
            self.rotationRate = MaxRotationRate
        elif key == ord('d'):
            self.rotationRate = -MaxRotationRate
            
    def keyUp( self, key):
        if key == ord('w'):
            self.acceleration = 0
        elif key == ord('s'):
            self.acceleration = 0
        elif key == ord('a'):
            self.rotationRate = 0
        elif key == ord('d'):
            self.rotationRate = 0
    
class AISpaceship( Spaceship):
    def __init__( self, bitmapFile, initPos, angle, vel,\
                  startFinishLine, trackPointsList):
        Spaceship.__init__( self, bitmapFile, initPos, angle, vel, startFinishLine)
        self.lastPointIdx = -1
        self.trackPointsList = trackPointsList

    def nearCorner( self):
        if abs(self.vel.x) > abs(self.vel.y):
            cornerApproachMaxThreshold = CornerApproachMaxThresholdX
        else:
            cornerApproachMaxThreshold = CornerApproachMaxThresholdY
        for p in TrackCorners:
            if p.distance( self.pos) >= CornerApproachMinThreshold\
                and p.distance( self.pos) <= cornerApproachMaxThreshold:
                return p
        return None

    def movingTowards( self, point, delta):
        newPos = self.computeNewPos( delta)
        if Distance( newPos, point) < Distance( self.pos, point):
            return True
        else:
            return False

    def getCurrentTargetPoint( self):
        # Find closest point
        idx, p = self.trackPointsList.findClosestPoint( self.pos)
        # Next point
        nextIdx, nextPoint = self.trackPointsList.nextPoint( idx)
        return nextIdx, nextPoint

    def brakeForCorner( self, delta):
        cornerPoint = self.nearCorner()
        if cornerPoint != None and self.vel.speed() > CornerApproachSpeed\
           and self.movingTowards( cornerPoint, delta):
            report1.report( 'Braking for corner %s; distance %.1f' %\
                (str(cornerPoint), cornerPoint.distance( self.pos)))
            self.acceleration = -PlayerSpaceshipDec
            return True
        else:
            return False
        
    def update( self, delta):
        self.AI( delta)
        super().update( delta)
        
    def AI( self, delta):
        nextPointIdx, nextPoint = self.getCurrentTargetPoint()
        if nextPointIdx < self.lastPointIdx and\
           self.lastPointIdx - nextPointIdx < 2:
            #report2.report( 'Dont move backwards; last %d next %d' % ( self.lastPointIdx, nextPointIdx))
            nextPointIdx = self.lastPointIdx
            nextPoint = self.trackPointsList.tpList[nextPointIdx]
        else:
            self.lastPointIdx = nextPointIdx
        nextX, nextY = nextPoint
        # next point angle
        newAngle = math.atan2( -(nextY - self.pos.y), nextX - self.pos.x)
        #report3.report( 'AI seeking point; idx %d %s' % ( nextPointIdx, nextPoint))
        #report4.report( 'AI current angle %s; desired angle %s' % ( self.angle, newAngle))
        # Steer towards point
        if abs(newAngle - self.angle) > math.radians( 5):
            #pdb.set_trace()
            #report5.report( 'AI turning; angle %f; newAngle %f' % ( self.angle, newAngle))
            diffAngle = newAngle - self.angle
            if diffAngle < -math.pi or diffAngle > math.pi:
                diffAngle = self.angle - newAngle
            if diffAngle < 0:
                self.rotationRate = -MaxRotationRate
            else:
                self.rotationRate = MaxRotationRate
        else:
            self.rotationRate = 0

        # Acclerate based on target speed
        if not self.brakeForCorner( delta):
            temp = AITargetSpeed - self.vel.speed()
            if temp > AITargetSpeedThreshold:
                self.acceleration = AISpaceshipAcc
            elif temp < -AITargetSpeedThreshold:
                self.acceleration = -AISpaceshipDec
            else:
                self.acceleration = 0

class TomSpaceship( Spaceship):
    def __init__( self, bitmapFile, initPos, angle, vel,\
                  startFinishLine, trackPointsList):
        Spaceship.__init__( self, bitmapFile, initPos, angle, vel, startFinishLine)
        self.lastPointIdx = -1
        self.trackPointsList = trackPointsList
        self.trackLists = list()
        listLen = len(trackPointsList.tpList)
        self.thrustMode = ACCELLERATE
        for i in range(listLen):
            self.trackLists += [[]]
            for j in range(listLen):
                self.trackLists[i] += [trackPointsList.tpList[(i+j)%listLen]]
        
        self.steerPoint = list()
        for i in range(listLen):
            self.steerPoint += [None]
            
        for i in range(listLen):
            trackList = self.trackLists[i]
            if trackList[0].y == trackList[1].y == trackList[2].y == trackList[3].y:
                self.steerPoint[i] = trackList[3]
            if trackList[0].x == trackList[1].x == trackList[2].x == trackList[3].x:
                self.steerPoint[i] = trackList[3]
            if trackList[0].y != trackList[1].y or trackList[0].x != trackList[1].x:
                priorDiffX = trackList[0].x-trackList[-1].x
                priorDiffY = trackList[0].y-trackList[-1].y
                steerPoint = XY(trackList[1].x, trackList[1].y)
                if priorDiffY == 0:
                    steerPoint.x = trackList[0].x
                if priorDiffX == 0:
                    steerPoint.y = trackList[0].y
                self.steerPoint[i] = steerPoint
            
        for i in range(listLen,0,-1):
            if self.steerPoint[i%listLen] is None:
                self.steerPoint[i%listLen] = self.steerPoint[(i+1)%listLen]

    def isPastPoint(self, idx, delta):
        point = self.trackPointsList.tpList[idx]
        nextPoint = self.trackPointsList.tpList[(idx+1)%len(self.trackPointsList.tpList)]
        distShip = (nextPoint.x - self.pos.x)**2 + (nextPoint.y - self.pos.y)**2
        distPoints = (point.x - nextPoint.x)**2 + (point.y - nextPoint.y)**2
        return distShip < distPoints

    def AI(self, delta):
        targetSpeed = 8.0*AISpaceshipAcc
        tooFast = targetSpeed
        tooSlow = targetSpeed - targetSpeed/3.0

        # Find next point by finding closest point
        idx, p = self.trackPointsList.findClosestPoint(self.pos)
        if self.isPastPoint(idx, delta):  # and then checking if the ship is past it
            idx = (idx+1)%len(self.trackPointsList.tpList) # and using the next point if so
        idx = (idx+2)%len(self.trackPointsList.tpList)

        point = self.trackPointsList.tpList[idx]
        distNow = math.sqrt((point.x - self.pos.x)**2 + (point.y - self.pos.y)**2)
        distNext = math.sqrt((point.x - self.pos.x + self.vel.x*0.001)**2 + (point.y - self.pos.y + self.vel.y*0.001)**2)
        relSpeed = (distNext-distNow)/0.001
        trueSpeed = math.sqrt((self.vel.x)**2 + (self.vel.y)**2)
        self.thrustMode = COAST
        if relSpeed*2.0 < targetSpeed:
            self.thrustMode += 1
        if max(relSpeed*2.0, trueSpeed) > tooFast:
            self.thrustMode = -10
        
        trackList = self.trackLists[idx]
        positionLine = XY(trackList[0].x-self.pos.x,trackList[0].y-self.pos.y)
        positionAngle = math.atan2(-positionLine.y,positionLine.x)
        velocityAngle = math.atan2(-self.vel.y, self.vel.x)
        if self.thrustMode < COAST:
            desiredAngle = velocityAngle
            thrust = max(-AISpaceshipDec, -trueSpeed/delta)
        elif self.thrustMode > COAST:
            desiredAngle = positionAngle
            thrust = min(AISpaceshipAcc, (targetSpeed-relSpeed)/delta)
        else:
            desiredAngle = positionAngle
            thrust = 0
            
        angleDiff = desiredAngle - self.angle
        if angleDiff > math.pi:
            angleDiff -= 2.0*math.pi 
        if angleDiff < -math.pi:
            angleDiff += 2.0*math.pi

        angleChange = max(-MaxRotationRate, min(MaxRotationRate, angleDiff/delta))

        return (angleChange, thrust)

    def update(self, delta):
        (self.rotationRate, self.acceleration) = self.AI(delta)
        super().update(delta)

class TrackPointsList:
    def __init__( self):
        self.tpList = []
        for idx, p1 in enumerate( TrackCorners):
            p2 = TrackCorners[(idx+1)%len(TrackCorners)]
            if idx == 0 or idx == 2:
                for i in range( TrackPointListHorzCount):
                    p = XY(int((p1.x + (p2.x - p1.x) / TrackPointListHorzCount * i)),
                        p1.y)
                    self.tpList.append( p)      
            else:
                for i in range( TrackPointListVertCount):
                    p = XY(p1.x,
                        int( p1.y + (p2.y - p1.y) / TrackPointListVertCount * i))
                    self.tpList.append( p)
        # Find closest point to start position
        startIdx, startPoint = self.findClosestPoint( PlayerStartLoc)
        # Remove corners and reorder
        tempList = []
        for i in range( startIdx, startIdx + len( self.tpList)):
            p = self.tpList[i%len(self.tpList)]
            if not p in TrackCorners:
                tempList.append( self.tpList[i])
        self.tpList = tempList
        
    def findClosestPoint( self, pos):
        minDistance = 1000000
        minDistancePointIdx = 0
        for idx, p in enumerate( self.tpList):
            tempDistance = Distance( pos, p)
            if tempDistance < minDistance:
                minDistance = tempDistance
                minDistancePointIdx = idx
        return minDistancePointIdx, self.tpList[minDistancePointIdx]

    def nextPoint( self, idx):
        nextIdx = idx + 1
        nextIdx %= len(self.tpList)
        #report5.report( 'idx %d; next idx %d' % ( idx, nextIdx))
        return nextIdx, self.tpList[nextIdx]
    
    def draw( self):
        for p in self.tpList:
            pygame.draw.circle( screen, White, p.list, 5)

def DrawText( textLines):
    tempRect = TextRect.copy()
    for line in textLines:
        textSurface = GameFont.render( line, False, White)
        screen.blit( textSurface, tempRect)
        wordWidth, wordHeight = textSurface.get_size()
        tempRect = tempRect.move( 0, wordHeight)
        
def DrawInfo( playerShip, AIShip):
    lines = []
    text = "Player laps: %d     Computer laps: %d" %\
        (playerShip.lapCounter.counter, AIShip.lapCounter.counter)
    lines.append( text)
    text = "Player speed: %.0f     Computer speed: %.0f"\
        % (playerShip.vel.speed(), AIShip.vel.speed())
    lines.append( text)
    text = "Player laptime: %.2f     Computer laptime: %.2f"\
        % (playerShip.lastLapTime, AIShip.lastLapTime)
    lines.append( text)
    text = "Tom speed: %.2f     Tom laptime: %.2f"\
        % (spaceshipComputer2.vel.speed(), spaceshipComputer2.lastLapTime)
    lines.append( text)
    text = "Tom laps: %d     Tom laptime: %.2f     Tom speed %.0f"\
        % (spaceshipComputer2.lapCounter.counter, spaceshipComputer2.vel.speed(),
           spaceshipComputer2.lastLapTime)
    lines.append( text)
    DrawText( lines)
    
pygame.init()

trackPointsList = TrackPointsList()
startFinishLine = StartFinishLine()

spaceshipPlayer = PlayerSpaceship( "spaceship1.bmp", PlayerStartLoc, 0,
    Velocity( 0.0, 0.0), startFinishLine)
spaceshipComputer = AISpaceship( "spaceship3.bmp", ComputerStartLoc, 0,
                                 Velocity( 0, 0), startFinishLine,
                                 trackPointsList)
spaceshipComputer2 = TomSpaceship( "spaceship4.bmp", XY(100,100), 0,
                                   Velocity( 0, 0), startFinishLine,
                                   trackPointsList)

prevTime = time.clock()

pause = True
while 1:
    currentTime = time.clock()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            pause = False
            spaceshipPlayer.keyDown( event.key)
        elif event.type == pygame.KEYUP:
            spaceshipPlayer.keyUp( event.key)
            
    screen.fill( Black)
    pygame.draw.rect( screen, White, InnerBorderRect, 1)
    spaceshipComputer.draw()
    spaceshipComputer2.draw()
    spaceshipPlayer.draw()
    trackPointsList.draw()
    DrawInfo( spaceshipPlayer, spaceshipComputer)
    startFinishLine.draw()
    pygame.display.flip()

    delta = currentTime - prevTime
    if not pause:
        spaceshipPlayer.update( delta)
        spaceshipComputer.update( delta)
        spaceshipComputer2.update( delta)
    prevTime = currentTime
    
    
