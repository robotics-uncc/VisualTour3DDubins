# build GLKH
curl -O http://webhotel4.ruc.dk/~keld/research/GLKH/GLKH-1.0.tgz
tar xvfz GLKH-1.0.tgz
rm GLKH-1.0.tgz
mv GLKH-1.0 ../subs/GLKH
cd ../subs/GLKH
make
cd ../../deploy

# build OpenGLDepthRenderer
cd ../subs/OpenGLDepthRenderer/
git submodule update --init --recursive
mkdir build
cd build
cmake ..
make
cd ../../../deploy

# install packages with conda
conda env create -n viewplanning --file ../environment.yaml
