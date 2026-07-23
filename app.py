# -*- coding:utf-8 -*-

"""
LabSafetyMonitor

实验室安全检测系统

FastAPI最终版

功能:

1. 首页
2. 温度检测
3. 湿度检测
4. 气体检测
5. 光照检测
6. 摄像头管理
7. YOLO人数检测
8. MJPEG视频流
9. 用户信息

"""


# ==================================================
# 导入
# ==================================================

from fastapi import FastAPI, Request

from fastapi.responses import StreamingResponse

from fastapi.staticfiles import StaticFiles

from fastapi.templating import Jinja2Templates


from contextlib import asynccontextmanager


import random

import time

import threading







# ==================================================
# 摄像头模块
# ==================================================

try:


    import camera_stream


    print(
        "camera_stream加载成功"
    )


except Exception as e:


    print(
        "camera_stream加载失败:",
        e
    )


    camera_stream=None










# ==================================================
# YOLO模块
# ==================================================

try:


    import yolo_detect


    print(
        "yolo_detect加载成功"
    )


except Exception as e:


    print(
        "yolo_detect加载失败:",
        e
    )


    yolo_detect=None











# ==================================================
# 用户信息
# ==================================================

USER_INFO={


    "username":

    "admin",



    "nickname":

    "管理员",



    "role":

    "系统管理员",



    "avatar":

    "/static/user.png"


}









# ==================================================
# 数据缓存
# ==================================================

history={


    "temperature":[],


    "humidity":[],


    "gas":[],


    "light":[]


}



time_history=[]











# ==================================================
# 安全阈值
# ==================================================

LIMIT={


    "temperature":

    28,



    "humidity":

    70,



    "gas":

    200,



    "light":

    800


}













# ==================================================
# 生命周期
# ==================================================

@asynccontextmanager

async def lifespan(app:FastAPI):



    print()


    print("==============================")

    print(" LabSafetyMonitor Running ")

    print(" http://127.0.0.1:5001 ")

    print("==============================")


    print()







    # --------------------------
    # 启动摄像头
    # --------------------------


    if camera_stream:


        try:


            thread=threading.Thread(


                target=camera_stream.get_camera,


                daemon=True


            )


            thread.start()



            print(

                "摄像头检测线程启动"

            )



        except Exception as e:



            print(

                "摄像头启动失败:",

                e

            )








    # 不再启动 yolo_detect

    # 防止YOLO重复加载

    print(

        "YOLO使用camera_stream实时检测"

    )







    yield







    # --------------------------
    # 关闭
    # --------------------------


    print()


    print(

        "LabSafetyMonitor关闭"

    )




    if camera_stream:


        try:


            camera_stream.release_camera()



            print(

                "摄像头已释放"

            )


        except Exception as e:


            print(

                "摄像头释放失败:",

                e

            )













# ==================================================
# FastAPI
# ==================================================

app=FastAPI(


    title="LabSafetyMonitor",


    lifespan=lifespan


)












# ==================================================
# 静态资源
# ==================================================

app.mount(


    "/static",


    StaticFiles(

        directory="static"

    ),


    name="static"


)











# ==================================================
# 模板
# ==================================================

templates=Jinja2Templates(


    directory="templates"


)














# ==================================================
# 首页
# ==================================================

@app.get("/")

async def index(request:Request):


    return templates.TemplateResponse(


        request=request,


        name="index.html",


        context={

            "user":USER_INFO

        }


    )














# ==================================================
# 温度检测
# ==================================================

@app.get("/temperature.html")

async def temperature_page(request:Request):


    return templates.TemplateResponse(


        request=request,


        name="temperature.html",


        context={

            "user":USER_INFO

        }


    )











# ==================================================
# 湿度检测
# ==================================================

@app.get("/humidity.html")

async def humidity_page(request:Request):


    return templates.TemplateResponse(


        request=request,


        name="humidity.html",


        context={

            "user":USER_INFO

        }


    )












# ==================================================
# 气体检测
# ==================================================

@app.get("/gas.html")

async def gas_page(request:Request):


    return templates.TemplateResponse(


        request=request,


        name="gas.html",


        context={

            "user":USER_INFO

        }


    )












# ==================================================
# 光照检测
# ==================================================

@app.get("/light.html")

async def light_page(request:Request):


    return templates.TemplateResponse(


        request=request,


        name="light.html",


        context={

            "user":USER_INFO

        }


    )













# ==================================================
# 摄像头页面
# ==================================================

@app.get("/camera.html")

async def camera_page(request:Request):


    return templates.TemplateResponse(


        request=request,


        name="camera.html",


        context={

            "user":USER_INFO

        }


    )














# ==================================================
# 个人信息页面
# ==================================================

@app.get("/profile.html")

async def profile_page(request:Request):


    return templates.TemplateResponse(


        request=request,


        name="profile.html",


        context={

            "user":USER_INFO

        }


    )
# ==================================================
# 用户信息接口
# ==================================================

@app.get("/api/user")

async def user_info():


    return {


        "ok":True,


        "user":USER_INFO


    }













# ==================================================
# 环境实时数据接口
# ==================================================

