/*
=================================================
LabSafetyMonitor

首页控制脚本

功能：

1. 获取环境数据
2. 更新首页四个传感器卡片
3. 更新数据表
4. 安全判断
5. 页面跳转

=================================================
*/



// =================================================
// 页面跳转
// =================================================


function goPage(url){


    window.location.href=url;


}






// =================================================
// 打开个人信息
// =================================================


function openProfile(){


    window.location.href="/profile.html";


}









// =================================================
// 获取环境数据
// =================================================


async function getEnvironment(){



    try{


        let response = await fetch(

            "/api/env"

        );



        let result = await response.json();




        if(result.ok){



            let data=result.data;






            // =========================
            // 四个主页卡片
            // =========================



            document.getElementById(
                "temperature"
            ).innerHTML=
            data.temperature;



            document.getElementById(
                "humidity"
            ).innerHTML=
            data.humidity;



            document.getElementById(
                "gas"
            ).innerHTML=
            data.gas;



            document.getElementById(
                "light"
            ).innerHTML=
            data.light;







            // =========================
            // 数据表
            // =========================


            document.getElementById(
                "tableTemp"
            ).innerHTML=
            data.temperature+" ℃";




            document.getElementById(
                "tableHum"
            ).innerHTML=
            data.humidity+" %";




            document.getElementById(
                "tableGas"
            ).innerHTML=
            data.gas+" %LEL";




            document.getElementById(
                "tableLight"
            ).innerHTML=
            data.light+" Lux";









            // =========================
            // 安全判断
            // =========================


            checkSafety(data);





        }



    }
    catch(error){


        console.log(

            "环境数据获取失败:",
            error

        );


    }


}









// =================================================
// 安全检测
// =================================================


function checkSafety(data){



    let alarm=
    document.getElementById(
        "alarm"
    );



    let score=
    document.getElementById(
        "score"
    );




    let danger=false;



    let message=[];





    // 温度


    if(
        data.temperature>28
    ){


        danger=true;


        message.push(
            "温度过高"
        );


    }






    // 湿度


    if(
        data.humidity>70
    ){


        danger=true;


        message.push(
            "湿度异常"
        );


    }







    // 气体


    if(
        data.gas>200
    ){


        danger=true;


        message.push(
            "气体浓度超标"
        );


    }







    // 光照


    if(
        data.light>800
    ){


        danger=true;


        message.push(
            "光照异常"
        );


    }









    if(danger){



        alarm.innerHTML=


        "⚠ "+message.join("、");



        alarm.style.color=

        "#dc2626";





        score.innerHTML=

        "70分";



    }

    else{



        alarm.innerHTML=


        "🟢 当前环境安全";



        alarm.style.color=

        "#16a34a";



        score.innerHTML=

        "100分";



    }



}











// =================================================
// 自动刷新
// =================================================


getEnvironment();



setInterval(


    getEnvironment,


    2000


);
