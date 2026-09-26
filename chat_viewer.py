#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Chat Export Viewer - 酒馆(SillyTavern) 聊天记录查看器

拖入 JSON 即可查看、搜索、复制与编辑消息。
界面为纯 tkinter 实现的轻量设计系统：
  · 浅色 / 深色双主题，自动记忆
  · 角色色标 + 标签式消息头，日期分隔，长文阅读更舒适
  · 可调正文字号、消息列表侧栏、右侧编辑面板
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

import tkinter as tk
import tkinter.font as tkfont
from tkinter import colorchooser, filedialog, messagebox, ttk

try:
    from PIL import Image as _PILImage
    from PIL import ImageDraw as _PILDraw
    from PIL import ImageTk as _PILImageTk
    HAS_PIL = True
except Exception:
    HAS_PIL = False

try:
    from tkinterdnd2 import TkinterDnD
    HAS_DND = True
except Exception:
    TkinterDnD = None
    HAS_DND = False


APP_NAME = "AI Chat Check"
APP_TITLE = "AI Chat Check · 聊天记录查看器"
PLACEHOLDER = "搜索消息内容…  (Ctrl+F)"


# ══════════════════════════════════════════════════════════════════════════
#  运行环境 / 设置持久化
# ══════════════════════════════════════════════════════════════════════════
def enable_dpi_awareness():
    """Windows 下开启 DPI 感知，高分屏字体不再发虚；返回缩放系数。"""
    if sys.platform != "win32":
        return 1.0
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                return 1.0
        dpi = float(ctypes.windll.user32.GetDpiForSystem())
        return max(1.0, dpi / 96.0) if dpi else 1.0
    except Exception:
        return 1.0


DPI_SCALE = enable_dpi_awareness()


def S(value):
    """按 DPI 缩放像素值。"""
    return max(1, int(round(value * DPI_SCALE)))


def settings_path():
    base = os.environ.get("APPDATA")
    if not base:
        base = os.path.join(os.path.expanduser("~"), ".ai_chat_viewer")
    return os.path.join(base, "AI_Chat_Viewer", "settings.json")


DEFAULT_SETTINGS = {
    "theme": "light",
    "content_size": 11,
    "show_sidebar": True,
    "width": 1150,
    "height": 760,
    "last_dir": "",
    "quote_highlight": True,
    "quote_color": "",
    "show_toolbar": True,
}


def load_settings():
    cfg = dict(DEFAULT_SETTINGS)
    try:
        with open(settings_path(), "r", encoding="utf-8-sig") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            for key in DEFAULT_SETTINGS:
                if key in data:
                    cfg[key] = data[key]
    except Exception:
        pass
    return cfg


