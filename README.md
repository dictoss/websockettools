# wsrelayd
websocket daemon and tools for EqCare.

# CurrentVersion
0.6.1

# wsrelayd function
- exec daemon. (support debian-9, rhel-6, rhel-7)
- connect EqCare websocket server. (support ws:// and wss://)
- listen downstream websocket clients.
- relay messages receivced EqCare websocket server to downstream.
- re-connect EqCare websocket server if disconnect.
- filtercast mode.
- authentication downstream websocket client.
  - ini-file support.
  - (yet) sqlite3 support
- SSL/TLS support downstream websocket.
- multiple upstream support.
- (yet) user-authentication config reload.
- (yet) client-to-client message support.

# Develop Environment (server)
- Debian GNU/Linux 9 (stretch) amd64
- python 2.7 or 3.5+
- Twisted 16.6.0
- autobahn 0.17.0
- txaio 2.5.2
- six 1.10.0
- cffi 1.11.2
- pyOpenSSL 17.5.0
- service-identity 1.0.0

# Develop Environment (client)
- Debian GNU/Linux 9 (stretch) amd64
- python 2.7 or 3.5+
- ws4py 0.3.5
