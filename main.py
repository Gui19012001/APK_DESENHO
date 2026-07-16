# -*- coding: utf-8 -*-
"""
Teste Android - Consulta de Desenho por SMB

Fluxo:
1) APK conecta direto na pasta de rede SMB por IP.
2) Procura PDF pelo código informado.
3) Baixa o PDF para o tablet.
4) Abre o PDF pelo visualizador padrão do Android.

Biblioteca SMB: pysmb
"""

from __future__ import annotations

import io
import json
import os
import re
import tempfile
import threading
from dataclasses import dataclass, asdict
from pathlib import PurePosixPath

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

try:
    from smb.SMBConnection import SMBConnection
except Exception:  # pragma: no cover
    SMBConnection = None

try:
    import smbclient
except Exception:  # pragma: no cover
    smbclient = None


APP_TITLE = "Teste Desenho SMB"
CONFIG_FILE = "config_smb.json"


@dataclass
class SmbConfig:
    server_ip: str = "192.168.2.2"
    server_name: str = "192.168.2.2"  # pode ser o nome real do servidor, se o TI passar
    share: str = "IBERO"
    remote_path: str = "Publico/BASE DE CONHECIMENTO"
    domain: str = "iberoeq.local"
    username: str = ""
    password: str = ""
    port: int = 445
    use_direct_tcp: bool = True
    backend: str = "auto"  # auto, pysmb ou smbprotocol


def clean_code(value: str) -> str:
    value = (value or "").strip()
    value = value.replace("/", "-")
    value = re.sub(r"[^A-Za-z0-9_.\-]", "", value)
    return value


def normalize_remote_path(path: str) -> str:
    path = (path or "").replace("\\", "/").strip().strip("/")
    return path or "/"


def smb_path_variants(path: str) -> list[str]:
    """Return path spellings accepted by different SMB servers/pysmb builds."""
    normalized = normalize_remote_path(path)
    if normalized == "/":
        return ["/"]

    variants = [
        f"/{normalized}",
        normalized,
        "\\" + normalized.replace("/", "\\"),
        normalized.replace("/", "\\"),
    ]
    unique: list[str] = []
    for item in variants:
        if item not in unique:
            unique.append(item)
    return unique


def share_path_candidates_for_config(config: SmbConfig, path: str) -> list[tuple[str, str]]:
    """Try configured share first, then path-first-segment as share fallback."""
    share = (config.share or "").strip().strip("/\\")
    normalized = normalize_remote_path(path)
    candidates: list[tuple[str, str]] = []

    for path_variant in smb_path_variants(normalized):
        candidates.append((share, path_variant))

    parts = [part for part in normalized.split("/") if part]
    if len(parts) >= 2:
        fallback_share = parts[0]
        fallback_path = "/".join(parts[1:])
        if fallback_share.lower() != share.lower():
            for path_variant in smb_path_variants(fallback_path):
                candidates.append((fallback_share, path_variant))

    unique: list[tuple[str, str]] = []
    for candidate in candidates:
        if candidate not in unique:
            unique.append(candidate)
    return unique


def join_remote(base: str, name: str) -> str:
    base = normalize_remote_path(base)
    if base == "/":
        return f"/{name}"
    return str(PurePosixPath(base) / name)


