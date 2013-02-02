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
import datetime

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
from twisted.internet.task import LoopingCall
from twisted.web.server import Site
from twisted.web.static import File

from autobahn.websocket import listenWS
from autobahn.wamp import WampServerFactory, WampServerProtocol, exportRpc


class Serial2WsOptions(usage.Options):
    optParameters = [
      ['baudrate', 'b', 9600, 'Serial baudrate'],
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
        self.writeTransmitter("FM", '\x20')

    @exportRpc("set-power")
    def setPower(self, power):
        if 0 <= float(power) <= 100.0:
            power_s = chr(int(round(int(power) / 100.0 * 34) + 4))
            self.writeTransmitter("FO", power_s)

    @exportRpc("set-freq")
    def setFrequency(self, freq):
        if 87.5 <= float(freq) <= 108.0:
            # convert from ASCII and from Mhz to KHz
            freq = float(freq) * 1000
            #low part of freq
            low = chr((int(freq / 5) - int(int(freq / 5) / 128) * 128) + 4)
            #high part of freq
            high = chr((int(int(freq / 5) / 128)) + 4)
            self.writeTransmitter("FF", low + high)

    @exportRpc("set-channels")
    def setChannels(self, channels):
        if 0 <= int(channels) <= 1:
            # convert from int to ASCII
            channels = str(channels)
            self.writeTransmitter("FS", channels)

    @exportRpc("set-DSP")
    def setDSP(self, attack, decay, interval, threshold, compression):
        self.setAttack(attack)
        self.setDecay(decay)
        self.setIntegration(interval)
        self.setThreshold(threshold)
        self.setCompression(compression)

    @exportRpc("set-alarms")
    def setAlarms(self, swr_alarm, current_alarm, temp_alarm, Uamp_alarm):
        self.setTempAlarm(temp_alarm)
        self.setSWRAlarm(swr_alarm)
        self.setUampAlarm(Uamp_alarm)
        self.setIampAlarm(current_alarm)

    @exportRpc("set-bass-treble")
    def setBassTreble(self, treble, bass):
        self.setTreble(treble)
        self.setBass(bass)

    @exportRpc("set-audio")
    def setAudio(self, left_gain, right_gain):
        self.setRightGain(right_gain)
        self.setLeftGain(left_gain)

    def setTreble(self, treble):
        self.writeTransmitter("FDT", chr(int(treble) + 4))

    def setBass(self, bass):
        self.writeTransmitter("FDB", chr(int(bass) + 4))

    def setAttack(self, attack):
        self.writeTransmitter("FDA", chr(int(attack) + 4))

    def setDecay(self, decay):
        self.writeTransmitter("FDD", chr(int(decay) + 4))

    def setThreshold(self, threshold):
        self.writeTransmitter("FDH", chr(int(threshold) + 4))

    def setCompression(self, compression):
        self.writeTransmitter("FDC", chr(int(compression) + 4))

    def setIntegration(self, integration):
        self.writeTransmitter("FDI", chr(int(integration) + 4))

    def setLeftGain(self, leftGain):
        self.writeTransmitter("FDGL", chr(int(leftGain) + 4))

    def setRightGain(self, rightGain):
        self.writeTransmitter("FDGR", chr(int(rightGain) + 4))

    def setTempAlarm(self, tempAlarm):
        self.writeTransmitter("FAT", chr(int(tempAlarm) + 4))

    def setSWRAlarm(self, SWRAlarm):
        self.writeTransmitter("FAS", chr(int(SWRAlarm) + 4))

    def setUampAlarm(self, UampAlarm):
        self.writeTransmitter("FAU", chr(int(UampAlarm) + 4))

    def setIampAlarm(self, IampAlarm):
        self.writeTransmitter("FAC", chr(int(IampAlarm) + 4))

    # RDS COMMANDS
    @exportRpc("PI-code")
    def setPICode(self, country, country_ecc, pr):
        if  0 <= int(pr) <= 255:
            print country, country_ecc, pr

    @exportRpc("A0-settings")
    def setA0Settings(self, tp, ta, ms, dyn_pty, compression, channels, ah, program_type):
        print tp, ta, ms, dyn_pty, compression, channels, ah, program_type

    @exportRpc("PF-alternative")
    def setPFAlternative(self, num, freq):
        if 87.5 <= float(freq) <= 108.0:
            print num, freq

    # FIXME: test for empty msg, perhaps?
    @exportRpc("static-PS")
    def setStaticPS(self, msg, delay):
        if  0 <= int(delay) <= 9:
            print msg, delay

    @exportRpc("dynamic-PS")
    def setStaticPS(self, k, msg, delay):
        #not inside k interval
        if not 1 <= int(k) <= 99:
            return
        # not inside delay interval
        if not 0 <= int(delay) <= 9:
            return
        # msg empty
        if not msg:
            return
        print k, msg, delay


    @exportRpc("sync-time")
    def setSyncTime(self):
        print datetime.datetime.now()

    @exportRpc("external-messages")
    def setExternalMessages(self, msg1, msg2, msg3, msg4, msg5, msg6, msg7, msg8):
        print msg1, msg2, msg3, msg4, msg5, msg6, msg7, msg8

    def writeTransmitter(self, command, data):
        self.transport.write('\x00\x00' + command + '\x01' + data + '\x02')

    def connectionMade(self):
        log.msg('Serial port connected.')

    def lineReceived(self, line):
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
        except AttributeError:
            print "Could not parse string."

    def updateDatetime(self):
        date = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.wsMcuFactory.dispatch("http://example.com/mcu#update-time", date)


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

    ## Looping Call to keep updating date and time on client
    lc = LoopingCall(wsMcuFactory.mcuProtocol.updateDatetime)
    lc.start(1)

    ## create embedded web server for static files
    ##
    webdir = File(".")   # Resource
    web = Site(webdir)
    reactor.listenTCP(webport, web)

    ## start Twisted reactor ..
    ##
    reactor.run()
