## 📝 Histórico de Alterações

| Data       | Descrição da Alteração                                                                          | Autor        | Versão |
|------------|-------------------------------------------------------------------------------------------------|--------------|--------|
| 2025-05-20 | Revisão de todos os testes de segurança com ferramentas SAST (Bandit, Semgrep)                  | Rafael       | 1.0    |
| 2025-05-22 | Melhorias nos testes SCA de forma a obter um relatório comploeto do snyk                        | Rafael       | 2.0    |
| 2025-05-25 | Testes finais antes do final sprint 1                                                           | Rafael       | 3.0    |

# 🔐 Segurança na Aplicação EventFlow

## 1.1 Validação Estática de Código (SAST) com Bandit

Durante a fase de testes de segurança automatizados, foi utilizada a ferramenta [Bandit](https://bandit.readthedocs.io/en/latest/) para analisar o código Python da aplicação. Um dos alertas críticos identificados foi:

### ⚠️ Alerta: B113 – `requests` sem `timeout`
- **Descrição:** Chamadas às funções `requests.get()` e `requests.post()` sem parâmetro `timeout` definido podem causar bloqueios indefinidos da aplicação.
- **Risco:** Exploração via ataque de negação de serviço (DoS) ou impacto na disponibilidade.
- **Ficheiros afetados:** `app.py`, `admin.py`

### 🛠️ Correção Implementada
Foi definido um `DEFAULT_TIMEOUT = 10` e aplicado consistentemente nas chamadas relevantes:

```python
# Antes:
requests.post(url, json=payload)

# Depois:
requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
```

---

## 1.2 Implementação de Claims Personalizados (Custom Claims)

A aplicação utiliza Firebase Authentication com **JWTs** contendo *claims personalizados* para representar a role do utilizador (`client`, `admin`, `event_manager`, etc.).

- **Definição:** feita via `auth.set_custom_user_claims(uid, { "role": "admin" })`
- **Verificação:** feita no backend via `verify_id_token(token)["role"]`

### 🔒 Proteção de Endpoints

Os endpoints mais sensíveis do backend estão protegidos com:
- Autenticação via `Bearer Token` (JWT)
- Autorização baseada em `role` do utilizador

Exemplo:

```python
@app.post("/events/create")
async def create_event(..., user=Depends(verify_token)):
    if user["role"] not in ["admin", "event_manager"]:
        raise HTTPException(status_code=403, detail="Forbidden")
```

---

## 1.3 Melhoria na Segurança das Variáveis Sensíveis

- **Variáveis como a Firebase API Key** foram movidas para o ficheiro `.env`, carregado com `load_dotenv()`.
- Criado `.env.example` para partilha segura entre membros da equipa sem expor chaves reais.

---

## 1.4 Outras Medidas Adicionais

| Medida                         | Estado    |
|-------------------------------|-----------|
| Validação de tokens JWT       | ✅ Ativa   |
| Middleware CORS               | ✅ Ativa   |
| Ocultação de menus por role   | ✅ Implementada em `app.py` |
| Logs de atribuição de roles   | ✅ Guardados em `admin_logs.csv` |
| Painel de gestão de roles     | ✅ Acessível apenas a `admin` verificados |

---
**Atualização feita a:** 2025-05-20


## 2.1 Validação Estática de Código (SAST) com Bandit e Semgrep

⚠️ Alertas principais do Bandit

## B113 - requests sem timeout

Descrição: Chamadas às funções requests.get() e requests.post() sem o parâmetro timeout definido podem provocar bloqueios indefinidos da aplicação.

Risco: Exploração possível via ataques de negação de serviço (DoS), afetando a disponibilidade do serviço.

Ficheiros afetados: streamlit_app/modules/cancel_events.py, streamlit_app/modules/create_event.py, streamlit_app/modules/view_events.py

## B112 - Uso de try-except com continue

Descrição: Utilização de try-except com continue pode mascarar erros importantes, dificultando o diagnóstico e a correção.

Ficheiro: app/main.py

## B101 - Uso de assert

Descrição: Uso de assert em código que pode ser removido em bytecode otimizado, afetando verificações em produção.

Ficheiro: tests/test_basic.py

🛠️ Correções Implementadas
Foi definido um DEFAULT_TIMEOUT = 10 segundos, aplicado em todas as chamadas HTTP relevantes, garantindo que a aplicação não fica bloqueada indefinidamente:

# Antes:
requests.post(url, json=payload)

# Depois:
requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
Além disso, foram revistas as estruturas de tratamento de exceções para evitar ocultar erros importantes.

## 2.2 Riscos e Impacto

Chamadas a requests sem timeout podem levar a bloqueios indefinidos da aplicação se o servidor remoto não responder, possibilitando ataques DoS.

Uso inadequado de try-except pode mascarar erros críticos, dificultando a deteção e correção.

Uso de assert no código de produção pode levar a comportamentos inesperados quando otimizações do Python estiverem ativadas.

## 2.3 Proteções de Endpoints e Autorização com Claims Personalizados

A aplicação utiliza o Firebase Authentication com tokens JWT que contêm claims personalizados para indicar a role do utilizador (client, admin, event_manager, etc.).

Definição de roles: via auth.set_custom_user_claims(uid, { "role": "admin" }) pelo backend/admin.

Verificação: feita no backend ao validar o token JWT e extrair o campo role.

Proteção de endpoints:

@app.post("/events/create")
async def create_event(..., user=Depends(verify_token)):
    if user["role"] not in ["admin", "event_manager"]:
        raise HTTPException(status_code=403, detail="Forbidden")

## 2.4 Melhoria na Gestão de Variáveis Sensíveis
Chaves e URLs sensíveis como a FIREBASE_API_KEY passaram a ser guardadas num ficheiro .env.

Utilização do pacote python-dotenv com load_dotenv() para carregar as variáveis.

Criação do ficheiro .env.example para facilitar o partilhar seguro das configurações na equipa sem expor chaves reais.

## 2.5 Outras Medidas de Segurança Aplicadas
Medida	|   Estado
Validação de tokens JWT     |	✅ Ativa e implementada no backend
Middleware CORS	            |   ✅ Ativo para permitir chamadas seguras
Ocultação de menus por role	|   ✅ Implementado na interface Streamlit
Logs de atribuição de roles	|   ✅ Gravados em ficheiro admin_logs.csv
Painel de gestão de roles	|   ✅ Acessível apenas a utilizadores admin

## 2.6 Testes SCA (Software Composition Analysis)
Durante a análise de segurança das dependências externas do projeto, foram utilizados os seguintes scanners:

- **Objetivo:** Detectar vulnerabilidades conhecidas nas bibliotecas Python usadas.
- **Resultados:**

| Biblioteca | Versão Atual | ID da Vulnerabilidade | Versão Corrigida Sugerida |
|------------|--------------|-----------------------|---------------------------|
| flask      | 3.1.0        | GHSA-4grg-w6v8-c28g   | 3.1.1                     |
| tornado    | 6.4.2        | GHSA-7cx3-6m66-7c5m   | 6.5.0                     |

- **Ação Recomendada:** Atualizar as bibliotecas para as versões sugeridas para mitigar vulnerabilidades conhecidas.

### 2.6.1 Snyk

Durante a análise de segurança das dependências com a ferramenta Snyk, foi identificada uma vulnerabilidade de alta severidade no pacote tornado na versão utilizada atualmente (6.4.2).

Detalhes da Vulnerabilidade
ID: SNYK-PYTHON-TORNADO-10176059

Título: Allocation of Resources Without Limits or Throttling

Severidade: Alta (High) — CVSS v3.1 Base Score: 7.5 / CVSS v4.0 Base Score: 8.7

CVE: CVE-2025-47287

Descrição:
A vulnerabilidade permite a alocação ilimitada de recursos através do parser multipart/form-data. Um atacante pode enviar dados multipart malformados que causam um alto volume de logs de erro contínuos, potencialmente resultando em negação de serviço (DoS) devido a sobrecarga do sistema.
Nota: Esta exploração depende da utilização do subsistema de logs síncronos.

Referência:
GitHub Commit de Correção

Pacote e Versão Afetados
Pacote: tornado

Versão atual usada: 6.4.2

Versão segura recomendada: >= 6.5

Impacto Potencial
Ataques de negação de serviço (DoS)

Impacto na disponibilidade do sistema

Correção implementada:
# Antes:
tornado==6.4.2

# Depois:
tornado==6.5.0

Enquanto a atualização não é possível, pode ser aplicada uma mitigação bloqueando requisições com o header Content-Type: multipart/form-data em um proxy reverso ou firewall.

## 2.6.2 Análise do Relatório Snyk - Tornado Vulnerabilidade Crítica

- Pacote afetado: tornado 6.4.2
- Identificador: SNYK-PYTHON-TORNADO-10176059
- Severidade: Alta (CVSS 8.7)
- Descrição: Vulnerabilidade no parser multipart/form-data que pode causar negação de serviço (DoS) por excessivo logging.
- Correção recomendada: Atualizar para tornado versão 6.5 ou superior.
- Referências: [GitHub Commit](https://github.com/tornadoweb/tornado/commit/b39b892bf78fe8fea01dd45199aa88307e7162f3)


**Atualização feita a:** 2025-05-22


## 3.1 Validação Estática de Código (SAST) com Bandit

### ⚠️ Alerta: B112 – Uso de try-except com continue
- **Descrição:** A utilização do try-except com a instrução continue foi identificada no código. Esse padrão pode mascarar erros importantes, dificultando a detecção e correção de falhas no sistema.
- **Risco:** Pode ocultar exceções críticas, prejudicando a análise de erros e a estabilidade da aplicação.
- **Ficheiros afetados:** `main.py`

### 🛠️ Correção Implementada

A lógica de tratamento de exceções foi alterada para garantir que os erros sejam tratados de forma adequada e não sejam ignorados silenciosamente. O código que anteriormente usava try-except com continue foi refatorado para capturar exceções específicas e fornecer mensagens de erro mais claras.


### ⚠️ Alerta: B101 – Uso de assert
- **Descrição:** O uso de assert no código de produção pode levar a falhas quando o Python estiver compilando para bytecode otimizado, uma vez que os asserts são removidos nessas situações.
- **Risco:** O uso de assert pode resultar em falhas invisíveis em ambientes de produção, onde as verificações de segurança são críticas.
- **Ficheiros afetados:** `tests/admin_test.py`, `tests/client_test.py`

### 🛠️ Correção Implementada
O uso de assert foi substituído por verificações explícitas e tratamento adequado de erros para garantir que as falhas sejam capturadas mesmo em ambientes otimizados.

```python
# Antes:
assert res.status_code == 200

# Depois:
if res.status_code != 200:
    raise AssertionError(f"Expected status code 200, but got {res.status_code}")
```

---

**Atualização feita a:** 2025-05-20