# Redmi 4X / santoni: installing TWRP, LineageOS and Magisk

[简体中文](README.md)

Recorded on October 1, 2026. Tested device: Redmi 4X (`santoni`), 2 GB RAM, 16 GB eMMC, originally running MIUI 8.2.18.0.

**The device successfully booted the matching TWRP 3.7.0 and LineageOS 18.1 (Android 11, Linux 4.19). The user subsequently flashed a Magisk-patched boot image with the bypass footer restored and reported success.** Magisk shows `Ramdisk: Yes`. The exact Magisk APK version used was not recorded. Hardware, calls, battery life and long-term performance have not been comprehensively tested.

This is a **boot verification bypass with a locked bootloader, not an official unlock**. No device-specific Xiaomi unlock signature was obtained, and an unlocked flag changing to true was not verified. Fastboot flashing restrictions may remain. This record does not cover removing a Mi account.

## Tested combination and mechanism

| Component | File used |
| --- | --- |
| Main aboot | Original Xiaomi-signed MBN from MIUI 11 `V11.0.2.0.NAMMIXM`, only zero-padded to 1 MiB |
| Initial recovery | `RedWolf-santoni-appended.img`, written through EDL |
| Matching recovery | `TWRP-3.7.0-A11-20240520-mi8937_4_19-appended.img` |
| ROM | `lineage-18.1-20260524-UNOFFICIAL-Mi8937_4_19.zip`, supports santoni and uses dynamic partitions |
| Unrooted boot | Original boot from that ROM, with the Appender footer added |
| Rooted boot | Original boot from that ROM, patched with Magisk on this device, then given the footer |

The original abootbak was preserved. TWRP 3.6.2 was an earlier experimental candidate; the completed installation used 3.7.0.

Append 4096 bytes at the aligned end of the boot/recovery payload: the first five bytes are `30 83 19 89 64`, followed by zeros. The original aboot panicked on this malformed signature length and entered 900E. With the MIUI 11 signed aboot, this device successfully booted images carrying the footer. The aboot machine code and signature were not modified.

Rooting, changing kernels or updating the ROM may rebuild boot and remove the footer. Use this order: **finish all boot modifications → inspect the image → append the footer → flash → boot**.

## Files and sources

Local repository: `D:\santoni-recovery-bypass`.

```text
README.md / README.en.md  Chinese and English guides
scripts/                 Offline image preparation scripts
payloads/                aboot, RedWolf, older candidates, Appender ZIPs
roms/                    ROM, matching TWRP, original/patched boot images
tools/                   emmcdl 2.16 and santoni Firehose
docs/                    Analysis and experimental records
local-only/              Device backups, logs and photos; excluded from Git
SHA256SUMS.txt            Local tool and image hashes
```

Third-party binaries and device-specific backups are excluded from Git by default. Cloning this repository does not provide the images; obtain them from the sources below. Tools came from the user's existing local toolbox; a redistributable source has not been established. Third-party files retain their original licenses.

