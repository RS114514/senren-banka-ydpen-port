# 有道词典笔《千恋＊万花》移植版 (Senren Banka for Youdao Pen)

面向**网易有道词典笔 X6 Pro**（Rockchip RK3562 / aarch64 Linux / Weston Wayland / 960×266 物理屏）的《千恋＊万花》完整视觉小说移植工程与全自动化资源转换工具链。

本项目采用**纯净开源引擎 + 自动化资产适配流水线**架构：仓库本身仅包含应用前端逻辑、原生软件混音插件、打包脚本与资源转换工具，**不附带、不分发任何受版权保护的商业游戏剧本、音频或美术素材**。

---

## 声明与重要提醒

### 1. 游戏资源推荐
为了避免繁琐的加密算法解密与版本不兼容问题，**强烈建议使用以下无 XP3 加密的资源**进行提取与转码：
- **推荐下载地址**：[https://pan.touchgal.net/s/wpwtv](https://pan.touchgal.net/s/wpwtv)
- 该版本资源未经专有算法混淆加密，可以直接通过本工程自带的解包与转码工具顺利提取全量剧本、语音、立绘及 CG。
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
   - 剧本、立绘、CG、SD、音频一键转换，自动生成适配词典笔的工程包。

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

## 一键导入与安装流程

只需一条命令即可完成正版资源解包、剧本转码、素材格式化、编译打包与真机部署：

```bash
# 1. 运行一键全自动管线（将 /path/to/game 替换为您的千恋万花游戏目录或无加密资源解压目录）
python3 import_and_install.py --game-dir "/path/to/game" --install --push-assets
```

该脚本将自动执行以下全过程：
1. 自动检测并解包 `data.xp3`、`adult.xp3`；
2. 反编译并转码全量 92 篇剧本，生成前端 `app/data/` 数据；
3. 批量将全屏 CG、SD 小人与背景缩放至 944×532 / 960×540 高清尺寸；
4. 调用 `build.py` 生成词典笔应用安装包 `dist/senren_banka-1.0.0.amr` 并安装；
5. 将美术与音频资产通过 ADB 推送到词典笔存储目录 `/userdisk/SenrenBanka/`。

---

## 手动分步指南（高级定制）

如果您希望分步调试或单独提取某些素材：

### 1. 手动解包 XP3 归档
```bash
python3 tools/unpack_xp3.py /path/to/data.xp3 -o ./assets_ready
```

### 2. 批量转换全屏 CG
```bash
python3 tools/convert_all_cgs.py --sources ./assets_ready/cg/evimage ./assets_ready/other -o ./build_assets/cg
```

### 3. 批量转换 SD 二头身小人
```bash
python3 tools/convert_all_sds.py --source ./assets_ready/cg/evimage/SD -o ./build_assets/sd
```

### 4. 编译与打包 Miniapp
```bash
python3 build.py --install
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
└── tools/                         # 解包、转码、立绘合成与多媒体转换工具集
```

---

## 开源协议

- 本项目代码部分以 **MIT License** 开源。
- 《千恋＊万花》（千恋＊万花 / Senren＊Banka）一切著作权、角色形象、剧本、音乐与美术所有权归 **Yuzusoft（柚子社）** 所有。
- 请勿将游戏原始版权素材打包发布到任何公共代码仓库或网络公开网盘。
