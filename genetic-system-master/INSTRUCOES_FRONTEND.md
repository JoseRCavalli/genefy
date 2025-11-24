# INSTRUÇÕES - ATUALIZAÇÃO DO FRONTEND

## ✅ O QUE JÁ FOI FEITO:

### 1. Correção de Encoding
- ✓ Adicionado forçamento UTF-8 em `backend/services/importer.py`
- ✓ Tratamento de caracteres especiais já implementado

### 2. Arquivos CSS e JS Criados
- ✓ `frontend/css/indices.css` - Estilos para visualização completa
- ✓ `frontend/js/indices.js` - Funções JavaScript para renderizar índices

## 📋 O QUE VOCÊ PRECISA FAZER:

### PASSO 1: Adicionar CSS e JS nas Páginas HTML

Em **TODAS** estas páginas, adicione no `<head>`:
- `frontend/pages/index.html`
- `frontend/pages/import.html`
- `frontend/pages/manual.html`
- `frontend/pages/batch.html`

```html
<link rel="stylesheet" href="/css/indices.css">
<script src="/js/indices.js"></script>
```

### PASSO 2: Atualizar Página de Importação (`import.html`)

Adicione após a mensagem de sucesso na importação:

```html
<!-- Resumo dos Índices Importados -->
<div id="indices-summary-container"></div>

<!-- Todos os Índices por Categoria -->
<div id="indices-complete-container"></div>

<script>
// Quando receber dados da importação (response.data)
function mostrarIndicesImportados(femaleData) {
    // Renderizar resumo
    renderIndicesSummary(femaleData, 'indices-summary-container');

    // Renderizar todos os índices
    renderIndicesComplete(femaleData, 'indices-complete-container');
}

// Chamar após sucesso da importação:
// mostrarIndicesImportados(response.data.female);
</script>
```

### PASSO 3: Atualizar Página de Acasalamento Manual (`manual.html`)

Adicione na seção de resultados da análise:

```html
<!-- Análise Completa -->
<div class="analysis-results" style="display: none;" id="analysis-results">
    <h2>Análise de Acasalamento Completo</h2>

    <!-- Resumo -->
    <div class="score-display">
        <div class="score-value" id="compatibility-score">0</div>
        <div class="score-grade" id="compatibility-grade">-</div>
    </div>

    <!-- Avisos e Destaques -->
    <div id="warnings-container"></div>
    <div id="highlights-container"></div>

    <!-- PPPV por Categoria -->
    <h3>PPPV Predito por Categoria</h3>
    <div id="pppv-categories"></div>

    <!-- Análise de Consanguinidade -->
    <div class="inbreeding-analysis">
        <h3>🧬 Análise de Consanguinidade</h3>
        <div class="inbreeding-details" id="inbreeding-details"></div>
        <div class="haplotype-risks" id="haplotype-risks"></div>
    </div>
</div>

<script>
// Quando analisar acasalamento
async function analisarAcasalamento(femaleId, bullId) {
    const response = await fetch('/api/matings/analyze_complete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ female_id: femaleId, bull_id: bullId })
    });

    const result = await response.json();

    // Mostrar score
    document.getElementById('compatibility-score').textContent = result.analysis.compatibility.score;
    document.getElementById('compatibility-grade').textContent = result.analysis.compatibility.grade;

    // Mostrar avisos
    const warningsHtml = result.recommendation.warnings.map(w =>
        `<div class="warning">${w.message}</div>`
    ).join('');
    document.getElementById('warnings-container').innerHTML = warningsHtml;

    // Mostrar destaques
    const highlightsHtml = result.recommendation.highlights.map(h =>
        `<div class="highlight">${h}</div>`
    ).join('');
    document.getElementById('highlights-container').innerHTML = highlightsHtml;

    // Renderizar PPPV por categoria
    renderPPPVCategories(result.analysis.pppv_complete);

    // Renderizar consanguinidade
    renderInbreedingAnalysis(result.analysis.inbreeding_analysis);

    // Mostrar resultados
    document.getElementById('analysis-results').style.display = 'block';
}

function renderPPPVCategories(pppv) {
    let html = '<div class="indices-container">';

    for (const [category, indices] of Object.entries(pppv)) {
        if (Object.keys(indices).length === 0) continue;

        html += `<div class="category">
            <h4>${getCategoryTitle(category)}</h4>
            <div class="index-grid">`;

        for (const [index, data] of Object.entries(indices)) {
            html += `
                <div class="index-item">
                    <span class="label">${INDICES_LABELS[index] || index}</span>
                    <div class="pppv-values">
                        <small>Fêmea: ${data.female}</small>
                        <small>Touro: ${data.bull}</small>
                        <strong>PPPV: ${formatIndexValue(index, data.pppv)}</strong>
                    </div>
                </div>
            `;
        }

        html += `</div></div>`;
    }

    html += '</div>';
    document.getElementById('pppv-categories').innerHTML = html;
}

function renderInbreedingAnalysis(inbreeding) {
    const html = `
        <div class="inbreeding-stats">
            <div class="stat">
                <span>Consanguinidade Esperada:</span>
                <strong class="${inbreeding.risk_level.toLowerCase()}">${inbreeding.expected_inbreeding}%</strong>
            </div>
            <div class="stat">
                <span>Nível de Risco:</span>
                <strong>${inbreeding.risk_level}</strong>
            </div>
            <div class="stat">
                <span>Recomendação:</span>
                <p>${inbreeding.recommendation}</p>
            </div>
        </div>
    `;
    document.getElementById('inbreeding-details').innerHTML = html;

    // Riscos de haplótipos
    if (inbreeding.haplotype_risks && inbreeding.haplotype_risks.length > 0) {
        const risksHtml = inbreeding.haplotype_risks.map(risk => `
            <div class="haplotype-risk ${risk.risk.startsWith('ALTO') ? 'high' : 'low'}">
                <h5>${risk.haplotype}</h5>
                <p>Fêmea: ${risk.female_status} | Touro: ${risk.bull_status}</p>
                <p><strong>${risk.risk}</strong></p>
                <p>${risk.recommendation}</p>
            </div>
        `).join('');
        document.getElementById('haplotype-risks').innerHTML = risksHtml;
    }
}

function getCategoryTitle(category) {
    const titles = {
        production: '🥛 Produção',
        economic: '💰 Econômicos',
        fertility: '🐄 Fertilidade',
        health: '🏥 Saúde',
        type: '📐 Tipo',
        efficiency: '⚡ Eficiência',
        sustainability: '🌱 Sustentabilidade',
        calving: '🐮 Parto'
    };
    return titles[category] || category;
}
</script>
```

