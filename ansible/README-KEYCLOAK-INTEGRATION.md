# DurvalCRM Keycloak Integration

Este documento descreve a configuração de integração entre Keycloak e WildFly para autenticação da aplicação DurvalCRM.

## Pré-requisitos

1. **Ambiente configurado**: Execute primeiro o playbook `00-set-environment.yml`
2. **Serviços em execução**: Keycloak e WildFly devem estar rodando
3. **Arquivo de realm**: O arquivo `realm-durvalcrm.json` deve estar presente em `files/keycloak/`

## Estrutura de Arquivos

```
durvalcrm-deployment/ansible/
├── playbook/
│   ├── 00-set-environment.yml      # Setup inicial do ambiente
│   └── 01-set-keycloak.yml         # Configuração do Keycloak (NOVO)
├── files/
│   ├── keycloak/
│   │   ├── realm-durvalcrm.json    # Definição do realm
│   │   └── keycloak.json           # Configuração do cliente
│   ├── wildfly/
│   │   └── keycloak-web.xml        # Configuração de segurança web
│   └── scripts/
│       └── test-keycloak-integration.sh  # Script de teste
└── README-KEYCLOAK-INTEGRATION.md  # Este documento
```

## Execução do Playbook

### 1. Configuração Básica

```bash
cd /Users/rafaeldeoliveira/projects/DurvalCRM/durvalcrm-deployment/ansible

# Execute o playbook de configuração do Keycloak
ansible-playbook -i inventory/hosts.ini playbook/01-set-keycloak.yml
```

### 2. Verificação dos Resultados

O playbook irá:

1. **Importar o realm** `durval-crm` no Keycloak
2. **Instalar o adapter** do Keycloak no WildFly
3. **Configurar a integração** entre os sistemas
4. **Criar o usuário de teste** `tesouraria`
5. **Testar a autenticação** automaticamente

### 3. Teste Manual da Integração

```bash
# Execute o script de teste
./files/scripts/test-keycloak-integration.sh

# Ou teste manualmente:
curl -k https://20.127.155.169:9443/auth/realms/durval-crm/.well-known/openid-configuration
```

## Configuração da Aplicação J2EE

### 1. Adicionar Dependências Maven

Adicione ao `pom.xml` da aplicação J2EE:

```xml
<dependency>
    <groupId>org.keycloak</groupId>
    <artifactId>keycloak-servlet-filter-adapter</artifactId>
    <version>26.0.7</version>
</dependency>
```

### 2. Configurar web.xml

Substitua o `web.xml` da aplicação pelo arquivo gerado em `/tmp/keycloak-web.xml` ou use como base.

### 3. Adicionar keycloak.json

Copie o arquivo `files/keycloak/keycloak.json` para `src/main/resources/` da aplicação.

### 4. Rebuild e Deploy

```bash
cd durvalcrm-j2ee
mvn clean package
# Deploy no WildFly via console ou CLI
```

## URLs de Acesso

Após a configuração bem-sucedida:

- **Keycloak Admin Console**: https://20.127.155.169:9443/admin/
- **Realm durval-crm**: https://20.127.155.169:9443/realms/durval-crm
- **WildFly Admin**: https://20.127.155.169:9990/
- **Aplicação DurvalCRM**: https://20.127.155.169:8443/durvalcrm-j2ee/

## Credenciais

### Keycloak Admin
- **Usuário**: admin
- **Senha**: admin

### Usuário de Teste
- **Usuário**: tesouraria
- **Senha**: cairbar@2025

### WildFly Admin
- **Usuário**: admin
- **Senha**: wildfly@2025

## Configuração do Cliente Keycloak

O realm importado inclui o cliente `durvalcrm-app` com as seguintes configurações:

- **Client ID**: `durvalcrm-app`
- **Protocol**: `openid-connect`
- **Access Type**: `confidential`
- **Valid Redirect URIs**:
  - `https://20.127.155.169:8443/*`
  - `https://localhost:8443/*`
- **Web Origins**: `https://20.127.155.169:8443`

## Fluxo de Autenticação

1. **Usuário acessa endpoint protegido** da aplicação J2EE
2. **WildFly redireciona** para Keycloak para login
3. **Usuário faz login** no Keycloak
4. **Keycloak retorna token** para a aplicação
5. **Aplicação autoriza acesso** aos recursos protegidos

## Troubleshooting

### 1. Keycloak não está acessível

```bash
# Verificar status do serviço
systemctl status keycloak

# Ver logs
journalctl -u keycloak -f

# Testar conectividade
curl -k https://20.127.155.169:9443/auth/
```

### 2. WildFly não reconhece o Keycloak

```bash
# Verificar se o adapter foi instalado
/opt/wildfly/bin/jboss-cli.sh --connect --command="ls /subsystem=keycloak"

# Ver logs do WildFly
tail -f /opt/wildfly/standalone/log/server.log
```

### 3. Aplicação não redireciona para login

1. Verificar se `keycloak.json` está no classpath
2. Verificar configuração do `web.xml`
3. Verificar se o adapter foi instalado corretamente
4. Verificar logs da aplicação

### 4. Erro de CORS

Ajustar configurações CORS no Keycloak Admin Console:
- Client → durvalcrm-app → Settings → Web Origins

### 5. Teste de Conectividade

```bash
# Testar Keycloak
curl -k https://20.127.155.169:9443/realms/durval-crm/.well-known/openid-configuration

# Testar autenticação de usuário
curl -k -X POST https://20.127.155.169:9443/realms/durval-crm/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=durvalcrm-app" \
  -d "username=tesouraria" \
  -d "password=cairbar@2025"
```

## Próximos Passos

1. **Configurar SSL certificates** apropriados para produção
2. **Ajustar configurações de segurança** conforme necessário
3. **Configurar roles e permissions** específicas
4. **Integrar com frontend** Vue.js
5. **Configurar logout** e session management
6. **Implementar refresh tokens**

## Suporte

Para problemas ou dúvidas:

1. Verificar logs dos serviços (`journalctl -u keycloak`, `/opt/wildfly/standalone/log/server.log`)
2. Executar script de teste: `./files/scripts/test-keycloak-integration.sh`
3. Consultar documentação do Keycloak: https://www.keycloak.org/documentation
4. Consultar documentação do WildFly: https://docs.wildfly.org/