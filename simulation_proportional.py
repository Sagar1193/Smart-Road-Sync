import random
import math
import time
import threading
import pygame
import sys
import os

vehicles = {
    'right': {0: [], 1: [], 2: [], 'crossed': 0},
    'down': {0: [], 1: [], 2: [], 'crossed': 0},
    'left': {0: [], 1: [], 2: [], 'crossed': 0},
    'up': {0: [], 1: [], 2: [], 'crossed': 0}
}

#to store count of total vehicles after each time unit
totalVehicles=0
totalVehiclesLane1=0
totalVehiclesLane2=0
totalVehiclesLane3=0
totalVehiclesLane4=0
totalWaitingTime=0
oneTimeUnit=60

# Default values of signal times
defaultRed = 150
defaultYellow = 5
defaultGreen = 10
defaultMinimum = 10
defaultMaximum = 60

signals = []
noOfSignals = 4
simTime = 36000       # change this to change time of simulation
timeElapsed = 0
#checked till here

currentGreen = 0   # Indicates which signal is green
nextGreen = (currentGreen + 1) % noOfSignals
currentYellow = 0   # Indicates whether yellow signal is on or off 

# Average times for vehicles to pass the intersection
carTime = 2
bikeTime = 1
rickshawTime = 2.25 
busTime = 2.5
truckTime = 2.5

# Count of cars at a traffic signal
noOfCars = 0
noOfBikes = 0
noOfBuses =0
noOfTrucks = 0
noOfRickshaws = 0
noOfLanes = 2
#2nd check done
# Red signal time at which cars will be detected at a signal
detectionTime = 5

speeds = {'car':2.25, 'bus':1.8, 'truck':1.8, 'rickshaw':2, 'bike':2.5}  # average speeds of vehicles

# Coordinates of start
x = {'right':[0,0,0], 'down':[755,727,697], 'left':[1400,1400,1400], 'up':[602,627,657]}    
y = {'right':[348,370,398], 'down':[0,0,0], 'left':[498,466,436], 'up':[800,800,800]}

vehicles = {'right': {0:[], 1:[], 2:[], 'crossed':0}, 'down': {0:[], 1:[], 2:[], 'crossed':0}, 'left': {0:[], 1:[], 2:[], 'crossed':0}, 'up': {0:[], 1:[], 2:[], 'crossed':0}}
vehicleTypes = {0:'car', 1:'bus', 2:'truck', 3:'rickshaw', 4:'bike'}
directionNumbers = {0:'right', 1:'down', 2:'left', 3:'up'}
#3rd check
# Coordinates of signal image, timer, and vehicle count
signalCoods = [(530,230),(810,230),(810,570),(530,570)]
signalTimerCoods = [(530,210),(810,210),(810,550),(530,550)]
vehicleCountCoods = [(480,210),(880,210),(880,550),(480,550)]
vehicleCountTexts = ["0", "0", "0", "0"]

#Carbon Emission Data
carbonEmissionCoods=[10,75] 
totalCarbonEmission=0
carbonValue={"car":0.8,"bus":1.2,"truck":1.3,"rickshaw":0.9,"bike":0.3} #Carbon emission of vehicles per second in micro-grams


# Coordinates of stop lines
stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}
stops = {'right': [580,580,580], 'down': [320,320,320], 'left': [810,810,810], 'up': [545,545,545]}

mid = {'right': {'x':705, 'y':445}, 'down': {'x':695, 'y':450}, 'left': {'x':695, 'y':425}, 'up': {'x':695, 'y':400}}
rotationAngle = 3

# Gap between vehicles
gap = 15    # stopping gap
gap2 = 15   # moving gap

#4th check

pygame.init()
simulation = pygame.sprite.Group()

