# Vendor artifact agent instructions

## Provenance and compatibility

- Treat `proprietary/` as opaque payload, not ordinary editable source. Documentation/tooling changes must preserve its bytes and existing generated build declarations.
- Intentional blob changes need an approved source, exact input/output hashes, and reproducible extraction/fixup provenance. Keep build declarations synchronized with the selected device repository's extraction rules.
- Preserve Git LFS rules and distinguish pointer files from retrieved payload. A Git commit alone does not prove that every required LFS object was published or inspected.
- Keep camera/audio/graphics dependencies coherent with their actual providers, namespaces, symbols, and platform ABI. Dependency-name matches alone do not prove runtime compatibility.
- Do not run inspected binaries through `ldd`, `dlopen`, or a device as part of a static audit. Never mix firmware/regions or replace userspace merely to hide an unresolved dependency error.

## Guidance and verification

[ELF_CONTRACTS.md](ELF_CONTRACTS.md) defines the focused read-only audit and prerequisites; [ELF_RESULTS.md](ELF_RESULTS.md) records results for specific inputs. Use `python3 -m unittest discover -s tests -v` for audit-tool changes with its Clang/LLD/readelf prerequisites. Missing tools or payloads are explicit gaps, not passing checks.

Retain metadata and hashes rather than private dumps or unnecessary binary copies. Keep agent guidance outside payload directories.

Completion requires verified payload preservation or a documented intentional replacement, affected extraction/build/ELF contracts checked, and exact evidence limits. Static PASS is not camera, DRM, firmware, boot, or release certification; no physical-device operation is authorized by this file.
