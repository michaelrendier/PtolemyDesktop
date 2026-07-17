#!/usr/bin/env bash
sudo apt-get install gcc automake autoconf libtool bison swig python-dev libpulse-dev subversion git
cd /home/rendier/Ptolemy/technical/sourcebuilds/
mkdir sphinx-source
cd sphinx-source

git clone https://github.com/cmusphinx/sphinxbase.git
cd sphinxbase
./autogen.sh
make
sudo make install
sudo echo '/usr/local/lib' >> /etc/ld.so.conf
sudo ldconfig
cd ..

git clone https://github.com/cmusphinx/pocketsphinx.git
cd pocketsphinx
./autogen.sh
make
sudo make install
cd ..

git clone https://github.com/cmusphinx/sphinxtrain.git
cd sphinxtrain
./autogen.sh
make
sudo make install
cd ..

svn checkout svn://svn.code.sf.net/p/cmusphinx/code/trunk cmusphinx-code
cd cmusphinx-code/cmuclmtk/
./autogen.sh
make
sudo make install
sudo pip3 install pocketsphinx
