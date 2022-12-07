#!/bin/bash
apt-get update
# dependencies for glkh and robust dubins
apt-get install -y curl libopenblas-dev
pip install cmake
curl -O http://webhotel4.ruc.dk/~keld/research/GLKH/GLKH-1.0.tgz
tar xvfz GLKH-1.0.tgz
rm GLKH-1.0.tgz
mkdir ../subs/GLKH
mv GLKH-1.0 ../subs/GLKH
cd ../subs/GLKH
make
cd ../../deploy

# build OpenGLDepthRenderer
apt-get install -y libglm-dev libglfw3-dev libassimp-dev libsoil-dev libglew-dev libpng-dev libxinerama-dev libxi-dev libxxf86vm-dev libxcursor-dev libfreetype-dev
pwd
mkdir ../subs/OpenGLDepthRenderer/build
cd ../subs/OpenGLDepthRenderer/build
cmake ..
make
cd ../../../deploy

# install packages with conda
conda env create -n viewplanning --file ../environment.yaml

#clean up
rm -rf GLKH-1.0
