(function () {
  var PAGE = 20;
  var TYPES = ["全部", "服装", "外观", "CC", "场景", "发型", "工具", "补丁", "其他"];
  var BODIES = ["全部", "Common", "Marie", "Honoka", "未标"];
  var FLAGS = [
    { id: "all", label: "全部" },
    { id: "login", label: "需登录" },
    { id: "dmm", label: "DMM 待确认" },
    { id: "plain", label: "非服装" },
  ];

  var state = {
    q: "",
    type: "全部",
    body: "全部",
    flag: "all",
    collection: "",
    page: 1,
  };
  var mods = [];
  var byId = {};

  var list = document.getElementById("list");
  var pager = document.getElementById("pager");
  var status = document.getElementById("status");
  var tally = document.getElementById("tally");
  var detail = document.getElementById("detail");
  var detailBody = document.getElementById("detail-body");
  var gate = document.getElementById("gate");

  function esc(value) {
    return String(value || "").replace(/[&<>"']/g, function (char) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char];
    });
  }

  function clip(text, limit) {
    text = text || "";
    return text.length > limit ? text.slice(0, limit) + "…" : text;
  }

  function shortCollection(name) {
    if (!name || name.length <= 22) return name;
    return name.split("/")[0].trim() + " 等";
  }

  function matches(mod) {
    if (state.type !== "全部" && mod.group !== state.type) return false;
    if (state.body !== "全部" && mod.bodies.indexOf(state.body) === -1) return false;
    if (state.collection && mod.collection !== state.collection) return false;
    if (state.flag === "login" && !mod.login) return false;
    if (state.flag === "dmm" && !mod.dmm) return false;
    if (state.flag === "plain" && mod.group === "服装") return false;
    if (!state.q) return true;
    var hay = [mod.title, mod.filename, mod.outfit, mod.purpose, mod.source, mod.collection, mod.type, mod.note]
      .join(" ")
      .toLowerCase();
    return hay.indexOf(state.q) !== -1;
  }

  function filtered() {
    return mods.filter(matches);
  }

  function pills(mod) {
    var bits = ['<span class="pill">' + esc(mod.group) + "</span>"];
    mod.bodies.forEach(function (body) {
      bits.push('<span class="pill">' + esc(body) + "</span>");
    });
    if (mod.dmm) bits.push('<span class="pill warn">DMM</span>');
    if (mod.login) bits.push('<span class="pill warn">需登录</span>');
    return bits.join("");
  }

  function render() {
    var rows = filtered();
    var pages = Math.max(1, Math.ceil(rows.length / PAGE));
    if (state.page > pages) state.page = pages;
    var start = (state.page - 1) * PAGE;
    var slice = rows.slice(start, start + PAGE);
    status.textContent = rows.length
      ? "显示 " + (start + 1) + "–" + (start + slice.length) + " / " + rows.length + " 条"
      : "没有符合条件的条目";
    tally.textContent = rows.length + " / " + mods.length + " 条";

    if (!slice.length) {
      list.innerHTML = '<li class="empty">换个关键词，或把筛选改回全部。</li>';
    } else {
      list.innerHTML = slice
        .map(function (mod, index) {
          var outfit = clip(mod.outfit || mod.purpose || mod.source || "对照表未写对应服装", 96);
          var file = mod.filename && mod.filename !== mod.title ? '<p class="file">' + esc(mod.filename) + "</p>" : "";
          return (
            '<li><button class="card" type="button" data-id="' +
            esc(mod.id) +
            '"><span class="card-top"><span class="index">#' +
            String(start + index + 1).padStart(4, "0") +
            '</span><span class="pills">' +
            pills(mod) +
            '</span></span><h3>' +
            esc(mod.title) +
            "</h3>" +
            file +
            '<p class="outfit">' +
            esc(outfit) +
            '</p><span class="card-foot"><span class="meta">' +
            esc(shortCollection(mod.collection)) +
            "</span><span class=\"meta\">" +
            esc(mod.source || "来源见下载页") +
            "</span></span></button></li>"
          );
        })
        .join("");
    }

    pager.innerHTML =
      '<button type="button" id="prev"' +
      (state.page <= 1 ? " disabled" : "") +
      ">上一页</button><span>第 " +
      state.page +
      " / " +
      pages +
      ' 页</span><button type="button" id="next"' +
      (state.page >= pages ? " disabled" : "") +
      ">下一页</button>";
  }

  function field(title, text) {
    if (!text) return "";
    return '<section class="detail-block"><h4>' + esc(title) + "</h4><p>" + esc(text) + "</p></section>";
  }

  function openDetail(id) {
    var mod = byId[id];
    if (!mod) return;
    var links = (mod.links || [mod.url])
      .map(function (url, index) {
        var label = (mod.links || []).length > 1 ? "下载页 " + (index + 1) : "打开下载页";
        return '<a href="' + esc(url) + '" target="_blank" rel="noreferrer">' + label + "</a>";
      })
      .join("");
    var extra = [mod.date, mod.page, mod.size].filter(Boolean).join(" · ");
    detailBody.innerHTML =
      '<p class="detail-kicker">' +
      esc(mod.collection) +
      "</p><h3>" +
      esc(mod.title) +
      "</h3><div class=\"pills\" style=\"margin-top:.6rem\">" +
      pills(mod) +
      "</div>" +
      field("文件名", mod.filename) +
      field("介绍用途", mod.purpose) +
      field("对应服装", mod.outfit) +
      field("来源", mod.source) +
      field("备注", [mod.note, extra].filter(Boolean).join(" · ")) +
      '<div class="detail-actions">' +
      links +
      '<button type="button" id="close-detail">关闭</button></div>';
    detail.showModal();
  }

  function choices(container, values, current, onPick) {
    container.innerHTML = values
      .map(function (value) {
        var id = typeof value === "string" ? value : value.id;
        var label = typeof value === "string" ? value : value.label;
        var pressed = current === id ? "true" : "false";
        return '<button type="button" aria-pressed="' + pressed + '" data-value="' + esc(id) + '">' + esc(label) + "</button>";
      })
      .join("");
    container.onclick = function (event) {
      var button = event.target.closest("button");
      if (!button) return;
      onPick(button.getAttribute("data-value"));
    };
  }

  function bindFilters() {
    choices(document.getElementById("type-filters"), TYPES, state.type, function (value) {
      state.type = value;
      state.page = 1;
      bindFilters();
      render();
    });
    choices(document.getElementById("body-filters"), BODIES, state.body, function (value) {
      state.body = value;
      state.page = 1;
      bindFilters();
      render();
    });
    choices(document.getElementById("flag-filters"), FLAGS, state.flag, function (value) {
      state.flag = value;
      state.page = 1;
      bindFilters();
      render();
    });
  }

  function fillCollections() {
    var counts = {};
    mods.forEach(function (mod) {
      counts[mod.collection] = (counts[mod.collection] || 0) + 1;
    });
    var select = document.getElementById("collection");
    Object.keys(counts)
      .sort(function (a, b) {
        return counts[b] - counts[a];
      })
      .forEach(function (name) {
        var option = document.createElement("option");
        option.value = name;
        option.textContent = shortCollection(name) + "（" + counts[name] + "）";
        select.appendChild(option);
      });
    select.addEventListener("change", function () {
      state.collection = select.value;
      state.page = 1;
      render();
    });
  }

  document.getElementById("search-form").addEventListener("submit", function (event) {
    event.preventDefault();
  });
  document.getElementById("q").addEventListener("input", function (event) {
    state.q = event.target.value.trim().toLowerCase();
    state.page = 1;
    render();
  });
  list.addEventListener("click", function (event) {
    var card = event.target.closest(".card");
    if (card) openDetail(card.getAttribute("data-id"));
  });
  pager.addEventListener("click", function (event) {
    if (event.target.id === "prev") state.page -= 1;
    if (event.target.id === "next") state.page += 1;
    render();
    document.getElementById("catalog").scrollIntoView({ block: "start" });
  });
  detail.addEventListener("click", function (event) {
    if (event.target.id === "close-detail") detail.close();
  });

  function showGate() {
    var preview = new URLSearchParams(location.search).get("preview") === "1";
    if (preview || sessionStorage.getItem("vv-ok") === "1") return;
    gate.hidden = false;
  }

  document.getElementById("enter").addEventListener("click", function () {
    sessionStorage.setItem("vv-ok", "1");
    gate.hidden = true;
    document.getElementById("q").focus();
  });

  if (window.matchMedia("(max-width: 800px)").matches) {
    document.getElementById("filter-panel").removeAttribute("open");
  }

  showGate();
  fetch("data/mods.json")
    .then(function (response) {
      if (!response.ok) throw new Error("bad status");
      return response.json();
    })
    .then(function (payload) {
      mods = payload.mods || [];
      mods.forEach(function (mod) {
        byId[mod.id] = mod;
      });
      fillCollections();
      bindFilters();
      render();
    })
    .catch(function () {
      status.textContent = "对照表没有载入。请从站点根目录打开页面。";
      tally.textContent = "载入失败";
    });
})();