### PASSO 4: Atualizar Dashboard (`index.html`)

Adicione uma nova seção para mostrar estatísticas completas:

```html
<div class="dashboard-indices">
    <h2>Índices do Rebanho</h2>

    <!-- Tabs por categoria -->
    <div class="indices-tabs">
        <button class="tab-button active" onclick="showTab('economic')">Econômicos</button>
        <button class="tab-button" onclick="showTab('production')">Produção</button>
        <button class="tab-button" onclick="showTab('health')">Saúde</button>
        <button class="tab-button" onclick="showTab('fertility')">Fertilidade</button>
        <button class="tab-button" onclick="showTab('efficiency')">Eficiência</button>
    </div>

    <div id="indices-dashboard-container"></div>
</div>

<script>
function showTab(category) {
    // Implementar lógica de tabs
    document.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');

    // Carregar dados da categoria
    loadCategoryData(category);
}

async function loadCategoryData(category) {
    // Buscar estatísticas do rebanho
    const response = await fetch(`/api/analytics/distributions?category=${category}`);
    const data = await response.json();

    // Renderizar gráficos/estatísticas
    // ...
}
</script>
```

### PASSO 5: Adicionar Estilos CSS Adicionais

Adicione em `frontend/css/main.css` ou crie `custom.css`:

```css
/* Avisos e Destaques */
.warning {
    background: #fff3cd;
    border-left: 4px solid #ffc107;
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 4px;
}

.highlight {
    background: #d4edda;
    border-left: 4px solid #28a745;
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 4px;
}

/* Score de Compatibilidade */
.score-display {
    text-align: center;
    padding: 2rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 12px;
    margin: 1rem 0;
}

.score-value {
    font-size: 4rem;
    font-weight: 700;
}

.score-grade {
    font-size: 1.5rem;
    opacity: 0.9;
}

/* Riscos de Haplótipos */
.haplotype-risk {
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 8px;
    border-left: 4px solid;
}

.haplotype-risk.high {
    background: #f8d7da;
    border-left-color: #dc3545;
}

.haplotype-risk.low {
    background: #fff3cd;
    border-left-color: #ffc107;
}

/* PPPV Values */
.pppv-values {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.pppv-values small {
    font-size: 0.75rem;
    color: #6c757d;
}
```

## 🧪 TESTE A IMPLEMENTAÇÃO:

### 1. Reiniciar Servidor
```bash
# Parar servidor atual (Ctrl+C) e reiniciar
cd genetic-system-master
PORT=8000 python app.py
```

### 2. Testar Importação
- Acesse: http://localhost:8000/import
- Faça upload do arquivo Excel
- Verifique se TODOS os índices aparecem organizados por categoria

### 3. Testar Acasalamento Manual
- Acesse: http://localhost:8000/manual
- Selecione uma fêmea e um touro
- Analise o acasalamento
- Verifique se mostra:
  - Score de compatibilidade
  - PPPV completo por categoria
  - Análise de consanguinidade com haplótipos
  - Avisos e destaques

## 📊 ESTRUTURA FINAL:

```
frontend/
├── css/
│   ├── main.css (existente)
│   ├── indices.css (✓ NOVO - criado)
│   └── custom.css (criar)
├── js/
│   ├── indices.js (✓ NOVO - criado)
│   └── main.js (atualizar)
└── pages/
    ├── index.html (atualizar)
    ├── import.html (atualizar)
    ├── manual.html (atualizar)
    └── batch.html (atualizar)
```

## ✅ CHECKLIST:

- [ ] Adicionar `<link>` para indices.css em todas as páginas
- [ ] Adicionar `<script>` para indices.js em todas as páginas
- [ ] Atualizar import.html com containers para índices
- [ ] Atualizar manual.html com análise completa
- [ ] Atualizar dashboard com tabs de categorias
- [ ] Adicionar CSS customizado para warnings/highlights
- [ ] Testar importação e verificar todos os índices
- [ ] Testar acasalamento e verificar análise completa
- [ ] Testar em diferentes navegadores

## 🔧 TROUBLESHOOTING:

Se os índices não aparecerem:
1. Verifique o console do navegador (F12)
2. Confirme que os arquivos CSS/JS foram carregados
3. Verifique se a API retorna `complete=true` nos dados
4. Teste a função `renderIndicesComplete()` manualmente no console

---

**Os arquivos CSS e JS já estão prontos e funcionais!**
Basta seguir os passos acima para integrar nas páginas HTML.