- [Community bypass procedure](https://www.ombob.eu.org/2024/03/redmi-4x-bypass-ubl-for-santoni-using.html), [RedWolf package](https://sfile.mobi/bOxnyjFkFU7).
- [MIUI 11 firmware listing](https://xmfirmwareupdater.com/firmware/santoni/stable/V11.0.2.0.NAMMIXM/), [original firmware ZIP](https://github.com/XiaomiFirmwareUpdaterReleases/firmware_xiaomi_santoni/releases/download/stable-15.11.2019/fw_santoni_miui_HM4XGlobal_V11.0.2.0.NAMMIXM_eae1390b46_7.1.zip). Published MD5 `9fb119dafdcd7ceb9d9148e26a44b08d` matched the download. Extract `firmware-update/emmc_appsboot.mbn`.
- [ROM releases](https://sourceforge.net/projects/crdroid7-mi8937/files/LOS/), [matching TWRP and converter](https://sourceforge.net/projects/crdroid7-mi8937/files/TWRP/), [publisher's installation instructions](https://bin.disroot.org/?b34bd12638cc113f#8pJchohkQ9CaRBFLuajznpTeWrEMhbVPmS4FAF28gmqH).
- [Official Magisk releases](https://github.com/topjohnwu/Magisk/releases), [image patching instructions](https://topjohnwu.github.io/Magisk/install.html). The official procedure assumes an unlocked bootloader; this device uses TWRP writes and the bypass footer instead.

See [BOOTLOADER-DIAGNOSIS.md](docs/BOOTLOADER-DIAGNOSIS.md) for analysis and [ROM-SELECTION.md](docs/ROM-SELECTION.md) for experimental logs. These supporting records are in Chinese and preserve historical intermediate states; this README describes the final outcome.

## 1. EDL backups

Required: reliable 9008 access, a compatible Firehose, emmcdl 2.16, ADB and Python. The following LBAs belong only to the GPT verified on this device, with 512-byte sectors. Read and verify another device's own GPT before using raw offsets. The COM port can change.

| Partition | Starting LBA | Sector count | Size |
| --- | ---: | ---: | ---: |
| aboot | 786432 | 2048 | 1 MiB |
| abootbak | 788480 | 2048 | 1 MiB |
| recovery | 921600 | 131072 | 64 MiB |

Preserve the original GPT, aboot, abootbak, recovery, devinfo, config and personal data. **Format Data in the first-install procedure deletes user data and internal storage. The user explicitly approved this for the tested phone.**

Run commands individually and inspect exit codes, logs, lengths and hashes. Stop on failure; do not keep pasting subsequent commands. Use a new `$run` directory each time.

```powershell
Set-Location D:\santoni-recovery-bypass
$edl = '.\tools\emmcdl-2.16.exe'
$loader = '.\tools\prog_emmc_firehose_8937_ddr.mbn'
$port = 'COM41' # Replace with the actual port
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

Two reads of the same partition must have matching lengths and hashes. In this emmcdl build, the second parameter of `-d start number` is a **sector count**. `-gpt` displays the layout; it does not replace a raw GPT backup. Do not use unchecked rawprogram XML or another device's devinfo/config/GPT.

## 2. Write the main aboot and initial RedWolf through EDL

```powershell
python .\scripts\prepare-images.py aboot .\payloads\emmc_appsboot-miui11-original.mbn .\payloads\aboot-miui11-signed-1MiB.bin
```

The original MBN is 557576 bytes; the output is 1048576 bytes. Scripts refuse to overwrite existing output. If it already exists, verify its hash and skip generation. After verifying backups, write only the main aboot and recovery, preserving abootbak:

```powershell
& $edl -p $port -f $loader -MaxPayloadSizeToTargetInBytes 16384 -b aboot .\payloads\aboot-miui11-signed-1MiB.bin
& $edl -p $port -f $loader -MaxPayloadSizeToTargetInBytes 16384 -b recovery .\payloads\RedWolf-santoni-appended.img
& $edl -p $port -f $loader -MaxPayloadSizeToTargetInBytes 16384 -d 786432 2048 -o "$run\aboot-after.bin"
& $edl -p $port -f $loader -MaxPayloadSizeToTargetInBytes 16384 -d 921600 131072 -o "$run\recovery-after.bin"
```

The full aboot readback hash must match the input. The first input-image-length bytes of the recovery readback must match the input byte for byte. After verification, reconnect the battery and enter recovery using Volume Up + Volume Down + Power. Do not boot the original MIUI first: it was observed restoring stock recovery on this phone.

## 3. Install the matching TWRP

```powershell
python .\scripts\append-boot-footer.py .\roms\TWRP-3.7.0-A11-20240520-mi8937_4_19.img .\roms\TWRP-3.7.0-A11-20240520-mi8937_4_19-appended.img
```

If output already exists, verify it and skip generation. Ordinary ADB in RedWolf is sufficient; Sideload and another trip to 9008 are unnecessary. The examples assume `adb` is on PATH:

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
# Reboot only after matching hashes:
adb reboot recovery
```

Alternatively, use Install → Install Image → select the image with the footer → **Recovery** → Reboot Recovery. Confirm the new TWRP main screen. Select Keep Read Only at the initial prompt; the installation commands subsequently allow writes.

## 4. First ROM installation

These are the tested steps when migrating from MIUI/standard partitions. They are not a generic recommendation to wipe an arbitrary list of partitions. Updating an existing dynamic-partition ROM does not require repeating conversion and formatting.

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
# Wait until adb devices shows recovery again; the next step deletes all user data:
adb shell "twrp format data"
adb shell "twrp mount /data"
adb push .\roms\lineage-18.1-20260524-UNOFFICIAL-Mi8937_4_19.zip /data/lineage18.zip
adb shell "sha256sum /data/lineage18.zip"
adb shell "twrp set tw_unmount_system 0"
adb shell "twrp install /data/lineage18.zip"
adb shell "tail -n 40 /tmp/recovery.log"
adb shell "ls -l /dev/block/mapper"
```

This recovery uses OEM as metadata. `twrp format data` formatted both userdata and metadata in this run; its CLI does not support `twrp wipe /metadata`. Immediately after formatting, `/sdcard` still pointed to rootfs, so the ZIP was stored on the mounted `/data` partition instead.

The converter reported `toybox: Unknown command blkdiscard`, but wrote the initial super metadata. The subsequent ROM installer successfully created and wrote system/vendor/product/odm/system_ext, with actual block counts matching expectations. Do not assume other errors are harmless: inspect installation logs and verify booting.

Do not reboot yet. Extract `boot.img` from this exact ROM ZIP as `roms/lineage18-boot-original.img`, then append the footer and write Boot:

```powershell
python .\scripts\append-boot-footer.py .\roms\lineage18-boot-original.img .\roms\lineage18-boot-appended.img
adb push .\roms\lineage18-boot-appended.img /tmp/lineage18-boot-appended.img
adb shell "sha256sum /tmp/lineage18-boot-appended.img"
adb shell "dd if=/tmp/lineage18-boot-appended.img of=/dev/block/bootdevice/by-name/boot bs=4096"
adb shell sync
adb shell "dd if=/dev/block/bootdevice/by-name/boot of=/tmp/boot-readback.img bs=4096 count=5260"
adb shell "sha256sum /tmp/boot-readback.img"
# After confirming the readback matches the input:
adb reboot
```

The phone successfully reached the LineageOS setup wizard. **Leave “Update Lineage Recovery alongside the OS” unchecked** to preserve TWRP with its footer. No additional GApps were installed; an APK filename inspection found no common Play Store or Play Services APKs.

## 5. Magisk root: restore the footer after patching

1. Install the official Magisk APK on this phone. Version 30.7 was suggested during this session, but the APK version actually used was not recorded. The app shows `Ramdisk: Yes`.
2. Copy the original `lineage18-boot-original.img` from the same ROM to this phone. In Magisk, choose Install → Select and Patch a File. Do not use somebody else's patched boot.
3. Copy the result to the computer. The user named it `lineage18-boot-original-magiskpatched.img`; it had no bypass footer.
4. Generate a separate image with the footer restored:

```powershell
python .\scripts\append-boot-footer.py .\roms\lineage18-boot-original-magiskpatched.img .\roms\lineage18-boot-magisk-appended.img
```

Inspection confirmed the kernel and boot command line were unchanged and the ramdisk contained Magisk. Footer processing only appended 4096 bytes and preserved the user's input file.

5. Enter TWRP and first select Backup → **Boot**. Then Install → **Install Image** → `lineage18-boot-magisk-appended.img` → **Boot** → swipe to flash → Reboot System.
6. Check the installed status in Magisk and verify authorization with an app requiring root. The user reported success. Updates, additional setup or Direct Install may rewrite boot again; ensure the final image still carries the footer before rebooting.

**Root installation does not require Format Data. Flash a boot image to Boot, not Recovery.** If it fails to boot, use TWRP to restore the verified `lineage18-boot-appended.img` to Boot. This restores the same ROM's unrooted boot, not erased user data.

`append-boot-footer.py` supports only the v0 image layout used here, refuses truncated images, unknown nonzero trailing data and existing output paths, and never connects to or flashes a phone.

## Key SHA-256 values

| File | SHA-256 |
| --- | --- |
| Padded MIUI 11 aboot | `b659e08b40b95a50418295aa98b5bd0ee72f7f4ce7a7b7f454dc47efd591be71` |
| TWRP 3.7.0 with footer | `dcf3d423dca32e35c4a413f99f2890ffd128b6550b395db277833720321bf19f` |
| ROM ZIP | `defb8f363768b0b146f502538a8a7be4a1cc2e9522418cee179239028f96432b` |
| Unrooted boot with footer | `6a7656bceee64b7383277995e5e185f5a36f9d9c94138a2835a3cd08eefefbbb` |
| This user's Magisk boot with footer | `3670525c3d873276a4af4ce586ea59df1707968901420d71afc9f2ead59815c9` |

The last hash applies only to this user's particular output; other patching runs may produce different hashes. These hashes were computed locally. The MIUI aboot was additionally checked for ELF segment hashes, Qualcomm RSA signature and certificate chain. The ROM publisher claims backported security patches, but their coverage was not audited; the build date is not proof of a complete security patch level.

## Troubleshooting and rollback

- **900E or failure to boot:** inspect actual partition contents, the aboot version and footer. Do not repeatedly format Data.
- **EDL Status 21 or a partial write:** this phone was successfully rewritten using the padded 1 MiB aboot and 16 KiB payload, then read back. Failure does not mean nothing was written. emmcdl 2.15 produced inconsistent large-partition reads on this device; 2.16 was reliable.
- **Missing fingerprint settings:** after reconnecting the sensor cable, its HAL was found stopped. The user subsequently reported recovery, but the exact recovery action was not recorded. Declared hardware features/properties alone do not prove a working sensor.
- **Stock rollback:** use only this device's backups and verify full readbacks. Restoring aboot/recovery alone does not restore the modified system/cust/metadata/data. The original aboot rejects the current custom boot; do not mix them as a working configuration.

```powershell
& $edl -p $port -f $loader -MaxPayloadSizeToTargetInBytes 16384 -b aboot .\local-only\backups\aboot.bin
& $edl -p $port -f $loader -MaxPayloadSizeToTargetInBytes 16384 -b recovery .\local-only\backups\recovery-original.bin
```

Every fixed `dd count` and hash above belongs to the specified file. Recalculate them when changing images.
