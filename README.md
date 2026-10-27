# 有道词典笔《千恋＊万花》移植版 (Senren Banka for Youdao Pen)

面向**网易有道词典笔 X6 Pro**（Rockchip RK3562 / aarch64 Linux / Weston Wayland / 960×266 物理屏）的《千恋＊万花》完整视觉小说移植工程与全自动化资源转换工具链。

底层基于通用视觉小说引擎 [**GAL Dictionary Pen Engine**](https://github.com/RS114514/gal-dictionary-pen-engine) 构建，在此基础上实现了针对《千恋＊万花》全角色路线、高保真画质、双声道 PCM 混音与自动化资产转码流水线的完整落地。

本项目采用**纯净开源引擎 + 自动化资产适配流水线**架构：仓库本身仅包含应用前端逻辑、原生软件混音插件、打包脚本与资源转换工具，**不附带、不分发任何受版权保护的商业游戏剧本、音频或美术素材**。

---

## 声明与重要提醒

### 1. 游戏资源推荐
为了避免繁琐的专有算法解密与加密版本不兼容问题，**强烈建议使用以下无 XP3 加密的资源**进行提取与转码：
- **推荐下载地址**：[https://pan.touchgal.net/s/wpwtv](https://pan.touchgal.net/s/wpwtv)
- 该版本资源未经专有加密算法混淆，可以直接通过本工程自带的解包与转码工具顺利提取全量剧本、语音、立绘及 CG。
- 请自觉支持正版游戏（Yuzusoft / 柚子社），所有提取产物仅限个人研究与学习使用。

### 2. 词典笔调试授权
- **有道词典笔官方系统的 ADB 接口默认设有密码验证与授权保护。**
- 本项目不提供破解工具或绕过方法。**请使用者自行想办法获取词典笔的 ADB 调试授权**（例如通过串口调试、社区公开的提权方法或官方开发者模式）。
- 确认 `adb devices` 能够正常识别并授权设备后，方可使用本工程提供的自动安装与素材推送功能。

---

## 特性亮点

1. **完整全剧情支持**：
   - 涵盖共通线（9155 句）以及 6 位女主角全量个人路线与分支选择支（全场景合流与嵌套跳过栈）；
   - 包含分支树流程图实时跳转与后日谈物语入口。
2. **多声道 PCM 软件混音引擎**：
   - RK3562 词典笔专用原生混音动态库（`libjsapi_gal.so`），完美解决硬件声卡独占冲突；
   - 原生支持背景音乐（BGM）与角色语音（Voice）并发播放，台词重播与自动避让（Ducking）。
3. **Retina 级高清画质适配**：
   - 16:9 主线背景重制缩放至 960×540（无锯齿无拉伸）；
   - 全角色 1274 张立绘差分升级为 780×440 高清舞台画布；
   - 全量 101 张名场面全屏 CG（944×532）与 295 张 SD Q版二头身小人图层展示。
4. **全自动资产解包与转换流水线**：
   - 纯 Python 编写的 XP3 原生解包器；
   - 剧本、立绘、CG、SD、音频一键转换，自动生成适配词典笔的工程包；
   - 内置 **Zero-Missing 完整性对账看门狗**，1:1 逐项核验素材覆盖率，杜绝遗漏。

---

## 环境准备

在进行资产转换与构建前，请确保您的电脑已安装以下依赖：

- **Python 3.9+**
- **FFmpeg**：用于音视频转码与 RGBA 图像处理
  ```bash
  # macOS
  brew install ffmpeg
  # Ubuntu / Debian
  sudo apt-get install ffmpeg
  ```
- **Mono**：用于运行 PSB / PIMG 资产反编译器
  ```bash
  # macOS
  brew install mono
  # Ubuntu / Debian
  sudo apt-get install mono-complete
  ```
- **Android SDK Platform-Tools (ADB)**：用于连接词典笔安装

---

## 一键导入与安装流程（推荐）

只需一条命令即可完成正版资源解包、剧本转码、素材格式化、全量对账、编译打包与真机部署：

```bash
# 运行一键全自动管线（将 /path/to/game 替换为您的千恋万花游戏目录或无加密资源解压目录）
python3 import_and_install.py --game-dir "/path/to/game" --install --push-assets
```

该脚本将全自动顺序执行 10 大流程：
1. 检测宿主机工具依赖；
2. 全量解包 `data.xp3`、`adult.xp3` 等；
3. 反编译并转码全量 92 篇剧本与选择支；
4. 批量缩放 90 张高清场景背景 (960×540)；
5. 批量多核合成 1274 张角色立绘差分 (780×440 Retina 2x)；
6. 批量提取并转码 101 张全屏 CG (944×532)；
7. 批量转码 295 张 SD 二头身 Q版小人 (944×566 RGBA 透明)；
8. 批量提取并同步 26,278 条台词语音、BGM 与 768 个音效；
9. 执行 1:1 完整性对账审计（零缺失看门狗）；
10. 构建 `senren_banka-1.0.0.amr`，安装并通过 ADB 推送全量媒体文件至词典笔。

---

## 手动分步指南（全量 8 大资源提取与处理流水线）

如果您希望单独调试某项资源或进行深度定制，可按照以下完整步骤分别执行：

### 1. 全量解包 XP3 归档
使用纯 Python 解包器从正版游戏归档中提取并自动分类全部原生文件：
```bash
python3 tools/unpack_xp3.py /path/to/data.xp3 /path/to/adult.xp3 -o ./assets_ready
```
*解包后将自动整理为 `scenario/`, `bg/`, `cg/`, `characters/`, `audio/`, `ui/`, `system/` 等标准子目录。*

### 2. 官方 92 篇剧本反编译与 Miniapp 数据转码
将原版 `.scn` 反编译，并转码为词典笔 Miniapp 前端驱动数据：
```bash
python3 tools/convert_scenario.py
```
*自动生成 `app/data/chapter_all.js`（9155 句主线）、`app/data/scn_*.js`（各角色路线）、`app/data/choices_all.js`（51 个选择支与合流跳过栈）以及 `app/data/fx_events.js`（转场白闪震动）。*

### 3. 场景背景高清重制与缩放 (960×540 16:9 标准高清)
解决原图 WebP 伪装与低分辨率模糊问题，使用 Lanczos 高画质抗锯齿算法缩放全量 90 张背景：
```bash
python3 tools/convert_all_bgs.py --source ./assets_ready/bg/bgimage -o ./build_assets/bg
```

### 4. 角色立绘差分多图层合成 (780×440 Retina 2x 画布)
原版立绘是分层存储的（身体素体、面部表情、发型发饰、服装配件），通过合成引擎批量导出 7 大主角与配角的全量 1274 张透明底 PNG：
```bash
python3 tools/composite_all_fgs.py
```

### 5. 全量全屏 CG 提取与转码 (944×532 16:9 标准)
从 `evimage/` 与 `other/` 目录挖掘全部 101 张核心全屏 CG（包含 6 大女主角个人线专属名场面、未和谐无修正 CG 及局部特写变体），批量转码为 944×532 16:9 PNG：
```bash
python3 tools/convert_all_cgs.py --sources ./assets_ready/cg/evimage ./assets_ready/other -o ./build_assets/cg
```

### 6. 全量 SD 二头身 Q版小人 RGBA 透明转码 (944×566)
将 `evimage/SD/` 中的 359 张原图批量转码为带 Alpha 透明通道的真 RGBA PNG：
```bash
python3 tools/convert_all_sds.py --source ./assets_ready/cg/evimage/SD -o ./build_assets/sd
```

### 7. 角色台词语音、BGM 与音效格式化同步
提取并同步全量 26,278 条角色语音文件（`rok001_005.ogg` 等）、30+ 首 BGM 以及 768 个音效：
```bash
python3 tools/sync_all_audio.py --source-root ./assets_ready -o ./build_assets
```

### 8. 全量资产 1:1 完整性审计对账 (Zero-Missing Audit)
逐行遍历剧本中的所有资源调用，对账检查提取产物目录，确保 100% 覆盖率，杜绝以往逐批修补遗漏的问题：
```bash
python3 tools/audit_assets.py --assets ./build_assets
```

### 9. 编译打包 Miniapp
将前端页面、配置与原生双声道混音库打包为词典笔安装包：
```bash
python3 build.py --install
```

### 10. 推送全量媒体文件至词典笔
通过 ADB 将适配完成的媒体文件同步推送到词典笔存储空间：
```bash
adb shell mkdir -p /userdisk/SenrenBanka
adb push build_assets/bg /userdisk/SenrenBanka/
adb push build_assets/fg /userdisk/SenrenBanka/
adb push build_assets/cg /userdisk/SenrenBanka/
adb push build_assets/sd /userdisk/SenrenBanka/
adb push build_assets/voice /userdisk/SenrenBanka/
adb push build_assets/bgm /userdisk/SenrenBanka/
adb push build_assets/se /userdisk/SenrenBanka/
```

---

## 目录结构说明

```text
senren-banka-ydpen-port/
├── README.md                      # 本文档
├── LICENSE                        # MIT 许可证
├── build.py                       # 词典笔 Miniapp 构建与安装脚本
├── import_and_install.py          # 一键全自动资产适配流水线入口
├── app/                           # 词典笔 Miniapp 前端工程代码
│   ├── manifest.json              # 应用元数据与权限
│   ├── app.js                     # 全局生命周期与错误捕获
│   ├── pages/                     # 游戏各界面（game, title, flowchart, afterstory 等）
│   └── data/                      # 剧情与选择支数据
├── native/                        # RK3562 原生软件 PCM 混音库源码 (gal_gs.c)
├── libs/                          # 预编译 aarch64 动态链接库 (libjsapi_gal.so)
└── tools/                         # 全套解包、转码、立绘合成与音频同步工具集
    ├── unpack_xp3.py              # 纯 Python 原生 XP3 解包器
    ├── convert_scenario.py        # 剧本与选择支转换引擎
    ├── convert_all_bgs.py         # 场景背景高清缩放工具 (960x540)
    ├── composite_all_fgs.py       # 角色立绘多图层差分多核合成工具
    ├── convert_all_cgs.py         # 全量全屏 CG 提取转码工具 (944x532)
    ├── convert_all_sds.py         # SD 二头身 Q版小人 RGBA 转码工具
    ├── sync_all_audio.py          # 2.6万条语音、BGM与音效同步工具
    ├── audit_assets.py            # 全量资产 1:1 完整性审计对账看门狗
    └── FreeMote/ & tlg2bmp        # 底层二进制解码辅助组件
```

---

## 开源协议

- 本项目代码部分以 **MIT License** 开源。
- 《千恋＊万花》（千恋＊万花 / Senren＊Banka）一切著作权、角色形象、剧本、音乐与美术所有权归 **Yuzusoft（柚子社）** 所有。
- 请勿将游戏原始版权素材打包发布到任何公共代码仓库或网络公开网盘。
