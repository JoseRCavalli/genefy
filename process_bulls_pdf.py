#!/usr/bin/env python3
"""
GENEFY - Parser UNIVERSAL de PDF de Touros
==========================================

Este parser foi projetado para capturar dados de touros de QUALQUER formato de PDF,
incluindo diferentes labs (CDCB, Interbull, etc) e diferentes layouts.

ESTRATÉGIA:
1. Extrair TODOS os números do texto
2. Identificar padrões conhecidos (código do touro, nome, etc)
3. Usar múltiplos padrões regex para cada campo
4. Buscar por contexto (palavras próximas aos valores)
5. Validar valores extraídos (ranges esperados)

Uso:
    python3 universal_bull_parser.py <pdf_path> [database_path]
"""

import re
import json
import sys
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple


class UniversalBullParser:
    """Parser universal para PDFs de touros - captura qualquer formato"""
    
    def __init__(self):
        # Ranges válidos para validação
        self.valid_ranges = {
            'milk': (-2000, 4000),
            'protein': (-100, 200),
            'fat': (-100, 200),
            'net_merit': (-500, 2000),
            'cheese_merit': (-500, 2000),
            'grazing_merit': (-500, 2000),
            'gtpi': (1500, 4000),
            'tpi': (1500, 4000),
            'productive_life': (-5, 15),
            'scs': (1.5, 4.0),
            'dpr': (-5, 10),
            'hcr': (-10, 15),
            'ccr': (-10, 15),
            'fertility_index': (-5, 15),
            'udc': (-3, 4),
            'flc': (-3, 4),
            'ptat': (-3, 5),
            'gfi': (0, 20),
            'feed_saved': (-200, 500),
            'rfi': (-100, 100),
        }
        
        # Aliases para nomes de campos (diferentes idiomas/labs)
        self.field_aliases = {
            'milk': ['milk', 'leite', 'latte', 'milch', 'ptam', 'pta milk', 'milk pta'],
            'protein': ['protein', 'proteina', 'proteína', 'prot', 'pta protein'],
            'fat': ['fat', 'gordura', 'grasa', 'fett', 'pta fat'],
            'net_merit': ['nm$', 'ml$', 'net merit', 'merito neto', 'mérito líquido', 'nm'],
            'cheese_merit': ['cm$', 'mq$', 'cheese merit', 'merito queso'],
            'grazing_merit': ['gm$', 'grazing merit', 'merito pastoreo'],
            'gtpi': ['gtpi', 'tpi', 'gpta', 'índice total'],
            'productive_life': ['pl', 'productive life', 'vida produtiva', 'longevity', 'longevidade'],
            'scs': ['scs', 'células somáticas', 'somatic cell', 'ccs'],
            'dpr': ['dpr', 'daughter pregnancy', 'preñez filhas', 'indice preñez'],
            'hcr': ['hcr', 'heifer conception', 'concepción novillas'],
            'ccr': ['ccr', 'cow conception', 'concepción vacas'],
            'fertility_index': ['fi', 'fertility index', 'índice fertilidade', 'fertilidad'],
            'udc': ['udc', 'udder composite', 'úbere', 'ubre'],
            'flc': ['flc', 'feet legs', 'pés pernas', 'patas'],
            'ptat': ['ptat', 'type', 'tipo', 'conformación'],
            'gfi': ['gfi', 'genomic future', 'consanguinidad futura'],
            'feed_saved': ['feed saved', 'alimento economizado', 'ahorro alimento'],
            'rfi': ['rfi', 'residual feed', 'consumo residual'],
        }
    
    def _extract_bull_code(self, text: str) -> Optional[str]:
        """Extrai código do touro - formato XXX?HO?XXXXX"""
        patterns = [
            r'(\d{1,3}HO\d{4,6})',           # 551HO3797, 7HO17200
            r'(\d{3}HO\d{5})',                # 551HO03797
            r'([A-Z]{2,3}\d{5,8})',           # HOUSA000123456
            r'(HO\d{10,13})',                 # HO8403132350683
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def _extract_bull_name(self, text: str) -> Optional[str]:
        """Extrai nome do touro"""
        # Padrão: código seguido de nome em maiúsculas
        patterns = [
            r'\d+HO\d+\s+([A-Z][A-Z\-]+)',     # 551HO3797 TAMPA
            r'\d+HO\d+\s+([A-Z][A-Za-z\-]+)',  # 551HO3797 Tampa
            r'([A-Z][A-Z\-]+)-ET',              # TAMPA-ET
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                # Limpar sufixos comuns
                name = re.sub(r'-?(ET|PP|P|RED|RC)$', '', name).strip()
                if len(name) >= 2:
                    return name
        return None
    
    def _find_value_near_label(self, text: str, labels: List[str], 
                                value_type: str = 'int',
                                search_range: int = 50) -> Optional[Tuple[Any, Optional[int]]]:
        """
        Encontra um valor numérico próximo a um label.
        
        Args:
            text: Texto do PDF
            labels: Lista de possíveis labels para o campo
            value_type: 'int', 'float', 'percent'
            search_range: Quantos caracteres procurar após o label
            
        Returns:
            Tuple (valor, reliability) ou None
        """
        text_lower = text.lower()
        
        for label in labels:
            # Encontrar posição do label
            pos = text_lower.find(label.lower())
            if pos == -1:
                continue
            
            # Pegar texto após o label
            search_text = text[pos:pos + search_range]
            
            # Procurar valor numérico
            if value_type == 'int':
                match = re.search(r'[+\-]?([\d,]+)', search_text)
                if match:
                    try:
                        value = int(match.group(1).replace(',', ''))
                        # Procurar reliability (XX%)
                        rel_match = re.search(r'(\d{2})%', search_text)
                        rel = int(rel_match.group(1)) if rel_match else None
                        return (value, rel)
                    except:
                        pass
                        
            elif value_type == 'float':
                match = re.search(r'[+\-]?(\d+\.?\d*)', search_text)
                if match:
                    try:
                        value = float(match.group(1))
                        rel_match = re.search(r'(\d{2})%', search_text)
                        rel = int(rel_match.group(1)) if rel_match else None
                        return (value, rel)
                    except:
                        pass
        
        return None
    
    def _extract_all_dollar_values(self, text: str) -> List[int]:
        """Extrai todos os valores em dólar do texto"""
        matches = re.findall(r'\+?\$(\d{2,4})', text)
        return [int(m) for m in matches]
    
    def _extract_all_percentages(self, text: str) -> List[Tuple[float, int]]:
        """Extrai pares (valor, reliability%) do texto"""
        # Padrão: +X.X XX%C ou +X.X XX%
        matches = re.findall(r'([+\-]?\d+\.?\d*)\s+(\d{2})%', text)
        return [(float(v), int(r)) for v, r in matches]
    
    def _extract_haplotypes(self, text: str) -> Dict[str, str]:
        """Extrai status de haplótipos"""
        haplotypes = {}
        for i in range(1, 7):
            hap = f'HH{i}'
            if f'{hap}T' in text or f'{hap}F' in text:
                haplotypes[hap.lower()] = 'Free'
            elif f'{hap}C' in text:
                haplotypes[hap.lower()] = 'Carrier'
        return haplotypes
    
    def _extract_genotypes(self, text: str) -> Dict[str, str]:
        """Extrai genótipos (Beta-Casein, Kappa-Casein, etc)"""
        genotypes = {}
        
        # Beta-Casein
        match = re.search(r'Beta.?Casein[:\s]*(A1A1|A1A2|A2A2)', text, re.IGNORECASE)
        if match:
            genotypes['beta_casein'] = match.group(1).upper()
        
        # Kappa-Casein
        match = re.search(r'Kappa.?Casein[:\s]*(AA|AB|BB)', text, re.IGNORECASE)
        if match:
            genotypes['kappa_casein'] = match.group(1).upper()
        
        return genotypes
    
    def _validate_value(self, field: str, value: Any) -> bool:
        """Valida se o valor está dentro do range esperado"""
        if field not in self.valid_ranges:
            return True
        
        min_val, max_val = self.valid_ranges[field]
        try:
            return min_val <= float(value) <= max_val
        except:
            return False
    
    def parse_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extrai dados de um texto de PDF usando múltiplas estratégias.
        """
        bull = {}
        
        # === IDENTIFICAÇÃO ===
        code = self._extract_bull_code(text)
        if not code:
            return None
        
        bull['code'] = code
        
        name = self._extract_bull_name(text)
        if name:
            bull['name'] = name
        
        # Reg ID completo
        reg_match = re.search(r'HO(\d{10,13})', text)
        if reg_match:
            bull['reg_id'] = 'HO' + reg_match.group(1)
        
        # === ESTRATÉGIA 1: Valores em dólar (Net Merit, Cheese Merit, etc) ===
        dollar_values = self._extract_all_dollar_values(text)
        if len(dollar_values) >= 3:
            # Geralmente: Net Merit, Cheese Merit, Grazing Merit
            bull['net_merit'] = dollar_values[0]
            bull['cheese_merit'] = dollar_values[1]
            bull['grazing_merit'] = dollar_values[2]
            if len(dollar_values) >= 4:
                bull['fluid_merit'] = dollar_values[3]
        
        # === ESTRATÉGIA 2: Busca por contexto ===
        # Milk
        milk_patterns = [
            r'(?:Leite|Milk)\s*\+?([\d,]+)',
            r'GM\$\+?([\d,]+)',  # Formato SelectSires
            r'PTAM\s*\+?([\d,]+)',
        ]
        for pattern in milk_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = int(match.group(1).replace(',', ''))
                if self._validate_value('milk', value):
                    bull['milk'] = value
                    break
        
        # Reliability do milk
        rel_match = re.search(r'(\d{2})%\s*C/', text)
        if rel_match:
            bull['milk_rel'] = int(rel_match.group(1))
        
        # Protein e Fat
        prot_match = re.search(r'(?:Proteina|Protein)\s*\+?(\d{2,3})', text, re.IGNORECASE)
        if prot_match:
            bull['protein'] = int(prot_match.group(1))
        
        fat_match = re.search(r'(?:Gordura|Fat)\s*\+?(\d{2,3})', text, re.IGNORECASE)
        if fat_match:
            bull['fat'] = int(fat_match.group(1))
        
        # === ESTRATÉGIA 3: Pares valor+reliability ===
        # Vida Produtiva
        pl_patterns = [
            r'(?:Vida Produtiva|Productive Life|PL)\s*\+?(\d+\.?\d*)\s+(\d{2})%',
            r'\+(\d+\.\d)\s+(\d{2})%C.*?(?:Permanência|Livability)',
        ]
        for pattern in pl_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                bull['productive_life'] = float(match.group(1))
                bull['productive_life_rel'] = int(match.group(2))
                break
        
        # SCS
        scs_match = re.search(r'(?:Células Somáticas|Somatic Cell|SCS)\s*(\d+\.?\d*)\s+(\d{2})%', text, re.IGNORECASE)
        if scs_match:
            bull['scs'] = float(scs_match.group(1))
            bull['scs_rel'] = int(scs_match.group(2))
        
        # DPR
        dpr_patterns = [
            r'(?:Indice Preñez|DPR|Daughter Pregnancy)\s*\+?([+\-]?\d+\.?\d*)\s+(\d{2})%',
            r'DPR\s*\+?([+\-]?\d+\.?\d*)\s+(\d{2})%',
        ]
        for pattern in dpr_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                bull['dpr'] = float(match.group(1))
                bull['dpr_rel'] = int(match.group(2))
                break
        
        # HCR
        hcr_match = re.search(r'(?:Heifer Conception|HCR)\s*\+?([+\-]?\d+\.?\d*)\s+(\d{2})%', text, re.IGNORECASE)
        if hcr_match:
            bull['hcr'] = float(hcr_match.group(1))
            bull['hcr_rel'] = int(hcr_match.group(2))
        
        # CCR
        ccr_match = re.search(r'(?:Cow Conception|CCR)\s*\+?([+\-]?\d+\.?\d*)\s+(\d{2})%', text, re.IGNORECASE)
        if ccr_match:
            bull['ccr'] = float(ccr_match.group(1))
            bull['ccr_rel'] = int(ccr_match.group(2))
        
        # Fertility Index
        fi_match = re.search(r'(?:Índice de Fertilidade|Fertility Index|FI)\s*\+?([+\-]?\d+\.?\d*)\s+(\d{2})%', text, re.IGNORECASE)
        if fi_match:
            bull['fertility_index'] = float(fi_match.group(1))
            bull['fertility_index_rel'] = int(fi_match.group(2))
        
        # === TIPO ===
        # GTPI
        gtpi_patterns = [
            r'(?:GTPI|TPI)\s*\+?(\d{4})',
            r'Tipo\+(\d{4})',
        ]
        for pattern in gtpi_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = int(match.group(1))
                if self._validate_value('gtpi', value):
                    bull['gtpi'] = value
                    break
        
        # UDC, FLC, PTAT
        udc_match = re.search(r'UDC\s*\+?([+\-]?\d+\.?\d*)', text)
        if udc_match:
            bull['udc'] = float(udc_match.group(1))
        
        flc_match = re.search(r'FLC\s*\+?([+\-]?\d+\.?\d*)', text)
        if flc_match:
            bull['flc'] = float(flc_match.group(1))
        
        ptat_match = re.search(r'(?:PTAT|Tipo)\s*\+?([+\-]?\d+\.?\d*)\s+(\d{2})%', text, re.IGNORECASE)
        if ptat_match:
            bull['ptat'] = float(ptat_match.group(1))
            bull['ptat_rel'] = int(ptat_match.group(2))
        
        # === EFICIÊNCIA ===
        fs_match = re.search(r'Feed Saved\s*\+?([+\-]?\d+)\s+(\d{2})%', text, re.IGNORECASE)
        if fs_match:
            bull['feed_saved'] = int(fs_match.group(1))
            bull['feed_saved_rel'] = int(fs_match.group(2))
        
        rfi_match = re.search(r'RFI\s*([+\-]?\d+)\s+(\d{2})%', text)
        if rfi_match:
            bull['rfi'] = int(rfi_match.group(1))
            bull['rfi_rel'] = int(rfi_match.group(2))
        
        # Milking Speed
        ms_match = re.search(r'(?:Veloc|Milking Speed)\S*\s*(\d+\.?\d*)/(\d{2})%', text, re.IGNORECASE)
        if ms_match:
            bull['milking_speed'] = float(ms_match.group(1))
            bull['milking_speed_rel'] = int(ms_match.group(2))
        
        # === PARTO ===
        sce_match = re.search(r'(?:Facilidade.*?Touro|Sire Calving|SCE)\s*(\d+\.?\d*)\s+(\d{2})%', text, re.IGNORECASE)
        if sce_match:
            bull['sire_calving_ease'] = float(sce_match.group(1))
            bull['sire_calving_ease_rel'] = int(sce_match.group(2))
        
        dce_match = re.search(r'(?:Parto.*?Filhas|Daughter Calving|DCE)\s*(\d+\.?\d*)\s+(\d{2})%', text, re.IGNORECASE)
        if dce_match:
            bull['daughter_calving_ease'] = float(dce_match.group(1))
            bull['daughter_calving_ease_rel'] = int(dce_match.group(2))
        
        # Stillbirth
        ssb_match = re.search(r'(?:Mortes.*?Touros|Sire Stillbirth)\s*(\d+\.?\d*)\s+(\d{2})%', text, re.IGNORECASE)
        if ssb_match:
            bull['sire_stillbirth'] = float(ssb_match.group(1))
            bull['sire_stillbirth_rel'] = int(ssb_match.group(2))
        
        dsb_match = re.search(r'(?:Mortes.*?Filhas|Daughter Stillbirth)\s*(\d+\.?\d*)\s+(\d{2})%', text, re.IGNORECASE)
        if dsb_match:
            bull['daughter_stillbirth'] = float(dsb_match.group(1))
            bull['daughter_stillbirth_rel'] = int(dsb_match.group(2))
        
        # === WELLNESS ===
        wellness_patterns = {
            'mastitis': r'(?:Mastite|Mastitis)\s*([+\-]?\d+\.?\d*)\s+(\d{2})%',
            'metritis': r'(?:Metrite|Metritis)\s*([+\-]?\d+\.?\d*)\s+(\d{2})%',
            'ketosis': r'(?:Cetose|Ketosis)\s*([+\-]?\d+\.?\d*)\s+(\d{2})%',
            'milk_fever': r'Milk Fever\s*([+\-]?\d+\.?\d*)\s+(\d{2})%',
            'displaced_abomasum': r'(?:Desp.*?Abomaso|Displaced Abomasum|DA)\s*([+\-]?\d+\.?\d*)\s+(\d{2})%',
            'retained_placenta': r'(?:Ret.*?Placenta|Retained Placenta)\s*([+\-]?\d+\.?\d*)\s+(\d{2})%',
        }
        
        for trait, pattern in wellness_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                bull[trait] = float(match.group(1))
                bull[f'{trait}_rel'] = int(match.group(2))
        
        # === GFI ===
        gfi_match = re.search(r'GFI\s*(\d+\.?\d*)%', text)
        if gfi_match:
            bull['gfi'] = float(gfi_match.group(1))
        
        # === HHP$ ===
        hhp_match = re.search(r'HHP\$[®]?\s*\+?\$?([\d,]+)', text)
        if hhp_match:
            bull['hhp'] = int(hhp_match.group(1).replace(',', ''))
        
        # === HAPLÓTIPOS E GENÓTIPOS ===
        haplotypes = self._extract_haplotypes(text)
        if haplotypes:
            bull['haplotypes'] = haplotypes
        
        genotypes = self._extract_genotypes(text)
        bull.update(genotypes)
        
        # === NÚMERO DE FILHAS ===
        daughters_matches = re.findall(r'([\d,]+)\s*(?:Filhas|Daughters|D\b)', text)
        if daughters_matches:
            max_d = max([int(d.replace(',', '')) for d in daughters_matches])
            bull['num_daughters'] = max_d
        
        return bull
    
    def parse_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Processa um arquivo PDF"""
        try:
            import PyPDF2
        except ImportError:
            raise ImportError("Instale PyPDF2: pip install PyPDF2")
        
        bulls = []
        
        with open(pdf_path, 'rb') as file:
            pdf = PyPDF2.PdfReader(file)
            total = len(pdf.pages)
            
            print(f"  Processando {total} página(s)...")
            
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                bull = self.parse_text(text)
                
                if bull and bull.get('code'):
                    bull['page'] = i + 1
                    bull['source'] = 'PDF Import'
                    bull['is_available'] = True
                    bulls.append(bull)
                    
                    # Mostrar progresso
                    milk = bull.get('milk', 'N/A')
                    milk_rel = bull.get('milk_rel', '?')
                    nm = bull.get('net_merit', 'N/A')
                    print(f"    ✅ Página {i+1}: {bull['code']} - {bull.get('name', '?')}")
        
        return bulls


class BullDatabaseManager:
    """Gerenciador de banco de dados para touros"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_columns()
    
    def _ensure_columns(self):
        """Garante que todas as colunas necessárias existem"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        new_columns = [
            ('milk_rel', 'FLOAT'), ('protein_rel', 'FLOAT'), ('fat_rel', 'FLOAT'),
            ('productive_life_rel', 'FLOAT'), ('scs_rel', 'FLOAT'),
            ('livability', 'FLOAT'), ('livability_rel', 'FLOAT'),
            ('heifer_livability', 'FLOAT'), ('heifer_livability_rel', 'FLOAT'),
            ('dpr_rel', 'FLOAT'), ('hcr_rel', 'FLOAT'), ('ccr_rel', 'FLOAT'),
            ('fertility_index_rel', 'FLOAT'), ('feed_saved_rel', 'FLOAT'),
            ('rfi_rel', 'FLOAT'), ('milking_speed', 'FLOAT'), ('milking_speed_rel', 'FLOAT'),
            ('sire_calving_ease_rel', 'FLOAT'), ('daughter_calving_ease_rel', 'FLOAT'),
            ('sire_stillbirth', 'FLOAT'), ('sire_stillbirth_rel', 'FLOAT'),
            ('daughter_stillbirth', 'FLOAT'), ('daughter_stillbirth_rel', 'FLOAT'),
            ('ptat_rel', 'FLOAT'), ('udc_rel', 'FLOAT'), ('flc_rel', 'FLOAT'),
            ('mastitis', 'FLOAT'), ('mastitis_rel', 'FLOAT'),
            ('metritis', 'FLOAT'), ('metritis_rel', 'FLOAT'),
            ('ketosis', 'FLOAT'), ('ketosis_rel', 'FLOAT'),
            ('milk_fever', 'FLOAT'), ('milk_fever_rel', 'FLOAT'),
            ('displaced_abomasum', 'FLOAT'), ('displaced_abomasum_rel', 'FLOAT'),
            ('retained_placenta', 'FLOAT'), ('retained_placenta_rel', 'FLOAT'),
            ('gestation_length', 'FLOAT'), ('gestation_length_rel', 'FLOAT'),
            ('hhp', 'FLOAT'), ('reliabilities', 'JSON'), ('num_daughters', 'INTEGER'),
        ]
        
        cursor.execute("PRAGMA table_info(bulls)")
        existing = {row[1] for row in cursor.fetchall()}
        
        for col_name, col_type in new_columns:
            if col_name not in existing:
                try:
                    cursor.execute(f"ALTER TABLE bulls ADD COLUMN {col_name} {col_type}")
                except:
                    pass
        
        conn.commit()
        conn.close()
    
    def upsert_bull(self, bull: Dict[str, Any]) -> bool:
        """Insere ou atualiza um touro"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        code = bull.get('code')
        if not code:
            conn.close()
            return False
        
        cursor.execute("SELECT id FROM bulls WHERE code = ?", (code,))
        existing = cursor.fetchone()
        
        bull_copy = bull.copy()
        
        if 'haplotypes' in bull_copy and isinstance(bull_copy['haplotypes'], dict):
            bull_copy['haplotypes'] = json.dumps(bull_copy['haplotypes'])
        
        reliabilities = {k: v for k, v in bull_copy.items() if k.endswith('_rel')}
        if reliabilities:
            bull_copy['reliabilities'] = json.dumps(reliabilities)
        
        cursor.execute("PRAGMA table_info(bulls)")
        valid_columns = {row[1] for row in cursor.fetchall()}
        bull_copy = {k: v for k, v in bull_copy.items() if k in valid_columns}
        
        bull_copy['last_updated'] = datetime.now().isoformat()
        
        if existing:
            cols = [k for k in bull_copy.keys() if k != 'id']
            set_clause = ', '.join([f"{k} = ?" for k in cols])
            values = [bull_copy[k] for k in cols] + [code]
            cursor.execute(f"UPDATE bulls SET {set_clause} WHERE code = ?", values)
            result = False
        else:
            cols = list(bull_copy.keys())
            placeholders = ', '.join(['?' for _ in cols])
            col_names = ', '.join(cols)
            values = [bull_copy[k] for k in cols]
            cursor.execute(f"INSERT INTO bulls ({col_names}) VALUES ({placeholders})", values)
            result = True
        
        conn.commit()
        conn.close()
        return result
    
    def upsert_bulls(self, bulls: List[Dict[str, Any]]) -> Dict[str, int]:
        """Insere ou atualiza múltiplos touros"""
        inserted = 0
        updated = 0
        
        for bull in bulls:
            if self.upsert_bull(bull):
                inserted += 1
            else:
                updated += 1
        
        return {'inserted': inserted, 'updated': updated}
    
    def get_bull_count(self) -> int:
        """Retorna o número total de touros"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM bulls")
        count = cursor.fetchone()[0]
        conn.close()
        return count


