--------------------
| for debian-7 (wheezy)
--------------------
- install modules and librairies
# apt-get install python-2.7
# apt-get install python-pip python-dev libffi-dev libssl-dev
# pip install -r requirements.txt

- install
# mkdir -p /usr/local/wsrelayd
# cd <git clone dir>
# cd wsrelayd
# cp wsrelayd.py wsrelayd.ini /usr/local/wsrelayd/
# chmod 755 /usr/local/wsrelayd/wsrelayd.py
# cp init.d/wsrelayd.debian /etc/init.d/wsrelayd
# insserv -d wsrelayd

- modify config
# vi /usr/local/wsrelayd/wsrelayd.ini
# vi /usr/local/wsrelayd/wsrelayd_user.ini

- make log directory
# mkdir /var/log/wsrelayd
# chown -fR nobody:nogroup /var/log/wsrelayd

- start daemon
# service wsrelayd start

--------------
| for centos-6
--------------
- setup ius-repo and epel
# yum check-update
# yum install epel-release
# rpm -ivh https://centos6.iuscommunity.org/ius-release.rpm
# yum clean all
# yum check-update

- get source code
# yum install git2u
# git clone https://github.com/dictoss/websockettools.git
# cd websockettools

- install modules and librairies
# yum install python36u python36u-devel python36u-setuptools libffi-devel openssl-devel gcc make
# easy_install-3.6 pip
# pip3.6 install -r requirements.txt

- install
# mkdir -p /usr/local/wsrelayd
# cd <git clone dir>
# cd wsrelayd
# cp wsrelayd.py wsrelayd.ini /usr/local/wsrelayd/
# chmod 755 /usr/local/wsrelayd/wsrelayd.py
# cp init.d/wsrelayd.rhel /etc/init.d/wsrelayd
# chkconfig --add wsrelayd

- add user for daemon
# adduser wsrelay

- modify config
# vi /usr/local/wsrelayd/wsrelayd.ini
# vi /usr/local/wsrelayd/wsrelayd_user.ini

- make log directory
# mkdir /var/log/wsrelayd
# chown -fR wsrelay:wsrelay /var/log/wsrelayd

- start daemon
# service wsrelayd start


--------------
| for centos-7
--------------
- setup ius-repo and epel
# yum check-update
# yum install epel-release
# rpm -ivh https://centos7.iuscommunity.org/ius-release.rpm
# yum clean all
# yum check-update

- get source code
# yum install git2u
# git clone https://github.com/dictoss/websockettools.git
# cd websockettools

- install modules and librairies
# yum install python36u python36u-devel python36u-setuptools libffi-devel openssl-devel gcc make
# easy_install-3.6 pip
# pip3.6 install -r requirements.txt

- install
# mkdir -p /usr/local/wsrelayd
# cd <git clone dir>
# cd wsrelayd
# cp wsrelayd.py wsrelayd.ini wsrelayd_user.ini /usr/local/wsrelayd/
# chmod 755 /usr/local/wsrelayd/wsrelayd.py

- regist systemd
# cd <git clone dir>
# cd wsrelayd/init.d
# cp wsrelayd.service /usr/lib/systemd/system/
# systemctl daemon-reload
# systemctl status wsrelayd

- add user for daemon
# adduser wsrelay

- modify config
# vi /usr/local/wsrelayd/wsrelayd.ini
# vi /usr/local/wsrelayd/wsrelayd_user.ini

- make log directory
# mkdir /var/log/wsrelayd
# chown -fR wsrelay:wsrelay /var/log/wsrelayd

- start daemon
# systemctl start wsrelayd
