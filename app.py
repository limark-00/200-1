# -*- coding:utf-8 -*-

"""
LabSafetyMonitor
实验室安全监测系统

Hi3861
 |
巴法云
 |
FastAPI
 |
Web Dashboard

"""


import os
import time
import random
import threading

from datetime import datetime
from collections import deque


from fastapi import FastAPI
from fastapi.responses import (
    HTMLResponse,
    StreamingResponse
)

from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel


import config
import bemfa_api



# 摄像头

try:

    import camera_stream

except:

    camera_stream=None






# ==================================================
# APP
# ==================================================


app=FastAPI(

    title="LabSafetyMonitor",

    version="1.0"

)






# ==================================================
# 静态目录
# ==================================================


if os.path.exists("static"):


    app.mount(

        "/static",

        StaticFiles(
            directory="static"
        ),

        name="static"

    )







# ==================================================
# 数据缓存
# ==================================================


history_data=deque(

    maxlen=config.HISTORY_SIZE

)





current_data={


    "temperature":0,

    "humidity":0,

    "gas":0,

    "light":0,

    "time":"--"

}





# ==================================================
# 模拟数据
# ==================================================


def mock_environment():


    return {


        "temperature":
        round(
            random.uniform(24,32),
            1
        ),


        "humidity":
        random.randint(
            40,75
        ),


        "gas":
        random.randint(
            80,250
        ),


        "light":
        random.randint(
            400,1000
        )


    }







# ==================================================
# 获取Hi3861数据
# ==================================================


def get_environment():


    if config.MOCK_MODE:


        return mock_environment()



    try:


        result=bemfa_api.get_topic_msg(

            config.ENV_PUB_TOPIC

        )


        msg=result.get(

            "msg",""

        )


        data=bemfa_api.parse_env_message(

            msg

        )



        return {


            "temperature":

            data.get(
                "temperature",
                0
            ),



            "humidity":

            data.get(
                "humidity",
                0
            ),



            "gas":

            data.get(
                "gas",
                0
            ),



            "light":

            data.get(
                "light",
                0
            )

        }



    except Exception as e:


        print(
            "读取设备失败:",
            e
        )


        return current_data








# ==================================================
# 更新数据
# ==================================================


def update_environment():


    global current_data



    env=get_environment()



    current_data={


        "temperature":
        env["temperature"],



        "humidity":
        env["humidity"],



        "gas":
        env["gas"],



        "light":
        env["light"],



        "time":
        datetime.now().strftime(
            "%H:%M:%S"
        )


    }



    history_data.append(

        current_data.copy()

    )


    return current_data







# ==================================================
# 后台采集线程
# ==================================================


def sensor_worker():


    print(
        "环境采集线程启动"
    )


    while True:


        try:


            data=update_environment()


            print(

                "实时数据:",
                data

            )


        except Exception as e:


            print(
                "采集错误:",
                e
            )


        time.sleep(2)










# ==================================================
# FastAPI启动
# ==================================================


@app.on_event("startup")

async def startup_event():


    threading.Thread(

        target=sensor_worker,

        daemon=True

    ).start()







# ==================================================
# 首页
# ==================================================


@app.get("/",
response_class=HTMLResponse)


async def index():


    path="templates/index.html"



    if os.path.exists(path):


        return open(

            path,

            encoding="utf-8"

        ).read()



    return "<h1>LabSafetyMonitor</h1>"








# ==================================================
# 图表页面
# ==================================================


@app.get("/chart.html",
response_class=HTMLResponse)


async def chart_page():


    path="templates/chart.html"


    if os.path.exists(path):


        return open(

            path,

            encoding="utf-8"

        ).read()



    return "chart不存在"








# ==================================================
# 当前数据
# ==================================================


@app.get("/api/env")


async def api_env():


    return {


        "ok":True,

        "data":current_data


    }








# ==================================================
# 历史曲线
# ==================================================


@app.get("/api/history")


async def history():


    return {


        "ok":True,

        "data":
        list(history_data)


    }







# ==================================================
# 安全分析
# ==================================================


@app.get("/api/analyse")


async def analyse():


    if not history_data:


        return {


            "ok":False,

            "message":"暂无数据"

        }



    data=history_data[-1]



    warning=[]



    if float(data["temperature"])>config.TEMP_MAX:


        warning.append(
            "温度超过阈值"
        )



    if float(data["humidity"])>config.HUM_MAX:


        warning.append(
            "湿度超过阈值"
        )



    if float(data["gas"])>config.GAS_MAX:


        warning.append(
            "气体超标"
        )



    if float(data["light"])>config.LIGHT_MAX:


        warning.append(
            "光照异常"
        )




    return {


        "ok":True,


        "safe":
        len(warning)==0,


        "warning":
        warning,


        "threshold":{


            "temperature":
            config.TEMP_MAX,


            "humidity":
            config.HUM_MAX,


            "gas":
            config.GAS_MAX,


            "light":
            config.LIGHT_MAX

        }


    }










# ==================================================
# 控制命令
# ==================================================


class Message(BaseModel):


    msg:str






@app.post("/api/env/send")


async def send_message(

    message:Message

):


    try:


        result=bemfa_api.send_msg(

            config.ENV_TOPIC,

            message.msg

        )


        return {


            "ok":True,

            "result":result

        }



    except Exception as e:


        return {


            "ok":False,

            "error":str(e)

        }









# ==================================================
# 摄像头
# ==================================================

@app.get("/camera")
async def camera():


    if not config.ENABLE_CAMERA:


        return {
            "error":
            "camera disabled"
        }



    if camera_stream is None:


        return {
            "error":
            "camera_stream加载失败"
        }



    return StreamingResponse(


        camera_stream.generate_frames(),


        media_type=
        "multipart/x-mixed-replace; boundary=frame"


    )





# ==================================================
# 启动
# ==================================================


if __name__=="__main__":


    import uvicorn



    print("======================")

    print(
        "LabSafetyMonitor Running"
    )


    print(

        f"http://127.0.0.1:{config.APP_PORT}"

    )


    print("======================")



    uvicorn.run(

        app,

        host=config.APP_HOST,

        port=config.APP_PORT

    )