def checkForEmergency():
    global currentGreen, signals
    for direction in vehicles:
        for lane in vehicles[direction]:
            for vehicle in vehicles[direction][lane]:
                if vehicle.is_emergency and vehicle.crossed == 0:  # If emergency vehicle is approaching and hasn't crossed
                    currentGreen = directionNumbers.index(direction)
                    signals[currentGreen].green = 30  # Set a longer green time for emergency vehicles
                    return  # Exit after handling the emergency vehicle

class TrafficSignal:
    def __init__(self, red, yellow, green, minimum, maximum):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.minimum = minimum
        self.maximum = maximum
        self.signalText = "30"
        self.totalGreenTime = 0
        
class Vehicle(pygame.sprite.Sprite):
    global totalCarbonEmission
    global totalWaitingTime
    def __init__(self, lane, vehicleClass, direction_number, direction, will_turn, is_emergency=False):
        pygame.sprite.Sprite.__init__(self)
        self.lane = lane
        self.vehicleClass = vehicleClass
        self.speed = speeds[vehicleClass]
        self.direction_number = direction_number
        self.direction = direction
        self.x = x[direction][lane]
        self.y = y[direction][lane]
        self.crossed = 0
        self.willTurn = will_turn
        self.turned = 0
        self.rotateAngle = 0
        self.waitingTime=0
        self.is_emergency = is_emergency  # Assign emergency status here
        vehicles[direction][lane].append(self)
        # self.stop = stops[direction][lane]
        self.index = len(vehicles[direction][lane]) - 1
        path = "images/" + direction + "/" + vehicleClass + ".png"
        self.originalImage = pygame.image.load(path)
        self.currentImage = pygame.image.load(path)

        self.isOn=1 #by default the engine would be on , which we would be toggling it on random basis on traffic signal

    
        if(direction=='right'):
            if(len(vehicles[direction][lane])>1 and vehicles[direction][lane][self.index-1].crossed==0):    # if more than 1 vehicle in the lane of vehicle before it has crossed stop line
                self.stop = vehicles[direction][lane][self.index-1].stop - vehicles[direction][lane][self.index-1].currentImage.get_rect().width - gap         # setting stop coordinate as: stop coordinate of next vehicle - width of next vehicle - gap
            else:
                self.stop = defaultStop[direction]
            # Set new starting and stopping coordinate
            temp = self.currentImage.get_rect().width + gap    
            x[direction][lane] -= temp
            stops[direction][lane] -= temp
        elif(direction=='left'):
            if(len(vehicles[direction][lane])>1 and vehicles[direction][lane][self.index-1].crossed==0):
                self.stop = vehicles[direction][lane][self.index-1].stop + vehicles[direction][lane][self.index-1].currentImage.get_rect().width + gap
            else:
                self.stop = defaultStop[direction]
            temp = self.currentImage.get_rect().width + gap
            x[direction][lane] += temp
            stops[direction][lane] += temp
        elif(direction=='down'):
            if(len(vehicles[direction][lane])>1 and vehicles[direction][lane][self.index-1].crossed==0):
                self.stop = vehicles[direction][lane][self.index-1].stop - vehicles[direction][lane][self.index-1].currentImage.get_rect().height - gap
            else:
                self.stop = defaultStop[direction]
            temp = self.currentImage.get_rect().height + gap
            y[direction][lane] -= temp
            stops[direction][lane] -= temp
        elif(direction=='up'):
            if(len(vehicles[direction][lane])>1 and vehicles[direction][lane][self.index-1].crossed==0):
                self.stop = vehicles[direction][lane][self.index-1].stop + vehicles[direction][lane][self.index-1].currentImage.get_rect().height + gap
            else:
                self.stop = defaultStop[direction]
            temp = self.currentImage.get_rect().height + gap
            y[direction][lane] += temp
            stops[direction][lane] += temp
        simulation.add(self)


    def render(self, screen):
        screen.blit(self.currentImage, (self.x, self.y))

    def move(self):
        global totalCarbonEmission
        global totalWaitingTime

      # If this is an emergency vehicle, it can proceed regardless of the signal
        if self.is_emergency:
            if self.direction == 'right':
                self.x += self.speed
            elif self.direction == 'down':
                self.y += self.speed
            elif self.direction == 'left':
                self.x -= self.speed
            elif self.direction == 'up':
                self.y -= self.speed
            return  # Skip the rest of the function for emergency vehicles

        # Stop non-emergency vehicles if there's an emergency vehicle in their lane
        if not self.is_emergency:
            for lane in vehicles[self.direction]:
                # Skip 'crossed' key, which is not a list
                if lane == 'crossed':
                    continue
                for vehicle in vehicles[self.direction][lane]:
                    if vehicle.is_emergency and vehicle.crossed == 0:
                        self.speed = 0  # Non-emergency vehicles stop
                        return
                    
        if(self.direction=='right'):
            if(self.crossed==0 and self.x+self.currentImage.get_rect().width>stopLines[self.direction]):   # if the image has crossed stop line now
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
            if(self.willTurn==1):
                if(self.crossed==0 or self.x+self.currentImage.get_rect().width<mid[self.direction]['x']):
                    if((self.x+self.currentImage.get_rect().width<=self.stop or (currentGreen==0 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x+self.currentImage.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - gap2) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                        self.x += self.speed
                        totalCarbonEmission+=carbonValue[self.vehicleClass]
                else:   
                    if(self.turned==0):
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x += 2
                        self.y += 1.8
                        totalCarbonEmission+=carbonValue[self.vehicleClass]
                        if(self.rotateAngle==90):
                            self.turned = 1
                    else:
                        if(self.index==0 or self.y+self.currentImage.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - gap2) or self.x+self.currentImage.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - gap2)):
                            self.y += self.speed
                            totalCarbonEmission+=carbonValue[self.vehicleClass]
            else: 
                if((self.x+self.currentImage.get_rect().width<=self.stop or self.crossed == 1 or (currentGreen==0 and currentYellow==0)) and (self.index==0 or self.x+self.currentImage.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - gap2) or (vehicles[self.direction][self.lane][self.index-1].turned==1))):                
                # (if the image has not reached its stop coordinate or has crossed stop line or has green signal) and (it is either the first vehicle in that lane or it is has enough gap to the next vehicle in that lane)
                    self.x += self.speed  # move the vehicle
                    totalCarbonEmission+=carbonValue[self.vehicleClass]
                    
                else:
                    #here the vehicle has stopped 
                    #if engine is ON then on random basis we'll turn it on or off
                    if self.isOn==1:
                        self.isOn=random.randint(0,1)
                        totalCarbonEmission+=(carbonValue[self.vehicleClass]*self.isOn) #if isOn is 0 then no carb emission , else carbon emission



        elif(self.direction=='down'):
            if(self.crossed==0 and self.y+self.currentImage.get_rect().height>stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
            if(self.willTurn==1):
                if(self.crossed==0 or self.y+self.currentImage.get_rect().height<mid[self.direction]['y']):
                    if((self.y+self.currentImage.get_rect().height<=self.stop or (currentGreen==1 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.y+self.currentImage.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - gap2) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                        self.y += self.speed
                        totalCarbonEmission+=carbonValue[self.vehicleClass]
                else:   
                    if(self.turned==0):
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x -= 2.5
                        self.y += 2
                        totalCarbonEmission+=carbonValue[self.vehicleClass]
                        if(self.rotateAngle==90):
                            self.turned = 1
                    else:
                        if(self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width + gap2) or self.y<(vehicles[self.direction][self.lane][self.index-1].y - gap2)):
                            self.x -= self.speed
                            totalCarbonEmission+=carbonValue[self.vehicleClass]
            else: 
                if((self.y+self.currentImage.get_rect().height<=self.stop or self.crossed == 1 or (currentGreen==1 and currentYellow==0)) and (self.index==0 or self.y+self.currentImage.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - gap2) or (vehicles[self.direction][self.lane][self.index-1].turned==1))):                
                    self.y += self.speed
                    totalCarbonEmission+=carbonValue[self.vehicleClass]
                else:
                    #here the vehicle has stopped 
                    #if engine is ON then on random basis we'll turn it on or off
                    if self.isOn==1:
                        self.isOn=random.randint(0,1)
                        totalCarbonEmission+=(carbonValue[self.vehicleClass]*self.isOn) #if isOn is 0 then no carb emission , else carbon emission
            
        elif(self.direction=='left'):
            if(self.crossed==0 and self.x<stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                totalCarbonEmission+=carbonValue[self.vehicleClass]
            if(self.willTurn==1):
                if(self.crossed==0 or self.x>mid[self.direction]['x']):
                    if((self.x>=self.stop or (currentGreen==2 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width + gap2) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                        self.x -= self.speed
                        totalCarbonEmission+=carbonValue[self.vehicleClass]
                else: 
                    if(self.turned==0):
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x -= 1.8
                        self.y -= 2.5
                        totalCarbonEmission+=carbonValue[self.vehicleClass]
                        if(self.rotateAngle==90):
                            self.turned = 1
                    else:
                        if(self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().height +  gap2) or self.x>(vehicles[self.direction][self.lane][self.index-1].x + gap2)):
                            self.y -= self.speed
                            totalCarbonEmission+=carbonValue[self.vehicleClass]
            else: 
                if((self.x>=self.stop or self.crossed == 1 or (currentGreen==2 and currentYellow==0)) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width + gap2) or (vehicles[self.direction][self.lane][self.index-1].turned==1))):                
                # (if the image has not reached its stop coordinate or has crossed stop line or has green signal) and (it is either the first vehicle in that lane or it is has enough gap to the next vehicle in that lane)
                    self.x -= self.speed  # move the vehicle    
                    totalCarbonEmission+=carbonValue[self.vehicleClass]
                else:
                    #here the vehicle has stopped 
                    #if engine is ON then on random basis we'll turn it on or off
                    if self.isOn==1:
                        self.isOn=random.randint(0,1)
                        totalCarbonEmission+=(carbonValue[self.vehicleClass]*self.isOn) #if isOn is 0 then no carb emission , else carbon emission
        elif(self.direction=='up'):
            if(self.crossed==0 and self.y<stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                totalCarbonEmission+=carbonValue[self.vehicleClass]
            if(self.willTurn==1):
                if(self.crossed==0 or self.y>mid[self.direction]['y']):
                    if((self.y>=self.stop or (currentGreen==3 and currentYellow==0) or self.crossed == 1) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().height +  gap2) or vehicles[self.direction][self.lane][self.index-1].turned==1)):
                        self.y -= self.speed
                        totalCarbonEmission+=carbonValue[self.vehicleClass]
                else:   
                    if(self.turned==0):
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x += 1
                        self.y -= 1
                        totalCarbonEmission+=carbonValue[self.vehicleClass]
                        if(self.rotateAngle==90):
                            self.turned = 1
                    else:
                        if(self.index==0 or self.x<(vehicles[self.direction][self.lane][self.index-1].x - vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width - gap2) or self.y>(vehicles[self.direction][self.lane][self.index-1].y + gap2)):
                            self.x += self.speed
                            totalCarbonEmission+=carbonValue[self.vehicleClass]
            else: 
                if((self.y>=self.stop or self.crossed == 1 or (currentGreen==3 and currentYellow==0)) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().height + gap2) or (vehicles[self.direction][self.lane][self.index-1].turned==1))):                
                    self.y -= self.speed
                    totalCarbonEmission+=carbonValue[self.vehicleClass]
                else:
                    #here the vehicle has stopped 
                    #if engine is ON then on random basis we'll turn it on or off
                    if self.isOn==1:
                        self.isOn=random.randint(0,1)
                        totalCarbonEmission+=(carbonValue[self.vehicleClass]*self.isOn) #if isOn is 0 then no carb emission , else carbon emission

