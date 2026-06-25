import os
import re
import threading
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.utils import platform

SERVER = "192.168.2.2"
PORT = 445
SHARE = "DADOS"
REMOTE_FOLDER = "IBERO/Publico/BASE DE CONHECIMENTO"
DOMAIN = "iberoeq.local"


class TesteDesenhoApp(App):
    status_text = StringProperty(
        "Digite o usuário da rede, a senha e o código do desenho."
    )

    def build(self):
        self.title = "Teste Desenho SMB"
        return Builder.load_file("main.kv")

    def abrir_desenho(self):
        codigo = self.root.ids.codigo.text.strip()
        usuario = self.root.ids.usuario.text.strip()
        senha = self.root.ids.senha.text

        if not codigo:
            self.status_text = "Digite o código do desenho."
            return

        if not re.fullmatch(r"[A-Za-z0-9._() -]+", codigo):
            self.status_text = (
                "Código inválido. Use letras, números, ponto, hífen ou underline."
            )
            return

        if not usuario:
            self.status_text = "Digite somente o usuário, por exemplo: guilherme.cruz"
            return

        if "\\" in usuario or "@" in usuario:
            self.status_text = (
                "Digite somente o usuário. O domínio iberoeq.local já está configurado."
            )
            return

        if not senha:
            self.status_text = "Digite a senha da rede."
            return

        self.root.ids.botao_abrir.disabled = True
        self.status_text = (
            f"Conectando em {SERVER}:{PORT} e procurando {codigo}.pdf..."
        )

        threading.Thread(
            target=self._consultar_smb,
            args=(codigo, usuario, senha),
            daemon=True,
        ).start()

    def _consultar_smb(self, codigo, usuario, senha):
        try:
            if platform != "android":
                raise RuntimeError("Este teste foi preparado para o APK Android.")

            from jnius import autoclass

            SmbDownloader = autoclass(
                "br.com.suaempresa.testedesenhosmb.SmbDownloader"
            )

            pasta_local = Path(self.user_data_dir) / "desenhos"
            pasta_local.mkdir(parents=True, exist_ok=True)

            caminho_local = SmbDownloader.downloadByCode(
                SERVER,
                PORT,
                SHARE,
                REMOTE_FOLDER,
                codigo,
                DOMAIN,
                usuario,
                senha,
                str(pasta_local),
            )

            if not caminho_local:
                raise RuntimeError("A consulta terminou sem retornar o arquivo.")

            Clock.schedule_once(
                lambda _dt: self._abrir_pdf_local(str(caminho_local)),
                0,
            )

        except Exception as erro:
            mensagem = self._traduzir_erro(str(erro))
            Clock.schedule_once(
                lambda _dt: self._finalizar_com_erro(mensagem),
                0,
            )

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
                "O desenho foi baixado, mas não foi possível abrir o PDF: "
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
                "O domínio iberoeq.local já é acrescentado pelo aplicativo."
            )
        if "FILE_NOT_FOUND" in texto:
            return (
                "Desenho não encontrado em "
                f"{SHARE}/{REMOTE_FOLDER}."
            )
        if "CONNECTION_FAILED" in texto:
            return (
                f"Não foi possível conectar a {SERVER}:{PORT}. "
                "Confirme o Wi-Fi interno e a liberação da porta 445."
            )

        return f"Falha ao consultar o desenho: {texto}"


if __name__ == "__main__":
    TesteDesenhoApp().run()
