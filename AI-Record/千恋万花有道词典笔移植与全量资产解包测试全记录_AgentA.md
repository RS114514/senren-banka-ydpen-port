# 有道词典笔《千恋＊万花》移植、全量资产解包与实战调优全记录

- **执行代理**：Agent A（主开发 & 资源流水线工程师）
- **对话 ID**：`35b3c1b9-5520-4af1-b6a7-e9405b5f1214`
- **目标硬件**：网易有道词典笔 X6 Pro（YDPX6-2）
- **系统核心规约**：
  - SoC：Rockchip RK3562（四核 Cortex-A53 @ 2.0GHz，Mali-G52 GPU）
  - 内核与图形：Linux 5.10.66 + Weston（Wayland 合成器，旋转 90 度渲染）
  - 屏幕分辨率：物理屏幕 960 × 266，Falcon 小程序应用视口逻辑坐标 800 × 220
  - 小程序引擎：网易官方自研 Falcon / JQuick 运行时（基于定制 QuickJS 字节码 + 裁剪版 Vue 2 响应式模型）
  - 业务 AppID：`8002026102400099`

---

## 一、 核心任务脉络与阶段目标

在本项目中，我承接并主导了词典笔千恋万花移植版从“单线半成品”向“全角色完整高保真移植版”的演进，主要攻克了以下核心环节：
1. **主线全量剧本与全角色出场**：将包含全角色完整立绘差分的剧本接入游戏运行模块，保证 7 位主要角色在主线中正常出场，差分表情自然变换；
2. **舞台特写立绘形变彻底修复**：解决用户反馈的“放大看图/舞台特写时人物被压扁细长”的问题；
3. **角色语音播放与声卡独占冲突排查**：定位“所有角色没有语音”的硬件与系统成因，实现 Voice Ducking（语音避让）与协助软件 PCM 混音；
4. **画质全量高清化升级**：从 500GB 硬盘 2220×1280 原画提取，生成 960×540 背景与 780×440（Retina 2x）立绘并真机推送；
5. **全量全屏 CG 深度挖掘与转换**：解决官方 CG 仅有部分被提取的缺口，对 92 个原版剧本中 1195 处 `ev` 引用做全盘逆向，找回散落无修资源，达成 101/101 全屏 CG 100% 覆盖；
6. **建立防遗漏资产对账看门狗机制**：针对以往逐批修补、容易遗漏素材的痛点，编写 `audit_assets.py` 进行 1:1 依赖对账；
7. **独立开源仓库解耦与 GitHub 三端同步**：建立 `senren-banka-ydpen-port`，完成一键全自动管线 `import_and_install.py`，并与底层引擎及主开发仓库建立双向引用并公开推送。

---

## 二、 详细实操全过程记录

### 1. 主线剧本装载与 7 大核心角色登场真机验证
- **工作内容**：
  - 修改 `app/pages/game/game.js`，挂载 `app/data/chapter_all.js`（9155 句全量主线台词，覆盖官方 17 个主线章节）；
  - 进度指示器动态自适应为 `X / 9155`，底部章节栏实时显示 `CHAPTER 1-1`、`CHAPTER 1-2` 等；
  - 梳理角色出场索引与立绘差分映射表，达成 7470 处角色出场立绘 100.00% 命中；
- **真机截屏佐证**：
  - 芦花登场（第 47 句，`shot_char_roka.png`）；
  - 小春登场（第 302 句，`shot_char_koharu.png`）；
  - 玄十郎登场（第 388 句，`shot_char_genjurou.png`）；
  - 丛雨登场（第 587 句，`shot_char_murasame.png`）；
  - 芳乃登场（第 744 句，`shot_char_yoshino.png`）；
  - 茉子登场（第 1063 句，`shot_char_mako.png`）；
  - 蕾娜登场（第 3495 句，`shot_char_rena_real.png`）。

### 2. 舞台特写立绘形变（人物被压扁）定位与修复
- **现象分析**：
  用户在游玩界面轻触左侧舞台放大看图时，人物比例严重失调，呈现极端细长干瘪状态。
- **机制与原因定位**：
  审查 `app/pages/game/game.js` 发现历史遗留硬编码：
  在特写放大模式下，立绘图层 `game-zoom-char` 的宽度被硬编码计算为 `Math.round(z.h * 0.47)`，强制将立绘挤压为一个狭窄矩形。
