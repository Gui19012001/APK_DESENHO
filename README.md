# Teste de desenho por pasta vinculada — Kivy

Esta versão não tenta abrir `smb://` por `ACTION_VIEW`, porque o teste no tablet mostrou que o Solid Explorer não registra esse esquema para chamadas externas.

## Fluxo do teste

1. Abra o APK.
2. Toque em **1. VINCULAR PASTA DE REDE**.
3. No seletor do Android, procure o armazenamento de rede já configurado e escolha exatamente:

   `192.168.2.2 > DADOS > IBERO > Publico > BASE DE CONHECIMENTO`

4. Confirme **Usar esta pasta**.
5. Digite `1519`.
6. Toque em **2. LOCALIZAR E ABRIR DESENHO**.

O aplicativo consulta os documentos da pasta concedida, procura `1519.pdf` e abre uma URI `content://` com permissão de leitura.

## Limitação que este APK também valida

O armazenamento remoto precisa aparecer no seletor oficial de documentos do Android. Se o Solid Explorer não publicar a conexão SMB como provedor de documentos, a pasta de rede não aparecerá. Nesse caso, a próxima solução será o próprio APK acessar SMB com credenciais, sem depender do Solid Explorer.

## GitHub Actions

Abra **Actions > Build Android APK > Run workflow**. Ao finalizar, baixe o artifact `apk-teste-desenho-saf`.
