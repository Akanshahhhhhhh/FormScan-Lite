"""
FormScan-Lite status check.
Put this file in the project root (the folder containing frontend/ and backend/), then run:
    python check_status.py
"""
import os
import subprocess
import importlib.util
import urllib.request
import urllib.error

OK, NO = "[OK]     ", "[MISSING]"


def check(label, condition):
    print(f"  {OK if condition else NO} {label}")
    return condition


def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, shell=True).stdout.strip()
    except Exception:
        return ""


print(f"\nChecking folder: {os.getcwd()}")

print("\n=== 1. GIT / GITHUB ===")
if check("Git repo initialised", os.path.isdir(".git")):
    print(f"           Current branch : {run('git branch --show-current') or '?'}")
    print(f"           Remote (GitHub): {run('git remote get-url origin') or 'none set'}")
    print(f"           Branches       : {run('git branch -a').replace(chr(10), ', ') or 'none'}")
    print(f"           Last commit    : {run('git log -1 --format=%h_%s_(%cr)') or 'no commits yet'}")
    changes = run("git status --porcelain")
    print(f"           Uncommitted    : {len(changes.splitlines()) if changes else 0} file(s)")

print("\n=== 2. TOOLS ===")
node_v, npm_v, py_v = run("node -v"), run("npm -v"), run("python --version")
check(f"Node.js ({node_v or 'not found'}) - need v18 or newer", bool(node_v))
check(f"npm ({npm_v or 'not found'})", bool(npm_v))
check(f"Python ({py_v or 'not found'})", bool(py_v))
check(f"Git ({run('git --version') or 'not found'})", bool(run("git --version")))

print("\n=== 3. FRONTEND (Akansha) ===")
fe = "frontend"
check("frontend/ folder", os.path.isdir(fe))
check("frontend/.env (copied from .env.example)", os.path.isfile(f"{fe}/.env"))
check("node_modules (npm install done)", os.path.isdir(f"{fe}/node_modules"))
for f in ["package.json", "vite.config.js", "index.html",
          "src/main.jsx", "src/App.jsx", "src/App.css",
          "src/utils/constants.js", "src/services/api.js",
          "src/components/Navbar.jsx", "src/components/TabContainer.jsx",
          "src/components/LanguageSelect.jsx", "src/components/ConfidenceBar.jsx",
          "src/components/AudioPlayer.jsx", "src/components/FeedbackButtons.jsx",
          "src/components/Tab1_ReadDocument.jsx", "src/components/Tab2_Translate.jsx",
          "src/components/Tab3_FAQBot.jsx"]:
    check(f, os.path.isfile(f"{fe}/{f}"))

print("\n=== 4. BACKEND (Neharin) ===")
be = "backend"
check("backend/ folder", os.path.isdir(be))
for f in ["app.py", "requirements.txt",
          "services/ocr_service.py", "services/translation_service.py",
          "services/tts_service.py", "services/faq_service.py"]:
    check(f, os.path.isfile(f"{be}/{f}"))
faq_dir = f"{be}/data/faqs"
faqs = os.listdir(faq_dir) if os.path.isdir(faq_dir) else []
check(f"FAQ JSON files ({len(faqs)} found)", len(faqs) > 0)

print("\n=== 5. BACKEND RUNNING? ===")
try:
    urllib.request.urlopen("http://localhost:5000/api/health", timeout=2)
    check("Flask server on localhost:5000", True)
except urllib.error.HTTPError:
    check("Flask server on localhost:5000 (responding, but /api/health missing)", True)
except Exception:
    check("Flask server on localhost:5000 (not running - fine, use demo mode)", False)

print("\nDone. Paste this whole output back to Claude.\n")
