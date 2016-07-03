# wsrelayd
websocket daemon and tools for EqCare.

# CurrentVersion
0.5.0

# wsrelayd function
- exec daemon. (support debian-8, rhel-6)
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
- Debian GNU/Linux 8 (jessie) amd64
- python 2.7
- Twisted 15.2.1
- txaio 2.5.1
- autobahn 0.10.4
- cffi 1.1.2
- pyOpenSSL 0.15.1
- service_identity 14.0.0

# Develop Environment (client)
- Debian GNU/Linux 8 (jessie) amd64
- python 2.7
- ws4py 0.3.5
