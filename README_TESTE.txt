TESTE DESENHO SMB ANDROID - IBERO
=================================

Objetivo
--------
Este projeto testa o acesso direto do APK Android a uma pasta de rede SMB por IP.
O fluxo é:

APK -> SMB por IP -> pasta de rede -> procura PDF pelo código -> baixa para Downloads/DesenhosIbero -> abre PDF.

Não usa:
- API intermediária no PC
- SharePoint
- Java SmbDownloader
- jcifs-ng

Arquivos
--------
main.py          = aplicativo Kivy
buildozer.spec   = configuração para gerar APK

Como testar no PC antes
-----------------------
1) Instale dependências:
   pip install kivy pysmb

2) Rode:
   python main.py

3) Preencha:
   IP do servidor: 192.168.2.2
   Nome do servidor/remote_name: 192.168.2.2 ou nome real do servidor
   Compartilhamento: IBERO
   Pasta dentro do compartilhamento: Publico/BASE DE CONHECIMENTO
   Domínio: iberoeq.local ou IBEROEQ, conforme funcionar
   Usuário: seu usuário de rede
   Senha: sua senha de rede

4) Clique em Testar conexão.
5) Digite o código, exemplo 79, e clique em Buscar PDF.

Como gerar APK
--------------
No Linux/WSL/Buildozer:

   cd teste_desenho_smb_android
   rm -rf .buildozer bin
   buildozer -v android debug 2>&1 | tee build.log

APK gerado em:
   bin/testedesenhosmbpy-0.1.0-arm64-v8a-debug.apk

Permissões
----------
O app usa INTERNET para acessar SMB na porta 445.
Em Android 10+ o PDF é salvo em Downloads/DesenhosIbero via MediaStore.

Observações importantes
-----------------------
1) O servidor precisa aceitar SMB2. A biblioteca pysmb suporta SMB1/SMB2.
2) Se a rede exigir somente SMB3, pode falhar. Nesse caso será necessário usar outra abordagem.
3) O tablet precisa estar na mesma rede Wi-Fi ou numa rede roteada até o servidor.
4) A porta 445 precisa estar liberada entre tablet e servidor.
5) O aplicativo salva a configuração localmente no armazenamento privado do APK.

Se der erro de login
--------------------
Teste variações do domínio:
- iberoeq.local
- IBEROEQ
- vazio

Teste também trocar Nome do servidor/remote_name de IP para o nome real do servidor.
