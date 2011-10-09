#!/bin/bash

GIT_DIR=/home/ubuntu/git/appsforsepta

aptitude install -y \
    build-essential \
    libevent-dev \
    libxml2-dev \
    libxslt1-dev \
    nginx-full \
    python-dev \
    python-pip \
    runit

# Python packages
pip install greenlet
pip install cherrypy gevent lxml pytz
HOME=/root/ pip install ipython # requires $HOME for soem reason

# Hokey launch of uwsgi
# nohup uwsgi --socket 127.0.0.1:3031 --chdir /home/ubuntu --pp .. -w app_wsgi \
#     &> /tmp/wsgi.log </dev/null &

# Nginx configuration
cat > /etc/nginx/sites-enabled/default <<EOF
server {
    listen       80;
    root         /usr/share/nginx/www;
    location /app/ {
        proxy_pass http://localhost:8000/;
    }
}
EOF
service nginx restart

ln -s $GIT_DIR/deployment/service/cherrpy /etc/service/cherrpy