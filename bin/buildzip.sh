#!/bin/bash
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
if [ -z $1 ]
then
    ZIPFile="$SCRIPTDIR/../mypkg.zip"
else
    ZIPFile="$SCRIPTDIR/../$1"
fi
ZIPFile="$(realpath "$ZIPFile")"

pushd $SCRIPTDIR/.. > /dev/null
# Lambda comes with boto3 and others
# lambdarequirements only packages other things
pip install -r $LAMBDAFOLDER/lambdarequirements.txt --target ./package
cd package
zip -r $ZIPFile .
cd ../$LAMBDAFOLDER
zip -rg $ZIPFile .
cd ..
rm -rf package