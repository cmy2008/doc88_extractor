#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取 verify_img 校验码图片 -> 识别缺口位置 -> 输出滑块轨迹参数
================================================================

一条命令完成三件事：
  1. 请求 verify_img，拿到校验码图片（也可用 --image 指定本地图片）；
  2. 用 缺口.png + 缺口位置.png 做水平模板匹配，得到 gap_x / gap_y；
  3. 生成滑块轨迹，输出 positions、data、endX、startTime、endTime 等参数。

输出：
  - 默认把完整结果以 JSON 打到 stdout；
  - 状态信息打到 stderr，方便重定向；
  - --json 可额外写入文件。

用法：
  # 在线获取 + 识别 + 输出轨迹
  python captcha_pipeline.py --pw 278 --st 0

  # 同时获取 captcha_init 的 key / serverTime
  python captcha_pipeline.py --pw 278 --st 0 --with-init

  # 用本地图片调试，不走网络
  python captcha_pipeline.py --image verify_img_samples\\xxx.png

  # 线性轨迹 + 固定随机种子
  python captcha_pipeline.py --mode linear --seed 7

  # 手动指定缺口位置
  python captcha_pipeline.py --image xxx.png --gap-x 185 --gap-y 32

  # 保存结果到文件
  python captcha_pipeline.py --json trajectory.json

  # 不保存下载的图片
  python captcha_pipeline.py --no-save

依赖：
  - Pillow（图片读取/像素访问）
  - Python 标准库（urllib / json / random 等）
