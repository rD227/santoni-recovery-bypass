> 最终状态（2026-10-01）：LineageOS 已进入设置向导；用户随后刷入 Magisk + Appender boot 并报告成功，Ramdisk: Yes。实际 Magisk APK 版本未记录。用户已将修补输入改名为 lineage18-boot-original-magiskpatched.img。下文保留历史过程，安装指南以 README.md / README.en.md 为准。

# ROM 选择记录（2026-10-01）

按本机可能只有 2 GB 内存选择 Android 11：优先候选为 zynpachi 发布的 `lineage-18.1-20260524-UNOFFICIAL-Mi8937_4_19.zip`。这不是 LineageOS 官方签名构建。

## 下载和离线检查

- 发布者项目：https://sourceforge.net/projects/crdroid7-mi8937/
- 下载：https://sourceforge.net/projects/crdroid7-mi8937/files/LOS/lineage-18.1-20260524-UNOFFICIAL-Mi8937_4_19.zip/download
- 本地文件：`../roms/lineage-18.1-20260524-UNOFFICIAL-Mi8937_4_19.zip`
- 大小：796596980 字节；SHA256：`defb8f363768b0b146f502538a8a7be4a1cc2e9522418cee179239028f96432b`。这是本地计算值，尚未与发布者提供的 SHA256 比对。
- ZIP 全部条目 CRC 检查通过。
- 安装脚本明确允许 `santoni`，Android SDK 30，boot image header v0。
- ZIP 安装脚本写入动态 system/vendor/product/odm/system_ext 和 boot；未包含 aboot、GPT、modem 或 recovery 的刷写步骤。
- OTA 声明的安全补丁日期仍为 2024-02-05。发布信息声称回移了 2026 年补丁；本次没有审计回移补丁内容，不能把构建日期等同于完整安全补丁覆盖。

## 流畅度判断的边界

没有本机刷入后的实测，也没有找到此确切 20260524 构建在 santoni 2 GB 设备上可量化、可复现的性能测试。因此不能保证“完全不卡”。选择较低 Android 版本且不额外装 GApps，是降低内存压力的工程判断。

同平台 Redmi 3S 3/32 用户报告 LOS18.1 k4.19 流畅，并报告 LOS22 加 GApps 存在微卡顿。这是不同设备、不同构建的个人体验，只能辅助选择，不能代表本机性能：
https://4pda.to/forum/index.php?showtopic=754768&st=34520

原设备树维护者的历史已知问题记录包含过相机问题（land/prada 比较严重，其他设备较轻），但条目后来被划除。记录陈旧，不能据此保证当前构建所有硬件正常：
https://t.me/mi_msm8937/812

## 安装条件与当前状态

本机目前为旧 RedWolf recovery，尚未安装该 ROM。电脑 ADB 尚未检测到手机。

发布者提供的说明要求配套 recovery、动态分区转换、清理 metadata，并在从另一 ROM 迁入时恢复出厂/建议 Format Data。它不能直接套用到本机的锁定 bootloader 绕过环境；boot 和 recovery 必须保留 Appender 尾块，才能尝试启动。

说明链接（Debian Paste 已失效，另一个可以读取）：
https://bin.disroot.org/?b34bd12638cc113f#8pJchohkQ9CaRBFLuajznpTeWrEMhbVPmS4FAF28gmqH

本地保存解密后的说明：`../local-only/los18-flash-guide.json`。

配套文件发布目录：https://sourceforge.net/projects/crdroid7-mi8937/files/TWRP/

注意：转换器会丢弃 system 和 cust 的内容；不是只改一个标志。新的 ROM 自身具备动态分区操作，但是否可以跳过转换器，需要按首次安装时的 recovery 与现有布局确认。本次未执行转换、清除或刷入 ROM。

下一步：先验证配套带尾块 recovery 启动及 ADB，再核对实际内存、备份所需分区与数据、确定首次安装的具体步骤。装完后测试桌面滑动、应用切换、Wi-Fi、音频、相机、指纹与通话；才可以评价本机日常可用性。

## 配套 recovery 离线准备

已完整下载 `TWRP-3.7.0-A11-20240520-mi8937_4_19.img`（31780864 字节）：SHA256 `7e2b3ef01114f8a55877f50071c9bb940e9a5669e7ed9b3463f290c44af86d6b`。

