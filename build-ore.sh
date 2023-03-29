#!/bin/bash
# More of list of steps to follow than a script... but it should work, assuming you have a clean checkout of this repository.

set -x
ROOT_DIR=`pwd`
echo "Treating current directory as root dirctory for build: $ROOT_DIR"
mkdir --parents boost/root
mkdir bin
cd boost
wget https://boostorg.jfrog.io/artifactory/main/release/1.81.0/source/boost_1_81_0.tar.gz
tar -xf boost_1_81_0.tar.gz
cd boost_1_81_0
./bootstrap.sh --prefix=$ROOT_DIR/boost/root > bootstrap.log 2>&1
if [ $? -ne 0 ]; then
    echo "Bootstrap  of boost libraries failed"
    exit 1
fi

./b2 install > b2-install.log 2>&1
if [ $? -ne 0 ]; then
    echo "Build of boost libraries failed"
    exit 1
fi
echo "Build of boost libraries succeeded"

cd $ROOT_DIR
git clone --recurse-submodules https://github.com/hmxlabs/corex-bin.git
if [ $? -ne 0 ]; then
    echo "Failed to clone corex-bin repository"
    exit 1
fi
cd corex-bin
git checkout tags/v1.8.8.0
if [ $? -ne 0 ]; then
    echo "Failed to checkout tag v1.8.8.0 of corex-bin repository for build"
    exit 1
fi


cmake -DBOOST_ROOT=$ROOT_DIR/boost/root/include -DBOOST_LIBRARYDIR=$ROOT_DIR/boost/root/lib > cmake.log 2>&1
if [ $? -ne 0 ]; then
    echo "Failed to configure cmake for build"
    exit 1
fi

CPU_COUNT=`lscpu | grep "^CPU(s):" | awk '{print $2}'`
make -j$CPU_COUNT > make.log 2>&1
if [ $? -ne 0 ]; then
    echo "Failed to build ORE binaries"
    exit 1
fi
echo "Build of ORE binaries succeeded"