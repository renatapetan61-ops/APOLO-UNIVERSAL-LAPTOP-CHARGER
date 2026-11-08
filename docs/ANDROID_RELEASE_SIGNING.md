# APOLO Charger — assinatura de versão Release

## Estado

O Gradle já está preparado para assinar o APK Release quando as variáveis de ambiente de assinatura estiverem presentes. O workflow Android CI foi reforçado para exigir os quatro segredos, gerar o APK, verificar a assinatura com `apksigner` e calcular o SHA-256.

A assinatura ainda NÃO está ativada no GitHub: isso depende de uma chave privada criada e guardada pelo proprietário do projeto. Não gere uma chave de produção automaticamente em CI, pois uma chave nova em cada execução impediria atualizações sobre a instalação anterior.

## 1. Criar a chave de assinatura uma única vez

Em um computador confiável com JDK instalado, abra PowerShell e execute (escolha uma senha forte; não use a senha do exemplo):

```powershell
keytool -genkeypair -v -keystore apolo-charger-release.jks -alias apolo-charger -keyalg RSA -keysize 3072 -validity 10000
```

Guarde o arquivo `apolo-charger-release.jks`, a senha do keystore, o alias e a senha da chave em local seguro e com backup offline. **Nunca** coloque o arquivo JKS ou senhas no Git, no APK, em issues ou em mensagens públicas. Perder a chave pode impedir atualizações do aplicativo distribuído fora do Play App Signing.

## 2. Criar os GitHub Actions secrets

No repositório, abra **Settings → Secrets and variables → Actions → New repository secret** e crie:

- `APOLO_RELEASE_KEYSTORE_BASE64`: conteúdo Base64 do arquivo JKS. No PowerShell:
  ```powershell
  [Convert]::ToBase64String([IO.File]::ReadAllBytes(".\apolo-charger-release.jks")) | Set-Clipboard
  ```
  Cole o conteúdo da área de transferência no secret. Não publique esse conteúdo.
- `APOLO_RELEASE_STORE_PASSWORD`: senha do keystore.
- `APOLO_RELEASE_KEY_ALIAS`: `apolo-charger` (ou o alias escolhido).
- `APOLO_RELEASE_KEY_PASSWORD`: senha da chave.

Em **Settings → Secrets and variables → Actions → Variables**, crie a variável:
- `APOLO_RELEASE_ENABLED` = `true`

A variável apenas habilita a etapa; sem os quatro secrets válidos, a compilação Release falha de forma explícita.

## 3. Gerar o Release

Faça um push/commit que acione Android CI ou execute **Actions → Android CI → Run workflow**. Quando a etapa Release terminar, baixe o artefato `apolo-charger-release-apk`. O workflow verifica a assinatura APK e publica o SHA-256 nos logs.

## 4. Instalação e atualizações

- O APK Release assinado com a mesma chave pode atualizar instalações que usem o mesmo certificado e package name.
- Se já houver no celular uma versão Debug assinada com a chave de depuração do Android, a instalação do Release poderá exigir desinstalar a versão Debug primeiro. Isso apaga os dados locais do app; faça backup de qualquer dado necessário.
- Não altere `applicationId` nem perca a chave de assinatura.
- Assinatura válida comprova integridade e continuidade do desenvolvedor; **não garante** que o Play Protect deixe de mostrar avisos. Para distribuição ampla, publique pelo Google Play Console e use Play App Signing, concluindo a análise e os requisitos da loja.
- Não tente ocultar o app do Play Protect nem desativar proteções do dispositivo.

## 5. O que foi automatizado

O workflow `.github/workflows/android-ci.yml`:
1. Confere a presença dos quatro secrets;
2. Reconstrói o keystore temporário no runner;
3. Executa `gradle :android:app:assembleRelease`;
4. Verifica o APK com `apksigner verify --verbose`;
5. Calcula SHA-256;
6. Remove o keystore temporário e publica o artefato Release.

A chave privada permanece fora do repositório e é fornecida ao runner apenas durante a etapa de assinatura.
