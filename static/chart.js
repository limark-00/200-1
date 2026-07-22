// ========================================
// LabSafetyMonitor
// 实时环境曲线分析
// ========================================



// 当前分析类型

let type =
new URLSearchParams(
window.location.search
).get("type");



// 默认温度

if(!type){

    type="temperature";

}



// ===============================
// 参数配置
// ===============================


const config={


temperature:{


name:"温度",

unit:"℃",

limit:30,

min:0,

max:50



},



humidity:{


name:"湿度",

unit:"%",

limit:70,

min:0,

max:100


},




gas:{


name:"气体浓度",

unit:"ppm",

limit:200,

min:0,

max:1000


},





light:{


name:"光照强度",

unit:"lux",

limit:1000,

min:0,

max:2000


}


};





let setting =
config[type];




// ===============================
// 页面文字初始化
// ===============================



document.getElementById(
"title"
).innerHTML=


"📊 "
+
setting.name
+
"实时分析";



document.getElementById(
"chartTitle"
).innerHTML=


setting.name
+
"实时折线图";



document.getElementById(
"name"
).innerHTML=
setting.name;



document.getElementById(
"limit"
).innerHTML=

setting.limit
+
setting.unit;




document.getElementById(
"range"
).innerHTML=


"0 ~ "
+
setting.limit
+
setting.unit;








// ===============================
// 数据缓存
// ===============================


let labels=[];


let values=[];


let maxPoints=50;



let index=0;








// ===============================
// 初始化Chart
// ===============================



const ctx =
document
.getElementById(
"lineChart"
)
.getContext(
"2d"
);





let chart =
new Chart(
ctx,
{


type:"line",



data:{


labels:labels,


datasets:[




// 数据线

{

label:
setting.name,


data:values,


borderWidth:3,


pointRadius:2,


tension:0.3,


segment:{


borderColor:
ctx=>{


let value=
ctx.p1.parsed.y;



if(value>
setting.limit){


return "red";


}


return "green";


}


}


},






// 阈值线

{


label:
"安全阈值",


data:[],


borderWidth:2,


borderDash:[
8,8
],


pointRadius:0,


borderColor:
"orange"


}



]



},



options:{


responsive:true,


maintainAspectRatio:false,



animation:false,



scales:{



y:{



min:
setting.min,


max:
setting.max



}



}




}



}

);








// ===============================
// 更新阈值线
// ===============================



function updateLimitLine(){



let arr=[];



for(
let i=0;
i<labels.length;
i++
){


arr.push(
setting.limit
);


}



chart.data.datasets[1]
.data=arr;


}









// ===============================
// 添加数据
// ===============================



function addPoint(value){



let now =
new Date()
.toLocaleTimeString();



if(labels.length>=maxPoints){



labels.shift();


values.shift();


}




labels.push(
now
);



values.push(
Number(value)
);



updateLimitLine();



chart.update();




}










// ===============================
// 状态判断
// ===============================



function updateStatus(value){



let status=
document.getElementById(
"status"
);



let current=
document.getElementById(
"current"
);



current.innerHTML=

value
+
setting.unit;






if(
Number(value)
>
setting.limit
){



status.innerHTML=

"⚠ 超过安全阈值";



status.className=
"danger";



}

else{



status.innerHTML=

"✔ 正常";



status.className=
"safe";



}



}








// ===============================
// 获取历史数据
// ===============================



async function loadHistory(){



try{



let res =
await fetch(
"/api/history"
);



let json =
await res.json();




if(
json.ok
){



let data =
json.data;



data.forEach(
item=>{


let value =
item[type];



if(
value!==undefined
){


addPoint(value);


}



}
);



}



}

catch(e){


console.log(
"history error",
e
);


}



}









// ===============================
// 实时刷新
// ===============================



async function updateData(){



try{


let res =
await fetch(
"/api/env"
);



let json =
await res.json();




if(
json.ok
){



let value =
json.data[type];



addPoint(
value
);



updateStatus(
value
);



}



}

catch(e){



console.log(
e
);



}



}









// ===============================
// 启动
// ===============================



loadHistory();



setInterval(
updateData,
2000
);