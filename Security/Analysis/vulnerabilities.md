Item	                O que registar
🔍 Ferramenta	        Qual ferramenta (ex: Bandit, Snyk)
🧠 Tipo de Análise	    SAST ou SCA
📁 Localização	        Nome do ficheiro + linha afetada
⚠️ Severidade	        Alta / Média / Baixa
💡 Descrição	         O que foi detetado
✅ Mitigação sugerida   Ex: usar método seguro, remover lib

## 🔒 Vulnerability 1

- **Tool:** Bandit
- **Type:** SAST
- **File:** `auth.py`
- **Line:** 42
- **Severity:** High
- **Description:** Use of `eval()` with user input
- **Mitigation:** Replace with a safe parser like `json.loads()` or create a secure evaluation logic.

---

## 🔒 Vulnerability 2

- **Tool:** Snyk
- **Type:** SCA
- **Library:** `pyyaml 5.3`
- **Severity:** High
- **CVE:** CVE-2020-14343
- **Mitigation:** Upgrade to `pyyaml>=5.4`
