/*
=========================================
 LabSafetyMonitor
 环境分析页面 JS

 用于:
 temperature.html
 humidity.html
 gas.html
 light.html

=========================================
*/


let chart = null;


// 当前检测类型

let type = "";


// 阈值

let limit = 0;


// 数据缓存

let labels = [];

let values = [];




// ================================
// 页面初始化
// ================================


window.onload = function(){


    type =
    document.body.dataset.type;



    limit =
    Number(
        document.body.dataset.limit
    );



    console.log(
        "检测类型:",
        type,
        "阈值:",
        limit
    );



    initChart();



    updateData();



    // 自动刷新

    setInterval(

        updateData,

        2000

    );



};







// ================================
// 获取环境数据
// ================================


async function updateData(){



try{



    let res =
    await fetch(
        "/api/env"
    );



    let result =
    await res.json();



    if(!result.ok)

        return;



    let data =
    result.data;



    let value =
    Number(
        data[type]
    );



    updateNumber(value);



    updateChart(value);



}



catch(e){


    console.log(
        "数据获取失败:",
        e
    );


}


}









// ================================
// 更新数字
// ================================


function updateNumber(value){



    let current =
    document.getElementById(
        "current"
    );



    if(current)

        current.innerHTML =
        value;





    let max =
    document.getElementById(
        "max"
    );



    if(max){


        let maxValue =
        values.length>0
        ?
        Math.max(
            ...values,
            value
        )
        :
        value;


        max.innerHTML =
        maxValue;



    }






    let min =
    document.getElementById(
        "min"
    );



    if(min){


        let minValue =
        values.length>0
        ?
        Math.min(
            ...values,
            value
        )
        :
        value;



        min.innerHTML =
        minValue;


    }





    let state =
    document.getElementById(
        "state"
    );



    if(state){


        if(value>limit){



            state.innerHTML =
            "🔴 超过安全阈值";


            state.className =
            "danger";



        }

        else{


            state.innerHTML =
            "🟢 安全";


            state.className =
            "safe";

        }


    }



}









// ================================
// 初始化Chart
// ================================


function initChart(){



let canvas =
document.getElementById(
    "analysisChart"
);



if(!canvas)

return;





let ctx =
canvas.getContext(
    "2d"
);






chart =
new Chart(
ctx,
{


type:"line",



data:{



labels:labels,



datasets:[



{


label:"实时数据",


data:values,


borderWidth:3,


fill:false,



// 动态颜色

segment:{


borderColor:
function(ctx){



let y =
ctx.p1.parsed.y;



if(y>limit)


return "red";



return "green";



}



}




},




{


label:"安全阈值",


data:[],


borderColor:
"red",


borderWidth:2,


borderDash:
[
8,
6
],


pointRadius:0



}




]



},






options:{



responsive:true,



animation:false,



plugins:{



legend:{


display:true


}



},




scales:{



y:{


beginAtZero:false


}



}



}



}



);



}











// ================================
// 更新折线
// ================================


function updateChart(value){



let now =
new Date()
.toLocaleTimeString();




labels.push(
now
);



values.push(
value
);





// 最大显示30个点


if(labels.length>30){


labels.shift();


values.shift();


}





// 阈值线


let thresholdLine =
[];





for(
let i=0;
i<values.length;
i++
){


thresholdLine.push(
limit
);


}






chart.data.labels =
labels;



chart.data.datasets[0]
.data =
values;



chart.data.datasets[1]
.data =
thresholdLine;






chart.update();



}







// ================================
// 返回首页
// ================================


function goHome(){


window.location.href="/";


}