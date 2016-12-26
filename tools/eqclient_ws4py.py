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
import six

if six.PY2:
    import ConfigParser
else:
    import configparser

from ws4py.client.threadedclient import WebSocketClient


class MyWebsocketClient(WebSocketClient):
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
        print(data)

    def closed(self, code, reason):
        print('Closed down. (code=%s, reason=%s)' % code, reason)

    def received_message(self, m):
        print('--------')
        print('EVENT : receive : %s' % datetime.datetime.now())
        message = json.loads(str(m))

        if 'details' in message and 'datatype' in message['common']:
            print('datatype: %s' % message['common']['datatype'])
            print(message)

            if 'authentication' == message['common']['datatype']:
                if '200' == message['details']['resultcode']:
                    print('success auth')
                else:
                    print('fail auth')
            else:
                print(message)
        else:
            print('receive unknown message.')

        print

    def sendmsg(self, data):
        message = json.dumps(data)
        self.send(message)
        print('senddata:')
        print(message)
        print


def main():
    ret = 0
    config = None

    try:
        if six.PY2:
            config = ConfigParser.ConfigParser()
        else:
            config = configparser.ConfigParser()

        config.read('./wsclient_ws4py.ini')

        print('success read config.')
    except:
        print('error read config. abort. (%s, %s)' % (
            sys.exc_info()[0], sys.exc_info()[1]))
        return 2

    try:
        print('try connect : %s' % (config.get('default', 'API_URL')))

        ws = MyWebsocketClient(
            config.get('default', 'API_URL'),
            protocols=['http-only', 'chat'])

        ws.api_userid = config.get('default', 'API_USERID')
        ws.api_password = config.get('default', 'API_PASSWORD')
        ws.api_termid = config.get('default', 'API_TERMID')

        ws.connect()

        while True:
            line = input()
            print("stdin!")

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