# Initialization of signals with default values
def initialize():
    ts1 = TrafficSignal(0, defaultYellow, defaultGreen, defaultMinimum, defaultMaximum)
    signals.append(ts1)
    ts2 = TrafficSignal(ts1.red+ts1.yellow+ts1.green, defaultYellow, defaultGreen, defaultMinimum, defaultMaximum)
    signals.append(ts2)
    ts3 = TrafficSignal(defaultRed, defaultYellow, defaultGreen, defaultMinimum, defaultMaximum)
    signals.append(ts3)
    ts4 = TrafficSignal(defaultRed, defaultYellow, defaultGreen, defaultMinimum, defaultMaximum)
    signals.append(ts4)
    repeat()

# Set time according to formula
def setTime():
    global totalCarbonEmission,totalWaitingTime , vehicles
    global noOfCars, noOfBikes, noOfBuses, noOfTrucks, noOfRickshaws, noOfLanes
    global carTime, busTime, truckTime, rickshawTime, bikeTime
    global totalVehicles,totalVehiclesLane1,totalVehiclesLane2,totalVehiclesLane3,totalVehiclesLane4,oneTimeUnit
    # os.system("say detecting vehicles, "+directionNumbers[(currentGreen+1)%noOfSignals])
    # if totalCarbonEmission<1000:
    #     os.system("say Carbon Emission , "+str(round(totalCarbonEmission,2))+" micro gram")
    # elif totalCarbonEmission >=1000 and totalCarbonEmission<1000000:
    #     os.system("say Carbon Emission , "+str(round(totalCarbonEmission/1000,2))+" milli gram")
    # elif totalCarbonEmission>=1000000 and totalCarbonEmission<1000000000:
    #     os.system("say Carbon Emission , "+str(round(totalCarbonEmission/1000000,2))+" gram")
    # else:
    #     os.system("say Total Carbon Emission =, "+str(round(totalCarbonEmission/1000000000,2))+" Kg")
    noOfCars, noOfBuses, noOfTrucks, noOfRickshaws, noOfBikes = 0,0,0,0,0
    for j in range(len(vehicles[directionNumbers[nextGreen]][0])):
        vehicle = vehicles[directionNumbers[nextGreen]][0][j]
        if(vehicle.crossed==0):
            vclass = vehicle.vehicleClass
            # print(vclass)
            noOfBikes += 1
    for i in range(1,3):
        for j in range(len(vehicles[directionNumbers[nextGreen]][i])):
            vehicle = vehicles[directionNumbers[nextGreen]][i][j]
            if(vehicle.crossed==0):
                vclass = vehicle.vehicleClass
                # print(vclass)
                if(vclass=='car'):
                    noOfCars += 1
                elif(vclass=='bus'):
                    noOfBuses += 1
                elif(vclass=='truck'):
                    noOfTrucks += 1
                elif(vclass=='rickshaw'):
                    noOfRickshaws += 1
    # print(noOfCars)
    # greenTime = math.ceil(((noOfCars*carTime) + (noOfRickshaws*rickshawTime) + (noOfBuses*busTime) + (noOfTrucks*truckTime)+ (noOfBikes*bikeTime))/(noOfLanes+1))
    
    greenTime = 0
    
    if totalVehicles!=0:
        if directionNumbers[(currentGreen+1)%noOfSignals]=="right":
            greenTime=int((totalVehiclesLane1/totalVehicles)*oneTimeUnit)
        elif directionNumbers[(currentGreen+1)%noOfSignals]=="down":
            greenTime=int((totalVehiclesLane2/totalVehicles)*oneTimeUnit)
        elif directionNumbers[(currentGreen+1)%noOfSignals]=="left":
            greenTime=int((totalVehiclesLane3/totalVehicles)*oneTimeUnit)
        elif directionNumbers[(currentGreen+1)%noOfSignals]=="up":
            greenTime=int((totalVehiclesLane4/totalVehicles)*oneTimeUnit)
    
    print('Green Time: ',greenTime)
    if greenTime==0:
        greenTime=10
    # greenTime = random.randint(15,50)

    #After each unit of time We will reach to right lane , so storing data at that point only
    if(directionNumbers[(currentGreen+1)%noOfSignals]=="right"):
        print("Debug : Total waiting Time : ",totalWaitingTime," Total Vehicles : ",totalVehicles," Avg : ",totalWaitingTime/totalVehicles)
        if(totalVehicles==0):#as it would return infinity
            avg_waiting=0
        else:
            avg_waiting=math.ceil(totalWaitingTime/totalVehicles)
        file=open('data.csv','a') #This is the file in which I will be storing all details
        file.write(str(totalVehiclesLane1)+','+str(totalVehiclesLane2)+','+str(totalVehiclesLane3)+','+str(totalVehiclesLane4)+','+str(totalVehicles)+','+str(avg_waiting)+'\n')
        file.close()
    
    #storing count of total vehicles
    totalVehicles+=noOfCars+noOfRickshaws+noOfBuses+noOfTrucks+noOfBikes

    direction=directionNumbers[(currentGreen+1)%noOfSignals]
    directions=["right","down","up","left"]
    for dir in directions:
        if dir==direction:
            continue
        else:
            for i in range(0,3):
                for vehicle in vehicles[dir][i]:
                    vehicle.waitingTime+=1
                    totalWaitingTime+=1

    #storing count of vehicles from each lane
    # print("ANAND Direction Number : ",directionNumbers[(currentGreen+1)%noOfSignals])
    if(directionNumbers[(currentGreen+1)%noOfSignals]=="right"):
        totalVehiclesLane1+=noOfCars+noOfRickshaws+noOfBuses+noOfTrucks+noOfBikes
    elif(directionNumbers[(currentGreen+1)%noOfSignals]=="down"):
        totalVehiclesLane2+=noOfCars+noOfRickshaws+noOfBuses+noOfTrucks+noOfBikes
    elif(directionNumbers[(currentGreen+1)%noOfSignals]=="left"):
        totalVehiclesLane3+=noOfCars+noOfRickshaws+noOfBuses+noOfTrucks+noOfBikes
    elif(directionNumbers[(currentGreen+1)%noOfSignals]=="up"):
        totalVehiclesLane4+=noOfCars+noOfRickshaws+noOfBuses+noOfTrucks+noOfBikes
    
    signals[(currentGreen+1)%(noOfSignals)].green = greenTime

   
