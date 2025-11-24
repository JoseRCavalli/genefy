# GUIA DE IMPLEMENTAÇÃO - SISTEMA COMPLETO DE GENÉTICA BOVINA

## SITUAÇÃO ATUAL

### Banco de Dados
- **Arquivo:** `database/cattle_breeding.db`
- **Registros:** 469 fêmeas
- **Colunas atuais:** 23 colunas (apenas 13 índices genéticos)
- **Problema:** Dados incompletos, faltam ~70 índices importantes

### Excel
- **Arquivo:** `uploads/Females All List - 2025-11-03.xlsx`
- **Colunas:** 165 colunas com dados completos
- **Registros:** 469 linhas

## OBJETIVO
Importar TODOS os 165 campos do Excel para o banco de dados, criando colunas dedicadas para os ~70 índices mais importantes e mantendo o restante em JSON.

---

## ETAPA 1: BACKUP DO BANCO

**CRÍTICO:** Sempre fazer backup antes de qualquer modificação!

```bash
python backup_database.py
```

Isso criará: `database/backups/cattle_breeding_backup_YYYYMMDD_HHMMSS.db`

---

## ETAPA 2: MIGRAÇÃO - ADICIONAR NOVOS ÍNDICES

### Índices a serem adicionados como colunas (70+ campos):

#### Identificação e Genômico
- `gINB` (genomic_inbreeding - já existe)
- `gEFI` (genomic_future_inbreeding)
- `test_type` (tipo de teste genômico)
- `cdcb` (código CDCB)

#### Dados do Pedigree
- `sire_reg`, `sire_naab`, `sire_name`
- `dam_reg`, `dam_id`
- `mgs_reg`, `mgs_naab`, `mgs_name` (pai da mãe)

#### Índices Econômicos
- `cheese_merit` (mérito para queijo)
- `fluid_merit` (mérito para leite fluido)
- `grazing_merit` (mérito para pastejo)
- `jpi` (Jersey Performance Index)
- `eco_dollars` (Eco$)

#### Eficiência Alimentar
- `feed_efficiency`
- `rfi` (Residual Feed Intake)
- `ecofeed_life`
- `ecofeed_heifer`
- `ecofeed_cow`
- `eco2feed`
- `rci`, `doi`

#### Fertilidade (expandido)
- `heifer_conception_rate` (HCR)
- `cow_conception_rate` (CCR)
- `early_first_calving` (EFC)

#### Facilidade de Parto
- `daughter_calving_ease` (DCE)
- `sire_calving_ease` (SCE)
- `daughter_stillbirth` (DSB)
- `sire_stillbirth` (SSB)

#### Saúde e Longevidade
- `health_index`
- `heifer_livability`
- `livability`
- `mastitis`
- `metritis`
- `displaced_abomasum` (DA)
- `milk_fever`
- `retained_placenta`
- `ketosis`

#### Conformação/Tipo (adicionais)
- `bde`, `dfm`, `fls`, `fta`, `ftp`, `fua`
- `rlr`, `rls`, `rpa`, `rtp`, `ruh`, `ruw`
- `sta`, `str`, `tlg`, `trw`
- `ucl`, `udp`
- `jui` (Jersey Type Index)

#### Genótipos
- `beta_casein` (A1A1, A1A2, A2A2)
- `kappa_casein` (AA, AB, BB, AE, etc.)
- `blg_betalacto` (Beta-Lactoglobulina)
- `dgat` (DGAT1)
- `dominant_red`
- `red_factor`
- `slick` (gene do calor)

#### Sustentabilidade
- `vei` (Valor Econômico Integrado)
- `vea` (Valor Econômico Ambiental)
- `bt` (Body Temperature)
- `ems`

#### Haplótipos (status)
- `hh1`, `hh2`, `hh3`, `hh4`, `hh5`, `hh6` (Holstein)
- `ah1`, `ah2` (Ayrshire)
- `jh1`, `jh2` (Jersey)
- `bh1`, `bh2` (Brown Swiss)

#### Outros
- `milking_speed`
- `ooc` (Oocyte Competence)

### Script de Migração

```bash
python database/migrations/migration_add_all_indices.py
```

Este script irá:
1. Verificar backup
2. Adicionar as novas colunas à tabela `females`
3. Adicionar índices para queries rápidas
4. Atualizar o modelo SQLAlchemy

