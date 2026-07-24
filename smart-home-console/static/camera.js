/*
LabSafetyMonitor - 摄像头管理页面 JS
状态轮询 / 告警事件 / 灯箱 / 重连 / 禁音
*/
let muted = false;

// 摄像头信息
async function getCameraInfo() {
  try {
    const res = await fetch("/api/camera/info");
    const data = await res.json();
    if (!data.ok) return;
    // 状态点
    const dot = document.getElementById("statusDot");
    const txt = document.getElementById("statusText");
    if (dot) dot.className = "cam-status-dot" + (data.connected ? " online" : "");
    if (txt) txt.textContent = data.connected ? "实时识别中" : "离线";
    // 总人数
    const peopleEl = document.getElementById("people");
    if (peopleEl) peopleEl.textContent = data.people;
    // FPS
    const fpsEl = document.getElementById("fps");
    if (fpsEl) fpsEl.textContent = data.fps + " FPS";
    // 索引
    const idxEl = document.getElementById("cameraIndex");
    if (idxEl) idxEl.textContent = data.camera_index;
    // 区域内人数 - 只有设置了危险区域才显示
    const areaPeopleEl = document.getElementById("areaPeople");
    const areaRow = document.getElementById("areaPeopleRow");
    if (data.has_danger_area) {
      if (areaPeopleEl) areaPeopleEl.textContent = data.area_people;
      if (areaRow) areaRow.style.display = "";
    } else {
      if (areaRow) areaRow.style.display = "none";
    }
  } catch (e) {}
}

// 加载告警事件
async function loadAlarmEvents() {
  try {
    const res = await fetch("/api/camera/alarm");
    const data = await res.json();
    if (!data.ok) return;
    const list = document.getElementById("eventList");
    if (!list) return;
    list.innerHTML = "";
    if (data.data.length === 0) {
      list.innerHTML = '<div class="cam-event-empty">暂无告警事件</div>';
      return;
    }
    data.data.reverse().forEach((item, i) => {
      const num = data.data.length - i;
      const div = document.createElement("div");
      div.className = "cam-event-item";
      div.innerHTML =
        '<div class="cam-event-header">' +
          '<strong>事件 #' + num + '</strong>' +
          '<span class="cam-event-status ended">已结束</span>' +
        '</div>' +
        '<div class="cam-event-detail">' +
          '<div><span>时间：</span>' + item.time + '</div>' +
          '<div><span>状态：</span>' + item.status + '</div>' +
          '<div><span>人数：</span>' + (item.people || '--') + '</div>' +
        '</div>' +
        (item.image && item.image !== "/static/no-image.png" ?
          '<a class="cam-event-link" onclick="openLightbox(\'' + item.image + '\')">查看告警截图</a>' : '');
      list.appendChild(div);
    });
  } catch (e) {}
}

// 重连画面
function reconnectCamera() {
  const img = document.getElementById("cameraVideo");
  if (img) img.src = "/camera?" + Date.now();
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
