```markdown
# Precificação — Central Analítica (Streamlit)

App em **Streamlit** para montar **orçamentos de projetos analíticos** (LC–MS/MS, GC–MS, etc.) a partir de uma tabela de **preços de referência** (solventes, plásticos, vidros, padrões/controles, colunas) + **parâmetros do estudo** (número de amostras/QC/blanks, consumos por amostra ou total) + **serviços de instrumentação** (custo por amostra).

O app gera:
- orçamento detalhado (por item)
- totais por categoria
- exportação para Excel com **todas as abas** (referências, parâmetros e orçamento final)

---

## ✅ Funcionalidades

### 1) Preços de referência (editáveis)
- **Consumíveis**: categoria, item, fornecedor, formato, preço, etc.
- **Instrumentação**: serviços com custo por amostra

### 2) Parâmetros do estudo (separado por blocos)
- **Solventes e volumes** (mL por amostra ou mL total)
- **Plásticos** (unidades por amostra ou unidades total)
- **Vidros** (unidades por amostra ou unidades total)
- **Padrões e Controles** (unidades total ou por amostra)
- **Colunas** (corridas total ou unidades total)
- **Instrumentação** (serviços + incluir/excluir + observação)

### 3) Orçamento calculado
- Multiplica quantidades totais pelos custos unitários de referência
- Permite sobrescrever qualquer linha com **Custo (manual)**

### 4) Exportação Excel
Gera um arquivo `.xlsx` com:
- `REF_Consumiveis`
- `REF_Instrumentacao`
- `PARAM_Solventes`
- `PARAM_Plasticos`
- `PARAM_Vidros`
- `PARAM_Padroes_Controles`
- `PARAM_Colunas`
- `PARAM_Instrumentacao`
- `ORCAMENTO`

---

## 📌 Regra de cálculo do custo unitário (importante)

O app usa a regra:

> **Custo_unitario = Preco_unitario / Formato**

Isso significa que:
- Para solventes: `Formato = volume da garrafa (mL)`  
  Ex.: 1000 mL, preço R$ 183,35 ⇒ custo = 183,35 / 1000 = **R$ 0,18335 por mL**
- Para consumíveis: `Formato = número de unidades na caixa`  
  Ex.: 1000 ponteiras, preço R$ 395,59 ⇒ custo = **R$ 0,39559 por unidade**
- Para colunas: `Formato = número de corridas estimadas`  
  Ex.: 800 corridas, preço R$ 8000 ⇒ custo = **R$ 10,00 por corrida**

> Se `Preco_unitario` e `Formato` estiverem preenchidos, o app calcula automaticamente.
> Se estiverem vazios, ele usa `Custo_unitario` como fallback (quando disponível).

---

## 🧱 Estrutura sugerida do repositório

```

precificacao-central-analitica/
├─ app.py
├─ requirements.txt
├─ README.md
└─ static/
└─ LAABio.png

````

> O app tenta carregar `static/LAABio.png` na sidebar. Se não existir, ele simplesmente ignora.

---

## 🚀 Como rodar localmente

### 1) Clone o repositório
```bash
git clone <SEU_REPO_URL>
cd precificacao-central-analitica
````

### 2) Crie um ambiente virtual (recomendado)

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

### 3) Instale dependências

```bash
pip install -r requirements.txt
```

### 4) Rode o app

```bash
streamlit run app.py
```

O navegador abrirá automaticamente. Se não abrir:

* copie a URL mostrada no terminal (geralmente `http://localhost:8501`).

---

## 📦 requirements.txt (mínimo recomendado)

Crie/edite o `requirements.txt` com:

```txt
streamlit
pandas
openpyxl
pillow
```

> Se você quiser travar versões, pode usar `pip freeze > requirements.txt` depois de testar.

---

## 🧪 Tutorial de uso (passo a passo)

### Passo 1 — Ajuste os preços de referência

Abra a aba **“Preços de referência”**:

1. Em **Consumíveis**, revise:

   * `Categoria` (Solventes, Plásticos, Vidros, Padrões e Controles, Colunas HPLC, Colunas GC)
   * `Formato` (quantidade operacional total: mL, unidades ou corridas)
   * `Preco_unitario` (R$ do pacote)
2. Em **Instrumentação**, revise:

   * `Servico`
   * `Custo_por_amostra`

> Dica: se você deixar um item sem preço/formato, ele aparecerá no orçamento com custo em branco.

---

### Passo 2 — Configure o tamanho do estudo

Na aba **“Parâmetros do estudo”**:

* Informe:

  * **Número de amostras**
  * **Número de QCs**
  * **Número de blanks**

O app calcula:

* **Total de injeções/amostras a cobrar**

---

### Passo 3 — Adicione consumos (por bloco)

Ainda na aba **“Parâmetros do estudo”**, vá bloco por bloco:

#### 3.1 Solventes e volumes

* Escolha um solvente
* Escolha o modo:

  * **mL por amostra** (multiplica pelo total)
  * **mL total** (não multiplica)
* Informe a quantidade e clique **Adicionar**

#### 3.2 Plásticos / Vidros / Padrões

* Escolha o item
* Modo:

  * **unidades por amostra** (multiplica pelo total)
  * **unidades total** (não multiplica)
* Informe a quantidade e **Adicionar**

#### 3.3 Colunas

* Escolha a coluna
* Modo:

  * **corridas total** (recomendado)
  * **unidades total**
* Informe a quantidade e **Adicionar**

#### 3.4 Instrumentação

* Escolha o serviço
* Marque **Incluir** (ou desmarque para excluir)
* Opcional: observação
* Clique **Adicionar**

---

### Passo 4 — Veja e edite o orçamento

Na aba **“Orçamento (calculado)”**:

* Confira:

  * quantidade total calculada (por item)
  * custo unitário de referência
  * custo calculado

#### Sobrescrever um custo

Se precisar forçar um valor:

* preencha **Custo (manual)**
  O app usa o manual no lugar do calculado.

---

### Passo 5 — Exportar Excel

Na aba **“Exportar”**:

* clique em **Baixar Excel**
* o arquivo vem com as referências + parâmetros + orçamento final

---

## 🛠 Upload de Excel (opcional)

Na sidebar existe um uploader para você futuramente implementar atualização das referências via Excel.

**Observação:** no código atual, o upload está na UI mas não está aplicando a leitura/merge do arquivo.
Se quiser, você pode implementar assim (ideia):

* ler `uploaded` com `pd.read_excel(uploaded, sheet_name=...)`
* substituir `st.session_state.cons_ref` e `st.session_state.inst_ref`

---

## ☁️ Publicar no Streamlit Community Cloud

1. Suba este repositório no GitHub com `app.py`, `requirements.txt`, `README.md`
2. Vá em:

   * Streamlit Community Cloud
3. Clique em **New app**
4. Selecione o repo e o arquivo `app.py`
5. Deploy

---

## ✅ Checklist antes de publicar

* [ ] `requirements.txt` existe e está correto
* [ ] `app.py` roda localmente sem erros
* [ ] (Opcional) `static/LAABio.png` existe, se você quiser logo
* [ ] Teste exportação Excel

---

## Licença

Defina a licença conforme seu plano (MIT, Apache-2.0, etc.).
Se você quiser uma recomendação: **MIT** é simples e bem aceita.

---

## Contato / Autor

Ricardo M. Borges — IPPN/UFRJ

```
```
