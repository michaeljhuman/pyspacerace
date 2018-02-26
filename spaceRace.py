# Space race, inspired by Omega race
import sys, pygame
import time
import math
import pdb


# Display stuff
DisplaySize = ScreenWidth, ScreenHeight = 900, 700
ScreenRect = pygame.Rect( 0, 0, ScreenWidth, ScreenHeight)
InnerBorderOffset = 200
InnerBorderRect = pygame.Rect( InnerBorderOffset, InnerBorderOffset,
                               ScreenWidth - 2*InnerBorderOffset, ScreenHeight - 2*InnerBorderOffset)
TextRect = pygame.Rect( InnerBorderOffset + InnerBorderRect.width // 4, InnerBorderOffset + 50,
                       200, 100)
PlayerStartLoc = ( 100, 100)
ComputerStartLoc = PlayerStartLoc
StartLine = pygame.Rect( ScreenWidth // 2, 0, 2, InnerBorderOffset)
TrackCorners = (( InnerBorderOffset // 2, InnerBorderOffset // 2),
    ( ScreenWidth - InnerBorderOffset // 2, InnerBorderOffset // 2),
    ( ScreenWidth - InnerBorderOffset // 2, ScreenHeight - InnerBorderOffset // 2),
    ( InnerBorderOffset // 2, ScreenHeight - InnerBorderOffset // 2))

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
AISpaceshipAcc = 80.0
AISpaceshipDec = 80.0
AITargetSpeed = 500
MaxSpeed = 500

# Misc
BounceVelLoss = .5
RotationThreshold = math.pi*2 * 5/360
AITargetSpeedThreshold = 5
TrackListPointCount = 23

# AI tuning
CornerApproachMaxThreshold = 300
CornerApproachMinThreshold = 50
CornerApproachSpeed = MaxSpeed*.3

def Distance( p1, p2):
    return math.sqrt( (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

def TrackPointsListMultiplier( v1, v2, x):
    return [ v1[i] + v2[i] * x for i in range(2)]

def AveragePoint( p1, p2):
    return ( (p1[0] + p2[0]) // 2, ( p1[1] + p2[1]) // 2)

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
        
class Velocity:
    def __init__( self, initVel):
        self.vel = [ initVel[0], initVel[1]]

    @property
    def x( self):
        return self.vel[0]
    @property
    def y( self):
        return self.vel[1]
    def getTuple( self):
        return ( self.vel[0], self.vel[1])
    def bouncex( self):
        self.vel[0] = -self.vel[0] * BounceVelLoss
    def bouncey( self):
        self.vel[1] = -self.vel[1] * BounceVelLoss
    def accelerate( self, acc, angle):
        oldVel = self.vel.copy()
        self.vel[0] += acc * math.cos( angle)
        self.vel[1] -= acc * math.sin( angle)
        # Speed limiter, for playability
        if self.speed() >= MaxSpeed:
            self.vel = oldVel
    def fromDelta( self, delta):
        return Velocity([ v * delta for v in self.vel ])
    def speed( self):
        return math.sqrt( self.vel[0] ** 2 + self.vel[1] ** 2)

    def copy( self):
        return Velocity( self.vel)
    
    def __str__( self):
        return str( self.vel)

class Coords:
    def __init__( self, initCoords):
        self.coords = initCoords
    @property
    def x( self):
        return self.coords[0]
    @x.setter
    def x( self, argX):
        self.coords = ( argX, self.coords[1])
    @property
    def y( self):
        return self.coords[1]
    @y.setter
    def y( self, argY):
        self.coords = ( self.coords[0], argY)
    def copy( self):
        return Coords( self.coords)
    
class Spaceship:
    def __init__(self, bitmapFile, initPos, angle, vel):
        self.vel = vel
        self.pos = Coords( initPos)
        self.image = pygame.image.load( bitmapFile)
        self.imageCopy = self.image.copy()
        self.rect = self.image.get_rect()
        self.rect = self.rect.move( initPos)
        self.originAngle = math.pi / 2 # Angle in radians, with 0 being positive x axis; counterclockwise rotation
        self.angle = angle
        self.lastAngle = angle
        self.acceleration = 0.0
        self.rotationRate = 0.0
        self.initialRotate()
        self.lapCounter = -1
        self.startLineCollision = False
        
    def updateVel( self, delta):
        self.vel.accelerate( self.acceleration * delta, self.angle)
        
    def updateAngle( self, delta):
        self.angle += self.rotationRate * delta
        if self.angle < -math.pi:
            self.angle += math.pi * 2
        elif self.angle > math.pi:
            self.angle -= math.pi * 2

    def computeNewPos( self, delta):
        newX = self.pos.x + self.vel.x * delta
        newY = self.pos.y + self.vel.y * delta
        return ( newX, newY)
    
    def updatePos( self, delta):
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
        self.updateVel( delta)
        self.updatePos( delta)
        self.countLaps( prevPos)

    def countLaps( self, prevPos):
        tempRect = pygame.Rect( prevPos.x, prevPos.y, abs( self.pos.x - prevPos.x), abs( self.pos.y - prevPos.y))
        if ( tempRect.colliderect( StartLine)):
            self.startLineCollision = True
        elif self.startLineCollision:
            # Count lap if we crossed in positive x direction
            if self.vel.x > 0:
                self.lapCounter += 1                
                print( 'lap')
                self.startLineCollision = False
            
    def initialRotate( self):
        rotationAngle = math.degrees( self.angle - self.originAngle)
        self.image = pygame.transform.rotate( self.imageCopy, rotationAngle)
        self.rect = self.image.get_rect( center=self.rect.center)
        
    def rotate( self, delta):
        self.updateAngle( delta)
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
    def __init__( self, bitmapFile, initPos, angle, vel):
        Spaceship.__init__( self, bitmapFile, initPos, angle, vel)
        
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
                  trackPointsList):
        Spaceship.__init__( self, bitmapFile, initPos, angle, vel)
        self.lastPointIdx = -1
        self.trackPointsList = trackPointsList
    def startAcceleration( self):
        self.acceleration = AISpaceshipAcc
                
    def startDeceleration( self):
        self.acceleration = -AISpaceshipDec

    def nearCorner( self):
        for p in TrackCorners:
            if Distance( p, self.pos.coords) <= CornerApproachMaxThreshold\
                and Distance( p, self.pos.coords) >= CornerApproachMinThreshold:
                return p
        return None

    def movingTowards( self, point, delta):
        newPos = self.computeNewPos( delta)
        if Distance( newPos, point) < Distance( self.pos.coords, point):
            return True
        else:
            return False

    def getCurrentTargetPoint( self):
        # Find closest point
        idx, p = self.trackPointsList.findClosestPoint( self.pos.coords)
        # Next point
        nextIdx, nextPoint = self.trackPointsList.nextPoint( idx)
        return nextIdx, nextPoint

    def brakeForCorner( self, delta):
        cornerPoint = self.nearCorner()
        if cornerPoint != None and self.vel.speed() > CornerApproachSpeed\
           and self.movingTowards( cornerPoint, delta):
            report4.report( 'Braking for corner %s; distance %f' %\
                (str(cornerPoint), Distance( cornerPoint, self.pos.coords)))
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
        report1.report( 'AI seeking point; idx %d %s' % ( nextPointIdx, nextPoint))
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

class TrackPointsList():
    def __init__( self):
        # Build list of points used to guide computer AI
        # First find starting point
        firstX, firstY = PlayerStartLoc
        firstY = InnerBorderOffset // 2
        trackPointsList = [ ( firstX, firstY)]
        nextX = firstX
        nextY = firstY
        direction = ( 1, 0)
        screenPerim = 2*screen.get_rect().width + 2*screen.get_rect().height
        innerBorderPerim = 2*InnerBorderRect.width + 2*InnerBorderRect.height
        perim = ( screenPerim + innerBorderPerim) // 2
        pointInc = perim //(TrackListPointCount - 1)
        self.list = [ ( firstX, firstY) ]
        for i in range( TrackListPointCount):
            newPoint = TrackPointsListMultiplier( ( nextX, nextY), direction, pointInc)
            nextX, nextY = newPoint
            if direction == ( 1, 0):
                if nextX > ScreenWidth - InnerBorderOffset // 2:
                    direction = ( 0, 1)
                    newPoint = AveragePoint( self.list[-1], newPoint)
            elif direction == ( 0, 1):
                if nextY > ScreenHeight - InnerBorderOffset // 2:
                    direction = ( -1, 0)
                    newPoint = AveragePoint( self.list[-1], newPoint)
            elif direction == ( -1, 0):
                if nextX < InnerBorderOffset // 2:
                    direction = ( 0, -1)
                    newPoint = AveragePoint( self.list[-1], newPoint)
            else:
                if nextY < InnerBorderOffset // 2:
                    direction = ( 1, 0)
                    newPoint = AveragePoint( self.list[-1], newPoint)
            nextX, nextY = newPoint
            #print( 'newPoint %s' % str(newPoint))
            self.list.append( newPoint)
            
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
        report5.report( 'idx %d; next idx %d' % ( idx, nextIdx))
        return nextIdx, self.list[nextIdx]
    
    def draw( self):
        for p in self.list:
            pygame.draw.circle( screen, pygame.Color('White'), p, 5)
    
def DrawLapCounters( playerShip, AIShip):
    text = "Player laps: %d     Computer laps: %d" % (playerShip.lapCounter, AIShip.lapCounter)
    textSurface = GameFont.render( text, False, pygame.Color('White'))
    pygame.draw.rect( screen, pygame.Color('white'), StartLine, 1)
    screen.blit( textSurface, TextRect)
    
pygame.init()
black = 0, 0, 0

trackPointsList = TrackPointsList()

spaceshipPlayer = PlayerSpaceship( "spaceship1.bmp", PlayerStartLoc, 0,
                             Velocity( (0.0, 0.0)))
spaceshipComputer = AISpaceship( "spaceship3.bmp", ComputerStartLoc, 0,
                             Velocity((15.0, 0.0)), trackPointsList)
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

    screen.fill(black)
    pygame.draw.rect( screen, pygame.Color('White'), InnerBorderRect, 1)
    spaceshipComputer.draw()
    spaceshipPlayer.draw()
    trackPointsList.draw()
    DrawLapCounters( spaceshipPlayer, spaceshipComputer)
    pygame.display.flip()

    delta = currentTime - prevTime
    spaceshipPlayer.move( delta)
    spaceshipPlayer.rotate( delta)
    spaceshipComputer.AI( delta)
    spaceshipComputer.move( delta)
    spaceshipComputer.rotate( delta)
    prevTime = currentTime
    

    