class AndroidFileHelper:
    """Salva e abre PDF no Android usando MediaStore quando possível.

    No PC, salva em pasta temporária e usa os.startfile/open equivalente.
    """

    @staticmethod
    def running_on_android() -> bool:
        return os.environ.get("ANDROID_ARGUMENT") is not None

    @staticmethod
    def save_and_open_pdf(data: bytes, filename: str) -> str:
        filename = filename if filename.lower().endswith(".pdf") else f"{filename}.pdf"

        if AndroidFileHelper.running_on_android():
            return AndroidFileHelper._save_and_open_android(data, filename)

        return AndroidFileHelper._save_and_open_desktop(data, filename)

    @staticmethod
    def _save_and_open_desktop(data: bytes, filename: str) -> str:
        folder = os.path.join(tempfile.gettempdir(), "desenhos_ibero")
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, filename)
        with open(path, "wb") as f:
            f.write(data)

        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                import subprocess
                subprocess.Popen(["xdg-open", path])
        except Exception:
            pass

        return path

    @staticmethod
    def _save_and_open_android(data: bytes, filename: str) -> str:
        from jnius import autoclass

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Intent = autoclass("android.content.Intent")
        Build = autoclass("android.os.Build")
        Environment = autoclass("android.os.Environment")
        MediaStore = autoclass("android.provider.MediaStore")
        ContentValues = autoclass("android.content.ContentValues")

        activity = PythonActivity.mActivity
        resolver = activity.getContentResolver()

        # Android 10+ salva em Downloads/DesenhosIbero via MediaStore.
        if Build.VERSION.SDK_INT >= 29:
            values = ContentValues()
            values.put(MediaStore.MediaColumns.DISPLAY_NAME, filename)
            values.put(MediaStore.MediaColumns.MIME_TYPE, "application/pdf")
            values.put(
                MediaStore.MediaColumns.RELATIVE_PATH,
                Environment.DIRECTORY_DOWNLOADS + "/DesenhosIbero",
            )

            uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values)
            if uri is None:
                raise RuntimeError("Não foi possível criar arquivo em Downloads via MediaStore.")

            stream = resolver.openOutputStream(uri)
            if stream is None:
                raise RuntimeError("Não foi possível abrir stream de gravação do PDF.")
            stream.write(data)
            stream.flush()
            stream.close()

            intent = Intent(Intent.ACTION_VIEW)
            intent.setDataAndType(uri, "application/pdf")
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            activity.startActivity(intent)
            return "Downloads/DesenhosIbero/" + filename

        # Android antigo: grava no Downloads público.
        File = autoclass("java.io.File")
        FileOutputStream = autoclass("java.io.FileOutputStream")
        Uri = autoclass("android.net.Uri")

        downloads = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS)
        folder = File(downloads, "DesenhosIbero")
        folder.mkdirs()
        out_file = File(folder, filename)
        fos = FileOutputStream(out_file)
        fos.write(data)
        fos.flush()
        fos.close()

        uri = Uri.fromFile(out_file)
        intent = Intent(Intent.ACTION_VIEW)
        intent.setDataAndType(uri, "application/pdf")
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        activity.startActivity(intent)
        return out_file.getAbsolutePath()


@dataclass
class RemoteEntry:
    filename: str
    isDirectory: bool


class SmbProtocolDrawingClient:
    """SMB2/SMB3 client based on smbprotocol/smbclient when packaged."""

    def __init__(self, config: SmbConfig):
        if smbclient is None:
            raise RuntimeError(
                "Biblioteca smbprotocol não está instalada no APK. "
                "Verifique requirements=smbprotocol,pyspnego,cryptography."
            )
        self.config = config
        self.effective_share = config.share
        self.connected = False

    def connect(self):
        cfg = self.config
        username = cfg.username
        if cfg.domain and "\\" not in username and "@" not in username:
            username = f"{cfg.domain}\\{username}"
        smbclient.register_session(
            cfg.server_ip,
            username=username,
            password=cfg.password,
            port=int(cfg.port),
            encrypt=False,
            connection_timeout=20,
        )
        self.connected = True
        return self

    def close(self):
        try:
            smbclient.reset_connection_cache()
        except Exception:
            pass

    def share_path_candidates(self, path: str) -> list[tuple[str, str]]:
        return share_path_candidates_for_config(self.config, path)

    def _unc(self, share: str, path: str) -> str:
        normalized = normalize_remote_path(path)
        if normalized == "/":
            return rf"\\{self.config.server_ip}\{share}"
        return rf"\\{self.config.server_ip}\{share}\{normalized.replace('/', '\\')}"

    def list_path_safe(self, path: str):
        errors: list[str] = []
        for share, candidate_path in self.share_path_candidates(path):
            try:
                unc = self._unc(share, candidate_path)
                names = smbclient.listdir(unc)
                entries: list[RemoteEntry] = []
                for name in names:
                    if name in (".", ".."):
                        continue
                    child_unc = unc.rstrip("\\") + "\\" + name
                    try:
                        is_dir = smbclient.path.isdir(child_unc)
                    except Exception:
                        is_dir = False
                    entries.append(RemoteEntry(filename=name, isDirectory=is_dir))
                self.effective_share = share
                return entries
            except Exception as exc:
                errors.append(f"{share}:{candidate_path} -> {exc}")
        raise RuntimeError(self._format_smb_error(path, errors))

    def _format_smb_error(self, path: str, errors: list[str]) -> str:
        detail = "\n".join(errors[-4:]) if errors else "erro desconhecido"
        return (
            f"Falha SMB3/smbprotocol ao listar '{path}' no share '{self.config.share}'.\n"
            f"Tentativas:\n{detail}\n"
            "Confirme usuário, senha, domínio, nome do share e liberação da porta 445."
        )

    def retrieve_file(self, remote_path: str) -> bytes:
        share = self.effective_share or self.config.share
        path = self._path_for_share(remote_path, share)
        unc = self._unc(share, path)
        with smbclient.open_file(unc, mode="rb") as fd:
            return fd.read()

    def _path_for_share(self, remote_path: str, share: str) -> str:
        normalized = normalize_remote_path(remote_path)
        parts = [part for part in normalized.split("/") if part]
        if parts and parts[0].lower() == share.lower():
            return "/".join(parts[1:]) or "/"
        return normalized

    def diagnostic_report(self) -> str:
        lines = ["Diagnóstico SMB3/smbprotocol:"]
        for share, path in self.share_path_candidates(self.config.remote_path):
            try:
                items = self.list_path_safe(path)
                lines.append(f"OK: share={self.effective_share} caminho={path} itens={len(items)}")
                break
            except Exception as exc:
                lines.append(f"FALHOU: share={share} caminho={path} erro={exc}")
        return "\n".join(lines)

    def find_pdf(self, code: str) -> str | None:
        return find_pdf_with_client(self, code)


