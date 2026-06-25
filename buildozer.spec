[app]
title = Teste Desenho SMB
package.name = testedesenhosmb
package.domain = br.com.suaempresa

source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,json,txt,java
source.exclude_dirs = .git,.github,__pycache__,bin,.buildozer,venv,.venv

version = 0.4.0

requirements = python3,kivy,pyjnius,androidstorage4kivy

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 34
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True

android.gradle_dependencies = eu.agno3.jcifs:jcifs-ng:2.1.10
android.add_src = android_src

p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 0
