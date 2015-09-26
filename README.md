# wsrelayd
websocket daemon and tools for EqCare.

# CurrentVersion
0.4.0

# wsrelayd function
- exec daemon. (support debian-8, rhel-6)
- connect EqCare websocket server. (support ws:// and wss://)
- listen downstream websocket clients.
- relay messages receivced EqCare websocket server to downstream.
- re-connect EqCare websocket server if disconnect.
- filtercast mode.
- authentication downstream websocket client.
- SSL/TLS support downstream websocket.
- (yet) user-authentication config reload.
- (yet) multiple upstream support.
- (yet) client-to-client message support.

# Develop Environment (server)
- Debian GNU/Linux 8 (jessie) amd64
- python 2.7
- Twisted 15.2.1
- autobahn 0.10.4
- cffi 1.1.2

# Develop Environment (client)
- Debian GNU/Linux 8 (jessie) amd64
- python 2.7
- ws4py 0.3.4 (with patched Host Header)
