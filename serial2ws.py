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


import sys
import re

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
      ['wsurl', 's', "ws://localhost:9000",\
                    'WebSocket port to use for embedded WebSocket server']
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
#        self.transport.write('\x00\x46\x4d\x01\x20\x02')
        self.transport.write('\x00' + "FM" + '\x01' + '\x20' + '\x02')

    @exportRpc("set-power")
    def setPower(self, power):
        if 0 < float(power) < 100.0:
            print "DEBUG", power
#           self.transport.write('\x00' + "FO" + '\x01' +
#                       str(int(round(int(power) / 100.0 * 34) + 4)) + '\x02')

    @exportRpc("set-freq")
    def setFrequency(self, freq):
        if 87.5 < float(freq) < 108.0:
            print "DEBUG", freq
#           self.transport.write('\x00' + "FO" + '\x01' + freq + '\x02')

    @exportRpc("set-channels")
    def setChannels(self, channels):
        if 0 <= int(channels) <= 1:
            print "DEBUG", channels
#           self.transport.write('\x00' + "FS" + '\x01' + channels + '\x02')

    @exportRpc("set-DSP")
    def setDSP(self, attack, decay, interval, threshold, compression):
        print "DEBUG", attack, decay, interval, threshold, compression

    @exportRpc("set-alarms")
    def setAlarms(self, swr_alarm, current_alarm, temp_alarm, Uamp_alarm):
        print "DEBUG", swr_alarm, current_alarm, temp_alarm, Uamp_alarm

    @exportRpc("set-bass-treble")
    def setBassTreble(self, treble, bass):
        print "DEBUG", treble, bass

    @exportRpc("set-audio")
    def setAudio(self, left_gain, right_gain):
        print "DEBUG", left_gain, right_gain

    def setTreble(self, treble):
        self.transport.write('\x00' + "FDT" + '\x01' +
                                            str(int(treble) + 4) + '\x02')

    def setBass(self, bass):
        self.transport.write('\x00' + "FDB" + '\x01' +
                                            str(int(bass) + 4) + '\x02')

    def setAttack(self, attack):
        self.transport.write('\x00' + "FDA" + '\x01' +
                                            str(int(attack) + 4) + '\x02')

    def setDecay(self, decay):
        self.transport.write('\x00' + "FDD" + '\x01' +
                                            str(int(decay) + 4) + '\x02')

    def setThreshold(self, threshold):
        self.transport.write('\x00' + "FDH" + '\x01' +
                                            str(int(threshold) + 4) + '\x02')

    def setIntegration(self, integration):
        self.transport.write('\x00' + "FDI" + '\x01' +
                                            str(int(integration) + 4) + '\x02')

    def setLeftGain(self, leftGain):
        self.transport.write('\x00' + "FDGL" + '\x01' +
                                            str(int(leftGain) + 4) + '\x02')

    def setRightGain(self, rightGain):
        self.transport.write('\x00' + "FDGR" + '\x01' +
                                            str(int(rightGain) + 4) + '\x02')

    def setTempAlarm(self, tempAlarm):
        self.transport.write('\x00' + "FAT" + '\x01' +
                                            str(int(tempAlarm) + 4) + '\x02')

    def setSWRAlarm(self, SWRAlarm):
        self.transport.write('\x00' + "FAS" + '\x01' +
                                            str(int(SWRAlarm) + 4) + '\x02')

    def setUampAlarm(self, UampAlarm):
        self.transport.write('\x00' + "FAU" + '\x01' +
                                              str(int(UampAlarm) + 4) + '\x02')

    def setIampAlarm(self, IampAlarm):
        self.transport.write('\x00' + "FAC" + '\x01' +
                                            str(int(IampAlarm) + 4) + '\x02')

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
        self.registerForRpc(self.factory.mcuProtocol,
                                    "http://example.com/mcu-control#")


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
    ## calls reactor internally
    listenWS(wsMcuFactory)

    ## create serial port and serial port protocol
    ##
    log.msg('About to open serial port %s [%d baud] ..' % (port, baudrate))
    serialPort = SerialPort(wsMcuFactory.mcuProtocol, port,\
                           reactor, baudrate=baudrate)

    ## create embedded web server for static files
    ##
    webdir = File(".")   # Resource
    web = Site(webdir)
    reactor.listenTCP(webport, web)

    ## start Twisted reactor ..
    ##
    reactor.run()
