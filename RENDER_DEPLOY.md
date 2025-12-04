# Deploy no Render - Instruções

## Configuração do Render

Para o deploy funcionar corretamente com o modo torneio, siga estas etapas:

### 1. Configurações do Serviço Web

No painel do Render, configure:

- **Build Command**: `./build.sh`
- **Start Command**: `python3 app.py`

### 2. Variáveis de Ambiente (opcional)

Se necessário, adicione:
- `PYTHON_VERSION`: `3.9` ou superior

### 3. Aplicar Migrations Manualmente (se necessário)

Se o deploy automático não aplicar as migrations, você pode conectar via SSH no Render e executar:

```bash
python3 apply_migration.py
```

### 4. Resetar Banco de Dados (apenas se necessário)

Se você quiser começar do zero com as novas colunas:

1. No Render Dashboard, vá em "Shell"
2. Execute:
```bash
rm poker.db
python3 apply_migration.py
```

### 5. Forçar Redeploy

Após fazer o push das mudanças:

1. Vá ao Render Dashboard
2. Clique em "Manual Deploy" → "Clear build cache & deploy"

## Verificação

Após o deploy, teste:

1. ✅ Criar um novo Cash Game
2. ✅ Criar um novo Torneio
3. ✅ Verificar timer de torneio
4. ✅ Testar rebuys em torneio
5. ✅ Encerrar torneio e ver premiação

## Solução de Problemas

**Erro: "no such column"**
- As migrations não foram aplicadas
- Execute `python3 apply_migration.py` via SSH no Render

**Erro: "Build failed"**
- Verifique se `build.sh` tem permissão de execução: `chmod +x build.sh`
- Verifique se `requirements.txt` está atualizado

**Deploy não detectado**
- Force push: `git push -f origin seu-branch`
- Ou use "Manual Deploy" no Render Dashboard
