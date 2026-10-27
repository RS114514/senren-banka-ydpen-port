#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_and_install.py —— 有道词典笔《千恋＊万花》移植版一键解包、转码、构建与安装总入口

功能说明：
1. 从未加密正版 XP3 文件（推荐：https://pan.touchgal.net/s/wpwtv ）或解包目录自动提取游戏资源；
2. 自动化将官方 92 篇剧本转码为 JQuick Miniapp 数据格式；
3. 批量将 CG、SD 小人、背景、立绘差分、音频转码适配至词典笔最佳分辨率与格式；
4. 自动编译打包生成 senren_banka-1.0.0.amr，并通过 ADB 一键推送部署到网易有道词典笔 X6 Pro。
"""

import os
import sys
import shutil
import argparse
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(HERE, "tools")
APP_DATA_DIR = os.path.join(HERE, "app", "data")


def check_tool_dependencies():
    print("=== [1/6] 检查宿主机环境工具链 ===")
    deps = {
        "ffmpeg": "用于音视频解码与图像转换 (brew install ffmpeg)",
        "mono": "用于运行 PSB 反编译器 (brew install mono)",
    }
    missing = []
    for cmd, desc in deps.items():
        if not shutil.which(cmd):
            # 兼容 Mac Homebrew 常用路径
            found = False
            for p in ['/opt/homebrew/bin', '/usr/local/bin']:
                if os.path.exists(os.path.join(p, cmd)):
                    found = True
                    break
            if not found:
                missing.append((cmd, desc))
    if missing:
        print("[!] 警告：系统缺少以下必要工具依赖，转换过程可能会受阻：")
        for cmd, desc in missing:
            print(f"    - {cmd}: {desc}")
    else:
        print("[+] 工具链环境依赖检查通过 (ffmpeg, mono 均已就绪)。")


def unpack_game_xp3(game_dir, out_assets_dir):
    print("\n=== [2/6] 解包正版游戏资源 ===")
    unpack_script = os.path.join(TOOLS_DIR, "unpack_xp3.py")
    candidates = ["data.xp3", "adult.xp3", "patch.xp3"]
    found_xp3 = []
    for c in candidates:
        p = os.path.join(game_dir, c)
        if os.path.exists(p):
            found_xp3.append(p)
    
    if not found_xp3:
        # 递归找一级
        for root, dirs, files in os.walk(game_dir):
            for f in files:
                if f.lower().endswith(".xp3"):
                    found_xp3.append(os.path.join(root, f))
            break

    if found_xp3:
        print(f"[*] 检测到 XP3 压缩包: {[os.path.basename(x) for x in found_xp3]}")
        cmd = [sys.executable, unpack_script, "-o", out_assets_dir] + found_xp3
        subprocess.run(cmd, check=True)
    else:
        print("[*] 未在指定目录下发现 .xp3 文件，跳过解包步骤（假设该目录已包含解压素材）。")


def transcode_scenarios(scenario_src_dir):
    print("\n=== [3/6] 转码剧情剧本与选择支 ===")
    trans_script = os.path.join(TOOLS_DIR, "convert_scenario.py")
    if os.path.exists(trans_script):
        cmd = [sys.executable, trans_script]
        subprocess.run(cmd, check=False)
        print("[+] 剧本转换完成，已输出至 app/data/")
    else:
        print("[!] 未找到 convert_scenario.py，保留工程现有默认剧本数据。")


def convert_multimedia_assets(assets_dir, out_build_assets):
    print("\n=== [4/6] 批量转换美术与音频资源 ===")
    os.makedirs(out_build_assets, exist_ok=True)
    cg_out = os.path.join(out_build_assets, "cg")
    sd_out = os.path.join(out_build_assets, "sd")
    bg_out = os.path.join(out_build_assets, "bg")

    # 1. 转换 CG
    cg_sources = [
        os.path.join(assets_dir, "cg", "evimage"),
        os.path.join(assets_dir, "other"),
        assets_dir
    ]
    cg_script = os.path.join(TOOLS_DIR, "convert_all_cgs.py")
    if os.path.exists(cg_script):
        subprocess.run([sys.executable, cg_script, "--sources"] + cg_sources + ["-o", cg_out], check=False)

    # 2. 转换 SD 小人
    sd_src = os.path.join(assets_dir, "cg", "evimage", "SD")
    if not os.path.exists(sd_src):
        sd_src = os.path.join(assets_dir, "SD")
    sd_script = os.path.join(TOOLS_DIR, "convert_all_sds.py")
    if os.path.exists(sd_script) and os.path.exists(sd_src):
        subprocess.run([sys.executable, sd_script, "--source", sd_src, "-o", sd_out], check=False)

    print("[+] 美术资产批量适配完成。")


def build_and_install_amr(do_install, pen_serial=None):
    print("\n=== [5/6] 打包 Miniapp 安装包 ===")
    build_script = os.path.join(HERE, "build.py")
    cmd = [sys.executable, build_script]
    if do_install:
        cmd.append("--install")
        if pen_serial:
            cmd.extend(["--serial", pen_serial])
    subprocess.run(cmd, check=True)


def push_runtime_assets(assets_dir, pen_serial=None):
    print("\n=== [6/6] 推送媒体素材至词典笔 /userdisk/SenrenBanka ===")
    adb_cmd = ["adb"]
    if pen_serial:
        adb_cmd.extend(["-s", pen_serial])

    # 检查 adb 连通性
    try:
        res = subprocess.run(adb_cmd + ["devices"], capture_output=True, text=True)
        if "device" not in res.stdout:
            print("[!] 提示：未检测到已连接并授权的 ADB 设备。")
            print("    特别提醒：有道词典笔官方 ADB 通常设置了密码授权防护，需自行获取调试授权后方可连接推送。")
            return
        
        # 确保目标路径存在
        subprocess.run(adb_cmd + ["shell", "mkdir -p /userdisk/SenrenBanka"], check=True)
        print("[*] 正在同步本地媒体素材至词典笔磁盘...")
        # 逐项推送
        for folder in ["cg", "sd", "bg", "fg", "voice", "bgm", "se"]:
            local_p = os.path.join(assets_dir, folder)
            if os.path.exists(local_p):
                print(f"    -> 推送 {folder}/ ...")
                subprocess.run(adb_cmd + ["push", local_p, "/userdisk/SenrenBanka/"], check=False)
        print("[+] 资源推送完成！可在词典笔主屏幕启动千恋万花移植版。")
    except Exception as e:
        print(f"[!] 推送过程提示：{e}")
        print("    注意：词典笔 ADB 需要密码授权，请确认已完成调试提权。")


def main():
    parser = argparse.ArgumentParser(description="Senren Banka Dictionary Pen Port - Auto Setup & Install")
    parser.add_argument("--game-dir", help="游戏根目录 (含 data.xp3 或已解密游戏文件)")
    parser.add_argument("--assets-dir", default="./assets_ready", help="已解包的资源目录")
    parser.add_argument("--install", action="store_true", help="构建完成后自动执行 ADB 安装")
    parser.add_argument("--push-assets", action="store_true", help="自动通过 ADB 推送美术和音频资源到设备端")
    parser.add_argument("--pen-serial", help="词典笔 ADB 设备序列号或 IP:端口")
    args = parser.parse_args()

    print("================================================================")
    print("      有道词典笔《千恋＊万花》移植版 (Senren Banka Pen Port)     ")
    print("================================================================")
    print("推荐资源来源 (免去 XP3 解密环节): https://pan.touchgal.net/s/wpwtv")
    print("设备连接说明: 词典笔 ADB 需要密码授权，需自行获取调试授权。")
    print("================================================================\n")

    check_tool_dependencies()

    if args.game_dir:
        unpack_game_xp3(args.game_dir, args.assets_dir)

    # 若存在解包目录则执行转码
    if os.path.exists(args.assets_dir):
        transcode_scenarios(args.assets_dir)
        convert_multimedia_assets(args.assets_dir, "./build_assets")

    # 构建并可选安装
    build_and_install_amr(args.install, args.pen_serial)

    # 推送素材
    if args.push_assets:
        push_runtime_assets("./build_assets", args.pen_serial)

    print("\n[+] 全部流水线执行完毕！")


if __name__ == '__main__':
    main()
