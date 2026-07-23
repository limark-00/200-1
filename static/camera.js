// ===================================
// 摄像头管理页面
// ===================================



// 阈值

const LIMIT={


temperature:28,


humidity:70,


gas:200,


light:800,


people:20


};








// ================================
// 时间
// ================================


function updateClock(){


let now=new Date();


document.getElementById(
"clock"
).innerHTML=

now.toLocaleString();



}



setInterval(
updateClock,
1000
);


updateClock();










// ================================
// 返回首页
// ================================


function goHome(){


window.location.href="/";


}











// ================================
// 摄像头信息
// ================================


async function getCameraInfo(){


try{


let res=await fetch(

"/api/camera/info"

);



let data=await res.json();





if(data.ok){





// 人数


document.getElementById(
"people"
).innerHTML=

data.people+" 人";






// FPS


document.getElementById(
"fps"
).innerHTML=

data.fps;







// 摄像头编号


document.getElementById(
"cameraIndex"
).innerHTML=

data.camera_index;








// 状态


let status=document.getElementById(
"cameraStatus"
);




if(data.connected){


status.innerHTML="🟢 在线";


status.className="info-value safe";


}

else{


status.innerHTML="🔴 离线";


status.className="info-value danger";


}








// 人数颜色


let people=document.getElementById(
"people"
);



if(data.people>LIMIT.people){


people.style.color="red";


}

else{


people.style.color="green";


}









// 更新时间


document.getElementById(
"updateTime"
).innerHTML=

new Date()
.toLocaleTimeString();







}






}catch(e){



console.log(
"摄像头接口错误",
e
);



}



}











// ================================
// 环境数据
// ================================


async function getEnvironment(){


try{


let res=await fetch(

"/api/env"

);



let data=await res.json();





if(data.ok){


let d=data.data;





showEnv(

"temperature",

d.temperature,

LIMIT.temperature

);



showEnv(

"humidity",

d.humidity,

LIMIT.humidity

);



showEnv(

"gas",

d.gas,

LIMIT.gas

);



showEnv(

"light",

d.light,

LIMIT.light

);



checkSafe(d);



}



}catch(e){


console.log(e);


}



}











// ================================
// 显示环境
// ================================


function showEnv(id,value,limit){



document.getElementById(
id
).innerHTML=value;



let state=document.getElementById(
id+"State"
);



if(value>limit){


state.innerHTML="🔴异常";


state.style.color="red";


}

else{


state.innerHTML="🟢正常";


state.style.color="green";


}



}











// ================================
// 综合安全判断
// ================================


function checkSafe(d){


let safe=true;



if(d.temperature>LIMIT.temperature)

safe=false;



if(d.humidity>LIMIT.humidity)

safe=false;



if(d.gas>LIMIT.gas)

safe=false;



if(d.light>LIMIT.light)

safe=false;






let box=document.getElementById(
"safe"
);





if(safe){


box.innerHTML="🟢 安全";


box.className="info-value safe";



}

else{


box.innerHTML="🔴 危险";


box.className="info-value danger";



}



}











// ================================
// 自动刷新
// ================================



getCameraInfo();


getEnvironment();




setInterval(

getCameraInfo,

2000

);



setInterval(

getEnvironment,

2000

);