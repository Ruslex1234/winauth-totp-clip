# Repository: `winauth-totp-clip`

A tiny CLI to search a WinAuth-style export for an `otpauth://` entry by nickname, generate the current TOTP code, and copy **only** the code to your clipboard. Prints a green box on success and a red box on failure.

---

## Repo structure
```
winauth-totp-clip/
├─ README.md
├─ LICENSE
├─ requirements.txt
├─ .gitignore
├─ src/
│  └─ totp_clip.py
├─ sample/
│  └─ winauth_export.txt
└─ scripts/
   └─ install.sh
```

---

## README.md
```markdown
# winauth-totp-clip

Search a text export containing `otpauth://totp/...` URIs, generate a TOTP for the first nickname match, and copy the code to your clipboard.

## Why
Use a WinAuth-style export outside of WinAuth. Keep it simple. Keep it local. No network.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Linux you can optionally install `xclip` for fast clipboard support:
```bash
# Debian/Ubuntu
sudo apt-get update && sudo apt-get install -y xclip
# Fedora
sudo dnf install -y xclip
```

macOS and Windows are supported via `pyperclip` fallback.

## Usage

```bash
python3 src/totp_clip.py <file_path> <search_text>
```

Example:
```bash
python3 src/totp_clip.py sample/winauth_export.txt bank
```

If a matching nickname is found, the current 6 digit TOTP will be copied to your clipboard and a green box will be printed. If no match is found, a red box will be printed.

## File format
Each line should contain an `otpauth://` URI like:
```
otpauth://totp/Nickname?secret=BASE32SECRET&digits=6&icon=WinAuth
```
Only `Nickname` and `secret` are required by this tool. `digits` defaults to 6 if missing.

## Security notes
- **Do not commit real secrets**. Use the provided `sample/winauth_export.txt` only for testing.
- Limit file permissions: `chmod 600 your_export.txt`.
- Consider encrypting the export with `age` or `gpg` when at rest.

## License
MIT
```

---

## LICENSE
```text
MIT License

Copyright (c) 2025 Rodney Rosario

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## requirements.txt
```text
pyotp>=2.9.0
pyperclip>=1.8.2
```

---

## .gitignore
```gitignore
# Python
__pycache__/
*.pyc
.venv/
.env

# Editors
.vscode/
.idea/

# Mac
.DS_Store
```

---

## src/totp_clip.py
```python
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
```

---

## sample/winauth_export.txt
```text
otpauth://totp/BankPrimary?secret=JBSWY3DPEHPK3PXP&digits=6&icon=WinAuth
otpauth://totp/EmailGmail?secret=KBKQK3TPOEBXG6DU&digits=6&icon=WinAuth
otpauth://totp/GithubMain?secret=KRUGS4ZANFZSAYJA&digits=6&icon=WinAuth
otpauth://totp/AWSRootAccount?secret=JBSWY3DPFQQFO33S&digits=6&icon=WinAuth
otpauth://totp/AzureTenant?secret=ONSWG4TFOQ======&digits=6&icon=WinAuth
otpauth://totp/OktaSso?secret=KRSXG5DSMFZGK4TQ&digits=6&icon=WinAuth
otpauth://totp/SlackWorkspace?secret=JBSWY3DPO5XXE3DE&digits=6&icon=WinAuth
otpauth://totp/Cloudflare?secret=MFRGGZDFMZTWQ2LK&digits=6&icon=WinAuth
otpauth://totp/ProtonMail?secret=KRSXG5A=OQ======&digits=6&icon=WinAuth
otpauth://totp/Bitwarden?secret=JBSWY3DPEHPK3PXP&digits=6&icon=WinAuth
```

> These secrets are placeholders for testing and not valid. Replace with your own export. Keep this file out of version control.

---

## scripts/install.sh
```bash
#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update && sudo apt-get install -y xclip || true
fi

echo "Install complete. Run: source .venv/bin/activate && python3 src/totp_clip.py sample/winauth_export.txt bank"
```

---

## Notes
- If you absolutely want to use `xclip` only like your original snippet, it will work fine on Linux. The script already prefers native tools, then falls back to `pyperclip`.
- For Windows PowerShell, you can pipe the code to the clipboard using `clip`. For macOS, `pbcopy` is used automatically if present.
- The tool stops at the **first** match. If you need multiple matches, we can extend it to present a numbered menu.
