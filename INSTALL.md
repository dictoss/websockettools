# Installation

## for debian-9 (stretch)

- install modules and librairies
    # apt-get install python3.5
    # apt-get install python3-pip python3-dev libffi-dev libssl-dev

- get source code
    # apt-get git
    # git clone https://github.com/dictoss/websockettools.git
    # cd websockettools

- install modules and librairies
    # apt-get install python3-txaio python3-autobahn
    # pip3 install -r requirements.txt

- install
    # mkdir -p /usr/local/wsrelayd
    # cd <git clone dir>
    # cd wsrelayd
    # cp wsrelayd.py wsrelayd.ini wsrelayd_user.ini /usr/local/wsrelayd/
    # chmod 755 /usr/local/wsrelayd/wsrelayd.py
    # cp init.d/wsrelayd.service.debian9 /etc/systemd/system/wsrelayd.service
    # systemctl daemon-reload
    # systemctl status wsrelayd

- modify config
    # vi /usr/local/wsrelayd/wsrelayd.ini
    # vi /usr/local/wsrelayd/wsrelayd_user.ini

- make log directory
    # mkdir /var/log/wsrelayd
    # chown -fR nobody:nogroup /var/log/wsrelayd

- start daemon
    # systemctl start wsrelayd


## for centos-6

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
    # cp init.d/wsrelayd.rhel6 /etc/init.d/wsrelayd
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


## for centos-7

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
    # cp wsrelayd.service.rhel7 /usr/lib/systemd/system/wsrelayd.service
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
