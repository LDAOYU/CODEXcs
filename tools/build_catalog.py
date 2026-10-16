#!/usr/bin/env python3
"""Build data/mods.json from the DOAXVV Steam mod comparison markdown."""

import json
import re
from pathlib import Path

SOURCE = Path("/home/ubuntu/.cursor/projects/workspace/uploads/doaxvv-steam-mods_c14f.md")
OUT = Path(__file__).resolve().parents[1] / "data" / "mods.json"

MARIE = ("marie", "nagisa", "kanna", "lobelia", "shizuku", "玛丽")
HONOKA = ("honoka", "luna", "sayuri", "tsukushi", "elise", "shandy", "穗香")
URL_RE = re.compile(r"https?://[^\s<>）)]+")
SIZE_RE = re.compile(r"大小\s*([0-9.]+\s*[kKmMgG]B)")
ATT_RE = re.compile(r"attachment\.php\?id=(\d+)", re.I)


def clean(text):
    text = (text or "").replace("`", "").strip()
    text = re.sub(r"\s+", " ", text)
    return text


def split_row(line):
    raw = line.strip()
    if raw.startswith("|"):
        raw = raw[1:]
    if raw.endswith("|"):
        raw = raw[:-1]
    return [clean(part) for part in raw.split("|")]


def is_separator(line):
    cells = split_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)


def group_of(type_name):
    text = type_name or ""
    if "发型" in text:
        return "发型"
    if any(word in text for word in ("场景", "姿势", "道具", "岛")):
        return "场景"
    if "工具" in text or "杂项" in text:
        return "工具"
    if "补丁" in text or "热修" in text:
        return "补丁"
    if any(word in text for word in ("皮肤", "外观", "表情", "脸")):
        return "外观"
    if "CC" in text or "Customizer" in text or "内容包" in text:
        return "CC"
    if "服装" in text or "泳装" in text:
        return "服装"
    return "其他"


def has_token(text, key):
    if any(ord(char) > 127 for char in key):
        return key in text
    return re.search(r"(?<![a-z0-9])" + re.escape(key) + r"(?![a-z0-9])", text) is not None


def bodies_of(*parts):
    raw = " ".join(parts)
    text = raw.lower()
    if "三体型" in raw:
        return ["Common", "Marie", "Honoka"]
    found = []
    if has_token(text, "common"):
        found.append("Common")
    if any(has_token(text, key) for key in MARIE):
        found.append("Marie")
    if any(has_token(text, key) for key in HONOKA):
        found.append("Honoka")
    if not found and ("全体系" in raw or "未标" in raw):
        return ["未标"]
    return found or ["未标"]


def display_title(name, outfit):
    plain = clean(name)
    if not re.search(r"\.(zip|7z|rar)$", plain, re.I):
        return plain
    quoted = re.search(r"「([^」]+)」", outfit or "")
    if quoted:
        return quoted.group(1)
    replaced = re.search(r"替换：([^；。]+)", outfit or "")
    if replaced:
        return clean(replaced.group(1))
    return re.sub(r"\.(zip|7z|rar)$", "", plain, flags=re.I)


def norm_name(name):
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", clean(name).lower())


def record_key(rec):
    url = rec.get("url") or ""
    attachment = ATT_RE.search(url)
    if attachment:
        return "att:" + attachment.group(1)
    return "url:" + url + "|" + norm_name(rec.get("name", ""))


def richer(a, b):
    score = lambda rec: len(rec.get("purpose") or "") + len(rec.get("outfit") or "")
    return a if score(a) >= score(b) else b


def collection_name(h2, h3):
    if not h2 or h2.startswith("来源总览") or h2.startswith("统计") or h2.startswith("下一轮"):
        base = ""
    elif h2.startswith("按类型"):
        base = "精选索引"
    elif h2.startswith("Markdown"):
        base = "精选索引"
    elif h2.startswith("第三轮"):
        base = "公开增补"
    else:
        base = re.split(r"[（(]", h2)[0].strip()
    if base == "公开增补" and h3:
        return "公开增补"
    return base or "其他"


def parse_tables(lines):
    records = []
    h2 = ""
    h3 = ""
    header = None
    last_url = ""
    for line in lines:
        if not line.strip():
            continue
        if line.startswith("## "):
            h2 = clean(line[3:])
            h3 = ""
            header = None
            last_url = ""
            continue
        if line.startswith("### "):
            h3 = clean(line[4:])
            header = None
            last_url = ""
            continue
        if line.startswith("#### "):
            header = None
            continue
        if not line.startswith("|"):
            header = None
            continue
        if is_separator(line):
            continue
        cells = split_row(line)
        if header is None:
            joined = " ".join(cells)
            if any(token in joined for token in ("下载链接", "下载页", "入口 URL", "链接")) and (
                "名称" in cells or "文件名" in cells or cells[:1] == ["#"]
            ):
                header = cells
                last_url = ""
            continue
        if len(cells) < len(header):
            cells = cells + [""] * (len(header) - len(cells))
        data = {header[i]: cells[i] for i in range(len(header))}
        link = data.get("下载链接") or data.get("下载页") or data.get("入口 URL") or data.get("链接") or ""
        urls = URL_RE.findall(link)
        if not urls and link in {"同上", "同上页", "同上页附件"} and last_url:
            urls = [last_url]
        if not urls:
            continue
        last_url = urls[0]
        name = data.get("文件名") or data.get("名称") or ""
        purpose = data.get("介绍用途") or data.get("说明") or data.get("原因") or ""
        outfit = data.get("对应服装") or ""
        note = " ".join(
            part
            for part in (data.get("备注") or "", data.get("建议") or "", data.get("日期备注") or "", data.get("状态") or "")
            if part
        )
        date = data.get("日期") or ""
        if not date:
            found = re.search(r"20\d{2}-\d{2}-\d{2}", note)
            date = found.group(0) if found else ""
        size = SIZE_RE.search(note)
        blob = " ".join((name, purpose, outfit, note, data.get("类型") or ""))
        records.append(
            {
                "name": name,
                "type": data.get("类型") or "",
                "source": data.get("来源") or "",
                "collection": collection_name(h2, h3),
                "purpose": purpose,
                "outfit": outfit,
                "url": urls[0],
                "links": urls,
                "page": data.get("页码") or "",
                "note": note,
                "date": date,
                "size": size.group(1).replace(" ", "") if size else "",
                "nsfw": "NSFW" in blob or "裸" in blob or "透视" in blob,
                "dmm": "DMM" in blob or "dmm" in blob.lower(),
                "login": "loverslab.com" in urls[0] or "需登录" in blob,
            }
        )
    return records


