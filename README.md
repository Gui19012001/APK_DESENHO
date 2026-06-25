# Teste de desenho pelo Solid Explorer — Kivy

Projeto mínimo em **Python + Kivy + Buildozer** para testar a chamada de um PDF existente no compartilhamento de rede da Ibero.

## Caminho configurado

- Servidor: `192.168.2.2`
- Pasta: `/DADOS/IBERO/Publico/BASE DE CONHECIMENTO`
- Exemplo: `1519.pdf`
- URI gerada: `smb://192.168.2.2/DADOS/IBERO/Publico/BASE%20DE%20CONHECIMENTO/1519.pdf`
- Pacote Android do Solid Explorer: `pl.solidexplorer2`

## Antes de testar

1. Instale o Solid Explorer no tablet.
2. Cadastre o servidor `192.168.2.2` no Solid Explorer.
3. Confirme manualmente que o arquivo `1519.pdf` abre na pasta indicada.
4. Instale o APK produzido pelo workflow.
5. Digite `1519` e toque em **ABRIR DESENHO NO SOLID EXPLORER**.

## Gerar APK no GitHub

1. Crie um repositório.
2. Extraia este ZIP.
3. Envie todos os arquivos para a raiz do repositório, incluindo `.github/workflows/build-apk.yml`.
4. Abra **Actions**.
5. Selecione **Build Android APK**.
6. Clique em **Run workflow**.
7. Ao concluir, baixe o artifact `apk-teste-solid-explorer`.

## Funcionamento

O APK cria uma `Intent ACTION_VIEW` com a URI SMB e define o pacote do Solid Explorer. Caso o Solid Explorer não aceite a chamada direta, o app tenta abrir o seletor de aplicativos do Android.

## Limitação importante

A abertura direta depende de o Solid Explorer disponibilizar uma Activity capaz de receber externamente a URI `smb://`. O APK testa exatamente essa compatibilidade. Se o Solid Explorer abrir apenas na tela inicial ou rejeitar a URI, será necessário adotar outra integração, como uma API local ou um `DocumentProvider`.
