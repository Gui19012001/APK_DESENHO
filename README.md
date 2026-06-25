# Teste de desenho via SMB — domínio fixo

O próprio APK conecta diretamente ao servidor:

- Servidor: `192.168.2.2`
- Porta: `445`
- Compartilhamento: `DADOS`
- Pasta: `IBERO/Publico/BASE DE CONHECIMENTO`
- Domínio fixo: `iberoeq.local`

Na tela, o usuário informa apenas:

- usuário, sem o domínio;
- senha;
- código do desenho.

Exemplo:

- usuário: `guilherme.cruz`
- o APK autentica como domínio `iberoeq.local` + usuário informado.

A senha não está incluída no projeto e não é salva pelo aplicativo.

## Compilar

1. Envie todos os arquivos para a raiz do GitHub.
2. Acesse **Actions**.
3. Execute **Build Android APK**.
4. Baixe o artifact `apk-teste-desenho-smb-dominio-fixo`.
