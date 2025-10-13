#!/bin/bash

if [[ "$OSTYPE" == "darwin"* ]]; then
        export ARTHOME=$PWD/src/acpcdetect_V2.2_macOS_Sierra_10.12.6
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        export ARTHOME=$PWD/src/acpcdetect_V2.2_Linux_x86_64_Ubuntu_22.04.01
elif [[ "$OSTYPE" == "cygwin" ]]; then
        export ARTHOME=$PWD/src/acpcdetect_V2.2_Linux_x86_64_Ubuntu_22.04.01
fi

export PATH=$ARTHOME/bin:$PATH

DO_ZIP=false

while getopts i:z flag
do
    case "${flag}" in
        i) IN_FILE=${OPTARG};;
    esac
done

FILE_NAME=${IN_FILE%%.*}
FILE_LAST_EXT=${IN_FILE##*.}

if [[ "$FILE_LAST_EXT" == "gz" ]]; 
then
        gzip -d -k ${IN_FILE}
        UNZIP_FILE=${FILE_NAME}".nii"
        acpcdetect -i ${UNZIP_FILE} -nopng -rvsps 30
        rm ${UNZIP_FILE}
        ACPC_FILE=${FILE_NAME}"_RAS.nii"
        gzip ${ACPC_FILE}
else
        acpcdetect -i ${IN_FILE} -nopng -rvsps 30
fi

