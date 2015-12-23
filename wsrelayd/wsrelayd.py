#!/usr/bin/python
# coding: utf-8
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
import getopt
import threading
import copy
# for python-2.7
import ConfigParser
# for python-3.x
# import configparser

from twisted.python import log
from twisted.internet import defer, ssl
from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory, WebSocketClientProtocol, WebSocketClientFactory, connectWS

# macro
PROCRET_SUCCESS = 0
PROCRET_ERROR_CONFIG = 1
PROCRET_ERROR_WS = 2
PROCRET_ERROR_GETOPT = 3

AUTH_BROADCAST = 0
AUTH_FILTERCAST = 1
AUTH_FILTERCAST_CUT = 2

MAX_UPSTREAM_COUNT = 2
DUP_MSGID_TIMEOUT_SEC = 120

# global var
glogger = None
gconfig = None
gdownman = None
gconfig_user = None

from twisted.internet import epollreactor
epollreactor.install()


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

    read_userconf(gconfig.get('main', 'userconf'))
    return True


def read_userconf(userconf):
    global gconfig_user

    try:
        _userconf = ConfigParser.ConfigParser()
        _userconf.read(userconf)
        gconfig_user = _userconf
    except:
        glogger.error('fail read user config. (%s,%s)\n' % (
            sys.exc_info()[1], sys.exc_info()[2]))