- **修复方案与验证**：
  彻底废除固定比例计算，将放大立绘的尺寸与位移完全绑定到背景图层几何参数：
  ```javascript
  width: z.w + 'px',
  height: z.h + 'px',
  left: gImgLeft + 'px',
  top: gImgTop + 'px'
  ```
  在 1.0x 标准特写与 1.5x 放大特写模式下真机截屏验证（`shot_stage_zoom_fixed_10x.png`、`shot_stage_zoom_fixed_15x.png`），人物身体与面部比例舒展匀称。

### 3. 角色无语音排查与语音避让机制（Voice Ducking）
- **现象分析**：
  进入游戏后台词毫无语音发声，控制台或调试管道静默失败。
- **机制与原因排查**：
  1. 独立执行 `gst-launch-1.0` 在词典笔播放 `rok001_005.ogg`，可清晰出声，证明音频硬件、驱动与文件本身正常；
  2. 分析系统声卡架构：词典笔 `/etc/asound.conf` 默认直通 `hw:1,0`，**未开启 ALSA dmixer 硬件混音**；
  3. 当游戏标题或场景循环播放 BGM 时，GStreamer BGM 管道的 `alsasink` 独占了唯一的硬件 PCM 设备 `/dev/snd/pcmC1D0p`；
  4. 触发台词语音时，语音管道打开声卡直接遭遇 `EBUSY`（`Device 'default' is busy`），导致语音静音。
- **解决方案**：
  - 在 `app/pages/game/game.js` 的 `applyCurrentLine` 与 `replayVoice` 中实现 Voice Ducking（语音避让）：台词有语音时调用 `G.stopBgm()` 释放声卡占用，随后调用 `G.playVoice()` 发声；
  - 引入 `startVoiceWatcher()` 状态轮询看门狗，监测到语音播放完毕或被跳过时，无缝恢复章节 BGM；
  - 后续进一步协助主 Agent 在原生 C 层通过 GStreamer 实现应用内双声道软件 PCM 混音库 `libjsapi_gal.so`。

### 4. 画质全量高清化重制与设备部署
- **现象分析**：
  词典笔屏幕物理分辨率为 960×266（逻辑视口在 Weston 下经过 1.2 倍抗锯齿缩放），而设备端原有的背景与立绘仅为 390×220，在 1.5x/2.0x 特写放大时严重模糊发虚。
- **重制方案**：
  1. **背景高清化**：
     编写 `tools/generate_hd_bg.swift`，利用 macOS CoreGraphics 与 ImageIO 原生解码源库 WebP 格式，提取 48 张主线全量背景图，高质量缩放到 **960×540**（16:9 标准高清分辨率，抗锯齿重采样），全部推送到设备端 `/userdisk/SenrenBanka/bg/`；
  2. **立绘多核重制**：
     升级 `tools/composite.swift` 多核合成引擎，将 1274 张角色立绘差分统一提升为 **780×440**（Retina 2x 舞台画布），全部推送到设备端 `/userdisk/SenrenBanka/fg/`；
  3. 设备端读取二进制 PNG 头部证实尺寸升维，实机画面清晰锐利。

### 5. 全量全屏 CG 挖掘、反编译与转换（101/101 全覆盖）
- **现象分析**：
  原工程仅有 50 张 CG，大量个人线后半段名场面和专属 CG 缺失。
- **深度挖掘与逆向分析**：
  1. 遍历 92 个原版反编译剧本（`scn_src_parent/*.ks.json`），检索所有 `item[0] == 'ev'` 且 `showmode` 为 1/3 的调用，共定位 1195 处 CG 引用；
  2. 发现剧本引用的 ID 为带差分后缀的格式（如 `ev101aa`, `ev101ba`, `ev102ac` 等），其本质是基于基础 CG 的图层组合；
  3. 审查官方资源库发现：`assets_ready/cg/evimage/` 仅有 50 个 `.pimg` 且多带和谐遮罩，而全量未和谐原版和专属 CG 散落在 `assets_ready/other/` 与 `(無修正ゲーム)` 目录下；
  4. 汇总所有资源路径，精确定位全量 101 个唯一 CG 目标（芳乃 25、茉子 18、丛雨 18、蕾娜 18、小春 8、芦花 8、共通 6）。
