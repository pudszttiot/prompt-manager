[app]
title = Prompt Manager
package.name = promptmanager
package.domain = org.example
source.dir = .
source.include_exts = py,html,db
source.exclude_dirs = .github,bin,.buildozer
version = 0.1
requirements = python3,flask,sqlite3
orientation = portrait
fullscreen = 0

# Needed to load Bootstrap from the CDN.
android.permissions = INTERNET
android.api = 33
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True

# Show a WebView and run main.py (Flask) in the background.
p4a.bootstrap = webview
p4a.port = 5000

[buildozer]
log_level = 2
warn_on_root = 1
