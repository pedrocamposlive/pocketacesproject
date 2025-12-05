# 🔧 Como Corrigir o Deploy no Render

## Problema Identificado

O Render está configurado para fazer deploy da branch **main**, mas essa branch:
1. ❌ Está protegida (não aceita push direto)
2. ❌ Não tem as mudanças do modo torneio
3. ❌ Não tem o script `build.sh`

**Suas implementações de torneio estão na branch:** `claude/review-ux-code-01Do9trb7z8L8QCV7Q3TJ8VW` ✅

---

## ✅ SOLUÇÃO RÁPIDA - Configurar Render

### Passo 1: Acessar Dashboard do Render
1. Vá para https://dashboard.render.com
2. Selecione seu serviço (pocketacesproject)

### Passo 2: Mudar Branch de Deploy
1. Clique em **Settings** (⚙️ no menu lateral)
2. Role até a seção **Build & Deploy**
3. Em **Branch**, mude de `main` para:
   ```
   claude/review-ux-code-01Do9trb7z8L8QCV7Q3TJ8VW
   ```
4. Clique em **Save Changes**

### Passo 3: Configurar Build Command
Na mesma seção **Build & Deploy**:
- **Build Command**: `./build.sh`
- **Start Command**: `python3 app.py`

### Passo 4: Deploy Manual
1. Vá em **Manual Deploy** (no topo da página)
2. Clique em **Clear build cache & deploy**
3. Aguarde o deploy (~2-3 minutos)

---

## ✅ ALTERNATIVA - Merge via Pull Request

Se preferir manter o deploy na main:

### Opção A: Via GitHub Interface
1. Acesse: https://github.com/pedrocamposlive/pocketacesproject
2. Vá em **Pull Requests**
3. Clique em **New Pull Request**
4. Base: `main` ← Compare: `claude/review-ux-code-01Do9trb7z8L8QCV7Q3TJ8VW`
5. Clique em **Create Pull Request**
6. Clique em **Merge Pull Request**
7. O Render fará deploy automaticamente

### Opção B: Desproteger Main (não recomendado)
1. Vá em Settings → Branches no GitHub
2. Remova proteção da branch main
3. Volte ao terminal e execute:
   ```bash
   git checkout main
   git merge claude/review-ux-code-01Do9trb7z8L8QCV7Q3TJ8VW
   git push origin main -f
   ```

---

## 📋 Checklist Após Deploy

Após o deploy bem-sucedido, verifique:

- [ ] Build completou sem erros
- [ ] Aplicação está rodando
- [ ] Consegue criar Cash Game
- [ ] Consegue criar Torneio
- [ ] Timer de torneio funciona
- [ ] Rebuy em torneio funciona
- [ ] Premiação do torneio aparece

---

## 🆘 Se ainda não funcionar

**Erro: "no such column"**
```bash
# Conecte via SSH no Render e execute:
python3 apply_migration.py
```

**Erro: "Build failed - build.sh not found"**
- Certifique-se que está usando a branch correta
- Verifique se build.sh existe: `ls -la build.sh`

**Logs do Render**
- Acesse: Settings → Logs para ver erros detalhados
