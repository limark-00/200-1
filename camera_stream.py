# -*- coding:utf-8 -*-

"""
camera_stream.py

LabSafetyMonitor 摄像头模块

功能:

1. 自动寻找摄像头
2. USB摄像头优先
3. MJPEG视频流
4. YOLOv8实时检测
5. 人员检测
6. 人数统计
7. FPS显示
8. 提供摄像头状态接口


说明:

YOLO模型唯一加载位置

"""


import cv2

import time

import threading



# ==================================================
# 人数同步模块
# ==================================================

import yolo_detect







# ==================================================
# YOLO模型
# ==================================================


try:


    from ultralytics import YOLO



    yolo_model = YOLO(

        "yolov8n.pt"

    )



    print(

        "YOLO模型加载成功"

    )



except Exception as e:



    print(

        "YOLO加载失败:",

        e

    )



    yolo_model=None







# ==================================================
# 摄像头列表
# ==================================================


CAMERA_LIST=[


    1,      # USB摄像头优先


    0,      # 内置摄像头


    2,


    3


]








# ==================================================
# 全局变量
# ==================================================


camera=None



camera_index=None



camera_lock=threading.Lock()





# 人数

people_count=0



# FPS

fps=0










# ==================================================
# 查找摄像头
# ==================================================


def find_camera():


    global camera_index



    print(

        "正在检测摄像头..."

    )



    for index in CAMERA_LIST:



        try:



            cap=cv2.VideoCapture(


                index,


                cv2.CAP_DSHOW


            )



            time.sleep(0.5)





            if cap.isOpened():



                ret,frame=cap.read()



                if ret:



                    camera_index=index



                    print(

                        "摄像头连接成功:",

                        index

                    )



                    return cap





            cap.release()



        except Exception as e:



            print(

                "摄像头检测失败:",

                e

            )







    print(

        "没有找到摄像头"

    )



    return None












# ==================================================
# 获取摄像头
# ==================================================


def get_camera():


    global camera



    with camera_lock:



        if camera is None:



            camera=find_camera()



        return camera











# ==================================================
# 释放摄像头
# ==================================================


def release_camera():


    global camera



    with camera_lock:



        if camera:



            camera.release()



        camera=None













# ==================================================
# YOLO检测
# ==================================================


def detect(frame):


    global people_count



    if yolo_model is None:



        return frame





    try:



        results=yolo_model(


            frame,


            verbose=False


        )



        count=0





        for r in results:



            boxes=r.boxes





            for box in boxes:



                cls=int(

                    box.cls[0]

                )



                conf=float(

                    box.conf[0]

                )





                # COCO类别0 = person


                if cls==0 and conf>0.5:



                    count+=1





                    x1,y1,x2,y2=map(


                        int,


                        box.xyxy[0]


                    )






                    # 绘制框


                    cv2.rectangle(


                        frame,


                        (x1,y1),


                        (x2,y2),


                        (0,255,0),


                        2


                    )






                    cv2.putText(


                        frame,


                        "person",


                        (x1,y1-10),


                        cv2.FONT_HERSHEY_SIMPLEX,


                        0.7,


                        (0,255,0),


                        2


                    )







        people_count=count





        # ===========================
        # 同步给 yolo_detect
        # ===========================


        try:



            yolo_detect.set_people(


                count


            )



        except Exception as e:



            print(

                "人数同步失败:",

                e

            )







    except Exception as e:



        print(

            "YOLO检测错误:",

            e

        )






    return frame











# ==================================================
# MJPEG视频流
# ==================================================


def generate_frames():


    global fps



    last=time.time()





    while True:




        cap=get_camera()




        if cap is None:



            time.sleep(3)


            continue






        success,frame=cap.read()




        if not success:



            print(

                "读取失败"

            )


            release_camera()


            continue








        # 镜像


        frame=cv2.flip(


            frame,


            1


        )






        # YOLO检测


        frame=detect(


            frame


        )






        # FPS


        now=time.time()



        if now-last!=0:



            fps=int(


                1/(now-last)


            )



        last=now







        # 左上角显示


        cv2.putText(


            frame,


            f"People:{people_count}",


            (20,40),


            cv2.FONT_HERSHEY_SIMPLEX,


            1,


            (255,0,0),


            2


        )







        cv2.putText(


            frame,


            f"FPS:{fps}",


            (20,80),


            cv2.FONT_HERSHEY_SIMPLEX,


            1,


            (255,0,0),


            2


        )







        # 调整大小


        frame=cv2.resize(


            frame,


            (1280,720)


        )








        ret,buffer=cv2.imencode(


            ".jpg",


            frame


        )




        if not ret:


            continue







        jpg=buffer.tobytes()






        yield (



            b"--frame\r\n"


            b"Content-Type: image/jpeg\r\n\r\n"


            + jpg +


            b"\r\n"



        )





        time.sleep(0.03)













# ==================================================
# 摄像头状态接口
# app.py调用
# ==================================================


def get_camera_info():


    return {



        "connected":

        camera is not None,



        "index":

        camera_index,



        "people":

        people_count,



        "fps":

        fps


    }













# ==================================================
# 测试
# ==================================================


if __name__=="__main__":



    for frame in generate_frames():


        pass