[app]
title = Teste Desenho SMB
package.name = testedesenhosmbpy
package.domain = br.com.ibero

source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,json,txt
source.exclude_dirs = .git,.github,__pycache__,bin,.buildozer,venv,.venv

version = 0.1.0

requirements = python3,kivy,pyjnius,pysmb

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 34
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True

# Não usa Java adicional e não usa jcifs.
# A lógica SMB é 100% Python com pysmb.

p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 0