@app.get("/api/env")

async def environment():



    data={


        "temperature":

        round(

            random.uniform(

                20,

                32

            ),

            1

        ),



        "humidity":

        round(

            random.uniform(

                40,

                80

            ),

            1

        ),




        "gas":

        round(

            random.uniform(

                50,

                250

            ),

            2

        ),




        "light":

        round(

            random.uniform(

                300,

                1000

            ),

            1

        )



    }







    now=time.strftime(

        "%H:%M:%S"

    )







    time_history.append(now)







    for key in history:


        history[key].append(

            data[key]

        )








    # 保存最近100条


    if len(time_history)>100:



        time_history.pop(0)



        for key in history:


            history[key].pop(0)









    return {


        "ok":True,


        "data":data


    }














# ==================================================
# 历史数据
# ==================================================

@app.get("/api/history")

async def get_history():



    return {


        "ok":True,


        "labels":

        time_history,



        "data":

        history,



        "limit":

        LIMIT


    }














# ==================================================
# 摄像头视频流
# ==================================================

@app.get("/camera")

async def camera_stream_route():



    if camera_stream is None:



        return {


            "error":

            "camera module unavailable"


        }







    return StreamingResponse(



        camera_stream.generate_frames(),



        media_type=


        "multipart/x-mixed-replace; boundary=frame"



    )













# ==================================================
# 摄像头状态
# ==================================================

@app.get("/api/camera/info")

async def camera_info():



    result={


        "ok":True,


        "connected":False,


        "camera_index":-1,


        "people":0,


        "fps":0,


        "safe":True


    }







    try:



        if camera_stream:



            info=camera_stream.get_camera_info()





            result["connected"]=info.get(

                "connected",

                False

            )



            result["camera_index"]=info.get(

                "index",

                -1

            )



            result["people"]=info.get(

                "people",

                0

            )



            result["fps"]=info.get(

                "fps",

                0

            )








        # 人数安全判断


        if result["people"]>20:


            result["safe"]=False







    except Exception as e:



        result={


            "ok":False,


            "error":str(e)


        }







    return result













# ==================================================
# YOLO人数接口
# ==================================================

@app.get("/api/yolo/people")

async def yolo_people():



    people=0







    try:



        if camera_stream:



            info=camera_stream.get_camera_info()



            people=info.get(


                "people",


                0


            )




    except Exception as e:



        print(

            "YOLO人数读取失败:",

            e

        )








    return {


        "ok":True,


        "people":people



    }












# ==================================================
# 安全状态检测
# ==================================================

@app.get("/api/security")

async def security():



    safe=True



    message="环境正常"






    try:



        if history["temperature"]:



            temperature=history["temperature"][-1]


            humidity=history["humidity"][-1]


            gas=history["gas"][-1]


            light=history["light"][-1]







            if temperature > LIMIT["temperature"]:



                safe=False


                message="温度超过安全阈值"





            elif humidity > LIMIT["humidity"]:



                safe=False


                message="湿度超过安全阈值"





            elif gas > LIMIT["gas"]:



                safe=False


                message="气体浓度异常"





            elif light > LIMIT["light"]:



                safe=False


                message="光照超过安全阈值"







    except Exception as e:



        print(

            "安全检测错误:",

            e

        )







    return {


        "ok":True,


        "safe":safe,


        "message":message



    }
# ==================================================
# 启动事件
# ==================================================

@app.on_event("startup")

async def startup_event():



    print()

    print("==============================")

    print(" LabSafetyMonitor Running ")

    print(" http://127.0.0.1:5001 ")

    print("==============================")

    print()







    # ==============================================
    # 启动摄像头
    # ==============================================


    if camera_stream:



        try:



            camera_thread=threading.Thread(



                target=camera_stream.get_camera,



                daemon=True



            )




            camera_thread.start()



            print(

                "摄像头检测线程启动"

            )




        except Exception as e:



            print(

                "摄像头启动失败:",

                e

            )









    # ==============================================
    # YOLO
    # ==============================================


    if yolo_detect:



        try:



            if hasattr(

                yolo_detect,

                "start_detect"

            ):



                yolo_thread=threading.Thread(



                    target=yolo_detect.start_detect,



                    daemon=True



                )




                yolo_thread.start()



                print(

                    "YOLO检测线程启动"

                )





            else:



                print(

                    "YOLO使用camera_stream实时检测"

                )






        except Exception as e:



            print(

                "YOLO启动失败:",

                e

            )













# ==================================================
# 关闭事件
# ==================================================

@app.on_event("shutdown")

async def shutdown_event():



    print()


    print(

        "LabSafetyMonitor关闭"

    )





    # ==============================================
    # 释放摄像头
    # ==============================================


    if camera_stream:



        try:



            if hasattr(

                camera_stream,

                "release_camera"

            ):



                camera_stream.release_camera()





            print(

                "摄像头已释放"

            )





        except Exception as e:



            print(

                "摄像头释放失败:",

                e

            )














# ==================================================
# 程序入口
# ==================================================

if __name__=="__main__":



    import uvicorn






    uvicorn.run(



        app,



        host="0.0.0.0",



        port=5001



    )