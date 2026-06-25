import re
from urllib.parse import quote

from kivy.app import App
from kivy.core.clipboard import Clipboard
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout


SERVIDOR = "192.168.2.2"
PASTA_REDE = "DADOS/IBERO/Publico/BASE DE CONHECIMENTO"
SOLID_EXPLORER_PACKAGE = "pl.solidexplorer2"


class TelaPrincipal(BoxLayout):
    status = StringProperty(
        "Digite o código do PDF. Exemplo: 1519"
    )
    ultima_uri = StringProperty("")

    def _codigo_seguro(self, valor: str) -> str:
        codigo = valor.strip()

        # Aceita código simples, pontos, hífen e underline.
        # Remove barras para impedir navegação fora da pasta configurada.
        codigo = re.sub(r"[^A-Za-z0-9._-]", "", codigo)

        if codigo.lower().endswith(".pdf"):
            codigo = codigo[:-4]

        return codigo

    def _uri_pasta(self) -> str:
        partes = [quote(parte, safe="") for parte in PASTA_REDE.split("/")]
        return f"smb://{SERVIDOR}/" + "/".join(partes)

    def _uri_arquivo(self, codigo_digitado: str) -> str:
        codigo = self._codigo_seguro(codigo_digitado)
        if not codigo:
            raise ValueError("Informe um código válido.")

        nome_arquivo = quote(f"{codigo}.pdf", safe="._-")
        return f"{self._uri_pasta()}/{nome_arquivo}"

    def abrir_desenho(self, codigo_digitado: str) -> None:
        try:
            uri = self._uri_arquivo(codigo_digitado)
        except ValueError as erro:
            self.status = str(erro)
            return

        self.ultima_uri = uri
        self._abrir_no_android(uri, "desenho")

    def abrir_pasta(self) -> None:
        uri = self._uri_pasta()
        self.ultima_uri = uri
        self._abrir_no_android(uri, "pasta")

    def copiar_uri(self) -> None:
        if not self.ultima_uri:
            self.ultima_uri = self._uri_pasta()

        Clipboard.copy(self.ultima_uri)
        self.status = "URI copiada para a área de transferência."

    def _abrir_no_android(self, uri: str, tipo: str) -> None:
        if platform != "android":
            self.status = (
                "Teste de Intent disponível somente no Android. URI: " + uri
            )
            return

        try:
            from jnius import autoclass

            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")

            activity = PythonActivity.mActivity

            # 1ª tentativa: encaminha diretamente ao Solid Explorer.
            intent = Intent(Intent.ACTION_VIEW)
            intent.setData(Uri.parse(uri))
            intent.setPackage(SOLID_EXPLORER_PACKAGE)
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            activity.startActivity(intent)

            self.status = (
                f"Solicitação enviada ao Solid Explorer para abrir o {tipo}."
            )
            return

        except Exception as erro_direto:
            try:
                from jnius import autoclass

                Intent = autoclass("android.content.Intent")
                Uri = autoclass("android.net.Uri")
                PythonActivity = autoclass("org.kivy.android.PythonActivity")

                activity = PythonActivity.mActivity

                # 2ª tentativa: deixa o Android escolher um app compatível.
                intent_generico = Intent(Intent.ACTION_VIEW)
                intent_generico.setData(Uri.parse(uri))
                intent_generico.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)

                seletor = Intent.createChooser(
                    intent_generico,
                    "Abrir caminho de rede",
                )
                seletor.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                activity.startActivity(seletor)

                self.status = (
                    "O Solid Explorer não aceitou a chamada direta. "
                    "O seletor de aplicativos foi aberto."
                )
                return

            except Exception as erro_generico:
                self.status = (
                    "Não foi possível abrir o caminho SMB. "
                    f"Direto: {erro_direto}. Alternativo: {erro_generico}"
                )


class TesteSolidExplorerApp(App):
    def build(self):
        self.title = "Teste de desenho"
        Builder.load_file("main.kv")
        return TelaPrincipal()


if __name__ == "__main__":
    TesteSolidExplorerApp().run()
