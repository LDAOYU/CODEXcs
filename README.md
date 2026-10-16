# DOAXVV Steam 模组对照

《死或生：沙滩排球维纳斯假期》Steam 版公开模组索引。数据来自 2026-10-16 第十五轮对照表，页面可以按套装、体型、作者和来源检索。

服装和 CC 多数含裸化或透视。站点只做对照，下载跳到原页面，不托管文件，也不放预览图。

## 本地打开

```bash
python3 -m http.server 4173
```

浏览器访问 `http://127.0.0.1:4173`。要先确认已满 18 岁。

## 更新数据

把新的对照 Markdown 路径写进 `tools/build_catalog.py` 的 `SOURCE`，然后：

```bash
python3 tools/build_catalog.py
```

生成的目录在 `data/mods.json`。
