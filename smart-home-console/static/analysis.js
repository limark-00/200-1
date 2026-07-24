/*
LabSafetyMonitor - 环境分析页面 JS
检测页: 实时数据 + 最大/最小/阈值 + 报警 + 蜂鸣器 + 红灯(气体)
数据由后端持续采集，进入页面直接读取历史 + 实时更新
*/
let chart = null, type = "", limit = 0, unit = "";
let labels = [], values = [];
let alarmTriggered = false;
let connected = false; // 巴法云连接状态

window.onload = function () {
  type = document.body.dataset.type || location.pathname.replace(/\//g, "").replace(".html", "");
  const limits = { temperature: 28, humidity: 70, gas: 200, light: 800 };
  limit = limits[type] || 28;
  initChart();
  checkBemfaStatus();
  updateData();
  setInterval(updateData, 2000);
  setInterval(checkBemfaStatus, 5000);
};

// 检查巴法云连接状态
async function checkBemfaStatus() {
  try {
    const res = await fetch("/api/llm/status");
    const data = await res.json();
    connected = data.configured;
    const el = document.getElementById("buzzerStatus");
    if (el) el.textContent = "蜂鸣器: " + (connected ? "已连接" : "未连接");
  } catch (e) {}
}

// 获取环境数据
async function updateData() {
  try {
    const envRes = await fetch("/api/env");
    const envResult = await envRes.json();
    if (!envResult.ok) return;
    const data = envResult.data;
    const value = Number(data[type]);
    // 更新当前值
    const curEl = document.getElementById("current");
    if (curEl) curEl.textContent = value;
    // 最大最小
    values.push(value);
    if (values.length > 100) values.shift();
    const maxEl = document.getElementById("max");
    if (maxEl) maxEl.textContent = Math.max(...values);
    const minEl = document.getElementById("min");
    if (minEl) minEl.textContent = Math.min(...values);
    // 状态
    const stateEl = document.getElementById("state");
    const danger = value > limit;
    if (stateEl) {
      stateEl.textContent = danger ? "超过阈值" : "安全";
      stateEl.className = "state-tag " + (danger ? "danger" : "safe");
    }
    // 报警按钮
    const btnAlarm = document.getElementById("btnAlarm");
    if (btnAlarm) btnAlarm.disabled = !danger || alarmTriggered;
    // 气体页红灯
    const redLight = document.getElementById("redLight");
    if (redLight) redLight.className = "red-light" + (danger ? " on" : "");
    // 图表用本地缓存数据
    updateChartFromLocal();
  } catch (e) {
    console.log("数据获取失败:", e);
  }
}

function updateChartFromLocal() {
  labels.length = 0;
  const start = Math.max(0, values.length - 50);
  for (let i = start; i < values.length; i++) { labels.push(i); }
  if (chart) {
    chart.data.labels = labels.slice(-50);
    chart.data.datasets[0].data = values.slice(-50);
    chart.data.datasets[1].data = values.slice(-50).map(() => limit);
    chart.update();
  }
}

// 初始化 Chart
function initChart() {
  const canvas = document.getElementById("analysisChart");
  if (!canvas) return;
  chart = new Chart(canvas.getContext("2d"), {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        { label: "实时数据", data: values, borderWidth: 2, fill: false, pointRadius: 2,
          segment: { borderColor: ctx => ctx.p1.parsed.y > limit ? "#ef4444" : "#2563eb" } },
        { label: "安全阈值", data: [], borderColor: "#ef4444", borderWidth: 1.5, borderDash: [6, 4], pointRadius: 0, fill: false }
      ]
    },
    options: { responsive: true, animation: false, plugins: { legend: { display: true } }, scales: { y: { beginAtZero: false } } }
  });
}

// 从后端历史更新图表
function updateChartFromHistory(result) {
  const hLabels = result.labels || [];
  const hValues = (result.data || {})[type] || [];
  labels.length = 0; values.length = 0;
  const start = Math.max(0, hLabels.length - 50);
  for (let i = start; i < hLabels.length; i++) { labels.push(hLabels[i]); values.push(hValues[i]); }
  chart.data.labels = labels;
  chart.data.datasets[0].data = values;
  chart.data.datasets[1].data = values.map(() => limit);
  chart.update();
}

// 触发报警 -> 发送巴法云
async function triggerAlarm() {
  if (alarmTriggered) return;
  alarmTriggered = true;
  const btn = document.getElementById("btnAlarm");
  if (btn) { btn.textContent = "已报警"; btn.disabled = true; }
  try {
    await fetch("/api/env/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ msg: "alarm_on" })
    });
  } catch (e) {}
}

// 停止报警
async function stopAlarm() {
  alarmTriggered = false;
  const btn = document.getElementById("btnAlarm");
  if (btn) { btn.textContent = "报警"; }
  try {
    await fetch("/api/env/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ msg: "alarm_off" })
    });
  } catch (e) {}
  // 重新判断是否还能报警
  const val = values.length > 0 ? values[values.length - 1] : 0;
  if (btn) btn.disabled = val <= limit;
}
