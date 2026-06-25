import os
import re
import threading
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty

SERVER = "192.168.2.2"
PORT = 445
SHARE = "DADOS"
REMOTE_FOLDER = "IBERO/Publico/BASE DE CONHECIMENTO"
DOMAIN = "iberoeq.local"


class DesenhoApp(App):
    status_text = StringProperty(
        "Digite o usuário, a senha e o código do desenho."
    )

    def build(self):
        self.title = "Consulta de Desenhos"
        return Builder.load_file("main.kv")

    def abrir_desenho(self):
        codigo = self.root.ids.codigo.text.strip()
        usuario = self.root.ids.usuario.text.strip()
        senha = self.root.ids.senha.text

        if not codigo:
            self.status_text = "Digite o código do desenho."
            return

        if not re.fullmatch(r"[A-Za-z0-9._() \-]+", codigo):
            self.status_text = (
                "Código inválido. Use letras, números, ponto, hífen ou underline."
            )
            return

        if not usuario:
            self.status_text = "Digite o usuário. Ex: guilherme.cruz"
            return

        if "\\" in usuario or "@" in usuario:
            self.status_text = (
                "Digite somente o usuário sem domínio. Ex: guilherme.cruz"
            )
            return

        if not senha:
            self.status_text = "Digite a senha da rede."
            return

        self.root.ids.botao_abrir.disabled = True
        self.status_text = f"Conectando em {SERVER}:{PORT} e procurando {codigo}.pdf..."

        threading.Thread(
            target=self._consultar_smb,
            args=(codigo, usuario, senha),
            daemon=True,
        ).start()

    def _consultar_smb(self, codigo, usuario, senha):
        try:
            import smbclient
            import smbclient.path

            # Registra a sessão SMB
            smbclient.register_session(
                SERVER,
                username=f"{DOMAIN}\\{usuario}",
                password=senha,
                port=PORT,
                connection_timeout=15,
            )

            pasta_remota = f"\\\\{SERVER}\\{SHARE}\\{REMOTE_FOLDER.replace('/', chr(92))}"

            # Lista arquivos na pasta remota
            try:
                arquivos = list(smbclient.scandir(pasta_remota))
            except Exception as e:
                msg = str(e)
                if "STATUS_ACCESS_DENIED" in msg or "STATUS_LOGON_FAILURE" in msg:
                    raise RuntimeError("AUTHENTICATION_FAILED: " + msg)
                raise RuntimeError("CONNECTION_FAILED: erro ao listar pasta: " + msg)

            codigo_lower = codigo.lower()
            if not codigo_lower.endswith(".pdf"):
                nome_exato = codigo_lower + ".pdf"
            else:
                nome_exato = codigo_lower

            prefixo = nome_exato.replace(".pdf", "")

            selecionado = None
            selecionado_data = None

            # Busca exata primeiro
            for entry in arquivos:
                if entry.name.lower() == nome_exato:
                    selecionado = entry
                    break

            # Se não achou exato, busca por prefixo
            if selecionado is None:
                for entry in arquivos:
                    nome = entry.name.lower()
                    if nome.endswith(".pdf") and nome.startswith(prefixo):
                        stat = entry.stat()
                        if selecionado is None or stat.st_mtime > selecionado_data:
                            selecionado = entry
                            selecionado_data = stat.st_mtime

            if selecionado is None:
                raise RuntimeError(
                    f"FILE_NOT_FOUND: nenhum PDF iniciando com '{codigo}' foi encontrado."
                )

            # Baixa para pasta local
            pasta_local = Path(self.user_data_dir) / "desenhos"
            pasta_local.mkdir(parents=True, exist_ok=True)

            nome_seguro = re.sub(r'[\\/:*?"<>|]', "_", selecionado.name)
            caminho_local = pasta_local / nome_seguro

            caminho_remoto = f"{pasta_remota}\\{selecionado.name}"

            with smbclient.open_file(caminho_remoto, mode="rb") as f_remoto:
                with open(caminho_local, "wb") as f_local:
                    while True:
                        chunk = f_remoto.read(65536)
                        if not chunk:
                            break
                        f_local.write(chunk)

            Clock.schedule_once(
                lambda _dt: self._abrir_pdf_local(str(caminho_local)), 0
            )

        except Exception as erro:
            mensagem = self._traduzir_erro(str(erro))
            Clock.schedule_once(
                lambda _dt: self._finalizar_com_erro(mensagem), 0
            )
        finally:
            try:
                smbclient.delete_session(SERVER, port=PORT)
            except Exception:
                pass

    def _abrir_pdf_local(self, caminho_local):
        try:
            from androidstorage4kivy import SharedStorage, ShareSheet

            self.status_text = "Desenho encontrado. Abrindo o PDF..."

            arquivo_compartilhado = SharedStorage().copy_to_shared(caminho_local)
            if arquivo_compartilhado is None:
                raise RuntimeError(
                    "Não foi possível disponibilizar o PDF para o Android."
                )

            ShareSheet().view_file(arquivo_compartilhado)
            self.status_text = (
                f"Desenho localizado: {os.path.basename(caminho_local)}"
            )

        except Exception as erro:
            self.status_text = (
                "Desenho baixado, mas não foi possível abrir o PDF: "
                f"{erro}"
            )
        finally:
            self.root.ids.botao_abrir.disabled = False

    def _finalizar_com_erro(self, mensagem):
        self.status_text = mensagem
        self.root.ids.botao_abrir.disabled = False

    @staticmethod
    def _traduzir_erro(mensagem):
        texto = mensagem or "Erro desconhecido."

        if "AUTHENTICATION_FAILED" in texto:
            return (
                "Acesso recusado. Confira o usuário e a senha. "
                "O domínio iberoeq.local já é acrescentado automaticamente."
            )
        if "FILE_NOT_FOUND" in texto:
            return (
                f"Desenho não encontrado em {SHARE}/{REMOTE_FOLDER}. "
                "Verifique o código digitado."
            )
        if "CONNECTION_FAILED" in texto or "Connection" in texto:
            return (
                f"Não foi possível conectar a {SERVER}:{PORT}. "
                "Confirme que está no Wi-Fi interno e que a porta 445 está liberada."
            )

        return f"Falha ao consultar o desenho: {texto}"


if __name__ == "__main__":
    DesenhoApp().run()
