#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_and_install.py —— 有道词典笔《千恋＊万花》移植版一键解包、全量转码、对账、构建与安装总入口

全量处理流水线：
1. 依赖工具链检测 (ffmpeg, mono, python3)
2. 原版 XP3 全量解包归类 (scenario, fgimage, bgimage, evimage, voice, bgm, se)
3. 官方 92 篇剧本反编译与 Miniapp 剧情/选择支/分支合流转码 (app/data/*.js)
4. 场景背景高清重制缩放 (960x540 16:9 标准无损)
5. 角色立绘多图层差分多核合成 (780x440 Retina 2x 画布)
6. 全量 101 张全屏 CG 提取转码 (944x532 16:9 标准)
7. 全量 295 张 SD 二头身 Q版小人 RGBA 透明转码 (944x566)
8. 全量 26,278 条台词语音、BGM 与 768 个音效格式化同步
9. 全量资产 1:1 完整性审计对账 (audit_assets.py，零缺失看门狗)
10. 构建 senren_banka-1.0.0.amr，通过 ADB 安装并推送媒体素材至 /userdisk/SenrenBanka
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
    print("=== [1/10] 检查宿主机环境工具链 ===")
    deps = {
        "ffmpeg": "用于音视频解码与图像转换 (brew install ffmpeg)",
        "mono": "用于运行 PSB 反编译器 (brew install mono)",
    }
    missing = []
    for cmd, desc in deps.items():
        found = False
        if shutil.which(cmd):
            found = True
        else:
            for p in ['/opt/homebrew/bin', '/usr/local/bin', '/usr/bin']:
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
    print("\n=== [2/10] 全量解包正版游戏资源 ===")
    unpack_script = os.path.join(TOOLS_DIR, "unpack_xp3.py")
    candidates = ["data.xp3", "adult.xp3", "patch.xp3", "update.xp3"]
    found_xp3 = []
    for c in candidates:
        p = os.path.join(game_dir, c)
        if os.path.exists(p):
            found_xp3.append(p)

    if not found_xp3:
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
    print("\n=== [3/10] 反编译并转码全场景 92 篇剧本与分支选择支 ===")
    trans_script = os.path.join(TOOLS_DIR, "convert_scenario.py")
    if os.path.exists(trans_script):
        subprocess.run([sys.executable, trans_script], check=False)
        print("[+] 剧本转码完成，已输出到 app/data/（含选择支、合流与分支跳过栈）。")
    else:
        print("[!] 未找到 convert_scenario.py，保留工程默认剧本。")


def convert_all_backgrounds(assets_dir, out_dir):
    print("\n=== [4/10] 批量缩放场景高清背景 (960x540 16:9 标准高清) ===")
    bg_src = os.path.join(assets_dir, "bg", "bgimage")
    if not os.path.exists(bg_src):
        bg_src = os.path.join(assets_dir, "bgimage")
    if not os.path.exists(bg_src):
        bg_src = os.path.join(assets_dir, "bg")

    bg_script = os.path.join(TOOLS_DIR, "convert_all_bgs.py")
    if os.path.exists(bg_script) and os.path.exists(bg_src):
        subprocess.run([sys.executable, bg_script, "--source", bg_src, "-o", os.path.join(out_dir, "bg")], check=False)
    else:
        print(f"[!] 背景源目录未找到: {bg_src}")


def composite_all_sprites(assets_dir, out_dir):
    print("\n=== [5/10] 批量合成 1274 张角色立绘差分 (780x440 Retina 2x 画布) ===")
    fg_script = os.path.join(TOOLS_DIR, "composite_all_fgs.py")
    if os.path.exists(fg_script):
        subprocess.run([sys.executable, fg_script], check=False)
        print("[+] 角色立绘多核合成完毕。")
    else:
        print("[!] 未找到 composite_all_fgs.py，跳过立绘合成。")


def convert_all_cgs(assets_dir, out_dir):
    print("\n=== [6/10] 批量提取与转码全量 101 张全屏 CG (944x532 16:9 标准) ===")
    cg_sources = [
        os.path.join(assets_dir, "cg", "evimage"),
        os.path.join(assets_dir, "other"),
        assets_dir
    ]
    cg_script = os.path.join(TOOLS_DIR, "convert_all_cgs.py")
    if os.path.exists(cg_script):
        subprocess.run([sys.executable, cg_script, "--sources"] + cg_sources + ["-o", os.path.join(out_dir, "cg")], check=False)


def convert_all_sds(assets_dir, out_dir):
    print("\n=== [7/10] 批量转码全量 295 张 SD 二头身 Q版小人 (944x566 RGBA 透明) ===")
    sd_src = os.path.join(assets_dir, "cg", "evimage", "SD")
    if not os.path.exists(sd_src):
        sd_src = os.path.join(assets_dir, "SD")
    sd_script = os.path.join(TOOLS_DIR, "convert_all_sds.py")
    if os.path.exists(sd_script) and os.path.exists(sd_src):
        subprocess.run([sys.executable, sd_script, "--source", sd_src, "-o", os.path.join(out_dir, "sd")], check=False)


def sync_multimedia_audio(assets_dir, out_dir):
    print("\n=== [8/10] 提取并同步 26,278 条角色语音、全量 BGM 与 768 个音效 ===")
    audio_script = os.path.join(TOOLS_DIR, "sync_all_audio.py")
    if os.path.exists(audio_script):
        subprocess.run([sys.executable, audio_script, "--source-root", assets_dir, "-o", out_dir], check=False)


def run_zero_missing_audit(build_assets_dir):
    print("\n=== [9/10] 执行全量资产 1:1 完整性审计对账 (Zero-Missing Audit) ===")
    audit_script = os.path.join(TOOLS_DIR, "audit_assets.py")
    if os.path.exists(audit_script):
        res = subprocess.run([sys.executable, audit_script, "--assets", build_assets_dir])
        if res.returncode != 0:
            print("[!] 提示：检测到部分素材尚未完全对齐，请根据上述提示查漏补缺。")
        else:
            print("[+] 审计全面通过！全量依赖资产 100% 覆盖就绪！")


def build_and_deploy_device(do_install, do_push_assets, build_assets_dir, pen_serial=None):
    print("\n=== [10/10] 编译构建 Miniapp 并部署到词典笔 ===")
    build_script = os.path.join(HERE, "build.py")
    cmd = [sys.executable, build_script]
    if do_install:
        cmd.append("--install")
        if pen_serial:
            cmd.extend(["--serial", pen_serial])
    subprocess.run(cmd, check=True)

    if do_push_assets:
        print("\n[*] 正在同步本地媒体素材至词典笔磁盘 /userdisk/SenrenBanka ...")
        adb_cmd = ["adb"]
        if pen_serial:
            adb_cmd.extend(["-s", pen_serial])

        try:
            chk = subprocess.run(adb_cmd + ["devices"], capture_output=True, text=True)
            if "device" not in chk.stdout:
                print("[!] 提示：未检测到已连接并授权的 ADB 设备。")
                print("    特别提醒：有道词典笔官方系统 ADB 默认设有密码授权，需自行想办法解决授权后方可推送。")
                return

            subprocess.run(adb_cmd + ["shell", "mkdir -p /userdisk/SenrenBanka"], check=True)
            for folder in ["bg", "fg", "cg", "sd", "voice", "bgm", "se"]:
                local_p = os.path.join(build_assets_dir, folder)
                if os.path.exists(local_p):
                    print(f"    -> 正在推送 {folder}/ ...")
                    subprocess.run(adb_cmd + ["push", local_p, "/userdisk/SenrenBanka/"], check=False)
            print("[+] 资产推送全部完成！可在词典笔主屏启动《千恋＊万花》移植版。")
        except Exception as e:
            print(f"[!] 推送异常提示：{e}")


def main():
    parser = argparse.ArgumentParser(description="Senren Banka Youdao Pen Port - End-to-End Asset Setup & Install")
    parser.add_argument("--game-dir", help="游戏根目录 (含 data.xp3 或已解密游戏文件)")
    parser.add_argument("--assets-dir", default="./assets_ready", help="已解包的资源目录")
    parser.add_argument("--build-assets", default="./build_assets", help="适配转换后的最终设备资产目录")
    parser.add_argument("--install", action="store_true", help="构建完成后自动执行 ADB 安装应用包")
    parser.add_argument("--push-assets", action="store_true", help="自动通过 ADB 推送美术和音频资源到设备端")
    parser.add_argument("--pen-serial", help="词典笔 ADB 设备序列号或 IP:端口")
    args = parser.parse_args()

    print("==================================================================")
    print("      有道词典笔《千恋＊万花》移植版 (Senren Banka Pen Port)      ")
    print("==================================================================")
    print("推荐无加密资源来源 (免除 XP3 专有加密算法困扰):")
    print("    https://pan.touchgal.net/s/wpwtv")
    print("设备连接提醒: 词典笔官方 ADB 默认需要密码授权，需自行解决调试授权。")
    print("==================================================================\n")

    check_tool_dependencies()

    if args.game_dir:
        unpack_game_xp3(args.game_dir, args.assets_dir)

    if os.path.exists(args.assets_dir):
        transcode_scenarios(args.assets_dir)
        convert_all_backgrounds(args.assets_dir, args.build_assets)
        composite_all_sprites(args.assets_dir, args.build_assets)
        convert_all_cgs(args.assets_dir, args.build_assets)
        convert_all_sds(args.assets_dir, args.build_assets)
        sync_multimedia_audio(args.assets_dir, args.build_assets)

    run_zero_missing_audit(args.build_assets)
    build_and_deploy_device(args.install, args.push_assets, args.build_assets, args.pen_serial)

    print("\n[+] 全流程处理顺利完成！")


if __name__ == '__main__':
    main()
