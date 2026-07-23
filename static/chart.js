/*
==================================================
LabSafetyMonitor
单项环境数据分析
==================================================
*/



let chart;



// ================================
// 获取类型
// ================================


let params=

new URLSearchParams(

window.location.search

);



let type=

params.get("type");




if(!type){

type="temperature";

}






let nameMap={


temperature:

{

name:"温度",

unit:"℃"

},



humidity:

{

name:"湿度",

unit:"%"

},



gas:

{

name:"气体浓度",

unit:"ppm"

},



light:

{

name:"光照强度",

unit:"Lux"

},



history:

{

name:"综合历史数据",

unit:""

}



};








document.getElementById(
"title"
).innerHTML=


nameMap[type].name+

"实时变化曲线";









// ================================
// 获取历史数据
// ================================


async function loadChart(){



let res=

await fetch(

"/api/history"

);



let json=

await res.json();



if(!json.ok)

return;



let data=json.data;




let labels=[];

let values=[];



data.forEach(item=>{



labels.push(

item.time

);



if(type=="history"){


values.push(

item.temperature

);


}

else{


values.push(

item[type]

);


}



});







drawChart(

labels,

values

);




}








// ================================
// 绘制
// ================================


function drawChart(

labels,

values

){



let ctx=

document.getElementById(

"myChart"

);



if(chart)

chart.destroy();





chart=

new Chart(

ctx,

{


type:"line",


data:{


labels:labels,


datasets:[{


label:

nameMap[type].name,


data:values,


borderWidth:3,


fill:false


}]


},



options:{


responsive:true,


scales:{


y:{


beginAtZero:false


}


}



}


}


);



}









loadChart();





// 每5秒刷新

setInterval(

loadChart,

5000

);