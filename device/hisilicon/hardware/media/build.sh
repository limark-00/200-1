#!/bin/bash
# Copyright 2020-2020, Huawei Technologies Co. Ltd.
#
# ALL RIGHTS RESERVED
#
# Compile media/hal project, this is the entrance script

# error out on errors
set -e
OUT_DIR="$1"
BOARD_NAME="$2"
HOS_KERNEL_TYPE="$3"
HOS_BUILD_COMPILER="$4"

function main(){
    CUR_DIR=$(cd $(dirname "$0");pwd)
    unset OS_TYPE
    BUILD_COMPILER="llvm"
    if [ "$HOS_KERNEL_TYPE" = "liteos_a" ];then
        OS_TYPE="ohos"
    elif [ "$HOS_KERNEL_TYPE" = "linux" ];then
        OS_TYPE="linux"
    fi
    if [ "$HOS_BUILD_COMPILER" = "gcc" ];then
        BUILD_COMPILER="gcc"
    fi

    cp -rf $CUR_DIR/hal/audio/$BOARD_NAME/$BUILD_COMPILER/$OS_TYPE/libs/libaudio_hw.so $OUT_DIR/
    cp -rf $CUR_DIR/hal/audio/$BOARD_NAME/$BUILD_COMPILER/$OS_TYPE/libs/libaudio_input_port.so $OUT_DIR/
    cp -rf $CUR_DIR/hal/audio/$BOARD_NAME/$BUILD_COMPILER/$OS_TYPE/libs/libaudio_output_port.so $OUT_DIR/

    cp -rf $CUR_DIR/hal/codec/$BOARD_NAME/$BUILD_COMPILER/$OS_TYPE/libs/libcodec.so $OUT_DIR/
    cp -rf $CUR_DIR/hal/codec/$BOARD_NAME/$BUILD_COMPILER/$OS_TYPE/libs/libhiaacdec.so $OUT_DIR/
    cp -rf $CUR_DIR/hal/codec/$BOARD_NAME/$BUILD_COMPILER/$OS_TYPE/libs/libhimp3dec.so $OUT_DIR/
    cp -rf $CUR_DIR/hal/codec/$BOARD_NAME/$BUILD_COMPILER/$OS_TYPE/libs/libplugin_adec_35xx.so $OUT_DIR/
    cp -rf $CUR_DIR/hal/codec/$BOARD_NAME/$BUILD_COMPILER/$OS_TYPE/libs/libplugin_aenc_35xx.so $OUT_DIR/
    cp -rf $CUR_DIR/hal/codec/$BOARD_NAME/$BUILD_COMPILER/$OS_TYPE/libs/libplugin_vdec_35xx.so $OUT_DIR/
    cp -rf $CUR_DIR/hal/codec/$BOARD_NAME/$BUILD_COMPILER/$OS_TYPE/libs/libplugin_venc_35xx.so $OUT_DIR/

    cp -rf $CUR_DIR/hal/format/$BOARD_NAME/$BUILD_COMPILER/$OS_TYPE/libs/libformat_hw.so $OUT_DIR/
    cp -rf $CUR_DIR/hal/format/$BOARD_NAME/$BUILD_COMPILER/$OS_TYPE/libs/libplugin_demuxer_ffmpeg.so $OUT_DIR/
    cp -rf $CUR_DIR/hal/format/$BOARD_NAME/$BUILD_COMPILER/$OS_TYPE/libs/libplugin_demuxer_mpf.so $OUT_DIR/
    cp -rf $CUR_DIR/hal/format/$BOARD_NAME/$BUILD_COMPILER/$OS_TYPE/libs/libplugin_demuxer_raw.so $OUT_DIR/
    cp -rf $CUR_DIR/hal/format/$BOARD_NAME/$BUILD_COMPILER/$OS_TYPE/libs/libplugin_muxer_recorder.so $OUT_DIR/

    cp -rf $CUR_DIR/hal/common/$BOARD_NAME/$BUILD_COMPILER/$OS_TYPE/libs/libmedia_hal_common.so $OUT_DIR/

    cp -rf $CUR_DIR/hal/camera/$BOARD_NAME/$BUILD_COMPILER/$OS_TYPE/libs/libhdi_camera.so $OUT_DIR/
    cp -rf $CUR_DIR/hal/videodisplay/$BOARD_NAME/$BUILD_COMPILER/$OS_TYPE/libs/libhdi_videodisplayer.so $OUT_DIR/
}

main "$@"
