###############################################################################
##
##  Copyright 2012 Tavendo GmbH
##
##  Licensed under the Apache License, Version 2.0 (the "License");
##  you may not use this file except in compliance with the License.
##  You may obtain a copy of the License at
##
##      http://www.apache.org/licenses/LICENSE-2.0
##
##  Unless required by applicable law or agreed to in writing, software
##  distributed under the License is distributed on an "AS IS" BASIS,
##  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
##  See the License for the specific language governing permissions and
##  limitations under the License.
##
###############################################################################


import sys, time, re

if sys.platform == 'win32':
   ## on windows, we need to use the following reactor for serial support
   ## http://twistedmatrix.com/trac/ticket/3802
   ##
   from twisted.internet import win32eventreactor
   win32eventreactor.install()

from twisted.internet import reactor
print "Using Twisted reactor", reactor.__class__
print

from twisted.python import usage, log
from twisted.protocols.basic import LineReceiver
from twisted.internet.serialport import SerialPort
from twisted.web.server import Site
from twisted.web.static import File

from autobahn.websocket import listenWS
from autobahn.wamp import WampServerFactory, WampServerProtocol, exportRpc


class Serial2WsOptions(usage.Options):
   optParameters = [
      ['baudrate', 'b', 19200, 'Serial baudrate'],
      ['port', 'p', '/dev/ttyUSB0', 'Serial port to use'],
      ['webport', 'w', 8080, 'Web port to use for embedded Web server'],
      ['wsurl', 's', "ws://localhost:9000", 'WebSocket port to use for embedded WebSocket server']
   ]


## MCU protocol
## knows nothing about websockets
##
class McuProtocol(LineReceiver):
   delimiter = '$'
   ## need a reference to our WS-MCU gateway factory to dispatch PubSub events
   ##
   def __init__(self, wsMcuFactory):
      self.wsMcuFactory = wsMcuFactory

   ## this method is exported as RPC and can be called by connected clients
   ##
   @exportRpc("read-tx")
   def readTX(self):
         print "DEBUG Read from transmitter"
         self.transport.write('\x00\x46\x4d\x01\x20\x02')

   @exportRpc("control-led")
   def controlLed(self, status):
      if status:
         print "turn on LED"
         self.transport.write('1')
      else:
         print "turn off LED"
         self.transport.write('0')


   def connectionMade(self):
      log.msg('Serial port connected.')

   def lineReceived(self, line):
      print "DEBUG line", line
      try:
            AlarmCode = int(re.search('AlarmCode=(.+?),', line).group(1))
            Pfwd = float(re.search('Pfwd=(.+?)W,', line).group(1))
            ref = float(re.search('ref=(.+?)W,', line).group(1))
            Texc = float(re.search('Texc=(.+?)C,', line).group(1))
            Tamp = float(re.search('Tamp=(.+?)C,', line).group(1))
            Uexc = float(re.search('Uexc=(.+?)V,', line).group(1))
            Uamp = float(re.search('Uamp=(.+?)V,', line).group(1))
            Audio = ord(re.search('Audio=(.+?),', line).group(1))
            Iexc = float(re.search('Iexc=(.+?)A,', line).group(1))
            Iamp = float(re.search('Iamp=(.+?)A,', line).group(1))
            Uptime = re.search('Uptime=(.+?),', line).group(1)
            Freq = float(re.search('Freq=(.+?)MHz,', line).group(1))
            Firmware = re.search('Firmware=(.+?),', line).group(1)
            PowerLimit = re.search('PowerLimit=(.+?),', line).group(1)
            evt = {'AlarmCode': AlarmCode, 'Pfwd': Pfwd, 'ref': ref,\
                 'Texc': Texc, 'Tamp': Tamp, 'Uexc': Uexc, 'Uamp': Uamp,\
                 'Audio': Audio, 'Iexc': Iexc, 'Iamp': Iamp, 'Uptime': Uptime,\
                 'Freq': Freq, 'Firmware': Firmware, 'PowerLimit': PowerLimit}
            self.wsMcuFactory.dispatch("http://example.com/mcu#tx-status", evt)
            print evt
      except AttributeError:
            print "Could not parse string."

## WS-MCU protocol
## knows about websockets
## registers for RPC and PubSub
##
class WsMcuProtocol(WampServerProtocol):

   def onSessionOpen(self):
      ## register topic prefix under which we will publish MCU measurements
      ##
      self.registerForPubSub("http://example.com/mcu#", True)

      ## register methods for RPC
      ##
      self.registerForRpc(self.factory.mcuProtocol, "http://example.com/mcu-control#")


## WS-MCU factory
## knows about websockets
## 
class WsMcuFactory(WampServerFactory):

   protocol = WsMcuProtocol

   def __init__(self, url):
      WampServerFactory.__init__(self, url)
      self.mcuProtocol = McuProtocol(self)


if __name__ == '__main__':

   ## parse options
   ##
   o = Serial2WsOptions()
   try:
      o.parseOptions()
   except usage.UsageError, errortext:
      print '%s %s' % (sys.argv[0], errortext)
      print 'Try %s --help for usage details' % sys.argv[0]
      sys.exit(1)

   baudrate = int(o.opts['baudrate'])
   port = o.opts['port']
   webport = int(o.opts['webport'])
   wsurl = o.opts['wsurl']

   ## start Twisted log system
   ##
   log.startLogging(sys.stdout)

   ## create Serial2Ws gateway factory
   ##
   wsMcuFactory = WsMcuFactory(wsurl)
   listenWS(wsMcuFactory)               ## calls reactor internally

   ## create serial port and serial port protocol
   ##
   log.msg('About to open serial port %s [%d baud] ..' % (port, baudrate))
   serialPort = SerialPort(wsMcuFactory.mcuProtocol, port, reactor, baudrate = baudrate)

   ## create embedded web server for static files
   ##
   webdir = File(".")
   web = Site(webdir)
   reactor.listenTCP(webport, web)

   ## start Twisted reactor ..
   ##
   reactor.run()
