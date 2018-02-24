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
PlayerStartLoc = ( 100, 100)
ComputerStartLoc = PlayerStartLoc
TrackCorners = (( InnerBorderOffset // 2, InnerBorderOffset // 2),
    ( ScreenWidth - InnerBorderOffset // 2, InnerBorderOffset // 2),
    ( ScreenWidth - InnerBorderOffset // 2, ScreenHeight - InnerBorderOffset // 2),
    ( InnerBorderOffset // 2, ScreenHeight - InnerBorderOffset // 2))

# Create screen
screen = pygame.display.set_mode( DisplaySize)

# Critical spaceship params
RotationRate = 2
PlayerSpaceshipAcc = 70.0
PlayerSpaceshipDec = 70.0
AISpaceshipAcc = 100.0
AISpaceshipDec = 100.0
AITargetSpeed = 160
MaxSpeed = 200

# Misc
BounceVelLoss = .5
RotationThreshold = math.pi*2 * 5/360
AITargetSpeedThreshold = 5
TrackListPointCount = 9

# AI tuning
CornerApproachThreshold = 200
CornerApproachSpeed = MaxSpeed*.3

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

def Distance( p1, p2):
    return math.sqrt( (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

def DotProd( v1, v2):
    return v1[0]*v2[0]+v1[1]*v2[1]

def SubtractVector( v1, v2):
    return ( v1[0] - v2[0], v1[1] - v2[1])
        
def MultScalerByVector( scaler, v):
    return ( scaler * v[0], scaler * v[1])

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
        self.updateVel( delta)
        self.updatePos( delta)

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
                  trackPointsList, trackPointsCorners):
        Spaceship.__init__( self, bitmapFile, initPos, angle, vel)
        self.lastPointIdx = -1
        self.trackPointsList = trackPointsList
        self.trackPointsCorners = trackPointsCorners
    def startAcceleration( self):
        self.acceleration = AISpaceshipAcc
                
    def startDeceleration( self):
        self.acceleration = -AISpaceshipDec

    def nearCorner( self):
        for p in self.trackPointsCorners:
            if Distance( p, self.pos.coords) < CornerApproachThreshold:
                return p
        return None

    def movingTowards( self, point, delta):
        newPos = self.computeNewPos( delta)
        if Distance( newPos, point) <\
            Distance( self.pos.coords, point):
            return True
        else:
            return False

    def getCurrentTargetPoint( self):
        # Find closest point
        minDistance = 1000000
        minDistancePointIdx = 0
        for idx, p in enumerate( self.trackPointsList):
            tempDistance = Distance( self.pos.coords, p)
            if tempDistance < minDistance:
                minDistance = tempDistance
                minDistancePointIdx = idx
        # Next point
        tempIdx = minDistancePointIdx
        tempIdx += 1
        tempIdx %= len( self.trackPointsList)
        nextPoint = self.trackPointsList[tempIdx]

        return tempIdx, nextPoint

    def brakeForCorner( self, delta):
        return False
        cornerPoint = self.nearCorner()
        if cornerPoint != None and self.vel.speed() > CornerApproachSpeed\
           and self.movingTowards( cornerPoint, delta):
            report4.report( 'Braking for corner %s' % str(cornerPoint))
            self.startDeceleration()
            return True
        else:
            return False

    def desiredAngle1( self, nextPoint):
        nextX, nextY = nextPoint
        return math.atan2( -(nextY - self.pos.y), nextX - self.pos.x)
    
    def desiredVelocity( self, next_point, position, velocity):
        next_dir = SubtractVector( next_point, position)
        temp = math.sqrt( DotProd(next_dir,next_dir))
        next_unit = MultScalerByVector( 1 / temp, next_dir)
        next_speed = DotProd(next_unit, velocity)
        tempVector = MultScalerByVector( next_speed, next_unit)
        perp_velocity = SubtractVector( velocity, tempVector)
        return SubtractVector( tempVector, perp_velocity)
        
    def desiredAngle2( self, nextPoint):
        desired_vel = self.desiredVelocity( nextPoint, self.pos.coords,
            self.vel.getTuple())
        return math.atan2( -desired_vel[1], desired_vel[0])

    def AI( self, delta):
        nextPointIdx, nextPoint = self.getCurrentTargetPoint()
        if nextPointIdx < self.lastPointIdx and\
           self.lastPointIdx - nextPointIdx < 2:
            #report6.report( 'Dont move backwards; last %d next %d' % ( self.lastPointIdx, nextPointIdx))
            nextPointIdx = self.lastPointIdx
            nextPoint = self.trackPointsList[nextPointIdx]
        else:
            self.lastPointIdx = nextPointIdx
        
        # next point angle
        newAngle = self.desiredAngle2( nextPoint)
        
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
            
                    
def TrackPointsListMultiplier( v1, v2, x):
    return [ v1[i] + v2[i] * x for i in range(2)]

def AveragePoint( p1, p2):
    return ( (p1[0] + p2[0]) // 2, ( p1[1] + p2[1]) // 2)

def CreateTrackPointsList():
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
    trackPointsList = [ ( firstX, firstY) ]
    for i in range( TrackListPointCount):
        newPoint = TrackPointsListMultiplier( ( nextX, nextY), direction, pointInc)
        nextX, nextY = newPoint
        if direction == ( 1, 0):
            if nextX > ScreenWidth - InnerBorderOffset // 2:
                direction = ( 0, 1)
                newPoint = AveragePoint( trackPointsList[-1], newPoint)
        elif direction == ( 0, 1):
            if nextY > ScreenHeight - InnerBorderOffset // 2:
                direction = ( -1, 0)
                newPoint = AveragePoint( trackPointsList[-1], newPoint)
        elif direction == ( -1, 0):
            if nextX < InnerBorderOffset // 2:
                direction = ( 0, -1)
                newPoint = AveragePoint( trackPointsList[-1], newPoint)
        else:
            if nextY < InnerBorderOffset // 2:
                direction = ( 1, 0)
                newPoint = AveragePoint( trackPointsList[-1], newPoint)
        nextX, nextY = newPoint
        trackPointsList.append( newPoint)
    return trackPointsList

def CreateTracksPointListCorners( trackPointsList):
    trackPointsCorners = []
    for c in TrackCorners:
        minDistance = 1000000
        minIdx = -1
        for idx, p in enumerate( trackPointsList):
            distance = Distance( c, p)
            if distance < minDistance:
                minIdx = idx
                minDistance = distance
        trackPointsCorners.append( trackPointsList[ minIdx])
    #print( 'trackPointsListCorners %s' % trackPointsCorners)
    return trackPointsCorners

#def CreateTrackPointsList2():
#    return (( InnerBorderOffset // 2, InnerBorderOffset // 2),
#              (ScreenWidth - InnerBorderOffset // 2, InnerBorderOffset // 2),
#              (ScreenWidth - InnerBorderOffset // 2, ScreenHeight - InnerBorderOffset // 2),
#              (InnerBorderOffset // 2, ScreenHeight - InnerBorderOffset // 2))
    
pygame.init()
black = 0, 0, 0

trackPointsList = CreateTrackPointsList()
trackPointsCorners = CreateTracksPointListCorners( trackPointsList)

spaceshipPlayer = PlayerSpaceship( "spaceship1.bmp", PlayerStartLoc, 0,
                             Velocity( (0.0, 0.0)))
spaceshipComputer = AISpaceship( "spaceship3.bmp", ComputerStartLoc, 0,
                             Velocity((15.0, 0.0)), trackPointsList, trackPointsCorners)
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
    spaceshipPlayer.draw()
    spaceshipComputer.draw()
    for p in trackPointsList:
        pygame.draw.circle( screen, pygame.Color('White'), p, 5)
    pygame.display.flip()

    delta = currentTime - prevTime
    spaceshipPlayer.move( delta)
    spaceshipPlayer.rotate( delta)
    spaceshipComputer.AI( delta)
    spaceshipComputer.move( delta)
    spaceshipComputer.rotate( delta)
    prevTime = currentTime
    

    
