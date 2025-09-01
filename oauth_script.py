import argparse
import os
import re
import subprocess
import sys
from typing import Optional

import pyotp

try:
    import pyperclip  # Fallback clipboard
    PYPERCLIP_AVAILABLE = True
except Exception:
    PYPERCLIP_AVAILABLE = False


GREEN = "\033[42m"
RED = "\033[41m"
RESET = "\033[0m"


def print_colored_box(success: bool) -> None:
    color = GREEN if success else RED
    # 40 spaces wide block
    print(f"{color}{' ' * 40}{RESET}")


def copy_to_clipboard(text: str) -> bool:
    """
    Try platform native methods first then fall back to pyperclip.
    Returns True if something succeeded.
    """
    # Linux: xclip
    if shutil_which("xclip"):
        try:
            p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
            p.communicate(input=text.encode())
            return p.returncode == 0
        except Exception:
            pass

    # macOS: pbcopy
    if shutil_which("pbcopy"):
        try:
            p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            p.communicate(input=text.encode())
            return p.returncode == 0
        except Exception:
            pass

    # Windows: clip
    if os.name == "nt" and shutil_which("clip"):
        try:
            p = subprocess.Popen(["clip"], stdin=subprocess.PIPE)
            p.communicate(input=text.encode())
            return p.returncode == 0
        except Exception:
            pass

    # Fallback: pyperclip
    if PYPERCLIP_AVAILABLE:
        try:
            pyperclip.copy(text)
            return True
        except Exception:
            pass

    return False


def shutil_which(cmd: str) -> Optional[str]:
    # tiny which implementation to avoid importing shutil for one call
    path = os.environ.get("PATH", "")
    exts = [""]
    if os.name == "nt":
        pathext = os.environ.get("PATHEXT", ".EXE;.BAT;.CMD").split(";")
        exts = pathext
    for directory in path.split(os.pathsep):
        candidate = os.path.join(directory, cmd)
        for ext in exts:
            file_path = candidate + ext
            if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
                return file_path
    return None


def parse_first_match(line: str, needle: str) -> Optional[dict]:
    # Match otpauth://totp/<label>?secret=<base32>&digits=<n>
    m = re.search(r"otpauth://totp/([^?]+)\?([^\s]+)", line, re.IGNORECASE)
    if not m:
        return None

    label = m.group(1)
    if needle.lower() not in label.lower():
        return None

    # Parse query string manually to avoid urlparse import
    query = m.group(2)
    params = {}
    for kv in query.split("&"):
        if "=" in kv:
            k, v = kv.split("=", 1)
            params[k.lower()] = v

    secret = params.get("secret")
    if not secret:
        return None
    digits = int(params.get("digits", 6))

    return {"label": label, "secret": secret, "digits": digits}


def search_and_generate_oauth(file_path: str, search_text: str) -> bool:
    with open(file_path, "r", encoding="utf-8") as f:
        for raw in f:
            data = parse_first_match(raw, search_text)
            if not data:
                continue
            totp = pyotp.TOTP(data["secret"], digits=data["digits"])
            code = totp.now()
            copied = copy_to_clipboard(str(code))
            print_colored_box(copied)
            if not copied:
                # As a last resort, print the code to STDOUT so the user can copy it
                print(str(code))
            return True
    print_colored_box(False)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Search a WinAuth-style export and copy current TOTP for the first matching nickname.")
    parser.add_argument("file_path", help="Path to file containing otpauth lines")
    parser.add_argument("search_text", help="Nickname or substring to match in the label")
    args = parser.parse_args()

    if not os.path.isfile(args.file_path):
        print(f"File not found: {args.file_path}")
        return 1

    ok = search_and_generate_oauth(args.file_path, args.search_text)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
