[app]
title = Consulta Desenhos
package.name = consultadesenhos
package.domain = br.com.iberoeq
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,json,txt
source.exclude_dirs = .git,.github,__pycache__,bin,.buildozer,venv,.venv,android_src
version = 1.0.0

# === DEPENDÊNCIAS — Python puro, sem Java ===
# smbprotocol: acesso SMB/CIFS direto via Python
# androidstorage4kivy: abrir PDF pelo ShareSheet do Android
requirements = python3,kivy==2.3.0,smbprotocol,androidstorage4kivy

orientation = portrait
fullscreen = 0

# === PERMISSÕES ===
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE

# === ANDROID ===
android.api = 34
android.minapi = 26
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True

# Sem android.add_src — não há mais código Java
# Sem android.gradle_dependencies — não há mais JCIFS-NG

[buildozer]
log_level = 2
warn_on_root = 0