确认 Android boot header v0、页大小 2048、各段对齐后的结尾恰好等于文件长度后，追加与已成功 RedWolf 相同的 4096 字节尾块，生成 `TWRP-3.7.0-A11-20240520-mi8937_4_19-appended.img`：SHA256 `dcf3d423dca32e35c4a413f99f2890ffd128b6550b395db277833720321bf19f`。仅完成离线准备，尚未刷入/验证启动。

转换器完整 ZIP CRC 未发现损坏，SHA256 `069a21a05e23a58380e772463c279cb771640996df7a21d3a267bd0b50a3f0f0`。

对 ROM 的 system/product/system_ext Brotli 数据流进行 APK 文件名检查，发现 LineageSetupWizard、Trebuchet、Snap、Jelly 等；没有发现常见 Play 商店 Phonesky、GmsCore/PrebuiltGmsCore APK。该检查支持其无 GApps 的判断，但不是全面的应用安全审计。

## 2026-10-01 配套 recovery 写入

通过 RedWolf 普通 ADB（root）完成，不需要返回 9008。

- 完整原 recovery 备份：`local-only/backups/recovery-before-twrp37-20261001.bin`，64 MiB，SHA256 `917a3741dcb2568234aa6eaddc2a7a4f7da1eaa879cfe21364b937a928400a62`。
- 写入 `roms/TWRP-3.7.0-A11-20240520-mi8937_4_19-appended.img`，31784960 字节。
- 写入后按相同长度读回，SHA256 `dcf3d423dca32e35c4a413f99f2890ffd128b6550b395db277833720321bf19f` 与输入一致。
- 已发送 `adb reboot recovery`，启动结果另行记录；未执行任何 ROM 安装或数据清除。

实际命令（ADB 路径为本机 platform-tools）：

```powershell
adb shell "dd if=/dev/block/bootdevice/by-name/recovery of=/tmp/recovery-before-twrp37.bin bs=1048576"
adb pull /tmp/recovery-before-twrp37.bin ./recovery-before-twrp37.bin
adb push ./TWRP-3.7.0-A11-20240520-mi8937_4_19-appended.img /tmp/twrp37-appended.img
adb shell "sha256sum /tmp/twrp37-appended.img"
adb shell "dd if=/tmp/twrp37-appended.img of=/dev/block/bootdevice/by-name/recovery bs=4096"
adb shell sync
adb shell "dd if=/dev/block/bootdevice/by-name/recovery of=/tmp/twrp37-readback.img bs=4096 count=7760"
adb shell "sha256sum /tmp/twrp37-readback.img"
# 仅在读回 SHA256 与输入完全一致后：
adb reboot recovery
```

## 2026-10-01 首次安装进度

用户确认无需保留数据，授权直接清空安装。配套 TWRP 已通过重启及 ADB 验证。

刷入前备份：
- `local-only/backups/boot-before-los18-20261001.bin`，64 MiB，SHA256 `cb7546c4c04a832087a1eb7f92dc68478238ea7d4d47dddd175304f6979f8727`。
- `local-only/backups/oem-before-los18-20261001.bin`，64 MiB，SHA256 `3b6a07d0d404fab4e23b6d34bc6696a6a312dd92821332385e5af7c01c421351`。本 recovery 将 OEM 用作 metadata。

执行动态分区转换器：写入初始 super 元数据成功，但其 `toybox blkdiscard` 两次返回 Unknown command。安装器未正确把这些返回码视作失败，不能只凭总 RC=0 认定所有动作成功。后续 ROM 安装器的动态分区创建和映射结果需单独核对。

`twrp wipe /metadata` 不受此版 CLI 支持，没有执行擦除。改用 `twrp format data`，日志确认 userdata F2FS 创建成功，并自动以 mke2fs/e2fsdroid 格式化 metadata（OEM）；各子进程 RC=0。

格式化后旧 recovery 会话未重新映射 `/sdcard`（此时它仍在 rootfs）。第一次向 /sdcard 推送 ROM 因空间不足失败，ADB 清理了未完成文件；没有执行 ROM 安装。随后直接向已挂载且空间充足的 `/data/lineage18.zip` 推送，SHA256 与电脑上的完整 ZIP 一致。

