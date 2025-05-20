Item	                O que registar
🔍 Ferramenta	        Qual ferramenta (ex: Bandit, Snyk)
🧠 Tipo de Análise	    SAST ou SCA
📁 Localização	        Nome do ficheiro + linha afetada
⚠️ Severidade	        Alta / Média / Baixa
💡 Descrição	         O que foi detetado
✅ Mitigação sugerida   Ex: usar método seguro, remover lib

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

**Última atualização:** 2025-05-20

