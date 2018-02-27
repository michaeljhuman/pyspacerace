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
TextRect = pygame.Rect( InnerBorderOffset + InnerBorderRect.width // 4, InnerBorderOffset + 50,
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

# init font
pygame.font.init() # you have to call this at the start, 
                   # if you want to use this module.
GameFont = pygame.font.SysFont('Comic Sans MS', 20)
    
# Critical spaceship params
RotationRate = 2
PlayerSpaceshipAcc = 70.0
PlayerSpaceshipDec = 70.0
AISpaceshipAcc = 90
AISpaceshipDec = 90
AITargetSpeed = 500
MaxSpeed = 500

# Misc
BounceVelLoss = .5
RotationThreshold = math.radians( 5)
AITargetSpeedThreshold = 5
TrackPointListVertCount = 5
TrackPointListHorzCount = 10

# AI tuning
CornerApproachMaxThreshold = 300
CornerApproachMinThreshold = 50
CornerApproachSpeed = MaxSpeed*.3

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
report7 = Report( .3)
            
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
                print( 't')
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
        self.acceleration = 0.0
        self.rotationRate = 0.0
        self._initialRotate()
        self.lapCounter = LapCounter( startFinishLine)
        
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
        if abs(self.angle - self.lastAngle) > RotationThreshold:
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
        self.move( delta)
        self.rotate( delta)
            
    def startAcceleration( self):
        self.acceleration = 50
        
    def stopAcceleration( self):
        self.acceleration = 0
        
    def startDeceleration( self):
        self.acceleration = -50

    def stopDeceleration( self):
        self.acceleration = 0
        
    def startRotatingLeft( self):
        self.rotationRate = RotationRate
                               
    def startRotatingRight( self):
        self.rotationRate = -RotationRate
        
    def stopRotating( self):
        self.rotationRate = 0
                               
    def draw( self):                    
        # Update screen
        screen.blit( self.image, self.rect)
    
class PlayerSpaceship( Spaceship):
    def __init__( self, bitmapFile, initPos, angle, vel, startFinishLine):
        Spaceship.__init__( self, bitmapFile, initPos, angle, vel, startFinishLine)
        
    def startAcceleration( self):
        self.acceleration = PlayerSpaceshipAcc
                
    def startDeceleration( self):
        self.acceleration = -PlayerSpaceshipDec

    def keyDown( self, key):
        if key == ord('w'):
            self.startAcceleration()
        elif key == ord('s'):
            self.startDeceleration()
        elif key == ord('a'):
            self.startRotatingLeft()
        elif key == ord('d'):
            self.startRotatingRight()
            
    def keyUp( self, key):
        if key == ord('w'):
            self.stopAcceleration()
        elif key == ord('s'):
            self.stopDeceleration()
        elif key == ord('a'):
            self.stopRotating()
        elif key == ord('d'):
            self.stopRotating()
    
class AISpaceship( Spaceship):
    def __init__( self, bitmapFile, initPos, angle, vel,\
                  startFinishLine, trackPointsList):
        Spaceship.__init__( self, bitmapFile, initPos, angle, vel, startFinishLine)
        self.lastPointIdx = -1
        self.trackPointsList = trackPointsList
    def startAcceleration( self):
        self.acceleration = AISpaceshipAcc
                
    def startDeceleration( self):
        self.acceleration = -AISpaceshipDec

    def nearCorner( self):
        for p in TrackCorners:
            if p.distance( self.pos) <= CornerApproachMaxThreshold\
                and p.distance( self.pos) >= CornerApproachMinThreshold:
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
            report4.report( 'Braking for corner %s; distance %.1f' %\
                (str(cornerPoint), cornerPoint.distance( self.pos)))
            self.startDeceleration()
            return True
        else:
            return False
        
    def AI( self, delta):
        nextPointIdx, nextPoint = self.getCurrentTargetPoint()
        if nextPointIdx < self.lastPointIdx and\
           self.lastPointIdx - nextPointIdx < 2:
            #report6.report( 'Dont move backwards; last %d next %d' % ( self.lastPointIdx, nextPointIdx))
            nextPointIdx = self.lastPointIdx
            nextPoint = self.trackPointsList.list[nextPointIdx]
        else:
            self.lastPointIdx = nextPointIdx
        nextX, nextY = nextPoint
        # next point angle
        newAngle = math.atan2( -(nextY - self.pos.y), nextX - self.pos.x)
        #report1.report( 'AI seeking point; idx %d %s' % ( nextPointIdx, nextPoint))
        #report2.report( 'AI current angle %s; desired angle %s' % ( self.angle, newAngle))
        # Steer towards point
        if abs(newAngle - self.angle) > math.radians( 5):
            #pdb.set_trace()
            #report3.report( 'AI turning; angle %f; newAngle %f' % ( self.angle, newAngle))
            diffAngle = newAngle - self.angle
            if diffAngle < -math.pi or diffAngle > math.pi:
                diffAngle = self.angle - newAngle
            if diffAngle < 0:
                self.startRotatingRight()
            else:
                self.startRotatingLeft()
        else:
            self.stopRotating()

        # Acclerate based on target speed
        if not self.brakeForCorner( delta):
            temp = AITargetSpeed - self.vel.speed()
            if temp > AITargetSpeedThreshold:
                self.stopDeceleration()
                self.startAcceleration()
            elif temp < -AITargetSpeedThreshold:
                self.stopAcceleration()
                self.startDeceleration()
            else:
                self.stopAcceleration()
                self.stopDeceleration()

    def update( self, delta):
        self.AI( delta)
        super().update( delta)

class TrackPointsList:
    def __init__( self):
        self.list = []
        for idx, p1 in enumerate( TrackCorners):
            p2 = TrackCorners[(idx+1)%len(TrackCorners)]
            if idx == 0 or idx == 2:
                for i in range( TrackPointListHorzCount):
                    p = XY(int((p1.x + (p2.x - p1.x) / TrackPointListHorzCount * i)),
                        p1.y)
                    self.list.append( p)      
            else:
                for i in range( TrackPointListVertCount):
                    p = XY(p1.x,
                        int( p1.y + (p2.y - p1.y) / TrackPointListVertCount * i))
                    self.list.append( p)
        # Find closest point to start position
        startIdx, startPoint = self.findClosestPoint( PlayerStartLoc)
        # Remove corners and reorder
        tempList = []
        for i in range( startIdx, startIdx + len( self.list)):
            p = self.list[i%len(self.list)]
            if not p in TrackCorners:
                tempList.append( self.list[i])
        self.list = tempList
        
    def findClosestPoint( self, pos):
        minDistance = 1000000
        minDistancePointIdx = 0
        for idx, p in enumerate( self.list):
            tempDistance = Distance( pos, p)
            if tempDistance < minDistance:
                minDistance = tempDistance
                minDistancePointIdx = idx
        return minDistancePointIdx, self.list[minDistancePointIdx]

    def nextPoint( self, idx):
        nextIdx = idx + 1
        nextIdx %= len(self.list)
        #report5.report( 'idx %d; next idx %d' % ( idx, nextIdx))
        return nextIdx, self.list[nextIdx]
    
    def draw( self):
        for p in self.list:
            pygame.draw.circle( screen, White, p.list, 5)
    
def DrawLapCounters( playerShip, AIShip):
    text = "Player laps: %d     Computer laps: %d" % (playerShip.lapCounter.counter, AIShip.lapCounter.counter)
    textSurface = GameFont.render( text, False, White)
    screen.blit( textSurface, TextRect)
    
pygame.init()

trackPointsList = TrackPointsList()
startFinishLine = StartFinishLine()

spaceshipPlayer = PlayerSpaceship( "spaceship1.bmp", PlayerStartLoc, 0,
    Velocity( 0.0, 0.0), startFinishLine)
spaceshipComputer = AISpaceship( "spaceship3.bmp", ComputerStartLoc, 0,
    Velocity( 15.0, 0.0), startFinishLine,
    trackPointsList)

prevTime = time.clock()

while 1:
    currentTime = time.clock()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            spaceshipPlayer.keyDown( event.key)
        elif event.type == pygame.KEYUP:
            spaceshipPlayer.keyUp( event.key)

    screen.fill( Black)
    pygame.draw.rect( screen, White, InnerBorderRect, 1)
    spaceshipComputer.draw()
    spaceshipPlayer.draw()
    trackPointsList.draw()
    DrawLapCounters( spaceshipPlayer, spaceshipComputer)
    startFinishLine.draw()
    pygame.display.flip()

    delta = currentTime - prevTime
    spaceshipPlayer.update( delta)
    spaceshipComputer.update( delta)
    
    prevTime = currentTime
    

    
