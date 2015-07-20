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
from ws4py.client.threadedclient import WebSocketClient


class MyWebsocketClient(WebSocketClient):
    api_userid = ''
    api_password = ''
    api_termid = ''

    def opened(self):
        print('opened')
        
        data = {
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
        #message = json.loads(str(m))
        print(m)
        print

    def sendmsg(self, data):
        message = json.dumps(data)
        self.send(message)
        print('senddata:')
        print(message)
        print


def main():
    _url = 'ws://localhost:8080/'

    try:
        print('try connect : %s' % (_url))

        ws = MyWebsocketClient(
            _url,
            protocols=['chat'])

        ws.api_userid = 'dummy_user'
        ws.api_password = 'dummy_pass'
        ws.api_termid = 'dummy_termid'

        #print(ws.port)

        ws.connect()
        ws.run_forever()
        #while True:
        #    line = input()
        #    print("stdin!")
    except KeyboardInterrupt:
        ws.close()
    except:
        print("EXCEPT: %s, %s" % (sys.exc_info()[1], sys.exc_info()[2]))
        return 1

    return 0


if __name__ == '__main__':
    ret = main()
    sys.exit(ret)