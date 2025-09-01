# Repository: `winauth-totp-clip`

A tiny CLI to search a WinAuth-style export for an `otpauth://` entry by nickname, generate the current TOTP code, and copy **only** the code to your clipboard. Prints a green box on success and a red box on failure.

---

## Repo structure
```
winauth-totp-clip/
├─ README.md
├─ requirements.txt
├─ oauth_script.py
├─ sample/
│  └─ winauth_export.txt
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
python3 src/oauth_script.py <file_path> <search_text>
```

Example:
```bash
python3 src/oauth_script.py sample/winauth_export.txt bank
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

<p align="center">
  <img width="626" height="220" alt="image" src="https://github.com/user-attachments/assets/f88d9418-b302-451f-969d-0d0276f16763" />
</p>

<p align="center">
  Here is a preview of what it looks like — red means it did not find anything
</p>

---

## Notes
- If you absolutely want to use `xclip` only like your original snippet, it will work fine on Linux. The script already prefers native tools, then falls back to `pyperclip`.
- For Windows PowerShell, you can pipe the code to the clipboard using `clip`. For macOS, `pbcopy` is used automatically if present.
- The tool stops at the **first** match. If you need multiple matches, we can extend it to present a numbered menu.
