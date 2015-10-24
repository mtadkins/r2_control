#!/usr/bin/python
#===============================================================================
# Copyright (C) 2013 Darren Poulson
#
# This file is part of R2_Control.
#
# R2_Control is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# R2_Control is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with R2_Control.  If not, see <http://www.gnu.org/licenses/>.
#===============================================================================

import os, sys
import thread
from Adafruit_PWM_Servo_Driver import PWM
import time
import csv
import collections

tick_duration = 100


class ServoControl :

  servo_list = [] # All servos, listed here.

  Servo = collections.namedtuple('Servo', 'address, channel, name, servoMin, servoMax, servoHome, servoCurrent')

  def init_config(self, address, servo_config_file):
   "Load in CSV of Servo definitions"
   ifile = open('config/%s' % servo_config_file, "rb")
   reader = csv.reader(ifile)
   for row in reader:
      servo_channel = int(row[0])
      servo_name = row[1]
      servo_servoMin = int(row[2])
      servo_servoMax = int(row[3])
      servo_home = int(row[4])
      self.servo_list.append(self.Servo(address = address, channel = servo_channel, name = servo_name, servoMin = servo_servoMin, servoMax = servo_servoMax, servoHome = servo_home, servoCurrent = servo_servoMin))
      if __debug__:
         print "Added servo: %s %s %s %s %s" % (servo_channel, servo_name, servo_servoMin, servo_servoMax, servo_home)
   ifile.close()


  def __init__(self, address, servo_config_file):
    self.i2c = PWM(int(address, 16), debug=False)
    self.i2c.setPWMFreq(60)
    self.init_config(address, servo_config_file)

  def list_servos(self, address):
    message = ""
    if __debug__:
       print "Listing servos for address: %s" % address
    for servo in self.servo_list:
       if servo.address == address:
          message += "%s,%s,%s\n" % ( servo.name, servo.channel, servo.servoCurrent )
    return message

  def close_all_servos(self, address):
    if __debug__:
       print "Closing all servos for address: %s" % address
    for servo in self.servo_list:
       if servo.address == address:
          self.i2c.setPWM(servo.channel, 0, servo.servoMin)
    return 

  def open_all_servos(self, address):
    if __debug__:
       print "Closing all servos for address: %s" % address
    for servo in self.servo_list:
       if servo.address == address:
          self.i2c.setPWM(servo.channel, 0, servo.servoMax)
    return

  # Send a command over i2c to turn a servo to a given position (percentage) over a set duration (seconds)
  def servo_command(self, servo_name, position, duration):
   current_servo = []
   try:
      position = float(position)
   except:
      print "Position not a float"
   try:
      duration = int(duration)
   except:
      print "Duration is not an int"
   for servo in self.servo_list:
      if servo.name == servo_name:
         current_servo = servo
   if position > 1 or position < 0 or not current_servo:
      print "Invalid name or position (%s, %s)" % (servo_name, position)
   else: 
      actual_position = int(((current_servo.servoMax - current_servo.servoMin)*position) + current_servo.servoMin)
      if __debug__:
         print "Duration: %s " % duration
      if duration > 0:
         ticks = (duration * 1000)/tick_duration 
         tick_position_shift = (actual_position - current_servo.servoCurrent )/float(ticks)
         tick_actual_position = current_servo.servoCurrent + tick_position_shift
         if __debug__:
            print "Ticks:%s  Current Position: %s Position shift: %s Starting Position: %s End Position %s" % (ticks, current_servo.servoCurrent, tick_position_shift, tick_actual_position, actual_position)
         for x in range(0, ticks):
            if __debug__:
               print "Tick: %s Position: %s" % (x, tick_actual_position)
            self.i2c.setPWM(current_servo.channel, 0, int(tick_actual_position)) 
            tick_actual_position += tick_position_shift
         if __debug__:
            print "Finished move: Position: %s" % tick_actual_position
      else:
         if __debug__:
            print "Setting servo %s(%s) to position = %s(%s) with duration = %s" % (servo_name, current_servo.channel, actual_position, position, duration)
         self.i2c.setPWM(current_servo.channel, 0, actual_position)
      # Save current position of servo
      for servo in self.servo_list:
        if servo.name == servo_name:
          idx = self.servo_list.index(servo)
          if __debug__:
             print "Servo move finished. Servo.name: %s ServoCurrent %s Tick %s Index %s" % (servo.name, servo.servoCurrent, actual_position, idx)
          self.servo_list[idx] = self.servo_list[idx]._replace(servoCurrent=actual_position)
          if __debug__:
             print "New current: %s" % self.servo_list[idx].servoCurrent
   time.sleep(0.5)
   self.i2c.setPWM(current_servo.channel, 4096, 0)




