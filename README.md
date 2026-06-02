# ✝ Missas em Teresina

Site para consulta de horários de missas, confissões e adoração nas igrejas da Arquidiocese de Teresina - PI.

## 🚀 Como rodar localmente

```bash
npm install
npm run dev
```

Acesse: http://localhost:5173

## 📦 Build para produção

```bash
npm run build
```

Os arquivos ficam na pasta `dist/`.

## 🌐 Deploy no Netlify via GitHub

### 1. Criar repositório no GitHub

```bash
git init
git add .
git commit -m "feat: site missas teresina"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/missas-teresina.git
git push -u origin main
```

### 2. Criar site no Netlify

1. Acesse https://app.netlify.com
2. Clique em **"Add new site" > "Import an existing project"**
3. Escolha **GitHub** e autorize
4. Selecione o repositório `missas-teresina`
5. Configurações de build (já estão no `netlify.toml`):
   - Build command: `npm run build`
   - Publish directory: `dist`
6. Clique em **"Deploy site"**

O Netlify publicará automaticamente a cada `git push` na branch `main`.

### Deploy manual (sem GitHub)

```bash
npm install -g netlify-cli
npm run build
netlify deploy --prod --dir=dist
```

## 📊 Como atualizar os dados (igrejas)

Os dados ficam em `src/data/igrejas.json`. Para atualizar:

1. Edite o arquivo `igrejas.json` com os novos horários
2. Cada igreja tem a estrutura:
```json
{
  "id": 1,
  "nome": "Nome da Igreja",
  "endereco": "Endereço completo",
  "bairro": "Bairro",
  "telefone": "99999-9999",
  "instagram": "perfil_instagram",
  "lat": -5.0889,
  "lng": -42.8016,
  "missas": {
    "domingo": ["8h", "18h"],
    "segunda": ["7h"],
    "terca": [],
    "quarta": [],
    "quinta": [],
    "sexta": ["18h30"],
    "sabado": ["9h"]
  },
  "confissoes": {
    "sabado": ["15h às 18h"]
  },
  "adoracao": {
    "quinta": ["17h às 18h"]
  }
}
```
3. Faça `git push` e o Netlify redeployará automaticamente.

## 🗺️ Como obter coordenadas (lat/lng)

1. Acesse https://www.google.com.br/maps
2. Clique com o botão direito no local
3. O primeiro item do menu mostrará as coordenadas
4. Copie para `lat` e `lng` no JSON

## 🛠️ Tecnologias

- **React 18** + **Vite 5**
- **Leaflet** + **React-Leaflet** — mapa interativo
- **Google Fonts**: Cormorant Garamond + DM Sans
- **OpenStreetMap** — tiles do mapa (gratuito)

## 📱 Funcionalidades

- ✅ Filtro por dia da semana (detecta dia atual automaticamente)
- ✅ Filtro por faixa de horário (slider duplo)
- ✅ Filtro por tipo: Missa, Confissão, Adoração
- ✅ Busca por nome, bairro ou endereço
- ✅ Mapa com marcadores verdes (aberto) e âmbar (fechado)
- ✅ Popup no mapa com resumo e botão para detalhes
- ✅ Modal com horário completo semanal
- ✅ Link direto para Google Maps de cada local
- ✅ Links para Instagram das paróquias
- ✅ Responsivo para celular

## ⚠️ Observações

- Os horários foram extraídos do documento da Arquidiocese de Teresina (17/04/2026)
- Confirme sempre com a paróquia antes de ir, pois podem haver alterações
- As coordenadas geográficas são aproximadas por bairro; ajuste conforme necessário
