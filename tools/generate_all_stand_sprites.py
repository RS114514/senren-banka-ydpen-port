#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generate_all_stand_sprites.py —— 批量生成 7 位角色的全身高清立绘（780x440画布，专供立绘鉴赏模式使用）
"""
import os, sys, json, subprocess, shutil, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(HERE)
OUT_DIR = os.path.join(PROJECT_DIR, "assets", "stand")
os.makedirs(OUT_DIR, exist_ok=True)

if "/opt/homebrew/bin" not in os.environ.get("PATH", ""):
    os.environ["PATH"] = os.environ.get("PATH", "") + ":/opt/homebrew/bin:/usr/local/bin"

FG_ROOT = "/Volumes/500GB/千恋万花_移植资源库/assets_ready/characters/fgimage"
DEVICE_DIR = "/userdisk/SenrenBanka/stand"
SERIAL = os.environ.get("PEN_SERIAL", "9DA2200007506350")

CHARACTER_CONFIGS = [
    {
        "name": "芳乃",
        "aliases": ["芳乃"],
        "folder": "１芳乃",
        "prefix": "芳乃a_0_",
        "info": "芳乃a_info.txt",
        "txt0": "芳乃a_0.txt",
        "dresses": {
            "舞服": ["舞巫女服", "髪かぶせ"],
            "巫女服": ["巫女服", "髪かぶせ"],
            "私服": ["私服", "髪かぶせ"],
            "制服": ["制服", "髪かぶせ"],
        },
        "crop": {"cropX": 300.0, "cropY": 700.0, "cropW": 1000.0, "cropH": 1720.0},
        "extra_faces": []
    },
    {
        "name": "茉子",
        "aliases": ["茉子"],
        "folder": "２茉子",
        "prefix": "茉子a_0_",
        "info": "茉子a_info.txt",
        "txt0": "茉子a_0.txt",
        "dresses": {
            "私服": ["私服1"],
            "忍者": ["忍者服", "忍者服用マフラー"],
            "制服": ["制服"],
            "洋装": ["私服2"],
        },
        "crop": {"cropX": 380.0, "cropY": 680.0, "cropW": 940.0, "cropH": 1740.0},
        "extra_faces": []
    },
    {
        "name": "ムラサメ",
        "aliases": ["ムラサメ", "丛雨"],
        "folder": "３ムラサメ",
        "prefix": "ムラサメa_0_",
        "info": "ムラサメa_info.txt",
        "txt0": "ムラサメa_0.txt",
        "dresses": {
            "私服": ["刀服", "髪かぶせ(刀服用)"],
            "洋装": ["私服", "髪かぶせ"],
            "制服": ["制服", "髪かぶせ"],
            "寝間着": ["寝間着", "髪かぶせ"],
        },
        "crop": {"cropX": 500.0, "cropY": 820.0, "cropW": 880.0, "cropH": 1560.0},
        "extra_faces": []
    },
    {
        "name": "レナ",
        "aliases": ["レナ", "蕾娜"],
        "folder": "４レナ",
        "prefix": "レナa_0_",
        "info": "レナa_info.txt",
        "txt0": "レナa_0.txt",
        "dresses": {
            "私服": ["私服", "前髪かぶせ"],
            "和装": ["現地服", "前髪かぶせ"],
            "制服": ["制服", "前髪かぶせ"],
            "仲居服": ["仲居服", "前髪かぶせ"],
        },
        "crop": {"cropX": 550.0, "cropY": 650.0, "cropW": 860.0, "cropH": 1760.0},
        "extra_faces": []
    },
    {
        "name": "小春",
        "aliases": ["小春"],
        "folder": "５小春",
        "prefix": "小春a_0_",
        "info": "小春a_info.txt",
        "txt0": "小春a_0.txt",
        "dresses": {
            "私服": ["私服"],
            "仕事着": ["店服"],
            "制服": ["制服"],
        },
        "crop": {"cropX": 520.0, "cropY": 700.0, "cropW": 660.0, "cropH": 1680.0},
        "extra_faces": []
    },
    {
        "name": "芦花",
        "aliases": ["芦花"],
        "folder": "６芦花",
        "prefix": "芦花a_0_",
        "info": "芦花a_info.txt",
        "txt0": "芦花a_0.txt",
        "dresses": {
            "仕事着": ["甘味処服", "髪かぶせ"],
            "私服": ["私服", "髪かぶせ"],
        },
        "crop": {"cropX": 540.0, "cropY": 670.0, "cropW": 720.0, "cropH": 1760.0},
        "extra_faces": []
    },
    {
        "name": "玄十郎",
        "aliases": ["玄十郎"],
        "folder": "９玄十郎",
        "prefix": "玄十郎a_0_",
        "info": "玄十郎a_info.txt",
        "txt0": "玄十郎a_0.txt",
        "dresses": {
            "剣道": ["剣道着", "髪かぶせ"],
            "私服": ["私服", "髪かぶせ"],
        },
        "crop": {"cropX": 520.0, "cropY": 480.0, "cropW": 760.0, "cropH": 1950.0},
        "extra_faces": []
    }
]

def load_character_tables(cfg):
    info_path = os.path.join(FG_ROOT, cfg["info"])
    if not os.path.exists(info_path):
        info_path = os.path.join(FG_ROOT, cfg["folder"], cfg["info"])

    txt0_path = os.path.join(FG_ROOT, cfg["folder"], cfg["txt0"])
    char_folder = os.path.join(FG_ROOT, cfg["folder"])

    with open(info_path, "r", encoding="utf-16", errors="ignore") as f:
        info_lines = [line.strip() for line in f if line.strip()]

    with open(txt0_path, "r", encoding="utf-16", errors="ignore") as f:
        txt0_lines = [line.strip() for line in f if line.strip()]

    layer_by_name = {}
    for line_idx, l in enumerate(txt0_lines):
        p = l.split("\t")
        if len(p) >= 10:
            name = p[1]
            try:
                lid = int(p[9])
                w = int(p[4])
                h = int(p[5])
                tlg_file = os.path.join(char_folder, f"{cfg['prefix']}{lid}.tlg")
                if w > 0 and h > 0 and os.path.exists(tlg_file):
                    if name not in layer_by_name:
                        layer_by_name[name] = {
                            "id": lid,
                            "file": tlg_file,
                            "x": int(p[2]),
                            "y": int(p[3]),
                            "w": w,
                            "h": h,
                            "name": name,
                            "line": line_idx
                        }
            except ValueError:
                pass

    faces_raw = {}
    for l in info_lines:
        p = l.split("\t")
        if len(p) >= 4 and p[0] == "face":
            code = p[1]
            raw_path = p[3]
            base_name = raw_path.split("/")[-1]
            faces_raw.setdefault(code, []).append((raw_path, base_name))

    resolved_faces = {}
    for code, items in faces_raw.items():
        base_num_str = code.rstrip("h").rstrip("m").rstrip("n").rstrip("d").rstrip("r")
        is_standard = False
        if base_num_str.isdigit() and 1 <= int(base_num_str) <= 20:
            if not any(code.endswith(sfx) for sfx in ["m", "n", "d", "r"]):
                is_standard = True
        if code in cfg.get("extra_faces", []):
            is_standard = True

        if not is_standard:
            continue

        layers = []
        for raw, bname in items:
            if bname in layer_by_name:
                layers.append(layer_by_name[bname])
            elif raw in layer_by_name:
                layers.append(layer_by_name[raw])

        if layers:
            resolved_faces[code] = layers

    return layer_by_name, resolved_faces

def build_specs():
    specs = []
    alias_map = {}

    for cfg in CHARACTER_CONFIGS:
        char_name = cfg["name"]
        aliases = cfg["aliases"]
        layer_by_name, resolved_faces = load_character_tables(cfg)
        crop = cfg["crop"]

        print(f"[{char_name}] 表情解析成功: {len(resolved_faces)} 种差分, 服装: {list(cfg['dresses'].keys())}")

        for dress_name, dress_layer_names in cfg["dresses"].items():
            dress_layers = [layer_by_name[l_name] for l_name in dress_layer_names if l_name in layer_by_name]

            for face_code, face_layers in resolved_faces.items():
                all_layers_map = {}
                for l in dress_layers:
                    all_layers_map[l["id"]] = l
                for l in face_layers:
                    all_layers_map[l["id"]] = l

                sorted_layers = sorted(all_layers_map.values(), key=lambda l: l["line"], reverse=True)

                primary_filename = f"{char_name}_{dress_name}_{face_code}.png"
                primary_out = os.path.join(OUT_DIR, primary_filename)

                spec = {
                    "out": primary_out,
                    "cropX": crop["cropX"],
                    "cropY": crop["cropY"],
                    "cropW": crop["cropW"],
                    "cropH": crop["cropH"],
                    "layers": [
                        {
                            "file": l["file"],
                            "x": l["x"],
                            "y": l["y"],
                            "w": l["w"],
                            "h": l["h"]
                        } for l in sorted_layers
                    ]
                }
                specs.append(spec)

                other_aliases = [a for a in aliases if a != char_name]
                if other_aliases:
                    alias_files = []
                    for a in other_aliases:
                        alias_filename = f"{a}_{dress_name}_{face_code}.png"
                        alias_files.append(os.path.join(OUT_DIR, alias_filename))
                    alias_map[primary_out] = alias_files

    return specs, alias_map

def main():
    parser = argparse.ArgumentParser(description="千恋万花全身立绘全差分批量合成与导出（专供立绘鉴赏模式）")
    parser.add_argument("--push", action="store_true", default=True, help="是否使用 adb 推送到设备")
    parser.add_argument("--no-push", dest="push", action="store_false", help="仅本地生成，不推送到设备")
    args = parser.parse_args()

    print("=== 开始构建角色全身立绘规格表 ===")
    specs, alias_map = build_specs()
    print(f"总计规划生成全身主立绘: {len(specs)} 张")

    spec_file = "/tmp/stand_full_specs.json"
    with open(spec_file, "w", encoding="utf-8") as f:
        json.dump(specs, f)

    bin_path = os.path.join(HERE, "composite_bin")
    print(f"调用 Swift 多核合成引擎执行图层合成与 780x440 全身画布输出...")
    ret = subprocess.run([bin_path, spec_file], capture_output=True, text=True)
    if ret.returncode != 0:
        print("Swift 合成引擎执行出错:", ret.stderr)
        sys.exit(1)
    print(ret.stdout.strip())

    alias_count = 0
    for primary_out, alias_paths in alias_map.items():
        if os.path.exists(primary_out):
            for dst in alias_paths:
                shutil.copyfile(primary_out, dst)
                alias_count += 1
    print(f"完成别名文件同步: {alias_count} 张（丛雨/蕾娜中日双向名称映射）")

    total_local = len([f for f in os.listdir(OUT_DIR) if f.endswith(".png")])
    print(f"本地全身立绘输出完成: {OUT_DIR}，共计 {total_local} 张 PNG 文件")

    if args.push:
        print(f"\n=== 开始通过 ADB 推送全身立绘至词典笔设备 ({SERIAL}) ===")
        subprocess.run(["adb", "-s", SERIAL, "shell", f"mkdir -p {DEVICE_DIR}"], check=True)
        print(f"批量推送本地 {OUT_DIR}/ 至设备 {DEVICE_DIR}/ ...")
        batch_push = subprocess.run(["adb", "-s", SERIAL, "push", OUT_DIR + "/.", DEVICE_DIR + "/"], capture_output=True, text=True)
        if batch_push.returncode != 0:
            print("ADB 推送失败:", batch_push.stderr)
            sys.exit(1)
        print("ADB 批量推送完成！")

        dev_check = subprocess.run(["adb", "-s", SERIAL, "shell", f"ls -1 {DEVICE_DIR} | wc -l"], capture_output=True, text=True)
        dev_count = dev_check.stdout.strip()
        print(f"设备端 {DEVICE_DIR} 当前全身立绘文件总数: {dev_count}")

if __name__ == "__main__":
    main()