class SmbDrawingClient:
    def __init__(self, config: SmbConfig):
        if SMBConnection is None:
            raise RuntimeError("Biblioteca pysmb não está instalada. Verifique requirements=pysmb.")
        self.config = config
        self.conn = None
        self.effective_share = config.share

    def connect(self):
        cfg = self.config
        self.conn = SMBConnection(
            username=cfg.username,
            password=cfg.password,
            my_name="tablet_ibero",
            remote_name=cfg.server_name or cfg.server_ip,
            domain=cfg.domain or "",
            use_ntlm_v2=True,
            is_direct_tcp=cfg.use_direct_tcp,
        )
        ok = self.conn.connect(cfg.server_ip, int(cfg.port), timeout=20)
        if not ok:
            raise RuntimeError("Não conectou ao servidor SMB.")
        return self.conn

    def close(self):
        try:
            if self.conn:
                self.conn.close()
        except Exception:
            pass

    def share_path_candidates(self, path: str) -> list[tuple[str, str]]:
        return share_path_candidates_for_config(self.config, path)

    def list_path_safe(self, path: str):
        assert self.conn is not None
        errors: list[str] = []
        for share, candidate_path in self.share_path_candidates(path):
            try:
                items = self.conn.listPath(share, candidate_path, timeout=30)
                self.effective_share = share
                return items
            except Exception as exc:
                errors.append(f"{share}:{candidate_path} -> {exc}")
        raise RuntimeError(self._format_smb_error(path, errors))

    def _format_smb_error(self, path: str, errors: list[str]) -> str:
        share = self.config.share
        detail = "\n".join(errors[-4:]) if errors else "erro desconhecido"
        hints = (
            f"Falha ao listar a pasta '{path}' no compartilhamento '{share}'.\n"
            f"Tentativas SMB:\n{detail}\n"
            "Se todas as tentativas falharem, o problema provavelmente é o nome do compartilhamento, "
            "permissão do usuário, remote_name/nome real do servidor, porta 445 bloqueada ou servidor exigindo SMB3."
        )
        return hints

    def retrieve_file(self, remote_path: str) -> bytes:
        assert self.conn is not None
        buffer = io.BytesIO()
        share = self.effective_share or self.config.share
        path = self._path_for_share(remote_path, share)
        self.conn.retrieveFile(share, path, buffer, timeout=60)
        return buffer.getvalue()

    def _path_for_share(self, remote_path: str, share: str) -> str:
        normalized = normalize_remote_path(remote_path)
        parts = [part for part in normalized.split("/") if part]
        if parts and parts[0].lower() == share.lower():
            return "/".join(parts[1:]) or "/"
        return normalized

    def diagnostic_report(self) -> str:
        assert self.conn is not None
        lines = ["Diagnóstico SMB:"]
        for share, path in self.share_path_candidates(self.config.remote_path):
            try:
                items = self.conn.listPath(share, path, timeout=15)
                qtd = len([x for x in items if x.filename not in (".", "..")])
                lines.append(f"OK: share={share} caminho={path} itens={qtd}")
                self.effective_share = share
                break
            except Exception as exc:
                lines.append(f"FALHOU: share={share} caminho={path} erro={exc}")
        return "\n".join(lines)

    def find_pdf(self, code: str) -> str | None:
        return find_pdf_with_client(self, code)


