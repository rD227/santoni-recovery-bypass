# Redmi 4X / santoni：TWRP、LineageOS 与 Magisk 安装记录

[English](README.en.md)

2026-10-01实测 Redmi 4X（`santoni`），2 GB RAM、16 GB eMMC，原系统 MIUI 8.2.18.0

**这里是ai写的对项目的简述，我认为这里可以起到介绍项目的作用，具体的短接之类的操作可以看我的blog，稍后我会写博客链接放在这里**

**但是刷入的具体命令还是在这里最详细**  ~~但是某些也可以通过图形界面操作的其实也没必要通过命令行刷入~~

基带显示，暂时没有插卡测试

这是锁定 bootloader 下的**启动验证绕过，不是正式解锁**；未获得设备专属 Xiaomi 解锁签名，未验证 unlocked 标志变为 true，fastboot 写入限制可能仍在   可以忽略已登录的小米账号强制刷入
## 已验证的组合与原理

| 部件 | 本次使用的文件 |
| --- | --- |
| 主 aboot | MIUI 11 `V11.0.2.0.NAMMIXM` 的原始小米签名 MBN，仅补零到 1 MiB |
| 初始 recovery | `RedWolf-santoni-appended.img`，通过 EDL 写入 |
| 配套 recovery | `TWRP-3.7.0-A11-20240520-mi8937_4_19-appended.img` |
| ROM | `lineage-18.1-20260524-UNOFFICIAL-Mi8937_4_19.zip`，支持 santoni，使用动态分区 |
| 未 root boot | 同一 ROM 原 boot 追加 Appender 尾块 |
| root boot | 用户在本机用 Magisk 修补同一 ROM 原 boot，再追加尾块 |

原始 abootbak 保留不变此前 TWRP 3.6.2 只是实验候选，完整安装使用 3.7.0

在 boot / recovery 有效数据段对齐后的结尾追加 4096 字节：前五字节 `30 83 19 89 64`，其余为零本机旧 aboot 遇到该异常签名长度会 panic / 进入 900E，换用 MIUI 11 原签名 aboot 后实测能启动带尾块镜像aboot 的机器码和签名没有修改

任何 root、换内核、ROM 更新若重打包 boot，可能去掉尾块正确顺序：**完成所有 boot 修补 → 检查镜像 → 追加尾块 → 刷入 → 启动**

## 目录和来源

本地仓库：`D:\santoni-recovery-bypass`

```text
README.md / README.en.md  中文与英文指南
scripts/                 离线生成脚本
payloads/                aboot、RedWolf、历史候选、Appender ZIP
roms/                    ROM、配套 TWRP、原始和修补后的 boot
tools/                   emmcdl 2.16、santoni Firehose
docs/                    分析和实测记录
local-only/              本机备份、日志、照片，不提交
SHA256SUMS.txt            工具及镜像校验值
```

默认不提交第三方二进制和个人设备备份；克隆仓库后需按来源下载镜像工具来自本机已有工具箱，尚未整理可重分发来源；第三方文件保留原许可证

