// =====================================================
// LabSafetyMonitor
// 前端主控制程序
// =====================================================


// 刷新周期

const REFRESH_TIME = 5000;



// 安全阈值

const LIMIT = {

    temperature:30,

    humidity:70,

    gas:200,

    light:1000

};




// =====================================================
// 页面加载
// =====================================================


window.onload=function(){


    updateClock();


    setInterval(
        updateClock,
        1000
    );


    loadEnvironment();


    setInterval(
        loadEnvironment,
        REFRESH_TIME
    );



};




// =====================================================
// 数字时钟
// =====================================================


function updateClock(){


    let now=new Date();


    let time=
        now.toLocaleTimeString(
            "zh-CN",
            {
                hour12:false
            }
        );


    let clock=
        document.getElementById(
            "clock"
        );


    if(clock){

        clock.innerHTML=time;

    }


}







// =====================================================
// 获取环境数据
// =====================================================


async function loadEnvironment(){


try{


    let res=
        await fetch(
            "/api/env"
        );


    let result=
        await res.json();



    console.log(
        result
    );



    if(
        result.ok
    ){


        let data=result.data;


        updateData(data);



        onlineState(true);



    }
    else{


        onlineState(false);


    }



}
catch(e){


    console.error(
        e
    );


    onlineState(false);



}



}









// =====================================================
// 更新页面数据
// =====================================================


function updateData(data){



    // 温度

    setText(
        "temperatureValue",
        data.temperature
    );



    // 湿度

    setText(
        "humidityValue",
        data.humidity
    );



    // 气体

    setText(
        "gasValue",
        data.gas
    );



    // 光照

    setText(
        "lightValue",
        data.light
    );






    //设备信息


    setText(
        "deviceIdValue",
        data.deviceId || "--"
    );



    setText(
        "groupIdValue",
        data.groupId || "--"
    );



    setText(
        "refreshTimeValue",
        new Date()
        .toLocaleString()
    );





    // 保存风险判断


    checkSafety(data);






    // 原始数据


    let raw=
        document.getElementById(
            "rawData"
        );


    if(raw){


        raw.innerHTML=
        JSON.stringify(
            data,
            null,
            4
        );

    }




}






function setText(id,value){


    let obj=
        document.getElementById(id);


    if(obj){

        if(value===undefined||
           value===null||
           value===""){


            obj.innerHTML="--";

        }
        else{


            obj.innerHTML=value;


        }

    }


}










// =====================================================
// 安全检测
// =====================================================


function checkSafety(data){



let level="正常";

let reason="环境参数正常";



let danger=false;

let warning=false;



// 温度


if(
Number(data.temperature)
>
LIMIT.temperature
){

    warning=true;

    reason=
    "温度超过安全阈值";

}





// 湿度


if(
Number(data.humidity)
>
LIMIT.humidity
){

    warning=true;

    reason=
    "湿度超过安全阈值";

}





// 气体


if(
Number(data.gas)
>
LIMIT.gas
){

    danger=true;

    reason=
    "气体浓度超标";

}






// 光照


if(
Number(data.light)
>
LIMIT.light
){

    warning=true;

    reason=
    "光照异常";

}





let badge=
document.getElementById(
"riskBadge"
);



let reasonBox=
document.getElementById(
"riskReason"
);





if(
danger
){


    level="危险";


    badge.className=
    "risk-badge danger";


}
else if(
warning
){


    level="预警";


    badge.className=
    "risk-badge warning";


}
else{


    badge.className=
    "risk-badge";


}




if(badge){

    badge.innerHTML=
    level;

}



if(reasonBox){

    reasonBox.innerHTML=
    reason;

}





// 卡片颜色


changeCard(
"temperatureCard",
Number(data.temperature),
LIMIT.temperature
);


changeCard(
"humidityCard",
Number(data.humidity),
LIMIT.humidity
);



changeCard(
"gasCard",
Number(data.gas),
LIMIT.gas
);



changeCard(
"lightCard",
Number(data.light),
LIMIT.light
);



}









// =====================================================
// 卡片颜色变化
// =====================================================


function changeCard(
id,
value,
limit
){



let card=
document.getElementById(id);



if(!card)
return;



card.classList.remove(
"warning",
"danger"
);



if(
value>limit
){


    card.classList.add(
        "danger"
    );


}


else if(
value>limit*0.8
){


    card.classList.add(
        "warning"
    );


}



}










// =====================================================
// 巴法云状态
// =====================================================


function onlineState(state){



let dot=
document.getElementById(
"stateDot"
);



let text=
document.getElementById(
"cloudStateText"
);



let connect=
document.getElementById(
"connectionValue"
);



if(state){



dot.className=
"state-dot online";


text.innerHTML=
"巴法云在线";


if(connect)

connect.innerHTML=
"在线";



}
else{


dot.className=
"state-dot offline";


text.innerHTML=
"连接失败";


if(connect)

connect.innerHTML=
"离线";


}



}









// =====================================================
// 点击传感器进入分析页面
// =====================================================


function openChart(type){



window.location.href=
"/chart.html?type="
+
type;



}









// =====================================================
// 手动刷新按钮
// =====================================================


let refresh=
document.getElementById(
"refreshButton"
);



if(refresh){


refresh.onclick=function(){


    loadEnvironment();


};


}









// =====================================================
// 发送控制命令
// =====================================================


let sendBtn=
document.getElementById(
"sendButton"
);



if(sendBtn){


sendBtn.onclick=
function(){


let msg=
document.getElementById(
"messageInput"
).value;



sendMessage(msg);



};


}








// 快捷按钮


document
.querySelectorAll(
".quick-button"
)
.forEach(
btn=>{


btn.onclick=function(){


sendMessage(
btn.dataset.message
);


};


});









async function sendMessage(msg){



if(!msg)
return;



try{


let res=
await fetch(
"/api/env/send",
{


method:"POST",


headers:{


"Content-Type":
"application/json"


},


body:
JSON.stringify(
{
msg:msg
}
)


}
);



let result=
await res.json();



document
.getElementById(
"sendStatus"
)
.innerHTML=
"发送成功:"+msg;



console.log(
result
);



}

catch(e){



document
.getElementById(
"sendStatus"
)
.innerHTML=
"发送失败";


}



}
