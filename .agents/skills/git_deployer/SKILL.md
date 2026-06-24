---
name: git_deployer
description: Deploy local modifications to the production environment (ssh alpine) using Git version control flow and service restarts.
---

# Skill: Git Deployer (git_deployer)

Esta skill define as melhores práticas e rotinas automatizadas para realizar versionamento local, validação e implantação física do código no servidor de produção (Raspberry Pi/Alpine no alias `ssh alpine`).

---

## ⚡ Fluxo de Deploy em Produção

Sempre siga este fluxo em ordem sequencial para evitar quebras em produção:

### 1. Validação de Integridade Local
Antes de comitar qualquer linha, garanta que nada foi quebrado executando a suíte de testes locais:
```bash
./run_tests.sh
```
> [!IMPORTANT]
> Nunca realize commits ou deploys se houver falhas nos testes locais. Aborte e corrija antes de prosseguir.

### 2. Versionamento e Push
Submeta as modificações para o repositório central:
```bash
git status
git add <arquivos>
git commit -m "tipo: mensagem descritiva curta"
git push origin main
```

### 3. Sincronização em Produção (Pull)
Conecte-se via SSH ao host de produção e atualize o código:
```bash
ssh alpine
cd /home/bruno/lightmanager
git pull
```

### 4. Recarregamento de Serviços e Cron
Após puxar o código no Alpine:
* **Se o Crontab mudou:** Recarregue o agendador:
  ```bash
  crontab crontab_template.txt
  ```
* **Reiniciar os serviços afetados:**
  * Para API: `bash scripts/restart_api.sh`
  * Para o Solar Worker: `bash scripts/restart_solar.sh`
  * Para o Bot Telegram: `bash scripts/restart_bot.sh`

### 5. Auditoria de Logs pós-boot
Valide se os serviços reiniciados subiram com sucesso e estão rodando sem erros:
```bash
tail -n 20 logs/api.log
tail -n 20 logs/solar.log
tail -n 20 logs/bot.log
```
