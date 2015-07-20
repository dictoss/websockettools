#!/usr/bin/python
#
# websocket relay daemon for EqCare.
#
"""
Copyright (c) 2015, SUGIMOTO Norimitsu <dictoss@live.jp>
All rights reserved.

Redistribution and use in source and binary forms,
with or without modification, are permitted provided
that the following conditions are met:

1. Redistributions of source code must retain the above
copyright notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above
copyright notice, this list of conditions and the following
disclaimer in the documentation and/or other materials
provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
import sys
import json
import datetime
import time
import logging

# for python-2.7
import ConfigParser
# for python-3.x
#import configparser

from twisted.python import log
from twisted.internet import reactor
from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory, WebSocketClientProtocol, WebSocketClientFactory, connectWS

# macro
PROCRET_SUCCESS = 0
PROCRET_ERROR_CONFIG = 1
PROCRET_ERROR_WS = 2


# global var
glogger = None
gconfig = None
gdownman = None


def init(confpath):
    # read config
    _config = None
    global glogger
    global gconfig
    global gdownman

    gdownman = MyDownstreamManager()

    try:
        _config = ConfigParser.ConfigParser()
        _config.read(confpath)

        gconfig = _config
    except:
        sys.stderr.write('fail read config file.\n')
        return False

    try:
        glogger = logging.getLogger(_config.get('main', 'name'))

        _logpath = _config.get('log', 'path')
        _h = logging.FileHandler(_logpath)

        _formatter = logging.Formatter(
            '%(asctime)s,%(levelname)-8s,%(message)s')
        _h.setFormatter(_formatter)

        glogger.addHandler(_h)

        glogger.setLevel(logging.DEBUG)
    except:
        sys.stderr.write('fail create logger. (%s,%s)\n' % (
                sys.exc_info()[1], sys.exc_info()[2]))

    return True


class MyEqCareProtocol(WebSocketClientProtocol):
    def onConnect(self, response):
        glogger.info("Server connected: {0}".format(response.peer))

    def onOpen(self):
        data = {
            "version": {
                "common_version": "1",
                "details_version": "1"},
            "common": {
                "datatype": "authentication",
                "msgid": "",
                "sendid": "",
                "senddatetime": ""
                },
            "details": {
                "password": gconfig.get('upstream', 'api_password')
                },
            "sender": {
                "version": "1",
                "userid": gconfig.get('upstream', 'api_userid'),
                "termid": gconfig.get('upstream', 'api_termid')
                },
            "receiver": {
                "version": "1",
                "userid": "*",
                "termid": "*"
                },
            }

        s = json.dumps(data).encode('utf8')
        self.sendMessage(s, isBinary=False)
        glogger.info(s)

    def onClose(self, wasClean, code, reason):
        glogger.info('Closed down. (code=%s, reason=%s)' % (code, reason))

    def onPong(self, payload):
        glogger.debug('UPSTREAM: onPong')
        super(MyEqCareProtocol, self).onPong(payload)

    def onPing(self, payload):
        glogger.debug('UPSTEAM: onPing')
        super(MyEqCareProtocol, self).onPing(payload)

    def onMessage(self, payload, isBinary):
        glogger.info('---- EVENT : receive : %s' % datetime.datetime.now())

        if isBinary:
            glogger.info("Binary message received: {0} bytes".format(len(payload)))
        else:
            s = payload.decode('utf8')
            message = json.loads(s)

            glogger.info("Text message received:")
            glogger.info(message)

            if 'details' in message and 'datatype' in message['common']:
                glogger.info('datatype: %s' % message['common']['datatype'])

                if 'authentication' == message['common']['datatype']:
                    if '200' == message['details']['resultcode']:
                        glogger.info('success auth')
                    else:
                        glogger.warn('fail auth')
                else:
                    glogger.info('do relay.')
                    #
                    # relay code
                    #
                    payload = json.dumps(message,
                                         ensure_ascii=False).encode('utf8')

                    gdownman.broadcast(payload)
            else:
                print('receive unknown message.')

        print


class MyDownstreamClinet(object):
    client = None
    is_auth = False
    datatypes = {}

    def __init__(self, client):
        self.client = client


class MyDownstreamManager(object):
    _clientlist = []

    def __init__(self):
        pass

    def add_client(self, c):
        self._clientlist.append(c)
        glogger.debug('add client : %s' % (c))

    def remove_client(self):
        pass

    def broadcast(self, payload):
        for c in self._clientlist:
            try:
                c.client.sendMessage(payload, isBinary=False)
            except:
                glogger.error('EXCEPT: fail relay. (%s, %s)' % (
                        sys.exc_info()[0], sys.exc_info()[1]))


class MyServerProtocol(WebSocketServerProtocol):
    def onConnect(self, request):
        glogger.info('CLIENT: onConnect, peer=%s' % (request.peer))

        c = MyDownstreamClinet(self)

        global gdownman
        gdownman.add_client(c)

    def onOpen(self):
        glogger.info('CLIENT: onOpen(), welcome Websocket!')

    def onClose(self, wasClean, code, reason):
        glogger.info('CLIENT: Closed down. (code=%s, reason=%s)' % (
                     code, reason))

    def onPong(self, payload):
        glogger.debug('CLIENT: onPong')
        super(MyServerProtocol, self).onPong(payload)

    def onPing(self, payload):
        glogger.debug('CLIENT: onPing')
        super(MyServerProtocol, self).onPing(payload)

    def onMessage(self, payload, isBinary):
        glogger.info('CLIENT-RECV : %s' % datetime.datetime.now())

        if isBinary:
            pass
        else:
            glogger.info(payload)


class MyController(object):
    _config = None
    _config_path = ''
    _downstream_factory = None
    _upstream = None

    def __init__(self, config):
        self._config = config

    def start(self):
        if self._config is None:
            return False

        try:
            #log.startLogging(sys.stdout)

            # start upstream client
            factory = WebSocketClientFactory(
                self._config.get('upstream', 'api_url'),
                debug=False)
            factory.protocol = MyEqCareProtocol

            connectWS(factory)

            glogger.info('start upstream connection.: %s' % (
                    self._config.get('upstream', 'api_url')))

            # start downstream server
            __listen_url = '%s://%s:%s/wsrelayd/' % (
                self._config.get('downstream', 'listen_protocol'),
                self._config.get('downstream', 'listen_address'),
                self._config.get('downstream', 'listen_port'))
            glogger.info('listen url: %s' % (__listen_url))

            self._downstream_factory = WebSocketServerFactory(
                url=__listen_url,
                protocols=['chat'],
                debug=False)
            self._downstream_factory.protocol = MyServerProtocol
            self._downstream_factory.setProtocolOptions(maxFramePayloadSize=0)
            self._downstream_factory.setProtocolOptions(maxMessagePayloadSize=0)
            self._downstream_factory.setProtocolOptions(autoFragmentSize=0)
            self._downstream_factory.setProtocolOptions(versions=[8, 13])

            self._downstream_factory.setProtocolOptions(
                openHandshakeTimeout=self._config.getint(
                    'downstream', 'openHandshakeTimeout'))
            self._downstream_factory.setProtocolOptions(
                autoPingInterval=self._config.getint(
                    'downstream', 'autoPingInterval'))
            self._downstream_factory.setProtocolOptions(
                autoPingTimeout=self._config.getint(
                    'downstream', 'autoPingTimeout'))

            glogger.info('start downstream connection.')
            reactor.listenTCP(
                self._config.getint('downstream', 'listen_port'),
                self._downstream_factory)

            # loop
            reactor.run()
        except:
            glogger.error('EXCEPT: fail start connection. (%s, %s)' % (
                    sys.exc_info()[1], sys.exc_info()[2]))
            return False

        return True


def main():
    confpath = './wsrelayd.ini'

    try:
        if False == init(confpath):
            sys.stderr.write('fail init. abort.\n')
            return PROCRET_ERROR_CONFIG
    except:
        return PROCRET_ERROR_CONFIG

    try:
        glogger.info('==== start program ====')

        relay = MyController(gconfig)

        if False == relay.start():
            glogger.error('error connection start. abort.')
            return PROCRET_ERROR_WS
    except:
        glogger.error('EXCEPT: %s' % sys.exc_info()[1])
        return PROCRET_ERROR_WS

    glogger.info('---- finish program ----')
    return PROCRET_SUCCESS


if __name__ == '__main__':
    ret = main()
    sys.exit(ret)
