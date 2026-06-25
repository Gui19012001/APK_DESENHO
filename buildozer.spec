[app]
title = Teste Desenho Solid Explorer
package.name = testedesenhosolid
package.domain = br.com.ibero

source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,json,txt,env,pdf
source.exclude_dirs = .git,.github,__pycache__,bin,.buildozer,venv,.venv

version = 0.1.0

requirements = python3,kivy,pyjnius

orientation = portrait
fullscreen = 0

# O APK não lê o compartilhamento diretamente; ele chama o Solid Explorer.
android.permissions = INTERNET
android.api = 34
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True

p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 0
