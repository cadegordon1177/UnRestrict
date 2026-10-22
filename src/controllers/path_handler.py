import os


def fix_windows_path(path: str) -> str:
    # On Windows, temporary paths use backslashes which break some of the
    # restore tooling. UnRestrict is macOS-only, so this is a no-op there,
    # but the helper is kept for parity with the upstream codebase.
    if os.name == "nt":
        return path.replace("/", "\\")
    return path