def find_pdf_with_client(client, code: str) -> str | None:
    code_clean = clean_code(code).lower()
    base_path = normalize_remote_path(client.config.remote_path)

    exact_matches: list[str] = []
    starts_matches: list[str] = []
    contains_matches: list[str] = []

    def walk(path: str, depth: int = 0):
        if depth > 10:
            return
        for item in client.list_path_safe(path):
            name = item.filename
            if name in (".", ".."):
                continue
            full = join_remote(path, name)
            if item.isDirectory:
                walk(full, depth + 1)
                continue

            lower_name = name.lower()
            if not lower_name.endswith(".pdf"):
                continue
            stem = lower_name[:-4]
            if stem == code_clean:
                exact_matches.append(full)
            elif stem.startswith(code_clean):
                starts_matches.append(full)
            elif code_clean in stem:
                contains_matches.append(full)

    walk(base_path)

    if exact_matches:
        return sorted(exact_matches)[0]
    if starts_matches:
        return sorted(starts_matches)[0]
    if contains_matches:
        return sorted(contains_matches)[0]
    return None


def create_smb_client(config: SmbConfig):
    backend = (config.backend or "auto").strip().lower()
    if backend == "smbprotocol":
        return SmbProtocolDrawingClient(config)
    if backend == "pysmb":
        return SmbDrawingClient(config)
    if smbclient is not None:
        return SmbProtocolDrawingClient(config)
    return SmbDrawingClient(config)


class Field(BoxLayout):
    def __init__(self, label: str, value: str = "", password: bool = False, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(4), size_hint_y=None, height=dp(72), **kwargs)
        self.add_widget(Label(text=label, size_hint_y=None, height=dp(22), halign="left", valign="middle"))
        self.input = TextInput(text=value, password=password, multiline=False, size_hint_y=None, height=dp(42))
        self.add_widget(self.input)

    @property
    def text(self) -> str:
        return self.input.text.strip()

    @text.setter
    def text(self, value: str):
        self.input.text = value or ""


