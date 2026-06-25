# Consulta de Desenhos — SMB puro Python

Consulta PDFs em servidor SMB/Samba diretamente do tablet Android.  
**Sem Java, sem JCIFS-NG, sem ClassNotFoundException.**

## Estrutura do projeto

```
apk_desenho/
├── main.py           ← App principal (Kivy + smbprotocol)
├── main.kv           ← Layout da tela
├── buildozer.spec    ← Configuração do build
└── README.md
```

## Como fazer o build

### Pré-requisitos (Linux / WSL / GitHub Actions)

```bash
pip install buildozer
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
```

### Build

```bash
cd apk_desenho
buildozer android debug
```

O APK gerado fica em `bin/consultadesenhos-1.0.0-arm64-v8a-debug.apk`.

### Instalar no tablet

```bash
adb install bin/consultadesenhos-1.0.0-arm64-v8a-debug.apk
```

## Por que funciona agora

A versão anterior usava `SmbDownloader.java` via `pyjnius` (JNI).  
O Buildozer não compilava o Java corretamente → `ClassNotFoundException`.

Esta versão usa **`smbprotocol`**, uma biblioteca Python pura que faz  
o protocolo SMB2/SMB3 diretamente — sem nenhum código Java.

## Configurações fixas (main.py)

| Parâmetro | Valor |
|-----------|-------|
| Servidor | 192.168.2.2 |
| Porta | 445 |
| Share | DADOS |
| Pasta | IBERO/Publico/BASE DE CONHECIMENTO |
| Domínio | iberoeq.local |

O usuário e a senha são digitados no app a cada uso e não são salvos.
