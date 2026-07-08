#!/usr/bin/env python3
"""
Hera - an RCL product
=====================
360° equirectangular → frames + cubemap extractor, the software companion to the
"Argus" rig. Wraps FFmpeg to turn equirectangular 360 video into SfM-ready
imagery, with per-camera cubemap orientation, a live 2D rig schematic, a
multi-camera test render, and a built-in AprilTag (tag36h11) sheet generator.

Standard library only at runtime (tkinter, subprocess, threading...). Needs
Python 3.8+ (Tk 8.6) and FFmpeg on PATH. Logos and the AprilTag patterns are
embedded as base64 so the script stays a single portable file.

Copyright (c) 2026 Rustin C. Newbold / Rusty's Creation Lab (RCL) Services.
Released under the MIT License (see LICENSE). Hera is an RCL product,
developed independently - not affiliated with or endorsed by any institution.
"""

import base64
import json
import math
import os
import shlex
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import queue
import webbrowser
import zlib
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import tkinter.font as tkfont

APP_NAME = "Hera"
APP_PRODUCT = "an RCL product"
APP_TAGLINE = "360° equirectangular → cubemap · companion to the Argus rig"
APP_VERSION = "2.7.0"
FFMPEG_URL = "https://ffmpeg.org/download.html"
CONFIG_PATH = Path.home() / ".hera_config.json"

# RCL Expanded Graphics Standard palette
BLACK = "#191303"; TAN = "#FFF9E8"; GOLD = "#FFC420"; BLUE = "#205BFF"
GREEN = "#2EFF20"; ORANGE = "#FF5520"; PAGE = "#F2EAD3"; CARD = TAN
LINE = "#E4D9B8"; INK = BLACK; MUTED = "#6E6750"; GREEN_TXT = "#1C8A12"
BLUE_DK = "#1746CC"; GOLD_DK = "#D99E00"

HERA_LOGO_B64 = ("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")
RCL_LOGO_B64 = ("iVBORw0KGgoAAAANSUhEUgAAAC8AAAAWCAYAAABQUsXJAAADnElEQVR4nM3XSYhdVRAG4O/e917aoW2NUxyIRBN0oUQccGVUVESc4sZh4U4RFETRjZtkoSJERIkgrgQRFIkKLuJAcEAQhIiCoqggxhHjQNQYu02n+z0XdY73+Lrf637dCBYc7r3n1KlTVafqr7pwK37Gh7gXl+M6XIHb8A6mcRcOR5XGqFSn5/GYQg+/Y2WaX4pMcCcew1dJaB578AQ2YcUyD8nKnyuU72IvTl+O3Lp434xXhNKvY2sf75K9g1Z6viUcsy89X07z7VEF1sIDbUyk9/vFVT6OL7EOHY2RVd9oFYoNUrqd9nfEDX+MQ7EznZP1GDkkM/MReAgn4Jak9CacOqKcxdA4tuG4EfYMPbCNtfi8mDsFq/GwuOIKs8X6NL7Gi3gprfeKZxtXiZssPVtjFR4UN3MxtiSZv2Ej/ijkzEtlnM0kxXMoVCJsThZJNog24CY8gns04bVSJOMZaa50VIV3BfL8gGNwVlqbssj4r+f57iVDsqd6wtsz+As7RJK9hi/SvhncjbPTvi4uwJU4YG6edHEZzkv7Z4t9OZEXpH4Lu33fWUhOyF9xDfan7wm8gXMS7wZ8IDx+Jn7BYXgOnw7Ro6dxZL9DB9KiGQsqY36vCK18Q500f5rw+Fha36VBpboYHcugUbC1l5TZiD+TIus1odHB+4n3KI1jdotwy3BY0lKc9w+NqvwEXhiwvh1vC6M64oYqgR7/CS3LcuHxPXgANwoDuyKBc3IeNGDvcqo1RlO+xiSuFYr+qInhXZpQ6olEzWtr0v6clFXxPQhVclVuFWOOsaP2E9MCXfaJRu1pUZmfxGcCu2t8K5KWwPITBZ7nmD84jak0SsoN4YJwuVjlS0HjIgGfFdi+Ps1vEVBZ4T1ciEMErN6R5j7CkThftAbZ6FxfugJatwlH5ZpQ477E25IQb1jcZaZLRIdJlOy1ov8nkGZ7ccD1eF4kbIWbRYWe1IRMVqgjkGgrbhC1ILcW89GleFMDy732EObyoANpw/5irSUq7Q5clNY341XNz8YOETarROh0RDLvxvea/qUrPD2bjCxrSXbMdJK5Gt9kJRaiGscWgn7qW2/jaE2R+m6AnDUCaidFgpcKtpKMQVSlc8fF394z+KSNpwyP/ez5TCv82+jc92TeMXN7/xlxa9mzY8LQjDiljEHKtwU4XI2T8Ggl+veFbqBc70eB/r2DUKLu41lITv9aT1Tu24XDdw7h/9/SuvzyNzYs5Nce6NdFAAAAAElFTkSuQmCC")           # black wordmark for UI (on tan)
APRILTAG_B64 = ("/5XFz6/T9///k9GHz6Xt//+R27/t9+P//43xsa2bz///i4eh67+7//+HnZOp46f///3TrcX79f//9/PXo/HX///vqfHBi6X//+21qd/dm///5eGL3aPz///hgbW7mdX//9+L7dnry///3Zel+b3B///ZrZe34a3//9e3z9ezo///083BldeP///L+aOTnef//8uD27Hv3f//wbn1z4mr//+/xa3t26H//73P542tl///ueXXy9GD//+xm/Hn6dH//6+nq4e7x///qcfT5bGp//+n042Fg5///6Pn/cOni///l7WJnePF//+Vv8G9tbv//43ro7n9k///6cWNq+HL///fhd/nzY///9W7+4Pl3f//zefdga21///L85Wf/6v//8n9zb/Rof//yYmF36OX//+538nZscf//7GV4/XLlf//qcHF85Ht//+h7afv2cX//5et+6vFif//k8Pr6ef1//+N5ZXH3df//4Ol6YPJm///8/2r/dfL///tqY37n6P//+m9/7nDj///3/WZ1dvd///Fl+mrp8f//73Dy6fvn///udm755OL//+xj9eDq9n//539i7vd9f//mZ21mdPX///16+Xr55n//+fDqeX1yf//yfGx25Op///Hh6OZt5X//7vH9dWh2f//udOt8/PP//+33eeTxcX//62fuc+xif//qbWrjdP1//+j1dPrydf//6PPxfmrm///laeJ87nL///138uHqaH//9uDmdv1i///2Y3R+8eB///Nz6W3scX//62Tnenzkf//ieHPvYXT///x763TrdH//+W7ua3ri///15H9p/m7///Rs6eF753//8P/seGr1///i9GJq5Wh///Tod/z/ev//8Xt68+7pf//idWz18fb///Rp4uhsaX//8H9z5u/1f//n8v/7dOX//+Lw+3F16n//+Ozx/Xfzf//q/nnn/eh///Z49Wf2d///9fvjb+r1f//vZHdk/e///+r89mt1+X//4u30eGZsf//88Wv98Gv///t5dnVt5H//8m/w8ebyf//s8HpvfHR///ni63f363//9vNgZvJ8f//1+Hx2e3d///No8WV2aH//7Wrlbnh4///s7XN2bPZ//+p6+f1zaf//5+tu7G36///u4Pd6c3F//+R87mZ1en///WhwY3zyf//2cWP47+z//+V17npk8H//4/348eJo///gc+nwZfT///Fte/JpYn//5Pb5ZXF+///m6n1pd/n///Hn5vFlZv//6nNo7mx+///p9fb2YPx///XqfXT18H///P13+2bpf//xYuPp8vl//+14dOh25X///u944uV1f//z8Ot+cHl//+v+++Nsbv//+/5p9Ph3f//w4mr4d/j//+1yZvX36X//9/H+5Xlz///ua2dp5v9///5qdXtzZ///7HL47+l3f//k/nrs8O9//+R5d+V+4f//9ur/cGR2///z+fDid3j///bmdPptaf///2x682l9f//o8e7ydGL///L0dOnqav//8+puZGpi///55XNh+HR//+jp/eNtd///63N7YfPq///0e31o8u3///tv4npwdX//+vJw4mTy///t/nv9Yez//+pse+x+7f//+HbifXzsf//v6Ot1ee3///3y8mZ37H///Hr8ffVk///rf+b/amh//+hxZnlx5////mz9ZXPw///ta3n0afh///NgcP95bf//8/ft9uD0///p7XbwZGH///9o9Orran//6Wn3ZXnjf//ndO/k63l//+994+V8an//923wY/jl///+9+7v9mV///Blff52e3//6mj15GB6///0a3t7duL//+V99P/uZf//+vly+nVuf///eXt2cXp///rh/21hbX//7Wln4Ov5///25upw7/R///9h+GF1/v//42Tu5Wbof//9ZP9x4Wn///z+8X9ibf//8+v3b+1h///x6nRqYP////tuZOzj9n//4Ov38mblf//wbfRr52t///N2Zv9g7///8X345WNn///+7Xvl6mF///F8dWh7eP///XRi4H/q///v6OF87eN//+/5d+/7bf//+ujidmLz///p+vxxdmP//+l1+Wpj9n//8ORpen3if//8eO/5cnZ///1p/v37YX//4m13fPpxf//8ZHN95nj//+x8aXHm9v//4+Tt9m5j///0dWts4vd///b9ZW7he3//42jv82L1///p8Hl/4uV///7xfPPmbv//5W/x9Hfkf///83Lj9Wn//+H68/R47X///en+b2J8///z6m/pdHh//+p3dXn/bH//5m5xY+/m///y5+tib23///Z8cvzy9f//9f1uYHhp///lcPvw6+5//+xgduxyaP//7HFs/3/zf//84uV5efr//+dv/Ptyd3//7WZ342l7///8ePF+fOv///Vi7/78dP//4PFo63Js///v4vpt42H//+5q9P14////6mTn+PF9///vZWlmaOp//+Tudnrt/3//+uptZvBof//l42HvaPL//+7vfuR36H//9GPtduTi///g+Wtnauf//+ftYPFg9P///2hu7WT1///jfuNuY/L//+lj9/tl8n//8Pb762pxf//06eD593V///ph+vLs5///4u3vbvlif//p+e1r9O////zpcXvrfH///+J3Z3p1f//h63v05ef//+5y5W1je3///u7mZ+xxf//+5WH0dnz//+N14XRxfn//6PHhdeVj///27n3q7vr///tiauHtbv//6Pzu9H33f//h6GFp/fT//+/u8Xpk+v//7Wf75X9w///16Xdo5Hd///T9Z/B14///6HFl/+N+f//1c37kdnB///Hrd/3r8H//83Z7+/Vw///l4Xbk7XT///Do+WXh9f//+nRrb+P8///59WZzaXD//+B2cuXi6f//4fFhZPfqf//1cWnscez//+5ndGpn83//7Pbg+fXnf//z6WLu63///+3r+2Vm6n//8vH7bmbjf//rZHZ56vD///ts6e99+P///Od26ejj///z7ej68fJ///x9ePX/an//+fvydXryf///93xxc2j//+z55W5+4H//7uNl8GBx///x6npk/Gx//+xpbHTx6n//7Wnkd3Rmf//z5PJ+9f3///J67HBx4v//6/zydP5n///jYvbj6nF//+/s923waH//6u9tcmD/f//s7mTj+33////15elhav///uT57PTkf//6Z/35Y2Z//+1g8WXs/P//+3vqYGfrf//g5XBx5fd///7na2D2c3//9uBr6X9hf//1ePR5YPT///Z/dH9m/P//5nNnb31s///283j/6er///V/+fvl+3//7uT4YPNof//m/2pqeXD//+9oY/plcf//5m72/+fq///86nrw42///+/97nLr9X//5OBi5uXjf//1bGbz9Pn///rk4nH04f//+/xuYer+///qcuZ++ur//+j29vzhe3//9fBqfW1t///y92Js9+///+FuaeD963//+PJjYPVm///k7uZs52X///v54fRrcf//4m10Y2lo///g4/Vm8ez//+np+nD1e///5urs4eL2///qa3z+5OZ///F6cm1od3///eRp7Xrof//18HL87v9//+VsemTn/v//83X9fOZt///g9fbh7+1//+L+e2Bv+3//8Wrx4GVzf//hY2Tt5uX//+104P/s8n//8OVh7PVx///l/On3duz//+X87WHrd///+2H49/D0f//ofPxpbOb//+Z/enF88n//4uRv8+Xp///+9uB45nL//+7xYnXi73//+3Tr+mvl///pa3b48+x///xocud/df//725t63bu///icvlj/u3///jw4+rh8X//5nb1YOR9f//6c2VqZ+7///3vZeJ3YX//+WD74G7pf//982HnZmT///p7cGXh+3//5Xf66mBv///9+mfh62R///XhcfN+aH//7fn4bPrs///wa2Lgc2V//+1jZm74d3//+2B+e25rf//i6Gl643N///B68GD64X///Xt+eu5k///t9vnj8OL//+niZ2Zu+///+GrvYPntf//2++709ur//+v/bvry43//5nZv4fNs///3//ry+GF//+Px//rncf//+PDyZulo///kbPN4c+7//+L0bOx0a///8Hzpee9p///gde3o/2d//+5iaeV98///9/p27+zkf//qY/7hcnL///H4/ub173//+mVndeT2f//4Zev3bnV///7x/Ptw43///2NxZOLp///+/en/6fR///jrdOlt+P//+vn1ff71f//48Xd0Z/1///DucPdrY///6ORx+Pvo///s6/vqZWn///L69udgaX//63Bl7Gnif//+fmz1aWN//+X1fPFgZ3//7mxiaPlzf//mdmbtfud//+lmaPpw9n//9WLm72d+f//ifvN1e2R///D9a+n85n//8XL/Y29y///ren/w6Wt//+vz6/d5fH//5Odh6+buf//vZGJ+Y+1///nwc+X84////eT47mt5////ZWT6bOL///Do/2N663//6v5r73N3f//wZ+5jYOV///535mR463//6f3keez4///hbWdifmP///NxZOhy8v//+nhs4/Lmf//9eel3Y+1//+F7/+xpcn///mn7aOr6f//3emphd3H//+n252H+ff//7XNgc2T+///nZGb0e3L///b6++l3bv//7+Nua/9m///ie+zn9Hj//+jk7+l2e3//43LvaXpgf//5c+H/feX//+91cnFmZP//82VvenJu///99P71+PB///797vv9aP//6uh87ud8///g/Gz7bnh//+7iY3D6ZH///f9iaPluf//y9+FreWR//+FyZPZmc3//5mr2fuhk///tdX7g8fz///p9aePrb///42b/5nV8f//3fW7n8+t//+Jr5PDlf3//5eht8+Vm///w+WfjYHZ//+/ve25yZP//8X1+7Hrsf//neH54dnz///lsaHlkeX//5/HqY+Z8///rYHTj9eF//+x1eWv8+n//9eVj/vzn///rYOj8evD///fu62xpe3//7eti9u7s///2+O7o4Hn//+rz7WZt4f//9Gpv8Xlg///8a//r8OR///l8cflt/n//+mjg/PHr///09vNp5uT////3fuJrb3///HBl6/Zof//3fHfjZfJ//+Bp4/j083//7efsZnH+f//v/HN5fHF///l2YfDy7///+n9n9uR5///n8XvybHR///d0Ym314P//5Wzg6HV////3e/nw83b//+ZhdvLve///7ed6df3mf//4Z+1heGj//+57YuDhYv//6vNj62L7///+a2Dqe+n///Zsdvh2Yn//4nlibfr7///q4eNwfHf//+d+4Wvxaf//8Gl3/uLv///jcfft+n5//+Vyen586P//+vzvbmhs///9b/d95PX///Rn4XP++P//6m5lfenq///sZWdxfft//+7pbedydH//+X764v9t///6YOX3ZXT//+hq8m5j/f///3p/62Jp///ycOJ0d+V///lnbnj9Yf//9XP1YHRu///6aWp8aW7///79ZWn19v//5Wnq++P4f//65GPwZ2t//+trbHVn8n//4f1qdHZw///2eHRidWl///Vm9G/wb3//8eh8+vpw///8eOd28/t///b9eX734f//+3b47eVrf//5cfzj/nd//+t5ceZu7H///nJ86H/2///jb2r18XF///9xYf5g93//7WLj7P7if//56XPsYGh//+lt/mR4fv//93L86ex8///y7vv+5G9///VheG70Zv//9OrsY29o///+ee9zZPr//+Pg52nm6///9XjtcPzo///3fO78afz///F3c2Z64P//+P9w6e5lf//4bvJzePn//+rr/OH75X//5GZvYevyf//+ZmvieGb//+l6YWtzZH//6m78/O5pf//v8Px25PF//+v67Gr9ef//7mjj63Drf//3Zf5/9XN//+L6fX9v5H//6nzsb+vhf//saW/i/G9///RpaXVien///2Z3+GL/f//1+WDh8uB///Zlb+V++v//5udg5G7h///3/vR45eh///j0bfDoaf//9eDj4+5nf//wdOf6Ze5//+3i7PVg4P//7u39Zu5w///6YPH4/3Z//+rmZOX34v///eT2aWn9f//3YnJo4nT///3o8fLh/3//9ehg/nT8f//473VlZHP///hg6u51bf//4unhY+jsf//+/HrjdmP//+Tr5HBs7v//7Ort7+Xqf//8ZnX45eT///z69Gvz8H//+n504+x+f//55fDp9vr///Bm+G/76P//+31t/O5if//i/mht6WZ/w==")      # 587 tag36h11 grids, 8 bytes each
RCL_BRAND_B64 = ("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")     # default branding for AprilTag sheets

FACES = [
    {"key": "front",  "mult": 4, "suffix": "front",  "label": "Front (+Z)"},
    {"key": "back",   "mult": 5, "suffix": "back",   "label": "Back (-Z)"},
    {"key": "left",   "mult": 1, "suffix": "left",   "label": "Left (-X)"},
    {"key": "right",  "mult": 0, "suffix": "right",  "label": "Right (+X)"},
    {"key": "top",    "mult": 2, "suffix": "top",    "label": "Top / Up (+Y)"},
    {"key": "bottom", "mult": 3, "suffix": "bottom", "label": "Bottom / Down (-Y)"},
]
FACE_KEYS = [f["key"] for f in FACES]
CROSS = {"top": (0, 1), "left": (1, 0), "front": (1, 1),
         "right": (1, 2), "back": (1, 3), "bottom": (2, 1)}
INTERP_CHOICES = ["nearest", "linear", "cubic", "lanczos", "spline16", "gaussian"]
SLOTS = [("Top", "top"), ("Middle", "mid"), ("Low", "low")]
RAW_360_EXTS = {".insv", ".insp", ".lrv"}

APRILTAG_N = 587
PAPER_SIZES = {  # (width_mm, height_mm)
    "Letter": (215.9, 279.4), "A4": (210.0, 297.0), "Legal": (215.9, 355.6),
    "A3": (297.0, 420.0), "A5": (148.0, 210.0),
}


def default_cam():
    return {"yaw": 0.0, "pitch": 0.0, "roll": 0.0, "faces": FACE_KEYS[:], "face_fov": 90.0}


DEFAULT_CONFIG = {
    "ffmpeg": "", "ffprobe": "", "fps": "1",
    "want_equirect": True, "want_cubemap": True,
    "interp": "cubic", "face_size": "", "jpeg_q": 2, "png_level": 6, "write_colmap": False,
    "eq_fmt": "JPEG", "cube_fmt": "JPEG",
    "output_dir": "", "prefix": "w1", "skip_intro": False,
    "rig_view": "side", "cam_target": "top",
    "tag_ids": "0-15", "tag_paper": "Letter", "tag_size_mm": "100",
    "tag_name": "Hera \u2022 tag {id}", "tag_dir": "", "tag_format": "PDF",
    "plan_units": "m", "plan_X": "8", "plan_Y": "10", "plan_Z": "3",
    "plan_height": "1.78", "plan_top_off": "0.55", "plan_bottom_off": "-0.75",
    "plan_eq_width": "7680",
}


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
def load_config():
    cfg = dict(DEFAULT_CONFIG)
    cfg["cams"] = {k: default_cam() for k in ("top", "mid", "low")}
    try:
        if CONFIG_PATH.exists():
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            for k, v in data.items():
                if k == "cams" and isinstance(v, dict):
                    for slot in ("top", "mid", "low"):
                        cv = v.get(slot, {})
                        cam = cfg["cams"][slot]
                        for a in ("yaw", "pitch", "roll"):
                            try:
                                cam[a] = float(cv.get(a, 0.0))
                            except Exception:
                                pass
                        fs = [f for f in cv.get("faces", FACE_KEYS) if f in FACE_KEYS]
                        cam["faces"] = fs or FACE_KEYS[:]
                        try:
                            cam["face_fov"] = float(cv.get("face_fov", 90.0))
                        except Exception:
                            cam["face_fov"] = 90.0
                elif k in cfg and k != "cams":
                    cfg[k] = v
    except Exception:
        pass
    return cfg


def save_config(cfg):
    try:
        CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# FFmpeg helpers
# --------------------------------------------------------------------------- #
def find_executable(name, configured):
    if configured and Path(configured).exists():
        return configured
    return shutil.which(name) or ""


def _no_window_kwargs():
    if os.name == "nt":
        return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}
    return {}


def open_in_file_manager(path):
    try:
        if os.name == "nt":
            os.startfile(path)  # noqa
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass


def ffmpeg_version(ffmpeg):
    if not ffmpeg:
        return ""
    try:
        out = subprocess.run([ffmpeg, "-version"], capture_output=True, text=True,
                             timeout=10, **_no_window_kwargs())
        return (out.stdout.splitlines()[0].strip() if out.stdout else "")
    except Exception:
        return ""


def ffprobe_duration(ffprobe, path):
    if not ffprobe:
        return None
    try:
        out = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(path)],
            capture_output=True, text=True, timeout=30, **_no_window_kwargs())
        val = out.stdout.strip()
        return float(val) if val and val.lower() != "n/a" else None
    except Exception:
        return None


def parse_fps(text):
    text = (text or "").strip()
    if not text:
        return False, "", 0.0
    try:
        if "/" in text:
            a, b = text.split("/", 1)
            value = float(a) / float(b)
        else:
            value = float(text)
        return (value > 0), text, (value if value > 0 else 0.0)
    except Exception:
        return False, text, 0.0


def _fmt(n):
    return ("%g" % round(float(n), 3))


def _v360_str(interp, face_size, yaw, pitch, roll):
    s = "v360=e:c6x1"
    if abs(yaw) > 1e-9:
        s += ":yaw=" + _fmt(yaw)
    if abs(pitch) > 1e-9:
        s += ":pitch=" + _fmt(pitch)
    if abs(roll) > 1e-9:
        s += ":roll=" + _fmt(roll)
    s += ":interp=" + interp
    if face_size:
        s += ":w=" + str(face_size * 6) + ":h=" + str(face_size)
    return s


FACE_DIR = {"front": (0, 0), "right": (90, 0), "back": (180, 0),
            "left": (-90, 0), "top": (0, 90), "bottom": (0, -90)}


def _norm_yaw(y):
    return ((float(y) + 180.0) % 360.0) - 180.0


def build_filtergraph(fps, want_eq, want_cube, faces, interp, face_size, yaw, pitch, roll, face_fov=90):
    # Overlapping faces (fov > 90°) require independent flat (rectilinear) projections.
    if want_cube and float(face_fov) > 90.5:
        return _flat_filtergraph(fps, want_eq, faces, interp, face_size, yaw, pitch, roll, face_fov)
    parts = []
    src = "[0:v]fps=" + str(fps)
    if want_eq and want_cube:
        parts.append(src + ",split=2[eq][cb]")
    elif want_eq:
        parts.append(src + "[eq]")
    else:
        parts.append(src + "[cb]")
    if want_cube:
        parts.append("[cb]" + _v360_str(interp, face_size, yaw, pitch, roll) + "[strip]")
        k = len(faces)
        labels = "".join("[s" + str(i) + "]" for i in range(k))
        parts.append("[strip]split=" + str(k) + labels)
        for i, face in enumerate(faces):
            parts.append("[s" + str(i) + "]crop=iw/6:ih:" + str(face["mult"]) + "*iw/6:0[" + face["key"] + "]")
    return ";".join(parts)


