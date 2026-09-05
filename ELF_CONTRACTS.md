# Preserved vendor ELF dependency contracts

The Android userspace baseline remains `28a87d5dda2c787dc839e76162ded180d59d5d42`.
No proprietary bytes or generated build metadata are changed by this audit.

Run on a Linux host with Python 3 and GNU readelf:

```sh
python3 -m unittest discover -s tests -v
python3 tools/audit_elf_contracts.py > vendor-elf-contracts.json
```

Tests additionally require Clang and LLD to produce a freestanding ARM64 shared
library fixture. They never run the fixture. CI sparsely checks out only the five
selected proprietary files plus the test/tool sources. It verifies payload and
generated-build paths against the original Git commit before inspecting them.

The checker records SHA-256, Git blob identity and DT_NEEDED names for the camera
core, camera algorithm engine, Codec2 FSR, primary audio and PQ implementation.
Required replacement/shim names and forbidden old names come from the unchanged
`extract-files.py` at device commit `0f54832a13d8b4a79328c96025e3aac73b124ba8`,
corroborated by this vendor tree's generated Android.bp declarations.

A failure identifies the exact missing/old dependency name; it is not a reason
to replace blobs with OS3 files or downgrade/cross-flash firmware. Preserve the
historical OS2.0.208.0.VOOMIXM userspace policy. The remaining proprietary
libraries are outside this focused audit.

PASS proves only the selected header and dependency-name contracts. It does not
prove the providers' symbols/versions, linker namespaces, GraphicBuffer binary
patch offsets, platform ABI, hardware camera behavior, DRM, or firmware
compatibility. Runtime compatibility remains GAP and release status BLOCKED,
even if every selected dependency name matches. No ldd/dlopen, module loading,
phone command or binary patching is used. Artifacts contain metadata, not blobs.
