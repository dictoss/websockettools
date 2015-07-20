#!/usr/bin/python
#
# websocket clinet for test.
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
import ConfigParser
import ssl
from twisted.python import log
from twisted.internet import reactor
from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory, connectWS

gconfig = None


class MyClientProtocol(WebSocketClientProtocol):
    def onConnect(self, response):
        print("Server connected: {0}".format(response.peer))

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
            "password": gconfig.get('default', 'api_password')
          },
          "sender": {
            "version": "1",
            "userid": gconfig.get('default', 'api_userid'),
            "termid": gconfig.get('default', 'api_termid')
          },
          "receiver": {
            "version": "1",
            "userid": "*",
            "termid": "*"
          },
        }

        s = json.dumps(data).encode('utf8')
        self.sendMessage(s, isBinary=False)
        print(s)

    def onMessage(self, payload, isBinary):
        print('--------')
        print('EVENT : receive : %s' % datetime.datetime.now())

        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            s = payload.decode('utf8')
            message = json.loads(s)

            print("Text message received:")
            print(message)

            if 'details' in message and 'datatype' in message['common']:
                print('datatype: %s' % message['common']['datatype'])

                if 'authentication' == message['common']['datatype']:
                    if '200' == message['details']['resultcode']:
                        print('success auth')
                    else:
                        print('fail auth')
                else:
                    print('do task.')
            else:
                print('receive unknown message.')

        print

    def onClose(self, wasClean, code, reason):
        print('Closed down. (code=%s, reason=%s)' % (code, reason))


def main():
    ret = 0
    global gconfig
    config = None

    try:
        config = ConfigParser.ConfigParser()
        config.read('./eqclient_autobahn.ini')

        gconfig = config
        print('success read config.')
    except:
        print('error read config. abort. (%s, %s)' % (
                sys.exc_info()[0], sys.exc_info()[1]))
        return 2

    try:
        print('try connect : %s' % (config.get('default', 'API_URL')))
        #log.startLogging(sys.stdout)

        factory = WebSocketClientFactory(
            config.get('default', 'API_URL'),
            debug=False)
        factory.protocol = MyClientProtocol

        connectWS(factory)

        reactor.run()
    except KeyboardInterrupt:
        ws.close()
        return 0
    except:
        print("EXCEPT: %s" % sys.exc_info()[1])
        return 1

    return ret


if __name__ == '__main__':
    ret = main()
    sys.exit(ret)
