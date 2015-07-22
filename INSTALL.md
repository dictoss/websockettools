--------------------
| for debian-7 (wheezy)
--------------------
- install modules and librairies
# apt-get install python-2.7 python-pip python-dev libffi-dev
# pip install pyOpenSSL
# pip install service_identity
# pip install twisted
# pip install cffi
# pip install autobahn
# pip install ws4py    (if use test client tool)

- add patch (if use ws4py)
$ diff -u __init__.py.0.3.4 __init__.py
--- /usr/local/lib/python2.7/dist-packages/ws4py/client/__init__.py.0.3.4       2015-07-19 12:25:25.000000000 +0900
+++ /usr/local/lib/python2.7/dist-packages/ws4py/client/__init__.py             2015-07-19 23:59:18.627314361 +0900
@@ -245,7 +245,7 @@
         handshake.
         """
         headers = [
-            ('Host', self.host),
+            ('Host', '%s:%s' % (self.host, self.port)),
             ('Connection', 'Upgrade'),
             ('Upgrade', 'websocket'),
             ('Sec-WebSocket-Key', self.key.decode('utf-8')),


- install
# mkdir -p /usr/local/wsrelayd
# cd <git clone dir>
# cd wsrelayd
# cp wsrelayd.py wsrelayd.ini /usr/local/wsrelayd/
# chmod 755 /usr/local/wsrelayd/wsrelay.py
# cp init.d/wsrelayd.sysvinit /etc/init.d/wsrelayd
# insserv -d wsrelayd

- modify config
# vi /usr/local/wsrelayd.ini

- make log directory
# mkdir /var/log/wsrelayd
# chown -fR nobody:nogroup /var/log/wsrelayd

- start daemon
# service wsrelayd start

--------------
| for centos-6
--------------