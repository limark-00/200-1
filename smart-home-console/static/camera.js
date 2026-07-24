/*
LabSafetyMonitor - 摄像头管理页面 JS
状态轮询 / 告警事件 / 灯箱 / 重连 / 禁音
*/
let muted = false;

// 摄像头信息
async function getCameraInfo() {
  try {
    const res = await fetch("/api/vision/status");
    const data = await res.json();
    // 状态点
    const dot = document.getElementById("statusDot");
    const txt = document.getElementById("statusText");
    if (dot) dot.className = "cam-status-dot" + (data.running ? " online" : "");
    if (txt) txt.textContent = data.running ? "实时识别中" : (data.enabled ? "连接中..." : "远程摄像头模式");
    // 总人数
    const peopleEl = document.getElementById("people");
    if (peopleEl) peopleEl.textContent = data.people_count;
    // FPS
    const fpsEl = document.getElementById("fps");
    if (fpsEl) fpsEl.textContent = data.fps.toFixed(1) + " FPS";
    // 索引
    const idxEl = document.getElementById("cameraIndex");
    if (idxEl) idxEl.textContent = data.camera_index;
    // 区域内人数
    const areaPeopleEl = document.getElementById("areaPeople");
    const areaRow = document.getElementById("areaPeopleRow");
    if (data.zone && data.zone.enabled) {
      if (areaPeopleEl) areaPeopleEl.textContent = data.people_in_zone;
      if (areaRow) areaRow.style.display = "";
    } else {
      if (areaRow) areaRow.style.display = "none";
    }
  } catch (e) {}
}

// 加载告警事件
async function loadAlarmEvents() {
  try {
    const res = await fetch("/api/vision/events?limit=20");
    const data = await res.json();
    const list = document.getElementById("eventList");
    if (!list) return;
    list.innerHTML = "";
    const events = data.events || [];
    if (events.length === 0) {
      list.innerHTML = '<div class="cam-event-empty">暂无告警事件</div>';
      return;
    }
    events.forEach((item) => {
      const div = document.createElement("div");
      div.className = "cam-event-item";
      div.innerHTML =
        '<div class="cam-event-header">' +
          '<strong>事件 #' + item.id + '</strong>' +
          '<span class="cam-event-status ended">' + (item.ended_at ? '已结束' : '进行中') + '</span>' +
        '</div>' +
        '<div class="cam-event-detail">' +
          '<div><span>时间：</span>' + item.started_at + '</div>' +
          '<div><span>人数：</span>' + item.max_people + '</div>' +
          '<div><span>原因：</span>' + (item.close_reason || '--') + '</div>' +
        '</div>' +
        (item.snapshot_filename ?
          '<a class="cam-event-link" onclick="openLightbox(\'/vision-events/' + item.snapshot_filename + '\')">查看告警截图</a>' : '');
      list.appendChild(div);
    });
  } catch (e) {}
}

// 重连画面
function reconnectCamera() {
  const img = document.getElementById("cameraVideo");
  if (img) img.src = "/api/vision/stream/remote?" + Date.now();
}

// 取消报警并禁音
document.getElementById("muteBtn").addEventListener("click", function () {
  muted = !muted;
  this.textContent = muted ? "已禁音" : "取消报警并禁音";
  this.className = muted ? "btn-cam btn-muted" : "btn-cam btn-yellow";
});

// 灯箱
function openLightbox(src) {
  const lb = document.getElementById("lightbox");
  const img = document.getElementById("lightboxImg");
  if (lb && img) { img.src = src; lb.classList.add("active"); }
}

function closeLightbox() {
  const lb = document.getElementById("lightbox");
  if (lb) lb.classList.remove("active");
}

document.addEventListener("keydown", function (e) {
  if (e.key === "Escape") closeLightbox();
});

// 初始化
getCameraInfo();
loadAlarmEvents();
setInterval(getCameraInfo, 2000);
setInterval(loadAlarmEvents, 5000);