def repeat():
    global currentGreen, currentYellow, nextGreen
    while(signals[currentGreen].green>0):   # while the timer of current green signal is not zero
        printStatus()
        updateValues()
        if(signals[(currentGreen+1)%(noOfSignals)].red==detectionTime):    # set time of next green signal 
            thread = threading.Thread(name="detection",target=setTime, args=())
            thread.daemon = True
            thread.start()
            # setTime()
        time.sleep(1)
        checkForEmergency()  # Check if there's an emergency vehicle approaching
    currentYellow = 1   # set yellow signal on
    vehicleCountTexts[currentGreen] = "0"
    # reset stop coordinates of lanes and vehicles 
    for i in range(0,3):
        stops[directionNumbers[currentGreen]][i] = defaultStop[directionNumbers[currentGreen]]
        for vehicle in vehicles[directionNumbers[currentGreen]][i]:
            vehicle.stop = defaultStop[directionNumbers[currentGreen]]
    while(signals[currentGreen].yellow>0):  # while the timer of current yellow signal is not zero
        printStatus()
        updateValues()
        time.sleep(1)
    currentYellow = 0   # set yellow signal off
    
    # reset all signal times of current signal to default times
    signals[currentGreen].green = defaultGreen
    signals[currentGreen].yellow = defaultYellow
    signals[currentGreen].red = defaultRed
       
    currentGreen = nextGreen # set next signal as green signal
    nextGreen = (currentGreen+1)%noOfSignals    # set next green signal
    signals[nextGreen].red = signals[currentGreen].yellow+signals[currentGreen].green    # set the red time of next to next signal as (yellow time + green time) of next signal
    repeat()     

