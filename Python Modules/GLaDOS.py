import webiopi
import time
from threading import Timer
import sys
sys.path.insert(0, '/home/pi/glados_interface/python')
import door
import esp
import infrared
import pc_control
import heater
import subprocess 

from datetime import datetime
import json

#Pin Variables#
GPIO = webiopi.GPIO

#CONSTANTS

PC_ADDRESS = "http://192.168.1.20"
ESP8266_ADDRESS = "http://192.168.1.30"
HEATER_SOCKET = 3 

#PINS

SERVO_PIN = 27
SERVO_STATUS_PIN = 24
OUTDOOR_PIN = 25
TRANSMITTER_PIN = 1 # GPIO.1 = pin 18
DOOR_STATUS_PIN = 4
INFRARED_PIN = 22 #just for reference, we set-up the pin while installing lirc (both for transmitter and receiver)


#GLobal Instances


do = door.Doors(SERVO_PIN,OUTDOOR_PIN,DOOR_STATUS_PIN,SERVO_STATUS_PIN)
ap = esp.Api(ESP8266_ADDRESS)
inf = infrared.Infrared(INFRARED_PIN)
pc = pc_control.Pc(PC_ADDRESS)
he = heater.Heater(HEATER_SOCKET,TRANSMITTER_PIN)

#global variables for sockets

socket1_status = 0
socket2_status = 0

def setup():
	webiopi.debug("Setup")
	GPIO.setFunction(SERVO_STATUS_PIN, GPIO.IN)
	GPIO.setFunction(OUTDOOR_PIN, GPIO.OUT)
	GPIO.setFunction(SERVO_STATUS_PIN, GPIO.OUT)
	GPIO.setFunction(SERVO_PIN, GPIO.PWM)
	GPIO.setFunction(DOOR_STATUS_PIN, GPIO.IN)	

	GPIO.digitalWrite(OUTDOOR_PIN, GPIO.LOW)
	GPIO.digitalWrite(SERVO_STATUS_PIN, GPIO.LOW)
	
	do.up_door(0)
	#sysr = subprocess.Popen("sudo python","/home/pi/glados_core/interface/python/system_restart.py") # call subprocess


def destroy():
	do.up_door(0)
	he.turn_off()


 #~~~~~~~~~~~~~~~~MACROS MACROS MACROS MACROS MACROS MACROS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

@webiopi.macro
def house(enter):
	enter = int(enter)
	webiopi.debug("type of enter=%s" %type(enter))
	do.up_door(enter)
	if enter == 1:
		webiopi.debug("entering house") #i am entering the house
		do.inside = 1
		do.down_door(1)
		if pc.status == 0:
			ap.turn_on_pc
		#
		if (datetime.now().time().hour > 6):
			ap.set_status("digital","left_light",enter)
			ap.set_status("digital","right_light",enter)
		
		ap.set_status("digital","tv-hifi",enter)
		#inf.send("HIFI","KEY_POWER")
		#inf.send(HIFI,"KEY_COMPUTER")
	
	else: #enter = 0 <=> I am exiting the house
		do.inside = 0
		webiopi.debug("leaving house")
		ap.set_status("digital","left_light",enter)
		ap.set_status("digital","right_light",enter)
		ap.set_status("digital","tv-hifi",enter)
		#
		Timer(10,do.alert)
@webiopi.macro
def open_door(door):
	if door == 1:
		do.up_door(1)
	elif door == 2:
		do.down_door(1)
		do.up_door(1)

@webiopi.macro
def gday():
	if pc.status == 0:
		ap.turn_on_pc
	ap.set_status("digital","left_light",1)
	ap.set_status("digital","right_light",1)
	ap.set_status(digital,"tv-hifi",1)
	inf.send(HIFI,"KEY_POWER")
	inf.send(HIFI,"KEY_COMPUTER")
	Timer(5,pc.log_in)
	Timer(10,pc.music,["morning","chill"])
@webiopi.macro
def gnight():
	ap.set_status("digital","left_light",0)
	ap.set_status("digital","right_light",0)
	ap.set_status("digital","tv-hifi",0)

@webiopi.macro
def heater(mode,time):
	mode = int(mode)
	time = int(time)
	if mode == 1:
		webiopi.debug("heater started for : ")
		webiopi.debug(time)

		he.turn_on(time) #time in seconds
	elif mode == 0:
		webiopi.debug("heater stop")
		he.turn_off()


@webiopi.macro
def lights(number,function): #function = 1 or 0, on/off
	number = int(number)
	function = int(function)
	if number == 1:
		ret = subprocess.call(["sudo python /home/pi/glados_interface/python/rc_send.py %s %s %s" %(str(TRANSMITTER_PIN),str(function),str(1))],shell=True)
		if ret !=0:
			webiopi.debug("can't call rc_send")
		socket1_status = function
	elif number == 2:
		ret = subprocess.call(["sudo python /home/pi/glados_interface/python/rc_send.py %s %s %s" %(str(TRANSMITTER_PIN),str(function),str(2))],shell=True)
		if ret !=0:
			webiopi.debug("can't call rc_send")
		socket2_status = function
		#rc2.send(function)
	elif number == 3:
		ap.set_status("digital","left_light",function)
	elif number == 4:
		ap.set_status("digital","right_light",function)

@webiopi.macro
def status():
	a = ap.get_status("digital","left_light")
	b = ap.get_status("digital","right_light")
	el_time = he.elapsed_time()
	webiopi.debug("elapsed time:%s" % el_time)
	he_stat = he.heater_status
	c = pc.status()
	
	#socket1 socket2 left_light right_light pc inside heater elapsed_time
	
	return json.dumps([socket1_status,socket2_status,a,b,c,do.inside,he_stat,el_time], separators=(',',':'))
@webiopi.macro
def desktop_pc(function):
	function = int(function)
	if function == 0: 
		pc.turn_off()
	if function == 1:
		ap.turn_on_pc

	if function == "status": #status = 1/0
		status = pc.status()
		return  json.dumps ([status])