def process_pdf(pdf_path: str, db_path: str = None) -> Dict[str, Any]:
    """Processa um PDF e insere/atualiza touros no banco"""
    print("\n" + "="*60)
    print("GENEFY - Parser UNIVERSAL de Touros")
    print("="*60)
    
    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {pdf_path}")
    
    print(f"\n📄 Arquivo: {pdf_path}")
    
    parser = UniversalBullParser()
    bulls = parser.parse_pdf(pdf_path)
    
    print(f"\n📊 Touros encontrados: {len(bulls)}")
    
    if not bulls:
        print("\n⚠️  Nenhum touro encontrado no PDF!")
        return {'total': 0, 'inserted': 0, 'updated': 0}
    
    # Mostrar resumo
    for bull in bulls[:5]:
        milk = bull.get('milk', 'N/A')
        milk_rel = bull.get('milk_rel', '?')
        nm = bull.get('net_merit', 'N/A')
        print(f"    • {bull['code']} - {bull.get('name', '?')}: Milk +{milk} ({milk_rel}%), NM$ {nm}")
    
    if len(bulls) > 5:
        print(f"    ... e mais {len(bulls) - 5} touros")
    
    if db_path:
        print(f"\n💾 Salvando no banco: {db_path}")
        
        db = BullDatabaseManager(db_path)
        result = db.upsert_bulls(bulls)
        
        print(f"\n✅ Processamento concluído!")
        print(f"    • Novos touros inseridos: {result['inserted']}")
        print(f"    • Touros atualizados: {result['updated']}")
        print(f"    • Total no banco: {db.get_bull_count()}")
        
        return {
            'total': len(bulls),
            'inserted': result['inserted'],
            'updated': result['updated']
        }
    else:
        output_path = Path(pdf_path).stem + '_bulls.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(bulls, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Dados salvos em: {output_path}")
        
        return {'total': len(bulls), 'output_file': output_path}


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python3 universal_bull_parser.py <pdf_path> [database_path]")
        print("\nExemplos:")
        print("  python3 universal_bull_parser.py touro.pdf")
        print("  python3 universal_bull_parser.py catalogo.pdf database/cattle_breeding.db")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    db_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        result = process_pdf(pdf_path, db_path)
        print("\n" + "="*60)
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)