---

## ETAPA 3: IMPORTAÇÃO COMPLETA DOS DADOS

### Script de Importação

```bash
python import_excel_complete.py
```

Este script irá:
1. Ler todas as 165 colunas do Excel
2. Para cada fêmea:
   - Atualizar as colunas dedicadas (70+ campos)
   - Armazenar campos restantes em `genetic_data` (JSON)
   - Preservar dados existentes
3. Gerar relatório detalhado de importação

### Mapeamento de Colunas

| Excel | Banco | Tipo |
|-------|-------|------|
| REG ID | reg_id | VARCHAR |
| ID | internal_id | VARCHAR |
| BDATE | birth_date | DATE |
| BREED | breed | VARCHAR |
| gINB | genomic_inbreeding | FLOAT |
| gEFI | genomic_future_inbreeding | FLOAT |
| NET MERIT | net_merit | FLOAT |
| TPI | tpi | FLOAT |
| ... | ... | ... |

---

## ETAPA 4: ATUALIZAR MÓDULO DE GENÉTICA

### Melhorias no `backend/services/genetics_complete.py`:

1. **Cálculo de PPPV mais preciso:**
   - Usar TODOS os índices disponíveis
   - Considerar confiabilidades (REL)
   - Calcular intervalos de confiança

2. **Análise de Consanguinidade aprimorada:**
   - Usar gINB e gEFI quando disponíveis
   - Detectar haplótipos recessivos (HH1-HH6)
   - Alertas para combinações de risco
   - Cálculo de COI (Coefficient of Inbreeding)

3. **Score de Compatibilidade expandido:**
   - Incluir saúde, eficiência alimentar
   - Considerar sustentabilidade (Eco$, VEI)
   - Análise de complementaridade genética

4. **Predições econômicas:**
   - Lifetime profit usando NM$
   - Impacto ambiental (Eco2Feed)
   - ROI por acasalamento

### Novas Funções:

```python
def detect_haplotype_risks(female_data, bull_data):
    """Detecta riscos de haplótipos recessivos letais"""
    pass

def calculate_true_inbreeding(female_data, bull_data):
    """Calcula consanguinidade genômica real usando gINB + pedigree"""
    pass

def predict_economic_value(pppv_data, prices):
    """Prediz valor econômico lifetime da progênie"""
    pass

def analyze_complementarity(female_data, bull_data, priorities):
    """Analisa complementaridade genética detalhada"""
    pass
```

---

## ETAPA 5: ATUALIZAR ROTAS DA API

### Endpoints a modificar:

#### 1. GET `/api/females/<id>`
Retornar TODOS os índices:
```json
{
  "id": 1,
  "reg_id": "10008",
  "main_indices": {
    "milk": 1234,
    "protein": 45,
    // ... todos os 70+ índices
  },
  "genotypes": {
    "beta_casein": "A2A2",
    "kappa_casein": "AB"
  },
  "haplotypes": {
    "hh1": "Free",
    "hh2": "Free",
    // ...
  },
  "health": {
    "health_index": 105,
    "mastitis": 2.1,
    // ...
  },
  "efficiency": {
    "rfi": -123,
    "feed_efficiency": 98,
    // ...
  },
  "sustainability": {
    "eco_dollars": 118,
    "vei": 3.0,
    // ...
  }
}
```

#### 2. POST `/api/mating/predict`
Retornar análise completa:
```json
{
  "pppv": {
    // TODOS os índices preditos
  },
  "inbreeding": {
    "expected_coi": 4.2,
    "genomic_inbreeding": 3.8,
    "haplotype_risks": []
  },
  "compatibility_score": 87.5,
  "economic_prediction": {
    "lifetime_profit": 1250,
    "eco_impact": "low"
  },
  "health_prediction": {
    "disease_resistance": "high",
    "longevity": "above_average"
  }
}
```

#### 3. GET `/api/females` (listagem)
Adicionar filtros por:
- Genótipos (A2A2, etc.)
- Haplótipos
- Saúde
- Eficiência alimentar
- Sustentabilidade

---

## ETAPA 6: TESTES

### 1. Teste de Importação
```bash
python -m pytest tests/test_import_complete.py -v
```

### 2. Teste de Genética
```bash
python -m pytest tests/test_genetics_complete.py -v
```

### 3. Teste de API
```bash
python -m pytest tests/test_api_complete.py -v
```

