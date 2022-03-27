# WARNINGS: This project has been archived. It will not be updated anymore.

- wsrelayd application has been archived.
- The reason is as follows.
    - As for the library you are using, ws4py is no longer maintained.
    - The program is difficult because many libraries are used. It requires extensive refactoring to maintain.
    - If you've done a large refactoring, the program will be a different one.
    - Therefore, we havetened to maintain this program.

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