- [社区绕过流程](https://www.ombob.eu.org/2024/03/redmi-4x-bypass-ubl-for-santoni-using.html)、[RedWolf 包](https://sfile.mobi/bOxnyjFkFU7)
- [MIUI 11 发布记录](https://xmfirmwareupdater.com/firmware/santoni/stable/V11.0.2.0.NAMMIXM/)、[原 firmware ZIP](https://github.com/XiaomiFirmwareUpdaterReleases/firmware_xiaomi_santoni/releases/download/stable-15.11.2019/fw_santoni_miui_HM4XGlobal_V11.0.2.0.NAMMIXM_eae1390b46_7.1.zip)发布 MD5 `9fb119dafdcd7ceb9d9148e26a44b08d` 与下载一致，提取 `firmware-update/emmc_appsboot.mbn`
- [ROM 发布目录](https://sourceforge.net/projects/crdroid7-mi8937/files/LOS/)、[配套 TWRP 和转换器](https://sourceforge.net/projects/crdroid7-mi8937/files/TWRP/)、[发布者安装说明](https://bin.disroot.org/?b34bd12638cc113f#8pJchohkQ9CaRBFLuajznpTeWrEMhbVPmS4FAF28gmqH)
- [Magisk 官方发布](https://github.com/topjohnwu/Magisk/releases)、[文件修补说明](https://topjohnwu.github.io/Magisk/install.html)官方流程假定已解锁；这里采用 TWRP 写入和尾块绕过

分析见 [BOOTLOADER-DIAGNOSIS.md](docs/BOOTLOADER-DIAGNOSIS.md)，实验日志说明见 [ROM-SELECTION.md](docs/ROM-SELECTION.md)历史中间状态以本 README 的最终结果为准

## 1. EDL 备份

需要稳定进入 9008、适用的 Firehose、emmcdl 2.16、ADB、Python下面 LBA 仅对应本机 GPT、512 字节扇区；其他手机先读取并核对自己的 GPTCOM 号可能改变

| 分区 | 起始 LBA | 扇区数 | 大小 |
| --- | ---: | ---: | ---: |
| aboot | 786432 | 2048 | 1 MiB |
| abootbak | 788480 | 2048 | 1 MiB |
| recovery | 921600 | 131072 | 64 MiB |

保留原 GPT、aboot、abootbak、recovery、devinfo、config 和个人数据**首次安装中的 Format Data 删除用户数据和内置存储，本次已经用户确认**

逐条执行并检查退出码、日志、长度及 hash；失败立即停止，不要继续粘贴后续命令每次使用新的 `$run` 目录：

```powershell
Set-Location D:\santoni-recovery-bypass
$edl = '.\tools\emmcdl-2.16.exe'
$loader = '.\tools\prog_emmc_firehose_8937_ddr.mbn'
$port = 'COM41' # 替换成实际端口
$run = '.\local-only\new-run'
New-Item -ItemType Directory -Path $run
& $edl -p $port -f $loader -MaxPayloadSizeToTargetInBytes 16384 -gpt
& $edl -p $port -f $loader -MaxPayloadSizeToTargetInBytes 16384 -d 786432 2048 -o "$run\aboot-a.bin"
& $edl -p $port -f $loader -MaxPayloadSizeToTargetInBytes 16384 -d 786432 2048 -o "$run\aboot-b.bin"
& $edl -p $port -f $loader -MaxPayloadSizeToTargetInBytes 16384 -d 788480 2048 -o "$run\abootbak.bin"
& $edl -p $port -f $loader -MaxPayloadSizeToTargetInBytes 16384 -d 921600 131072 -o "$run\recovery-a.bin"
& $edl -p $port -f $loader -MaxPayloadSizeToTargetInBytes 16384 -d 921600 131072 -o "$run\recovery-b.bin"
Get-FileHash "$run\*.bin" -Algorithm SHA256
```

同一分区两次读取长度、hash 必须一致本版 `-d start number` 的第二参数为**扇区数量**`-gpt` 显示布局，不代替原始 GPT 备份不要使用未经核对的 rawprogram XML，不要写入别人的 devinfo/config/GPT

## 2. EDL 写入主 aboot 和初始 RedWolf

```powershell
python .\scripts\prepare-images.py aboot .\payloads\emmc_appsboot-miui11-original.mbn .\payloads\aboot-miui11-signed-1MiB.bin
```

原 MBN 557576 字节，输出 1048576 字节脚本不覆盖已有文件；文件已存在时核对 hash，跳过生成备份确认后，仅写入主 aboot 和 recovery，保留 abootbak：

```powershell
& $edl -p $port -f $loader -MaxPayloadSizeToTargetInBytes 16384 -b aboot .\payloads\aboot-miui11-signed-1MiB.bin
& $edl -p $port -f $loader -MaxPayloadSizeToTargetInBytes 16384 -b recovery .\payloads\RedWolf-santoni-appended.img
& $edl -p $port -f $loader -MaxPayloadSizeToTargetInBytes 16384 -d 786432 2048 -o "$run\aboot-after.bin"
& $edl -p $port -f $loader -MaxPayloadSizeToTargetInBytes 16384 -d 921600 131072 -o "$run\recovery-after.bin"
```

aboot 完整读回 hash 应与输入一致；recovery 读回前“输入镜像长度”范围应逐字节一致确认后接好电池，用音量上 + 音量下 + 电源进入 recovery不要先启动原 MIUI，本机观察到它覆盖自定义 recovery

## 3. 换成配套 TWRP

```powershell
python .\scripts\append-boot-footer.py .\roms\TWRP-3.7.0-A11-20240520-mi8937_4_19.img .\roms\TWRP-3.7.0-A11-20240520-mi8937_4_19-appended.img
```

输出已存在时先校验、跳过生成RedWolf 普通 ADB 即可，无需 Sideload 或重进 9008以下假定 `adb` 在 PATH：

```powershell
adb devices -l
adb shell "dd if=/dev/block/bootdevice/by-name/recovery of=/tmp/recovery-before-twrp37.bin bs=1048576"
adb pull /tmp/recovery-before-twrp37.bin "$run\recovery-before-twrp37.bin"
adb push .\roms\TWRP-3.7.0-A11-20240520-mi8937_4_19-appended.img /tmp/twrp37-appended.img
adb shell "sha256sum /tmp/twrp37-appended.img"
adb shell "dd if=/tmp/twrp37-appended.img of=/dev/block/bootdevice/by-name/recovery bs=4096"
adb shell sync
adb shell "dd if=/dev/block/bootdevice/by-name/recovery of=/tmp/twrp37-readback.img bs=4096 count=7760"
adb shell "sha256sum /tmp/twrp37-readback.img"
# hash 一致才重启：
adb reboot recovery
```

也可用 Install → Install Image → 带尾块镜像 → **Recovery** → Reboot Recovery确认新 TWRP 主界面；修改系统提示先选 Keep Read Only，安装步骤再允许写入

## 4. 首次安装 ROM

这是从 MIUI / 普通分区迁入的实测步骤，不是通用“双清/四清”动态分区 ROM 的更新不需重复转换及格式化

```powershell
adb shell "dd if=/dev/block/bootdevice/by-name/boot of=/tmp/boot-before-rom.bin bs=1048576"
adb pull /tmp/boot-before-rom.bin "$run\boot-before-rom.bin"
adb shell "rm /tmp/boot-before-rom.bin"
adb shell "dd if=/dev/block/bootdevice/by-name/oem of=/tmp/oem-before-rom.bin bs=1048576"
adb pull /tmp/oem-before-rom.bin "$run\oem-before-rom.bin"
adb shell "rm /tmp/oem-before-rom.bin"
adb shell "twrp set tw_unmount_system 0"
adb shell "twrp remountrw"
adb push .\roms\Mi8937_Retrofit_Dynamic_Partitions_Converter_20220718_0xCAFEBABE.zip /tmp/rdp-converter.zip
adb shell "twrp install /tmp/rdp-converter.zip"
adb reboot recovery
# 待 adb devices 再显示 recovery；下一步删除所有用户数据：
adb shell "twrp format data"
adb shell "twrp mount /data"
adb push .\roms\lineage-18.1-20260524-UNOFFICIAL-Mi8937_4_19.zip /data/lineage18.zip
adb shell "sha256sum /data/lineage18.zip"
adb shell "twrp set tw_unmount_system 0"
adb shell "twrp install /data/lineage18.zip"
adb shell "tail -n 40 /tmp/recovery.log"
adb shell "ls -l /dev/block/mapper"
```

本 recovery 将 OEM 用作 metadata`twrp format data` 本次同时格式化 userdata 和 metadata；`twrp wipe /metadata` 不受此 CLI 支持格式化后 `/sdcard` 暂时指向 rootfs，因此使用已挂载的 `/data` 放置安装包

转换器的 `toybox blkdiscard` 本次显示 Unknown command，但初始 super 元数据已写入；后续 ROM 成功创建并写入 system/vendor/product/odm/system_ext，实际块数与预期一致不要将其他错误一概视作可忽略，需核对安装日志与实际开机

完成后暂不重启从同一 ROM ZIP 提取 `boot.img` 为 `roms/lineage18-boot-original.img`，补尾块后写入：

```powershell
python .\scripts\append-boot-footer.py .\roms\lineage18-boot-original.img .\roms\lineage18-boot-appended.img
adb push .\roms\lineage18-boot-appended.img /tmp/lineage18-boot-appended.img
adb shell "sha256sum /tmp/lineage18-boot-appended.img"
adb shell "dd if=/tmp/lineage18-boot-appended.img of=/dev/block/bootdevice/by-name/boot bs=4096"
adb shell sync
adb shell "dd if=/dev/block/bootdevice/by-name/boot of=/tmp/boot-readback.img bs=4096 count=5260"
adb shell "sha256sum /tmp/boot-readback.img"
# 与输入一致后：
adb reboot
```

已实测进入设置向导**不勾选“与操作系统一起更新 Lineage 恢复”**，保留带尾块的 TWRP本次没有额外安装 GApps；APK 文件名检查未发现常见 Play 商店及 Play 服务 APK

## 5. Magisk root：修补后补回尾块

1. 本机安装官方 Magisk APK本次曾建议 v30.7，但实际 APK 版本未记录；本机显示 `Ramdisk: Yes`
2. 将同一 ROM 的原 `lineage18-boot-original.img` 放到手机，Magisk → 安装 → 选择并修补一个文件不要使用别人生成的 patched boot
3. 输出复制回电脑本次命名为 `lineage18-boot-original-magiskpatched.img`，它没有尾块
4. 生成补好尾块的版本：

```powershell
python .\scripts\append-boot-footer.py .\roms\lineage18-boot-original-magiskpatched.img .\roms\lineage18-boot-magisk-appended.img
```

本次检查确认内核及启动命令行未变、ramdisk 包含 Magisk补尾块只追加 4096 字节，保留用户原文件

5. 进入 TWRP，先 Backup → **Boot**Install → **Install Image** → `lineage18-boot-magisk-appended.img` → **Boot** → 滑动确认 → Reboot System
6. 在 Magisk 查看安装状态，用需要 root 的应用验证授权用户已报告成功更新、额外设置或 Direct Install 可能再次重写 boot，重启前确保最终镜像仍有尾块

**root 不需要 Format Data；boot 镜像应写入 Boot，不是 Recovery** 若无法启动，用 TWRP 将已验证的 `lineage18-boot-appended.img` 写回 Boot，只恢复同一 ROM 的未 root boot，不恢复清空的数据

`append-boot-footer.py` 仅支持本次使用的 v0 镜像布局，拒绝截断、未知非零尾部及覆盖文件；不会连接或刷写手机

## 关键 SHA-256

| 文件 | SHA-256 |
| --- | --- |
| MIUI 11 补齐 aboot | `b659e08b40b95a50418295aa98b5bd0ee72f7f4ce7a7b7f454dc47efd591be71` |
| TWRP 3.7.0 带尾块 | `dcf3d423dca32e35c4a413f99f2890ffd128b6550b395db277833720321bf19f` |
| ROM ZIP | `defb8f363768b0b146f502538a8a7be4a1cc2e9522418cee179239028f96432b` |
| 未 root、带尾块 boot | `6a7656bceee64b7383277995e5e185f5a36f9d9c94138a2835a3cd08eefefbbb` |
| 本次 Magisk、带尾块 boot | `3670525c3d873276a4af4ce586ea59df1707968901420d71afc9f2ead59815c9` |

最后一行只对应此次用户输出；不同修补结果 hash 可以不同以上为本地计算值；MIUI aboot 另做过 ELF 段 hash、Qualcomm RSA 签名与证书链检查ROM 声称回移安全补丁，但未审计覆盖范围，构建日期不等于完整安全补丁级别

## 故障与回退

- 900E / 无法启动：~~检查实际分区内容、aboot 版本和尾块，不要反复格式化 Data~~ 确认分区无误之后可以直接断开电池排线，然后接回，即可重新开机
- EDL Status 21 / 部分写入：本机改为补齐 1 MiB aboot、16 KiB payload 后重写并读回成功失败不意味着没有写入；emmcdl 2.15 大分区读取曾不一致，2.16 才稳定
- 指纹入口：~~本次重接排线后发现 HAL 未启动，用户后续反馈恢复；没有完整记录恢复动作硬件 feature / 属性不证明硬件正常~~ 第一次如果是断开指纹排线然后启动的话，再次接回指纹排线重启即可
- 原版回退：仅使用同一手机备份，完整读回比对只恢复 aboot/recovery 不恢复已改变的 system/cust/metadata/data；原 aboot 会拒绝当前自定义 boot，不能直接混用

```powershell
& $edl -p $port -f $loader -MaxPayloadSizeToTargetInBytes 16384 -b aboot .\local-only\backups\aboot.bin
& $edl -p $port -f $loader -MaxPayloadSizeToTargetInBytes 16384 -b recovery .\local-only\backups\recovery-original.bin
```

所有固定 `dd count` 和 hash 仅对应本文指定文件；换镜像必须重新计算
