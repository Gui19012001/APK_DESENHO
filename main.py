import os
import re

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivy.storage.jsonstore import JsonStore
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import platform


REQUEST_SELECIONAR_PASTA = 7419
SOLID_EXPLORER_PACKAGE = "pl.solidexplorer2"
NOME_PASTA_ESPERADA = "BASE DE CONHECIMENTO"


class TelaPrincipal(BoxLayout):
    status = StringProperty(
        "Primeiro vincule a pasta BASE DE CONHECIMENTO."
    )
    pasta_status = StringProperty("Pasta ainda não vinculada")
    ultima_uri = StringProperty("")
    pasta_configurada = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._store = None
        self._android_activity = None

    def on_kv_post(self, _base_widget):
        app = App.get_running_app()
        self._store = JsonStore(
            os.path.join(app.user_data_dir, "config_rede.json")
        )
        self._carregar_pasta_salva()

        if platform == "android":
            try:
                from android import activity

                self._android_activity = activity
                activity.bind(on_activity_result=self._on_activity_result)
            except Exception as erro:
                self.status = f"Falha ao preparar retorno do Android: {erro}"

    def _carregar_pasta_salva(self):
        if self._store is None or not self._store.exists("pasta_rede"):
            self.pasta_configurada = False
            self.pasta_status = "Pasta ainda não vinculada"
            return

        dados = self._store.get("pasta_rede")
        uri = dados.get("uri", "")
        authority = dados.get("authority", "")

        if not uri:
            self.pasta_configurada = False
            self.pasta_status = "Pasta ainda não vinculada"
            return

        self.pasta_configurada = True
        self.pasta_status = (
            f"Pasta vinculada • provedor: {authority or 'Android'}"
        )

    @staticmethod
    def _codigo_seguro(valor: str) -> str:
        codigo = valor.strip()
        codigo = re.sub(r"[^A-Za-z0-9._-]", "", codigo)

        if codigo.lower().endswith(".pdf"):
            codigo = codigo[:-4]

        return codigo

    def selecionar_pasta(self):
        """
        Abre o seletor oficial do Android.

        No seletor, o usuário deve entrar no armazenamento de rede já
        configurado e escolher exatamente a pasta BASE DE CONHECIMENTO.
        """
        if platform != "android":
            self.status = "A seleção de pasta só funciona no APK Android."
            return

        try:
            from jnius import autoclass

            Intent = autoclass("android.content.Intent")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")

            intent = Intent(Intent.ACTION_OPEN_DOCUMENT_TREE)
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            intent.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
            intent.addFlags(Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION)
            intent.addFlags(Intent.FLAG_GRANT_PREFIX_URI_PERMISSION)

            PythonActivity.mActivity.startActivityForResult(
                intent,
                REQUEST_SELECIONAR_PASTA,
            )
            self.status = (
                "No seletor, escolha 192.168.2.2 > DADOS > IBERO > "
                "Publico > BASE DE CONHECIMENTO."
            )
        except Exception as erro:
            self.status = f"Não foi possível abrir o seletor de pastas: {erro}"

    def _on_activity_result(self, request_code, result_code, data):
        if request_code != REQUEST_SELECIONAR_PASTA:
            return

        try:
            from jnius import autoclass

            Activity = autoclass("android.app.Activity")
            Intent = autoclass("android.content.Intent")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")

            if result_code != Activity.RESULT_OK or data is None:
                Clock.schedule_once(
                    lambda _dt: self._definir_status(
                        "Seleção cancelada. Nenhuma pasta foi alterada."
                    ),
                    0,
                )
                return

            tree_uri = data.getData()
            if tree_uri is None:
                raise RuntimeError("O Android não retornou a URI da pasta.")

            flags_recebidas = data.getFlags()
            flags_permissao = flags_recebidas & (
                Intent.FLAG_GRANT_READ_URI_PERMISSION
                | Intent.FLAG_GRANT_WRITE_URI_PERMISSION
            )

            resolver = PythonActivity.mActivity.getContentResolver()
            permissao_persistida = True

            try:
                resolver.takePersistableUriPermission(
                    tree_uri,
                    flags_permissao,
                )
            except Exception:
                # Alguns provedores concedem acesso, mas não permitem
                # persistência. O teste ainda pode funcionar nesta sessão.
                permissao_persistida = False

            uri_texto = str(tree_uri.toString())
            authority = str(tree_uri.getAuthority() or "")

            self._store.put(
                "pasta_rede",
                uri=uri_texto,
                authority=authority,
                persistida=permissao_persistida,
            )

            mensagem = (
                "Pasta vinculada. Agora digite 1519 e toque em ABRIR DESENHO."
            )
            if not permissao_persistida:
                mensagem += (
                    " O provedor não confirmou acesso permanente; talvez seja "
                    "necessário vincular novamente após reiniciar o tablet."
                )

            Clock.schedule_once(
                lambda _dt: self._aplicar_pasta_configurada(
                    authority,
                    mensagem,
                ),
                0,
            )
        except Exception as erro:
            Clock.schedule_once(
                lambda _dt, texto=str(erro): self._definir_status(
                    f"Falha ao salvar a pasta selecionada: {texto}"
                ),
                0,
            )

    def _aplicar_pasta_configurada(self, authority: str, mensagem: str):
        self.pasta_configurada = True
        self.pasta_status = (
            f"Pasta vinculada • provedor: {authority or 'Android'}"
        )
        self.status = mensagem

    def _definir_status(self, texto: str):
        self.status = texto

    def limpar_pasta(self):
        if self._store is None or not self._store.exists("pasta_rede"):
            self._carregar_pasta_salva()
            self.status = "Nenhuma pasta estava vinculada."
            return

        dados = self._store.get("pasta_rede")
        uri_texto = dados.get("uri", "")

        if platform == "android" and uri_texto:
            try:
                from jnius import autoclass

                Intent = autoclass("android.content.Intent")
                Uri = autoclass("android.net.Uri")
                PythonActivity = autoclass("org.kivy.android.PythonActivity")

                flags = (
                    Intent.FLAG_GRANT_READ_URI_PERMISSION
                    | Intent.FLAG_GRANT_WRITE_URI_PERMISSION
                )
                PythonActivity.mActivity.getContentResolver().releasePersistableUriPermission(
                    Uri.parse(uri_texto),
                    flags,
                )
            except Exception:
                pass

        self._store.delete("pasta_rede")
        self._carregar_pasta_salva()
        self.ultima_uri = ""
        self.status = "Pasta desvinculada. Vincule novamente para continuar."

    def abrir_desenho(self, codigo_digitado: str):
        codigo = self._codigo_seguro(codigo_digitado)
        if not codigo:
            self.status = "Informe um código válido. Exemplo: 1519"
            return

        if self._store is None or not self._store.exists("pasta_rede"):
            self.status = (
                "Primeiro toque em VINCULAR PASTA DE REDE e selecione "
                f"{NOME_PASTA_ESPERADA}."
            )
            return

        if platform != "android":
            self.status = "A procura do PDF só funciona no APK Android."
            return

        try:
            uri_arquivo = self._localizar_pdf_na_pasta(f"{codigo}.pdf")
        except Exception as erro:
            self.status = f"Falha ao consultar a pasta vinculada: {erro}"
            return

        if uri_arquivo is None:
            self.status = (
                f"O arquivo {codigo}.pdf não foi encontrado diretamente na "
                f"pasta {NOME_PASTA_ESPERADA}."
            )
            return

        self.ultima_uri = str(uri_arquivo.toString())
        self._abrir_pdf(uri_arquivo, f"{codigo}.pdf")

    def _localizar_pdf_na_pasta(self, nome_arquivo: str):
        from jnius import autoclass

        Uri = autoclass("android.net.Uri")
        DocumentsContract = autoclass("android.provider.DocumentsContract")
        Document = autoclass("android.provider.DocumentsContract$Document")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")

        dados = self._store.get("pasta_rede")
        tree_uri = Uri.parse(dados["uri"])

        tree_document_id = DocumentsContract.getTreeDocumentId(tree_uri)
        children_uri = DocumentsContract.buildChildDocumentsUriUsingTree(
            tree_uri,
            tree_document_id,
        )

        projection = [
            Document.COLUMN_DOCUMENT_ID,
            Document.COLUMN_DISPLAY_NAME,
            Document.COLUMN_MIME_TYPE,
        ]

        resolver = PythonActivity.mActivity.getContentResolver()
        cursor = resolver.query(
            children_uri,
            projection,
            None,
            None,
            None,
        )

        if cursor is None:
            raise RuntimeError("O provedor não permitiu listar os arquivos.")

        nome_procurado = nome_arquivo.casefold()
        documento_encontrado = None

        try:
            indice_id = cursor.getColumnIndex(Document.COLUMN_DOCUMENT_ID)
            indice_nome = cursor.getColumnIndex(Document.COLUMN_DISPLAY_NAME)

            while cursor.moveToNext():
                nome_atual = str(cursor.getString(indice_nome) or "")
                if nome_atual.casefold() != nome_procurado:
                    continue

                document_id = cursor.getString(indice_id)
                documento_encontrado = (
                    DocumentsContract.buildDocumentUriUsingTree(
                        tree_uri,
                        document_id,
                    )
                )
                break
        finally:
            cursor.close()

        return documento_encontrado

    def _abrir_pdf(self, uri_arquivo, nome_arquivo: str):
        try:
            from jnius import autoclass

            Intent = autoclass("android.content.Intent")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")

            activity = PythonActivity.mActivity

            # Primeiro tenta entregar a URI content:// ao Solid Explorer.
            intent_solid = Intent(Intent.ACTION_VIEW)
            intent_solid.setDataAndType(uri_arquivo, "application/pdf")
            intent_solid.setPackage(SOLID_EXPLORER_PACKAGE)
            intent_solid.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)

            try:
                activity.startActivity(intent_solid)
                self.status = f"Abrindo {nome_arquivo} no Solid Explorer."
                return
            except Exception:
                pass

            # Se o Solid Explorer não atuar como visualizador de PDF,
            # usa qualquer visualizador compatível instalado no tablet.
            intent_pdf = Intent(Intent.ACTION_VIEW)
            intent_pdf.setDataAndType(uri_arquivo, "application/pdf")
            intent_pdf.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)

            chooser = Intent.createChooser(
                intent_pdf,
                f"Abrir {nome_arquivo}",
            )
            activity.startActivity(chooser)
            self.status = (
                f"{nome_arquivo} localizado. Escolha o visualizador de PDF."
            )
        except Exception as erro:
            self.status = (
                f"O arquivo foi localizado, mas não foi possível abri-lo: {erro}"
            )


class TesteSolidExplorerSafApp(App):
    def build(self):
        self.title = "Teste desenho por pasta"
        Builder.load_file("main.kv")
        return TelaPrincipal()

    def on_stop(self):
        root = self.root
        if (
            platform == "android"
            and root is not None
            and root._android_activity is not None
        ):
            try:
                root._android_activity.unbind(
                    on_activity_result=root._on_activity_result
                )
            except Exception:
                pass


if __name__ == "__main__":
    TesteSolidExplorerSafApp().run()
