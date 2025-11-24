/**
 * Funções para exibição e manipulação de índices genéticos
 */

// Definição das categorias de índices
const INDICES_CATEGORIES = {
    economic: {
        title: '💰 Econômicos',
        indices: ['net_merit', 'tpi', 'cheese_merit', 'fluid_merit', 'grazing_merit', 'jpi', 'eco_dollars']
    },
    production: {
        title: '🥛 Produção',
        indices: ['milk', 'protein', 'fat', 'fat_percent', 'protein_percent']
    },
    health: {
        title: '🏥 Saúde',
        indices: ['health_index', 'scs', 'mastitis', 'metritis', 'displaced_abomasum', 'milk_fever', 'retained_placenta', 'ketosis', 'heifer_livability', 'livability']
    },
    fertility: {
        title: '🐄 Fertilidade',
        indices: ['dpr', 'heifer_conception_rate', 'cow_conception_rate', 'fertility_index', 'early_first_calving']
    },
    type: {
        title: '📐 Conformação/Tipo',
        indices: ['ptat', 'udc', 'flc', 'jui', 'bde', 'dfm', 'sta', 'str', 'fls', 'fta', 'ftp', 'fua', 'rlr', 'rls', 'rpa', 'rtp', 'ruh', 'ruw', 'tlg', 'trw', 'ucl', 'udp']
    },
    efficiency: {
        title: '⚡ Eficiência',
        indices: ['feed_efficiency', 'rfi', 'ecofeed_life', 'ecofeed_heifer', 'ecofeed_cow', 'rci', 'doi']
    },
    sustainability: {
        title: '🌱 Sustentabilidade',
        indices: ['eco2feed', 'vei', 'vea', 'bt', 'ems', 'milking_speed', 'ooc']
    },
    calving: {
        title: '🐮 Facilidade de Parto',
        indices: ['daughter_calving_ease', 'sire_calving_ease', 'daughter_stillbirth', 'sire_stillbirth']
    },
    genotypes: {
        title: '🧬 Genótipos',
        indices: ['beta_casein', 'kappa_casein', 'blg_betalacto', 'dgat', 'dominant_red', 'red_factor', 'slick']
    },
    longevity: {
        title: '⏳ Longevidade',
        indices: ['productive_life']
    }
};

// Labels amigáveis para os índices
const INDICES_LABELS = {
    net_merit: 'NM$',
    tpi: 'TPI',
    cheese_merit: 'CM$',
    fluid_merit: 'FM$',
    grazing_merit: 'GM$',
    jpi: 'JPI',
    eco_dollars: 'Eco$',
    milk: 'Leite (lbs)',
    protein: 'Proteína (lbs)',
    fat: 'Gordura (lbs)',
    fat_percent: 'Gordura %',
    protein_percent: 'Proteína %',
    health_index: 'Health Index',
    scs: 'SCS',
    mastitis: 'Mastite',
    metritis: 'Metrite',
    displaced_abomasum: 'DA',
    milk_fever: 'Milk Fever',
    retained_placenta: 'RP',
    ketosis: 'Cetose',
    heifer_livability: 'Heifer Livab.',
    livability: 'Livability',
    dpr: 'DPR',
    heifer_conception_rate: 'HCR',
    cow_conception_rate: 'CCR',
    fertility_index: 'Fert. Index',
    early_first_calving: 'EFC',
    ptat: 'PTAT',
    udc: 'UDC',
    flc: 'FLC',
    jui: 'JUI',
    bde: 'BDE',
    dfm: 'DFM',
    sta: 'STA',
    str: 'STR',
    fls: 'FLS',
    fta: 'FTA',
    ftp: 'FTP',
    fua: 'FUA',
    rlr: 'RLR',
    rls: 'RLS',
    rpa: 'RPA',
    rtp: 'RTP',
    ruh: 'RUH',
    ruw: 'RUW',
    tlg: 'TLG',
    trw: 'TRW',
    ucl: 'UCL',
    udp: 'UDP',
    feed_efficiency: 'Feed Eff.',
    rfi: 'RFI',
    ecofeed_life: 'EcoFeed Life',
    ecofeed_heifer: 'EcoFeed Heifer',
    ecofeed_cow: 'EcoFeed Cow',
    rci: 'RCI',
    doi: 'DOI',
    eco2feed: 'Eco2Feed',
    vei: 'VEI',
    vea: 'VEA',
    bt: 'BT',
    ems: 'EMS',
    milking_speed: 'Milking Speed',
    ooc: 'OOC',
    daughter_calving_ease: 'DCE',
    sire_calving_ease: 'SCE',
    daughter_stillbirth: 'DSB',
    sire_stillbirth: 'SSB',
    beta_casein: 'Beta Caseína',
    kappa_casein: 'Kappa Caseína',
    blg_betalacto: 'BLG',
    dgat: 'DGAT',
    dominant_red: 'Dom. Red',
    red_factor: 'Red Factor',
    slick: 'Slick',
    productive_life: 'Prod. Life'
};