"""

from __future__ import annotations

import argparse
import http.cookiejar
import io
import json
import random
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from PIL import Image

# ---------------------------------------------------------------------------
# 默认配置
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = "缺口.png"
DEFAULT_POS_IMAGE = "缺口位置.png"
DEFAULT_API = "https://www.doc88.com/api.php"
DEFAULT_INIT = "https://www.doc88.com/member.php?act=captcha_init"
DEFAULT_REFERER = "https://www.doc88.com/"
DEFAULT_PW = 278
DEFAULT_ST = 0
DEFAULT_BUTTON_WIDTH = 44

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


# ---------------------------------------------------------------------------
# 基础工具
# ---------------------------------------------------------------------------

def eprint(*args, **kwargs) -> None:
    print(*args, file=sys.stderr, **kwargs)


def resolve(path_str: str, base: Path) -> Path:
    p = Path(path_str)
    if not p.is_absolute():
        p = base / p
    return p


@dataclass
class Gap:
    x: int
    y: int
    w: int
    h: int
    score: float


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

def make_opener() -> urllib.request.OpenerDirector:
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar)
    )


def http_get(opener: urllib.request.OpenerDirector, url: str,
             headers: Dict[str, str], timeout: float) -> Tuple[bytes, str, str]:
    req = urllib.request.Request(url, headers=headers)
    with opener.open(req, timeout=timeout) as resp:
        return resp.read(), resp.headers.get("Content-Type", ""), resp.geturl()


def fetch_init(opener: urllib.request.OpenerDirector, url: str,
               headers: Dict[str, str], timeout: float) -> Dict[str, str]:
    data, ctype, final_url = http_get(opener, url, headers, timeout)
    try:
        obj = json.loads(data.decode("utf-8"))
    except Exception as exc:
        raise RuntimeError(
            f"captcha_init 返回非 JSON（{ctype}）: {data[:120]!r}"
        ) from exc

    raw = str(obj.get("data", "")).strip()
    if raw in ("0", "2"):
        return {
            "status": raw,
            "server_time": "",
            "key": "",
            "raw": raw,
            "url": final_url,
        }
    # 格式：00 + 13 位 serverTime + key。
    # 线上 key 目前可能是 15 或 16 位，前端用的是 substring(15, 31)，
    # 所以这里同样取 raw[15:31]，不要强制要求总长度一定是 31。
    if len(raw) < 28:
        raise RuntimeError(f"captcha_init data 长度异常: {raw!r}")

    server_time = raw[2:15]
    key = raw[15:31]
    if not server_time.isdigit():
        raise RuntimeError(f"captcha_init serverTime 非数字: {raw!r}")
    if not key:
        raise RuntimeError(f"captcha_init key 为空: {raw!r}")

    return {
        "status": "1",
        "server_time": server_time,
        "key": key,
        "raw": raw,
        "url": final_url,
    }


def fetch_image(opener: urllib.request.OpenerDirector, api_url: str,
                v: float, pw: int, st: int, fmt: str,
                headers: Dict[str, str], timeout: float
                ) -> Tuple[bytes, str, str]:
    params = {"act": "verify_img", "v": v, "pw": pw, "st": st}
    if fmt and fmt != "png":
        params["fmt"] = fmt
    url = api_url + "?" + urllib.parse.urlencode(params)

    data, ctype, final_url = http_get(opener, url, headers, timeout)
    if data.startswith(b"\x89PNG"):
        ext = ".png"
    elif data.startswith(b"\xff\xd8"):
        ext = ".jpg"
    else:
        raise RuntimeError(
            f"verify_img 返回的不是图片（{ctype}）: {data[:120]!r}"
        )
    return data, ext, final_url


def save_image(data: bytes, ext: str, out_dir: Path,
               v: float, pw: int, st: int) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    ms = int(time.time() * 1000) % 1000
    name = f"verify_img_{ts}_{ms:03d}_pw{pw}_st{st}_{v:.8f}{ext}"
    path = out_dir / name
    path.write_bytes(data)
    return path


# ---------------------------------------------------------------------------
# 缺口识别
# ---------------------------------------------------------------------------

def load_template(template_path: Path, pos_path: Path,
                  gap_y_override: Optional[int]) -> Tuple[Image.Image, int, int, int]:
    tpl = Image.open(template_path).convert("RGBA")
    tw, th = tpl.size

    y0 = gap_y_override if gap_y_override is not None else 32
    if pos_path.is_file():
        pos = Image.open(pos_path).convert("RGBA")
        alpha = pos.getchannel("A")
        bbox = alpha.getbbox()
        if bbox:
            x0, yb, x1, y1 = bbox
            if gap_y_override is None:
                y0 = yb
            if (x1 - x0, y1 - yb) != (tw, th):
                eprint(
                    f"[warn] 位置图 bbox {x1 - x0}x{y1 - yb} "
                    f"与模板 {tw}x{th} 不一致"
                )
    return tpl, tw, th, y0


def build_template_points(tpl: Image.Image
                          ) -> List[Tuple[int, int, int, int, int]]:
    tw, th = tpl.size
    b = tpl.tobytes()
    points: List[Tuple[int, int, int, int, int]] = []

    for dy in range(th):
        for dx in range(tw):
            i = (dy * tw + dx) * 4
            if b[i + 3] >= 128:
                points.append((dx, dy, b[i], b[i + 1], b[i + 2]))

    if not points:
        for dy in range(th):
            for dx in range(tw):
                i = (dy * tw + dx) * 4
                points.append((dx, dy, b[i], b[i + 1], b[i + 2]))
    return points


def match_template(target: Image.Image,
                   points: Sequence[Tuple[int, int, int, int, int]],
                   tw: int, th: int, y0: int) -> Tuple[int, float]:
    width, height = target.size
    if y0 < 0 or y0 + th > height:
        raise ValueError(f"gap_y={y0} 超出图片范围 0..{height - th}")

    tb = target.tobytes()
    best_x = -1
    best_score = float("inf")

    for x in range(0, width - tw + 1):
        score = 0
        for dx, dy, tr, tg, tbb in points:
            i = ((y0 + dy) * width + (x + dx)) * 3
            score += abs(tb[i] - tr) + abs(tb[i + 1] - tg) + abs(tb[i + 2] - tbb)
            if score >= best_score:
                break
        else:
            best_score = float(score)
            best_x = x

    if best_x < 0:
        raise RuntimeError("模板匹配失败")

    mean_abs = best_score / (len(points) * 3) if points else float("inf")
    return best_x, mean_abs


def detect_gap(image: Image.Image, template_path: Path, pos_path: Path,
               gap_x_override: Optional[int],
               gap_y_override: Optional[int]) -> Gap:
    tpl, tw, th, y0 = load_template(template_path, pos_path, gap_y_override)

    if gap_x_override is not None:
        max_x = image.width - tw
        if not (0 <= gap_x_override <= max_x):
            raise ValueError(f"gap_x={gap_x_override} 超出范围 0..{max_x}")
        return Gap(gap_x_override, y0, tw, th, 0.0)

    points = build_template_points(tpl)
    x, score = match_template(image, points, tw, th, y0)
    return Gap(x, y0, tw, th, score)


# ---------------------------------------------------------------------------
# 轨迹
# ---------------------------------------------------------------------------

def make_positions(end_x: int, args: argparse.Namespace,
                   rng: random.Random) -> List[float]:
    duration = rng.randint(args.min_duration, args.max_duration)
    n = max(16, int(round(duration / args.frame_ms)))

    if args.mode == "linear":
        pts: List[float] = []
        for i in range(n):
            t = i / (n - 1)
            x = end_x * t
            if args.jitter > 0:
                x += rng.uniform(-args.jitter, args.jitter) * (1 - t * 0.5)
            pts.append(x)
    else:
        pause_start = rng.uniform(0.45, 0.65)
        pause_end = min(0.88, pause_start + rng.uniform(0.08, 0.18))
        pause_val = 1 - (1 - pause_start) ** 1.8

        pts = []
        for i in range(n):
            t = i / (n - 1)
            if t <= pause_start:
                p = 1 - (1 - t) ** 1.8
            elif t < pause_end:
                p = pause_val
            else:
                u = (t - pause_end) / (1 - pause_end)
                p = pause_val + (1 - pause_val) * (1 - (1 - u) ** 2.2)

            x = end_x * p
            if args.jitter > 0:
                x += rng.uniform(-args.jitter, args.jitter) * (1 - p)
            pts.append(x)

        if args.pause_frames > 0:
            idx = int(len(pts) * 0.6)
            pts = pts[:idx] + [pts[idx]] * args.pause_frames + pts[idx:]

    pts = [max(0.0, min(float(end_x), x)) for x in pts]
    for i in range(1, len(pts)):
        pts[i] = max(pts[i], pts[i - 1])
    pts[-1] = float(end_x)
    return pts


def make_trace(positions: Sequence[float], track_max: int,
               frame_ms: int, start_time: int) -> str:
    buckets = ["0-0-0"] * 100
    for i, x in enumerate(positions):
        percent = int(round(x / track_max * 100)) if track_max > 0 else 0
        percent = max(0, min(99, percent))
        timestamp = start_time + i * frame_ms
        buckets[percent] = f"{percent}-{int(round(x))}-{timestamp}"
    return ",".join(buckets)


# ---------------------------------------------------------------------------
# 结果
# ---------------------------------------------------------------------------

def build_result(args: argparse.Namespace, image_info: Dict[str, object],
                 gap: Gap, positions: Sequence[float], data: str,
                 start_time: int, end_time: int,
                 init: Optional[Dict[str, str]],
                 warnings: Sequence[str]) -> Dict[str, object]:
    track_max = max(1, int(image_info["width"]) - args.button_width)
    end_x = int(round(positions[-1]))

    payload: Dict[str, str] = {
        "startX": "0",
        "startTime": str(start_time),
        "endX": str(end_x),
        "endTime": str(end_time),
        "data": data,
    }
    if init is not None:
        payload["key"] = init.get("key", "")
        payload["serverTime"] = init.get("server_time", "")

    return {
        "ok": True,
        "image": image_info,
        "gap": {
            "x": gap.x,
            "y": gap.y,
            "w": gap.w,
            "h": gap.h,
            "score": round(gap.score, 4),
        },
        "slider": {
            "track_width": image_info["width"],
            "button_width": args.button_width,
            "max_x": track_max,
        },
        "trajectory": {
            "mode": args.mode,
            "start_x": 0,
            "end_x": end_x,
            "start_time": start_time,
            "end_time": end_time,
            "duration_ms": end_time - start_time,
            "frames": len(positions),
            "frame_ms": args.frame_ms,
            "positions": [int(round(x)) for x in positions],
            "data": data,
        },
        "payload": payload,
        "init": init,
        "warnings": list(warnings),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="获取 verify_img 图片 -> 识别缺口 -> 输出滑块轨迹参数",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  python captcha_pipeline.py --pw 278 --st 0\n"
            "  python captcha_pipeline.py --pw 278 --st 0 --with-init\n"
            "  python captcha_pipeline.py --image verify_img_samples\\xxx.png\n"
            "  python captcha_pipeline.py --mode linear --seed 7 --json trajectory.json\n"
            "  python captcha_pipeline.py --image xxx.png --gap-x 185 --gap-y 32\n"
        ),
    )

    # 网络
    p.add_argument("--api", default=DEFAULT_API,
                   help=f"verify_img 接口，默认 {DEFAULT_API}")
    p.add_argument("--init-url", default=DEFAULT_INIT,
                   help=f"captcha_init 接口，默认 {DEFAULT_INIT}")
    p.add_argument("--v", type=float, default=None,
                   help="verify_img 的 v 参数，默认随机")
    p.add_argument("--pw", type=int, default=DEFAULT_PW,
                   help=f"轨道宽度，默认 {DEFAULT_PW}")
    p.add_argument("--st", type=int, choices=(0, 1), default=DEFAULT_ST,
                   help=f"st 参数，默认 {DEFAULT_ST}")
    p.add_argument("--fmt", choices=("png", "jpeg"), default="png",
                   help="图片格式，默认 png")
    p.add_argument("--cookie", default=None,
                   help="可选 Cookie 头")
    p.add_argument("--referer", default=DEFAULT_REFERER,
                   help=f"Referer，默认 {DEFAULT_REFERER}")
    p.add_argument("--timeout", type=float, default=15.0,
                   help="HTTP 超时秒数，默认 15")
    p.add_argument("--with-init", action="store_true",
                   help="额外请求 captcha_init，输出 key / serverTime")
    p.add_argument("--image", default=None,
                   help="本地图片路径；指定后不再下载 verify_img")
    p.add_argument("--out-dir", default="captcha_images",
                   help="下载图片保存目录，默认 captcha_images")
    p.add_argument("--no-save", action="store_true",
                   help="不保存下载的图片")

    # 缺口识别
    p.add_argument("--template", default=DEFAULT_TEMPLATE,
                   help=f"缺口模板，默认 {DEFAULT_TEMPLATE}")
    p.add_argument("--pos-image", default=DEFAULT_POS_IMAGE,
                   help=f"缺口位置图，默认 {DEFAULT_POS_IMAGE}")
    p.add_argument("--gap-x", type=int, default=None,
                   help="手动指定 gap_x，跳过模板匹配")
    p.add_argument("--gap-y", type=int, default=None,
                   help="手动指定 gap_y；默认从位置图读取")

    # 轨迹
    p.add_argument("--mode", choices=("human", "linear"), default="human",
                   help="轨迹模式，默认 human")
    p.add_argument("--min-duration", type=int, default=900,
                   help="拖动时长下限 ms，默认 900")
    p.add_argument("--max-duration", type=int, default=1500,
                   help="拖动时长上限 ms，默认 1500")
    p.add_argument("--frame-ms", type=int, default=50,
                   help="每帧时长 ms，默认 50")
    p.add_argument("--pause-frames", type=int, default=2,
                   help="human 模式中间停顿帧数，默认 2")
    p.add_argument("--jitter", type=float, default=1.5,
                   help="水平抖动像素，默认 1.5")
    p.add_argument("--seed", type=int, default=None,
                   help="随机种子")
    p.add_argument("--button-width", type=int, default=DEFAULT_BUTTON_WIDTH,
                   help=f"滑块按钮宽度，默认 {DEFAULT_BUTTON_WIDTH}")

    # 输出
    p.add_argument("--json", default=None,
                   help="额外写入 JSON 文件")
    p.add_argument("--quiet", action="store_true",
                   help="不输出 stderr 状态信息")
    return p


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.frame_ms < 20:
        args.frame_ms = 20
    if args.min_duration < 500:
        args.min_duration = 500
    if args.max_duration < args.min_duration:
        args.max_duration = args.min_duration

    template_path = resolve(args.template, SCRIPT_DIR)
    pos_path = resolve(args.pos_image, SCRIPT_DIR)
    if not template_path.is_file():
        raise FileNotFoundError(f"模板不存在: {template_path}")

    headers = dict(DEFAULT_HEADERS)
    headers["Referer"] = args.referer
    if args.cookie:
        headers["Cookie"] = args.cookie

    opener = make_opener()
    init: Optional[Dict[str, str]] = None
    warnings: List[str] = []

    if args.with_init:
        try:
            init = fetch_init(opener, args.init_url, headers, args.timeout)
            if not args.quiet:
                eprint(
                    f"[init] status={init['status']} "
                    f"key={init['key']} serverTime={init['server_time']}"
                )
        except Exception as exc:
            warnings.append(f"captcha_init failed: {exc}")
            eprint(f"[warn] captcha_init 失败: {exc}")

    # 获取图片
    if args.image:
        image_path = Path(args.image)
        if not image_path.is_absolute():
            image_path = Path.cwd() / image_path
        if not image_path.is_file():
            raise FileNotFoundError(f"图片不存在: {image_path}")
        data = image_path.read_bytes()
        image_url = None
        image_info_path: Optional[Path] = image_path
    else:
        v = args.v if args.v is not None else random.random()
        data, ext, image_url = fetch_image(
            opener, args.api, v, args.pw, args.st, args.fmt,
            headers, args.timeout,
        )
        if not args.quiet:
            eprint(f"[fetch] {image_url}  {len(data)} bytes")

        if args.no_save:
            image_info_path = None
        else:
            out_dir = resolve(args.out_dir, Path.cwd())
            image_info_path = save_image(data, ext, out_dir, v, args.pw, args.st)
            if not args.quiet:
                eprint(f"[save] {image_info_path}")

    try:
        image = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception as exc:
        raise RuntimeError(f"图片解码失败: {exc}") from exc

    if not args.quiet:
        eprint(f"[image] {image.width}x{image.height}")

    # 识别缺口
    gap = detect_gap(
        image, template_path, pos_path,
        gap_x_override=args.gap_x,
        gap_y_override=args.gap_y,
    )
    if not args.quiet:
        eprint(
            f"[gap] x={gap.x} y={gap.y} w={gap.w} h={gap.h} "
            f"score={gap.score:.4f}"
        )

    track_max = max(1, image.width - args.button_width)
    end_x = min(gap.x, track_max)

    if gap.x > track_max:
        warnings.append(
            f"gap_x={gap.x} 超过滑块最大位置 {track_max}，endX 已截断"
        )
    if end_x < 10:
        warnings.append(
            f"endX={end_x} < 10，前端可能因位移过小直接拒绝"
        )
    if gap.score > 5.0:
        warnings.append(
            f"模板匹配分数 {gap.score:.2f} > 5，缺口位置可能不准"
        )

    # 生成轨迹
    rng = random.Random(args.seed)
    positions = make_positions(end_x, args, rng)
    start_time = int(time.time() * 1000)
    end_time = start_time + len(positions) * args.frame_ms
    data_str = make_trace(positions, track_max, args.frame_ms, start_time)

    if not args.quiet:
        eprint(
            f"[traj] mode={args.mode} frames={len(positions)} "
            f"endX={end_x} duration={end_time - start_time}ms"
        )
        for w in warnings:
            eprint(f"[warn] {w}")

    image_info: Dict[str, object] = {
        "path": str(image_info_path) if image_info_path else None,
        "url": image_url,
        "width": image.width,
        "height": image.height,
        "bytes": len(data),
    }

    result = build_result(
        args, image_info, gap, positions, data_str,
        start_time, end_time, init, warnings,
    )

    text = json.dumps(result, ensure_ascii=False, indent=2)

    if args.json:
        out_path = Path(args.json)
        if not out_path.is_absolute():
            out_path = Path.cwd() / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        if not args.quiet:
            eprint(f"[json] {out_path}")

    print(text)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        eprint(f"[error] {exc}")
        sys.exit(1)
