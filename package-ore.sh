#!/bin/bash

# Copy the ORE binaries to the bin directory


ROOT_DIR=`pwd`
if [ ! -d bin ]; then
    echo "Creating bin directory"
    mkdir --parents $ROOT_DIR/bin
fi

echo "Copying ORE binaries to bin directory"
cp $ROOT_DIR/corex-bin/App/ore $ROOT_DIR/bin
cp $ROOT_DIR/corex-bin/OREAnalytics/orea/libOREAnalytics.so $ROOT_DIR/bin
cp $ROOT_DIR/corex-bin/QuantExt/qle/libQuantExt.so $ROOT_DIR/bin
cp $ROOT_DIR/corex-bin/OREData/ored/libOREData.so $ROOT_DIR/bin
cp $ROOT_DIR/corex-bin/QuantLib/ql/libQuantLib.so $ROOT_DIR/bin
cp $ROOT_DIR/corex-bin/QuantLib/ql/libQuantLib.so.1 $ROOT_DIR/bin
cp $ROOT_DIR/corex-bin/license.txt $ROOT_DIR/bin/ore-license.txt

echo "Copying boost libraries to bin directory"
cp $ROOT_DIR/boost/root/lib/* $ROOT_DIR/bin

echo "Creating tarball of ORE binaries"
cd $ROOT_DIR/bin
tar -czf corex-bin-boost.tar.gz *
cd $ROOT_DIR
mv $ROOT_DIR/bin/corex-bin-boost.tar.gz $ROOT_DIR
echo "Packaging of ORE binaries complete"