def _flat_face(label_in, out_key, interp, size, yaw, pitch, roll, fov):
    by, bp = FACE_DIR[out_key]
    fy = _norm_yaw(yaw + by)
    fp = max(-90.0, min(90.0, pitch + bp))
    s = "[%s]v360=e:flat:yaw=%s:pitch=%s" % (label_in, _fmt(fy), _fmt(fp))
    if abs(roll) > 1e-9:
        s += ":roll=" + _fmt(roll)
    s += ":h_fov=%s:v_fov=%s:w=%d:h=%d:interp=%s[%s]" % (_fmt(fov), _fmt(fov), int(size), int(size), interp, out_key)
    return s


def _flat_filtergraph(fps, want_eq, faces, interp, face_size, yaw, pitch, roll, fov):
    size = face_size or 1280
    labels = (["eq"] if want_eq else []) + ["c%d" % j for j in range(len(faces))]
    parts = ["[0:v]fps=%s,split=%d%s" % (fps, len(labels), "".join("[%s]" % l for l in labels))]
    for j, face in enumerate(faces):
        parts.append(_flat_face("c%d" % j, face["key"], interp, size, yaw, pitch, roll, fov))
    return ";".join(parts)


def build_command(ffmpeg, video, eqdir, cubedir, fps, want_eq, want_cube,
                  faces, interp, face_size, jpeg_q, png_level, yaw, pitch, roll, face_fov=90,
                  eq_fmt="JPEG", cube_fmt="JPEG"):
    graph = build_filtergraph(fps, want_eq, want_cube, faces, interp, face_size, yaw, pitch, roll, face_fov)
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(video),
           "-filter_complex", graph]
    if want_eq:
        if str(eq_fmt).upper() == "PNG":
            cmd += ["-map", "[eq]", "-compression_level", str(png_level),
                    "-start_number", "1", str(Path(eqdir) / "frame-%05d.png")]
        else:
            cmd += ["-map", "[eq]", "-c:v", "mjpeg", "-q:v", str(jpeg_q),
                    "-start_number", "1", str(Path(eqdir) / "frame-%05d.jpg")]
    if want_cube:
        for face in faces:
            if str(cube_fmt).upper() == "PNG":
                cmd += ["-map", "[" + face["key"] + "]", "-compression_level", str(png_level),
                        "-start_number", "1", str(Path(cubedir) / ("%05d_" + face["suffix"] + ".png"))]
            else:
                cmd += ["-map", "[" + face["key"] + "]", "-c:v", "mjpeg", "-q:v", str(jpeg_q),
                        "-start_number", "1", str(Path(cubedir) / ("%05d_" + face["suffix"] + ".jpg"))]
    cmd += ["-progress", "pipe:1", "-nostats"]
    return cmd


def build_test_command(ffmpeg, video, outdir, faces, interp, yaw, pitch, roll, size=170, face_fov=90):
    if float(face_fov) > 90.5:
        sz = max(120, min(240, size + 40))
        parts = ["[0:v]split=%d%s" % (len(faces), "".join("[c%d]" % j for j in range(len(faces))))]
        for j, face in enumerate(faces):
            parts.append(_flat_face("c%d" % j, face["key"], interp, sz, yaw, pitch, roll, face_fov))
    else:
        parts = ["[0:v]" + _v360_str(interp, size, yaw, pitch, roll) + "[strip]"]
        k = len(faces)
        parts.append("[strip]split=" + str(k) + "".join("[s" + str(i) + "]" for i in range(k)))
        for i, face in enumerate(faces):
            parts.append("[s" + str(i) + "]crop=iw/6:ih:" + str(face["mult"]) + "*iw/6:0[" + face["key"] + "]")
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(video),
           "-filter_complex", ";".join(parts)]
    for face in faces:
        cmd += ["-map", "[" + face["key"] + "]", "-frames:v", "1",
                str(Path(outdir) / ("test_" + face["suffix"] + ".png"))]
    return cmd


def colmap_cameras_txt(W, H, fov_deg):
    """Exact pinhole intrinsics for a square cube face of the given FOV."""
    f = (W / 2.0) / math.tan(math.radians(fov_deg) / 2.0)
    cx, cy = W / 2.0, H / 2.0
    return ("# COLMAP camera model - generated by Hera (RCL).\n"
            "# Every face in this folder is a distortion-free pinhole rendering with a\n"
            "# square %.1f deg field of view at %dx%d px, so the intrinsics below are\n"
            "# EXACT (fx = fy = (W/2)/tan(FOV/2); principal point at the image centre).\n"
            "# Use during feature extraction (shared intrinsics, calibration fixed):\n"
            "#   colmap feature_extractor ... --ImageReader.single_camera 1 \\\n"
            "#     --ImageReader.camera_model PINHOLE \\\n"
            "#     --ImageReader.camera_params \"%.6f,%.6f,%.6f,%.6f\"\n"
            "# Or import this file directly as a COLMAP cameras.txt (CAMERA_ID 1).\n"
            "# Format: CAMERA_ID MODEL WIDTH HEIGHT fx fy cx cy\n"
            "1 PINHOLE %d %d %.6f %.6f %.6f %.6f\n"
            % (fov_deg, W, H, f, f, cx, cy, W, H, f, f, cx, cy))


def display_command(cmd):
    return subprocess.list2cmdline(cmd) if os.name == "nt" else shlex.join(cmd)


# --------------------------------------------------------------------------- #
# AprilTag generation (tag36h11, embedded patterns, pure-stdlib renderer)
# --------------------------------------------------------------------------- #
_APRILTAG_BYTES = None


def _tag_bytes():
    global _APRILTAG_BYTES
    if _APRILTAG_BYTES is None:
        _APRILTAG_BYTES = base64.b64decode(APRILTAG_B64)
    return _APRILTAG_BYTES


def tag_grid(i):
    """Return the 8x8 grid (1=black) for tag36h11 id i (0..586)."""
    data = _tag_bytes()
    off = i * 8
    grid = []
    for byte in data[off:off + 8]:
        grid.append([(byte >> k) & 1 for k in range(7, -1, -1)])
    return grid


def parse_id_spec(text):
    """'0-9, 12, 15' -> ([0..9,12,15], error_or_None). Validates 0..586."""
    ids = []
    for chunk in (text or "").replace(";", ",").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            if "-" in chunk:
                a, b = chunk.split("-", 1)
                a, b = int(a), int(b)
                rng = range(a, b + 1) if a <= b else range(a, b - 1, -1)
                ids.extend(rng)
            else:
                ids.append(int(chunk))
        except ValueError:
            return [], "Could not read '" + chunk + "'. Use IDs like 0-9, 12, 15."
    out = []
    for i in ids:
        if not (0 <= i < APRILTAG_N):
            return [], "ID " + str(i) + " is out of range (tag36h11 has 0-" + str(APRILTAG_N - 1) + ")."
        if i not in out:
            out.append(i)
    if not out:
        return [], "No tag IDs given."
    return out, None


def build_tag_svg(i, size_mm):
    grid = tag_grid(i)
    cell = size_mm / 8.0
    rects = []
    for r in range(8):
        for c in range(8):
            if grid[r][c]:
                rects.append('<rect x="%.4f" y="%.4f" width="%.4f" height="%.4f"/>'
                             % (c * cell, r * cell, cell, cell))
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%fmm" height="%fmm" '
            'viewBox="0 0 %f %f" shape-rendering="crispEdges">'
            '<rect width="%f" height="%f" fill="#fff"/><g fill="#000">%s</g></svg>'
            % (size_mm, size_mm, size_mm, size_mm, size_mm, size_mm, "".join(rects)))


def brand_data_uri(mode, path):
    """For the on-screen SVG preview only (data URI). PDF uses _resolve_branding."""
    if mode == "none":
        return None, None
    if mode == "rcl":
        return "data:image/png;base64," + RCL_BRAND_B64, None
    try:
        ext = Path(path).suffix.lower()
        mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".gif": "image/gif", ".svg": "image/svg+xml"}.get(ext, "image/png")
        return "data:" + mime + ";base64," + base64.b64encode(Path(path).read_bytes()).decode(), None
    except Exception as exc:
        return None, "Could not read branding image: " + str(exc)


# --- pure-stdlib PNG decode (→ RGB, alpha flattened on white) --------------- #
# RealityScan / RealityCapture marker numbering for tag36h11.
# RS ranks the 587 tag payloads (as read by its own detector) in ascending
# order and labels each marker by that 1-based rank, displayed in hex - e.g.
# official AprilTag ID 0 is RS marker 506 = "36h11:1fa".  Verified against the
# numbering rule stated by a RealityCapture developer (payloads sorted
# ascending, first 0x0110bba61 / last 0xfece0e599) and a community lookup
# table (Epic Dev Community forums, "IDs of April Tags", 2023-2025).
RS_RANK_B64 = ("AfoCBAINAhUCKwI6AAgAKQBUAFwAhQCcAKMArgDDAMwA4gEBAQoBMQE7AUYBVwGGAZABqwG6AccB8QH9AhYAcgCkANoA+AECAQsBEAFYAYcBrAHRAfICBQIXAkUAPQBeAHMAnwEhAUcBWQGJAdoB7AA1AH0BDAEXAU0BWgFkAZcBrwHJAcoCAQA3ALsAxQD8AZgCLwBHAIkA0QDoASMCJADlARsCMADrAS0B1QIlAJQBnAC/AMcBSwGeAiYAQQBXAQ8BewCCALYAyQD+AXEBfQGnAdkBVQILADsAwQH4AhACSgEfAgMB4gEWAakBuQDNAD8BIgFrABkA8QGMAFEBLAFvAKEBXQAlAYICAgIMALgA7wC6AAoBywEGAPUAgQHNAZQA5gBaAGUBYgGwAJYBQAAtAEgBkQHSACMBcAEAAPABvAALAcMB3QFEAKwAFQE3AbIA6QH2AGQABwBqAXMAuQAQAh4APAA+APMBFABbAkQBMgD6ARgAGwEaADgBQQE6AGcBtgHAASsASgA6AjIAUAGAAhIA5wCxAhwBuwAYAfwABAI2AC8A9AGoAeoBCQC+AMYB+wGKAYMARQHeAXUASQDdAkMBQwFeAbMBSgIHAGYB9AFPAO4CQQHYAAwCFAHFASYA5AB4AicBtwBDAAUCOAFbABoAHQIYAcwAtwBfAcYCOQE+AXQAzgDgAdMA2AESAPkB9QEpAHAAfAJIAjcA2QFgAXoA9gFmAQcBmQBdAEQA8gBGAHsAAgF5AVMBEwGFAXIA9wENAY0CHwE/AaEBfAADAB4AdgF4AFYCRgAcALwA1QC9AegAtQDUAVIB4AFJAekAQgE4AgoA2wBoAFIBqgHIAMsBBQI9AI8CBgBTAjMCRwG9AeEBsQEcADMAygH/APsCQgIgASACPwFtASoB7wHuAGAB0AHkAioAFgFOAFkBwgBOAUgCMQCSAeUAcQAuAIwALABuAfcAKgDSAWMBMwF2AGECKQEvADQBZQG+AJgAsgGLAeYAnQIRAJECDgIjAS4CSQFhAKABtAERAHcAmgAXAA8AEgCVAGMAkAEnAc8BfgEDAZUAHwHwAVwB5wHEAN4CLAEkAR4BkgGPAgkBTAB+ADEADgEoAZ0BNQAhAbUCPgD9AG8ANgI7ACYAqQG4AW4B3wCzAUICLQHOAhkAhwFFAP8AKwARAaMCQAFUACgBBAI8AesBbABtAh0ApQI0AfMBJQE9ARkB3ACKAdYBmwGBANABmgCiAWcAtAGfAOoATQCEAHUA4QABAEwApwJLAWgBOQCGAGsB1wCqAf4AqAHtAWkAmQFWAaAAJADCAi4BpQHbATQCGgH5AGIAOQDtAa4BiAFRAIMAegHUAAYBDgCLANcAdAATAgAAaQGWAjUAwADcARUASwCwAFgAiAGTACICGwAJAXcAfwHBAKsBCADfAOMAIAITANYApgEdAI0AlwGiAg8AJwG/Aa0BPAGOAV8ArQIiAaYBhADsAA0AyADEAeMAngCOANMBMAFqAVAAeQGkADIArwAwAM8AkwCbAigAFAIIAX8ATwBAAGwAgAE2AFUCIQ==")
_RS_RANKS = None


def rs_rank(tag_id):
    """RealityScan 1-based marker number for an official tag36h11 ID."""
    global _RS_RANKS
    if _RS_RANKS is None:
        raw = base64.b64decode(RS_RANK_B64)
        _RS_RANKS = [(raw[2 * i] << 8) | raw[2 * i + 1] for i in range(len(raw) // 2)]
    return _RS_RANKS[tag_id] if 0 <= tag_id < len(_RS_RANKS) else None


def rs_name(tag_id):
    """Name RealityScan shows when it detects this tag, e.g. '36h11:1fa'."""
    r = rs_rank(tag_id)
    return ("36h11:%03x" % r) if r else "?"


def tag_caption(tmpl, tag_id):
    return (tmpl or "").replace("{id}", str(tag_id)).replace("{rs}", rs_name(tag_id))


def _png_size(data):
    """Width/height from a PNG IHDR without decoding pixels."""
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return None
    return (int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big"))


def png_decode(data):
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    pos = 8; w = h = bd = ct = None; idat = b""; plte = None; trns = None
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]; typ = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + ln]; pos += 12 + ln
        if typ == b"IHDR":
            w, h, bd, ct, _, _, interlace = struct.unpack(">IIBBBBB", chunk)
            if interlace:
                raise ValueError("interlaced PNG unsupported")
        elif typ == b"PLTE":
            plte = chunk
        elif typ == b"tRNS":
            trns = chunk
        elif typ == b"IDAT":
            idat += chunk
        elif typ == b"IEND":
            break
    raw = zlib.decompress(idat)
    ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ct]
    if bd == 8:
        stride = w * ch
    elif bd in (1, 2, 4) and ct == 3:
        stride = (w * bd + 7) // 8
    else:
        raise ValueError("unsupported PNG bit depth/colour type")
    out = bytearray(); prev = bytearray(stride); bpp = max(1, ch) if bd == 8 else 1
    i = 0
    for _y in range(h):
        f = raw[i]; i += 1; line = bytearray(raw[i:i + stride]); i += stride
        if f == 1:
            for x in range(stride):
                line[x] = (line[x] + (line[x - bpp] if x >= bpp else 0)) & 255
        elif f == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 255
        elif f == 3:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 255
        elif f == 4:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0; b = prev[x]; c = prev[x - bpp] if x >= bpp else 0
                p = a + b - c; pa = abs(p - a); pb = abs(p - b); pc = abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        out += line; prev = line
    rgb = bytearray()
    if bd == 8 and ct == 2:
        rgb = out
    elif bd == 8 and ct == 6:
        for j in range(0, len(out), 4):
            a = out[j + 3] / 255.0
            for k in range(3):
                rgb.append(int(out[j + k] * a + 255 * (1 - a)))
    elif bd == 8 and ct == 0:
        for v in out:
            rgb += bytes([v, v, v])
    elif bd == 8 and ct == 4:
        for j in range(0, len(out), 2):
            a = out[j + 1] / 255.0; v = int(out[j] * a + 255 * (1 - a)); rgb += bytes([v, v, v])
    elif ct == 3:
        tr = {k: a for k, a in enumerate(trns)} if trns else {}
        per = 8 // bd if bd < 8 else 1; mask = (1 << bd) - 1
        for y in range(h):
            row = out[y * stride:(y + 1) * stride]
            if bd == 8:
                vals = list(row)
            else:
                vals = []
                for byte in row:
                    for s in range(per):
                        vals.append((byte >> (8 - bd * (s + 1))) & mask)
                vals = vals[:w]
            for v in vals:
                r, g, b = plte[v * 3], plte[v * 3 + 1], plte[v * 3 + 2]
                a = tr.get(v, 255) / 255.0
                rgb += bytes([int(r * a + 255 * (1 - a)), int(g * a + 255 * (1 - a)), int(b * a + 255 * (1 - a))])
    else:
        raise ValueError("unsupported PNG")
    return w, h, bytes(rgb)


def png_encode_rgb(w, h, rgb):
    raw = bytearray()
    for y in range(h):
        raw.append(0); raw += rgb[y * w * 3:(y + 1) * w * 3]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