# Print the signal timers on cmd
def printStatus():                                                                                           
	for i in range(0, noOfSignals):
		if(i==currentGreen):
			if(currentYellow==0):
				print(" GREEN TS",i+1,"-> r:",signals[i].red," y:",signals[i].yellow," g:",signals[i].green)
			else:
				print("YELLOW TS",i+1,"-> r:",signals[i].red," y:",signals[i].yellow," g:",signals[i].green)
		else:
			print("   RED TS",i+1,"-> r:",signals[i].red," y:",signals[i].yellow," g:",signals[i].green)
	print()

# Update values of the signal timers after every second
def updateValues():
    for i in range(0, noOfSignals):
        if(i==currentGreen):
            if(currentYellow==0):
                signals[i].green-=1
                signals[i].totalGreenTime+=1
            else:
                signals[i].yellow-=1
        else:
            signals[i].red-=1

# Generating vehicles in the simulation

def generateVehicles():
    # Define the probability for a vehicle to be an emergency vehicle (e.g., 10%)
    emergency_probability = 0.1

    while True:
        vehicle_type = random.randint(0, 4)
        if vehicle_type == 4:
            lane_number = 0
        else:
            lane_number = random.randint(0, 1) + 1
        will_turn = 0
        if lane_number == 2:
            temp = random.randint(0, 4)
            if temp <= 2:
                will_turn = 1
            elif temp > 2:
                will_turn = 0
        temp = random.randint(0, 999)
        direction_number = 0
        a = [400, 800, 900, 1000]
        if temp < a[0]:
            direction_number = 0
        elif temp < a[1]:
            direction_number = 1
        elif temp < a[2]:
            direction_number = 2
        elif temp < a[3]:
            direction_number = 3

        # Decide if this vehicle is an emergency vehicle based on the probability
        is_emergency = random.random() < emergency_probability

        # Create the vehicle with the determined emergency status
        Vehicle(lane_number, vehicleTypes[vehicle_type], direction_number, directionNumbers[direction_number], will_turn, is_emergency=is_emergency)
        
        # Log to the console if an emergency vehicle is created
        if is_emergency:
            print(f"Emergency vehicle created in direction: {directionNumbers[direction_number]}, lane: {lane_number}")

        # Wait before generating the next vehicle
        time.sleep(0.75)

