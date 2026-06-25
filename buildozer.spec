[app]
title = Teste Desenho Pasta Android
package.name = testedesenhosaf
package.domain = br.com.ibero

source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,json,txt,env,pdf
source.exclude_dirs = .git,.github,__pycache__,bin,.buildozer,venv,.venv

version = 0.2.0

requirements = python3,kivy,pyjnius

orientation = portrait
fullscreen = 0

# INTERNET é usado pelo provedor de rede. O acesso à pasta é concedido
# pelo Storage Access Framework; não são necessárias permissões antigas
# de leitura/gravação do armazenamento.
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