- **自动化批处理实现**：
  编写 `tools/batch_convert_cg_ext.py`，调度 `mono tools/FreeMote/PsbDecompile.exe -raw` 解压图层，自动选取基础底图（WebP 走 ffmpeg，TLG 走 `tlg2bmp` + sips），统一标准化为 944×532 16:9 PNG：
  - 成功转换：101 / 101（无一失败）；
  - 生成 `cg_ext_manifest.json` 与设备推送归档 `cg_ext.tar`（56.13 MB，成员权限全部严格校验为 644，文件名 NFC 归一化）。

### 6. 建立防遗漏资产对账看门狗（Zero-Missing Audit）机制
- **背景与目的**：
  解决以往“人工发现缺素材 -> AI 打补丁 -> 下次又漏新素材”的反复修补问题。
- **实现手段**：
  编写独立审计工具 `tools/audit_assets.py`：
  1. 深入遍历 `app/data/*.js` 全部剧本，提取运行必需的资源全集：
     - 全屏 CG ID：148 项（含别名映射）；
     - 场景背景 ID：89 项；
     - 角色台词语音：24861 条；
     - 背景音乐 BGM：47 首；
  2. 自动检测目标资产目录（支持别名路径与归一化回退），执行 1:1 逐项校验；
  3. 任何素材覆盖率若低于 100%，直接输出具体缺失名称清单并中断构建，从流程上杜绝资产遗漏。

### 7. 独立开源移植仓库构建与 GitHub 三端同步
- **项目解耦与初始化**：
  - 创建全新独立目录 `/Volumes/500GB/Ydpen/senren-banka-ydpen-port`；
  - 迁移最新经过验证的 `app/`、`native/`、`libs/`、`build.py` 与全套工具链；
  - 编写端到端一键执行脚本 `import_and_install.py`，支持使用者通过正版资源一键完成解包、转码、对账、构建与真机安装。
- **落实核心政策与声明**：
  - **资源推荐**：明确指引建议使用无 XP3 加密的资源 [https://pan.touchgal.net/s/wpwtv](https://pan.touchgal.net/s/wpwtv)；
  - **ADB 授权声明**：醒目提醒有道词典笔官方 ADB 默认需要密码授权，使用者需自行解决调试提权。
- **三仓库同步与双向引用建立**：
  1. [RS114514/gal-dictionary-pen-engine](https://github.com/RS114514/gal-dictionary-pen-engine)：纯净通用视觉小说引擎仓库（已公开推送）；
  2. [RS114514/senren-banka-ydpen-port](https://github.com/RS114514/senren-banka-ydpen-port)：《千恋＊万花》移植版独立仓库（已公开推送，README 中明确引用底层通用引擎）；
  3. [RS114514/ydpen-hacking](https://github.com/RS114514/ydpen-hacking)：词典笔开发主仓库（已将千恋万花条目指向独立仓库并完成推送）。

---

## 三、 给后续维护者的建议与经验要点

1. **资源解密优先选择无加密源**：
   原版 Steam / 官方 XP3 带有专门的混淆加密算法，解密失败往往耗费大量算力。推荐直接使用经社区解密导出的无加密资源库（如前述 pan.touchgal.net 镜像），可直接由纯 Python 解包脚本处理。
2. **多媒体转码必须保留 Alpha 通道**：
   对于 SD/二头身素材与角色立绘，源文件常为 WebP 伪装成 PNG 后缀。转码时必须使用 `pix_fmt=rgba` 并开启双线性/Lanczos 缩放，避免半透明边缘产生黑边或锯齿。
3. **保持资产对账运行**：
   在向 `app/data/` 增改任何剧本、支线或后日谈数据后，务必先运行 `python3 tools/audit_assets.py`，确认全部引用的音频、CG 和背景均已在设备端或构建目录就绪后再行安装。
4. **严禁将游戏原版版权文件纳入 Git 跟踪**：
   保持 `.gitignore` 对 `*.amr`、`*.xp3`、`*.ogg`、`*.png` 资产目录的排除，确保开源仓库纯净合规。
