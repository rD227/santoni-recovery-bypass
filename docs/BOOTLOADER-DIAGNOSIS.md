# Santoni diagnosis — 2026-10-01

RedWolf survived the attempted boot unchanged, with SHA-256 D411149E3C87C5BCE464D3C36CF3B20E66EA40099F119038775DA89D0CB9E164. The device's original aboot hash is 1C498A6445E05DDE5C0165E98A62F1007475B5EABE13570B31938C8040BCCA38.

IDA analysis of the original bootloader shows that `sub_8F6109D0` calls the DER length parser `sub_8F610120`. The footer `30 83 19 89 64` declares a content length of 0x198964; the parser returns that plus its five header bytes. When this exceeds the signature buffer size, the original verifier calls the panic function `sub_8F635CC8`. This provides a code-level explanation for the 900E behavior; no device UART trace has been collected.

The unmodified MIUI 11 V11.0.2.0.NAMMIXM bootloader differs: `sub_8F60FF68` returns 0 on the oversized-signature path without calling `sub_8F60F5D8`, which would set the verified-boot state to red. This is a candidate for the Appender method; device boot compatibility remains untested.

Source: https://xmfirmwareupdater.com/firmware/santoni/stable/V11.0.2.0.NAMMIXM/

The downloaded firmware ZIP MD5 is 9fb119dafdcd7ceb9d9148e26a44b08d, matching the publication. The extracted emmc_appsboot.mbn SHA-256 is 28A2F559B7C56C9565DA334E21B78D5A94BF0179417D895FAF0A2688A5ECBEB3.

Offline verification passed for ELF segment hashes, the Qualcomm RSA signature over the signed hash table, and both certificate-chain signatures. The original and candidate use the same Xiaomi root and intermediate CA and the same SW_ID 9, HW_ID 0006B0E100000000, OEM_ID 0000 and MODEL_ID 0000. These checks do not guarantee compatibility with all installed firmware components.

Before the bootloader write, aboot was read twice with identical hashes. abootbak also matched the original. These backups are in redwolf-failure-20261001-102409.

The attempted main-aboot write with the original 557576-byte MBN and 1 MiB payload returned Firehose raw-mode ACK, then Status 21 (device not ready). The extent of any write is unknown. No further device commands were issued afterwards. abootbak was not written.

The retry candidate aboot-miui11-signed-1MiB.bin preserves the original signed file byte-for-byte and adds zero padding to exactly 1048576 bytes. Retry only after a fresh EDL power cycle, with a 16384-byte payload, followed by complete readback verification. Do not boot the phone before completing or rolling back this write.

## Completed retry

After a fresh EDL entry on COM41, the main aboot was read before retry. Its SHA-256 was 8AC0D680B1B9B3B97B2E040FEA241FBDF26AEE294370CB292FCE7F73EACEECD8, matching neither the original partition nor the complete candidate. The previous failed write had changed the partition.

The sector-aligned 1 MiB candidate was then successfully written using a 16384-byte payload. Firehose returned ACK and Status 0. Complete readback matched the candidate byte-for-byte: B659E08B40B95A50418295AA98B5BD0EE72F7F4CE7A7B7F454DC47EFD591BE71.

Post-write checks also verified that abootbak remained unchanged and the RedWolf recovery image was still present byte-for-byte. Boot behavior is pending the user's physical boot attempt. This does not constitute a true bootloader unlock.

Executed write command (run from this kit directory):

```powershell
.\emmcdl-2.16.exe -p COM41 -f .\prog_emmc_firehose_8937_ddr.mbn -MaxPayloadSizeToTargetInBytes 16384 -b aboot .\aboot-miui11-signed-1MiB.bin
```

Readback command:

```powershell
.\emmcdl-2.16.exe -p COM41 -f .\prog_emmc_firehose_8937_ddr.mbn -MaxPayloadSizeToTargetInBytes 16384 -d 786432 2048 -o .\redwolf-failure-20261001-102409\aboot-miui11-verified.bin
```

Original main aboot is available in `redwolf-failure-20261001-102409/aboot-before-a.bin` and `aboot-before-b.bin`; original backup bootloader is `abootbak-before.bin`. All three had the same hash before the update.
