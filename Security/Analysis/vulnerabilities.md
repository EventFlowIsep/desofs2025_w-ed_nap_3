## 📝 Histórico de Alterações

| Data       | Descrição da Alteração                                                                          | Autor        | Versão |
|------------|-------------------------------------------------------------------------------------------------|--------------|--------|
| 2025-05-20 | Revisão de todos os testes de segurança com ferramentas SAST (Bandit, Semgrep)                  | Rafael       | 1.0    |
| 2025-05-22 | Melhorias nos testes SCA de forma a obter um relatório completo do snyk                         | Rafael       | 2.0    |
| 2025-05-25 | Testes finais antes do final sprint 1                                                           | Rafael       | 3.0    |
| 2025-06-03 | Reformulação do plano de segurança, eliminação de redundâncias e integração com OWASP Top 10    | Rafael       | 4.0    |

# 🔐 Segurança na Aplicação EventFlow

## ✅ Resumo das Medidas de Segurança

| Área                                | Ferramenta/Implementação                      | Estado |
|-------------------------------------|-----------------------------------------------|--------|
| Validação Estática (SAST)          | Bandit, Semgrep                               | ✅     |
| Análise de Dependências (SCA)      | Snyk                                          | ✅     |
| Validação JWT + Claims             | Firebase Auth                                 | ✅     |
| Proteção contra XSS e JSON Scripts | Sanitização manual (regex)                    | ✅     |
| Rate Limiting                      | Rate limit por IP via `session_state`         | ✅     |
| Logs de Segurança                  | `eventflow_logs.db` e `admin_logs.csv`        | ✅     |
| Painel de Gestão de Roles          | Acesso restrito via autenticação e claims     | ✅     |

---

### 1. Alertas Identificados com Bandit e Semgrep

#### ⚠️ B113 – `requests` sem `timeout`
- **Descrição:** Pode causar bloqueios indefinidos.
- **Correção:** Aplicação do `timeout=DEFAULT_TIMEOUT` em todos os pedidos externos.
- **Ficheiros:** `app.py`, `admin.py`, `view_events.py`, `cancel_events.py`, `create_event.py`

#### ⚠️ B112 – `try-except` com `continue`
- **Descrição:** Pode mascarar erros importantes.
- **Correção:** Refatorado para capturar exceções específicas.
- **Ficheiro:** `main.py`

#### ⚠️ B101 – Uso de `assert`
- **Descrição:** `assert` é ignorado em bytecode otimizado.
- **Correção:** Substituído por `if` + `raise Exception`.
- **Ficheiros:** `tests/admin_test.py`, `tests/client_test.py`


---

## 2. Testes SCA (Software Composition Analysis)
Durante a análise de segurança das dependências externas do projeto, foram utilizados os seguintes scanners:

- **Objetivo:** Detectar vulnerabilidades conhecidas nas bibliotecas Python usadas.
- **Resultados:**

| Biblioteca | Versão Atual | ID da Vulnerabilidade | Versão Corrigida Sugerida |
|------------|--------------|-----------------------|---------------------------|
| flask      | 3.1.0        | GHSA-4grg-w6v8-c28g   | 3.1.1                     |
| tornado    | 6.4.2        | GHSA-7cx3-6m66-7c5m   | 6.5.0                     |

- **Ação Recomendada:** Atualizar as bibliotecas para as versões sugeridas para mitigar vulnerabilidades conhecidas.

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

Impacto Potencial
Ataques de negação de serviço (DoS)

Impacto na disponibilidade do sistema

# Correção Implementada:
# Antes:
tornado==6.4.2

# Depois:
tornado==6.5.0

---

## 3. Implementação de Claims Personalizados (Custom Claims) + Autorização por Role

A aplicação utiliza Firebase Authentication com **JWTs** contendo *claims personalizados* para representar a role do utilizador (`client`, `admin`, `event_manager`, etc.).

- **Definição:** feita via `auth.set_custom_user_claims(uid, { "role": "admin" })`
- **Verificação:** feita no backend via `verify_id_token(token)["role"]`

### 🔒 Proteção de Endpoints

Os endpoints mais sensíveis do backend estão protegidos com:
- Autenticação via `Bearer Token` (JWT)
- Autorização baseada em `role` do utilizador

---

## 4. Melhoria na Segurança das Variáveis Sensíveis

- **Variáveis como a Firebase API Key** foram movidas para o ficheiro `.env`, carregado com `load_dotenv()`.
- Criado `.env.example` para partilha segura entre membros da equipa sem expor chaves reais.

---

## 5. OWASP Top 10 (2021) – Cobertura

| Código | Categoria                                  | Estado            | Local de Implementação / Justificação                                       |
|--------|--------------------------------------------|-------------------|-----------------------------------------------------------------------------|
| A01    | Broken Access Control                      | ✅ Mitigado      | Verificação de roles no backend (`if user["role"] not in [...]`)            |
| A02    | Cryptographic Failures                     | ✅ Mitigado      | Firebase usa HTTPS e tokens JWT assinados                                   |
| A03    | Injection                                  | ✅ Mitigado      | Sanitização manual + Firestore (sem SQL)                                    |
| A04    | Insecure Design                            | ✅ Parcial       | Design defensivo e autenticação bem definidos                               |
| A05    | Security Misconfiguration                  | ✅ Mitigado      | `.env`, CORS middleware, API Gateway (manual)                               |
| A06    | Vulnerable and Outdated Components         | ✅ Mitigado      | Uso do `snyk`, plano de atualização contínua                                |
| A07    | Identification and Authentication Failures | ✅ Mitigado      | Firebase Auth + verificação de role                                         |
| A08    | Software and Data Integrity Failures       | ❌ Não aplicável | A aplicação não executa código externo nem usa auto-updates                 |
| A09    | Security Logging and Monitoring Failures   | ✅ Mitigado      | Logs persistentes em SQLite + alertas automáticos                           |
| A10    | SSRF (Server-Side Request Forgery)         | ✅ Mitigado      | A aplicação não faz chamadas dinâmicas para URLs fornecidas pelo utilizador |

---