实际安装命令：
```powershell
adb shell "twrp set tw_unmount_system 0"
adb shell "twrp remountrw"
adb push ./Mi8937_Retrofit_Dynamic_Partitions_Converter_20220718_0xCAFEBABE.zip /tmp/rdp-converter.zip
adb shell "twrp install /tmp/rdp-converter.zip"
adb reboot recovery
# 重新检测到 recovery 后：
adb shell "twrp format data"
adb shell "twrp mount /data"
adb push ./lineage-18.1-20260524-UNOFFICIAL-Mi8937_4_19.zip /data/lineage18.zip
adb shell "sha256sum /data/lineage18.zip"
adb shell "twrp set tw_unmount_system 0"
adb shell "twrp install /data/lineage18.zip"
```

离线从 ROM 原 ZIP 提取 boot.img，确认 header v0 的全部段对齐结尾与原文件长度一致（21540864 字节），追加同样 4096 字节 Appender 尾块，得到 `roms/lineage18-boot-appended.img`（21544960 字节，SHA256 `6a7656bceee64b7383277995e5e185f5a36f9d9c94138a2835a3cd08eefefbbb`）。仅改变尾部，不修改原 boot 有效载荷。待 ROM 完成后写入并读回核对，不能先重启系统。

## 2026-10-01 安装完成（首次开机待确认）

ROM 安装耗时 104 秒，安装器 RC=0，日志记录每个逻辑分区写入的实际块数与期望块数一致。`/dev/block/mapper` 已出现 system/vendor/product/odm/system_ext，转换器此前 blkdiscard 不支持的提示没有阻止后续 ROM 分区创建及写入。完整日志：`local-only/logs/los18-install-20261001.log`。

随后直接写入离线追加尾块的原 ROM boot（没有安装 Magisk、GApps 或其他模块）：
```powershell
adb push ./lineage18-boot-appended.img /tmp/lineage18-boot-appended.img
adb shell "sha256sum /tmp/lineage18-boot-appended.img"
adb shell "dd if=/tmp/lineage18-boot-appended.img of=/dev/block/bootdevice/by-name/boot bs=4096"
adb shell sync
adb shell "dd if=/dev/block/bootdevice/by-name/boot of=/tmp/lineage18-boot-readback.img bs=4096 count=5260"
adb shell "sha256sum /tmp/lineage18-boot-readback.img"
# 读回 hash 与输入一致后：
adb reboot
```

读回 21544960 字节，SHA256 `6a7656bceee64b7383277995e5e185f5a36f9d9c94138a2835a3cd08eefefbbb`，与离线准备的 boot 完全一致。读回副本：`local-only/backups/lineage18-boot-readback-20261001.img`。ROM ZIP 和未使用的 Appender ZIP 已从 /data 删除，以释放空间。

已发送重启系统；尚待实际进入设置向导及验证硬件。不能把写入成功等同于已经验证系统开机、通话或流畅度。

## 用户提供的 Magisk patched boot（2026-10-01）

检查 `roms/lineage18-boot-original-patched.img`：header v0、页大小 2048，各段长度完整；内核与本次 ROM 原 boot 完全一致，启动命令行未变。Ramdisk 可完整 gzip 解压并解析 CPIO，包含 `.backup/.magisk` 和 `overlay.d/sbin/magisk.xz`，配置 KEEPVERITY=true、KEEPFORCEENCRYPT=true、RECOVERYMODE=false、PREINITDEVICE=cache。

该文件大小 21671936 字节，SHA256 `d17829ac774f7fed28df16115af184bc92fd09db9d261631e5d55ec00686b20b`；有效段结尾就是文件结尾，没有 Appender 尾块。

保留用户输入，另外生成 `roms/lineage18-boot-magisk-appended.img`：21676032 字节，SHA256 `3670525c3d873276a4af4ce586ea59df1707968901420d71afc9f2ead59815c9`。它仅在用户 patched boot 后追加此前验证过的 4096 字节尾块。尚未刷入、尚未验证 Magisk 实际开机运行；离线结构检查不能代替启动验证。
