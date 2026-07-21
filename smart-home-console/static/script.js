/**
 * script.js —— 控制台前端逻辑（原生 JS，无框架）
 *
 * 学生可重点看：
 * 1. refreshSensors()  怎么调 /api/sensor
 * 2. sendControl()     怎么调 /api/control
 * 3. mockToggle        怎么切换 Mock / 巴法云
 */

(function () {
  const TOPICS = window.TOPICS || {};
  let isMock = !!window.INITIAL_MOCK;

  const $ = (id) => document.getElementById(id);

  function setStatus(el, text, ok) {
    if (!el) return;
    el.textContent = text || "";
    el.classList.remove("ok", "err");
    if (ok === true) el.classList.add("ok");
    if (ok === false) el.classList.add("err");
  }

  function updateModeUI() {
    const text = $("modeText");
    const toggle = $("mockToggle");
    if (text) {
      text.textContent = isMock
        ? "当前：模拟模式（假数据）"
        : "当前：巴法云模式（需真实topic）";
    }
    if (toggle) toggle.checked = isMock;
    // 真实模式下仍保留「立即抓拍」，但「模拟 PIR」只在 Mock 下有意义
    const btnMock = $("btnMockPir");
    if (btnMock) {
      btnMock.disabled = !isMock;
      btnMock.title = isMock
        ? "模拟人体感应触发，后台会自动抓拍"
        : "请先把右上角开关拨到「模拟」一侧";
      btnMock.style.opacity = isMock ? "1" : "0.45";
    }
  }

  async function apiJson(url, options) {
    const resp = await fetch(url, options);
    let data = null;
    try {
      data = await resp.json();
    } catch (e) {
      data = { ok: false, error: "响应不是 JSON" };
    }
    return { resp, data };
  }

  // ---------- 模式切换 ----------
  async function setMode(mock) {
    const { data } = await apiJson("/api/mode", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mock: !!mock }),
    });
    if (data && data.ok) {
      isMock = !!data.mock;
      updateModeUI();
      setStatus($("pirStatus"), data.message || "模式已切换", true);
      // 切换模式后立刻刷新一次传感器，避免还停在 --
      refreshSensors();
    } else {
      setStatus($("pirStatus"), (data && data.error) || "切换失败", false);
      updateModeUI();
    }
  }

  // ---------- 传感器刷新 ----------
  function parseTempHum(msg) {
    // 约定：消息形如 "25.6,60" 或 "25.6 60"
    if (!msg) return { temp: "--", hum: "--" };
    const parts = String(msg).split(/[,，\s]+/).filter(Boolean);
    return {
      temp: parts[0] != null ? parts[0] : "--",
      hum: parts[1] != null ? parts[1] : "--",
    };
  }

  async function refreshSensors() {
    try {
      const [th, light, pir] = await Promise.all([
        apiJson("/api/sensor/" + encodeURIComponent(TOPICS.temp_hum || "")),
        apiJson("/api/sensor/" + encodeURIComponent(TOPICS.light || "")),
        apiJson("/api/sensor/" + encodeURIComponent(TOPICS.pir || "")),
      ]);

      if (th.data && th.data.ok) {
        const { temp, hum } = parseTempHum(th.data.msg);
        $("tempValue").textContent = temp;
        $("humValue").textContent = hum;
      }

      if (light.data && light.data.ok) {
        $("lightValue").textContent = light.data.msg || "--";
      }

      if (pir.data && pir.data.ok) {
        const triggered = isPirMsg(pir.data.msg);
        const badge = $("pirBadge");
        badge.textContent = triggered ? "有人" : "无人";
        badge.classList.toggle("active", triggered);
        badge.classList.toggle("idle", !triggered);
      }

      // 任一传感器失败时给出明确提示（巴法云 topic 未配好时最常见）
      const fails = [th, light, pir]
        .filter(function (x) { return !(x.data && x.data.ok); })
        .map(function (x) { return (x.data && (x.data.error || x.data.message)) || "失败"; });

      const modeTag = isMock ? "模拟" : "巴法云";
      if (fails.length) {
        setStatus(
          $("sensorStatus"),
          modeTag + " 读取失败：" + fails[0] +
            (isMock ? "" : "（占位 topic 无效时请先拨到「模拟」，或在 config.py 填真实主题）") +
            " · " + new Date().toLocaleTimeString(),
          false
        );
      } else {
        setStatus(
          $("sensorStatus"),
          "已更新 · " + modeTag + " · " + new Date().toLocaleTimeString(),
          true
        );
      }
    } catch (e) {
      setStatus($("sensorStatus"), "刷新失败: " + e, false);
    }
  }

  function isPirMsg(msg) {
    const t = String(msg || "").trim().toLowerCase();
    return ["1", "on", "true", "yes", "触发", "有人", "detected", "alarm"].indexOf(t) >= 0;
  }

  // ---------- 控制下发 ----------
  async function sendControl(kind, msg) {
    const map = {
      traffic: TOPICS.traffic,
      buzzer: TOPICS.buzzer,
      rgb: TOPICS.rgb,
    };
    const topic = map[kind];
    if (!topic) {
      setStatus($("controlStatus"), "未知控制类型: " + kind, false);
      return;
    }
    const { data } = await apiJson("/api/control", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic: topic, msg: msg }),
    });
    if (data && data.ok) {
      setStatus($("controlStatus"), "已下发 " + topic + " ← " + msg, true);
    } else {
      setStatus($("controlStatus"), (data && data.error) || "下发失败", false);
    }
  }

  // ---------- 照片墙 ----------
  async function refreshGallery() {
    try {
      const { data } = await apiJson("/api/captures");
      const box = $("gallery");
      if (!data || !data.ok) {
        setStatus($("galleryStatus"), (data && data.error) || "加载失败", false);
        return;
      }
      const files = data.files || [];
      const base = data.base_url || "/static/captures/";
      if (!files.length) {
        box.innerHTML = '<div class="gallery-empty">暂无抓拍照片。可点「模拟 PIR 触发」或「立即抓拍」。</div>';
      } else {
        box.innerHTML = files
          .map(function (name) {
            const src = base + encodeURIComponent(name) + "?t=" + Date.now();
            return (
              '<figure class="gallery-item" data-src="' +
              base +
              encodeURIComponent(name) +
              '" title="' +
              name +
              '"><img src="' +
              src +
              '" alt="' +
              name +
              '" loading="lazy" /></figure>'
            );
          })
          .join("");
      }
      setStatus($("galleryStatus"), "共 " + files.length + " 张 · " + (data.time || ""), true);
    } catch (e) {
      setStatus($("galleryStatus"), "照片墙刷新失败: " + e, false);
    }
  }

  function openLightbox(src) {
    $("lightboxImg").src = src;
    $("lightbox").classList.remove("hidden");
  }

  function closeLightbox() {
    $("lightbox").classList.add("hidden");
    $("lightboxImg").src = "";
  }

  // ---------- 事件绑定 ----------
  function bindEvents() {
    $("mockToggle").addEventListener("change", function (e) {
      setMode(e.target.checked);
    });

    $("btnMockPir").addEventListener("click", async function () {
      if (!isMock) {
        alert("当前是「巴法云模式」，模拟 PIR 不可用。\n请先把右上角开关拨到右侧「模拟」。");
        setStatus($("pirStatus"), "请先切换到模拟模式", false);
        return;
      }
      const { data } = await apiJson("/api/mock/pir", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ triggered: true }),
      });
      if (data && data.ok) {
        setStatus($("pirStatus"), data.message + "；" + (data.hint || ""), true);
        // 马上刷新一次 PIR 显示
        refreshSensors();
        // 稍等轮询抓拍后再刷照片墙
        setTimeout(refreshGallery, 4000);
      } else {
        setStatus($("pirStatus"), (data && data.error) || "模拟失败", false);
      }
    });

    $("btnCaptureNow").addEventListener("click", async function () {
      setStatus($("pirStatus"), "正在抓拍…", true);
      const { data } = await apiJson("/api/capture/now", { method: "POST" });
      if (data && data.ok) {
        setStatus(
          $("pirStatus"),
          "抓拍成功: " + data.filename + (data.error ? "（" + data.error + "）" : ""),
          true
        );
        refreshGallery();
      } else {
        setStatus($("pirStatus"), (data && data.error) || "抓拍失败", false);
      }
    });

    document.querySelectorAll("[data-control]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        sendControl(btn.getAttribute("data-control"), btn.getAttribute("data-msg"));
      });
    });

    $("gallery").addEventListener("click", function (e) {
      const item = e.target.closest(".gallery-item");
      if (item) openLightbox(item.getAttribute("data-src"));
    });

    $("lightboxClose").addEventListener("click", closeLightbox);
    $("lightbox").addEventListener("click", function (e) {
      if (e.target === $("lightbox")) closeLightbox();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeLightbox();
    });
  }

  // ---------- 启动：先向服务器确认当前模式，避免页面显示与后端不一致 ----------
  async function syncModeFromServer() {
    try {
      const { data } = await apiJson("/api/mode");
      if (data && typeof data.mock === "boolean") {
        isMock = !!data.mock;
      }
    } catch (e) {
      // 忽略，沿用页面初始值
    }
    updateModeUI();
  }

  syncModeFromServer().then(function () {
    bindEvents();
    refreshSensors();
    refreshGallery();
    setInterval(refreshSensors, 5000);
    setInterval(refreshGallery, 5000);
  });
})();