/**
 * Formata valor de índice com sinal e cor
 */
function formatIndexValue(index, value) {
    if (value === null || value === undefined || value === '') {
        return '<span class="value na">N/A</span>';
    }

    const numValue = parseFloat(value);
    if (isNaN(numValue)) {
        // Valor textual (genótipos)
        return `<span class="value neutral">${value}</span>`;
    }

    // Determinar classe baseado no valor
    let cssClass = 'neutral';
    let sign = '';

    // Índices onde menor é melhor (invertidos)
    const lowerIsBetter = ['scs', 'rfi', 'daughter_stillbirth', 'sire_stillbirth'];

    if (lowerIsBetter.includes(index)) {
        if (numValue < 0) {
            cssClass = 'positive';
            sign = '';
        } else if (numValue > 0) {
            cssClass = 'negative';
            sign = '+';
        }
    } else {
        if (numValue > 0) {
            cssClass = 'positive';
            sign = '+';
        } else if (numValue < 0) {
            cssClass = 'negative';
            sign = '';
        }
    }

    const formattedValue = Math.abs(numValue) >= 1000
        ? numValue.toFixed(0)
        : numValue.toFixed(1);

    return `<span class="value ${cssClass}">${sign}${formattedValue}</span>`;
}

/**
 * Renderiza todos os índices organizados por categoria
 */
function renderIndicesComplete(data, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    let html = '<div class="indices-container">';

    for (const [categoryKey, category] of Object.entries(INDICES_CATEGORIES)) {
        const categoryClass = `category ${categoryKey}`;

        html += `
            <div class="${categoryClass}">
                <div class="category-header" onclick="toggleCategory(this)">
                    <h3>${category.title}</h3>
                    <span class="toggle-icon">▼</span>
                </div>
                <div class="index-grid">
        `;

        for (const indexKey of category.indices) {
            const label = INDICES_LABELS[indexKey] || indexKey.toUpperCase();
            let value = null;

            // Tentar pegar valor de diferentes estruturas
            if (data[indexKey] !== undefined) {
                value = data[indexKey];
            } else if (data.main_indices && data.main_indices[indexKey] !== undefined) {
                value = data.main_indices[indexKey];
            } else if (data[categoryKey] && data[categoryKey][indexKey] !== undefined) {
                value = data[categoryKey][indexKey];
            } else if (data.production && data.production[indexKey] !== undefined) {
                value = data.production[indexKey];
            } else if (data.economic && data.economic[indexKey] !== undefined) {
                value = data.economic[indexKey];
            } else if (data.health && data.health[indexKey] !== undefined) {
                value = data.health[indexKey];
            } else if (data.fertility && data.fertility[indexKey] !== undefined) {
                value = data.fertility[indexKey];
            } else if (data.type && data.type[indexKey] !== undefined) {
                value = data.type[indexKey];
            } else if (data.efficiency && data.efficiency[indexKey] !== undefined) {
                value = data.efficiency[indexKey];
            } else if (data.sustainability && data.sustainability[indexKey] !== undefined) {
                value = data.sustainability[indexKey];
            } else if (data.calving && data.calving[indexKey] !== undefined) {
                value = data.calving[indexKey];
            } else if (data.genotypes && data.genotypes[indexKey] !== undefined) {
                value = data.genotypes[indexKey];
            }

            html += `
                <div class="index-item">
                    <span class="label">${label}</span>
                    ${formatIndexValue(indexKey, value)}
                </div>
            `;
        }

        html += `
                </div>
            </div>
        `;
    }

    html += '</div>';
    container.innerHTML = html;
}

/**
 * Toggle collapse/expand de categoria
 */
function toggleCategory(element) {
    const category = element.closest('.category');
    category.classList.toggle('collapsed');
}

/**
 * Renderiza resumo de estatísticas
 */
function renderIndicesSummary(data, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const stats = {
        'NM$': data.net_merit || data.main_indices?.net_merit,
        'TPI': data.tpi || data.main_indices?.tpi,
        'Milk': data.milk || data.main_indices?.milk,
        'PL': data.productive_life || data.main_indices?.productive_life
    };

    let html = '<div class="indices-summary">';
    for (const [label, value] of Object.entries(stats)) {
        if (value !== null && value !== undefined) {
            const formatted = parseFloat(value).toFixed(0);
            const sign = value > 0 ? '+' : '';
            html += `
                <div class="summary-card">
                    <h4>${label}</h4>
                    <div class="value">${sign}${formatted}</div>
                </div>
            `;
        }
    }
    html += '</div>';
    container.innerHTML = html;
}