def parse_headings(lines):
    records = []
    h2 = ""
    h3 = ""
    current = None

    def flush():
        nonlocal current
        if not current:
            return
        urls = current.get("links") or []
        if urls and current.get("name"):
            blob = " ".join(
                (
                    current.get("name") or "",
                    current.get("type") or "",
                    current.get("purpose") or "",
                    current.get("note") or "",
                )
            )
            current["url"] = urls[0]
            current["nsfw"] = "NSFW" in blob or "裸" in blob or "透视" in blob
            current["dmm"] = "DMM" in blob
            current["login"] = any("loverslab.com" in url for url in urls) or "需登录" in blob
            current["collection"] = collection_name(h2, h3) or "精选索引"
            records.append(current)
        current = None

    for line in lines:
        if line.startswith("## "):
            flush()
            h2 = clean(line[3:])
            h3 = ""
            continue
        if line.startswith("### "):
            flush()
            h3 = clean(line[4:])
            continue
        if line.startswith("#### "):
            flush()
            title = re.sub(r"^[A-Z]*-?\d+\.\s*", "", clean(line[5:]))
            title = re.sub(r"\s*★.*$", "", title).strip()
            current = {
                "name": title,
                "type": "",
                "source": "",
                "purpose": "",
                "outfit": "",
                "links": [],
                "page": "",
                "note": "",
                "date": "",
                "size": "",
                "collection": "",
            }
            continue
        if current is None or not line.startswith("- "):
            continue
        body = line[2:].strip()
        label = re.match(r"\*\*(.+?)\*\*\s*(.*)", body)
        if not label:
            continue
        key, value = clean(label.group(1)).rstrip("：:"), clean(label.group(2)).replace("*", "")
        if key.startswith("类型"):
            current["type"] = value.split("·")[0].strip()
            if "来源" in value and not current["source"]:
                source = re.search(r"来源[：:]\s*([^·]+)", value)
                if source:
                    current["source"] = clean(source.group(1))
            if "日期" in value and not current["date"]:
                found = re.search(r"20\d{2}-\d{2}-\d{2}", value)
                current["date"] = found.group(0) if found else ""
        elif key.startswith("说明") or key.startswith("介绍"):
            current["purpose"] = value
        elif key.startswith("对应"):
            current["outfit"] = value
        elif key.startswith("来源"):
            current["source"] = value.split("·")[0].strip()
        elif key.startswith("下载"):
            current["links"] = URL_RE.findall(value)
        elif key.startswith("日期"):
            found = re.search(r"20\d{2}-\d{2}-\d{2}", value)
            current["date"] = found.group(0) if found else value
        elif key.startswith("备注"):
            current["note"] = value
    flush()
    return records


def finalize(records):
    merged = {}
    order = []
    for rec in records:
        if not rec.get("url") or not rec.get("name"):
            continue
        key = record_key(rec)
        if key in merged:
            merged[key] = richer(merged[key], rec)
            continue
        merged[key] = rec
        order.append(key)
    mods = []
    for index, key in enumerate(order, start=1):
        rec = merged[key]
        def strip_md(text):
            return (text or "").replace("**", "")

        outfit = strip_md(rec.get("outfit"))
        purpose = strip_md(rec.get("purpose"))
        name = rec.get("name") or ""
        source = strip_md(rec.get("source"))
        note = strip_md(rec.get("note"))
        mods.append(
            {
                "id": f"m{index}",
                "title": display_title(name, outfit),
                "filename": clean(name) if re.search(r"\.(zip|7z|rar)$", name, re.I) else "",
                "type": rec.get("type") or "未分类",
                "group": group_of(rec.get("type") or ""),
                "bodies": bodies_of(name, outfit, purpose),
                "source": source,
                "collection": rec.get("collection") or "其他",
                "purpose": purpose,
                "outfit": outfit,
                "url": rec["url"],
                "links": rec.get("links") or [rec["url"]],
                "page": rec.get("page") or "",
                "note": note,
                "date": rec.get("date") or "",
                "size": rec.get("size") or "",
                "nsfw": bool(rec.get("nsfw")),
                "dmm": bool(rec.get("dmm")),
                "login": bool(rec.get("login")),
            }
        )
    return mods


def main():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    records = parse_headings(lines) + parse_tables(lines)
    mods = finalize(records)
    payload = {
        "updated": "2026-10-16",
        "round": 15,
        "game": "Dead or Alive Xtreme Venus Vacation",
        "count": len(mods),
        "mods": mods,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    groups = {}
    collections = {}
    for mod in mods:
        groups[mod["group"]] = groups.get(mod["group"], 0) + 1
        collections[mod["collection"]] = collections.get(mod["collection"], 0) + 1
    print("count", len(mods))
    print("bytes", OUT.stat().st_size)
    print("groups", groups)
    print("collections", collections)


if __name__ == "__main__":
    main()
