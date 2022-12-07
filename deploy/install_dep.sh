#!/bin/bash
apt-get update
# dependencies for glkh
apt-get install -y curl libopenblas-dev cmake gcc make
# dependencies for opengldepthrenderer
apt-get install -y libglm-dev libglfw3-dev libassimp-dev libsoil-dev libglew-dev libpng-dev libxinerama-dev libxi-dev libxxf86vm-dev libxcursor-dev libfreetype-dev
