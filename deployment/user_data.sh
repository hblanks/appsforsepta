#!/bin/bash

GIT_DIR=/home/ubuntu/git/appsforsepta

aptitude -y install screen git

mkdir -p $GIT_DIR
git clone git://github.com/hblanks/appsforsepta.git $GIT_DIR

(cd $GIT_DIR/deployment; ./install.sh) &> /tmp/install.log