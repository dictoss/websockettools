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

# for upstream
from ws4py.client.threadedclient import WebSocketClient
# for client
from twisted.python import log
from twisted.internet import reactor
from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory

# macro
PROCRET_SUCCESS = 0
PROCRET_ERROR_CONFIG = 1
PROCRET_ERROR_WS = 2


# global var
glogger = None
gconfig = None
gclientlist = []


def init(confpath):
    # read config
    _config = None
    global glogger
    global gconfig

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

        glogger.setLevel(logging.INFO)
    except:
        sys.stderr.write('fail create logger. (%s,%s)\n' % (
                sys.exc_info()[1], sys.exc_info()[2]))

    return True


class MyEqCareWs4pyClient(WebSocketClient):
    api_userid = ''
    api_password = ''
    api_termid = ''

    def opened(self):
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
            "password": self.api_password
          },
          "sender": {
            "version": "1",
            "userid": self.api_userid,
            "termid": self.api_termid
          },
          "receiver": {
            "version": "1",
            "userid": "*",
            "termid": "*"
          },
        }

        self.send(json.dumps(data))

        glogger.info('UPSTREAM: send auth message.')
        glogger.info(data)

    def closed(self, code, reason):
        glogger.info('UPSTREAM: Closed down. (code=%s, reason=%s)' % (
                code, reason))

    def received_message(self, m):
        glogger.info('UPSTREAN-RECV : receive : %s' % datetime.datetime.now())
        message = json.loads(str(m))

        if 'details' in message and 'datatype' in message['common']:
            glogger.info('UPSTREAM: datatype: %s' %
                        message['common']['datatype'])
            glogger.info(message)

            if 'authentication' == message['common']['datatype']:
                if '200' == message['details']['resultcode']:
                    glogger.info('UPSTREAM: success auth')
                else:
                    glogger.info('UPSTREAM: fail auth')
            else:
                glogger.info('do relay message')
                #
                # relay code
                #
                payload = json.dumps(message, ensure_ascii=False).encode('utf8')
                for c in gclientlist:
                    try:
                        c.client.sendMessage(payload, isBinary=False)
                    except:
                        glogger.error('EXCEPT: fail relay. (%s, %s)' % (
                                sys.exc_info()[0], sys.exc_info()[1]))
        else:
            glogger.debug('receive unknown message.')


class MyWebsocetClinetInfo(object):
    client = None
    is_auth = False
    datatypes = {}

    def __init__(self, client):
        self.client = client


class MyServerProtocol(WebSocketServerProtocol):
    def onConnect(self, request):
        glogger.info('CLIENT: onConnect, peer=%s' % (request.peer))

        wsc = MyWebsocetClinetInfo(self)

        global gclientlist
        gclientlist.append(wsc)

    def onOpen(self):
        glogger.info('CLIENT: onOpen(), welcome Websocket!')

    def onClose(self, wasClean, code, reason):
        glogger.info('CLIENT: Closed down. (code=%s, reason=%s)' % (
                     code, reason))

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
            # start upstream client
            self._upstream = MyEqCareWs4pyClient(
                self._config.get('upstream', 'api_url'),
                protocols=['http-only', 'chat'])

            self._upstream.api_userid = self._config.get(
                'upstream', 'api_userid')
            self._upstream.api_password = self._config.get(
                'upstream', 'api_password')
            self._upstream.api_termid = self._config.get(
                'upstream', 'api_termid')

            self._upstream.relay_streams = self._downstream_factory

            glogger.info('start upstream connection.: %s' % (
                    self._config.get('upstream', 'api_url')))
            self._upstream.connect()

            # start downstream server
            #log.startLogging(sys.stdout)

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
            self._downstream_factory.setProtocolOptions(openHandshakeTimeout=0)
            self._downstream_factory.setProtocolOptions(autoPingInterval=300)
            self._downstream_factory.setProtocolOptions(autoPingTimeout=15)
            self._downstream_factory.setProtocolOptions(versions=[8, 13])

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