# def generateVehicles():
#     while(True):
#         vehicle_type = random.randint(0,4)
#         if(vehicle_type==4):
#             lane_number = 0
#         else:
#             lane_number = random.randint(0,1) + 1
#         will_turn = 0
#         if(lane_number==2):
#             temp = random.randint(0,4)
#             if(temp<=2):
#                 will_turn = 1
#             elif(temp>2):
#                 will_turn = 0
#         temp = random.randint(0,999)
#         direction_number = 0
#         a = [400,800,900,1000]
#         if(temp<a[0]):
#             direction_number = 0
#         elif(temp<a[1]):
#             direction_number = 1
#         elif(temp<a[2]):
#             direction_number = 2
#         elif(temp<a[3]):
#             direction_number = 3
#         # Randomly decide if a vehicle is an emergency vehicle (adjust the probability as needed)
#         is_emergency = random.choice([True, False])  # Example: 50% chance to be emergency
#         Vehicle(lane_number, vehicleTypes[vehicle_type], direction_number, directionNumbers[direction_number], will_turn)
#         time.sleep(0.75)

def simulationTime():
    global timeElapsed, simTime
    while(True):
        timeElapsed += 1
        time.sleep(1)
        if(timeElapsed==simTime):
            totalVehicles = 0
            print('Lane-wise Vehicle Counts')
            for i in range(noOfSignals):
                print('Lane',i+1,':',vehicles[directionNumbers[i]]['crossed'])
                totalVehicles += vehicles[directionNumbers[i]]['crossed']
            print('Total vehicles passed: ',totalVehicles)
            print('Total time passed: ',timeElapsed)
            print('No. of vehicles passed per unit time: ',(float(totalVehicles)/float(timeElapsed)))
            os._exit(1)
    