class SmbTestApp(App):
    def build(self):
        self.title = APP_TITLE
        self.config_data = self.load_config_file()

        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))

        root.add_widget(Label(text="Consulta SMB - Desenhos Ibero", font_size="20sp", bold=True, size_hint_y=None, height=dp(36)))

        scroll = ScrollView(size_hint=(1, 1))
        form = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None)
        form.bind(minimum_height=form.setter("height"))

        self.server_ip = Field("IP do servidor", self.config_data.server_ip)
        self.server_name = Field("Nome do servidor/remote_name", self.config_data.server_name)
        self.share = Field("Compartilhamento", self.config_data.share)
        self.remote_path = Field("Pasta dentro do compartilhamento", self.config_data.remote_path)
        self.domain = Field("Domínio", self.config_data.domain)
        self.port = Field("Porta SMB", str(self.config_data.port))
        self.backend = Field("Modo SMB (auto/pysmb/smbprotocol)", self.config_data.backend)
        self.username = Field("Usuário", self.config_data.username)
        self.password = Field("Senha", self.config_data.password, password=True)
        self.code = Field("Código do desenho/produto", "")

        for w in [self.server_ip, self.server_name, self.share, self.remote_path, self.domain, self.port, self.backend, self.username, self.password, self.code]:
            form.add_widget(w)

        scroll.add_widget(form)
        root.add_widget(scroll)

        buttons = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(52))
        btn_save = Button(text="Salvar config")
        btn_test = Button(text="Testar conexão")
        btn_diag = Button(text="Diagnóstico")
        btn_find = Button(text="Buscar PDF")
        btn_save.bind(on_release=lambda *_: self.save_config_from_ui(show_status=True))
        btn_test.bind(on_release=lambda *_: self.run_thread("test"))
        btn_diag.bind(on_release=lambda *_: self.run_thread("diag"))
        btn_find.bind(on_release=lambda *_: self.run_thread("find"))
        buttons.add_widget(btn_save)
        buttons.add_widget(btn_test)
        buttons.add_widget(btn_diag)
        buttons.add_widget(btn_find)
        root.add_widget(buttons)

        self.status = Label(text="Preencha usuário/senha e teste a conexão.", size_hint_y=None, height=dp(92), halign="left", valign="top")
        self.status.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        root.add_widget(self.status)

        return root

    def config_path(self) -> str:
        return os.path.join(self.user_data_dir, CONFIG_FILE)

    def load_config_file(self) -> SmbConfig:
        try:
            with open(self.config_path(), "r", encoding="utf-8") as f:
                data = json.load(f)
            return SmbConfig(**{**asdict(SmbConfig()), **data})
        except Exception:
            return SmbConfig()

    def save_config_from_ui(self, show_status: bool = False) -> SmbConfig:
        cfg = SmbConfig(
            server_ip=self.server_ip.text,
            server_name=self.server_name.text or self.server_ip.text,
            share=self.share.text,
            remote_path=self.remote_path.text,
            domain=self.domain.text,
            username=self.username.text,
            password=self.password.text,
            port=self._parse_port(),
            backend=self.backend.text or "auto",
        )
        os.makedirs(self.user_data_dir, exist_ok=True)
        with open(self.config_path(), "w", encoding="utf-8") as f:
            json.dump(asdict(cfg), f, ensure_ascii=False, indent=2)
        self.config_data = cfg
        if show_status:
            self.set_status("Configuração salva.")
        return cfg

    def _parse_port(self) -> int:
        try:
            return int(self.port.text or "445")
        except ValueError:
            return 445

    def set_status(self, text: str):
        def update(_dt):
            self.status.text = text
        Clock.schedule_once(update, 0)

    def run_thread(self, mode: str):
        self.save_config_from_ui(show_status=False)
        if mode == "find" and not self.code.text:
            self.set_status("Informe o código do desenho/produto.")
            return
        threading.Thread(target=self.worker, args=(mode,), daemon=True).start()

    def worker(self, mode: str):
        cfg = self.config_data
        client = None
        try:
            self.set_status("Conectando ao servidor SMB...")
            client = create_smb_client(cfg)
            client.connect()

            if mode == "diag":
                self.set_status(client.diagnostic_report())
                return

            if mode == "test":
                base = normalize_remote_path(cfg.remote_path)
                items = client.list_path_safe(base)
                qtd = len([x for x in items if x.filename not in (".", "..")])
                self.set_status(
                    f"Conexão OK. Pasta acessível: {base}\n"
                    f"Share usado: {client.effective_share}\n"
                    f"Itens encontrados: {qtd}"
                )
                return

            code = self.code.text
            self.set_status(f"Conectado. Procurando PDF para: {code}")
            remote_pdf = client.find_pdf(code)
            if not remote_pdf:
                self.set_status(f"PDF não encontrado para o código: {code}")
                return

            self.set_status(f"Encontrado:\n{remote_pdf}\nBaixando...")
            data = client.retrieve_file(remote_pdf)
            filename = os.path.basename(remote_pdf.replace("\\", "/")) or f"{clean_code(code)}.pdf"
            local = AndroidFileHelper.save_and_open_pdf(data, filename)
            self.set_status(f"PDF baixado e enviado para abertura.\nLocal: {local}")

        except Exception as exc:
            self.set_status(f"Erro: {exc}")
        finally:
            if client:
                client.close()


if __name__ == "__main__":
    SmbTestApp().run()
