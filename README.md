# wsrelayd
websocket daemon and tools for EqCare.

# CurrentVersion
0.6.1

# wsrelayd function
- exec daemon. (support debian-10, rhel-7)
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
- Debian GNU/Linux 10 (buster) amd64
- python 3.6+

# Develop Environment (client)
- Debian GNU/Linux 10 (stretch) amd64
- python 3.6+
- ws4py 0.5.1
