/*
LabSafetyMonitor - 摄像头危险区域 Canvas 管理
编辑时拖拽画虚线框，保存后显示黄色实框，删除则清除
*/
let canvas, ctx, video;
let dangerArea = null;
let editing = false;
let drawing = false;
let startX = 0, startY = 0;
let backupArea = null;

window.addEventListener("load", () => {
  canvas = document.getElementById("areaCanvas");
  video = document.getElementById("cameraVideo");
  if (!canvas || !video) return;
  ctx = canvas.getContext("2d");
  resizeCanvas();
  window.addEventListener("resize", resizeCanvas);
  loadArea();
  canvas.addEventListener("mousedown", onMouseDown);
  canvas.addEventListener("mousemove", onMouseMove);
  canvas.addEventListener("mouseup", onMouseUp);
  canvas.addEventListener("mouseleave", onMouseLeave);
});

function resizeCanvas() {
  if (!video) return;
  canvas.width = video.clientWidth;
  canvas.height = video.clientHeight;
  // 保存后重新绘制实框
  if (!editing && dangerArea) drawSavedArea();
}

function screenToVideo(sx, sy) {
  return {
    x: Math.round(sx * (1280 / canvas.width)),
    y: Math.round(sy * (720 / canvas.height))
  };
}

// 绘制已保存的区域（黄色实框）
function drawSavedArea() {
  if (!ctx || !dangerArea) return;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const sx = canvas.width / 1280;
  const sy = canvas.height / 720;
  const x1 = dangerArea.x1 * sx;
  const y1 = dangerArea.y1 * sy;
  const x2 = dangerArea.x2 * sx;
  const y2 = dangerArea.y2 * sy;
  ctx.strokeStyle = "#ffd700";
  ctx.lineWidth = 2.5;
  ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
}

// 绘制拖拽预览（黄色虚线框）
function drawPreview(x1, y1, x2, y2) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const rx = Math.min(x1, x2), ry = Math.min(y1, y2);
  const w = Math.abs(x2 - x1), h = Math.abs(y2 - y1);
  ctx.fillStyle = "rgba(255,215,0,0.15)";
  ctx.fillRect(rx, ry, w, h);
  ctx.strokeStyle = "#ffd700";
  ctx.lineWidth = 2;
  ctx.setLineDash([6, 4]);
  ctx.strokeRect(rx, ry, w, h);
  ctx.setLineDash([]);
}

function clearCanvas() {
  if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
}

function onMouseDown(e) {
  if (!editing) return;
  const rect = canvas.getBoundingClientRect();
  startX = e.clientX - rect.left;
  startY = e.clientY - rect.top;
  drawing = true;
}

function onMouseMove(e) {
  if (!drawing || !editing) return;
  const rect = canvas.getBoundingClientRect();
  const cx = e.clientX - rect.left;
  const cy = e.clientY - rect.top;
  drawPreview(startX, startY, cx, cy);
}

function onMouseUp(e) {
  if (!drawing || !editing) return;
  drawing = false;
  const rect = canvas.getBoundingClientRect();
  const cx = e.clientX - rect.left;
  const cy = e.clientY - rect.top;
  if (Math.abs(cx - startX) < 10 || Math.abs(cy - startY) < 10) return;
  const p1 = screenToVideo(Math.min(startX, cx), Math.min(startY, cy));
  const p2 = screenToVideo(Math.max(startX, cx), Math.max(startY, cy));
  dangerArea = { x1: p1.x, y1: p1.y, x2: p2.x, y2: p2.y };
  drawPreview(startX, startY, cx, cy);
  updateHint("区域已绘制，可重新拖拽修改，或点击保存。");
}

function onMouseLeave() {
  if (drawing) drawing = false;
}

async function loadArea() {
  try {
    const res = await fetch("/api/vision/zone");
    const data = await res.json();
    if (data.ok && data.area) {
      dangerArea = data.area;
      if (dangerArea.x1 !== 0 || dangerArea.y1 !== 0 || dangerArea.x2 !== 0 || dangerArea.y2 !== 0) {
        updateDeployTag(true);
        drawSavedArea();
      } else {
        dangerArea = null;
      }
      updateAreaText();
    }
  } catch (e) {}
}

async function saveAreaToServer() {
  if (!dangerArea) return;
  try {
    await fetch("/api/vision/zone", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dangerArea)
    });
  } catch (e) {}
  updateAreaText();
}

function startEdit() {
  editing = true;
  backupArea = dangerArea ? JSON.parse(JSON.stringify(dangerArea)) : null;
  canvas.style.cursor = "crosshair";
  clearCanvas();
  document.getElementById("editBtn").style.display = "none";
  document.getElementById("saveBtn").style.display = "";
  document.getElementById("cancelBtn").style.display = "";
  document.getElementById("deleteBtn").style.display = "none";
  updateHint("在画面内点击并拖拽绘制一个矩形。");
}

async function saveArea() {
  editing = false;
  canvas.style.cursor = "default";
  await saveAreaToServer();
  drawSavedArea();
  updateDeployTag(!!dangerArea);
  resetButtons();
  updateHint("点击编辑后，在画面内拖拽绘制一个矩形。");
}

function cancelEdit() {
  editing = false;
  canvas.style.cursor = "default";
  dangerArea = backupArea;
  clearCanvas();
  if (dangerArea) drawSavedArea();
  resetButtons();
  updateHint("点击编辑后，在画面内拖拽绘制一个矩形。");
}

async function deleteArea() {
  dangerArea = null;
  editing = false;
  canvas.style.cursor = "default";
  clearCanvas();
  try {
    await fetch("/api/vision/zone", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ x1: 0, y1: 0, x2: 0, y2: 0 })
    });
  } catch (e) {}
  updateDeployTag(false);
  updateAreaText();
  resetButtons();
  updateHint("点击编辑后，在画面内拖拽绘制一个矩形。");
}

function resetButtons() {
  document.getElementById("editBtn").style.display = "";
  document.getElementById("saveBtn").style.display = "none";
  document.getElementById("cancelBtn").style.display = "none";
  document.getElementById("deleteBtn").style.display = "";
}

function updateDeployTag(armed) {
  const tag = document.getElementById("deployTag");
  if (tag) {
    tag.textContent = armed ? "已布防" : "未布防";
    tag.className = "cam-deploy-tag " + (armed ? "armed" : "disarmed");
  }
}

function updateAreaText() {
  const el = document.getElementById("areaText");
  if (!el) return;
  if (!dangerArea) {
    el.textContent = "未设置";
  } else {
    el.textContent = "(" + dangerArea.x1 + "," + dangerArea.y1 + ") - (" + dangerArea.x2 + "," + dangerArea.y2 + ")";
  }
}

function updateHint(text) {
  const el = document.getElementById("camHint");
  if (el) el.textContent = text;
}