### 4. Teste Manual
```bash
# Iniciar servidor
python app.py

# Testar endpoints
curl http://localhost:5000/api/females/1
curl -X POST http://localhost:5000/api/mating/predict -d '{"female_id": 1, "bull_id": 5}'
```

---

## CHECKLIST DE EXECUÇÃO

- [ ] 1. Fazer backup do banco
- [ ] 2. Executar migração (adicionar colunas)
- [ ] 3. Executar importação completa
- [ ] 4. Verificar dados importados
- [ ] 5. Atualizar módulo de genética
- [ ] 6. Atualizar rotas da API
- [ ] 7. Testar cada endpoint
- [ ] 8. Validar cálculos de PPPV
- [ ] 9. Validar análise de consanguinidade
- [ ] 10. Testar detecção de haplótipos

---

## ESTRUTURA FINAL DO BANCO

```
females (93 colunas totais)
├── Identificação (7)
│   ├── id, reg_id, internal_id, name
│   ├── birth_date, breed, cdcb
├── Genômico (3)
│   ├── genomic_inbreeding (gINB)
│   ├── genomic_future_inbreeding (gEFI)
│   └── test_type
├── Pedigree (9)
│   ├── sire_reg, sire_naab, sire_name
│   ├── dam_reg, dam_id
│   └── mgs_reg, mgs_naab, mgs_name
├── Produção (8)
│   ├── milk, protein, fat
│   ├── fat_percent, protein_percent
│   ├── jpi
├── Econômicos (6)
│   ├── net_merit, tpi
│   ├── cheese_merit, fluid_merit, grazing_merit
│   └── eco_dollars
├── Fertilidade (7)
│   ├── dpr, hcr, ccr
│   ├── fertility_index
│   └── early_first_calving
├── Funcionalidade (3)
│   ├── productive_life, scs
│   └── milking_speed
├── Facilidade Parto (4)
│   ├── daughter_calving_ease, sire_calving_ease
│   └── daughter_stillbirth, sire_stillbirth
├── Saúde (10)
│   ├── health_index, heifer_livability, livability
│   ├── mastitis, metritis, displaced_abomasum
│   └── milk_fever, retained_placenta, ketosis
├── Tipo/Conformação (20)
│   ├── ptat, udc, flc, jui
│   ├── bde, dfm, fls, fta, ftp, fua
│   ├── rlr, rls, rpa, rtp, ruh, ruw
│   └── sta, str, tlg, trw, ucl, udp
├── Eficiência (9)
│   ├── feed_efficiency, rfi
│   ├── ecofeed_life, ecofeed_heifer, ecofeed_cow
│   ├── eco2feed, rci, doi
├── Genótipos (7)
│   ├── beta_casein, kappa_casein
│   ├── blg_betalacto, dgat
│   ├── dominant_red, red_factor, slick
├── Haplótipos (14)
│   ├── hh1-hh6 (Holstein)
│   ├── ah1-ah2 (Ayrshire)
│   ├── jh1-jh2 (Jersey)
│   └── bh1-bh2 (Brown Swiss)
├── Sustentabilidade (5)
│   ├── vei, vea, bt, ems, ooc
├── Metadata (4)
│   ├── last_updated, is_active, notes
│   └── genetic_data (JSON com campos restantes)
```

---

## COMANDOS RÁPIDOS

```bash
# 1. Backup
python backup_database.py

# 2. Migração
python database/migrations/migration_add_all_indices.py

# 3. Importação
python import_excel_complete.py

# 4. Verificar
python check_import_results.py

# 5. Testar API
python app.py
```

---

## OBSERVAÇÕES IMPORTANTES

1. **Sempre fazer backup antes de qualquer alteração!**
2. **Preservar dados existentes** - nunca sobrescrever sem verificar
3. **Validar cada etapa** antes de prosseguir
4. **Manter genetic_data** para campos não mapeados
5. **Usar transações** para garantir integridade dos dados
6. **Logar todas as operações** para auditoria

---

## PRÓXIMOS PASSOS (PÓS-IMPLEMENTAÇÃO)

1. Implementar cache para queries pesadas
2. Adicionar análise de tendências genéticas do rebanho
3. Criar relatórios automáticos de progresso genético
4. Implementar sistema de recomendações baseado em ML
5. Adicionar visualizações de distribuição de índices