class MyEqCareProtocol(WebSocketClientProtocol):
    _force_broadcast = False
    _broadcast_list = ['']
    config_section = ''

    # class variables. share multi upstream instances.
    _msgid_list = []
    _msgid_lock = threading.RLock()

    def onConnect(self, response):
        glogger.info("Server connected: {0}".format(response.peer))
        self.config_section = self.factory.config_section

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
                "password": gconfig.get(self.config_section, 'api_password')
                },
            "sender": {
                "version": "1",
                "userid": gconfig.get(self.config_section, 'api_userid'),
                "termid": gconfig.get(self.config_section, 'api_termid')
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
        glogger.warn('Closed down. (code=%s, reason=%s)' % (code, reason))

    def onPong(self, payload):
        glogger.debug('%s: onPong' % (self.config_section))
        super(MyEqCareProtocol, self).onPong(payload)

    def onPing(self, payload):
        glogger.debug('%s: onPing' % (self.config_section))
        super(MyEqCareProtocol, self).onPing(payload)

    def onMessage(self, payload, isBinary):
        glogger.info('---- EVENT : %s : receive : %s' % (
            self.config_section,
            datetime.datetime.now()))

        if isBinary:
            glogger.info("Binary message received: %s bytes" % (
                len(payload)))
        else:
            s = payload.decode('utf8')
            glogger.info("Text message received:")
            glogger.info(s)

            try:
                message = json.loads(s)

                if 'details' in message and 'datatype' in message['common']:
                    datatype = message['common']['datatype']
                    msgid = message['common']['msgid']
                    glogger.info('datatype: %s' % (datatype))

                    if 'authentication' == message['common']['datatype']:
                        if '200' == message['details']['resultcode']:
                            glogger.info('success auth')
                        else:
                            glogger.warn('fail auth')
                    else:
                        #
                        # relay code
                        #

                        # write downstream to first upstream only.
                        self.delete_expire_msgid()
                        is_first = self.is_first_forward(msgid)

                        if is_first:
                            if self._force_broadcast:
                                # use broadcast if received any datatype.
                                glogger.info('do broadcast force')
                                gdownman.broadcast(payload)
                            else:
                                if datatype in self._broadcast_list:
                                    # use broadcast if received any datatype.
                                    glogger.info('do broadcast in')
                                    gdownman.broadcast(payload)
                                else:
                                    glogger.info('do filtercast')
                                    gdownman.filtercast(payload)

                            glogger.info('%s: message is first. forwarded.' % (
                                self.config_section))
                        else:
                            glogger.info('%s: message is duplicate.' % (
                                self.config_section))
                else:
                    glogger.debug('receive unknown message.')
            except:
                glogger.warn('%s: EXCEPT: onMessage. (%s, %s)' % (
                    self.config_section,
                    sys.exc_info()[0], sys.exc_info()[1]))

    def is_first_forward(self, msgid):
        glogger.debug('IN is_first_forward()')

        result = False

        with MyEqCareProtocol._msgid_lock:
            for o in MyEqCareProtocol._msgid_list:
                if msgid == o['msgid']:
                    break
            else:
                d = {'msgid': msgid, 'time': datetime.datetime.now()}
                MyEqCareProtocol._msgid_list.append(d)
                result = True

        return result

    def delete_expire_msgid(self):
        glogger.debug('IN delete_expire_msgid()')

        delta = datetime.timedelta(seconds=DUP_MSGID_TIMEOUT_SEC)
        now = datetime.datetime.now()
        swaplist = None

        with MyEqCareProtocol._msgid_lock:
            swaplist = [x for x in MyEqCareProtocol._msgid_list if now - x['time'] < delta]
            MyEqCareProtocol._msgid_list = swaplist
            glogger.debug('duplicate-msgid-list : %s' % (
                MyEqCareProtocol._msgid_list))


class MyDownstreamClinet(object):
    client = None
    userid = None
    _is_auth = False
    _is_auth_broadcast = False
    _recv_filter = {}

    def __init__(self, client):
        self.client = client

    def auth(self, userid, password):
        # match user config file.
        try:
            global gconfig_user

            confpass = gconfig_user.get(userid, 'password')
            if confpass == password:
                if '1' == gconfig_user.get(userid, 'is_broadcast'):
                    self._is_auth_broadcast = True

                self._is_auth = True
                self.userid = userid
                glogger.info('auth() : success. user=%s' % (userid))
            else:
                glogger.warn('auth() : failed. not match password.')
        except:
            glogger.warn('auth() : failed.(%s, %s)' % (
                sys.exc_info()[0], sys.exc_info()[1]))
            self._is_auth_broadcast = False
            self._is_auth = False

        return self._is_auth

    def is_auth(self):
        return self._is_auth

    def is_auth_broadcast(self):
        return self._is_auth_broadcast

    def is_broadcast(self):
        if self._recv_filter is None:
            return True
        else:
            return False

    def set_filter(self, use_broadcast, recv_filter):
        """
        filter format
        {'datatype': {'filter_key': ['value1', 'value2']}

        ex)
        {
        'earthquake': {'areainfo': ['123456']},
        'tsunami': {'areacode': ['200']}
        }
        """
        ret = AUTH_BROADCAST

        if '1' == use_broadcast and True == self.is_auth_broadcast():
            glogger.info("client is broadcast mode.")
            self._recv_filter = None

            ret = AUTH_BROADCAST
        else:
            glogger.info("client is filter mode.")
            ret = AUTH_FILTERCAST

            limit = gconfig.getint('downstream', 'datatype_filter_max')

            for k, v in recv_filter.iteritems():
                try:
                    self._recv_filter[k] = {}

                    if v:
                        for kk, vv in v.iteritems():
                            # if over limit, delete tail.
                            if limit < len(vv):
                                glogger.warn('over filter count.(%s:%s=%s)' % (k, kk, len(vv)))
                                self._recv_filter[k][kk] = vv[0:limit]
                                ret = AUTH_FILTERCAST_CUT
                            else:
                                self._recv_filter[k][kk] = vv
                except:
                    glogger.warn('fail parse client filter. (%s, %s)' % (
                        sys.exc_info()[0], sys.exc_info()[1]))
                    self._recv_filter[k] = {}
                    ret = AUTH_FILTERCAST_CUT

            glogger.info(self._recv_filter)

        return ret

    def filter_payload(self, message):
        filtered = {}

        try:
            if 'details' in message and 'datatype' in message['common']:
                datatype = message['common']['datatype']

                filtertypes = self._recv_filter.keys()
                if datatype not in filtertypes:
                    return None

                filtered['version'] = message['version']
                filtered['common'] = message['common']

                # filter details
                if datatype == 'earthquake':
                    filtered['details'] = copy.deepcopy(message['details'])

                    # get sub-set araeinfo
                    del filtered['details']['areainfo']
                    filtered['details']['areainfo'] = {}

                    if 'areainfo' in self._recv_filter['earthquake']:
                        c_set = set(self._recv_filter['earthquake']['areainfo'])
                        data_set = set(message['details']['areainfo'].keys())

                        target_set = data_set.intersection(c_set)
                        glogger.info('terget_set : %s' % target_set)
                        for i in target_set:
                            filtered['details']['areainfo'][i] = message['details']['areainfo'][i]
                else:
                    filtered['details'] = []

                    for r in message['details']:
                        for k, v in self._recv_filter[datatype].iteritems():
                            for i in v:
                                if k in r and i == r[k]:
                                    glogger.debug('match, k=%s, v=%s' % (k, i))
                                    break
                            else:
                                break
                        else:
                            filtered['details'].append(r)
            else:
                glogger.warn('not found details or datatype in message.')
                return None
        except:
            glogger.warn('fail parse upstream message - filter.(%s, %s)' % (
                sys.exc_info()[0], sys.exc_info()[1]))

            return None

        return json.dumps(filtered)

    def sendMessage(self, payload):
        try:
            glogger.info('client send message. : userid=%s' % (self.userid))
            self.client.sendMessage(payload, isBinary=False)
        except:
            glogger.warn('EXCEPT: fail relay<%s>. (%s, %s)' % (
                id(self.client), sys.exc_info()[0], sys.exc_info()[1]))


class MyDownstreamManager(object):
    # key is id(MyServerProtocol),
    # value is MyDownstreamClinet instance
    _clients = {}
    _client_count = 0
    _lock_clients = threading.Lock()

    def __init__(self):
        pass

    def add_client(self, c):
        glogger.debug('add client<id> : %s' % (id(c)))

        client = MyDownstreamClinet(c)

        with self._lock_clients:
            self._clients[id(c)] = client
            self._client_count = self._client_count + 1
            glogger.info('client count<add> = %s' % (self._client_count))

    def remove_client(self, c):
        glogger.debug('remove client<id> : %s' % (id(c)))

        with self._lock_clients:
            if id(c) in self._clients:
                del self._clients[id(c)]
                self._client_count = self._client_count - 1
                glogger.info('client count<rm> = %s' % (self._client_count))

    def get_client(self, c):
        glogger.debug('select client<id> : %s' % (id(c)))

        with self._lock_clients:
            # if id(c) in self._clients:
            return self._clients[id(c)]

    def broadcast(self, payload):
        with self._lock_clients:
            for k, v in self._clients.iteritems():
                v.sendMessage(payload)

    def filtercast(self, payload):
        with self._lock_clients:
            s = payload.decode('utf8')
            message = json.loads(s)

            for k, v in self._clients.iteritems():
                if v.is_auth_broadcast() and v.is_broadcast():
                    v.sendMessage(payload)
                else:
                    filtered = v.filter_payload(message)
                    if filtered is not None:
                        v.sendMessage(filtered)


class MyServerProtocol(WebSocketServerProtocol):
    def onConnect(self, request):
        glogger.info('CLIENT: onConnect, peer=%s' % (request.peer))

        global gdownman
        gdownman.add_client(self)

    def onOpen(self):
        glogger.info('CLIENT: onOpen(), welcome Websocket!')

    def onClose(self, wasClean, code, reason):
        glogger.info('CLIENT: Closed down. (code=%s, reason=%s)' % (
                     code, reason))

        global gdownman
        gdownman.remove_client(self)

    def onPong(self, payload):
        glogger.debug('CLIENT: onPong')
        super(MyServerProtocol, self).onPong(payload)

    def onPing(self, payload):
        glogger.debug('CLIENT: onPing')
        super(MyServerProtocol, self).onPing(payload)

    def onMessage(self, payload, isBinary):
        glogger.info('CLIENT-RECV : %s' % datetime.datetime.now())

        if isBinary:
            glogger.warn('unsupport binary message.')
            return

        try:
            glogger.info(payload)

            s = payload.decode('utf8')
            glogger.info(s)

            message = json.loads(s)

            if 'details' in message and 'datatype' in message['common']:
                datatype = message['common']['datatype']
                glogger.info('client datatype: %s' % (datatype))

                if 'authentication' == message['common']['datatype']:
                    # optional parameter
                    if 'use_broadcast' not in message['details']:
                        message['details']['use_broadcast'] = '0'

                    global gdownman
                    client = gdownman.get_client(self)

                    if client.auth(message['sender']['userid'],
                                   message['details']['password']):
                        glogger.info('client success auth')

                        ret = client.set_filter(
                            message['details']['use_broadcast'],
                            message['details']['filter'])

                        # response auth message
                        resmsg = {
                            'version': {
                                'common_version': '1',
                                'details_version': '1',
                            },
                            'common': {
                                'datatype': 'authentication',
                                'msgid': '',
                                'sendid': '',
                                'senddatetime': '',
                            },
                            'details': {
                                'resultcode': '200',
                                'castmode': '',
                                'message': 'authorized success.'
                            },
                        }

                        details_msg = 'authorized success.'
                        if ret == AUTH_BROADCAST:
                            resmsg['details']['castmode'] = 'broadcast'
                            details_msg = details_msg
                        elif ret == AUTH_FILTERCAST:
                            resmsg['details']['castmode'] = 'filtercast'
                            details_msg = details_msg
                        else:
                            resmsg['details']['castmode'] = 'filtercast'
                            details_msg = details_msg + ' (cut filter list)'

                        resmsg['details']['message'] = details_msg

                        client.sendMessage(json.dumps(resmsg))
                    else:
                        glogger.warn('client fail auth. bye.')
                        self.sendClose()
                        gdownman.remove_client(self)
                else:
                    glogger.warn('client send unknown messsage.')
        except:
            glogger.warn('fail parse client message (%s, %s)' % (
                sys.exc_info()[0], sys.exc_info()[1]))


class EqCareWebSocketClientFactory(WebSocketClientFactory):
    config_section = ''

    def clientConnectionFailed(self, connector, reason):
        glogger.warn('%s: Connection failed. Reason: %s' % (
            self.config_section,
            reason))

        from twisted.internet import reactor

        # retry connect
        glogger.debug('set retry connect timer.')
        deferred = defer.Deferred()
        reactor.callLater(
            gconfig.getint(self.config_section, 'retry_connect_spantime'),
            self._retry_connect)

    def clientConnectionLost(self, connector, reason):
        glogger.warn('%s: Lost connection.  Reason: %s' % (
            self.config_section,
            reason))

        from twisted.internet import reactor

        # retry connect
        glogger.debug('set retry connect timer.')
        deferred = defer.Deferred()
        reactor.callLater(
            gconfig.getint(self.config_section, 'retry_connect_spantime'),
            self._retry_connect)

    def _retry_connect(self):
        glogger.info('retry connect.')
        connectWS(
            self,
            timeout=gconfig.getint(self.config_section, 'connect_timeout'))


class MyController(object):
    _config = None
    _config_path = ''
    _downstream_factory = None

    def __init__(self, config):
        self._config = config

    def start(self):
        if self._config is None:
            return False

        try:
            # log.startLogging(sys.stdout)

            # start upstream client
            for i in range(1, MAX_UPSTREAM_COUNT + 1):
                upstream_sec = 'upstream_%d' % ((i))

                if self._config.has_section(upstream_sec):
                    factory = EqCareWebSocketClientFactory(
                        self._config.get(upstream_sec, 'api_url'),
                        debug=False)
                    factory.protocol = MyEqCareProtocol
                    factory.config_section = upstream_sec

                    connectWS(
                        factory,
                        timeout=gconfig.getint(upstream_sec,
                                               'connect_timeout')
                    )

                    glogger.info('start %s connection.: %s' % (
                        upstream_sec,
                        self._config.get(upstream_sec, 'api_url')))
                else:
                    glogger.info('not found section. no use %s' % (
                        upstream_sec))

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
            glogger.info('backlog is %s' % (
                self._config.get('downstream', 'backlog')))

            from twisted.internet import reactor

            if 'wss' == self._config.get('downstream', 'listen_protocol'):
                glogger.info('listen ssl/tls for downstream.')
                reactor.listenSSL(
                    self._config.getint('downstream', 'listen_port'),
                    self._downstream_factory,
                    ssl.DefaultOpenSSLContextFactory(
                        self._config.get('downstream', 'ssl_key'),
                        self._config.get('downstream', 'ssl_cert')),
                    backlog=self._config.getint('downstream', 'backlog'),
                    interface=self._config.get('downstream', 'listen_address')
                )
            else:
                glogger.info('listen plain for downstream.')
                reactor.listenTCP(
                    self._config.getint('downstream', 'listen_port'),
                    self._downstream_factory,
                    backlog=self._config.getint('downstream', 'backlog'),
                    interface=self._config.get('downstream', 'listen_address')
                )

            reactor.run()
        except:
            glogger.error('EXCEPT: fail start connection. (%s, %s)' % (
                sys.exc_info()[1], sys.exc_info()[2]))
            return False

        return True


def usage():
    print('usage: wsrelayd.py -c [configfile]')


def main():
    confpath = './wsrelayd.ini'

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'c:')

        for o, a in opts:
            if o == "-c":
                confpath = a
    except:
        usage()
        return PROCRET_ERROR_GETOPT

    try:
        if False == init(confpath):
            sys.stderr.write('fail init. abort.\n')
            return PROCRET_ERROR_CONFIG
    except:
        return PROCRET_ERROR_CONFIG

    try:
        glogger.info('==== start program ====')
        glogger.info('use config file: %s' % (confpath))

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