def tag_png(i, px):
    """Render a tag-only PNG (1-cell white quiet zone) ~px wide."""
    g = tag_grid(i); cell = max(1, px // 10); q = cell; side = 8 * cell + 2 * q
    rgb = bytearray(b"\xff" * (side * side * 3))
    for r in range(8):
        for c in range(8):
            if g[r][c]:
                for yy in range(cell):
                    base = ((q + r * cell + yy) * side + q + c * cell) * 3
                    for xx in range(cell):
                        o = base + xx * 3; rgb[o] = rgb[o + 1] = rgb[o + 2] = 0
    return png_encode_rgb(side, side, bytes(rgb))


def _jpeg_size(data):
    i = 2
    while i < len(data) - 8:
        if data[i] != 0xFF:
            i += 1; continue
        m = data[i + 1]
        if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
            h = struct.unpack(">H", data[i + 5:i + 7])[0]; w = struct.unpack(">H", data[i + 7:i + 9])[0]
            return w, h
        i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    return None


def resolve_branding(mode, path):
    """→ (kind, payload, err). kind: None | 'rgb' (w,h,bytes) | 'jpeg' (w,h,bytes)."""
    if mode == "none":
        return None, None, None
    try:
        if mode == "rcl":
            return ("rgb", png_decode(base64.b64decode(RCL_BRAND_B64)), None)
        ext = Path(path).suffix.lower()
        raw = Path(path).read_bytes()
        if ext == ".png":
            return ("rgb", png_decode(raw), None)
        if ext in (".jpg", ".jpeg"):
            wh = _jpeg_size(raw)
            if not wh:
                return None, None, "Could not read JPEG dimensions."
            return ("jpeg", (wh[0], wh[1], raw), None)
        return None, None, "PDF branding supports PNG or JPG (got " + ext + ")."
    except Exception as exc:
        return None, None, "Could not use branding image: " + str(exc)


# --- pure-stdlib PDF writer (vector tag + Helvetica caption + raster brand) -- #
_PT = 72.0 / 25.4  # mm → points
_HELV_W = {**{c: 556 for c in "0123456789"}, ' ': 278, '!': 278, '"': 355, '#': 556, '$': 556,
           '%': 889, '&': 667, "'": 191, '(': 333, ')': 333, '*': 389, '+': 584, ',': 278, '-': 333,
           '.': 278, '/': 278, ':': 278, ';': 278, '<': 584, '=': 584, '>': 584, '?': 556, '@': 1015,
           'A': 667, 'B': 667, 'C': 722, 'D': 722, 'E': 667, 'F': 611, 'G': 778, 'H': 722, 'I': 278,
           'J': 500, 'K': 667, 'L': 556, 'M': 833, 'N': 722, 'O': 778, 'P': 667, 'Q': 778, 'R': 722,
           'S': 667, 'T': 611, 'U': 722, 'V': 667, 'W': 944, 'X': 667, 'Y': 667, 'Z': 611, '[': 278,
           '\\': 278, ']': 278, '^': 469, '_': 556, '`': 333, 'a': 556, 'b': 556, 'c': 500, 'd': 556,
           'e': 556, 'f': 278, 'g': 556, 'h': 556, 'i': 222, 'j': 222, 'k': 500, 'l': 222, 'm': 833,
           'n': 556, 'o': 556, 'p': 556, 'q': 556, 'r': 333, 's': 500, 't': 278, 'u': 556, 'v': 500,
           'w': 722, 'x': 500, 'y': 500, 'z': 500, '{': 334, '|': 260, '}': 334, '~': 584}


def _helv_w(s, size):
    return sum(_HELV_W.get(ch, 556) for ch in s) / 1000.0 * size


def _pdf_text(s):
    s = (s or "").replace("•", "-").replace("·", "-").replace("→", "->").replace("’", "'").replace("°", " deg")
    enc = s.encode("cp1252", "replace")
    return "".join(("\\" + chr(c)) if c in (40, 41, 92) else chr(c) for c in enc)


def build_tag_pdf(ids, paper, size_mm, name_tmpl, branding, cut):
    pw, ph = PAPER_SIZES.get(paper, PAPER_SIZES["Letter"])
    margin = 12.0; cell = size_mm / 8.0
    kind, payload = (branding[0], branding[1]) if branding else (None, None)
    if kind:
        bw, bh, bdata = payload; bw_mm = min(55.0, pw * 0.32); bh_mm = bw_mm * bh / bw
    objs = {}
    n_cat, n_pages, n_font = 1, 2, 3
    n_img = 4 if kind else None
    base = 5 if kind else 4
    page_nums = []
    for k, tid in enumerate(ids):
        n_content = base + 2 * k; n_page = base + 2 * k + 1; page_nums.append(n_page)
        g = tag_grid(tid); tx = (pw - size_mm) / 2; ty = (ph - size_mm) / 2 - 6
        ops = ["0 0 0 rg"]
        for r in range(8):
            for c in range(8):
                if g[r][c]:
                    x = tx + c * cell; ytop = ty + r * cell
                    ops.append("%.3f %.3f %.3f %.3f re f" % (x * _PT, (ph - ytop - cell) * _PT, cell * _PT, cell * _PT))
        if cut:
            q = cell
            ops.append("0.7 0.7 0.7 RG 0.5 w %.3f %.3f %.3f %.3f re S"
                       % ((tx - q) * _PT, (ph - (ty - q) - (size_mm + 2 * q)) * _PT,
                          (size_mm + 2 * q) * _PT, (size_mm + 2 * q) * _PT))
        cap = tag_caption(name_tmpl, tid)
        sub = "tag36h11   ID %d   %gmm" % (tid, size_mm)
        cy = ph - (ty + size_mm + cell + 6)
        if cap:
            ops.append("0 0 0 rg BT /F1 12 Tf %.2f %.2f Td (%s) Tj ET"
                       % ((pw / 2 * _PT) - _helv_w(cap, 12) / 2, cy * _PT, _pdf_text(cap)))
        ops.append("0.25 0.25 0.25 rg BT /F1 9 Tf %.2f %.2f Td (%s) Tj ET"
                   % ((pw / 2 * _PT) - _helv_w(sub, 9) / 2, (cy - 5) * _PT, _pdf_text(sub)))
        if kind:
            x = pw - margin - bw_mm; y = ph - margin - bh_mm
            ops.append("q %.3f 0 0 %.3f %.3f %.3f cm /Im0 Do Q" % (bw_mm * _PT, bh_mm * _PT, x * _PT, y * _PT))
        comp = zlib.compress(("\n".join(ops)).encode("latin1"))
        objs[n_content] = b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(comp) + comp + b"\nendstream"
        res = "/Font << /F1 %d 0 R >>" % n_font + (" /XObject << /Im0 %d 0 R >>" % n_img if kind else "")
        objs[n_page] = ("<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %.2f %.2f] /Resources << %s >> /Contents %d 0 R >>"
                        % (n_pages, pw * _PT, ph * _PT, res, n_content)).encode("latin1")
    objs[n_cat] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objs[n_pages] = ("<< /Type /Pages /Kids [%s] /Count %d >>"
                     % (" ".join("%d 0 R" % n for n in page_nums), len(ids))).encode("latin1")
    objs[n_font] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
    if kind == "rgb":
        comp = zlib.compress(bdata)
        objs[n_img] = (b"<< /Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace /DeviceRGB "
                       b"/BitsPerComponent 8 /Filter /FlateDecode /Length %d >>\nstream\n" % (bw, bh, len(comp))) + comp + b"\nendstream"
    elif kind == "jpeg":
        objs[n_img] = (b"<< /Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace /DeviceRGB "
                       b"/BitsPerComponent 8 /Filter /DCTDecode /Length %d >>\nstream\n" % (bw, bh, len(bdata))) + bdata + b"\nendstream"
    out = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"; offs = {}
    for num in sorted(objs):
        offs[num] = len(out); out += ("%d 0 obj\n" % num).encode() + objs[num] + b"\nendobj\n"
    xref = len(out); n = len(objs) + 1
    out += ("xref\n0 %d\n" % n).encode() + b"0000000000 65535 f \n"
    for num in range(1, n):
        out += ("%010d 00000 n \n" % offs[num]).encode()
    out += ("trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF" % (n, xref)).encode()
    return out


def export_tags(fmt, ids, paper, size_mm, name_tmpl, brand_mode, brand_path, cut, outdir):
    """Write tag files. Returns (main_path, count, err)."""
    out = Path(outdir)
    if fmt == "PDF":
        kind, payload, berr = resolve_branding(brand_mode, brand_path)
        pdf = build_tag_pdf(ids, paper, size_mm, name_tmpl, (kind, payload) if kind else None, cut)
        p = out / ("hera_apriltags_" + paper.lower() + "_" + str(len(ids)) + "tags.pdf")
        p.write_bytes(pdf)
        return p, len(ids), berr
    sub = out / ("hera_apriltags_" + fmt.lower())
    sub.mkdir(parents=True, exist_ok=True)
    for tid in ids:
        if fmt == "SVG":
            (sub / ("tag36h11_%05d.svg" % tid)).write_text(build_tag_svg(tid, size_mm), encoding="utf-8")
        else:  # PNG
            (sub / ("tag36h11_%05d.png" % tid)).write_bytes(tag_png(tid, int(size_mm / 25.4 * 300)))
    return sub, len(ids), None


# --------------------------------------------------------------------------- #
# Fonts + theme
# --------------------------------------------------------------------------- #
def pick_family(preferred, fallback="TkDefaultFont"):
    try:
        available = set(tkfont.families())
    except Exception:
        return fallback
    for fam in preferred:
        if fam in available:
            return fam
    return fallback


def make_fonts():
    head = pick_family(["Montserrat", "Montserrat ExtraBold", "Segoe UI Semibold",
                        "Helvetica Neue", "Arial"], "TkDefaultFont")
    body = pick_family(["Lexend", "Lexend Medium", "Segoe UI", "Helvetica Neue", "Arial"], "TkDefaultFont")
    return {"title": (head, 17, "bold"), "subtitle": (body, 10), "section": (head, 10, "bold"),
            "body": (body, 10), "small": (body, 9), "button": (head, 10, "bold"),
            "badge": (head, 9, "bold"), "mono": ("Consolas" if os.name == "nt" else "Menlo", 9)}


def apply_theme(root, fonts):
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")
    root.configure(bg=PAGE)
    style.configure("TFrame", background=PAGE)
    style.configure("Card.TFrame", background=CARD)
    style.configure("Card.TLabelframe", background=CARD, bordercolor=LINE, relief="solid", borderwidth=1)
    style.configure("Card.TLabelframe.Label", background=CARD, foreground=INK, font=fonts["section"])
    style.configure("TLabel", background=CARD, foreground=INK, font=fonts["body"])
    style.configure("Muted.TLabel", background=CARD, foreground=MUTED, font=fonts["small"])
    style.configure("TCheckbutton", background=CARD, foreground=INK, font=fonts["body"])
    style.map("TCheckbutton", background=[("active", CARD)])
    style.configure("TRadiobutton", background=CARD, foreground=INK, font=fonts["body"])
    style.map("TRadiobutton", background=[("active", CARD)])
    style.configure("TEntry", fieldbackground="#FFFFFF")
    style.configure("TCombobox", fieldbackground="#FFFFFF")
    style.configure("TSpinbox", fieldbackground="#FFFFFF", arrowcolor=BLACK)
    style.configure("TScale", background=CARD, troughcolor=LINE)
    style.configure("TButton", background="#EFE6C8", foreground=INK, padding=6, borderwidth=0, font=fonts["body"])
    style.map("TButton", background=[("active", "#E6DBB6"), ("disabled", "#EFEAD8")],
              foreground=[("disabled", "#B6AE92")])
    style.configure("Accent.TButton", background=BLUE, foreground="#FFFFFF", padding=8, borderwidth=0, font=fonts["button"])
    style.map("Accent.TButton", background=[("active", BLUE_DK), ("disabled", "#A9B8E8")],
              foreground=[("disabled", "#EEF1FB")])
    style.configure("Gold.TButton", background=GOLD, foreground=BLACK, padding=6, borderwidth=0, font=fonts["button"])
    style.map("Gold.TButton", background=[("active", GOLD_DK), ("disabled", "#EAD9A6")])
    style.configure("Header.TFrame", background=BLACK)
    style.configure("Header.TLabel", background=BLACK, foreground=GOLD, font=fonts["title"])
    style.configure("HeaderSub.TLabel", background=BLACK, foreground="#CDBE86", font=fonts["subtitle"])
    style.configure("Badge.TLabel", background=GOLD, foreground=BLACK, font=fonts["badge"])
    style.configure("Footer.TFrame", background=PAGE)
    style.configure("Footer.TLabel", background=PAGE, foreground=MUTED, font=fonts["small"])
    style.configure("Status.TLabel", background=PAGE, foreground=INK, font=fonts["body"])
    style.configure("Horizontal.TProgressbar", troughcolor="#EADFBE", background=GOLD,
                    bordercolor=LINE, lightcolor=GOLD, darkcolor=GOLD)
    return style


def load_photo(b64):
    try:
        return tk.PhotoImage(data=b64)
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# First-run dialog
# --------------------------------------------------------------------------- #
class IntroDialog(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title(APP_NAME + " - before you start")
        self.configure(bg=PAGE); self.resizable(False, False); self.transient(app.root)
        f = app.fonts
        head = ttk.Frame(self, style="Header.TFrame", padding=(16, 12)); head.pack(fill="x")
        if app.logo:
            ttk.Label(head, image=app.logo, style="Header.TLabel").pack(side="left", padx=(0, 14))
        box = ttk.Frame(head, style="Header.TFrame"); box.pack(side="left")
        trow = ttk.Frame(box, style="Header.TFrame"); trow.pack(anchor="w")
        ttk.Label(trow, text=APP_NAME, style="Header.TLabel").pack(side="left")
        ttk.Label(trow, text=" " + APP_PRODUCT + " ", style="Badge.TLabel").pack(side="left", padx=8)
        ttk.Label(box, text="v" + APP_VERSION + " · " + APP_TAGLINE, style="HeaderSub.TLabel").pack(anchor="w")

        body = tk.Frame(self, bg=CARD, padx=18, pady=14); body.pack(fill="both", expand=True)

        def row(ok, title, detail, warn=False):
            r = tk.Frame(body, bg=CARD); r.pack(fill="x", pady=3)
            tk.Label(r, text=("✓" if ok else ("!" if warn else "✗")), bg=CARD,
                     fg=(GREEN_TXT if ok else ORANGE), font=(f["section"][0], 12, "bold"), width=2).pack(side="left", anchor="n")
            t = tk.Frame(r, bg=CARD); t.pack(side="left", fill="x", expand=True)
            tk.Label(t, text=title, bg=CARD, fg=INK, font=f["body"], anchor="w", justify="left").pack(anchor="w")
            if detail:
                tk.Label(t, text=detail, bg=CARD, fg=MUTED, font=f["small"], anchor="w",
                         justify="left", wraplength=440).pack(anchor="w")

        tk.Label(body, text="Requirements", bg=CARD, fg=INK, font=f["section"]).pack(anchor="w", pady=(0, 6))
        row(True, "Python " + ".".join(map(str, sys.version_info[:3])) + " (Tk " + str(tk.TkVersion) + ")", "Running - you're good.")
        ff, fp = app.cfg["ffmpeg"], app.cfg["ffprobe"]
        row(bool(ff), "FFmpeg " + ("detected" if ff else "NOT found on PATH"),
            (ffmpeg_version(ff) or ff) if ff else "Hera needs FFmpeg. Install it, then reopen or use 'Locate…'.", warn=not ff)
        row(bool(fp), "ffprobe " + ("detected" if fp else "not found"),
            "Progress percentage " + ("enabled." if fp else "needs ffprobe (optional)."), warn=not fp)

        tk.Label(body, text="Housekeeping", bg=CARD, fg=INK, font=f["section"]).pack(anchor="w", pady=(10, 6))
        for line in [
            "Input must be EQUIRECTANGULAR video (.mp4/.mov). Export raw .insv from Insta360 Studio first.",
            "Each camera (Top/Middle/Low) has its own cubemap orientation and face selection.",
            "Test render previews the first frame of every loaded camera before you commit.",
            "Hera tools (top bar): AprilTag Generator, and a Capture Planner for indoor/outdoor scans.",
            "An RCL product - free to use under the MIT License.",
            "Hera was developed independently by Rustin C. Newbold (RCL) on personal time and equipment "
            "to fix a redundant 360-to-SfM workflow; it is not affiliated with or endorsed by any institution.",
        ]:
            tk.Label(body, text="•  " + line, bg=CARD, fg=INK, font=f["small"], anchor="w",
                     justify="left", wraplength=470).pack(anchor="w", pady=1)
        link = tk.Label(body, text="Download FFmpeg →", bg=CARD, fg=BLUE, font=f["small"], cursor="hand2")
        link.pack(anchor="w", pady=(8, 0)); link.bind("<Button-1>", lambda _e: webbrowser.open(FFMPEG_URL))

        foot = tk.Frame(self, bg=PAGE, padx=18, pady=12); foot.pack(fill="x")
        self.skip_var = tk.BooleanVar(value=False)
        tk.Checkbutton(foot, text="Don't show this again", variable=self.skip_var, bg=PAGE, fg=INK,
                       activebackground=PAGE, font=f["small"], selectcolor=TAN).pack(side="left")
        tk.Button(foot, text="Continue", command=self._continue, bg=BLUE, fg="#FFFFFF", activebackground=BLUE_DK,
                  activeforeground="#FFFFFF", relief="flat", padx=18, pady=6, font=f["button"], cursor="hand2").pack(side="right")
        if app.rcl_logo:
            tk.Label(foot, image=app.rcl_logo, bg=PAGE).pack(side="right", padx=12)
        self.update_idletasks(); self._center(); self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._continue)

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry("+" + str((sw - w) // 2) + "+" + str((sh - h) // 3))

    def _continue(self):
        if self.skip_var.get():
            self.app.cfg["skip_intro"] = True; save_config(self.app.cfg)
        self.grab_release(); self.destroy()


# --------------------------------------------------------------------------- #
# Test-render preview (one tab per camera)
# --------------------------------------------------------------------------- #
class PreviewWindow(tk.Toplevel):
    def __init__(self, app, results):
        super().__init__(app.root)
        self.title(APP_NAME + " - test render (first frame)")
        self.configure(bg=PAGE); self.resizable(False, False); self.transient(app.root)
        f = app.fonts
        self._refs = []
        nb = ttk.Notebook(self); nb.pack(fill="both", expand=True, padx=10, pady=10)
        by_suffix = {fc["suffix"]: fc for fc in FACES}
        for label, render_dir, selected_keys, ori in results:
            tab = tk.Frame(nb, bg=PAGE); nb.add(tab, text=label)
            tk.Label(tab, text=ori, bg=PAGE, fg=MUTED, font=f["small"]).pack(anchor="w", padx=6, pady=(6, 2))
            grid = tk.Frame(tab, bg=PAGE, padx=8, pady=6); grid.pack()
            cell = 150
            for suffix, (r, c) in CROSS.items():
                face = by_suffix[suffix]
                holder = tk.Frame(grid, bg=BLACK, width=cell, height=cell,
                                  highlightthickness=1, highlightbackground=LINE)
                holder.grid(row=r, column=c, padx=3, pady=3); holder.grid_propagate(False)
                png = Path(render_dir) / ("test_" + suffix + ".png")
                if face["key"] in selected_keys and png.exists():
                    try:
                        img = tk.PhotoImage(file=str(png)); self._refs.append(img)
                        tk.Label(holder, image=img, bg=BLACK).place(relx=0.5, rely=0.5, anchor="center")
                        tk.Label(holder, text=suffix, bg=BLACK, fg=GOLD, font=f["small"]).place(x=4, y=2)
                    except Exception:
                        self._ph(holder, suffix, "render failed", f)
                else:
                    self._ph(holder, suffix, "face deselected", f)
        tk.Button(self, text="Close", command=self.destroy, bg="#EFE6C8", fg=INK, relief="flat",
                  padx=16, pady=5, font=f["button"]).pack(pady=(0, 12))
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry("+" + str((sw - self.winfo_width()) // 2) + "+" + str((sh - self.winfo_height()) // 3))

    def _ph(self, holder, suffix, msg, f):
        tk.Label(holder, text=suffix, bg=BLACK, fg=MUTED, font=f["small"]).place(x=4, y=2)
        tk.Label(holder, text=msg, bg=BLACK, fg="#8A8262", font=f["small"]).place(relx=0.5, rely=0.5, anchor="center")


# --------------------------------------------------------------------------- #
# AprilTag page preview (true-to-layout, page through)
# --------------------------------------------------------------------------- #
class PreviewTagWindow(tk.Toplevel):
    def __init__(self, app, ids, paper, size_mm, name_tmpl, brand_mode, brand_path, cut):
        super().__init__(app.root)
        self.app = app; self.ids = ids; self.paper = paper; self.size_mm = size_mm
        self.name_tmpl = name_tmpl; self.cut = cut; self.idx = 0
        self.title(APP_NAME + " - tag sheet preview")
        self.configure(bg=PAGE); self.resizable(False, False); self.transient(app.root)
        self.f = app.fonts
        self._refs = []
        self._brand_img = self._load_brand(brand_mode, brand_path)

        pw, ph = PAPER_SIZES.get(paper, PAPER_SIZES["Letter"])
        self.scale = 470.0 / ph
        self.cw, self.ch = pw * self.scale, ph * self.scale
        wrap = tk.Frame(self, bg=PAGE, padx=14, pady=12); wrap.pack()
        tk.Label(wrap, text=paper + " · tag " + _fmt(size_mm) + " mm", bg=PAGE, fg=MUTED,
                 font=self.f["small"]).pack(anchor="w")
        self.canvas = tk.Canvas(wrap, width=self.cw + 2, height=self.ch + 2, bg=PAGE, highlightthickness=0)
        self.canvas.pack(pady=6)
        nav = tk.Frame(wrap, bg=PAGE); nav.pack(fill="x")
        tk.Button(nav, text="‹ Prev", command=self._prev, bg="#EFE6C8", fg=INK, relief="flat",
                  padx=12, pady=4, font=self.f["small"]).pack(side="left")
        self.page_lbl = tk.Label(nav, text="", bg=PAGE, fg=INK, font=self.f["small"]); self.page_lbl.pack(side="left", expand=True)
        tk.Button(nav, text="Next ›", command=self._next, bg="#EFE6C8", fg=INK, relief="flat",
                  padx=12, pady=4, font=self.f["small"]).pack(side="right")
        tk.Button(wrap, text="Close", command=self.destroy, bg=GOLD, fg=BLACK, relief="flat",
                  padx=16, pady=5, font=self.f["button"]).pack(pady=(8, 0))
        self._draw()
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry("+" + str((sw - self.winfo_width()) // 2) + "+" + str((sh - self.winfo_height()) // 6))

    def _load_brand(self, mode, path):
        try:
            if mode == "rcl":
                img = tk.PhotoImage(data=RCL_BRAND_B64)
            elif mode == "custom" and path and Path(path).suffix.lower() in (".png", ".gif"):
                img = tk.PhotoImage(file=path)
            else:
                return None
            f = max(1, int(img.width() / 150))
            return img.subsample(f, f)
        except Exception:
            return None

    def _prev(self):
        self.idx = (self.idx - 1) % len(self.ids); self._draw()

    def _next(self):
        self.idx = (self.idx + 1) % len(self.ids); self._draw()

    def _draw(self):
        c = self.canvas; c.delete("all"); self._refs = [self._brand_img] if self._brand_img else []
        pw, ph = PAPER_SIZES.get(self.paper, PAPER_SIZES["Letter"]); s = self.scale
        c.create_rectangle(1, 1, self.cw, self.ch, fill="#FFFFFF", outline=LINE)
        tid = self.ids[self.idx]
        grid = tag_grid(tid)
        cell = (self.size_mm * s) / 8.0
        tx = (pw - self.size_mm) / 2 * s; ty = ((ph - self.size_mm) / 2 - 6) * s
        if self.cut:
            q = cell
            c.create_rectangle(tx - q, ty - q, tx + 8 * cell + q, ty + 8 * cell + q, outline="#BBBBBB", dash=(2, 2))
        for r in range(8):
            for col in range(8):
                if grid[r][col]:
                    c.create_rectangle(tx + col * cell, ty + r * cell, tx + (col + 1) * cell, ty + (r + 1) * cell,
                                       fill="#000000", outline="#000000")
        cap = tag_caption(self.name_tmpl, tid) + "   \u2192 RealityScan: " + rs_name(tid)
        cyy = ty + 8 * cell + cell + 8 * s
        if cap:
            c.create_text(self.cw / 2, cyy, text=cap, fill="#000", font=self.f["body"])
        c.create_text(self.cw / 2, cyy + 16, text="tag36h11 · ID " + str(tid) + " · " + _fmt(self.size_mm) + "mm",
                      fill="#333", font=self.f["small"])
        if self._brand_img:
            m = 12 * s
            c.create_image(self.cw - m, m, image=self._brand_img, anchor="ne")
        else:
            m = 12 * s; bw = min(55.0, pw * 0.32) * s
            c.create_rectangle(self.cw - m - bw, m, self.cw - m, m + bw * 0.45, outline="#CCC", dash=(2, 2))
            c.create_text(self.cw - m - bw / 2, m + bw * 0.22, text="branding", fill="#AAA", font=self.f["small"])
        self.page_lbl.config(text="Page " + str(self.idx + 1) + " of " + str(len(self.ids)) + "   ·   ID " + str(tid))


# --------------------------------------------------------------------------- #
# AprilTag generator dialog
# --------------------------------------------------------------------------- #
class AprilTagDialog(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title(APP_NAME + " - AprilTag generator (tag36h11)")
        self.configure(bg=CARD); self.resizable(False, False); self.transient(app.root)
        f = app.fonts; cfg = app.cfg
        self.brand_mode = tk.StringVar(value="rcl")
        self.brand_path = tk.StringVar(value="")
        self.fmt_var = tk.StringVar(value=cfg.get("tag_format", "PDF"))

        head = ttk.Frame(self, style="Header.TFrame", padding=(14, 10)); head.pack(fill="x")
        ttk.Label(head, text="AprilTag sheets", style="Header.TLabel").pack(side="left")
        ttk.Label(head, text=" tag36h11 · IDs 0-" + str(APRILTAG_N - 1) + " ", style="Badge.TLabel").pack(side="left", padx=8)

        body = ttk.Frame(self, style="Card.TFrame", padding=14); body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)

        def lbl(r, t):
            ttk.Label(body, text=t).grid(row=r, column=0, sticky="w", pady=4, padx=(0, 8))

        lbl(0, "Tag IDs:")
        self.ids_var = tk.StringVar(value=cfg.get("tag_ids", "0-15"))
        e = ttk.Entry(body, textvariable=self.ids_var); e.grid(row=0, column=1, columnspan=2, sticky="ew")
        e.bind("<KeyRelease>", lambda _e: self._refresh_preview())
        ttk.Label(body, text="e.g.  0-15, 20, 33", style="Muted.TLabel").grid(row=1, column=1, sticky="w")

        lbl(2, "Paper size:")
        self.paper_var = tk.StringVar(value=cfg.get("tag_paper", "Letter"))
        ttk.Combobox(body, textvariable=self.paper_var, values=list(PAPER_SIZES.keys()),
                     width=10, state="readonly").grid(row=2, column=1, sticky="w")

        lbl(3, "Tag size (mm):")
        self.size_var = tk.StringVar(value=str(cfg.get("tag_size_mm", "100")))
        sp = ttk.Spinbox(body, from_=10, to=400, textvariable=self.size_var, width=8,
                         command=self._refresh_preview)
        sp.grid(row=3, column=1, sticky="w")
        ttk.Label(body, text="side length of the black square", style="Muted.TLabel").grid(row=3, column=2, sticky="w")

        lbl(4, "Name / text:")
        self.name_var = tk.StringVar(value=cfg.get("tag_name", "Hera \u2022 tag {id}"))
        ne = ttk.Entry(body, textvariable=self.name_var); ne.grid(row=4, column=1, columnspan=2, sticky="ew")
        ne.bind("<KeyRelease>", lambda _e: self._refresh_preview())
        ttk.Label(body, text="{id} = tag number \u00b7 {rs} = name RealityScan shows on detection (e.g. ID 0 \u2192 36h11:1fa)", style="Muted.TLabel", wraplength=380).grid(row=5, column=1, columnspan=2, sticky="w")

        lbl(6, "Branding:")
        brow = ttk.Frame(body, style="Card.TFrame"); brow.grid(row=6, column=1, columnspan=2, sticky="w")
        ttk.Radiobutton(brow, text="RCL logo", value="rcl", variable=self.brand_mode,
                        command=self._brand_changed).pack(side="left")
        ttk.Radiobutton(brow, text="Custom…", value="custom", variable=self.brand_mode,
                        command=self._pick_brand).pack(side="left", padx=6)
        ttk.Radiobutton(brow, text="None", value="none", variable=self.brand_mode,
                        command=self._brand_changed).pack(side="left")
        self.brand_lbl = ttk.Label(body, text="top-right corner: RCL logo", style="Muted.TLabel")
        self.brand_lbl.grid(row=7, column=1, columnspan=2, sticky="w")

        self.cut_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(body, text="Thin cut border around each tag", variable=self.cut_var).grid(
            row=8, column=1, sticky="w", pady=(4, 0))

        lbl(9, "Output folder:")
        self.dir_var = tk.StringVar(value=cfg.get("tag_dir", "") or cfg.get("output_dir", ""))
        ttk.Entry(body, textvariable=self.dir_var).grid(row=9, column=1, sticky="ew")
        ttk.Button(body, text="Browse…", command=self._browse_dir).grid(row=9, column=2, padx=4)

        prev = ttk.LabelFrame(body, text="Preview (first tag)", style="Card.TLabelframe", padding=6)
        prev.grid(row=0, column=3, rowspan=8, padx=(16, 0), sticky="n")
        self.canvas = tk.Canvas(prev, width=170, height=170, bg="#FFFFFF",
                                highlightthickness=1, highlightbackground=LINE)
        self.canvas.pack()
        self.prev_cap = ttk.Label(prev, text="", style="Muted.TLabel"); self.prev_cap.pack(pady=(4, 0))

        foot = ttk.Frame(self, style="Card.TFrame", padding=(14, 10)); foot.pack(fill="x")
        ttk.Label(foot, text="Format:").pack(side="left")
        ttk.Combobox(foot, textvariable=self.fmt_var, values=["PDF", "PNG", "SVG"], width=6,
                     state="readonly").pack(side="left", padx=(4, 6))
        ttk.Label(foot, text="PDF = printable sheet · PNG/SVG = tag images",
                  style="Muted.TLabel").pack(side="left")
        self.status = ttk.Label(foot, text="", style="Muted.TLabel"); self.status.pack(side="left", padx=10)
        ttk.Button(foot, text="Export", style="Accent.TButton", command=self._generate).pack(side="right")
        ttk.Button(foot, text="Preview…", style="Gold.TButton", command=self._open_preview).pack(side="right", padx=6)
        ttk.Button(foot, text="Close", command=self.destroy).pack(side="right", padx=6)

        self._refresh_preview()
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry("+" + str((sw - self.winfo_width()) // 2) + "+" + str((sh - self.winfo_height()) // 4))

    def _brand_changed(self):
        text = {"rcl": "top-right corner: RCL logo", "none": "no branding"}.get(self.brand_mode.get(), "")
        if self.brand_mode.get() == "custom" and self.brand_path.get():
            text = "top-right corner: " + Path(self.brand_path.get()).name
        self.brand_lbl.config(text=text)

    def _pick_brand(self):
        path = filedialog.askopenfilename(title="Select branding image",
                                          filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.svg"), ("All files", "*.*")])
        if path:
            self.brand_path.set(path); self.brand_mode.set("custom")
        elif not self.brand_path.get():
            self.brand_mode.set("rcl")
        self._brand_changed()

    def _browse_dir(self):
        path = filedialog.askdirectory(title="Output folder for the AprilTag sheet")
        if path:
            self.dir_var.set(path)

    def _refresh_preview(self):
        ids, err = parse_id_spec(self.ids_var.get())
        c = self.canvas; c.delete("all")
        if err or not ids:
            c.create_text(85, 85, text=" - ", fill=MUTED); self.prev_cap.config(text=err or "")
            return
        i = ids[0]; grid = tag_grid(i); cell = 160 / 8
        for r in range(8):
            for col in range(8):
                if grid[r][col]:
                    c.create_rectangle(5 + col * cell, 5 + r * cell, 5 + (col + 1) * cell, 5 + (r + 1) * cell,
                                       fill="#000", outline="#000")
        nm = tag_caption(self.name_var.get(), i)
        self.prev_cap.config(text=(nm + "  ·  " if nm else "") + "ID " + str(i) +
                             "  ·  " + str(len(ids)) + " tag(s)")

    def _open_preview(self):
        ids, err = parse_id_spec(self.ids_var.get())
        if err or not ids:
            messagebox.showerror(APP_NAME, err or "Enter at least one tag ID."); return
        try:
            size_mm = float(self.size_var.get()); assert size_mm > 0
        except Exception:
            messagebox.showerror(APP_NAME, "Tag size must be a positive number of millimetres."); return
        PreviewTagWindow(self.app, ids, self.paper_var.get(), size_mm, self.name_var.get(),
                         self.brand_mode.get(), self.brand_path.get(), self.cut_var.get())

    def _generate(self):
        ids, err = parse_id_spec(self.ids_var.get())
        if err:
            messagebox.showerror(APP_NAME, err); return
        try:
            size_mm = float(self.size_var.get()); assert size_mm > 0
        except Exception:
            messagebox.showerror(APP_NAME, "Tag size must be a positive number of millimetres."); return
        outdir = self.dir_var.get().strip()
        if not outdir or not Path(outdir).is_dir():
            messagebox.showerror(APP_NAME, "Choose a valid output folder."); return
        fmt = self.fmt_var.get()
        try:
            main_path, count, berr = export_tags(fmt, ids, self.paper_var.get(), size_mm,
                                                 self.name_var.get(), self.brand_mode.get(),
                                                 self.brand_path.get(), self.cut_var.get(), outdir)
        except Exception as exc:
            messagebox.showerror(APP_NAME, "Export failed:\n" + str(exc)); return
        if berr:
            messagebox.showwarning(APP_NAME, berr + "\n(Exported without branding.)")
        self.app.cfg.update({"tag_ids": self.ids_var.get(), "tag_paper": self.paper_var.get(),
                             "tag_size_mm": self.size_var.get(), "tag_name": self.name_var.get(),
                             "tag_dir": outdir, "tag_format": fmt})
        save_config(self.app.cfg)
        self.status.config(text="Wrote " + main_path.name)
        note = ("PDF is ready to print at exact size." if fmt == "PDF"
                else str(count) + " " + fmt + " files written.")
        if messagebox.askyesno(APP_NAME, "Exported " + str(count) + " tag(s) as " + fmt + ":\n"
                               + str(main_path) + "\n\n" + note + "\n\nOpen it now?"):
            if fmt == "PDF":
                webbrowser.open(main_path.as_uri())
            else:
                open_in_file_manager(str(main_path))


# --------------------------------------------------------------------------- #
# Capture planner - spacing / path / camera-height advice for indoor scans
# --------------------------------------------------------------------------- #
def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _route_around(pts, rects, bx, by, clr=0.5, depth=0):
    """Re-route an axis-aligned polyline around inflated rectangles.
    rects: (x, y, w, h) obstacles; bx/by: room bounds for clamping detours."""
    if not rects or len(pts) < 2 or depth > 24:
        return list(pts)
    out = [pts[0]]
    for k in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[k], pts[k + 1]
        seg = [(x0, y0), (x1, y1)]
        if abs(x0 - x1) < 1e-9:                      # vertical
            lo, hi = min(y0, y1), max(y0, y1)
            hits = []
            for (rx, ry, rw, rh) in rects:
                if rx - clr < x0 < rx + rw + clr and lo < ry + rh + clr and hi > ry - clr:
                    hits.append((ry - clr, ry + rh + clr, rx - clr, rx + rw + clr))
            if hits:
                hits.sort(key=lambda h: h[0] if y1 > y0 else -h[1])
                e0, e1, xl, xr = hits[0]
                side = _clamp(xl if abs(x0 - xl) <= abs(x0 - xr) else xr, 0.15, bx - 0.15)
                a, b = (e0, e1) if y1 > y0 else (e1, e0)
                a = _clamp(a, min(y0, y1), max(y0, y1)); b = _clamp(b, min(y0, y1), max(y0, y1))
                rest = _route_around([(x0, b), (x1, y1)], rects, bx, by, clr, depth + 1)
                seg = [(x0, y0), (x0, a), (side, a), (side, b)] + rest
        elif abs(y0 - y1) < 1e-9:                    # horizontal
            lo, hi = min(x0, x1), max(x0, x1)
            hits = []
            for (rx, ry, rw, rh) in rects:
                if ry - clr < y0 < ry + rh + clr and lo < rx + rw + clr and hi > rx - clr:
                    hits.append((rx - clr, rx + rw + clr, ry - clr, ry + rh + clr))
            if hits:
                hits.sort(key=lambda h: h[0] if x1 > x0 else -h[1])
                e0, e1, yt, yb = hits[0]
                side = _clamp(yt if abs(y0 - yt) <= abs(y0 - yb) else yb, 0.15, by - 0.15)
                a, b = (e0, e1) if x1 > x0 else (e1, e0)
                a = _clamp(a, min(x0, x1), max(x0, x1)); b = _clamp(b, min(x0, x1), max(x0, x1))
                rest = _route_around([(b, y0), (x1, y1)], rects, bx, by, clr, depth + 1)
                seg = [(x0, y0), (a, y0), (a, side), (b, side)] + rest
        out += seg[1:]
    # drop consecutive duplicates
    ded = [out[0]]
    for pt in out[1:]:
        if math.dist(pt, ded[-1]) > 1e-6:
            ded.append(pt)
    return ded


def _poly_len(pts):
    return sum(math.dist(pts[k], pts[k + 1]) for k in range(len(pts) - 1))


# --------------------------------------------------------------------------- #
# Capture planning core (multi-room scenes)
# --------------------------------------------------------------------------- #
def _room_bounds(rm):
    if rm["kind"] == "circle":
        return (rm["x"] - rm["r"], rm["y"] - rm["r"], rm["x"] + rm["r"], rm["y"] + rm["r"])
    return (rm["x"], rm["y"], rm["x"] + rm["w"], rm["y"] + rm["l"])


def _scene_bounds(rooms):
    bs = [_room_bounds(r) for r in rooms]
    return (min(b[0] for b in bs), min(b[1] for b in bs),
            max(b[2] for b in bs), max(b[3] for b in bs))


def _rect_walls(rm):
    x0, y0, x1, y1 = _room_bounds(rm)
    return [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
            ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]


def _march_tags(segs, spacing, out, room_ids, rid):
    """Place tags every `spacing` along a list of segments."""
    total = sum(math.dist(a, b) for a, b in segs)
    if total <= 0:
        return 0
    n = int(_clamp(math.ceil(total / spacing), 3, 120))
    step = total / n
    d = step / 2
    lens = [math.dist(a, b) for a, b in segs]
    for _ in range(n):
        dd = d
        si = 0
        while si < len(segs) - 1 and dd > lens[si]:
            dd -= lens[si]
            si += 1
        (ax, ay), (bx, by) = segs[si]
        tt = dd / lens[si] if lens[si] else 0
        out.append((ax + (bx - ax) * tt, ay + (by - ay) * tt))
        room_ids.append(frozenset([rid]))
        d += step
    return n


def _room_junctions(rooms, tol=0.25, min_overlap=0.5):
    """Find doorway points where rooms touch. Returns (ia, ib, (jx, jy), (ux, uy))
    with (ux, uy) the unit direction ALONG the shared wall."""
    out = []
    for a in range(len(rooms)):
        for b in range(a + 1, len(rooms)):
            ra, rb = rooms[a], rooms[b]
            if ra["kind"] == "rect" and rb["kind"] == "rect":
                ax0, ay0, ax1, ay1 = _room_bounds(ra)
                bx0, by0, bx1, by1 = _room_bounds(rb)
                # vertical shared wall (a right on b left, or a left on b right)
                for xa, xb in ((ax1, bx0), (ax0, bx1)):
                    if abs(xa - xb) <= tol:
                        lo, hi = max(ay0, by0), min(ay1, by1)
                        if hi - lo >= min_overlap:
                            out.append((a, b, ((xa + xb) / 2, (lo + hi) / 2), (0.0, 1.0)))
                # horizontal shared wall
                for ya, yb in ((ay1, by0), (ay0, by1)):
                    if abs(ya - yb) <= tol:
                        lo, hi = max(ax0, bx0), min(ax1, bx1)
                        if hi - lo >= min_overlap:
                            out.append((a, b, ((lo + hi) / 2, (ya + yb) / 2), (1.0, 0.0)))
            elif ra["kind"] == "circle" and rb["kind"] == "circle":
                d = math.dist((ra["x"], ra["y"]), (rb["x"], rb["y"]))
                if abs(d - (ra["r"] + rb["r"])) <= tol and d > 0:
                    t = ra["r"] / d
                    jx = ra["x"] + (rb["x"] - ra["x"]) * t
                    jy = ra["y"] + (rb["y"] - ra["y"]) * t
                    ux, uy = -(rb["y"] - ra["y"]) / d, (rb["x"] - ra["x"]) / d
                    out.append((a, b, (jx, jy), (ux, uy)))
            else:
                circ, rect = (ra, rb) if ra["kind"] == "circle" else (rb, ra)
                ci = a if ra["kind"] == "circle" else b
                ri = b if ra["kind"] == "circle" else a
                cx, cy, r = circ["x"], circ["y"], circ["r"]
                for (p0, p1) in _rect_walls(rect):
                    (x0, y0), (x1, y1) = p0, p1
                    if abs(x0 - x1) < 1e-9:                    # vertical wall
                        if min(y0, y1) - 0.2 <= cy <= max(y0, y1) + 0.2 and abs(abs(cx - x0) - r) <= tol:
                            out.append((ci, ri, (x0, cy), (0.0, 1.0)))
                    else:                                       # horizontal wall
                        if min(x0, x1) - 0.2 <= cx <= max(x0, x1) + 0.2 and abs(abs(cy - y0) - r) <= tol:
                            out.append((ci, ri, (cx, y0), (1.0, 0.0)))
    return out


def _circle_pts(cx, cy, r, n=28, closed=True):
    pts = [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n))
           for k in range(n)]
    return pts + [pts[0]] if closed else pts


def _rect_room_path(rm, obstacles):
    """Walking path inside one rectangular room, routed around its obstacles.
    Pattern picked from the room's shape: corridor, big open space, or room."""
    x0, y0, x1, y1 = _room_bounds(rm)
    w, l = x1 - x0, y1 - y0
    short, long_ = min(w, l), max(w, l)
    aspect = long_ / max(short, 1e-9)
    obs = [ob for ob in obstacles
           if x0 < ob[0] + ob[2] / 2 + 0 * 1 and x0 <= ob[0] + ob[2] and ob[0] <= x1
           and y0 <= ob[1] + ob[3] and ob[1] <= y1]
    if aspect >= 3.0 or short < 2.2:
        # corridor: two offset passes along the long axis
        off = _clamp(short * 0.22, 0.15, 0.8)
        if w >= l:
            c1, c2 = (y0 + y1) / 2 - off, (y0 + y1) / 2 + off
            raw = [(x0 + 0.4, c1), (x1 - 0.4, c1), (x1 - 0.4, c2), (x0 + 0.4, c2)]
        else:
            c1, c2 = (x0 + x1) / 2 - off, (x0 + x1) / 2 + off
            raw = [(c1, y0 + 0.4), (c1, y1 - 0.4), (c2, y1 - 0.4), (c2, y0 + 0.4)]
        desc = "corridor: down one side, back the other"
    elif short >= 5.0:
        row = round(_clamp(0.5 * short, 1.2, 2.5), 1)
        m = _clamp(row / 2, 0.4, 1.2)
        n_rows = max(2, int(math.ceil(w / row)) + 1)
        xs = [_clamp(x0 + m + i * row, x0 + m, x1 - m) for i in range(n_rows)]
        raw = []
        for i, x in enumerate(xs):
            raw += [(x, y0 + m), (x, y1 - m)] if i % 2 == 0 else [(x, y1 - m), (x, y0 + m)]
        desc = "open space: serpentine rows " + ("%g" % row) + " m apart + one wall loop"
    else:
        m = 0.6
        raw = [(x0 + m, y0 + m), (x1 - m, y0 + m), (x1 - m, y1 - m),
               (x0 + m, y1 - m), (x0 + m, y0 + m), (x1 - m, y1 - m)]
        desc = "room: wall loop + one diagonal"
    pts = _route_around(raw, obs, x1, y1) if obs else raw
    return pts, desc


def _circle_room_path(rm):
    cx, cy, r = rm["x"], rm["y"], rm["r"]
    m = _clamp(r * 0.25, 0.4, 0.9)
    pts = _circle_pts(cx, cy, max(0.3, r - m))
    desc = "circular room: one ring near the wall"
    if r >= 3.2:
        pts = pts + _circle_pts(cx, cy, max(0.3, (r - m) * 0.5))
        desc = "circular room: two concentric rings"
    pts = pts + [(cx - (r - m), cy), (cx + (r - m), cy)]
    desc += " + one diameter pass"
    return pts, desc


def plan_capture(p):
    """Capture plan for a multi-room scene. Lengths in metres.
    Heuristics are conservative starting points, not law."""
    rooms = []
    for rm in p.get("rooms", []):
        if rm.get("kind") == "circle":
            r = max(0.5, float(rm.get("r", 2)))
            rooms.append({"kind": "circle", "x": float(rm.get("x", 0)), "y": float(rm.get("y", 0)), "r": r})
        else:
            rooms.append({"kind": "rect", "x": float(rm.get("x", 0)), "y": float(rm.get("y", 0)),
                          "w": max(0.5, float(rm.get("w", 4))), "l": max(0.5, float(rm.get("l", 4)))})
    if not rooms:
        rooms = [{"kind": "rect", "x": 0.0, "y": 0.0, "w": 8.0, "l": 10.0}]
    # normalise the scene so everything sits in positive coordinates
    b = _scene_bounds(rooms)
    dx, dy = -b[0], -b[1]
    for rm in rooms:
        rm["x"] += dx
        rm["y"] += dy
    sb = _scene_bounds(rooms)
    SX, SY = sb[2], sb[3]

    Z = max(1.6, p["Z"])
    C = _clamp(p["height"], 1.0, 2.3)
    mid = _clamp(0.72 * C, 0.6, Z - 0.15)
    top = _clamp(mid + p["top_off"], mid + 0.05, Z - 0.05)
    low = _clamp(mid + p["bottom_off"], 0.12, mid - 0.05)
    eqw = max(2000, p["eq_width"])
    tag_m = max(0.02, p["tag_mm"] / 1000.0)
    fps = max(0.1, p["fps"])

    # tag36h11 is an 8x8-module pattern (6x6 data + border); ~5 px per module
    # (~40 px across the black square) is a conservative floor for reliable
    # detection at moderate viewing angles (Olson 2011; Wang & Olson 2016;
    # Kalaitzakis et al. 2021).
    px_needed = 40.0
    d_max = tag_m * eqw / (2 * math.pi * px_needed)
    spacing = round(_clamp(0.6 * d_max, 0.4, 8.0), 1)
    station = 0.30
    speed = round(station * fps, 2)

    warnings = []
    if d_max < 1.5:
        warnings.append("Tags this small are only detectable within ~%.1f m. Use bigger tags or place them densely." % d_max)
    if p["bottom_off"] >= 0 or low >= mid:
        warnings.append("Bottom camera should sit below the middle (use a negative offset).")
    if top >= Z - 0.05:
        warnings.append("Top camera is near the ceiling. It may mostly see ceiling; lower it a little.")

    mode = p.get("mode", "Indoor")
    outdoor = mode in ("Outdoor", "Perimeter")
    pattern = {"type": mode, "outdoor": outdoor}

    # obstacles in scene coordinates (already shifted by the dialog before call)
    obstacles = []
    if mode != "Perimeter":
        for ob in p.get("obstacles", []):
            ow, ol = max(0.0, ob.get("w", 0)), max(0.0, ob.get("l", 0))
            if ow <= 0.05 or ol <= 0.05:
                continue
            ocx = _clamp(ob.get("cx", SX / 2.0) + dx, ow / 2 + 0.2, SX - ow / 2 - 0.2)
            ocy = _clamp(ob.get("cy", SY / 2.0) + dy, ol / 2 + 0.2, SY - ol / 2 - 0.2)
            obstacles.append((ocx - ow / 2, ocy - ol / 2, ow, ol))
    elif p.get("obstacles"):
        warnings.append("Building-perimeter mode ignores obstacles. It plans the loop around the building itself.")

    world = None
    building = None
    gcp_pts = []
    paths = []
    links = []
    room_descs = []
    tag_pts = []
    tag_rooms = []       # frozenset of room indices with line of sight to the tag
    floor_pts = []
    floor_rooms = []
    junctions = []

    if mode == "Perimeter":
        # scene bounding box is the BUILDING footprint; walk a loop OUTSIDE it.
        if len(rooms) > 1:
            warnings.append("Perimeter mode approximates a multi-room scene by its bounding box. "
                            "Walk the real outline; the numbers still apply.")
        s = _clamp(min(SX, SY) * 0.25, 1.5, 5.0)
        o = s + 1.2
        world = (SX + 2 * o, SY + 2 * o)
        building = (o, o, SX, SY)
        loop = [(o - s, o - s), (o + SX + s, o - s), (o + SX + s, o + SY + s),
                (o - s, o + SY + s), (o - s, o - s)]
        paths.append(loop)
        pattern.update({"path_len": round(2 * ((SX + 2 * s) + (SY + 2 * s)), 1), "standoff": round(s, 1)})
        room_descs.append("one closed loop around the building, facade kept to one side")
        segs = [((o, o), (o + SX, o)), ((o + SX, o), (o + SX, o + SY)),
                ((o + SX, o + SY), (o, o + SY)), ((o, o + SY), (o, o))]
        _march_tags(segs, spacing, tag_pts, tag_rooms, 0)
        # RTK GCP spots: entrance plus two opposite loop corners. Outdoors, GCPs
        # are the primary scale and georeferencing control (James et al. 2017;
        # Barazzetti et al. 2022): do NOT plan tag-to-tag laser lines here,
        # they would pass through the building.
        gcp_pts = [(o + SX / 2, o - 0.45), (o - s, o - s), (o + SX + s, o + SY + s)]
    elif mode == "Outdoor":
        # open outdoor area = the scene bounding box, wider serpentine
        row = round(_clamp(0.8 * min(SX, SY), 1.6, 4.0), 1)
        m = _clamp(row / 2, 0.5, 1.4)
        n_rows = max(2, int(math.ceil(SX / row)) + 1)
        xs = [_clamp(m + i * row, m, SX - m) for i in range(n_rows)]
        raw = []
        for i, x in enumerate(xs):
            raw += [(x, m), (x, SY - m)] if i % 2 == 0 else [(x, SY - m), (x, m)]
        pts = _route_around(raw, obstacles, SX, SY) if obstacles else raw
        paths.append(pts)
        pattern.update({"row_spacing": row, "n_rows": n_rows,
                        "path_len": round(_poly_len(pts) + 2 * (SX + SY), 1)})
        room_descs.append("outdoor open area: serpentine rows " + ("%g" % row) + " m apart + one boundary loop")
        segs = [((0, 0), (SX, 0)), ((SX, 0), (SX, SY)), ((SX, SY), (0, SY)), ((0, SY), (0, 0))]
        _march_tags(segs, spacing, tag_pts, tag_rooms, 0)
        gcp_pts = [(0.5, 0.5), (SX - 0.5, SY - 0.5)]
        world = (SX, SY)
    else:
        # INDOOR multi-room scene
        total = 0.0
        for ri, rm in enumerate(rooms):
            if rm["kind"] == "circle":
                pts, desc = _circle_room_path(rm)
                cx, cy, r = rm["x"], rm["y"], rm["r"]
                n = int(_clamp(math.ceil(2 * math.pi * r / spacing), 3, 60))
                for k in range(n):
                    a = 2 * math.pi * k / n
                    tag_pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
                    tag_rooms.append(frozenset([ri]))
                if r >= 3.0:
                    floor_pts.append((cx, cy))
                    floor_rooms.append(frozenset([ri]))
            else:
                pts, desc = _rect_room_path(rm, obstacles)
                _march_tags(_rect_walls(rm), spacing, tag_pts, tag_rooms, ri)
                x0, y0, x1, y1 = _room_bounds(rm)
                if min(x1 - x0, y1 - y0) >= 5.0:
                    g = _clamp(d_max, 3.0, 8.0)
                    ins = _clamp(spacing, 1.0, 3.0)
                    fx = x0 + ins
                    while fx <= x1 - ins + 1e-9:
                        fy = y0 + ins
                        while fy <= y1 - ins + 1e-9:
                            floor_pts.append((fx, fy))
                            floor_rooms.append(frozenset([ri]))
                            fy += g
                        fx += g
            paths.append(pts)
            room_descs.append(("R%d " % (ri + 1)) + desc)
            total += _poly_len(pts)
        while len(floor_pts) > 16:
            floor_pts = floor_pts[::2]
            floor_rooms = floor_rooms[::2]
        # doorway junctions: tags visible from BOTH rooms rigidly join the
        # per-room image blocks (Barazzetti et al. 2019); walking through each
        # doorway closes the loop between rooms (Vynikal et al. 2023;
        # Perfetti & Fassi 2022).
        junctions = _room_junctions(rooms)
        for (ia, ib, (jx, jy), (ux, uy)) in junctions:
            for s_ in (-0.35, 0.35):
                tag_pts.append((jx + ux * s_, jy + uy * s_))
                tag_rooms.append(frozenset([ia, ib]))
            pa = min(paths[ia], key=lambda q: math.dist(q, (jx, jy)))
            pb = min(paths[ib], key=lambda q: math.dist(q, (jx, jy)))
            links.append((pa, (jx, jy), pb))
            total += math.dist(pa, (jx, jy)) + math.dist((jx, jy), pb)
        if len(rooms) > 1 and not junctions:
            warnings.append("Rooms don't touch. Drag them together (walls snap) so every room "
                            "connects through a doorway; isolated rooms reconstruct as separate models.")
        pattern.update({"path_len": round(total + 2 * (SX + SY) * 0, 1)})
        world = (SX, SY)

    # obstacle loops and obstacle tags (small obstacle: one tag flat on top)
    ob_loops = []
    small_obs = 0
    def _room_of(pt):
        for ri, rm in enumerate(rooms):
            if rm["kind"] == "circle":
                if math.dist(pt, (rm["x"], rm["y"])) <= rm["r"]:
                    return ri
            else:
                x0, y0, x1, y1 = _room_bounds(rm)
                if x0 <= pt[0] <= x1 and y0 <= pt[1] <= y1:
                    return ri
        return 0
    for (rx, ry, ow, ol) in obstacles:
        ocx, ocy = rx + ow / 2, ry + ol / 2
        rid = _room_of((ocx, ocy)) if mode == "Indoor" else 0
        clr = 0.7
        hx, hy = ow / 2 + clr, ol / 2 + clr
        ob_loops.append([(ocx - hx, ocy - hy), (ocx + hx, ocy - hy), (ocx + hx, ocy + hy),
                         (ocx - hx, ocy + hy), (ocx - hx, ocy - hy)])
        pattern["path_len"] = round(pattern["path_len"] + 2 * (ow + ol) + 8 * clr, 1)
        if ow <= 1.2 and ol <= 1.2:
            floor_pts.append((ocx, ocy))
            floor_rooms.append(frozenset([rid]))
            small_obs += 1
        else:
            for tp in ((ocx, ry - 0.05), (ocx, ry + ol + 0.05), (rx - 0.05, ocy), (rx + ow + 0.05, ocy)):
                tag_pts.append(tp)
                tag_rooms.append(frozenset([rid]))

    # scale-constraint suggestions (indoor and outdoor-open only): two long,
    # differently oriented tag pairs, each with LINE OF SIGHT (same room), so
    # the laser can actually be shot between them. Multiple long baselines in
    # different directions constrain scale far better than one short bar
    # (James et al. 2017). Perimeter mode uses RTK GCPs for scale instead.
    tags_all = tag_pts + floor_pts
    vis_all = tag_rooms + floor_rooms
    measure_pairs = []
    if mode != "Perimeter" and len(tags_all) >= 2:
        best = None
        for i in range(len(tags_all)):
            for j in range(i + 1, len(tags_all)):
                if not (vis_all[i] & vis_all[j]):
                    continue
                dd = math.dist(tags_all[i], tags_all[j])
                if best is None or dd > best[0]:
                    best = (dd, i, j)
        if best:
            d1, i1, j1 = best
            ux = (tags_all[j1][0] - tags_all[i1][0]) / max(d1, 1e-9)
            uy = (tags_all[j1][1] - tags_all[i1][1]) / max(d1, 1e-9)
            measure_pairs.append((i1, j1, round(d1, 2)))
            best2 = None
            for i in range(len(tags_all)):
                for j in range(i + 1, len(tags_all)):
                    if {i, j} & {i1, j1} or not (vis_all[i] & vis_all[j]):
                        continue
                    dd = math.dist(tags_all[i], tags_all[j])
                    if dd < 1.0:
                        continue
                    vx = (tags_all[j][0] - tags_all[i][0]) / dd
                    vy = (tags_all[j][1] - tags_all[i][1]) / dd
                    if abs(ux * vx + uy * vy) <= 0.5:
                        if best2 is None or dd > best2[0]:
                            best2 = (dd, i, j)
            if best2:
                measure_pairs.append((best2[1], best2[2], round(best2[0], 2)))

    if outdoor:
        warnings.append("Outdoors, survey at least one RTK GCP (and one near each entrance). GCPs are the "
                        "primary scale and position control; tags mainly bridge to the interior.")
    if small_obs:
        warnings.append("Small obstacle(s): one tag laid flat on top works well. It stays visible "
                        "from every side as you orbit, and adds a horizontal-plane tag to the network.")

    n_pos = len(tags_all)
    est_time_min = round(pattern["path_len"] / max(0.1, speed) / 60.0, 1)

    n_cams = int(_clamp(p.get("n_cams", 3), 1, 3))
    frames = int(math.ceil(pattern["path_len"] / station))
    want_cube = p.get("want_cube", True)
    want_eq = p.get("want_eq", False)
    mb_cube = 2.5 if str(p.get("cube_fmt", "JPEG")).upper() == "PNG" else 0.5
    mb_eq = 25.0 if str(p.get("eq_fmt", "JPEG")).upper() == "PNG" else 4.0
    per_cam_imgs = max(1, (6 if want_cube else 0) + (1 if want_eq else 0))
    images = frames * n_cams * per_cam_imgs
    mb_per_pos = (6 * mb_cube if want_cube else 0) + (mb_eq if want_eq else 0)
    storage_gb = round(frames * n_cams * max(0.5, mb_per_pos) / 1024.0, 2)

    return {"X": SX, "Y": SY, "Z": Z, "low": low, "mid": mid, "top": top, "d_max": d_max,
            "spacing": spacing, "n_pos": n_pos, "station": station, "speed": speed, "fps": fps,
            "rooms": rooms, "junctions": junctions, "paths": paths, "links": links,
            "room_descs": room_descs, "pattern": pattern,
            "tag_pts": tag_pts, "floor_pts": floor_pts, "tags_all": tags_all,
            "tag_vis": vis_all, "measure_pairs": measure_pairs, "est_time_min": est_time_min,
            "obstacles": obstacles, "ob_loops": ob_loops, "frames": frames, "images": images,
            "storage_gb": storage_gb, "n_cams": n_cams, "outdoor": outdoor,
            "world": world, "building": building, "gcp_pts": gcp_pts, "warnings": warnings,
            "shift": (dx, dy)}


REFERENCES = [
    "Olson, E. (2011). AprilTag: A robust and flexible visual fiducial system. IEEE ICRA, 3400-3407.",
    "Wang, J., & Olson, E. (2016). AprilTag 2: Efficient and robust fiducial detection. IEEE/RSJ IROS, 4193-4198.",
    "Kalaitzakis, M., Cain, B., Carroll, S., Ambrosi, A., Whitehead, C., & Vitzilaios, N. (2021). Fiducial "
    "markers for pose estimation: overview, applications and experimental comparison of the ARTag, AprilTag, "
    "ArUco and STag markers. J. Intell. Robot. Syst., 101(4), 71.  (AprilTag: best detection across "
    "distance/orientation; accuracy degrades at grazing view angles.)",
    "Barazzetti, L., Previtali, M., Roncoroni, F., & Valente, R. (2019). Connecting inside and outside "
    "through 360° imagery for close-range photogrammetry. Int. Arch. Photogramm. Remote Sens. Spatial "
    "Inf. Sci., XLII-2/W9, 87-92.  (360° images seeing both sides of a doorway rigidly join indoor and "
    "outdoor blocks.)",
    "Vynikal, J., et al. (2023). Floor plan creation using a low-cost 360° camera. The Photogrammetric "
    "Record, 38(184).  (Long spherical-image lines drift at the ends; close loops and add control.)",
    "Kwiatek, K., & Tokarczyk, R. (2018). Photogrammetric 3D measurements based on immersive images in a "
    "spherical model. Geomatics and Environmental Engineering, 12(4), 55-74.",
    "Rau, J.-Y., & Su, B.-W. (2016). Systematic calibration for a backpacked spherical photogrammetry imaging "
    "system. Int. Arch. Photogramm. Remote Sens. Spatial Inf. Sci., XLI-B1, 695-702.",
    "James, M. R., Robson, S., d'Oleire-Oltmanns, S., & Niethammer, U. (2017). Optimising UAV topographic "
    "surveys processed with structure-from-motion: ground control quality, quantity and bundle adjustment. "
    "Geomorphology, 280, 51-66.",
    "Westoby, M. J., et al. (2012). 'Structure-from-Motion' photogrammetry: a low-cost, effective tool for "
    "geoscience applications. Geomorphology, 179, 300-314.",
    "Schönberger, J. L., & Frahm, J.-M. (2016). Structure-from-Motion revisited. IEEE CVPR, 4104-4113. (COLMAP)",
    "Kerbl, B., Kopanas, G., Leimkühler, T., & Drettakis, G. (2023). 3D Gaussian splatting for real-time "
    "radiance field rendering. ACM Trans. Graph., 42(4).",
    "Alfio, V. S., Costantino, D., & Pepe, M. (2020). Influence of image TIFF format and JPEG compression "
    "level in the accuracy of the 3D model and quality of the orthophoto in UAV photogrammetry. "
    "J. Imaging, 6(5), 30.  (JPEG at low compression ratios is near-lossless for SfM.)",
    "Akçay, Ö., et al. (2017). The effect of JPEG compression in close range photogrammetry. "
    "Int. J. Eng. Geosci., 2(1), 35-40.",
    "Perfetti, L., & Fassi, F. (2022). Handheld fisheye multicamera system: surveying meandering "
    "architectonic spaces in open-loop mode. Int. Arch. Photogramm. Remote Sens. Spatial Inf. Sci., "
    "XLVI-2/W1, 435-442.  (Long open-loop chains through connected rooms drift; close the loop.)",
    "Teppati Lose, L., Chiabrando, F., & Spano, A. (2021). 360 images for UAV-multisensor data fusion: "
    "documentation of complex indoor environments. (360 cameras document complex interiors; ground "
    "control remains fundamental to reliable results.)",
    "Barazzetti, L., Previtali, M., & Roncoroni, F. (2022). 3D modeling with 5K 360 videos. Int. Arch. "
    "Photogramm. Remote Sens. Spatial Inf. Sci., XLVI-2/W1, 65-71.  (Continuous 360 video walkthroughs "
    "reconstruct well; GCPs highlighted as fundamental.)",
    "Epic Games / Capturing Reality (2023-2025). RealityScan AprilTag numbering: detected 36h11 payloads are "
    "ranked ascending and labelled in hex (developer statement + community lookup, Epic Dev Community forums).",
]


PLAN_TIPS = [
    "Keep the rig vertical and at a steady height - a monopod/handle helps avoid bob.",
    "Walk slowly and smoothly; sudden turns and fast spins cause motion blur that wrecks matching.",
    "Lock exposure and white balance if your camera allows it, so brightness doesn't pulse frame-to-frame.",
    "Always keep a few AprilTags in view, spread in 3D (not all on one wall or one line).",
    "Walk closed loops and return to your start - loop closure dramatically improves alignment.",
    "Overlap adjacent passes by ~50% so the same surfaces appear from multiple positions.",
    "Texture-less walls, mirrors and glass break SfM - add temporary tags/markers or skip reflective areas.",
    "Capture every doorway threshold slowly; that's your bridge between rooms (and indoor↔outdoor).",
    "Avoid moving people/pets in frame; capture when the space is still.",
    "Middle camera ≈ chest height; raise the top toward (not into) the ceiling and drop the bottom toward the floor for vertical coverage.",
]


class CapturePlannerDialog(tk.Toplevel):
    CANVAS_W, CANVAS_H = 340, 280

    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.cfg = app.cfg
        self.f = app.fonts
        self.title(APP_NAME + " - capture planner")
        self.configure(bg=CARD)
        self.resizable(False, False)
        self.transient(app.root)

        head = ttk.Frame(self, style="Header.TFrame", padding=(14, 10))
        head.pack(fill="x")
        ttk.Label(head, text="Capture planner", style="Header.TLabel").pack(side="left")
        ttk.Label(head, text=" rooms · path · tags · heights ", style="Badge.TLabel").pack(side="left", padx=8)

        body = ttk.Frame(self, style="Card.TFrame", padding=12)
        body.pack(fill="both", expand=True)
        left = ttk.Frame(body, style="Card.TFrame")
        left.pack(side="left", anchor="n")
        right = ttk.Frame(body, style="Card.TFrame")
        right.pack(side="left", padx=(14, 0), anchor="n")

        self.units = tk.StringVar(value=self.cfg.get("plan_units", "m"))
        urow = ttk.Frame(left, style="Card.TFrame")
        urow.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        ttk.Label(urow, text="Units:").pack(side="left")
        ttk.Radiobutton(urow, text="metres", value="m", variable=self.units).pack(side="left", padx=4)
        ttk.Radiobutton(urow, text="feet", value="ft", variable=self.units).pack(side="left")

        ttk.Label(left, text="Mode:").grid(row=1, column=0, sticky="w", pady=2)
        self.vMode = tk.StringVar(value=self.cfg.get("plan_mode", "Indoor rooms"))
        ttk.Combobox(left, textvariable=self.vMode,
                     values=["Indoor rooms", "Outdoor open area", "Building perimeter"],
                     width=17, state="readonly").grid(row=1, column=1, sticky="w", padx=6)

        def field(r, label, key, default):
            ttk.Label(left, text=label).grid(row=r, column=0, sticky="w", pady=2)
            v = tk.StringVar(value=str(self.cfg.get(key, default)))
            ttk.Entry(left, textvariable=v, width=10).grid(row=r, column=1, sticky="w", padx=6)
            return v

        self.vZ = field(2, "Ceiling height:", "plan_Z", 3)
        self.vH = field(3, "Your height:", "plan_height", 1.78)
        self.vTop = field(4, "Top cam offset (+):", "plan_top_off", 0.55)
        self.vBot = field(5, "Bottom cam offset (-):", "plan_bottom_off", -0.75)
        self.vTag = field(6, "Tag size (mm):", "tag_size_mm", 100)
        self.vEq = field(7, "360 video width (px):", "plan_eq_width", 7680)
        self.vFps = field(8, "Planned fps:", "fps", 2)
        ttk.Separator(left, orient="horizontal").grid(row=9, column=0, columnspan=2, sticky="ew", pady=6)

        rhead = ttk.Frame(left, style="Card.TFrame")
        rhead.grid(row=10, column=0, columnspan=2, sticky="ew")
        ttk.Label(rhead, text="Rooms (drag on map; walls snap):", style="Muted.TLabel").pack(side="left")
        ttk.Button(rhead, text="+ Rect", width=6, command=lambda: self._add_room("rect")).pack(side="right")
        ttk.Button(rhead, text="+ Circle", width=7, command=lambda: self._add_room("circle")).pack(side="right", padx=2)
        self.room_frame = ttk.Frame(left, style="Card.TFrame")
        self.room_frame.grid(row=11, column=0, columnspan=2, sticky="ew")
        self.rooms = []           # {"kind","x","y","w":Var,"l":Var} or {"kind","x","y","d":Var}
        self._active_room = None

        obhead = ttk.Frame(left, style="Card.TFrame")
        obhead.grid(row=12, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        ttk.Label(obhead, text="Obstacles (islands / tables):", style="Muted.TLabel").pack(side="left")
        ttk.Button(obhead, text="+ Add", command=self._add_obstacle).pack(side="right")
        self.ob_frame = ttk.Frame(left, style="Card.TFrame")
        self.ob_frame.grid(row=13, column=0, columnspan=2, sticky="ew")
        self.obstacles = []       # {"row","w":Var,"l":Var,"cx","cy"}
        self._arm_ob = None       # obstacle awaiting a placement click

        brow0 = ttk.Frame(left, style="Card.TFrame")
        brow0.grid(row=14, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Button(brow0, text="Save scene…", command=self._save_scene).pack(side="left")
        ttk.Button(brow0, text="Load scene…", command=self._load_scene).pack(side="left", padx=6)
        ttk.Button(left, text="Compute plan", style="Accent.TButton", command=self._compute).grid(
            row=15, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        self.canvas = tk.Canvas(right, width=self.CANVAS_W, height=self.CANVAS_H, bg="#FFFFFF",
                                highlightthickness=1, highlightbackground=LINE)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        ttk.Label(right, text="path (blue) · wall tags (gold ▪) · floor tags (○) · doorway tags (◆) · GCPs (▲)\n"
                  "drag rooms to move; edges snap · 'place' arms an obstacle, then click the map",
                  style="Muted.TLabel", justify="left").pack(anchor="w", pady=(2, 6))
        self.out = scrolledtext.ScrolledText(right, width=56, height=17, wrap="word", bg="#FFFFFF",
                                             fg=INK, relief="flat", borderwidth=0, font=self.f["small"])
        self.out.pack(fill="both", expand=True)
        brow = ttk.Frame(right, style="Card.TFrame")
        brow.pack(fill="x", pady=(6, 0))
        ttk.Button(brow, text="Copy", command=self._copy).pack(side="left")
        ttk.Button(brow, text="Save plan…", command=self._save).pack(side="left", padx=6)
        ttk.Button(brow, text="Close", command=self.destroy).pack(side="right")

        self._drag = None
        self._tf = None
        self._plan = None
        self._restore_scene()
        self._compute()
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry("+" + str((sw - self.winfo_width()) // 2) + "+" + str((sh - self.winfo_height()) // 10))

    # ---- units ------------------------------------------------------------ #
    def _to_m(self, s):
        return float(s) * (0.3048 if self.units.get() == "ft" else 1.0)

    def _fmt_len(self, m):
        if self.units.get() == "ft":
            return "%.1f ft" % (m / 0.3048)
        return "%.2f m" % m

    # ---- rooms ------------------------------------------------------------ #
    def _add_room(self, kind, w="8", l="10", d="6", x=None, y=None):
        # default placement: touching the right edge of the current scene, so it
        # arrives already snapped to a wall
        if x is None:
            if self.rooms:
                bx = max((self._room_geom(r)[2]) for r in self.rooms)
                x, y = bx, 0.0
            else:
                x, y = 0.0, 0.0
        rm = {"kind": kind, "x": x, "y": y or 0.0}
        row = ttk.Frame(self.room_frame, style="Card.TFrame")
        rm["row"] = row
        idx = len(self.rooms) + 1
        rm["btn"] = ttk.Button(row, text=("R%d ◯" if kind == "circle" else "R%d ▭") % idx, width=6,
                               command=lambda r=rm: self._select_room(r))
        rm["btn"].pack(side="left")
        if kind == "circle":
            rm["d"] = tk.StringVar(value=d)
            ttk.Label(row, text="D").pack(side="left", padx=(4, 0))
            ttk.Entry(row, textvariable=rm["d"], width=4).pack(side="left", padx=2)
        else:
            rm["w"] = tk.StringVar(value=w)
            rm["l"] = tk.StringVar(value=l)
            ttk.Label(row, text="W").pack(side="left", padx=(4, 0))
            ttk.Entry(row, textvariable=rm["w"], width=4).pack(side="left", padx=2)
            ttk.Label(row, text="L").pack(side="left")
            ttk.Entry(row, textvariable=rm["l"], width=4).pack(side="left", padx=2)
        ttk.Button(row, text="✕", width=2, command=lambda r=rm: self._remove_room(r)).pack(side="left", padx=2)
        self.rooms.append(rm)
        self._relayout_rooms()
        self._active_room = rm

    def _room_geom(self, rm):
        """(x0, y0, x1, y1) in metres from the row's current entries."""
        try:
            if rm["kind"] == "circle":
                r = max(0.25, self._to_m(rm["d"].get() or 6) / 2.0)
                return (rm["x"] - r, rm["y"] - r, rm["x"] + r, rm["y"] + r)
            w = max(0.5, self._to_m(rm["w"].get() or 4))
            l = max(0.5, self._to_m(rm["l"].get() or 4))
            return (rm["x"], rm["y"], rm["x"] + w, rm["y"] + l)
        except Exception:
            return (rm["x"], rm["y"], rm["x"] + 1, rm["y"] + 1)

    def _relayout_rooms(self):
        for i, rm in enumerate(self.rooms):
            rm["row"].grid(row=i, column=0, sticky="w", pady=1)
            rm["btn"].config(text=("R%d ◯" if rm["kind"] == "circle" else "R%d ▭") % (i + 1))

    def _remove_room(self, rm):
        if len(self.rooms) <= 1:
            return
        try:
            rm["row"].destroy()
        except Exception:
            pass
        self.rooms = [r for r in self.rooms if r is not rm]
        if self._active_room is rm:
            self._active_room = self.rooms[-1]
        self._relayout_rooms()
        self._compute()

    def _select_room(self, rm):
        self._active_room = rm
        if self._plan:
            self._draw(self._plan)

    def _snap_room(self, rm, tol=0.45):
        """Snap the dragged room's edges to other rooms' edges / tangents."""
        x0, y0, x1, y1 = self._room_geom(rm)
        best_dx = best_dy = None
        for other in self.rooms:
            if other is rm:
                continue
            ox0, oy0, ox1, oy1 = self._room_geom(other)
            for mine, theirs in ((x0, ox1), (x1, ox0), (x0, ox0), (x1, ox1)):
                d = theirs - mine
                if abs(d) <= tol and (best_dx is None or abs(d) < abs(best_dx)):
                    best_dx = d
            for mine, theirs in ((y0, oy1), (y1, oy0), (y0, oy0), (y1, oy1)):
                d = theirs - mine
                if abs(d) <= tol and (best_dy is None or abs(d) < abs(best_dy)):
                    best_dy = d
        if best_dx is not None:
            rm["x"] += best_dx
        if best_dy is not None:
            rm["y"] += best_dy

    # ---- obstacles --------------------------------------------------------- #
    def _add_obstacle(self, w="1.0", l="1.0"):
        ob = {"w": tk.StringVar(value=w), "l": tk.StringVar(value=l), "cx": None, "cy": None}
        row = ttk.Frame(self.ob_frame, style="Card.TFrame")
        ob["row"] = row
        ttk.Label(row, text="W").pack(side="left")
        ttk.Entry(row, textvariable=ob["w"], width=4).pack(side="left", padx=(2, 4))
        ttk.Label(row, text="L").pack(side="left")
        ttk.Entry(row, textvariable=ob["l"], width=4).pack(side="left", padx=(2, 4))
        ttk.Button(row, text="place", width=6, command=lambda o=ob: self._arm_place(o)).pack(side="left", padx=2)
        ttk.Button(row, text="✕", width=2, command=lambda o=ob: self._remove_obstacle(o)).pack(side="left")
        self.obstacles.append(ob)
        self._relayout_obstacles()

    def _arm_place(self, ob):
        self._arm_ob = ob
        self.canvas.configure(cursor="crosshair")

    def _relayout_obstacles(self):
        for i, ob in enumerate(self.obstacles):
            ob["row"].grid(row=i, column=0, sticky="w", pady=1)

    def _remove_obstacle(self, ob):
        try:
            ob["row"].destroy()
        except Exception:
            pass
        self.obstacles = [o for o in self.obstacles if o is not ob]
        if self._arm_ob is ob:
            self._arm_ob = None
        self._relayout_obstacles()
        self._compute()

    # ---- canvas interaction ------------------------------------------------ #
    def _world_xy(self, evt):
        if not self._tf:
            return None
        ox, oy, s = self._tf
        return ((evt.x - ox) / s, (evt.y - oy) / s)

    def _on_press(self, evt):
        pt = self._world_xy(evt)
        if pt is None:
            return
        if self._arm_ob is not None:
            self._arm_ob["cx"], self._arm_ob["cy"] = pt
            self._arm_ob = None
            self.canvas.configure(cursor="")
            self._compute()
            return
        sh = self._plan.get("shift", (0, 0)) if self._plan else (0, 0)
        wx, wy = pt[0] - sh[0], pt[1] - sh[1]
        for rm in reversed(self.rooms):
            x0, y0, x1, y1 = self._room_geom(rm)
            inside = (rm["kind"] == "circle" and math.dist((wx, wy), ((x0 + x1) / 2, (y0 + y1) / 2)) <= (x1 - x0) / 2) \
                or (rm["kind"] == "rect" and x0 <= wx <= x1 and y0 <= wy <= y1)
            if inside:
                self._active_room = rm
                self._drag = (rm, wx - rm["x"], wy - rm["y"])
                self._draw(self._plan)
                return
        self._drag = None

    def _on_drag(self, evt):
        if not self._drag or not self._tf:
            return
        rm, gx, gy = self._drag
        pt = self._world_xy(evt)
        sh = self._plan.get("shift", (0, 0)) if self._plan else (0, 0)
        rm["x"], rm["y"] = pt[0] - sh[0] - gx, pt[1] - sh[1] - gy
        # light ghost feedback while dragging (full recompute happens on release)
        self.canvas.delete("ghost")
        x0, y0, x1, y1 = self._room_geom(rm)
        ox, oy, s = self._tf
        X0, Y0 = ox + (x0 + sh[0]) * s, oy + (y0 + sh[1]) * s
        X1, Y1 = ox + (x1 + sh[0]) * s, oy + (y1 + sh[1]) * s
        if rm["kind"] == "circle":
            self.canvas.create_oval(X0, Y0, X1, Y1, outline=GOLD, width=2, dash=(4, 3), tags="ghost")
        else:
            self.canvas.create_rectangle(X0, Y0, X1, Y1, outline=GOLD, width=2, dash=(4, 3), tags="ghost")

    def _on_release(self, _evt):
        if self._drag:
            rm = self._drag[0]
            self._snap_room(rm)
            self._drag = None
            self._compute()

    # ---- scene save / load -------------------------------------------------- #
    def _scene_dict(self):
        rooms = []
        for rm in self.rooms:
            if rm["kind"] == "circle":
                rooms.append({"kind": "circle", "x": rm["x"], "y": rm["y"], "d": rm["d"].get()})
            else:
                rooms.append({"kind": "rect", "x": rm["x"], "y": rm["y"], "w": rm["w"].get(), "l": rm["l"].get()})
        obs = [{"w": o["w"].get(), "l": o["l"].get(), "cx": o["cx"], "cy": o["cy"]} for o in self.obstacles]
        return {"hera_plan": 1, "units": self.units.get(), "mode": self.vMode.get(),
                "Z": self.vZ.get(), "height": self.vH.get(), "top": self.vTop.get(), "bot": self.vBot.get(),
                "tag": self.vTag.get(), "eqw": self.vEq.get(), "fps": self.vFps.get(),
                "rooms": rooms, "obstacles": obs}

    def _apply_scene(self, sc):
        for rm in self.rooms:
            rm["row"].destroy()
        for ob in self.obstacles:
            ob["row"].destroy()
        self.rooms = []
        self.obstacles = []
        self.units.set(sc.get("units", "m"))
        self.vMode.set(sc.get("mode", "Indoor rooms"))
        for k, v in (("vZ", "Z"), ("vH", "height"), ("vTop", "top"), ("vBot", "bot"),
                     ("vTag", "tag"), ("vEq", "eqw"), ("vFps", "fps")):
            if sc.get(v) is not None:
                getattr(self, k).set(str(sc[v]))
        for rm in sc.get("rooms", []):
            if rm.get("kind") == "circle":
                self._add_room("circle", d=str(rm.get("d", 6)), x=float(rm.get("x", 0)), y=float(rm.get("y", 0)))
            else:
                self._add_room("rect", w=str(rm.get("w", 8)), l=str(rm.get("l", 10)),
                               x=float(rm.get("x", 0)), y=float(rm.get("y", 0)))
        for ob in sc.get("obstacles", []):
            self._add_obstacle(w=str(ob.get("w", 1)), l=str(ob.get("l", 1)))
            self.obstacles[-1]["cx"] = ob.get("cx")
            self.obstacles[-1]["cy"] = ob.get("cy")
        if not self.rooms:
            self._add_room("rect")

    def _save_scene(self):
        path = filedialog.asksaveasfilename(title="Save planner scene", defaultextension=".json",
                                            initialfile="capture_scene.json",
                                            filetypes=[("Hera planner scene", "*.json")])
        if not path:
            return
        try:
            Path(path).write_text(json.dumps(self._scene_dict(), indent=2), encoding="utf-8")
            self.title(APP_NAME + " - capture planner  (scene saved)")
        except Exception as exc:
            messagebox.showerror(APP_NAME, "Could not save scene:\n" + str(exc))

    def _load_scene(self):
        path = filedialog.askopenfilename(title="Load planner scene",
                                          filetypes=[("Hera planner scene", "*.json"), ("All files", "*.*")])
        if not path:
            return
        try:
            sc = json.loads(Path(path).read_text(encoding="utf-8"))
            assert sc.get("hera_plan") == 1
        except Exception as exc:
            messagebox.showerror(APP_NAME, "Not a valid planner scene:\n" + str(exc))
            return
        self._apply_scene(sc)
        self._compute()

    def _restore_scene(self):
        sc = self.cfg.get("plan_scene")
        if isinstance(sc, dict) and sc.get("hera_plan") == 1:
            try:
                self._apply_scene(sc)
                return
            except Exception:
                self.rooms = []
        # first run (or legacy config): seed one room from the old W x L fields
        self._add_room("rect", w=str(self.cfg.get("plan_X", 8)), l=str(self.cfg.get("plan_Y", 10)), x=0.0, y=0.0)

    # ---- compute / format --------------------------------------------------- #
    def _mode_key(self):
        m = self.vMode.get()
        if m.startswith("Outdoor"):
            return "Outdoor"
        if m.startswith("Building"):
            return "Perimeter"
        return "Indoor"

    def _gather(self):
        rooms = []
        for rm in self.rooms:
            if rm["kind"] == "circle":
                rooms.append({"kind": "circle", "x": rm["x"], "y": rm["y"],
                              "r": max(0.25, self._to_m(rm["d"].get() or 6) / 2.0)})
            else:
                rooms.append({"kind": "rect", "x": rm["x"], "y": rm["y"],
                              "w": self._to_m(rm["w"].get() or 4), "l": self._to_m(rm["l"].get() or 4)})
        obs = []
        for ob in self.obstacles:
            try:
                w = self._to_m(ob["w"].get() or 0)
                l = self._to_m(ob["l"].get() or 0)
            except Exception:
                continue
            if w > 0.05 and l > 0.05 and ob["cx"] is not None:
                obs.append({"w": w, "l": l, "cx": ob["cx"], "cy": ob["cy"]})
        return {"rooms": rooms, "mode": self._mode_key(),
                "Z": self._to_m(self.vZ.get()), "height": self._to_m(self.vH.get()),
                "top_off": self._to_m(self.vTop.get()), "bottom_off": self._to_m(self.vBot.get()),
                "tag_mm": float(self.vTag.get()), "eq_width": float(self.vEq.get()),
                "fps": float(self.vFps.get()), "obstacles": obs,
                "n_cams": sum(1 for k in ("top", "mid", "low") if self.app.slot_vars[k].get().strip()) or 3,
                "want_cube": self.app.want_cube.get(), "want_eq": self.app.want_eq.get(),
                "cube_fmt": self.app.cube_fmt.get(), "eq_fmt": self.app.eq_fmt.get()}

    def _compute(self):
        try:
            p = self._gather()
            plan = plan_capture(p)
        except Exception as exc:
            self.out.delete("1.0", "end")
            self.out.insert("end", "Check your inputs: " + str(exc))
            return
        self._plan = plan
        self.cfg.update({"plan_units": self.units.get(), "plan_mode": self.vMode.get(),
                         "plan_Z": self.vZ.get(), "plan_height": self.vH.get(),
                         "plan_top_off": self.vTop.get(), "plan_bottom_off": self.vBot.get(),
                         "plan_eq_width": self.vEq.get(), "plan_scene": self._scene_dict()})
        save_config(self.cfg)
        self.out.delete("1.0", "end")
        self.out.insert("end", self._format(plan))
        self._draw(plan)

    def _format(self, pl):
        L = self._fmt_len
        pat = pl["pattern"]
        lines = []
        lines.append("CAMERA HEIGHTS (rig set-up)")
        lines.append("  • Top camera:    " + L(pl["top"]))
        lines.append("  • Middle camera: " + L(pl["mid"]) + "   (~ chest height)")
        lines.append("  • Bottom camera: " + L(pl["low"]))
        lines.append("")
        lines.append("APRILTAG PLACEMENT")
        lines.append("  • Reliable detection out to ~ " + L(pl["d_max"]) + " for this tag size.")
        lines.append("  • Space tags every ~ " + L(pl["spacing"]) + " along walls; " + str(pl["n_pos"]) + " positions planned.")
        lines.append("  • Stagger heights (knee / chest / above head) for 3D spread; keep 3+ visible at once.")
        nj = len(pl.get("junctions", []))
        if nj:
            lines.append("  • " + str(nj) + " doorway(s) found: 2 tags flank each doorway, visible from BOTH")
            lines.append("    rooms. These rigidly join the per-room image blocks; capture each")
            lines.append("    threshold slowly (Barazzetti et al. 2019).")
        if pl.get("floor_pts"):
            lines.append("  • " + str(len(pl["floor_pts"])) + " floor tag(s) (○) away from the walls: lay flat or on low stands.")
        lines.append("")
        lines.append("WALK PATTERN")
        for d in pl.get("room_descs", []):
            lines.append("  • " + d)
        if pat.get("standoff"):
            lines.append("  • Stand off ~ " + L(pat["standoff"]) + " from the facade; keep the building to one side.")
        if pl.get("obstacles"):
            lines.append("  • " + str(len(pl["obstacles"])) + " obstacle(s): the path detours around each; loop each one")
            lines.append("    and keep ~0.7 m clear.")
        if nj:
            lines.append("  • Walk room to room THROUGH each doorway without stopping; finish back at")
            lines.append("    your start. Closed loops stop drift from accumulating along the chain")
            lines.append("    (Vynikal et al. 2023; Perfetti & Fassi 2022).")
        lines.append("  • Approx path length: " + L(pat["path_len"]))
        lines.append("")
        if pl.get("measure_pairs"):
            lines.append("SCALE (laser measurements, line of sight within one room)")
            for k, (i, j, dd) in enumerate(pl["measure_pairs"]):
                lines.append("  • M" + str(k + 1) + ": tag #" + str(i + 1) + " ↔ tag #" + str(j + 1)
                             + "  (~ " + L(dd) + ", dashed on the map)")
            lines.append("  • Enter these as distance constraints in RealityScan/COLMAP. Two long,")
            lines.append("    differently oriented baselines constrain scale far better than one")
            lines.append("    short bar (James et al. 2017). Add a vertical pair too (tape a tag high).")
            lines.append("")
        if pl.get("gcp_pts"):
            lines.append("GEOREFERENCING (▲ on the map)")
            lines.append("  • Survey the marked spots with your RTK rover: one at the entrance, plus")
            lines.append("    the far corners. Outdoors, GCPs are the scale AND position control")
            lines.append("    (James et al. 2017; Barazzetti et al. 2022). Never laser between tags")
            lines.append("    on opposite sides of a building; the line has no line of sight.")
            lines.append("")
        lines.append("PACE")
        lines.append("  • Aim for a captured frame every ~ " + L(pl["station"]) + ".")
        lines.append("  • At " + ("%g" % pl["fps"]) + " fps that's ~ %.2f m/s" % pl["speed"]
                     + " (%.2f ft/s)." % (pl["speed"] / 0.3048))
        lines.append("  • Rough capture time for the main path: ~ " + str(pl["est_time_min"]) + " min.")
        lines.append("")
        lines.append("ESTIMATES (rough, for storage/time planning)")
        lines.append("  • ~ " + str(pl["frames"]) + " capture positions × " + str(pl["n_cams"]) + " camera(s).")
        lines.append("  • ~ " + format(pl["images"], ",") + " output images after Hera.")
        lines.append("  • ~ " + str(pl["storage_gb"]) + " GB on disk with the current output formats.")
        lines.append("")
        if pl["warnings"]:
            lines.append("HEADS-UP")
            for w in pl["warnings"]:
                lines.append("  ! " + w)
            lines.append("")
        lines.append("REMEMBER (capture with the rig)")
        for t in PLAN_TIPS:
            lines.append("  • " + t)
        lines.append("")
        lines.append("Sources for these numbers: Workflow Tips ▸ References.")
        return "\n".join(lines)

    # ---- drawing ------------------------------------------------------------ #
    def _draw(self, pl):
        c = self.canvas
        c.delete("all")
        W, H = self.CANVAS_W, self.CANVAS_H
        pad = 16
        wX, wY = pl["world"] if pl.get("world") else (pl["X"], pl["Y"])
        s = min((W - 2 * pad) / max(wX, 0.1), (H - 2 * pad) / max(wY, 0.1))
        ox = (W - wX * s) / 2
        oy = (H - wY * s) / 2

        def P(pt):
            return (ox + pt[0] * s, oy + pt[1] * s)
        self._tf = (ox, oy, s)

        if pl.get("building"):
            c.create_rectangle(ox, oy, ox + wX * s, oy + wY * s, outline=LINE, width=1, dash=(2, 3))
            bx, by, bw, bh = pl["building"]
            c.create_rectangle(*P((bx, by)), *P((bx + bw, by + bh)), fill="#DDD6C4", outline=INK, width=2)
            c.create_text(*P((bx + bw / 2, by + bh / 2)), text="building", fill=MUTED, font=self.f["small"])
        else:
            for ri, rm in enumerate(pl.get("rooms", [])):
                x0, y0, x1, y1 = _room_bounds(rm)
                active = (self._active_room is not None and ri < len(self.rooms)
                          and self.rooms[ri] is self._active_room)
                kw = dict(outline=GOLD_DK if active else INK, width=2)
                if rm["kind"] == "circle":
                    c.create_oval(*P((x0, y0)), *P((x1, y1)), **kw)
                else:
                    c.create_rectangle(*P((x0, y0)), *P((x1, y1)), **kw)
                c.create_text(*P(((x0 + x1) / 2, y0 + 0.02 * (y1 - y0) + 0.35)),
                              text="R" + str(ri + 1), fill=GOLD_DK if active else MUTED, font=self.f["small"])
        for loop in pl.get("ob_loops", []):
            flat = []
            for pt in loop:
                flat += list(P(pt))
            c.create_line(*flat, fill=BLUE_DK, width=2, dash=(3, 2))
        for idx, (bx, by, bw, bh) in enumerate(pl.get("obstacles", [])):
            c.create_rectangle(*P((bx, by)), *P((bx + bw, by + bh)), fill="#E9DEBE", outline=GOLD_DK)
            c.create_text(*P((bx + bw / 2, by + bh / 2)), text=str(idx + 1), fill=MUTED, font=self.f["small"])
        for pts in pl.get("paths", []):
            if len(pts) >= 2:
                flat = []
                for pt in pts:
                    flat += list(P(pt))
                c.create_line(*flat, fill=BLUE, width=2)
                sx, sy = P(pts[0])
                c.create_oval(sx - 3, sy - 3, sx + 3, sy + 3, fill=GREEN_TXT, outline="")
        for (pa, j, pb) in pl.get("links", []):
            c.create_line(*P(pa), *P(j), *P(pb), fill=BLUE_DK, width=1, dash=(2, 3))
        label_ids = set()
        for (i, j, _dd) in pl.get("measure_pairs", []):
            a, b = pl["tags_all"][i], pl["tags_all"][j]
            c.create_line(*P(a), *P(b), fill=GOLD_DK, width=1, dash=(5, 3))
            label_ids.update((i, j))
        n_wall = len(pl.get("tag_pts", []))
        for k, pt in enumerate(pl.get("tags_all", [])):
            x, y = P(pt)
            vis = pl["tag_vis"][k] if k < len(pl.get("tag_vis", [])) else frozenset()
            if len(vis) > 1:                                   # doorway tag
                c.create_polygon(x, y - 4, x + 4, y, x, y + 4, x - 4, y, fill=GOLD, outline=GOLD_DK)
            elif k < n_wall:
                c.create_rectangle(x - 2.5, y - 2.5, x + 2.5, y + 2.5, fill=GOLD, outline=GOLD_DK)
            else:
                c.create_oval(x - 3, y - 3, x + 3, y + 3, fill="#FFFFFF", outline=GOLD_DK, width=2)
            if k in label_ids:
                c.create_text(x + 7, y - 7, text=str(k + 1), fill=GOLD_DK, font=self.f["small"])
        for pt in pl.get("gcp_pts", []):
            x, y = P(pt)
            c.create_polygon(x, y - 5, x - 5, y + 4, x + 5, y + 4, fill=GREEN_TXT, outline="")
        cap = self._fmt_len(pl["X"]) + " × " + self._fmt_len(pl["Y"])
        cap += "  (building)" if pl.get("building") else "  (scene extent)"
        c.create_text(W / 2, H - 6, text=cap, fill=MUTED, font=self.f["small"])

    def _copy(self):
        self.app.root.clipboard_clear()
        self.app.root.clipboard_append(self.out.get("1.0", "end"))

    def _save(self):
        path = filedialog.asksaveasfilename(title="Save capture plan", defaultextension=".md",
                                            filetypes=[("Markdown", "*.md"), ("Text", "*.txt")])
        if not path:
            return
        try:
            Path(path).write_text("# Hera capture plan\n\n```\n" + self.out.get("1.0", "end") + "\n```\n\n## References\n\n"
                                  + "\n".join("- " + r for r in REFERENCES) + "\n", encoding="utf-8")
            self.title(APP_NAME + " - capture planner  (saved)")
        except Exception as exc:
            messagebox.showerror(APP_NAME, "Could not save:\n" + str(exc))


# --------------------------------------------------------------------------- #
# Workflow tips (before / after Hera)
# --------------------------------------------------------------------------- #
BEFORE_TIPS = [
    ("Slate every clip", "With all cameras already rolling, do an audio slate - a sharp clap, or your "
     "four-cue clap-stomp…stomp-clap. The spike lets you line up the Top/Middle/Low tracks and trim "
     "them to a common start."),
    ("Export equirectangular", "From Insta360 Studio, export EQUIRECTANGULAR video (not the raw "
     "dual-fisheye .insv) at the highest resolution and bitrate. Turn off sharpening/denoise that "
     "alter geometry."),
    ("Match all three cameras", "Same resolution, fps, and exposure mode on Top, Middle and Low so the "
     "faces line up and brightness matches."),
    ("Lock exposure & white balance", "Auto-exposure pulsing between frames hurts matching. Lock AE/AWB "
     "if the camera allows it."),
    ("Go easy on stabilization", "Aggressive in-camera stabilization / horizon-lock re-projects pixels and "
     "can warp geometry. Prefer a steady rig; if you must stabilize, do it identically on every camera."),
    ("Name files by slot", "Save as something you can tell apart at a glance - e.g. top.mp4 / middle.mp4 / "
     "low.mp4 - matching the rig position."),
    ("Clean lenses, watch the light", "Wipe the lenses; avoid direct sun flare and blown highlights; "
     "favour even, diffuse lighting."),
    ("Move slow and steady", "Use the Capture planner for spacing, path and pace. Avoid fast spins "
     "(motion blur) and keep AprilTags in view, spread in 3D."),
]

AFTER_TIPS = [
    ("Pick ONE image set per camera", "Feed your reconstruction software either the equirectangular frames "
     "or the cube faces - not both for the same camera. RealityScan / COLMAP / Metashape generally prefer "
     "standard 90° cube faces; equirect suits pipelines/3DGS that accept spherical input."),
    ("Raise features & tie points", "Indoors is texture-poor. Bump max features per image and tie points "
     "(RealityScan/Metashape), or raise COLMAP's SiftExtraction.max_num_features to ~8k-16k. Use "
     "sequential + vocab-tree (or exhaustive) matching so loops close."),
    ("Use overlap", "Hera's Face overlap (FOV) adds shared content across face seams, which makes matching "
     "more robust. ~100-110° is a good starting point; verify with a Test render."),
    ("Mask the noise", "Mask moving people/pets, the operator and rig if visible, and mirrors/glass - "
     "reflections create false geometry."),
    ("Tie real-world scale to your tags (indoors)", "Measure tag-to-tag distance with the laser, LINE OF SIGHT "
     "within one room, and enter it as a known distance / control constraint. The planner suggests two pairs. "
     "Outdoors, RTK GCPs provide scale and position instead; never plan a laser line through a building."),
    ("3DGS needs a clean SfM first", "For LichtFeld Studio and similar, get a solid COLMAP solution, then "
     "train. Use LOCAL-ORIGIN coordinates (subtract a base easting/northing) - full UTM/State-Plane values "
     "overflow float precision during training."),
    ("Don't mix height datums", "When georeferencing, don't mix orthometric and ellipsoidal heights - "
     "pick one and stay consistent."),
    ("Close your loops", "Keep capture loops closed and passes overlapping; loop closure is what removes "
     "drift across a big indoor space."),
]

TIEIN_TIPS = [
    ("Shared marks are the bridge", "Tie the indoor walk-around and the outdoor drone model together with "
     "features BOTH can see: put AprilTags in the doorway/threshold, visible from inside and out."),
    ("Survey a GCP outside the door", "Place a marked ground control point right outside the entrance and log "
     "it with RTK (your Emlid). That point anchors both models to the same real-world coordinates."),
    ("Fly the drone as close as safe", "Fly the exterior as close to the building and the open doorway as you "
     "safely can, so the aerial imagery overlaps the first few metres your ground rig saw inside."),
    ("Walk out through the door", "Start inside with the rig, keep a doorway tag in view, and walk straight "
     "out without stopping - that continuous overlap stitches interior to exterior."),
    ("Spread threshold tags in 3D", "Three tags in a line on the door frame is a weak, ambiguous constraint. "
     "Spread them in 3D - frame, floor, and a stand - so the bridge is rigid."),
    ("One datum, one origin", "Georeference both models in the same CRS, never mix orthometric and ellipsoidal "
     "heights, and solve/train in local-origin coordinates (subtract a base easting/northing)."),
]

OUTDOOR_TIPS = [
    ("RTK is your friend outside", "Outdoors you can lean on RTK GCPs for scale and position - but still keep "
     "AprilTags near the building and entrances so the indoor bridge holds."),
    ("Perimeter = one overlapping loop", "For a building's perimeter, walk a full loop keeping the wall ~2-4 m "
     "to one side, then close the loop back to your start point."),
    ("Open area = wider serpentine", "For an open outdoor area, use the same lawnmower rows as indoors but "
     "wider (surfaces are farther away), plus a boundary loop."),
    ("Mind the sun and sky", "Lock exposure; don't shoot into the sun; overcast light is ideal. Blank sky "
     "simply won't reconstruct - that's fine, not a problem."),
    ("Watch for moving clutter", "Cars, pedestrians and wind-blown foliage cause bad matches - capture when "
     "it's calm and mask movers afterward."),
]


class TipsDialog(tk.Toplevel):
    def __init__(self, app, start="before"):
        super().__init__(app.root)
        self.title(APP_NAME + " - workflow tips")
        self.configure(bg=PAGE); self.resizable(False, False); self.transient(app.root)
        f = app.fonts
        head = ttk.Frame(self, style="Header.TFrame", padding=(14, 10)); head.pack(fill="x")
        ttk.Label(head, text="Workflow tips", style="Header.TLabel").pack(side="left")
        ttk.Label(head, text=" plan → capture → Hera → reconstruct ", style="Badge.TLabel").pack(side="left", padx=8)

        wrap = tk.Frame(self, bg=PAGE); wrap.pack(fill="both", expand=True, padx=12, pady=12)
        txt = scrolledtext.ScrolledText(wrap, width=82, height=30, wrap="word", bg="#FFFFFF",
                                        fg=INK, relief="flat", borderwidth=0, font=f["small"])
        txt.pack(fill="both", expand=True)
        txt.tag_configure("sec", font=f["section"], foreground=BLACK, spacing1=14, spacing3=6)
        txt.tag_configure("intro", foreground=MUTED, spacing3=6)
        txt.tag_configure("h", font=f["button"], foreground=GOLD_DK, spacing1=6, spacing3=2)

        def section(title, intro, tips):
            txt.insert("end", title + "\n", "sec")
            txt.insert("end", intro + "\n", "intro")
            for t_, b_ in tips:
                txt.insert("end", "▸ " + t_ + "\n", "h")
                txt.insert("end", "   " + b_ + "\n")

        # Before at the top → After at the bottom, with the tie-in/outdoor guidance in between.
        section("BEFORE HERA  ·  capture & export",
                "Clean, matched footage off the rig - where most reconstruction problems are actually born.",
                BEFORE_TIPS)
        section("INDOOR ↔ OUTDOOR  ·  tying two models together",
                "How to tether an interior walk-around to an exterior drone flight into one model.",
                TIEIN_TIPS)
        section("OUTDOOR  ·  walking the rig outside",
                "Same rig, but open areas or a building perimeter.", OUTDOOR_TIPS)
        after_index = txt.index("end-1c")
        section("AFTER HERA  ·  reconstruction",
                "Once Hera has written your frames/faces - RealityScan, COLMAP, Metashape, and 3DGS tools like LichtFeld.",
                AFTER_TIPS)
        txt.insert("end", "REFERENCES  ·  the research behind these numbers\n", "sec")
        for r in REFERENCES:
            txt.insert("end", "• " + r + "\n")
        txt.config(state="disabled")
        txt.see(after_index if start == "after" else "1.0")

        tk.Button(self, text="Close", command=self.destroy, bg=GOLD, fg=BLACK, relief="flat",
                  padx=16, pady=5, font=f["button"]).pack(pady=(0, 12))
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry("+" + str((sw - self.winfo_width()) // 2) + "+" + str((sh - self.winfo_height()) // 8))


# --------------------------------------------------------------------------- #
# Main app
# --------------------------------------------------------------------------- #
class App:
    def __init__(self, root):
        self.root = root
        self.cfg = load_config()
        self.cfg["ffmpeg"] = find_executable("ffmpeg", self.cfg["ffmpeg"])
        self.cfg["ffprobe"] = find_executable("ffprobe", self.cfg["ffprobe"])
        self.proc = None; self.cancelled = False; self.worker = None
        self.msgq = queue.Queue(); self._syncing = False; self._loading = False; self._last_out = None

        self.fonts = make_fonts(); apply_theme(root, self.fonts)
        self.logo = load_photo(HERA_LOGO_B64); self.rcl_logo = load_photo(RCL_LOGO_B64)

        # per-camera state (plain python; controls reflect the selected camera)
        self.cam_state = {slot: {"yaw": self.cfg["cams"][slot]["yaw"],
                                 "pitch": self.cfg["cams"][slot]["pitch"],
                                 "roll": self.cfg["cams"][slot]["roll"],
                                 "faces": set(self.cfg["cams"][slot]["faces"]),
                                 "face_fov": self.cfg["cams"][slot].get("face_fov", 90.0)}
                          for slot in ("top", "mid", "low")}
        self._cur = self.cfg.get("cam_target", "top")

        root.title(APP_NAME + " - " + APP_PRODUCT + "   v" + APP_VERSION)
        root.geometry("900x840"); root.minsize(720, 480)

        self._build_ui()
        self._refresh_ffmpeg_status()
        self._load_cam(self._cur)
        self.root.after(100, self._drain_queue)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        if not self.cfg.get("skip_intro"):
            self.root.after(120, lambda: IntroDialog(self))

    # ---- scaffolding ------------------------------------------------------ #
    def _build_ui(self):
        f = self.fonts
        header = ttk.Frame(self.root, style="Header.TFrame", padding=(16, 12)); header.pack(fill="x")
        if self.logo:
            ttk.Label(header, image=self.logo, style="Header.TLabel").pack(side="left", padx=(0, 16))
        tbox = ttk.Frame(header, style="Header.TFrame"); tbox.pack(side="left")
        trow = ttk.Frame(tbox, style="Header.TFrame"); trow.pack(anchor="w")
        ttk.Label(trow, text=APP_NAME, style="Header.TLabel").pack(side="left")
        ttk.Label(trow, text=" " + APP_PRODUCT + " ", style="Badge.TLabel").pack(side="left", padx=10)
        ttk.Label(tbox, text=APP_TAGLINE, style="HeaderSub.TLabel").pack(anchor="w")

        # top toolbar (fixed): Hera tools + reset
        bar = ttk.Frame(self.root, style="Card.TFrame", padding=(12, 7)); bar.pack(fill="x")
        ttk.Label(bar, text="Hera tools:", style="Muted.TLabel").pack(side="left", padx=(2, 8))
        ttk.Button(bar, text="AprilTag Generator", style="Gold.TButton",
                   command=lambda: AprilTagDialog(self)).pack(side="left", padx=3)
        ttk.Button(bar, text="Capture Planner", style="Gold.TButton",
                   command=lambda: CapturePlannerDialog(self)).pack(side="left", padx=3)
        ttk.Button(bar, text="Workflow Tips", style="Gold.TButton",
                   command=lambda: TipsDialog(self)).pack(side="left", padx=3)
        tk.Button(bar, text="Reset to Defaults", command=self._reset_defaults,
                  bg="#C0392B", fg="#FFFFFF", relief="flat", padx=12, pady=4,
                  activebackground="#A93226", activeforeground="#FFFFFF",
                  font=self.fonts["button"]).pack(side="right", padx=2)

        # footer (fixed)
        foot = ttk.Frame(self.root, style="Footer.TFrame", padding=(14, 6)); foot.pack(fill="x", side="bottom")
        if self.rcl_logo:
            ttk.Label(foot, image=self.rcl_logo, background=PAGE).pack(side="right")
        ttk.Label(foot, style="Footer.TLabel",
                  text=("© 2026 Rustin C. Newbold · Rusty's Creation Lab · Hera is " + APP_PRODUCT
                        + " · MIT License")
                  ).pack(side="left", anchor="w")

        # scrollable middle
        mid = ttk.Frame(self.root); mid.pack(fill="both", expand=True)
        self.vcanvas = tk.Canvas(mid, bg=PAGE, highlightthickness=0)
        vbar = ttk.Scrollbar(mid, orient="vertical", command=self.vcanvas.yview)
        self.vcanvas.configure(yscrollcommand=vbar.set)
        vbar.pack(side="right", fill="y"); self.vcanvas.pack(side="left", fill="both", expand=True)
        self.body = ttk.Frame(self.vcanvas, padding=12)
        self._body_id = self.vcanvas.create_window((0, 0), window=self.body, anchor="nw")
        self.body.bind("<Configure>", lambda e: self.vcanvas.configure(scrollregion=self.vcanvas.bbox("all")))
        self.vcanvas.bind("<Configure>", lambda e: self.vcanvas.itemconfigure(self._body_id, width=e.width))
        self.vcanvas.bind_all("<MouseWheel>", self._wheel)
        self.vcanvas.bind_all("<Button-4>", lambda e: self.vcanvas.yview_scroll(-1, "units"))
        self.vcanvas.bind_all("<Button-5>", lambda e: self.vcanvas.yview_scroll(1, "units"))

        self._build_body(self.body)

    def _wheel(self, event):
        delta = -1 if event.delta > 0 else 1
        self.vcanvas.yview_scroll(delta, "units")

    def _log_wheel(self, event):
        self.log.yview_scroll(-1 if event.delta > 0 else 1, "units")
        return "break"

    # ---- body ------------------------------------------------------------- #
    def _build_body(self, outer):
        f = self.fonts
        outer.columnconfigure(0, weight=1)
        pad = {"padx": 8, "pady": 5}

        ff = ttk.LabelFrame(outer, text="FFmpeg", style="Card.TLabelframe", padding=8)
        ff.grid(row=0, column=0, sticky="ew", **pad); ff.columnconfigure(0, weight=1)
        self.ff_status = ttk.Label(ff, text="checking..."); self.ff_status.grid(row=0, column=0, sticky="w")
        ttk.Button(ff, text="Requirements…", command=lambda: IntroDialog(self)).grid(row=0, column=1, padx=2)
        ttk.Button(ff, text="Locate ffmpeg/ffprobe…", command=self._locate_ffmpeg).grid(row=0, column=2, sticky="e")

        inp = ttk.LabelFrame(outer, text="Input 360 videos (equirectangular .mp4 / .mov)",
                             style="Card.TLabelframe", padding=8)
        inp.grid(row=1, column=0, sticky="ew", **pad); inp.columnconfigure(1, weight=1)
        self.slot_vars = {}
        for i, (display, key) in enumerate(SLOTS):
            ttk.Label(inp, text=display + ":").grid(row=i, column=0, sticky="w", padx=4, pady=3)
            var = tk.StringVar(); self.slot_vars[key] = var
            ent = ttk.Entry(inp, textvariable=var)
            ent.grid(row=i, column=1, sticky="ew", padx=4, pady=3)
            self._enable_drop(ent, var)
            ttk.Button(inp, text="Browse…", command=lambda v=var: self._browse_video(v)).grid(row=i, column=2, padx=2)
            ttk.Button(inp, text="Clear", command=lambda v=var: v.set("")).grid(row=i, column=3, padx=2)
        drop_hint = " Drag a video onto a box or use Browse." if getattr(self.root, "_hera_dnd", False) else ""
        ttk.Label(inp, text="Any slot may be left blank." + drop_hint + " Before filming, skim Workflow Tips "
                  "(top bar): slate/clap to sync, export equirect at max bitrate, name files by slot.",
                  style="Muted.TLabel", wraplength=560).grid(row=len(SLOTS), column=1, columnspan=3, sticky="w", padx=4)

        s = ttk.LabelFrame(outer, text="Global settings (apply to all cameras)", style="Card.TLabelframe", padding=8)
        s.grid(row=2, column=0, sticky="ew", **pad)
        for c in (1, 2, 3):
            s.columnconfigure(c, weight=1)
        ttk.Label(s, text="Frame rate (fps):").grid(row=0, column=0, sticky="w", padx=4, pady=3)
        self.fps_var = tk.StringVar(value=str(self.cfg["fps"]))
        fe = ttk.Entry(s, textvariable=self.fps_var, width=8); fe.grid(row=0, column=1, sticky="w", padx=4)
        ttk.Label(s, text="0.1-10; fractions ok (1/3)", style="Muted.TLabel").grid(row=1, column=0, columnspan=2, sticky="w", padx=4)
        fe.bind("<KeyRelease>", self._on_fps_entry)
        ok, _, val = parse_fps(self.cfg["fps"])
        self.fps_scale = ttk.Scale(s, from_=0.1, to=10.0, orient="horizontal", command=self._on_fps_slider)
        self.fps_scale.set(val if ok else 1.0); self.fps_scale.grid(row=0, column=2, columnspan=2, sticky="ew", padx=4)
        self.want_eq = tk.BooleanVar(value=self.cfg["want_equirect"])
        self.want_cube = tk.BooleanVar(value=self.cfg["want_cubemap"])
        ttk.Checkbutton(s, text="Extract equirectangular frames", variable=self.want_eq).grid(
            row=2, column=0, columnspan=2, sticky="w", padx=4, pady=(8, 2))
        self.eq_fmt = tk.StringVar(value=self.cfg.get("eq_fmt", "JPEG"))
        ttk.Combobox(s, textvariable=self.eq_fmt, values=["JPEG", "PNG"], width=6,
                     state="readonly").grid(row=2, column=1, sticky="e", padx=4, pady=(8, 2))
        ttk.Checkbutton(s, text="Generate cubemap faces", variable=self.want_cube).grid(
            row=2, column=2, sticky="w", padx=4, pady=(8, 2))
        self.cube_fmt = tk.StringVar(value=self.cfg.get("cube_fmt", "JPEG"))
        ttk.Combobox(s, textvariable=self.cube_fmt, values=["JPEG", "PNG"], width=6,
                     state="readonly").grid(row=2, column=3, sticky="w", padx=4, pady=(8, 2))
        ttk.Label(s, text="Interpolation:").grid(row=3, column=0, sticky="w", padx=4, pady=(6, 0))
        self.interp_var = tk.StringVar(value=self.cfg["interp"])
        ttk.Combobox(s, textvariable=self.interp_var, values=INTERP_CHOICES, width=10, state="readonly").grid(
            row=3, column=1, sticky="w", padx=4, pady=(6, 0))
        ttk.Label(s, text="Face size px (blank=auto):").grid(row=3, column=2, sticky="w", pady=(6, 0))
        self.facesize_var = tk.StringVar(value=str(self.cfg["face_size"]))
        ttk.Entry(s, textvariable=self.facesize_var, width=8).grid(row=3, column=3, sticky="w", padx=4, pady=(6, 0))
        ttk.Label(s, text="JPEG q (2 best..31):").grid(row=4, column=0, sticky="w", padx=4, pady=(6, 0))
        self.jpegq_var = tk.IntVar(value=self.cfg["jpeg_q"])
        ttk.Spinbox(s, from_=2, to=31, textvariable=self.jpegq_var, width=6).grid(row=4, column=1, sticky="w", padx=4, pady=(6, 0))
        ttk.Label(s, text="PNG compression (0..9):").grid(row=4, column=2, sticky="w", pady=(6, 0))
        self.pnglvl_var = tk.IntVar(value=self.cfg["png_level"])
        ttk.Spinbox(s, from_=0, to=9, textvariable=self.pnglvl_var, width=6).grid(row=4, column=3, sticky="w", padx=4, pady=(6, 0))
        self.write_colmap = tk.BooleanVar(value=self.cfg.get("write_colmap", False))
        ttk.Checkbutton(s, text="Write COLMAP camera calibration (cameras.txt) into each cubemap folder",
                        variable=self.write_colmap).grid(row=5, column=0, columnspan=4, sticky="w", padx=4, pady=(8, 0))
        ttk.Label(s, text="Exact pinhole intrinsics from face size + FOV; no manual calibration downstream.",
                  style="Muted.TLabel").grid(row=6, column=0, columnspan=4, sticky="w", padx=4)

        self._build_percam(outer).grid(row=3, column=0, sticky="ew", **pad)

        out = ttk.LabelFrame(outer, text="Output", style="Card.TLabelframe", padding=8)
        out.grid(row=4, column=0, sticky="ew", **pad); out.columnconfigure(1, weight=1)
        ttk.Label(out, text="Output folder:").grid(row=0, column=0, sticky="w", padx=4, pady=3)
        self.outdir_var = tk.StringVar(value=self.cfg["output_dir"])
        ttk.Entry(out, textvariable=self.outdir_var).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(out, text="Browse…", command=self._browse_outdir).grid(row=0, column=2, padx=2)
        ttk.Label(out, text="Session prefix:").grid(row=1, column=0, sticky="w", padx=4, pady=3)
        self.prefix_var = tk.StringVar(value=self.cfg["prefix"])
        ttk.Entry(out, textvariable=self.prefix_var, width=20).grid(row=1, column=1, sticky="w", padx=4)
        ttk.Label(out, text="folders: <prefix>_<top|mid|low>_<equirect|cubemap>/", style="Muted.TLabel").grid(
            row=2, column=1, sticky="w", padx=4)

        act = ttk.Frame(outer); act.grid(row=6, column=0, sticky="ew", **pad); act.columnconfigure(4, weight=1)
        self.run_btn = ttk.Button(act, text="Run", style="Accent.TButton", command=self._on_run)
        self.run_btn.grid(row=0, column=0, padx=4)
        self.cancel_btn = ttk.Button(act, text="Cancel", command=self._on_cancel, state="disabled")
        self.cancel_btn.grid(row=0, column=1, padx=4)
        self.open_btn = ttk.Button(act, text="Open output", command=self._open_output, state="disabled")
        self.open_btn.grid(row=0, column=3, padx=4)
        ttk.Button(act, text="Preview commands", command=self._on_preview).grid(row=0, column=5, padx=4)

        self.file_lbl = ttk.Label(outer, text="Idle.", style="Status.TLabel")
        self.file_lbl.grid(row=7, column=0, sticky="w", padx=12)
        self.progress = ttk.Progressbar(outer, mode="determinate", maximum=1000)
        self.progress.grid(row=8, column=0, sticky="ew", padx=12, pady=(2, 6))

        logf = ttk.LabelFrame(outer, text="Log", style="Card.TLabelframe", padding=6)
        logf.grid(row=9, column=0, sticky="nsew", **pad)
        outer.rowconfigure(9, weight=1); logf.columnconfigure(0, weight=1); logf.rowconfigure(0, weight=1)
        self.log = scrolledtext.ScrolledText(logf, height=8, wrap="word", bg="#FFFFFF", fg=INK,
                                             insertbackground=INK, relief="flat", borderwidth=0, font=f["mono"])
        self.log.grid(row=0, column=0, sticky="nsew")
        self.log.bind("<MouseWheel>", self._log_wheel)
        lb = ttk.Frame(logf); lb.configure(style="Card.TLabelframe"); lb.grid(row=1, column=0, sticky="e", pady=(4, 0))
        ttk.Button(lb, text="Copy log", command=self._copy_log).grid(row=0, column=0, padx=2)
        ttk.Button(lb, text="Clear log", command=lambda: self.log.delete("1.0", "end")).grid(row=0, column=1, padx=2)

    def _build_percam(self, parent):
        f = self.fonts
        frame = ttk.LabelFrame(parent, text="Per-camera: cubemap orientation, faces & overlap",
                               style="Card.TLabelframe", padding=10)
        frame.columnconfigure(1, weight=1)

        # camera selector (segmented, full width)
        sel = ttk.Frame(frame); sel.configure(style="Card.TLabelframe")
        sel.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Label(sel, text="Editing camera:").pack(side="left", padx=(0, 6))
        self.cam_target = tk.StringVar(value=self._cur)
        for disp, slot in SLOTS:
            ttk.Radiobutton(sel, text=disp, value=slot, variable=self.cam_target,
                            command=self._switch_cam).pack(side="left", padx=2)

        # left: visual + view selector
        left = ttk.Frame(frame); left.configure(style="Card.TLabelframe")
        left.grid(row=1, column=0, sticky="nw", padx=(0, 14))
        self.canvas = tk.Canvas(left, width=300, height=270, bg="#FFFFFF",
                                highlightthickness=1, highlightbackground=LINE)
        self.canvas.pack()
        vrow = ttk.Frame(left); vrow.configure(style="Card.TLabelframe"); vrow.pack(anchor="w", pady=(6, 0))
        ttk.Label(vrow, text="View:").pack(side="left")
        self.rig_view = tk.StringVar(value=self.cfg.get("rig_view", "side"))
        for label, val in [("Side", "side"), ("Top", "top"), ("Front", "front"), ("Faces", "faces")]:
            ttk.Radiobutton(vrow, text=label, value=val, variable=self.rig_view,
                            command=self._draw_rig).pack(side="left", padx=2)

        # right: controls
        right = ttk.Frame(frame); right.configure(style="Card.TLabelframe")
        right.grid(row=1, column=1, sticky="new")
        right.columnconfigure(1, weight=1)

        fbox = ttk.LabelFrame(right, text="Generate which faces", style="Card.TLabelframe", padding=4)
        fbox.grid(row=0, column=0, columnspan=3, sticky="ew")
        self.face_vars = {}
        for i, face in enumerate(FACES):
            v = tk.BooleanVar(value=True); self.face_vars[face["key"]] = v
            ttk.Checkbutton(fbox, text=face["label"], variable=v,
                            command=self._on_ctrl_change).grid(row=i // 3, column=i % 3, sticky="w", padx=6, pady=1)

        self.yaw_var = tk.DoubleVar(value=0.0); self.pitch_var = tk.DoubleVar(value=0.0)
        self.roll_var = tk.DoubleVar(value=0.0); self.fov_var = tk.DoubleVar(value=90.0)
        self._ori_labels = {}

        def slider_row(r, name, var, lo, hi, hint=""):
            ttk.Label(right, text=name).grid(row=r, column=0, sticky="w", pady=3)
            holder = ttk.Frame(right); holder.configure(style="Card.TLabelframe")
            holder.grid(row=r, column=1, columnspan=2, sticky="ew", padx=4)
            holder.columnconfigure(0, weight=1)
            ttk.Scale(holder, from_=lo, to=hi, orient="horizontal", variable=var).grid(row=0, column=0, sticky="ew")
            ttk.Spinbox(holder, from_=lo, to=hi, textvariable=var, width=6, increment=1).grid(row=0, column=1, padx=(6, 0))
            var.trace_add("write", lambda *_a: self._on_ctrl_change())
            if hint:
                ttk.Label(right, text=hint, style="Muted.TLabel").grid(row=r + 1, column=1, columnspan=2, sticky="w")

        ttk.Label(right, text="Orientation (whole cube, before faces are cut)",
                  style="Muted.TLabel").grid(row=1, column=0, columnspan=3, sticky="w", pady=(8, 0))
        slider_row(2, "Yaw °", self.yaw_var, -180, 180)
        slider_row(3, "Pitch °", self.pitch_var, -90, 90)
        slider_row(4, "Roll °", self.roll_var, -180, 180)
        ttk.Separator(right, orient="horizontal").grid(row=5, column=0, columnspan=3, sticky="ew", pady=(8, 4))
        slider_row(6, "Face overlap (FOV °)", self.fov_var, 90, 140,
                   hint="90 = standard cube · >90 widens each face so neighbours overlap "
                        "(better feature matching, larger files).")

        brow = ttk.Frame(right); brow.configure(style="Card.TLabelframe")
        brow.grid(row=8, column=0, columnspan=3, sticky="w", pady=(8, 0))
        self.test_btn = ttk.Button(brow, text="Test render", style="Gold.TButton", command=self._on_test)
        self.test_btn.pack(side="left")
        ttk.Button(brow, text="Reset this camera", command=self._reset_cam).pack(side="left", padx=8)
        ttk.Button(brow, text="Copy to all cameras", command=self._copy_to_all).pack(side="left")
        prow = ttk.Frame(right); prow.configure(style="Card.TLabelframe")
        prow.grid(row=9, column=0, columnspan=3, sticky="w", pady=(4, 0))
        ttk.Label(prow, text="Rig profile:", style="Muted.TLabel").pack(side="left")
        ttk.Button(prow, text="Save…", command=self._save_profile).pack(side="left", padx=4)
        ttk.Button(prow, text="Load…", command=self._load_profile).pack(side="left")
        return frame

    # ---- per-camera logic ------------------------------------------------- #
    def _load_cam(self, slot):
        self._loading = True
        st = self.cam_state[slot]
        self.yaw_var.set(st["yaw"]); self.pitch_var.set(st["pitch"]); self.roll_var.set(st["roll"])
        self.fov_var.set(st.get("face_fov", 90.0))
        for k, v in self.face_vars.items():
            v.set(k in st["faces"])
        self._loading = False
        self._update_labels(); self._draw_rig()

    def _save_controls_to(self, slot):
        try:
            self.cam_state[slot] = {
                "yaw": float(self.yaw_var.get()), "pitch": float(self.pitch_var.get()),
                "roll": float(self.roll_var.get()), "face_fov": float(self.fov_var.get()),
                "faces": {k for k, v in self.face_vars.items() if v.get()}}
        except Exception:
            pass

    def _switch_cam(self):
        self._save_controls_to(self._cur)
        self._cur = self.cam_target.get()
        self._load_cam(self._cur)

    def _on_ctrl_change(self):
        if self._loading:
            return
        self._save_controls_to(self._cur)
        self._update_labels(); self._draw_rig()

    def _update_labels(self):
        if "Yaw" in self._ori_labels:
            pass  # labels are the spinboxes themselves now

    def _reset_cam(self):
        self._loading = True
        self.yaw_var.set(0.0); self.pitch_var.set(0.0); self.roll_var.set(0.0); self.fov_var.set(90.0)
        for v in self.face_vars.values():
            v.set(True)
        self._loading = False
        self._on_ctrl_change()

    def _copy_to_all(self):
        self._save_controls_to(self._cur)
        src = self.cam_state[self._cur]
        for slot in ("top", "mid", "low"):
            self.cam_state[slot] = {"yaw": src["yaw"], "pitch": src["pitch"], "roll": src["roll"],
                                    "face_fov": src.get("face_fov", 90.0), "faces": set(src["faces"])}
        self.file_lbl.config(text="Copied " + self._cur + " settings to all cameras.")

    def _wedge(self, ax, ay, ang, half, length, color):
        p1 = (ax + length * math.cos(ang - half), ay + length * math.sin(ang - half))
        p2 = (ax + length * math.cos(ang + half), ay + length * math.sin(ang + half))
        self.canvas.create_polygon(ax, ay, p1[0], p1[1], p2[0], p2[1], fill=color, stipple="gray25", outline=color, width=2)
        self.canvas.create_line(ax, ay, ax + length * math.cos(ang), ay + length * math.sin(ang), fill=color, width=2)

    def _draw_rig(self):
        if not hasattr(self, "canvas"):
            return
        c = self.canvas; c.delete("all")
        W, H = 300, 270
        view = self.rig_view.get()
        try:
            yaw, pitch, roll = self.yaw_var.get(), self.pitch_var.get(), self.roll_var.get()
        except Exception:
            yaw = pitch = roll = 0.0
        cx, cy = W // 2, H // 2
        sel = self._cur
        view = self.rig_view.get()
        if view == "faces":
            self._draw_facemap(c, W, H)
            return
        c.create_text(W // 2, 12, text=view.upper() + " VIEW", fill=MUTED, font=self.fonts["small"])
        half = math.radians(45)
        slots = ["top", "mid", "low"]; tags = ["T", "M", "L"]
        sel_idx = slots.index(sel) if sel in slots else 1
        if view in ("side", "front"):
            sp, r = 58, 14
            ys = [cy - sp, cy, cy + sp]
            sel_y = ys[sel_idx]
            rigx = cx - 72 if view == "side" else cx
            c.create_line(rigx, ys[0], rigx, ys[2], fill=INK, width=4)
            # the cone/vision is attached to the SELECTED camera - draw a faint marker on it
            for i, yy in enumerate(ys):
                fill = GOLD if i == sel_idx else "#FFFFFF"
                if i == sel_idx:
                    c.create_oval(rigx - r - 4, yy - r - 4, rigx + r + 4, yy + r + 4, outline=GOLD_DK, width=1, dash=(2, 2))
                c.create_oval(rigx - r, yy - r, rigx + r, yy + r, outline=INK, width=2, fill=fill)
                c.create_text(rigx, yy, text=tags[i], fill=INK, font=self.fonts["small"])
            if view == "side":
                self._wedge(rigx + r, sel_y, -math.radians(pitch), half, 140, GOLD)
                c.create_text(W - 8, H - 8, anchor="e",
                              text=tags[sel_idx] + " pitch " + _fmt(pitch) + "°", fill=INK, font=self.fonts["small"])
            else:
                L = 30
                c.create_oval(rigx - L, sel_y - L, rigx + L, sel_y + L, outline=GOLD, width=2, stipple="gray25", fill=GOLD)
                rr = math.radians(roll); dx, dy = math.cos(rr) * (L + 6), math.sin(rr) * (L + 6)
                c.create_line(rigx - dx, sel_y - dy, rigx + dx, sel_y + dy, fill=BLUE, width=3)
                c.create_text(W - 8, H - 8, anchor="e",
                              text=tags[sel_idx] + " roll " + _fmt(roll) + "°", fill=INK, font=self.fonts["small"])
        else:
            for rr in (44, 29, 15):
                c.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, outline=INK if rr == 44 else LINE, width=2 if rr == 44 else 1)
            self._wedge(cx, cy, -math.radians(yaw), half, 115, GOLD)
            c.create_text(W - 8, H - 8, anchor="e",
                          text=tags[sel_idx] + " yaw " + _fmt(yaw) + "°  (plan view)", fill=INK, font=self.fonts["small"])

    # ---- shared ----------------------------------------------------------- #
    def _draw_facemap(self, c, W, H):
        c.create_text(W // 2, 12, text="FACE MAP  ·  " + self._cur.upper(), fill=MUTED, font=self.fonts["small"])
        try:
            fov = float(self.fov_var.get())
        except Exception:
            fov = 90.0
        by_suffix = {fc["suffix"]: fc for fc in FACES}
        cell, gap = 56, 6
        cols = max(cc for _, cc in CROSS.values()) + 1
        rows = max(rr for rr, _ in CROSS.values()) + 1
        gw = cols * cell + (cols - 1) * gap
        gh = rows * cell + (rows - 1) * gap
        ox = (W - gw) // 2
        oy = (H - gh) // 2 + 6
        overlap = max(0.0, fov - 90.0)
        for suffix, (r, cc) in CROSS.items():
            face = by_suffix.get(suffix)
            if not face:
                continue
            x = ox + cc * (cell + gap)
            y = oy + r * (cell + gap)
            on = self.face_vars[face["key"]].get() if face["key"] in self.face_vars else True
            if overlap > 0.5 and on:
                ex = overlap / 90.0 * cell * 0.3
                c.create_rectangle(x - ex, y - ex, x + cell + ex, y + cell + ex, outline=GOLD_DK, dash=(2, 2))
            c.create_rectangle(x, y, x + cell, y + cell, outline=INK, width=2, fill=GOLD if on else "#FFFFFF")
            c.create_text(x + cell / 2, y + cell / 2, text=face["suffix"],
                          fill=INK if on else MUTED, font=self.fonts["small"])
        n_on = sum(1 for v in self.face_vars.values() if v.get())
        cap = str(n_on) + " faces · FOV " + _fmt(fov) + "°"
        if overlap > 0.5:
            cap += " · overlap +" + _fmt(overlap) + "°"
        c.create_text(W // 2, H - 10, text=cap, fill=INK, font=self.fonts["small"])

    def _enable_drop(self, widget, var):
        """Attach OS file drag-and-drop to an entry when tkinterdnd2 is present."""
        if not getattr(self.root, "_hera_dnd", False):
            return
        try:
            from tkinterdnd2 import DND_FILES

            def _dropped(evt, v=var):
                raw = evt.data.strip()
                if raw.startswith("{") and "}" in raw:          # Tk list braces around paths with spaces
                    raw = raw[1:raw.index("}")]
                else:
                    raw = raw.split()[0] if raw else raw
                if raw:
                    v.set(raw)
                return "copy"
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<Drop>>", _dropped)
        except Exception:
            pass

    def _log(self, text):
        self.log.insert("end", text + "\n"); self.log.see("end")

    # ---- reset & rig profiles --------------------------------------------- #
    def _reset_defaults(self):
        msg = ("Reset ALL Hera settings to their defaults?\n\n"
               "This clears frame rate, output choices, interpolation, face size, JPEG/PNG quality, "
               "every camera's orientation / faces / overlap, the output prefix, and the AprilTag and "
               "Capture-planner settings - and erases the saved config file.\n\n"
               "It does NOT delete any frames, faces, tag sheets or plans you've already written to "
               "disk. FFmpeg's location will be re-detected.\n\nProceed?")
        if not messagebox.askyesno(APP_NAME + " - reset to defaults", msg, icon="warning"):
            return
        self.cfg = dict(DEFAULT_CONFIG)
        self.cfg["cams"] = {k: default_cam() for k in ("top", "mid", "low")}
        self.cfg["ffmpeg"] = find_executable("ffmpeg", "")
        self.cfg["ffprobe"] = find_executable("ffprobe", "")
        self.cam_state = {slot: {"yaw": 0.0, "pitch": 0.0, "roll": 0.0,
                                 "faces": set(FACE_KEYS), "face_fov": 90.0}
                          for slot in ("top", "mid", "low")}
        self._cur = "top"
        self._apply_cfg_to_ui()
        save_config(self.cfg)
        self._refresh_ffmpeg_status()
        self.file_lbl.config(text="Settings reset to defaults.")

    def _apply_cfg_to_ui(self):
        self._loading = True
        c = self.cfg

        def setv(attr, val):
            w = getattr(self, attr, None)
            if w is not None:
                try:
                    w.set(val)
                except Exception:
                    pass
        setv("fps_var", str(c["fps"])); setv("want_eq", c["want_equirect"]); setv("want_cube", c["want_cubemap"])
        setv("interp_var", c["interp"]); setv("facesize_var", str(c.get("face_size", "") or ""))
        setv("jpegq_var", c["jpeg_q"]); setv("pnglvl_var", c["png_level"])
        setv("prefix_var", c["prefix"]); setv("outdir_var", c.get("output_dir", ""))
        setv("rig_view", c.get("rig_view", "side")); setv("cam_target", "top")
        setv("write_colmap", c.get("write_colmap", False))
        setv("eq_fmt", c.get("eq_fmt", "JPEG")); setv("cube_fmt", c.get("cube_fmt", "JPEG"))
        try:
            self.fps_scale.set(float(c["fps"]))
        except Exception:
            pass
        for v in getattr(self, "slot_vars", {}).values():
            try:
                v.set("")
            except Exception:
                pass
        self._loading = False
        self._load_cam("top")

    def _save_profile(self):
        self._save_controls_to(self._cur)
        path = filedialog.asksaveasfilename(title="Save rig profile", defaultextension=".json",
                                            initialfile="rig_profile.json",
                                            filetypes=[("Hera rig profile", "*.json")])
        if not path:
            return
        data = {"hera_rig_profile": 1,
                "cams": {slot: {"yaw": self.cam_state[slot]["yaw"], "pitch": self.cam_state[slot]["pitch"],
                                "roll": self.cam_state[slot]["roll"],
                                "face_fov": self.cam_state[slot].get("face_fov", 90.0),
                                "faces": sorted(self.cam_state[slot]["faces"])}
                         for slot in ("top", "mid", "low")}}
        try:
            Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")
            self.file_lbl.config(text="Saved rig profile: " + Path(path).name)
        except Exception as exc:
            messagebox.showerror(APP_NAME, "Could not save profile:\n" + str(exc))

    def _load_profile(self):
        path = filedialog.askopenfilename(title="Load rig profile",
                                          filetypes=[("Hera rig profile", "*.json"), ("All files", "*.*")])
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            cams = data["cams"]
        except Exception as exc:
            messagebox.showerror(APP_NAME, "Not a valid rig profile:\n" + str(exc)); return
        for slot in ("top", "mid", "low"):
            cv = cams.get(slot, {})
            fs = [f for f in cv.get("faces", FACE_KEYS) if f in FACE_KEYS] or FACE_KEYS[:]
            self.cam_state[slot] = {"yaw": float(cv.get("yaw", 0.0)), "pitch": float(cv.get("pitch", 0.0)),
                                    "roll": float(cv.get("roll", 0.0)), "face_fov": float(cv.get("face_fov", 90.0)),
                                    "faces": set(fs)}
        self._load_cam(self._cur)
        self.file_lbl.config(text="Loaded rig profile: " + Path(path).name)

    def _refresh_ffmpeg_status(self):
        ff, fp = self.cfg["ffmpeg"], self.cfg["ffprobe"]
        if ff and fp:
            self.ff_status.config(text="FFmpeg + ffprobe found.", foreground=GREEN_TXT)
        elif ff:
            self.ff_status.config(text="ffmpeg found; ffprobe missing (progress % disabled).", foreground=ORANGE)
        else:
            self.ff_status.config(text="FFmpeg not found on PATH. Click 'Locate' or install it.", foreground=ORANGE)

    def _locate_ffmpeg(self):
        path = filedialog.askopenfilename(title="Select the ffmpeg executable")
        if path:
            self.cfg["ffmpeg"] = path
            guess = Path(path).with_name("ffprobe" + (".exe" if os.name == "nt" else ""))
            self.cfg["ffprobe"] = str(guess) if guess.exists() else find_executable("ffprobe", "")
            save_config(self.cfg); self._refresh_ffmpeg_status()

    def _browse_video(self, var):
        path = filedialog.askopenfilename(title="Select equirectangular 360 video",
                                          filetypes=[("Video files", "*.mp4 *.mov *.mkv *.avi *.m4v"), ("All files", "*.*")])
        if not path:
            return
        if Path(path).suffix.lower() in RAW_360_EXTS:
            if not messagebox.askyesno(APP_NAME, "'" + Path(path).name + "' looks like a RAW Insta360 file.\n\n"
                                       "Hera needs an EQUIRECTANGULAR .mp4/.mov. Use this file anyway?"):
                return
        var.set(path)
        if not self.outdir_var.get():
            self.outdir_var.set(str(Path(path).parent))

    def _browse_outdir(self):
        path = filedialog.askdirectory(title="Select output folder")
        if path:
            self.outdir_var.set(path)

    def _open_output(self):
        if self._last_out and Path(self._last_out).exists():
            open_in_file_manager(self._last_out)

    def _on_fps_slider(self, _val):
        if self._syncing:
            return
        self._syncing = True
        self.fps_var.set(("%.2f" % float(self.fps_scale.get())).rstrip("0").rstrip("."))
        self._syncing = False

    def _on_fps_entry(self, _evt=None):
        if self._syncing:
            return
        ok, _, val = parse_fps(self.fps_var.get())
        if ok and 0.1 <= val <= 10.0:
            self._syncing = True; self.fps_scale.set(val); self._syncing = False

    def _copy_log(self):
        self.root.clipboard_clear(); self.root.clipboard_append(self.log.get("1.0", "end"))

    # ---- gather ----------------------------------------------------------- #
    def _collect(self):
        self._save_controls_to(self._cur)
        if not self.cfg["ffmpeg"]:
            messagebox.showerror(APP_NAME, "FFmpeg not found. Click 'Locate ffmpeg/ffprobe…'."); return None
        loaded = [(disp, key, self.slot_vars[key].get().strip()) for disp, key in SLOTS if self.slot_vars[key].get().strip()]
        if not loaded:
            messagebox.showerror(APP_NAME, "Select at least one input video."); return None
        want_eq, want_cube = self.want_eq.get(), self.want_cube.get()
        if not (want_eq or want_cube):
            messagebox.showerror(APP_NAME, "Enable equirectangular frames and/or cubemap faces."); return None
        ok, fps, _ = parse_fps(self.fps_var.get())
        if not ok:
            messagebox.showerror(APP_NAME, "Frame rate must be positive (e.g. 1, 0.5, 1/3)."); return None
        face_size = self.facesize_var.get().strip()
        if face_size:
            if not face_size.isdigit() or int(face_size) <= 0:
                messagebox.showerror(APP_NAME, "Face size must be a positive whole number, or blank."); return None
            face_size = int(face_size)
        else:
            face_size = None
        outdir = self.outdir_var.get().strip()
        if not outdir:
            messagebox.showerror(APP_NAME, "Choose an output folder."); return None
        inputs = []
        for disp, key, path in loaded:
            if not Path(path).exists():
                messagebox.showerror(APP_NAME, "File not found:\n" + path); return None
            st = self.cam_state[key]
            faces = [fc for fc in FACES if fc["key"] in st["faces"]]
            if want_cube and not faces:
                messagebox.showerror(APP_NAME, disp + " camera has no cubemap faces selected."); return None
            inputs.append({"disp": disp, "slot": key, "path": path, "faces": faces,
                           "yaw": st["yaw"], "pitch": st["pitch"], "roll": st["roll"],
                           "face_fov": st.get("face_fov", 90.0)})
        return {"inputs": inputs, "fps": fps, "want_eq": want_eq, "want_cube": want_cube,
                "interp": self.interp_var.get(), "face_size": face_size, "jpeg_q": self.jpegq_var.get(),
                "png_level": self.pnglvl_var.get(), "outdir": outdir,
                "eq_fmt": self.eq_fmt.get(), "cube_fmt": self.cube_fmt.get(),
                "write_colmap": self.write_colmap.get(),
                "prefix": self.prefix_var.get().strip() or "session"}

    def _persist(self, job):
        cams = {slot: {"yaw": self.cam_state[slot]["yaw"], "pitch": self.cam_state[slot]["pitch"],
                       "roll": self.cam_state[slot]["roll"], "face_fov": self.cam_state[slot].get("face_fov", 90.0),
                       "faces": sorted(self.cam_state[slot]["faces"])}
                for slot in ("top", "mid", "low")}
        self.cfg.update({"fps": job["fps"], "want_equirect": job["want_eq"], "want_cubemap": job["want_cube"],
                         "interp": job["interp"], "face_size": job["face_size"] or "", "jpeg_q": job["jpeg_q"],
                         "png_level": job["png_level"], "output_dir": job["outdir"], "prefix": job["prefix"],
                         "write_colmap": job.get("write_colmap", False),
                         "eq_fmt": job.get("eq_fmt", "JPEG"), "cube_fmt": job.get("cube_fmt", "JPEG"),
                         "rig_view": self.rig_view.get(), "cam_target": self._cur, "cams": cams})
        save_config(self.cfg)

    def _job_dirs(self, job, slot_key):
        base = Path(job["outdir"])
        return (base / (job["prefix"] + "_" + slot_key + "_equirect"),
                base / (job["prefix"] + "_" + slot_key + "_cubemap"))

    def _on_preview(self):
        job = self._collect()
        if not job:
            return
        self._log("=" * 60 + "\nPREVIEW (no files written):")
        for inp in job["inputs"]:
            eqdir, cubedir = self._job_dirs(job, inp["slot"])
            cmd = build_command(self.cfg["ffmpeg"], inp["path"], eqdir, cubedir, job["fps"], job["want_eq"],
                                job["want_cube"], inp["faces"], job["interp"], job["face_size"], job["jpeg_q"],
                                job["png_level"], inp["yaw"], inp["pitch"], inp["roll"], face_fov=inp["face_fov"],
                                eq_fmt=job["eq_fmt"], cube_fmt=job["cube_fmt"])
            self._log("\n# " + inp["disp"] + "\n" + display_command(cmd))
        self._log("=" * 60)

    # ---- test render (all loaded cameras) --------------------------------- #
    def _on_test(self):
        self._save_controls_to(self._cur)
        if not self.cfg["ffmpeg"]:
            messagebox.showerror(APP_NAME, "FFmpeg not found. Click 'Locate ffmpeg/ffprobe…'."); return
        loaded = [(disp, key, self.slot_vars[key].get().strip()) for disp, key in SLOTS if self.slot_vars[key].get().strip()]
        loaded = [(d, k, p) for d, k, p in loaded if Path(p).exists()]
        if not loaded:
            messagebox.showerror(APP_NAME, "Add at least one valid input video to test."); return
        interp = self.interp_var.get()
        jobs = []
        for disp, key, path in loaded:
            st = self.cam_state[key]
            faces = [fc for fc in FACES if fc["key"] in st["faces"]] or FACES
            jobs.append({"disp": disp, "path": path, "faces": faces, "sel": set(st["faces"]),
                         "yaw": st["yaw"], "pitch": st["pitch"], "roll": st["roll"],
                         "face_fov": st.get("face_fov", 90.0),
                         "dir": tempfile.mkdtemp(prefix="hera_test_")})
        self.test_btn.config(state="disabled")
        self.file_lbl.config(text="Rendering test frames for " + str(len(jobs)) + " camera(s)…")
        threading.Thread(target=self._test_worker, args=(jobs, interp), daemon=True).start()

    def _test_worker(self, jobs, interp):
        results = []
        try:
            for j in jobs:
                cmd = build_test_command(self.cfg["ffmpeg"], j["path"], j["dir"], j["faces"], interp,
                                         j["yaw"], j["pitch"], j["roll"], face_fov=j["face_fov"])
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=180, **_no_window_kwargs())
                if r.returncode != 0:
                    self.msgq.put(("test_err", j["disp"] + ": " + (r.stderr.strip()[:200] or "FFmpeg failed.")))
                ori = ("yaw " + _fmt(j["yaw"]) + "°  ·  pitch " + _fmt(j["pitch"]) + "°  ·  roll " + _fmt(j["roll"]) + "°")
                if float(j["face_fov"]) > 90.5:
                    ori += "  ·  FOV " + _fmt(j["face_fov"]) + "°"
                results.append((j["disp"], j["dir"], j["sel"], ori))
            self.msgq.put(("test_ok", results))
        except Exception as exc:
            self.msgq.put(("test_err", str(exc)))
            if results:
                self.msgq.put(("test_ok", results))

    # ---- run -------------------------------------------------------------- #
    def _on_run(self):
        job = self._collect()
        if not job:
            return
        self._persist(job); self._last_out = job["outdir"]
        self.cancelled = False
        self.run_btn.config(state="disabled"); self.cancel_btn.config(state="normal")
        self.open_btn.config(state="disabled"); self.progress["value"] = 0
        self.worker = threading.Thread(target=self._work, args=(job,), daemon=True); self.worker.start()

    def _on_cancel(self):
        self.cancelled = True
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
            except Exception:
                pass
        self.msgq.put(("status", "Cancelling…"))

    def _work(self, job):
        ffmpeg, ffprobe = self.cfg["ffmpeg"], self.cfg["ffprobe"]
        inputs = job["inputs"]; total = len(inputs)
        try:
            for idx, inp in enumerate(inputs):
                if self.cancelled:
                    break
                self.msgq.put(("file", "[" + str(idx + 1) + "/" + str(total) + "] " + inp["disp"] + ": " + Path(inp["path"]).name))
                eqdir, cubedir = self._job_dirs(job, inp["slot"])
                if job["want_eq"]:
                    eqdir.mkdir(parents=True, exist_ok=True)
                if job["want_cube"]:
                    cubedir.mkdir(parents=True, exist_ok=True)
                cmd = build_command(ffmpeg, inp["path"], eqdir, cubedir, job["fps"], job["want_eq"], job["want_cube"],
                                    inp["faces"], job["interp"], job["face_size"], job["jpeg_q"], job["png_level"],
                                    inp["yaw"], inp["pitch"], inp["roll"], face_fov=inp["face_fov"],
                                    eq_fmt=job["eq_fmt"], cube_fmt=job["cube_fmt"])
                self.msgq.put(("log", "\n# " + inp["disp"] + "\n" + display_command(cmd)))
                duration = ffprobe_duration(ffprobe, inp["path"])
                rc = self._run_one(cmd, duration, idx, total)
                if rc != 0 and not self.cancelled:
                    self.msgq.put(("log", "  ! FFmpeg exited with code " + str(rc) + " for " + inp["disp"] + "."))
                    self.msgq.put(("status", "Error on " + inp["disp"] + " (code " + str(rc) + "). See log."))
                elif not self.cancelled:
                    self.msgq.put(("log", "  done: " + inp["disp"]))
                    if job.get("write_colmap") and job["want_cube"] and rc == 0:
                        try:
                            faces_jpg = sorted(Path(cubedir).glob("*.jpg")) or sorted(Path(cubedir).glob("*.png"))
                            if faces_jpg:
                                raw = faces_jpg[0].read_bytes()
                                wh = _jpeg_size(raw) if faces_jpg[0].suffix == ".jpg" else _png_size(raw)
                                if wh:
                                    fov = inp["face_fov"] if float(inp["face_fov"]) > 90.5 else 90.0
                                    (Path(cubedir) / "cameras.txt").write_text(
                                        colmap_cameras_txt(wh[0], wh[1], fov), encoding="utf-8")
                                    self.msgq.put(("log", "  wrote cameras.txt (COLMAP intrinsics, "
                                                   + str(wh[0]) + "x" + str(wh[1]) + " @ " + _fmt(fov) + "°)"))
                        except Exception as exc:
                            self.msgq.put(("log", "  ! cameras.txt: " + str(exc)))
            self.msgq.put(("status", "Cancelled." if self.cancelled else "Finished."))
            if not self.cancelled:
                self.msgq.put(("progress_abs", 1000)); self.msgq.put(("enable_open", None))
        except Exception as exc:
            self.msgq.put(("log", "  ! Unexpected error: " + str(exc))); self.msgq.put(("status", "Error: " + str(exc)))
        finally:
            self.msgq.put(("done", None))

    def _run_one(self, cmd, duration, idx, total):
        err_file = tempfile.TemporaryFile(mode="w+")
        try:
            self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=err_file, text=True, bufsize=1, **_no_window_kwargs())
        except Exception as exc:
            self.msgq.put(("log", "  ! Could not launch FFmpeg: " + str(exc))); err_file.close(); return -1
        for line in self.proc.stdout:
            line = line.strip()
            if line.startswith("out_time_ms=") and duration:
                try:
                    secs = int(line.split("=", 1)[1]) / 1_000_000.0
                    frac = max(0.0, min(1.0, secs / duration))
                    self.msgq.put(("progress_abs", int(((idx + frac) / total) * 1000)))
                except Exception:
                    pass
            elif line.startswith("frame=") and not duration:
                self.msgq.put(("status", "frames written: " + line.split("=", 1)[1]))
        self.proc.wait(); rc = self.proc.returncode
        if rc != 0:
            err_file.seek(0); msg = err_file.read().strip()
            if msg:
                self.msgq.put(("log", "  --- ffmpeg stderr ---\n  " + msg.replace("\n", "\n  ")))
        err_file.close(); self.proc = None
        if not self.cancelled:
            self.msgq.put(("progress_abs", int(((idx + 1) / total) * 1000)))
        return rc

    def _drain_queue(self):
        try:
            while True:
                kind, payload = self.msgq.get_nowait()
                if kind == "log":
                    self._log(payload)
                elif kind in ("status", "file"):
                    self.file_lbl.config(text=payload)
                elif kind == "progress_abs":
                    self.progress["value"] = payload
                elif kind == "enable_open":
                    self.open_btn.config(state="normal")
                elif kind == "test_ok":
                    self.test_btn.config(state="normal")
                    self.file_lbl.config(text="Test render ready.")
                    PreviewWindow(self, payload)
                elif kind == "test_err":
                    self.test_btn.config(state="normal")
                    self._log("  ! Test render: " + str(payload))
                elif kind == "done":
                    self.run_btn.config(state="normal"); self.cancel_btn.config(state="disabled")
                    if not self.cancelled:
                        self._log("\nFrames written. Tip: open Workflow Tips (top bar) ▸ After Hera for "
                                  "RealityScan / COLMAP / 3DGS settings (features, tie points, scale).")
        except queue.Empty:
            pass
        self.root.after(100, self._drain_queue)

    def _on_close(self):
        if self.proc and self.proc.poll() is None:
            if not messagebox.askyesno(APP_NAME, "A job is running. Quit anyway?"):
                return
            self.cancelled = True
            try:
                self.proc.terminate()
            except Exception:
                pass
        self.root.destroy()


def main():
    # OS drag-and-drop needs the optional tkinterdnd2 package (stdlib Tkinter
    # has no cross-platform file-drop support). If it's installed we use it;
    # otherwise Hera runs identically with the Browse buttons.
    root = None
    try:
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
        root._hera_dnd = True
    except Exception:
        root = tk.Tk()
        root._hera_dnd = False
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