class Main:
    global totalCarbonEmission
    thread4 = threading.Thread(name="simulationTime",target=simulationTime, args=()) 
    thread4.daemon = True
    thread4.start()

    thread2 = threading.Thread(name="initialization",target=initialize, args=())    # initialization
    thread2.daemon = True
    thread2.start()

    # Colours 
    black = (0, 0, 0)
    white = (255, 255, 255)

    # Screensize 
    screenWidth = 1400
    screenHeight = 800
    screenSize = (screenWidth, screenHeight)

    # Setting background image i.e. image of intersection
    background = pygame.image.load('images/mod_int.png')

    screen = pygame.display.set_mode(screenSize)
    pygame.display.set_caption("SIMULATION")

    # Loading signal images and font
    redSignal = pygame.image.load('images/signals/red.png')
    yellowSignal = pygame.image.load('images/signals/yellow.png')
    greenSignal = pygame.image.load('images/signals/green.png')
    font = pygame.font.Font(None, 30)

    thread3 = threading.Thread(name="generateVehicles",target=generateVehicles, args=())    # Generating vehicles
    thread3.daemon = True
    thread3.start()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        screen.blit(background,(0,0))   # display background in simulation
        for i in range(0,noOfSignals):  # display signal and set timer according to current status: green, yello, or red
            if(i==currentGreen):
                if(currentYellow==1):
                    if(signals[i].yellow==0):
                        signals[i].signalText = "STOP"
                    else:
                        signals[i].signalText = signals[i].yellow
                    screen.blit(yellowSignal, signalCoods[i])
                else:
                    if(signals[i].green==0):
                        signals[i].signalText = "SLOW"
                    else:
                        signals[i].signalText = signals[i].green
                    screen.blit(greenSignal, signalCoods[i])
            else:
                if(signals[i].red<=10):
                    if(signals[i].red==0):
                        signals[i].signalText = "GO"
                    else:
                        signals[i].signalText = signals[i].red
                else:
                    signals[i].signalText = "---"
                screen.blit(redSignal, signalCoods[i])
        signalTexts = ["","","",""]

        # display signal timer and vehicle count
        for i in range(0,noOfSignals):  
            signalTexts[i] = font.render(str(signals[i].signalText), True, white, black)
            screen.blit(signalTexts[i],signalTimerCoods[i]) 
            displayText = vehicles[directionNumbers[i]]['crossed']
            vehicleCountTexts[i] = font.render(str(displayText), True, black, white)
            screen.blit(vehicleCountTexts[i],vehicleCountCoods[i])

        timeElapsedText = font.render(("Time Elapsed: "+str(timeElapsed)), True, black, white)
        screen.blit(timeElapsedText,(1100,50))

        if totalCarbonEmission<1000:
            carbonText=font.render(("Carbon Emission : "+str(round(totalCarbonEmission,2))+"  µg"), True, black, white)
        elif totalCarbonEmission>=1000 and totalCarbonEmission<1000000:
            carbonText=font.render(("Carbon Emission : "+str(round(totalCarbonEmission/1000,2))+"  mg"), True, black, white)
        elif totalCarbonEmission>=1000000 and totalCarbonEmission<1000000000:
            carbonText=font.render(("Carbon Emission : "+str(round(totalCarbonEmission/1000000,2))+"  g"), True, black, white)
        else:
            carbonText=font.render(("Carbon Emission : "+str(round(totalCarbonEmission/1000000000,2))+"  Kg"), True, black, white)
        screen.blit(carbonText,(10,75))


        # display the vehicles
        for vehicle in simulation:  
            screen.blit(vehicle.currentImage, [vehicle.x, vehicle.y])
            # vehicle.render(screen)
            vehicle.move()
        pygame.display.update()


Main()

   
