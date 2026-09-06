# Verified preserved-blob dependency checks

Run [33999461192](https://github.com/cmdr-chara/proprietary_vendor_xiaomi_malachite/actions/runs/33999461192) passed the payload/build-file preservation check, all eight tests and all five real-blob audits. Tool revision: `d689c2ee59be2f48f431fe6c7cbf7a9e45ef55a4`; PR test merge: `b19c8b0c84a74396638b8c89aac1b0052b07de83`.

Artifact `9979047359` was downloaded and its archive SHA-256 independently verified as `1492e08a634723c7fd7f2ff6195ecd624b25993961f641f3686d594291d0021b`. Each reported Git blob hash also matched the collected vendor tree at `28a87d5dda2c787dc839e76162ded180d59d5d42`.

All paths below are under `proprietary/vendor/lib64/`.

| Library | Bytes | SHA-256 | Selected dependency contract |
| --- | ---: | --- | --- |
| libmicamera_hal_core.so | 4871849 | `988b31e4a7a264fcb3559fe5e9f11a203128f8c4a06296a1f6944b4547092207` | PASS |
| libmialgoengine.so | 1241617 | `a63f3692c5f54e73156ceed45c6c6b52d28ca65b7b1d13c52c394f3586b64c2b` | PASS |
| libcodec2_fsr.so | 186288 | `3331686b047d65424908f89a10abecfde00345ee14e90b2c826abe475451a9aa` | PASS |
| hw/audio.primary.mt6878.so | 4778137 | `9db8d7b95304fd7ad964f7f8ddf300f02384fc8752acda3b701bced21bbf2ff9` | PASS |
| hw/vendor.mediatek.hardware.pq_aidl-impl.so | 935169 | `f92e0d6a4745fa7b0f6c835aa769866732bcbce869d21c391087d06582a1199b` | PASS |

No required dependency was missing and no explicitly forbidden old dependency was present. The inspector used GNU readelf 2.42; fixtures used Ubuntu Clang/LLD 18.1.3. The first CI attempt stopped because the fixture linker was absent; the follow-up installed the missing host dependency and reran, without skipping tests or changing blob assertions.

These are source-review checks only. Provider symbols, linker namespaces, full ELF ABI, binary patch correctness, OS3 compatibility, camera/audio runtime and physical-device validation remain GAP. The OS2 userspace baseline is retained; no binary or generated build metadata was changed. See [ELF_CONTRACTS.md](ELF_CONTRACTS.md) to reproduce the audit.