def save_settings(cfg):
    try:
        path = settings_path()
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(cfg, handle, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════
#  设计令牌（配色）
# ══════════════════════════════════════════════════════════════════════════
PALETTES = {
    "light": {
        "bg":            "#f3f4f7",
        "surface":       "#ffffff",
        "surface_2":     "#f7f8fa",
        "surface_3":     "#eceef3",
        "border":        "#e4e7ed",
        "border_strong": "#d2d8e2",
        "text":          "#1c1f26",
        "text_2":        "#59616f",
        "text_3":        "#9299a7",
        "accent":        "#4a63e7",
        "accent_hover":  "#3b53d4",
        "accent_soft":   "#e8ebfd",
        "accent_fg":     "#ffffff",
        "user":          "#4a63e7",
        "user_soft":     "#e9ecfd",
        "ai":            "#0e9184",
        "ai_soft":       "#e0f4f1",
        "sys":           "#b0761c",
        "sys_soft":      "#fbf1dd",
        "other":         "#7c5cd6",
        "other_soft":    "#f0ebfc",
        "danger":        "#d9435c",
        "danger_soft":   "#fdeaee",
        "ok":            "#1f9254",
        "ok_soft":       "#e5f5ea",
        "select":        "#c8d4fb",
        "hl":            "#ffe08a",
        "hl_cur":        "#ffb638",
        "hl_fg":         "#33260a",
        "flash":         "#fdf1c9",
        "thumb":         "#ccd2dd",
        "thumb_hover":   "#b3bccb",
        "trough":        "#f3f4f7",
    },
    "dark": {
        "bg":            "#12141a",
        "surface":       "#191c23",
        "surface_2":     "#1e222a",
        "surface_3":     "#272c36",
        "border":        "#272c36",
        "border_strong": "#373e4c",
        "text":          "#e6e8ee",
        "text_2":        "#a2a9b7",
        "text_3":        "#71798a",
        "accent":        "#7189ff",
        "accent_hover":  "#8b9eff",
        "accent_soft":   "#232b4c",
        "accent_fg":     "#0a0d18",
        "user":          "#8098ff",
        "user_soft":     "#20294a",
        "ai":            "#3fcfa0",
        "ai_soft":       "#16332c",
        "sys":           "#e3ab5f",
        "sys_soft":       "#33291a",
        "other":         "#b39dff",
        "other_soft":    "#2a2440",
        "danger":        "#ff7186",
        "danger_soft":   "#3a2027",
        "ok":            "#4ade80",
        "ok_soft":       "#1b3327",
        "select":        "#3a4670",
        "hl":            "#6b5416",
        "hl_cur":        "#a37c1c",
        "hl_fg":         "#ffeab0",
        "flash":         "#3a3419",
        "thumb":         "#3a4150",
        "thumb_hover":   "#4c5464",
        "trough":        "#191c23",
    },
}

FONT_FAMILIES = (
    "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", "PingFang SC",
    "Hiragino Sans GB", "Noto Sans CJK SC", "Source Han Sans SC",
    "WenQuanYi Micro Hei", "TkTextFont",
)
MONO_FAMILIES = ("Cascadia Mono", "Consolas", "SF Mono", "Menlo", "DejaVu Sans Mono", "TkFixedFont")


class Theme:
    """主题管理：所有控件通过 subscribe 注册回调，切换时统一重绘。"""

    def __init__(self, name="light"):
        self.name = name if name in PALETTES else "light"
        self._subs = []

    @property
    def pal(self):
        return PALETTES[self.name]

    def subscribe(self, callback):
        self._subs.append(callback)
        callback(self.pal)

    def unsubscribe(self, callback):
        try:
            self._subs.remove(callback)
        except ValueError:
            pass

    def toggle(self):
        self.name = "dark" if self.name == "light" else "light"
        for callback in list(self._subs):
            callback(self.pal)
        return self.name


class Fonts:
    """集中管理字体，正文大小可调。"""

    def __init__(self, root, content_size=11):
        try:
            available = set(tkfont.families(root))
        except Exception:
            available = set()
        self.family = next((f for f in FONT_FAMILIES if f in available), "TkTextFont")
        self.mono = next((f for f in MONO_FAMILIES if f in available), "TkFixedFont")
        self.content_size = int(content_size)
        self.rebuild()

    def rebuild(self):
        fam = self.family
        size = self.content_size
        self.ui = (fam, 10)
        self.ui_bold = (fam, 10, "bold")
        self.small = (fam, 9)
        self.small_bold = (fam, 9, "bold")
        self.tiny = (fam, 8)
        self.section = (fam, 11, "bold")
        self.title = (fam, 14, "bold")
        self.hero = (fam, 17, "bold")
        self.chip = (fam, max(8, size - 2), "bold")
        self.chip_plain = (fam, max(8, size - 2))
        self.content = (fam, size)
        self.content_italic = (fam, size, "italic")
        self.gap = (fam, 2)

    def set_content_size(self, size):
        self.content_size = max(9, min(20, int(size)))
        self.rebuild()


# ══════════════════════════════════════════════════════════════════════════
#  角色信息
# ══════════════════════════════════════════════════════════════════════════
ROLE_META = {
    "user":      {"cn": "user", "en": "USER",      "color": "user"},
    "assistant": {"cn": "char", "en": "ASSISTANT", "color": "ai"},
    "system":    {"cn": "系统", "en": "SYSTEM",    "color": "sys"},
}
DOT = "\u25cf"

FILTERS = [
    ("all", "全部"),
    ("user", "user"),
    ("assistant", "char"),
]


def role_meta(role):
    meta = ROLE_META.get(role)
    if meta:
        return meta
    text = str(role or "未知")
    return {"cn": text, "en": text.upper(), "color": "other"}


def role_color_key(role):
    return role_meta(role)["color"]


def get_role_label(role):
    meta = role_meta(role)
    return f"{meta['cn']} ({meta['en'].title()})"


def get_role_color(role, pal):
    return pal[role_color_key(role)]


# ══════════════════════════════════════════════════════════════════════════
#  时间处理
# ══════════════════════════════════════════════════════════════════════════
def to_datetime(ts_ms):
    """Unix 毫秒时间戳 -> 本地 datetime（失败返回 None）。"""
    try:
        value = float(ts_ms)
    except (TypeError, ValueError):
        return None
    if value <= 0:
        return None
    if value > 1e15:
        value /= 1000.0
    try:
        return datetime.fromtimestamp(value / 1000.0)
    except (ValueError, OSError, OverflowError):
        return None


def parse_timestamp(ts_ms, fmt="%Y-%m-%d %H:%M:%S"):
    moment = to_datetime(ts_ms)
    if moment is None:
        return ""
    return moment.strftime(fmt)


def time_label(ts_ms):
    return parse_timestamp(ts_ms, "%H:%M:%S")


def date_key(ts_ms):
    return parse_timestamp(ts_ms, "%Y-%m-%d")


def date_label(ts_ms):
    moment = to_datetime(ts_ms)
    if moment is None:
        return ""
    today = datetime.now().date()
    if moment.date() == today:
        return "今天"
    return f"{moment.year} 年 {moment.month} 月 {moment.day} 日"


def parse_exported_at(value):
    if not value:
        return ""
    text = str(value).strip()
    try:
        moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    if moment.tzinfo is not None:
        try:
            moment = moment.astimezone()
        except Exception:
            moment = moment.replace(tzinfo=None)
    return moment.strftime("%Y-%m-%d %H:%M")


# ══════════════════════════════════════════════════════════════════════════
#  聊天数据解析
# ══════════════════════════════════════════════════════════════════════════
def traverse_chunks(chunks):
    """按 chunk 树的 active 分支展开，返回 [(chunk_id, messages), ...]。"""
    if not chunks:
        return []

    chunk_map = {c["id"]: c for c in chunks if isinstance(c, dict) and "id" in c}

    root = None
    for chunk in chunks:
        parent = chunk.get("parent")
        if parent is None or parent not in chunk_map:
            root = chunk
            break
    if root is None:
        root = chunks[0]

    visited = set()
    result = []

    def dfs(chunk):
        cid = chunk.get("id")
        if cid in visited:
            return
        visited.add(cid)
        result.append((cid, chunk.get("messages", []) or []))
        for child_id in chunk.get("children", []) or []:
            child = chunk_map.get(child_id)
            if child and child.get("active", False):
                dfs(child)

    dfs(root)
    return result


def extract_messages(json_data):
    """从酒馆导出的 JSON 中抽取全部消息与元信息。"""
    chat_meta = json_data.get("chat", {}) or {}
    title = chat_meta.get("title") or "未命名会话"
    model = chat_meta.get("model") or "未知模型"
    total_msgs = chat_meta.get("total_message", 0)
    exported_at = json_data.get("exported_at", "")

    chunks = chat_meta.get("chunks")
    msg_blocks = json_data.get("messages", []) or []
    all_messages = []

    if chunks:
        chunk_msgs_map = {}
        for block in msg_blocks:
            chunk_msgs_map[block.get("chunk_id", "")] = block.get("messages", []) or []

        chunk_sequence = traverse_chunks(chunks)
        seen = set()

        for chunk_id, inline_msgs in chunk_sequence:
            for msg in chunk_msgs_map.get(chunk_id, inline_msgs):
                key = "{}_{}_{}".format(
                    msg.get("createAt", ""), msg.get("role", ""),
                    (msg.get("content") or "")[:20],
                )
                if key in seen:
                    continue
                seen.add(key)
                # 用副本承载内部字段，避免保存时把 _index/_chunk_id 写回原文件
                record = dict(msg)
                record["_chunk_id"] = chunk_id
                all_messages.append(record)
    else:
        for block in msg_blocks:
            for msg in block.get("messages", []) or []:
                all_messages.append(dict(msg))

    for index, msg in enumerate(all_messages):
        msg["_index"] = index

    return {
        "title": title,
        "model": model,
        "total_messages": total_msgs,
        "exported_at": exported_at,
        "messages": all_messages,
        "raw": json_data,
    }


GENERIC_TITLES = {"会话", "未命名会话", "new chat", "untitled", ""}


def display_title(chat_data, filepath):
    """chat.title 常常是「会话」，此时改用文件名里的剧本名。"""
    title = (chat_data.get("title") or "").strip()
    if title.lower() not in GENERIC_TITLES:
        return title
    base = os.path.basename(filepath or "")
    match = re.match(r"^chat_export_[0-9a-fA-F\-]{8,}_(.+)\.json$", base)
    if match:
        return match.group(1).strip()
    return os.path.splitext(base)[0] or title or "未命名会话"


# ══════════════════════════════════════════════════════════════════════════
#  基础控件（跟随主题自动重绘）
# ══════════════════════════════════════════════════════════════════════════
class TFrame(tk.Frame):
    def __init__(self, master, theme, bg_key="surface", **kw):
        self._theme = theme
        self._bg_key = bg_key
        super().__init__(master, **kw)
        theme.subscribe(self._paint)

    def _paint(self, pal):
        self.configure(bg=pal[self._bg_key])

    def set_bg_key(self, bg_key):
        self._bg_key = bg_key
        self._paint(self._theme.pal)


class TLabel(tk.Label):
    def __init__(self, master, theme, bg_key="surface", fg_key="text", **kw):
        self._theme = theme
        self._bg_key = bg_key
        self._fg_key = fg_key
        super().__init__(master, **kw)
        theme.subscribe(self._paint)

    def _paint(self, pal):
        self.configure(bg=pal[self._bg_key], fg=pal[self._fg_key])

    def set_keys(self, bg_key=None, fg_key=None):
        if bg_key:
            self._bg_key = bg_key
        if fg_key:
            self._fg_key = fg_key
        self._paint(self._theme.pal)


class RoundWidget(tk.Canvas):
    """圆角控件基类：canvas 自绘圆角底，按内容自动调整尺寸。"""

    def __init__(self, master, theme, radius=None, on_key="surface", **kw):
        self._theme = theme
        self._radius = radius
        self._on_key = on_key
        self._rw = 0
        self._rh = 0
        self._fobj = None
        self._fobj_spec = None
        kw.setdefault("highlightthickness", 0)
        kw.setdefault("bd", 0)
        kw.setdefault("takefocus", 0)
        super().__init__(master, **kw)

    def _guarded_paint(self, pal):
        # 嵌入 Text 的控件会随刷新销毁，销毁后需退订主题回调
        if not self.winfo_exists():
            self._theme.unsubscribe(self._guarded_paint)
            return
        self._paint(pal)

    def _resize(self, width, height):
        width = max(6, int(round(width)))
        height = max(6, int(round(height)))
        if (width, height) != (self._rw, self._rh):
            self._rw, self._rh = width, height
            super().configure(width=width, height=height)

    def _font_obj(self, spec):
        if self._fobj is None or self._fobj_spec != spec:
            self._fobj_spec = spec
            try:
                self._fobj = tkfont.Font(self, font=spec) if spec else tkfont.Font(self)
            except Exception:
                self._fobj = tkfont.Font(self)
        return self._fobj

    def _round(self, fill, outline=None, pill=True, inset=0):
        if pill:
            radius = self._rh // 2
        else:
            radius = min(self._radius or S(9), self._rh // 2)
        radius = max(2, radius)
        return rounded_rect(self, inset, inset, self._rw - 1 - inset, self._rh - 1 - inset,
                            radius, fill=fill or "", outline=outline or "",
                            width=S(1) if outline else 0)


class Chip(RoundWidget):
    """圆角小标签（pill），用柔和底色 + 主色文字。"""

    def __init__(self, master, theme, text="", bg_key="surface_3", fg_key="text_2",
                 font=None, padx=None, pady=None, **kw):
        super().__init__(master, theme, **kw)
        self._bg_key = bg_key
        self._fg_key = fg_key
        self._font = font
        self._padx = S(9) if padx is None else padx
        self._pady = S(2) if pady is None else pady
        self._text = text
        theme.subscribe(self._guarded_paint)

    def set_keys(self, bg_key=None, fg_key=None):
        if bg_key:
            self._bg_key = bg_key
        if fg_key:
            self._fg_key = fg_key
        self._paint(self._theme.pal)

    def configure(self, cnf=None, **kw):
        repaint = False
        for key in ("text", "font"):
            if key in kw:
                setattr(self, "_" + key, kw.pop(key))
                repaint = True
        if kw:
            super().configure(**kw)
        elif cnf:
            super().configure(cnf)
        if repaint:
            self._paint(self._theme.pal)

    config = configure

    def _paint(self, pal):
        fobj = self._font_obj(self._font)
        width = fobj.measure(self._text or "") + 2 * self._padx
        height = fobj.metrics("linespace") + 2 * self._pady + S(2)
        self.delete("all")
        super().configure(bg=pal[self._on_key])
        if HAS_PIL:
            self._resize(width + 2 * AA_MARGIN, height + 2 * AA_MARGIN)
            photo = rounded_photo(self, width, height, height / 2.0,
                                  fill=pal[self._bg_key])
            self.create_image(self._rw / 2.0, self._rh / 2.0, image=photo,
                              anchor="center")
        else:
            self._resize(width, height)
            self._round(pal[self._bg_key])
        self.create_text(self._rw / 2.0, self._rh / 2.0, text=self._text or "",
                         font=self._font, fill=pal[self._fg_key], anchor="center")


class FlatButton(RoundWidget):
    """圆角按钮，带 hover / 按下 / 选中 / 禁用 四种状态。"""

    def __init__(self, master, theme, text="", command=None, variant="default",
                 font=None, padx=None, pady=None, **kw):
        super().__init__(master, theme, **kw)
        self._variant = variant
        self._command = command
        self._font = font
        self._padx = S(14) if padx is None else padx
        self._pady = S(6) if pady is None else pady
        self._text = text
        self._on = False
        self._enabled = True
        self._hover = False
        self._press = False
        self._scale = 1.0
        self._anim_jobs = []
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_down)
        self.bind("<ButtonRelease-1>", self._on_up)
        theme.subscribe(self._guarded_paint)

    # -- 状态 API --
    def set_variant(self, variant):
        self._variant = variant
        self._paint(self._theme.pal)

    def set_on(self, on):
        self._on = bool(on)
        self._paint(self._theme.pal)

    def set_enabled(self, enabled):
        self._enabled = bool(enabled)
        self._paint(self._theme.pal)

    def configure(self, cnf=None, **kw):
        repaint = False
        for key in ("text", "command", "font"):
            if key in kw:
                setattr(self, "_" + key, kw.pop(key))
                repaint = True
        if kw:
            super().configure(**kw)
        elif cnf:
            super().configure(cnf)
        if repaint:
            self._paint(self._theme.pal)

    config = configure

    # -- 事件 --
    def _on_enter(self, _event=None):
        self._hover = True
        self._paint(self._theme.pal)

    def _on_leave(self, _event=None):
        self._hover = False
        if self._press:
            self._press = False
            self._spring_back()
        else:
            self._paint(self._theme.pal)

    def _on_down(self, _event=None):
        if not self._enabled:
            return
        self._press = True
        self._stop_anim()
        self._set_scale(0.93)

    def _on_up(self, event=None):
        if not self._press:
            return
        self._press = False
        inside = event is None or (0 <= event.x <= self._rw and 0 <= event.y <= self._rh)
        self._spring_back()
        if self._enabled and inside and self._command:
            self._command()

    # -- 弹性动画 --
    def _set_scale(self, scale):
        self._scale = scale
        self._paint(self._theme.pal)

    def _stop_anim(self):
        for job in self._anim_jobs:
            try:
                self.after_cancel(job)
            except Exception:
                pass
        self._anim_jobs = []

    def _spring_back(self):
        """松手回弹：缩小 → 过冲放大 → 回稳，制造弹性手感。"""
        self._stop_anim()
        for ms, scale in ((0, 0.93), (70, 1.06), (150, 0.985), (220, 1.0)):
            self._anim_jobs.append(
                self.after(ms, lambda s=scale: self._set_scale(s)))

    # -- 配色 --
    def _states(self, pal):
        variant = self._variant
        if variant == "primary":
            base = (pal["accent"], pal["accent_fg"])
            hover = (pal["accent_hover"], pal["accent_fg"])
        elif variant == "danger":
            base = (pal["danger_soft"], pal["danger"])
            hover = (pal["danger"], "#ffffff")
        elif variant == "ghost":
            base = (None, pal["text_2"])
            hover = (pal["surface_3"], pal["text"])
        elif variant == "segment":
            base = (pal["surface_3"], pal["text_2"])
            hover = (pal["border"], pal["text"])
        else:
            base = (pal["surface_3"], pal["text"])
            hover = (pal["border"], pal["text"])
        press = (pal["border_strong"], pal["text"]) if variant == "default" else hover
        if self._on:
            base = hover = press = (pal["accent_soft"], pal["accent"])
        if not self._enabled:
            base = hover = press = (pal["surface_2"], pal["text_3"])
        return base, hover, press

    def _paint(self, pal):
        base, hover, press = self._states(pal)
        fill, fg = press if self._press else (hover if (self._hover and self._enabled) else base)
        fobj = self._font_obj(self._font)
        width = fobj.measure(self._text or "") + 2 * self._padx
        height = max(S(26), fobj.metrics("linespace") + 2 * self._pady)
        self.delete("all")
        super().configure(bg=pal[self._on_key])
        if fill and HAS_PIL:
            self._resize(width + 2 * AA_MARGIN, height + 2 * AA_MARGIN)
            lift = 1 if self._press else (3 if self._hover and self._enabled else 2)
            bw, bh = width * self._scale, height * self._scale
            photo = rounded_photo(self, bw, bh, bh / 2.0, fill=fill,
                                  outline=_darker(fill, 0.22),
                                  gloss=_lighter(fill, 0.14),
                                  shadow=_hex_mix(pal[self._on_key], "#000000", 0.25),
                                  shadow_lift=lift)
            self.create_image(self._rw / 2.0, self._rh / 2.0, image=photo,
                              anchor="center")
        else:
            self._resize(width, height)
            if fill:
                w, h = self._rw, self._rh
                sc = self._scale
                iw, ih = w * sc, h * sc
                x1 = (w - iw) / 2.0
                y1 = (h - ih) / 2.0
                x2, y2 = x1 + iw, y1 + ih
                radius = max(2.0, ih / 2.0)
                lift = S(1) if self._press else (S(3) if self._hover and self._enabled else S(2))
                rounded_rect(self, x1 + S(1), y1 + lift, x2 - S(1), y2 + lift, radius,
                             fill=_darker(fill, 0.3))
                rounded_rect(self, x1, y1, x2, y2, radius, fill=fill,
                             outline=_darker(fill, 0.22), width=S(1))
                rounded_rect(self, x1 + S(2), y1 + S(1.5), x2 - S(2), y1 + ih * 0.52,
                             max(2.0, radius * 0.6), fill=_lighter(fill, 0.14))
        self.create_text(self._rw / 2.0, self._rh / 2.0, text=self._text or "",
                         font=self._font, fill=fg, anchor="center")
        super().configure(cursor="hand2" if self._enabled else "arrow")


class ColorSwatch(RoundWidget):
    """圆形色块按钮：点击选择引号高亮颜色。"""

    def __init__(self, master, theme, color="#888888", command=None, **kw):
        super().__init__(master, theme, **kw)
        self._color = color
        self._command = command
        self._hover = False
        self.bind("<Enter>", lambda e: self._hover_paint(True))
        self.bind("<Leave>", lambda e: self._hover_paint(False))
        self.bind("<ButtonRelease-1>", self._on_up)
        theme.subscribe(self._guarded_paint)

    def set_color(self, color):
        self._color = color
        self._paint(self._theme.pal)

    def _hover_paint(self, on):
        self._hover = on
        self._paint(self._theme.pal)

    def _on_up(self, event=None):
        inside = event is None or (0 <= event.x <= self._rw and 0 <= event.y <= self._rh)
        if inside and self._command:
            self._command()

    def _paint(self, pal):
        size = S(24)
        self.delete("all")
        super().configure(bg=pal[self._on_key])
        if HAS_PIL:
            self._resize(size + 2 * AA_MARGIN, size + 2 * AA_MARGIN)
            d = size - S(4)
            photo = rounded_photo(self, d, d, d / 2.0, fill=self._color,
                                  outline=pal["border_strong"] if self._hover else None)
            self.create_image(self._rw / 2.0, self._rh / 2.0, image=photo,
                              anchor="center")
        else:
            self._resize(size, size)
            pad = S(5)
            outline = pal["border_strong"] if self._hover else None
            self.create_oval(pad, pad, size - pad, size - pad, fill=self._color,
                             outline=outline or "", width=S(1) if outline else 0)
        super().configure(cursor="hand2")


class SearchBox(RoundWidget):
    """圆角搜索框：canvas 画底与聚焦环，内嵌输入行。"""

    def __init__(self, master, theme, fonts, on_change=None, on_enter=None,
                 on_shift_enter=None, on_escape=None, width=24):
        super().__init__(master, theme, radius=S(12))
        self._fonts = fonts
        self._on_change = on_change
        self._on_enter = on_enter
        self._on_shift_enter = on_shift_enter
        self._on_escape = on_escape
        self._placeholder = True
        self._clear_visible = False

        self.inner = tk.Frame(self)
        self.glyph = tk.Label(self.inner, text="\U0001f50d")
        self.glyph.pack(side="left", padx=(S(2), S(3)))
        self.var = tk.StringVar()
        self.entry = tk.Entry(self.inner, textvariable=self.var, font=fonts.ui,
                              relief="flat", bd=0, highlightthickness=0,
                              width=width, insertwidth=S(1))
        self.entry.pack(side="left", fill="x", expand=True, pady=S(4))
        self.clear_btn = FlatButton(self.inner, theme, text="\u2715", variant="ghost",
                                    font=fonts.small, padx=S(6), pady=0,
                                    on_key="surface_2", command=self.clear)
        self._inset = S(10)

        uif = self._font_obj(fonts.ui)
        smallf = self._font_obj(fonts.small)
        inner_w = (smallf.measure("\U0001f50d") + S(5) + uif.measure("0" * width)
                   + smallf.measure("\u2715") + 2 * S(6) + S(12))
        inner_h = uif.metrics("linespace") + 2 * S(4)
        self._resize(inner_w + 2 * self._inset + 2 * AA_MARGIN,
                     inner_h + 2 * AA_MARGIN)
        self.create_window(AA_MARGIN + self._inset, AA_MARGIN, window=self.inner,
                           anchor="nw", width=inner_w, height=inner_h)

        self.entry.bind("<FocusIn>", self._focus_in)
        self.entry.bind("<FocusOut>", self._focus_out)
        self.entry.bind("<Return>", self._enter_key)
        self.entry.bind("<Shift-Return>", self._shift_enter_key)
        self.entry.bind("<Escape>", self._escape_key)
        self.var.trace_add("write", self._on_var_change)
        theme.subscribe(self._guarded_paint)
        self._show_placeholder()

    # -- 外观 --
    def _paint(self, pal):
        self._pal = pal
        self.inner.configure(bg=pal["surface_2"])
        self.glyph.configure(bg=pal["surface_2"], fg=pal["text_3"], font=self._fonts.small)
        self.entry.configure(
            bg=pal["surface_2"],
            fg=pal["text_3"] if self._placeholder else pal["text"],
            insertbackground=pal["accent"],
            selectbackground=pal["select"],
            selectforeground=pal["text"],
            readonlybackground=pal["surface_2"],
        )
        self.delete("bg")
        focused = False
        try:
            focused = self.entry.focus_get() is self.entry
        except Exception:
            focused = False
        outline = pal["accent"] if focused else pal["border_strong"]
        if HAS_PIL:
            photo = rounded_photo(self, self._rw - 2 * AA_MARGIN,
                                  self._rh - 2 * AA_MARGIN, S(12),
                                  fill=pal["surface_2"], outline=outline)
            item = self.create_image(self._rw / 2.0, self._rh / 2.0, image=photo,
                                     anchor="center", tags=("bg",))
        else:
            item = self._round(pal["surface_2"], outline, pill=False)
            self.addtag_withtag("bg", item)
        self.tag_lower(item)

    def _paint_ring(self):
        self._paint(self._pal)

    # -- 占位符 --
    def _show_placeholder(self):
        self._placeholder = True
        self.var.set(PLACEHOLDER)
        if hasattr(self, "_pal"):
            self.entry.configure(fg=self._pal["text_3"])

    def text(self):
        return "" if self._placeholder else self.var.get()

    def set_text(self, value):
        self._placeholder = not bool(value)
        self.var.set(value if value else PLACEHOLDER)
        if hasattr(self, "_pal"):
            self.entry.configure(fg=self._pal["text"] if value else self._pal["text_3"])

    def clear(self):
        self.set_text("")
        self.entry.focus_set()
        if self._on_change:
            self._on_change("")

    def focus_entry(self):
        self.entry.focus_set()
        if not self._placeholder:
            try:
                self.entry.select_range(0, "end")
            except Exception:
                pass

    def _focus_in(self, _event=None):
        if self._placeholder:
            self._placeholder = False
            self.var.set("")
            self.entry.configure(fg=self._pal["text"])
        self._paint_ring()

    def _focus_out(self, _event=None):
        if not self.var.get().strip():
            self._show_placeholder()
        self._paint_ring()

    def _on_var_change(self, *_args):
        value = self.text()
        self._toggle_clear(bool(value))
        if self._on_change:
            self._on_change(value)

    def _toggle_clear(self, visible):
        if visible == self._clear_visible:
            return
        self._clear_visible = visible
        if visible:
            self.clear_btn.pack(side="right", padx=(S(2), S(4)))
        else:
            self.clear_btn.pack_forget()

    def _enter_key(self, _event=None):
        if self._on_enter:
            self._on_enter()
        return "break"

    def _shift_enter_key(self, _event=None):
        if self._on_shift_enter:
            self._on_shift_enter()
        return "break"

    def _escape_key(self, _event=None):
        if self._placeholder:
            self.entry.focus_set()
        else:
            self.clear()
        if self._on_escape:
            self._on_escape()


class Segmented(TFrame):
    """分段筛选控件。"""

    def __init__(self, master, theme, fonts, items, value="all", command=None):
        super().__init__(master, theme, bg_key="surface")
        self.value = value
        self._command = command
        self.buttons = {}
        for key, label in items:
            button = FlatButton(self, theme, text=label, variant="segment",
                                font=fonts.small_bold, padx=S(10), pady=S(2),
                                command=lambda k=key: self.select(k))
            button.pack(side="left", padx=S(2), pady=S(2))
            self.buttons[key] = button
        self._refresh()

    def select(self, key):
        if key == self.value:
            return
        self.value = key
        self._refresh()
        if self._command:
            self._command(key)

    def _refresh(self):
        for key, button in self.buttons.items():
            button.set_on(key == self.value)


def rounded_rect(canvas, x1, y1, x2, y2, radius, **kw):
    """用 smooth 多边形画圆角矩形。"""
    points = [
        x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
        x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
        x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kw)


AA_MARGIN = 4
_ROUND_CACHE = {}


def _rgba(hexcolor):
    h = hexcolor.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def rounded_photo(master, w, h, radius, fill=None, outline=None,
                  outline_width=1, gloss=None, shadow=None, shadow_lift=2,
                  supersample=3):
    """PIL 超采样绘制抗锯齿圆角矩形，按参数缓存 PhotoImage。"""
    w = int(round(w))
    h = int(round(h) )
    radius = int(round(min(radius, h // 2)))
    ss = max(1, int(supersample))
    # 键里放 tk 解释器对象本身（强引用），避免解释器销毁后 id 被复用而取到失效图片
    key = (master.tk, w, h, radius, fill, outline, outline_width,
           gloss, shadow, shadow_lift, ss)
    hit = _ROUND_CACHE.get(key)
    if hit is not None:
        return hit
    m = AA_MARGIN * ss
    img = _PILImage.new("RGBA", (w * ss + 2 * m, h * ss + 2 * m), (0, 0, 0, 0))
    d = _PILDraw.Draw(img)
    if shadow:
        d.rounded_rectangle([m + ss, m + shadow_lift * ss,
                             m + (w - 1) * ss, m + (h - 1) * ss + shadow_lift * ss],
                            radius=radius * ss, fill=_rgba(shadow))
    if fill or outline:
        d.rounded_rectangle([m, m, m + (w - 1) * ss, m + (h - 1) * ss],
                            radius=radius * ss,
                            fill=_rgba(fill) if fill else None,
                            outline=_rgba(outline) if outline else None,
                            width=max(1, outline_width * ss))
    if gloss and fill:
        d.rounded_rectangle([m + 2 * ss, m + int(1.5 * ss),
                             m + (w - 2) * ss, m + int(h * 0.52 * ss)],
                            radius=max(2, int(radius * 0.6 * ss)), fill=_rgba(gloss))
    img = img.resize((img.width // ss, img.height // ss), _PILImage.LANCZOS)
    photo = _PILImageTk.PhotoImage(img, master=master)
    _ROUND_CACHE[key] = photo
    return photo


def _hex_mix(color_a, color_b, ratio):
    """两个 #rrggbb 颜色按 ratio（b 的占比）线性插值。"""
    try:
        a = color_a.lstrip("#")
        b = color_b.lstrip("#")
        ca = tuple(int(a[i:i + 2], 16) for i in (0, 2, 4))
        cb = tuple(int(b[i:i + 2], 16) for i in (0, 2, 4))
        mixed = tuple(int(round(x + (y - x) * ratio)) for x, y in zip(ca, cb))
        return "#%02x%02x%02x" % mixed
    except Exception:
        return color_a


def _lighter(color, ratio=0.14):
    return _hex_mix(color, "#ffffff", ratio)


def _darker(color, ratio=0.2):
    return _hex_mix(color, "#000000", ratio)


def ellipsis(text, limit):
    text = (text or "").replace("\r", " ").replace("\n", " ").strip()
    return text if len(text) <= limit else text[:limit - 1] + "\u2026"


# ══════════════════════════════════════════════════════════════════════════
#  主程序
# ══════════════════════════════════════════════════════════════════════════
class ChatViewerApp:
    def __init__(self, filepath=None):
        self.settings = load_settings()
        self.theme = Theme(self.settings.get("theme", "light"))
        self.root = TkinterDnD.Tk() if HAS_DND else tk.Tk()

        try:
            self.root.tk.call("tk", "scaling", DPI_SCALE * 96.0 / 72.0)
        except Exception:
            pass

        self.fonts = Fonts(self.root, self.settings.get("content_size", 11))
        self.style = ttk.Style(self.root)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        # ── 运行状态 ──
        self.current_file = None
        self.chat_data = None
        self.messages = []
        self.edited = {}
        self.filter_key = "all"
        self.visible = []
        self.blocks = {}
        self.line_blocks = []
        self.side_rows = []
        self.side_selected = None
        self.side_hover_line = None
        self.hl_ranges = []
        self.hl_pos = -1
        self.edit_msg_index = None
        self.edit_mode = tk.BooleanVar(value=False)
        self._filter_job = None
        self._flash_job = None
        self._geom_job = None
        self.cursor_index = None
        self._last_dir = self.settings.get("last_dir") or ""

        # ── 窗口 ──
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        logical_w = int(self.settings.get("width", 1150))
        logical_h = int(self.settings.get("height", 760))
        logical_w = min(logical_w, max(760, int(screen_w / DPI_SCALE) - 90))
        logical_h = min(logical_h, max(520, int(screen_h / DPI_SCALE) - 100))
        width = S(logical_w)
        height = S(logical_h)
        pos_x = max(0, (screen_w - width) // 2)
        pos_y = max(0, (screen_h - height) // 3)
        self.root.title(APP_TITLE)
        self.root.geometry("%dx%d+%d+%d" % (width, height, pos_x, pos_y))
        self.root.minsize(S(900), S(560))
        self.root.pack_propagate(False)

        # ── 界面 ──
        self.theme.subscribe(lambda pal: self.root.configure(bg=pal["bg"]))
        self.theme.subscribe(self._apply_ttk)
        self._build_toolbar()
        self._build_infobar()
        self._build_statusbar()
        self._build_body()
        self.btn_toolbar_show = FlatButton(self.root, self.theme, text="展开",
                                           variant="ghost", font=self.fonts.small,
                                           padx=S(9), pady=S(2),
                                           command=self.toggle_toolbar)
        self.theme.subscribe(self._apply_text_theme)
        self.theme.subscribe(self._apply_side_theme)
        self._apply_font_dependent_styles()

        # ── 快捷键 / 事件 ──
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-c>", lambda e: self.copy_selected())
        self.root.bind("<Control-e>", lambda e: self.toggle_edit_mode())
        self.root.bind("<Control-f>", lambda e: self.focus_search())
        self.root.bind("<Control-h>", lambda e: self.toggle_quote_highlight())
        self.root.bind("<Control-t>", lambda e: self.toggle_toolbar())
        self.root.bind("<Control-plus>", lambda e: self.change_font_size(1))
        self.root.bind("<Control-equal>", lambda e: self.change_font_size(1))
        self.root.bind("<Control-minus>", lambda e: self.change_font_size(-1))
        self.root.bind("<Escape>", lambda e: self._on_escape())
        self.root.bind("<MouseWheel>", self._on_mousewheel, add="+")

        if HAS_DND:
            try:
                self.root.drop_target_register("DND_Files")
                self.root.dnd_bind("<<Drop>>", self._on_drop)
                self.root.dnd_bind("<<DragEnter>>", self._on_drag_enter)
                self.root.dnd_bind("<<DragLeave>>", self._on_drag_leave)
            except Exception:
                pass

        self._refresh_theme_button()
        self.btn_quote.set_on(bool(self.settings.get("quote_highlight", True)))
        self._update_saved_chip()
        self._set_infobar_visible(False)
        self._want_sidebar = bool(self.settings.get("show_sidebar", True))
        self._set_sidebar_visible(False)
        if not self.settings.get("show_toolbar", True):
            self._set_toolbar_visible(False)

        if filepath and os.path.isfile(filepath):
            self._load_json(filepath)
        else:
            self._show_empty_state()

        # 窗口映射后再设置标题栏属性，否则 DWM 不生效
        self.root.update()
        self._apply_titlebar()
        self._apply_window_icon()

        self.root.mainloop()

    # ══════════════════════════ 顶部工具栏 ══════════════════════════
    def _vline(self, parent, bg_key="border"):
        return TFrame(parent, self.theme, bg_key=bg_key, width=1)

    def _build_toolbar(self):
        self._toolbar_visible = True
        bar = TFrame(self.root, self.theme, bg_key="surface")
        bar.pack(side="top", fill="x")
        self.toolbar = bar
        self.toolbar_line = TFrame(self.root, self.theme, bg_key="border", height=1)
        self.toolbar_line.pack(side="top", fill="x")

        brand = TFrame(bar, self.theme, bg_key="surface")
        brand.pack(side="left", padx=(S(14), S(8)), pady=S(9))
        TLabel(brand, self.theme, text=DOT, bg_key="surface", fg_key="accent",
               font=(self.fonts.family, 12)).pack(side="left", pady=S(2))
        stack = TFrame(brand, self.theme, bg_key="surface")
        stack.pack(side="left", padx=(S(6), 0))
        TLabel(stack, self.theme, text="AI Chat Check", bg_key="surface", fg_key="text",
               font=self.fonts.ui_bold).pack(anchor="w")
        TLabel(stack, self.theme, text="酒馆聊天记录查看器", bg_key="surface", fg_key="text_3",
               font=self.fonts.tiny).pack(anchor="w")

        self._vline(bar).pack(side="left", fill="y", padx=S(8), pady=S(14))

        self.btn_open = FlatButton(bar, self.theme, text="打开", variant="primary",
                                   font=self.fonts.ui, command=self.open_file)
        self.btn_open.pack(side="left", padx=(S(2), S(3)), pady=S(9))
        self.btn_copy = FlatButton(bar, self.theme, text="复制", variant="ghost",
                                   font=self.fonts.ui, command=self.copy_selected)
        self.btn_copy.pack(side="left", padx=S(3), pady=S(9))
        self.btn_edit = FlatButton(bar, self.theme, text="编辑模式", variant="ghost",
                                   font=self.fonts.ui, command=self.toggle_edit_mode)
        self.btn_edit.pack(side="left", padx=S(3), pady=S(9))
        self.btn_save = FlatButton(bar, self.theme, text="保存", variant="default",
                                   font=self.fonts.ui, command=self.save_file)
        self.btn_save.pack(side="left", padx=S(3), pady=S(9))
        self.btn_quote = FlatButton(bar, self.theme, text="高亮", variant="ghost",
                                    font=self.fonts.ui, command=self.toggle_quote_highlight)
        self.btn_quote.pack(side="left", padx=(S(3), S(1)), pady=S(9))
        self.btn_quote_color = ColorSwatch(bar, self.theme, color=self._quote_color(),
                                           command=self.choose_quote_color)
        self.btn_quote_color.pack(side="left", padx=S(1), pady=S(9))
        self.btn_quote_color.bind("<Button-3>", lambda e: self.set_quote_color(""))
        self.btn_export = FlatButton(bar, self.theme, text="导出", variant="ghost",
                                     font=self.fonts.ui, command=self.export_txt)
        self.btn_export.pack(side="left", padx=S(3), pady=S(9))

        # 右侧工具（先 pack 的在最右）
        self.btn_collapse = FlatButton(bar, self.theme, text="收起", variant="ghost",
                                       font=self.fonts.ui, command=self.toggle_toolbar)
        self.btn_collapse.pack(side="right", padx=(S(4), S(2)), pady=S(9))
        self.btn_sidebar = FlatButton(bar, self.theme, text="列表", variant="ghost",
                                      font=self.fonts.ui, command=self.toggle_sidebar)
        self.btn_sidebar.pack(side="right", padx=(S(4), S(12)), pady=S(9))
        self.btn_theme = FlatButton(bar, self.theme, text="深色", variant="ghost",
                                    font=self.fonts.ui, command=self.toggle_theme)
        self.btn_theme.pack(side="right", padx=S(3), pady=S(9))
        self.btn_font_up = FlatButton(bar, self.theme, text="A+", variant="ghost",
                                      font=self.fonts.ui, padx=S(8),
                                      command=lambda: self.change_font_size(1))
        self.btn_font_up.pack(side="right", padx=S(3), pady=S(9))
        self.btn_font_down = FlatButton(bar, self.theme, text="A\u2212", variant="ghost",
                                        font=self.fonts.ui, padx=S(8),
                                        command=lambda: self.change_font_size(-1))
        self.btn_font_down.pack(side="right", padx=S(3), pady=S(9))
        self._vline(bar).pack(side="right", fill="y", padx=S(8), pady=S(14))

        self.match_label = TLabel(bar, self.theme, text="", bg_key="surface",
                                  fg_key="text_3", font=self.fonts.small)
        self.match_label.pack(side="right", padx=(S(8), S(10)))
        self.search_box = SearchBox(bar, self.theme, self.fonts, width=20,
                                    on_change=self._on_search_change,
                                    on_enter=self.search_next,
                                    on_shift_enter=self.search_prev,
                                    on_escape=self._on_search_escape)
        self.search_box.pack(side="right", pady=S(9))

    # ══════════════════════════ 会话信息栏 ══════════════════════════
    def _build_infobar(self):
        bar = TFrame(self.root, self.theme, bg_key="surface")
        self.infobar = bar
        self.infobar_line = TFrame(self.root, self.theme, bg_key="border", height=1)

        inner = TFrame(bar, self.theme, bg_key="surface")
        inner.pack(side="left", fill="both", expand=True, padx=S(16), pady=S(7))
        self.infobar_inner = inner

        self.filter_seg = Segmented(inner, self.theme, self.fonts, FILTERS,
                                    value="all", command=self._on_filter_change)
        self.filter_seg.pack(side="right", pady=S(2))

        self.info_title = TLabel(inner, self.theme, text="未打开文件", bg_key="surface",
                                 fg_key="text", font=self.fonts.title, anchor="w")
        self.info_title.pack(side="left")

        self.info_model = Chip(inner, self.theme, text="", bg_key="surface_3",
                               fg_key="text_2", font=self.fonts.small)
        self.info_model.pack(side="left", padx=(S(10), S(6)))
        self.info_time = Chip(inner, self.theme, text="", bg_key="surface",
                              fg_key="text_3", font=self.fonts.small)
        self.info_time.pack(side="left")

    def _set_infobar_visible(self, visible):
        self._infobar_visible = bool(visible)
        if visible:
            self.infobar.pack(side="top", fill="x", before=self.body)
            self.infobar_line.pack(side="top", fill="x", before=self.body)
        else:
            self.infobar.pack_forget()
            self.infobar_line.pack_forget()
        self._place_toolbar_handle()

    # ══════════════════════════ 状态栏 ══════════════════════════
    def _build_statusbar(self):
        bar = TFrame(self.root, self.theme, bg_key="surface")
        bar.pack(side="bottom", fill="x")
        self.statusbar = bar
        self.status_line = TFrame(self.root, self.theme, bg_key="border", height=1)
        self.status_line.pack(side="bottom", fill="x")

        self.lbl_status = TLabel(bar, self.theme, bg_key="surface", fg_key="text_2",
                                 font=self.fonts.tiny, anchor="w",
                                 text="就绪")
        self.lbl_status.pack(side="left", padx=S(14), pady=S(6))

        self.lbl_saved = Chip(bar, self.theme, text="", bg_key="accent_soft",
                              fg_key="accent", font=self.fonts.tiny)
        self.lbl_info = TLabel(bar, self.theme, bg_key="surface", fg_key="text_3",
                               font=self.fonts.tiny)
        self.lbl_info.pack(side="right", padx=S(14), pady=S(6))

    # ══════════════════════════ 主体区域 ══════════════════════════
    def _build_body(self):
        self.body = TFrame(self.root, self.theme, bg_key="bg")
        self.body.pack(side="top", fill="both", expand=True)

        self.sidebar = TFrame(self.body, self.theme, bg_key="surface", width=S(288))
        self.sidebar.pack_propagate(False)
        self.sidebar_line = TFrame(self.body, self.theme, bg_key="border", width=1)
        self._build_sidebar()

        self.stage = TFrame(self.body, self.theme, bg_key="bg")
        self.stage.pack(side="left", fill="both", expand=True)
        self._build_transcript()
        self._build_empty_state()

        self.edit_panel = TFrame(self.body, self.theme, bg_key="surface", width=S(372))
        self.edit_panel.pack_propagate(False)
        self.edit_line = TFrame(self.body, self.theme, bg_key="border", width=1)
        self._build_edit_panel()

    def _build_transcript(self):
        frame = TFrame(self.stage, self.theme, bg_key="bg")
        frame.pack(side="left", fill="both", expand=True)
        self.chat_frame = frame

        self.text_area = tk.Text(
            frame, wrap="word", bd=0, relief="flat", font=self.fonts.content,
            padx=S(28), pady=S(16), highlightthickness=0, insertwidth=0,
            state="disabled", cursor="xterm", spacing1=0, spacing2=0, spacing3=0,
            undo=False, width=30, height=12,
        )
        self.scroll = ttk.Scrollbar(frame, orient="vertical", command=self.text_area.yview,
                                    style="Chat.Vertical.TScrollbar")
        self.text_area.configure(yscrollcommand=self.scroll.set)
        self.scroll.pack(side="right", fill="y")
        self.text_area.pack(side="left", fill="both", expand=True)

        self.text_area.bind("<Button-1>", self._on_text_click, add="+")
        self.text_area.bind("<Double-Button-1>", self._on_text_double_click)
        self.text_area.bind("<Button-3>", self._show_context_menu)
        self.text_area.bind("<Button-2>", self._show_context_menu)
        self._build_context_menu()

    def _build_empty_state(self):
        empty = TFrame(self.stage, self.theme, bg_key="bg")
        self.empty_state = empty
        box = TFrame(empty, self.theme, bg_key="bg")
        box.place(relx=0.5, rely=0.44, anchor="center")

        self.art = tk.Canvas(box, width=S(104), height=S(92), bd=0, highlightthickness=0)
        self.art.pack(pady=(0, S(14)))
        self.theme.subscribe(self._draw_art)

        TLabel(box, self.theme, text="拖入 JSON 文件即可开始", bg_key="bg", fg_key="text",
               font=self.fonts.hero).pack()
        subtitle = "支持 SillyTavern（酒馆）导出的聊天记录"
        if not HAS_DND:
            subtitle += " · 当前未安装 tkinterdnd2，请用「打开」按钮选择文件"
        self.empty_subtitle = TLabel(box, self.theme, text=subtitle, bg_key="bg",
                                     fg_key="text_2", font=self.fonts.ui)
        self.empty_subtitle.pack(pady=(S(6), S(20)))

        tips = TFrame(box, self.theme, bg_key="bg")
        tips.pack()
        shortcuts = [
            ("Ctrl + O", "打开文件"),
            ("Ctrl + F", "搜索内容"),
            ("Ctrl + E", "编辑模式"),
            ("Ctrl + C", "复制选中"),
            ("Ctrl + H", "引号高亮"),
            ("Ctrl + T", "操作栏收展"),
        ]
        for row, (key, desc) in enumerate(shortcuts):
            cell = TFrame(tips, self.theme, bg_key="bg")
            cell.grid(row=row // 2, column=row % 2, sticky="w", padx=S(10), pady=S(4))
            Chip(cell, self.theme, text=key, bg_key="surface", fg_key="text_2",
                 on_key="bg", font=(self.fonts.mono, 8, "bold")).pack(side="left")
            TLabel(cell, self.theme, text=desc, bg_key="bg", fg_key="text_3",
                   font=self.fonts.small).pack(side="left", padx=(S(8), S(18)))

        self.empty_open = FlatButton(box, self.theme, text="选择 JSON 文件", variant="primary",
                                     font=self.fonts.ui_bold, padx=S(18), pady=S(7),
                                     on_key="bg", command=self.open_file)
        self.empty_open.pack(pady=(S(22), 0))

    def _draw_art(self, pal):
        canvas = self.art
        canvas.configure(bg=pal["bg"])
        canvas.delete("all")
        width = S(104)
        height = S(92)
        rounded_rect(canvas, S(6), S(8), width - S(26), S(42), S(12),
                     fill=pal["user_soft"], outline=pal["user"], width=S(2))
        rounded_rect(canvas, S(26), S(52), width - S(6), height - S(8), S(12),
                     fill=pal["ai_soft"], outline=pal["ai"], width=S(2))
        for offset in (S(18), S(28), S(38)):
            canvas.create_oval(offset, S(22), offset + S(4), S(26), fill=pal["user"], outline="")
        for offset in (S(40), S(50), S(60)):
            canvas.create_oval(offset, S(68), offset + S(4), S(72), fill=pal["ai"], outline="")

    # ══════════════════════════ 左侧消息列表 ══════════════════════════
    def _build_sidebar(self):
        head = TFrame(self.sidebar, self.theme, bg_key="surface")
        head.pack(side="top", fill="x", padx=S(14), pady=(S(13), S(8)))
        TLabel(head, self.theme, text="消息列表", bg_key="surface", fg_key="text",
               font=self.fonts.section).pack(side="left")
        self.side_count = Chip(head, self.theme, text="0", bg_key="surface_3",
                               fg_key="text_2", font=self.fonts.small_bold)
        self.side_count.pack(side="right")

        holder = TFrame(self.sidebar, self.theme, bg_key="surface")
        holder.pack(side="top", fill="both", expand=True)

        self.side_text = tk.Text(
            holder, wrap="none", bd=0, relief="flat", highlightthickness=0,
            state="disabled", cursor="hand2", padx=S(2), pady=S(4), insertwidth=0,
            font=self.fonts.small, spacing1=0, spacing2=0, spacing3=0,
            width=22, height=8,
        )
        side_scroll = ttk.Scrollbar(holder, orient="vertical", command=self.side_text.yview,
                                    style="Side.Vertical.TScrollbar")
        self.side_text.configure(yscrollcommand=side_scroll.set)
        side_scroll.pack(side="right", fill="y")
        self.side_text.pack(side="left", fill="both", expand=True)

        self.side_text.bind("<Button-1>", self._on_side_click)
        self.side_text.bind("<Double-Button-1>", self._on_side_double_click)
        self.side_text.bind("<Motion>", self._on_side_motion)
        self.side_text.bind("<Leave>", self._on_side_leave)
        self.side_text.bind("<Up>", self._on_side_key)
        self.side_text.bind("<Down>", self._on_side_key)
        self.side_text.bind("<Return>", self._on_side_key)

        self.side_hint = TLabel(self.sidebar, self.theme, text="单击定位 · 双击编辑",
                                bg_key="surface", fg_key="text_3", font=self.fonts.tiny)
        self.side_hint.pack(side="bottom", fill="x", padx=S(14), pady=(S(6), S(10)))
        TFrame(self.sidebar, self.theme, bg_key="border", height=1).pack(side="bottom", fill="x")

    # ══════════════════════════ 右侧编辑面板 ══════════════════════════
    def _build_edit_panel(self):
        inner = TFrame(self.edit_panel, self.theme, bg_key="surface")
        inner.pack(side="top", fill="both", expand=True, padx=S(16), pady=S(14))

        head = TFrame(inner, self.theme, bg_key="surface")
        head.pack(side="top", fill="x")
        TLabel(head, self.theme, text="编辑消息", bg_key="surface", fg_key="text",
               font=self.fonts.section).pack(side="left")
        self.btn_edit_close = FlatButton(head, self.theme, text="\u2715", variant="ghost",
                                         font=self.fonts.small, padx=S(7), pady=S(1),
                                         command=self._close_edit_panel)
        self.btn_edit_close.pack(side="right")

        meta_row = TFrame(inner, self.theme, bg_key="surface")
        meta_row.pack(side="top", fill="x", pady=(S(9), S(11)))
        self.edit_role_chip = Chip(meta_row, self.theme, text="未选择消息",
                                   bg_key="surface_3", fg_key="text_2",
                                   font=self.fonts.small_bold)
        self.edit_role_chip.pack(side="left")
        self.edit_meta_label = TLabel(meta_row, self.theme, text="", bg_key="surface",
                                      fg_key="text_3", font=self.fonts.small)
        self.edit_meta_label.pack(side="left", padx=(S(9), 0))

        foot = TFrame(inner, self.theme, bg_key="surface")
        foot.pack(side="bottom", fill="x", pady=(S(12), 0))
        self.edit_count = TLabel(foot, self.theme, text="", bg_key="surface",
                                 fg_key="text_3", font=self.fonts.tiny)
        self.edit_count.pack(side="left")
        self.btn_cancel = FlatButton(foot, self.theme, text="取消", variant="ghost",
                                     font=self.fonts.ui, command=self._cancel_edit)
        self.btn_cancel.pack(side="right")
        self.btn_revert = FlatButton(foot, self.theme, text="还原", variant="ghost",
                                     font=self.fonts.ui, command=self._revert_edit)
        self.btn_revert.pack(side="right", padx=(0, S(6)))
        self.btn_apply = FlatButton(foot, self.theme, text="应用修改", variant="primary",
                                    font=self.fonts.ui_bold, command=self._apply_edit)
        self.btn_apply.pack(side="right", padx=(0, S(6)))

        self.edit_border = TFrame(inner, self.theme, bg_key="border_strong")
        self.edit_border.pack(side="top", fill="both", expand=True)
        self.edit_text = tk.Text(
            self.edit_border, wrap="word", bd=0, relief="flat", font=self.fonts.content,
            padx=S(12), pady=S(10), highlightthickness=0, insertwidth=S(1),
            width=30, height=8,
            spacing1=0, spacing2=S(5), spacing3=0, undo=True,
        )
        self.edit_scroll = ttk.Scrollbar(self.edit_border, orient="vertical",
                                         command=self.edit_text.yview,
                                         style="Side.Vertical.TScrollbar")
        self.edit_text.configure(yscrollcommand=self.edit_scroll.set)
        self.edit_scroll.pack(side="right", fill="y", pady=1, padx=(0, 1))
        self.edit_text.pack(side="left", fill="both", expand=True, padx=1, pady=1)

        self.edit_text.bind("<KeyRelease>", self._on_edit_change)
        self.edit_text.bind("<<Modified>>", self._on_edit_change)
        self.edit_text.bind("<FocusIn>", self._on_edit_focus)
        self.edit_text.bind("<FocusOut>", self._on_edit_blur)
        self.edit_text.bind("<Control-Return>", lambda e: self._apply_edit())
        self._set_edit_enabled(False)

    def _on_edit_focus(self, _event=None):
        self.edit_border.set_bg_key("accent")

    def _on_edit_blur(self, _event=None):
        self.edit_border.set_bg_key("border_strong")

    def _set_edit_enabled(self, enabled):
        self.btn_apply.set_enabled(enabled)
        self.btn_revert.set_enabled(enabled)
        self.btn_cancel.set_enabled(enabled)

    # ══════════════════════════ 右键菜单 ══════════════════════════
    def _build_context_menu(self):
        menu = tk.Menu(self.root, tearoff=0, font=self.fonts.ui)
        menu.add_command(label="复制选中文字", command=self.copy_selected)
        menu.add_command(label="复制整条消息", command=self.copy_message)
        menu.add_command(label="复制全部消息", command=self.copy_all)
        menu.add_separator()
        menu.add_command(label="编辑这条消息", command=self.edit_message_under_cursor)
        menu.add_separator()
        menu.add_command(label="搜索…", command=self.focus_search)
        self.ctx_menu = menu
        self.ctx_index = None
        self.theme.subscribe(self._paint_menu)

    def _paint_menu(self, pal):
        for menu in (getattr(self, "ctx_menu", None),):
            if menu is None:
                continue
            menu.configure(
                bg=pal["surface"], fg=pal["text"],
                activebackground=pal["accent_soft"], activeforeground=pal["accent"],
                disabledforeground=pal["text_3"],
                borderwidth=0, relief="flat",
                selectcolor=pal["accent"],
            )

    # ══════════════════════════ 主题应用 ══════════════════════════
    def _apply_ttk(self, pal):
        style = self.style
        for name, trough in (("Chat.Vertical.TScrollbar", pal["bg"]),
                             ("Side.Vertical.TScrollbar", pal["surface"])):
            style.configure(name, background=pal["thumb"], troughcolor=trough,
                            bordercolor=trough, lightcolor=pal["thumb"],
                            darkcolor=pal["thumb"], arrowcolor=pal["text_3"],
                            relief="flat", width=S(11), arrowsize=S(10))
            style.map(name, background=[("pressed", pal["thumb_hover"]),
                                        ("active", pal["thumb_hover"]),
                                        ("!active", pal["thumb"])])

    def _apply_text_theme(self, pal):
        area = self.text_area
        area.configure(
            bg=pal["bg"], fg=pal["text"], insertbackground=pal["accent"],
            selectbackground=pal["select"], selectforeground=pal["text"],
            inactiveselectbackground=pal["select"], highlightthickness=0,
            font=self.fonts.content,
        )
        area.tag_configure("gap", font=self.fonts.gap)
        area.tag_configure("body", font=self.fonts.content, foreground=pal["text"],
                           lmargin1=S(13), lmargin2=S(13), rmargin=S(26),
                           spacing1=S(1), spacing2=S(6), spacing3=S(2), justify="left")
        area.tag_configure("body_dim", font=self.fonts.content_italic, foreground=pal["text_2"])
        area.tag_configure("ital", font=self.fonts.content_italic, foreground=pal["text_2"])
        for key in ("user", "ai", "sys", "other"):
            area.tag_configure("chip_" + key, font=self.fonts.chip, foreground=pal[key],
                               background=pal[key + "_soft"], spacing1=S(15), spacing3=S(7))
        area.tag_configure("hdr_meta", font=self.fonts.chip_plain, foreground=pal["text_3"],
                           spacing1=S(15), spacing3=S(7))
        area.tag_configure("hdr_edited", font=self.fonts.chip, foreground=pal["accent"],
                           background=pal["accent_soft"])
        area.tag_configure("date_chip", justify="center", font=self.fonts.small_bold,
                           foreground=pal["text_2"], background=pal["surface_3"],
                           spacing1=S(22), spacing3=S(13))
        area.tag_configure("hdr_line", spacing1=S(15), spacing3=S(7))
        area.tag_configure("date_line", justify="center", spacing1=S(22), spacing3=S(13))
        area.tag_configure("quote", foreground=self._quote_color(pal))
        area.tag_configure("flash", background=pal["flash"])
        area.tag_configure("hl", background=pal["hl"], foreground=pal["hl_fg"])
        area.tag_configure("hl_cur", background=pal["hl_cur"], foreground=pal["hl_fg"])

        self.edit_text.configure(
            bg=pal["surface_2"], fg=pal["text"], insertbackground=pal["accent"],
            selectbackground=pal["select"], selectforeground=pal["text"],
            font=self.fonts.content, spacing2=S(5),
        )

    def _apply_side_theme(self, pal):
        area = self.side_text
        area.configure(bg=pal["surface"], fg=pal["text"], highlightthickness=0,
                       selectbackground=pal["select"], font=self.fonts.small,
                       spacing1=0, spacing2=0, spacing3=0)
        area.tag_configure("row", font=self.fonts.small, spacing1=S(4), spacing3=S(4),
                           lmargin1=S(10), lmargin2=S(10), rmargin=S(4))
        area.tag_configure("pad", font=self.fonts.small)
        area.tag_configure("num", font=self.fonts.small_bold, foreground=pal["text_3"])
        area.tag_configure("prev", font=self.fonts.small, foreground=pal["text_2"])
        area.tag_configure("prev_edited", font=self.fonts.small_bold, foreground=pal["accent"])
        area.tag_configure("empty", font=self.fonts.small, foreground=pal["text_3"],
                           justify="center", spacing1=S(24))
        for key in ("user", "ai", "sys", "other"):
            area.tag_configure("dot_" + key, font=self.fonts.small_bold, foreground=pal[key])
        area.tag_configure("hover", background=pal["surface_2"])
        area.tag_configure("sel", background=pal["accent_soft"])
        area.tag_configure("sel_num", font=self.fonts.small_bold, foreground=pal["accent"])

    def _apply_font_dependent_styles(self):
        pal = self.theme.pal
        self._apply_text_theme(pal)
        self._apply_side_theme(pal)
        self._draw_art(pal)

    # ══════════════════════════ 工具 ══════════════════════════
    @staticmethod
    def _editable(widget):
        class _Guard:
            def __enter__(guard):
                guard.was = str(widget.cget("state"))
                if guard.was == "disabled":
                    widget.configure(state="normal")
                return widget

            def __exit__(guard, *_exc):
                if guard.was == "disabled":
                    widget.configure(state="disabled")
                return False
        return _Guard()

    def _set_status(self, text):
        self.lbl_status.configure(text=text)

    # ══════════════════════════ 文件操作 ══════════════════════════
    def open_file(self):
        initial = self._last_dir if (self._last_dir and os.path.isdir(self._last_dir)) else None
        filepath = filedialog.askopenfilename(
            title="打开聊天记录 JSON",
            initialdir=initial,
            filetypes=[("JSON 聊天记录", "*.json"), ("所有文件", "*.*")],
        )
        if filepath and os.path.isfile(filepath):
            self._load_json(filepath)

    def _on_drop(self, event):
        data = event.data or ""
        for path in self.root.tk.splitlist(data):
            path = path.strip().strip("{}")
            if os.path.isfile(path) and path.lower().endswith(".json"):
                self._load_json(path)
                return
        messagebox.showwarning("格式不支持", "请拖入酒馆导出的 .json 聊天文件。")

    def _on_drag_enter(self, _event=None):
        self._set_status("松开鼠标即可打开该 JSON 文件")
        self.toolbar_line.set_bg_key("accent")

    def _on_drag_leave(self, _event=None):
        self.toolbar_line.set_bg_key("border")
        self._refresh_status_counts()

    def _load_json(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except json.JSONDecodeError as exc:
            messagebox.showerror("JSON 解析错误", "无法解析 JSON 文件：\n%s" % exc)
            return
        except Exception as exc:
            messagebox.showerror("读取错误", "无法读取文件：\n%s" % exc)
            return

        try:
            chat_data = extract_messages(data)
        except Exception as exc:
            messagebox.showerror("数据格式错误",
                                 "无法识别聊天数据格式，请确认是酒馆(SillyTavern)导出的 JSON。\n\n错误：%s" % exc)
            return

        self.chat_data = chat_data
        self.messages = chat_data["messages"]
        self.edited = {}
        self.current_file = filepath
        self.edit_msg_index = None
        self.side_selected = None
        self._last_dir = os.path.dirname(os.path.abspath(filepath))
        self.settings["last_dir"] = self._last_dir

        name = display_title(chat_data, filepath)
        self.root.title("%s · %s" % (ellipsis(name, 40), APP_NAME))
        self._update_infobar()
        self._clear_edit_panel()
        self.refresh_display()
        self._set_sidebar_visible(self._want_sidebar)
        self._set_status("已加载 %s" % ellipsis(os.path.basename(filepath), 60))
        self._update_saved_chip()
        self.text_area.see("1.0")

    def save_file(self):
        if not self.current_file or not self.chat_data:
            messagebox.showinfo("提示", "请先打开一个聊天文件。")
            return
        if not self.edited:
            messagebox.showinfo("提示", "没有需要保存的修改。")
            return

        count = len(self.edited)
        if not messagebox.askyesno(
                "确认保存",
                "共有 %d 条消息被修改。\n\n将覆盖写入：\n%s\n\n确认保存？" % (count, self.current_file)):
            return

        try:
            raw = self.chat_data["raw"]
            for idx, new_content in self.edited.items():
                if idx >= len(self.messages):
                    continue
                msg = self.messages[idx]
                msg["content"] = new_content
                chunk_id = msg.get("_chunk_id")
                for block in raw.get("messages", []) or []:
                    if chunk_id and block.get("chunk_id") != chunk_id:
                        continue
                    for item in block.get("messages", []) or []:
                        if (item.get("createAt") == msg.get("createAt")
                                and item.get("role") == msg.get("role")):
                            item["content"] = new_content

            with open(self.current_file, "w", encoding="utf-8") as handle:
                json.dump(raw, handle, ensure_ascii=False)
        except Exception as exc:
            messagebox.showerror("保存失败", "保存时发生错误：\n%s" % exc)
            return

        self.edited = {}
        self.refresh_display(keep_scroll=True)
        self._update_saved_chip()
        self._set_status("已保存 %d 条修改 → %s" % (count, os.path.basename(self.current_file)))
        if self.edit_msg_index is not None:
            self._open_message_for_edit(self.edit_msg_index)

    # ══════════════════════════ 渲染 ══════════════════════════
    ITALIC_RE = re.compile(r"\*([^*\n]{1,300})\*")
    QUOTE_RE = re.compile(
        "“([^”]{1,2000}?)”"
        "|\"([^\"]{1,2000}?)\""
        "|「([^」]{1,2000}?)」"
        "|『([^』]{1,2000}?)』",
        re.S)

    def _iter_visible(self):
        key = self.filter_key
        term = self._search_term().lower()
        for msg in self.messages:
            role = msg.get("role", "")
            if key == "user" and role != "user":
                continue
            if key == "assistant" and role != "assistant":
                continue
            if key == "system" and role in ("user", "assistant"):
                continue
            if term:
                content = self.edited.get(msg["_index"], msg.get("content", "")) or ""
                if term not in content.lower():
                    continue
            yield msg

    def refresh_display(self, keep_scroll=False):
        area = self.text_area
        previous = area.yview()[0] if keep_scroll else 0.0
        self.visible = list(self._iter_visible())

        with self._editable(area):
            area.delete("1.0", "end")
            self.blocks = {}
            self.line_blocks = []

            if not self.messages:
                area.configure(state="disabled")
                self._show_empty_state()
                self.side_rows = []
                self._render_sidebar()
                self._refresh_status_counts()
                return

            self._hide_empty_state()
            last_date = None
            for msg in self.visible:
                idx = msg["_index"]
                role = msg.get("role", "")
                meta = role_meta(role)
                color = meta["color"]
                raw_content = self.edited.get(idx, msg.get("content", "")) or ""
                content = raw_content.rstrip()
                internal = bool(msg.get("isInternalMessage"))

                created = msg.get("createAt")
                key = date_key(created)
                start = area.index("end-1c")
                if key and key != last_date:
                    last_date = key
                    area.insert("end", " ", ("date_line",))
                    area.window_create("end", window=Chip(
                        area, self.theme, text=date_label(created), on_key="bg",
                        bg_key="surface_3", fg_key="text_2", font=self.fonts.small_bold))
                    area.insert("end", " \n", ("date_line",))
                    start = area.index("end-1c")

                area.window_create("end", window=Chip(
                    area, self.theme, text="%s %s" % (DOT, meta["cn"]), on_key="bg",
                    bg_key=color + "_soft", fg_key=color, font=self.fonts.chip))
                if internal:
                    area.window_create("end", window=Chip(
                        area, self.theme, text="内部", on_key="bg",
                        bg_key=color + "_soft", fg_key=color, font=self.fonts.chip),
                        padx=S(4))
                bits = [bit for bit in (time_label(created), "#%d" % (idx + 1)) if bit]
                area.insert("end", "    " + "   ·   ".join(bits), ("hdr_meta",))
                if idx in self.edited:
                    area.window_create("end", window=Chip(
                        area, self.theme, text="已修改", on_key="bg",
                        bg_key="accent_soft", fg_key="accent", font=self.fonts.chip),
                        padx=S(6))
                area.insert("end", "\n", ("hdr_line",))

                body_tags = ("body",) + (("body_dim",) if (internal or role == "system") else ())
                body_start = area.index("end-1c")
                if content:
                    area.insert("end", content, body_tags)
                    for match in self.ITALIC_RE.finditer(content):
                        if match.group(1).strip():
                            area.tag_add("ital",
                                         "%s+%dc" % (body_start, match.start(1)),
                                         "%s+%dc" % (body_start, match.end(1)))
                    if self.settings.get("quote_highlight", True):
                        for match in self.QUOTE_RE.finditer(content):
                            for group in range(1, 5):
                                if match.group(group) and match.group(group).strip():
                                    area.tag_add("quote",
                                                 "%s+%dc" % (body_start, match.start(group)),
                                                 "%s+%dc" % (body_start, match.end(group)))
                                    break
                area.insert("end", "\n", body_tags)
                area.insert("end", "\n", ("gap",))

                end = area.index("end-1c")
                self.blocks[idx] = (start, end)
                self.line_blocks.append((int(start.split(".")[0]),
                                         int(end.split(".")[0]), idx))

            area.configure(state="disabled")

        if keep_scroll and previous:
            area.yview_moveto(previous)
        else:
            area.see("1.0")
        self._render_sidebar()
        self._apply_search_highlights()
        self._refresh_status_counts()

    def _render_sidebar(self):
        area = self.side_text
        with self._editable(area):
            area.delete("1.0", "end")
            self.side_rows = []
            self.side_hover_line = None
            pad = " " * 90
            if not self.visible:
                area.insert("end", "没有符合条件的消息\n", ("empty",))
            for msg in self.visible:
                idx = msg["_index"]
                color = role_color_key(msg.get("role", ""))
                content = self.edited.get(idx, msg.get("content", "")) or ""
                preview = ellipsis(content, 48) or "（空消息）"
                area.insert("end", "%s " % DOT, ("dot_" + color, "row"))
                area.insert("end", str(idx + 1), ("num", "row"))
                area.insert("end", "   ", ("row",))
                prev_tags = ("prev_edited", "row") if idx in self.edited else ("prev", "row")
                area.insert("end", preview, prev_tags)
                area.insert("end", pad, ("pad", "row"))
                area.insert("end", "\n", ("row",))
                self.side_rows.append(idx)
            area.configure(state="disabled")
            area.xview_moveto(0)

        self.side_count.configure(text="%d" % len(self.side_rows))
        if self.side_selected in self.side_rows:
            self._mark_side_line(self.side_rows.index(self.side_selected) + 1)
        else:
            self.side_selected = None

    def _mark_side_line(self, line):
        area = self.side_text
        with self._editable(area):
            area.tag_remove("sel", "1.0", "end")
            area.tag_remove("sel_num", "1.0", "end")
            if line and 1 <= line <= len(self.side_rows):
                area.tag_add("sel", "%d.0" % line, "%d.end" % line)
                area.tag_add("sel_num", "%d.0" % line, "%d.end" % line)

    def _refresh_status_counts(self):
        total = len(self.messages)
        shown = len(self.visible)
        if not total:
            self.lbl_info.configure(text="")
            return
        users = sum(1 for m in self.messages if m.get("role") == "user")
        bots = sum(1 for m in self.messages if m.get("role") == "assistant")
        text = "显示 %d/%d 条   ·   用户 %d   ·   助手 %d" % (shown, total, users, bots)
        if shown != total:
            text += "   ·   已筛选"
        self.lbl_info.configure(text=text)

    def _update_infobar(self):
        if not self.chat_data:
            self._set_infobar_visible(False)
            return
        name = display_title(self.chat_data, self.current_file)
        self.info_title.configure(text=ellipsis(name, 40))
        model = self.chat_data.get("model") or ""
        self.info_model.configure(text=ellipsis(model, 26) if model else "未知模型")
        exported = parse_exported_at(self.chat_data.get("exported_at"))
        self.info_time.configure(text=("导出 " + exported) if exported else "")
        self._set_infobar_visible(True)

    def _update_saved_chip(self):
        count = len(self.edited)
        if count:
            self.lbl_saved.configure(text="%d 条未保存" % count)
            self.lbl_saved.pack(side="right", padx=(0, S(12)))
            self.btn_save.set_variant("primary")
        else:
            self.lbl_saved.pack_forget()
            self.btn_save.set_variant("default")

    def _show_empty_state(self):
        self.chat_frame.pack_forget()
        self.empty_state.pack(side="left", fill="both", expand=True)
        self._set_infobar_visible(False)
        self._refresh_status_counts()

    def _hide_empty_state(self):
        self.empty_state.pack_forget()
        self.chat_frame.pack(side="left", fill="both", expand=True)

    def _set_sidebar_visible(self, visible):
        visible = bool(visible)
        if visible:
            self.sidebar.pack(side="left", fill="y", before=self.stage)
            self.sidebar_line.pack(side="left", fill="y", before=self.stage)
        else:
            self.sidebar.pack_forget()
            self.sidebar_line.pack_forget()
        self.btn_sidebar.set_on(visible)
        self.settings["show_sidebar"] = visible

    def _set_edit_panel_visible(self, visible):
        if visible:
            self.edit_panel.pack(side="right", fill="y")
            self.edit_line.pack(side="right", fill="y")
        else:
            self.edit_panel.pack_forget()
            self.edit_line.pack_forget()

    # ══════════════════════════ 列表交互 ══════════════════════════
    def _side_line_at(self, x, y):
        try:
            index = self.side_text.index("@%d,%d" % (x, y))
        except Exception:
            return None
        line = int(index.split(".")[0])
        if 1 <= line <= len(self.side_rows):
            return line
        return None

    def _on_side_click(self, event):
        line = self._side_line_at(event.x, event.y)
        if not line:
            return
        self._select_message(self.side_rows[line - 1], jump=True, line=line)
        self.side_text.focus_set()

    def _on_side_double_click(self, event):
        line = self._side_line_at(event.x, event.y)
        if not line:
            return "break"
        idx = self.side_rows[line - 1]
        self._select_message(idx, jump=True, line=line)
        self._open_message_for_edit(idx)
        return "break"

    def _on_side_motion(self, event):
        line = self._side_line_at(event.x, event.y)
        if line == self.side_hover_line:
            return
        area = self.side_text
        with self._editable(area):
            if self.side_hover_line:
                area.tag_remove("hover", "%d.0" % self.side_hover_line,
                                "%d.end" % self.side_hover_line)
            if line:
                area.tag_add("hover", "%d.0" % line, "%d.end" % line)
        self.side_hover_line = line

    def _on_side_leave(self, _event=None):
        if self.side_hover_line:
            area = self.side_text
            with self._editable(area):
                area.tag_remove("hover", "%d.0" % self.side_hover_line,
                                "%d.end" % self.side_hover_line)
            self.side_hover_line = None

    def _on_side_key(self, event):
        if not self.side_rows:
            return
        keysym = event.keysym
        current = self.side_rows.index(self.side_selected) + 1 if self.side_selected in self.side_rows else 0
        if keysym == "Up":
            line = max(1, (current or len(self.side_rows)) - 1)
        elif keysym == "Down":
            line = min(len(self.side_rows), current + 1)
        else:
            if current:
                self._open_message_for_edit(self.side_rows[current - 1])
            return "break"
        self._select_message(self.side_rows[line - 1], jump=True, line=line)
        return "break"

    def _select_message(self, idx, jump=True, line=None):
        self.side_selected = idx
        if line is None and idx in self.side_rows:
            line = self.side_rows.index(idx) + 1
        self._mark_side_line(line)
        if line:
            self.side_text.see("%d.0" % line)
            self.side_text.xview_moveto(0)
        if jump:
            self._scroll_to_message(idx)

    def _scroll_to_message(self, idx):
        block = self.blocks.get(idx)
        area = self.text_area
        if not block:
            return
        area.see(block[0])
        info = area.dlineinfo(block[0])
        if info:
            line_height = self._line_height()
            wanted = max(S(24), int(area.winfo_height() * 0.16))
            shift = int(round((info[1] - wanted) / float(line_height)))
            if shift:
                area.yview_scroll(shift, "units")
        self._flash_block(idx)

    def _line_height(self):
        return max(8, int(self.fonts.content_size * DPI_SCALE * 1.42))

    def _flash_block(self, idx):
        block = self.blocks.get(idx)
        if not block:
            return
        area = self.text_area
        with self._editable(area):
            area.tag_remove("flash", "1.0", "end")
            area.tag_add("flash", block[0], block[1])
        if self._flash_job:
            try:
                self.root.after_cancel(self._flash_job)
            except Exception:
                pass
        self._flash_job = self.root.after(1500, self._clear_flash)

    def _clear_flash(self):
        self._flash_job = None
        with self._editable(self.text_area):
            self.text_area.tag_remove("flash", "1.0", "end")

    # ══════════════════════════ 正文交互 ══════════════════════════
    def _on_text_click(self, event):
        try:
            self.cursor_index = self.text_area.index("@%d,%d" % (event.x, event.y))
        except Exception:
            self.cursor_index = None

    def _on_text_double_click(self, event):
        self._on_text_click(event)
        if not self.edit_mode.get():
            return
        idx = self._cursor_msg_index()
        if idx is not None:
            self._open_message_for_edit(idx)

    def _cursor_msg_index(self):
        index = self.cursor_index
        if not index:
            return None
        try:
            line = int(index.split(".")[0])
        except (ValueError, AttributeError):
            return None
        for start_line, end_line, idx in self.line_blocks:
            if start_line <= line <= end_line:
                return idx
        return None

    def _show_context_menu(self, event):
        self._on_text_click(event)
        idx = self._cursor_msg_index()
        self.ctx_index = idx
        try:
            self.ctx_menu.entryconfigure(4, state="normal" if idx is not None else "disabled")
            self.ctx_menu.entryconfigure(1, state="normal" if idx is not None else "disabled")
        except Exception:
            pass
        try:
            self.ctx_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.ctx_menu.grab_release()

    def edit_message_under_cursor(self):
        idx = self.ctx_index if self.ctx_index is not None else self._cursor_msg_index()
        if idx is None:
            idx = self.side_selected
        if idx is None:
            messagebox.showinfo("提示", "请把光标放在要编辑的消息上。")
            return
        self._select_message(idx, jump=False)
        self._open_message_for_edit(idx)

    # ══════════════════════════ 编辑 ══════════════════════════
    def toggle_edit_mode(self):
        enabled = not self.edit_mode.get()
        self.edit_mode.set(enabled)
        self.btn_edit.set_on(enabled)
        if enabled:
            self._set_edit_panel_visible(True)
            if not self.sidebar.winfo_ismapped() and self.messages:
                self._set_sidebar_visible(True)
            self._set_status("编辑模式已开启 · 双击消息或在列表中双击即可编辑")
            if self.side_selected is not None:
                self._open_message_for_edit(self.side_selected)
        else:
            self._close_edit_panel()
            self._set_status("编辑模式已关闭")

    def _open_message_for_edit(self, idx):
        if idx is None or idx < 0 or idx >= len(self.messages):
            return
        if not self.edit_mode.get():
            self.edit_mode.set(True)
            self.btn_edit.set_on(True)
        self.edit_msg_index = idx
        msg = self.messages[idx]
        meta = role_meta(msg.get("role", ""))
        content = self.edited.get(idx, msg.get("content", "")) or ""

        self.edit_role_chip.set_keys(bg_key=meta["color"] + "_soft", fg_key=meta["color"])
        self.edit_role_chip.configure(text="%s %s" % (DOT, meta["cn"]))
        stamp = parse_timestamp(msg.get("createAt"))
        self.edit_meta_label.configure(text=("#%d" % (idx + 1)) + (("   " + stamp) if stamp else ""))

        self.edit_text.delete("1.0", "end")
        self.edit_text.insert("1.0", content)
        try:
            self.edit_text.edit_reset()
            self.edit_text.edit_modified(False)
        except Exception:
            pass
        self._set_edit_panel_visible(True)
        self._on_edit_change()
        self.edit_text.focus_set()
        self.edit_text.see("1.0")

    def _clear_edit_panel(self):
        self.edit_msg_index = None
        self.edit_role_chip.set_keys(bg_key="surface_3", fg_key="text_2")
        self.edit_role_chip.configure(text="未选择消息")
        self.edit_meta_label.configure(text="")
        self.edit_text.delete("1.0", "end")
        self.edit_count.configure(text="")
        self._set_edit_enabled(False)

    def _close_edit_panel(self):
        self._clear_edit_panel()
        self._set_edit_panel_visible(False)
        self.edit_mode.set(False)
        self.btn_edit.set_on(False)

    def _cancel_edit(self):
        self._close_edit_panel()
        self._set_status("已退出编辑模式")

    def _on_edit_change(self, _event=None):
        if self.edit_msg_index is None:
            self.edit_count.configure(text="")
            self._set_edit_enabled(False)
            return
        current = self.edit_text.get("1.0", "end-1c")
        original = self.messages[self.edit_msg_index].get("content", "") or ""
        note = "  ·  与原文不同" if current != original else ""
        self.edit_count.configure(text="%d 字%s" % (len(current), note))
        self._set_edit_enabled(True)

    def _apply_edit(self):
        idx = self.edit_msg_index
        if idx is None:
            messagebox.showinfo("提示", "请先选择一条消息：在列表中双击，或在正文中右键选择「编辑这条消息」。")
            return
        new_content = self.edit_text.get("1.0", "end-1c")
        original = self.messages[idx].get("content", "") or ""
        if new_content == original:
            self.edited.pop(idx, None)
        else:
            self.edited[idx] = new_content
        self.refresh_display(keep_scroll=True)
        self._update_saved_chip()
        self._on_edit_change()
        if self.edited:
            self._set_status("已修改第 %d 条 · 共 %d 条待保存" % (idx + 1, len(self.edited)))
        else:
            self._set_status("第 %d 条已恢复原文 · 没有待保存的修改" % (idx + 1))

    def _revert_edit(self):
        if self.edit_msg_index is None:
            return
        original = self.messages[self.edit_msg_index].get("content", "") or ""
        self.edit_text.delete("1.0", "end")
        self.edit_text.insert("1.0", original)
        self._on_edit_change()
        self._set_status("已还原为原始内容（点击「应用修改」后生效）")

    # ══════════════════════════ 复制 ══════════════════════════
    def _copy_text(self, text, note):
        if not text:
            return False
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self._set_status("%s（%d 字符）" % (note, len(text)))
        return True

    def copy_selected(self):
        focused = None
        try:
            focused = self.root.focus_get()
        except Exception:
            focused = None
        if focused is self.edit_text or isinstance(focused, (tk.Entry, ttk.Entry)):
            return
        try:
            selected = self.text_area.get("sel.first", "sel.last")
        except tk.TclError:
            selected = ""
        if selected:
            self._copy_text(selected, "已复制选中内容")
            return
        idx = self.side_selected
        if idx is None:
            idx = self._cursor_msg_index()
        if idx is not None and idx < len(self.messages):
            content = self.edited.get(idx, self.messages[idx].get("content", "")) or ""
            self._copy_text(content, "已复制第 %d 条消息" % (idx + 1))
            return
        self._set_status("请先选中文字，或先在列表中定位一条消息")

    def copy_message(self):
        idx = self.ctx_index if self.ctx_index is not None else self.side_selected
        if idx is None or idx >= len(self.messages):
            self._set_status("没有可复制的消息")
            return
        content = self.edited.get(idx, self.messages[idx].get("content", "")) or ""
        self._copy_text(content, "已复制第 %d 条消息" % (idx + 1))

    def _transcript_text(self):
        chunks = []
        for msg in self.visible:
            idx = msg["_index"]
            meta = role_meta(msg.get("role", ""))
            content = (self.edited.get(idx, msg.get("content", "")) or "").rstrip()
            stamp = parse_timestamp(msg.get("createAt"))
            chunks.append("[%s · #%d%s]\n%s" % (meta["cn"], idx + 1,
                                                (" · " + stamp) if stamp else "", content))
        return "\n\n".join(chunks) + ("\n" if chunks else "")

    def _plain_text(self):
        chunks = []
        for msg in self.visible:
            idx = msg["_index"]
            content = (self.edited.get(idx, msg.get("content", "")) or "").strip()
            if content:
                chunks.append(content)
        return "\n\n".join(chunks) + ("\n" if chunks else "")

    def copy_all(self):
        if not self.visible:
            self._set_status("没有可复制的消息")
            return
        self._copy_text(self._transcript_text(), "已复制 %d 条消息" % len(self.visible))

    def _quote_color(self, pal=None):
        pal = pal or self.theme.pal
        color = (self.settings.get("quote_color") or "").strip()
        if re.match(r"^#[0-9a-fA-F]{6}$", color):
            return color
        return pal["accent"]

    def set_quote_color(self, value):
        self.settings["quote_color"] = (value or "").strip()
        save_settings(self.settings)
        self.btn_quote_color.set_color(self._quote_color())
        self._apply_text_theme(self.theme.pal)
        self._set_status("高亮颜色已%s" % ("恢复默认" if not value
                                         else "设为 " + self.settings["quote_color"]))

    def choose_quote_color(self):
        picked = colorchooser.askcolor(parent=self.root, title="选择引号高亮颜色",
                                       initialcolor=self._quote_color())
        hexval = (picked[1] or "").strip()
        if re.match(r"^#[0-9a-fA-F]{6}$", hexval):
            self.set_quote_color(hexval)

    def toggle_quote_highlight(self):
        enabled = not bool(self.settings.get("quote_highlight", True))
        self.settings["quote_highlight"] = enabled
        self.btn_quote.set_on(enabled)
        save_settings(self.settings)
        if self.messages:
            self.refresh_display(keep_scroll=True)
        self._set_status("引号高亮已%s" % ("开启" if enabled else "关闭"))

    def export_txt(self, _event=None):
        if not self.visible:
            messagebox.showinfo("提示", "没有可导出的消息。")
            return
        base = re.sub(r'[\\/:*?"<>|\s]+', "_",
                      display_title(self.chat_data, self.current_file))[:60] or "chat"
        path = filedialog.asksaveasfilename(
            parent=self.root, title="导出为 TXT",
            defaultextension=".txt", initialfile=base + ".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(self._plain_text())
        except Exception as exc:
            messagebox.showerror("导出失败", "写入文件时出错：\n%s" % exc)
            return
        self._set_status("已导出 %d 条消息 → %s" % (len(self.visible), os.path.basename(path)))

    # ══════════════════════════ 搜索 / 筛选 ══════════════════════════
    def _search_term(self):
        try:
            return self.search_box.text().strip()
        except Exception:
            return ""

    def focus_search(self, _event=None):
        self.search_box.focus_entry()

    def _on_search_escape(self):
        if not self._search_term():
            self.text_area.focus_set()

    def _on_search_change(self, _value):
        if self._filter_job:
            try:
                self.root.after_cancel(self._filter_job)
            except Exception:
                pass
        self._filter_job = self.root.after(220, self._apply_filter)

    def _apply_filter(self):
        self._filter_job = None
        if not self.messages:
            return
        self.refresh_display()

    def _on_filter_change(self, key):
        self.filter_key = key
        if not self.messages:
            return
        self.refresh_display()
        label = dict(FILTERS).get(key, key)
        self._set_status("筛选：%s" % label)

    def _apply_search_highlights(self):
        area = self.text_area
        term = self._search_term()
        with self._editable(area):
            area.tag_remove("hl", "1.0", "end")
            area.tag_remove("hl_cur", "1.0", "end")
        self.hl_ranges = []
        self.hl_pos = -1
        if not term:
            self.match_label.configure(text="")
            return
        found = []
        position = "1.0"
        while True:
            position = area.search(term, position, "end", nocase=True)
            if not position:
                break
            end = "%s+%dc" % (position, len(term))
            found.append((position, end))
            position = end
        if not found:
            self.match_label.configure(text="无匹配")
            return
        with self._editable(area):
            for start, end in found:
                area.tag_add("hl", start, end)
        self.hl_ranges = found
        self.match_label.configure(text="%d 处" % len(found))

    def _goto_highlight(self, index):
        if not self.hl_ranges:
            return
        index = index % len(self.hl_ranges)
        area = self.text_area
        start, end = self.hl_ranges[index]
        with self._editable(area):
            area.tag_remove("hl_cur", "1.0", "end")
            area.tag_add("hl_cur", start, end)
            area.see(start)
        self.hl_pos = index
        self.match_label.configure(text="%d/%d" % (index + 1, len(self.hl_ranges)))
        self._set_status("跳转到第 %d 处匹配（共 %d 处）" % (index + 1, len(self.hl_ranges)))

    def search_next(self):
        if not self.hl_ranges:
            self._apply_search_highlights()
            if not self.hl_ranges:
                term = self._search_term()
                if term:
                    self.match_label.configure(text="无匹配")
                    self._set_status("未找到：%s" % term)
                return
        self._goto_highlight(self.hl_pos + 1)

    def search_prev(self):
        if not self.hl_ranges:
            self.search_next()
            return
        self._goto_highlight(self.hl_pos - 1)

    # ══════════════════════════ 视图控制 ══════════════════════════
    def toggle_toolbar(self, _event=None):
        """隐藏 / 展开顶部操作栏（Ctrl+T）。"""
        self._set_toolbar_visible(not getattr(self, "_toolbar_visible", True))
        self._set_status("操作栏已%s" % ("隐藏" if not self._toolbar_visible else "显示"))

    def _set_toolbar_visible(self, visible):
        self._toolbar_visible = bool(visible)
        if self._toolbar_visible:
            self.btn_toolbar_show.place_forget()
            self.btn_toolbar_show.pack_forget()
            anchor = self.infobar if getattr(self, "_infobar_visible", False) else self.body
            self.toolbar.pack(side="top", fill="x", before=anchor)
            self.toolbar_line.pack(side="top", fill="x", before=anchor)
        else:
            self.toolbar.pack_forget()
            self.toolbar_line.pack_forget()
            self._place_toolbar_handle()
        self.settings["show_toolbar"] = self._toolbar_visible
        save_settings(self.settings)

    def _place_toolbar_handle(self):
        """操作栏隐藏时的「展开」把手：信息栏可见就贴在筛选器左侧，否则悬浮在右上角。"""
        handle = getattr(self, "btn_toolbar_show", None)
        if handle is None:
            return
        handle.place_forget()
        handle.pack_forget()
        if getattr(self, "_toolbar_visible", True):
            return
        if getattr(self, "_infobar_visible", False):
            handle.pack(in_=self.infobar_inner, side="right",
                        padx=(S(2), S(12)), pady=S(2))
        else:
            handle.place(in_=self.root, relx=1.0, x=-S(10), y=S(6), anchor="ne")

    def toggle_sidebar(self):
        self._set_sidebar_visible(not self.sidebar.winfo_ismapped())
        save_settings(self.settings)

    def toggle_theme(self):
        name = self.theme.toggle()
        self.settings["theme"] = name
        self._refresh_theme_button()
        self._apply_titlebar()
        save_settings(self.settings)
        self._set_status("已切换到%s主题" % ("深色" if name == "dark" else "浅色"))

    def _refresh_theme_button(self):
        self.btn_theme.configure(text="深色" if self.theme.name == "light" else "浅色")

    def _top_hwnd(self):
        """Tk 子窗口句柄不是顶层 HWND，标题栏属性必须设在 wm frame 上。"""
        try:
            return int(self.root.frame(), 16)
        except Exception:
            return None

    def _apply_titlebar(self):
        """Windows 10/11 下让原生标题栏跟随深色主题。"""
        if sys.platform != "win32":
            return
        hwnd = self._top_hwnd()
        if not hwnd:
            return
        try:
            import ctypes
            dark = 1 if self.theme.name == "dark" else 0
            value = ctypes.c_int(dark)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 20, ctypes.byref(value), ctypes.sizeof(value))
            corner = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 33, ctypes.byref(corner), ctypes.sizeof(corner))
        except Exception:
            pass

    def _apply_window_icon(self):
        """窗口 / 任务栏图标：优先用打包内嵌的 good.ico。"""
        try:
            base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
            ico = os.path.join(base, "good.ico")
            if not os.path.isfile(ico):
                return
            self.root.iconbitmap(default=ico)
            self.root.iconbitmap(ico)
        except Exception:
            pass

    def change_font_size(self, delta):
        before = self.fonts.content_size
        self.fonts.set_content_size(before + delta)
        if self.fonts.content_size == before:
            self._set_status("字号已到边界（9 - 20）")
            return
        self.settings["content_size"] = self.fonts.content_size
        self._apply_font_dependent_styles()
        self.refresh_display(keep_scroll=True)
        save_settings(self.settings)
        self._set_status("正文字号 %d pt" % self.fonts.content_size)

    def _on_mousewheel(self, event):
        delta = getattr(event, "delta", 0)
        if not delta:
            return
        steps = -3 if delta > 0 else 3
        try:
            widget = self.root.winfo_containing(event.x_root, event.y_root)
        except Exception:
            widget = None
        while widget is not None:
            if isinstance(widget, tk.Text):
                widget.yview_scroll(steps, "units")
                if widget is self.side_text:
                    widget.xview_moveto(0)
                return "break"
            widget = getattr(widget, "master", None)
        return None

    def _save_geometry(self):
        try:
            match = re.match(r"(\d+)x(\d+)", self.root.geometry())
            if not match:
                return
            self.settings["width"] = max(600, int(int(match.group(1)) / DPI_SCALE))
            self.settings["height"] = max(400, int(int(match.group(2)) / DPI_SCALE))
            save_settings(self.settings)
        except Exception:
            pass

    def _on_escape(self):
        if self.edit_panel.winfo_ismapped():
            self._close_edit_panel()
            return
        if self._search_term():
            self.search_box.clear()
            return
        self.side_selected = None
        self._mark_side_line(None)

    def _on_close(self):
        self._save_geometry()
        self.settings["theme"] = self.theme.name
        self.settings["content_size"] = self.fonts.content_size
        save_settings(self.settings)
        if self.edited:
            if not messagebox.askyesno(
                    "有未保存的修改",
                    "还有 %d 条消息的修改没有保存。\n\n确定要退出吗？" % len(self.edited)):
                return
        self.root.destroy()


# ══════════════════════════════════════════════════════════════════════════
#  入口
# ══════════════════════════════════════════════════════════════════════════
def main():
    filepath = None
    if len(sys.argv) > 1:
        candidate = sys.argv[1]
        if os.path.isfile(candidate):
            filepath = candidate
    ChatViewerApp(filepath=filepath)


if __name__ == "__main__":
    main()
