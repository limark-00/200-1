# -*- coding:utf-8 -*-

"""
camera_stream.py

实验室安全监测系统实时摄像头

功能：
1. 支持USB外接摄像头
2. 自动检测摄像头编号
3. 优先使用config.py配置
4. 输出MJPEG视频流给FastAPI
"""


import cv2
import time
import config



# ================================
# 摄像头对象
# ================================

camera = None



# ================================
# 摄像头编号
# ================================


def find_camera():

    """
    自动寻找可用摄像头

    优先:
    config.CAMERA_INDEX

    """

    index_list = [

        config.CAMERA_INDEX,

        0,
        1,
        2,
        3

    ]


    checked=[]


    for index in index_list:


        if index in checked:

            continue


        checked.append(index)


        cap=cv2.VideoCapture(

            index,

            cv2.CAP_DSHOW

        )


        if cap.isOpened():


            print(

                "找到摄像头:",
                index

            )


            cap.release()


            return index



        cap.release()



    print(

        "没有找到摄像头"

    )


    return -1







# ================================
# 初始化摄像头
# ================================


def get_camera():


    global camera



    if camera is None:


        index=find_camera()



        if index==-1:


            return None



        camera=cv2.VideoCapture(

            index,

            cv2.CAP_DSHOW

        )



        # 设置分辨率


        camera.set(

            cv2.CAP_PROP_FRAME_WIDTH,

            getattr(

                config,

                "CAMERA_WIDTH",

                1280

            )

        )


        camera.set(

            cv2.CAP_PROP_FRAME_HEIGHT,

            getattr(

                config,

                "CAMERA_HEIGHT",

                720

            )

        )



        # FPS

        camera.set(

            cv2.CAP_PROP_FPS,

            30

        )



    return camera







# ================================
# MJPEG视频流
# ================================


def generate_frames():


    cap=get_camera()



    if cap is None:


        print(

            "摄像头初始化失败"

        )


        return



    while True:



        if not cap.isOpened():


            print(

                "摄像头断开"

            )


            time.sleep(2)


            break





        success,frame=cap.read()



        if not success:


            time.sleep(0.05)

            continue





        # 镜像显示

        frame=cv2.flip(

            frame,

            1

        )




        # JPEG编码


        ret,buffer=cv2.imencode(

            ".jpg",

            frame,

            [

                cv2.IMWRITE_JPEG_QUALITY,

                80

            ]

        )



        if not ret:


            continue





        frame_bytes=buffer.tobytes()



        yield (


            b"--frame\r\n"


            b"Content-Type: image/jpeg\r\n\r\n"


            +

            frame_bytes


            +

            b"\r\n"



        )







# ================================
# 释放摄像头
# ================================


def release_camera():


    global camera



    if camera:


        camera.release()


        camera=None