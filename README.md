# wsrelayd
websocket daemon and tools for EqCare.

# CurrentVersion
0.2.0

# wsrelayd function
- (only debian, not rhel6 yet) exec daemon.
- connect EqCare websocket server.
- listen downstream websocket clients.
- relay messages receivced EqCare websocket server to downstream.
- re-connect EqCare websocket server if disconnect.
- filtercast mode.
- (yet) authentication downstream websocket client.

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
