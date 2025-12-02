"""
Serviço de Importação de Dados
Importa Excel (fêmeas) e PDF (touros) de forma inteligente

PARSER UNIVERSAL DE PDF:
- Captura qualquer formato de PDF de touro (SelectSires, ABS, CRI, etc)
- Múltiplas estratégias de extração
- Validação de valores
- Funciona com PDFs individuais ou catálogos
"""

import sys
import io
import re
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd
import PyPDF2
from sqlalchemy.orm import Session

from backend.models.database import Female, Bull, ImportHistory


class UniversalBullParser:
    """Parser UNIVERSAL de PDF de touros - captura qualquer formato"""
    
    def __init__(self):
        self.valid_ranges = {
            'milk': (-2000, 4000), 'protein': (-100, 200), 'fat': (-100, 200),
            'net_merit': (-500, 2000), 'cheese_merit': (-500, 2000),
            'grazing_merit': (-500, 2000), 'gtpi': (1500, 4000), 'tpi': (1500, 4000),
            'productive_life': (-5, 15), 'scs': (1.5, 4.0), 'dpr': (-5, 10),
            'hcr': (-10, 15), 'ccr': (-10, 15), 'fertility_index': (-5, 15),
            'udc': (-3, 4), 'flc': (-3, 4), 'ptat': (-3, 5), 'gfi': (0, 20),
            'feed_saved': (-200, 500), 'rfi': (-100, 100),
        }
    
    def parse_pdf(self, pdf_path: str) -> List[Dict]:
        """Processa um arquivo PDF e extrai todos os touros"""
        bulls = []
        
        with open(pdf_path, 'rb') as file:
            pdf = PyPDF2.PdfReader(file)
            
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                bull = self._parse_page(text)
                
                if bull and bull.get('code'):
                    bull['page'] = i + 1
                    bull['source'] = 'PDF Import'
                    bull['is_available'] = True
                    bulls.append(bull)
        
        return bulls
    
    def _parse_page(self, text: str) -> Optional[Dict]:
        """Extrai dados de uma página usando múltiplas estratégias"""
        bull = {}
        
        # === CÓDIGO DO TOURO ===
        code = self._extract_code(text)
        if not code:
            return None
        bull['code'] = code
        
        # === NOME ===
        name = self._extract_name(text, code)
        if name:
            bull['name'] = name
        
        # === REG ID ===
        reg_match = re.search(r'(HO\d{10,13})', text)
        if reg_match:
            bull['reg_id'] = reg_match.group(1)
        
        # === VALORES EM DÓLAR (Net Merit, etc) ===
        dollar_values = self._extract_dollar_values(text)
        if dollar_values:
            bull.update(dollar_values)
        
        # === MILK ===
        milk_data = self._extract_milk(text)
        if milk_data:
            bull.update(milk_data)
        
        # === PROTEIN E FAT ===
        prot_fat = self._extract_protein_fat(text)
        if prot_fat:
            bull.update(prot_fat)
        
        # === GTPI/TPI ===
        gtpi = self._extract_gtpi(text)
        if gtpi:
            bull['gtpi'] = gtpi
            bull['tpi'] = gtpi
        
        # === TIPO (PTAT, UDC, FLC) ===
        type_data = self._extract_type(text)
        if type_data:
            bull.update(type_data)
        
        # === SAÚDE ===
        health_data = self._extract_health(text)
        if health_data:
            bull.update(health_data)
        
        # === FERTILIDADE ===
        fertility_data = self._extract_fertility(text)
        if fertility_data:
            bull.update(fertility_data)
        
        # === EFICIÊNCIA ===
        efficiency_data = self._extract_efficiency(text)
        if efficiency_data:
            bull.update(efficiency_data)
        
        # === PARTO ===
        calving_data = self._extract_calving(text)
        if calving_data:
            bull.update(calving_data)
        
        # === WELLNESS ===
        wellness_data = self._extract_wellness(text)
        if wellness_data:
            bull.update(wellness_data)
        
        # === GFI ===
        gfi_match = re.search(r'GFI[:\s]*(\d+\.?\d*)%?', text, re.IGNORECASE)
        if gfi_match:
            bull['gfi'] = float(gfi_match.group(1))
        
        # === HHP$ ===
        hhp_match = re.search(r'HHP\$?[®]?\s*\+?\$?([\d,]+)', text)
        if hhp_match:
            bull['hhp'] = int(hhp_match.group(1).replace(',', ''))
        
        # === HAPLÓTIPOS ===
        haplotypes = self._extract_haplotypes(text)
        if haplotypes:
            bull['haplotypes'] = haplotypes
        
        # === GENÓTIPOS ===
        genotypes = self._extract_genotypes(text)
        if genotypes:
            bull.update(genotypes)
        
        # === NÚMERO DE FILHAS ===
        daughters = self._extract_daughters(text)
        if daughters:
            bull['num_daughters'] = daughters
        
        return bull
    
    def _extract_code(self, text: str) -> Optional[str]:
        """Extrai código do touro"""
        patterns = [
            r'(\d{1,3}HO\d{4,6})',  # 551HO3797, 7HO17200
            r'(\d{3}HO\d{5})',       # 551HO03797
            r'([A-Z]{2,3}\d{5,8})',  # HOUSA000123456
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def _extract_name(self, text: str, code: str) -> Optional[str]:
        """Extrai nome do touro"""
        patterns = [
            rf'{code}\s+([A-Z][A-Z\-]+)',
            rf'{code}\s+([A-Z][A-Za-z\-]+)',
            r'([A-Z][A-Z\-]+)-ET',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                name = re.sub(r'-?(ET|PP|P|RED|RC)$', '', name).strip()
                if len(name) >= 2:
                    return name
        return None
    
    def _extract_dollar_values(self, text: str) -> Dict:
        """Extrai valores em dólar"""
        result = {}
        
        # Padrão: +$XXX ou $XXX
        matches = re.findall(r'\+?\$([\d,]+)', text)
        values = [int(m.replace(',', '')) for m in matches]
        
        # Filtrar valores válidos para Net Merit (200-1500)
        valid_nm = [v for v in values if 200 <= v <= 1500]
        
        if valid_nm:
            # Geralmente o primeiro é Net Merit
            result['net_merit'] = valid_nm[0]
            if len(valid_nm) >= 2:
                result['cheese_merit'] = valid_nm[1]
            if len(valid_nm) >= 3:
                result['grazing_merit'] = valid_nm[2]
            if len(valid_nm) >= 4:
                result['fluid_merit'] = valid_nm[3]
        
        # Tentar padrões específicos
        nm_patterns = [
            r'(?:NM\$|Net Merit|ML\$)[:\s]*\+?\$?([\d,]+)',
            r'GM\$\+?([\d,]+)',
        ]
        for pattern in nm_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['net_merit'] = int(match.group(1).replace(',', ''))
                break
        
        return result
    
    def _extract_milk(self, text: str) -> Dict:
        """Extrai dados de leite"""
        result = {}
        
        patterns = [
            r'(?:Leite|Milk|PTAM)[:\s]*\+?([\d,]+)',
            r'GM\$\+?([\d,]+)',  # SelectSires format
            r'Milk\s+\+?([\d,]+)\s+lbs',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = int(match.group(1).replace(',', ''))
                if self._validate_value('milk', value):
                    result['milk'] = value
                    break
        
        # Reliability do milk
        rel_patterns = [
            r'(\d{2,3})%\s*[CR]?/',
            r'Milk.*?(\d{2,3})%\s*R',
            r'(\d{2,3})%\s*Conf',
        ]
        for pattern in rel_patterns:
            match = re.search(pattern, text)
            if match:
                result['milk_rel'] = int(match.group(1))
                break
        
        return result
    
    def _extract_protein_fat(self, text: str) -> Dict:
        """Extrai proteína e gordura"""
        result = {}
        
        prot_match = re.search(r'(?:Proteina|Protein)[:\s]*\+?(\d{1,3})', text, re.IGNORECASE)
        if prot_match:
            result['protein'] = int(prot_match.group(1))
        
        fat_match = re.search(r'(?:Gordura|Fat)[:\s]*\+?(\d{1,3})', text, re.IGNORECASE)
        if fat_match:
            result['fat'] = int(fat_match.group(1))
        
        # Percentuais
        prot_pct = re.search(r'%\s*Prot(?:ein)?[:\s]*([+\-]?\d+\.\d+)', text, re.IGNORECASE)
        if prot_pct:
            result['protein_percent'] = float(prot_pct.group(1))
        
        fat_pct = re.search(r'%\s*(?:Gordura|Fat)[:\s]*([+\-]?\d+\.\d+)', text, re.IGNORECASE)
        if fat_pct:
            result['fat_percent'] = float(fat_pct.group(1))
        
        return result
    
    def _extract_gtpi(self, text: str) -> Optional[int]:
        """Extrai GTPI/TPI"""
        patterns = [
            r'(?:GTPI|TPI)[:\s]*\+?(\d{4})',
            r'Tipo\+(\d{4})',
            r'G?TPI[:\s]*(\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = int(match.group(1))
                if self._validate_value('gtpi', value):
                    return value
        return None
    
    def _extract_type(self, text: str) -> Dict:
        """Extrai dados de tipo"""
        result = {}
        
        # PTAT
        ptat_patterns = [
            r'(?:PTAT|Tipo)[:\s]*([+\-]?\d+\.?\d*)\s*(\d{2,3})?%?',
            r'PTAT\s*([+\-]?\d+\.?\d*)',
        ]
        for pattern in ptat_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['ptat'] = float(match.group(1))
                if match.lastindex >= 2 and match.group(2):
                    result['ptat_rel'] = int(match.group(2))
                break
        
        # UDC
        udc_match = re.search(r'UDC[:\s]*([+\-]?\d+\.?\d*)\s*(\d{2,3})?%?', text)
        if udc_match:
            result['udc'] = float(udc_match.group(1))
            if udc_match.lastindex >= 2 and udc_match.group(2):
                result['udc_rel'] = int(udc_match.group(2))
        
        # FLC
        flc_match = re.search(r'FLC[:\s]*([+\-]?\d+\.?\d*)\s*(\d{2,3})?%?', text)
        if flc_match:
            result['flc'] = float(flc_match.group(1))
            if flc_match.lastindex >= 2 and flc_match.group(2):
                result['flc_rel'] = int(flc_match.group(2))
        
        return result
    
    def _extract_health(self, text: str) -> Dict:
        """Extrai dados de saúde"""
        result = {}
        
        # Productive Life
        pl_patterns = [
            r'(?:Vida Produtiva|Productive Life|PL)[:\s]*([+\-]?\d+\.?\d*)\s*(\d{2,3})?%?',
            r'PL\s*([+\-]?\d+\.?\d*)',
        ]
        for pattern in pl_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['productive_life'] = float(match.group(1))
                if match.lastindex >= 2 and match.group(2):
                    result['productive_life_rel'] = int(match.group(2))
                break
        
        # SCS
        scs_patterns = [
            r'(?:Células Somáticas|Somatic Cell|SCS)[:\s]*(\d+\.?\d*)\s*(\d{2,3})?%?',
            r'SCS\s*(\d+\.?\d*)',
        ]
        for pattern in scs_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['scs'] = float(match.group(1))
                if match.lastindex >= 2 and match.group(2):
                    result['scs_rel'] = int(match.group(2))
                break
        
        # Livability
        liv_match = re.search(r'(?:Permanência|Livability)[:\s]*([+\-]?\d+\.?\d*)\s*(\d{2,3})?%?', text, re.IGNORECASE)
        if liv_match:
            result['livability'] = float(liv_match.group(1))
            if liv_match.lastindex >= 2 and liv_match.group(2):
                result['livability_rel'] = int(liv_match.group(2))
        
        return result
    
    def _extract_fertility(self, text: str) -> Dict:
        """Extrai dados de fertilidade"""
        result = {}
        
        # DPR
        dpr_patterns = [
            r'(?:Indice Preñez|DPR|Daughter Pregnancy)[:\s]*([+\-]?\d+\.?\d*)\s*(\d{2,3})?%?',
            r'DPR\s*([+\-]?\d+\.?\d*)',
        ]
        for pattern in dpr_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['dpr'] = float(match.group(1))
                if match.lastindex >= 2 and match.group(2):
                    result['dpr_rel'] = int(match.group(2))
                break
        
        # HCR
        hcr_match = re.search(r'(?:Heifer Conception|HCR)[:\s]*([+\-]?\d+\.?\d*)\s*(\d{2,3})?%?', text, re.IGNORECASE)
        if hcr_match:
            result['hcr'] = float(hcr_match.group(1))
            if hcr_match.lastindex >= 2 and hcr_match.group(2):
                result['hcr_rel'] = int(hcr_match.group(2))
        
        # CCR
        ccr_match = re.search(r'(?:Cow Conception|CCR)[:\s]*([+\-]?\d+\.?\d*)\s*(\d{2,3})?%?', text, re.IGNORECASE)
        if ccr_match:
            result['ccr'] = float(ccr_match.group(1))
            if ccr_match.lastindex >= 2 and ccr_match.group(2):
                result['ccr_rel'] = int(ccr_match.group(2))
        
        # Fertility Index
        fi_match = re.search(r'(?:Índice.*?Fertilidade|Fertility Index|FI)[:\s]*([+\-]?\d+\.?\d*)\s*(\d{2,3})?%?', text, re.IGNORECASE)
        if fi_match:
            result['fertility_index'] = float(fi_match.group(1))
            if fi_match.lastindex >= 2 and fi_match.group(2):
                result['fertility_index_rel'] = int(fi_match.group(2))
        
        return result
    
    def _extract_efficiency(self, text: str) -> Dict:
        """Extrai dados de eficiência"""
        result = {}
        
        # Feed Saved
        fs_match = re.search(r'Feed Saved[:\s]*([+\-]?\d+)\s*(\d{2,3})?%?', text, re.IGNORECASE)
        if fs_match:
            result['feed_saved'] = int(fs_match.group(1))
            if fs_match.lastindex >= 2 and fs_match.group(2):
                result['feed_saved_rel'] = int(fs_match.group(2))
        
        # RFI
        rfi_match = re.search(r'RFI[:\s]*([+\-]?\d+)\s*(\d{2,3})?%?', text)
        if rfi_match:
            result['rfi'] = int(rfi_match.group(1))
            if rfi_match.lastindex >= 2 and rfi_match.group(2):
                result['rfi_rel'] = int(rfi_match.group(2))
        
        # Milking Speed
        ms_match = re.search(r'(?:Veloc|Milking Speed)[^\d]*(\d+\.?\d*)[/\s]*(\d{2,3})?%?', text, re.IGNORECASE)
        if ms_match:
            result['milking_speed'] = float(ms_match.group(1))
            if ms_match.lastindex >= 2 and ms_match.group(2):
                result['milking_speed_rel'] = int(ms_match.group(2))
        
        return result
    
    def _extract_calving(self, text: str) -> Dict:
        """Extrai dados de parto"""
        result = {}
        
        # SCE
        sce_match = re.search(r'(?:Facilidade.*?Touro|Sire Calving|SCE)[:\s]*(\d+\.?\d*)\s*(\d{2,3})?%?', text, re.IGNORECASE)
        if sce_match:
            result['sire_calving_ease'] = float(sce_match.group(1))
            if sce_match.lastindex >= 2 and sce_match.group(2):
                result['sire_calving_ease_rel'] = int(sce_match.group(2))
        
        # DCE
        dce_match = re.search(r'(?:Parto.*?Filhas|Daughter Calving|DCE)[:\s]*(\d+\.?\d*)\s*(\d{2,3})?%?', text, re.IGNORECASE)
        if dce_match:
            result['daughter_calving_ease'] = float(dce_match.group(1))
            if dce_match.lastindex >= 2 and dce_match.group(2):
                result['daughter_calving_ease_rel'] = int(dce_match.group(2))
        
        # SSB
        ssb_match = re.search(r'(?:Mortes.*?Touros|Sire Stillbirth|SSB)[:\s]*(\d+\.?\d*)\s*(\d{2,3})?%?', text, re.IGNORECASE)
        if ssb_match:
            result['sire_stillbirth'] = float(ssb_match.group(1))
            if ssb_match.lastindex >= 2 and ssb_match.group(2):
                result['sire_stillbirth_rel'] = int(ssb_match.group(2))
        
        # DSB
        dsb_match = re.search(r'(?:Mortes.*?Filhas|Daughter Stillbirth|DSB)[:\s]*(\d+\.?\d*)\s*(\d{2,3})?%?', text, re.IGNORECASE)
        if dsb_match:
            result['daughter_stillbirth'] = float(dsb_match.group(1))
            if dsb_match.lastindex >= 2 and dsb_match.group(2):
                result['daughter_stillbirth_rel'] = int(dsb_match.group(2))
        
        # Gestation Length
        gl_match = re.search(r'(?:Gestação|Gestation)[:\s]*([+\-]?\d+\.?\d*)\s*(\d{2,3})?%?', text, re.IGNORECASE)
        if gl_match:
            result['gestation_length'] = float(gl_match.group(1))
            if gl_match.lastindex >= 2 and gl_match.group(2):
                result['gestation_length_rel'] = int(gl_match.group(2))
        
        return result
    
    def _extract_wellness(self, text: str) -> Dict:
        """Extrai dados de wellness"""
        result = {}
        
        wellness_patterns = {
            'mastitis': r'(?:Mastite|Mastitis)[:\s]*([+\-]?\d+\.?\d*)\s*(\d{2,3})?%?',
            'metritis': r'(?:Metrite|Metritis)[:\s]*([+\-]?\d+\.?\d*)\s*(\d{2,3})?%?',
            'ketosis': r'(?:Cetose|Ketosis)[:\s]*([+\-]?\d+\.?\d*)\s*(\d{2,3})?%?',
            'milk_fever': r'Milk Fever[:\s]*([+\-]?\d+\.?\d*)\s*(\d{2,3})?%?',
            'displaced_abomasum': r'(?:Desp.*?Abomaso|Displaced Abomasum|DA)[:\s]*([+\-]?\d+\.?\d*)\s*(\d{2,3})?%?',
            'retained_placenta': r'(?:Ret.*?Placenta|Retained Placenta)[:\s]*([+\-]?\d+\.?\d*)\s*(\d{2,3})?%?',
        }
        
        for trait, pattern in wellness_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result[trait] = float(match.group(1))
                if match.lastindex >= 2 and match.group(2):
                    result[f'{trait}_rel'] = int(match.group(2))
        
        return result
    
    def _extract_haplotypes(self, text: str) -> Dict:
        """Extrai status de haplótipos"""
        haplotypes = {}
        
        for i in range(1, 7):
            hap = f'HH{i}'
            
            # Padrões: HH1T, HH1F, HH1C, HH1 Free, HH1 Carrier
            if re.search(rf'{hap}[TF]', text) or re.search(rf'{hap}\s*(?:Free|Tested)', text, re.IGNORECASE):
                haplotypes[hap.lower()] = 'Free'
            elif re.search(rf'{hap}C', text) or re.search(rf'{hap}\s*Carrier', text, re.IGNORECASE):
                haplotypes[hap.lower()] = 'Carrier'
        
        return haplotypes
    
    def _extract_genotypes(self, text: str) -> Dict:
        """Extrai genótipos"""
        result = {}
        
        # Beta-Casein
        beta_match = re.search(r'Beta.?Casein[:\s]*(A1A1|A1A2|A2A2)', text, re.IGNORECASE)
        if beta_match:
            result['beta_casein'] = beta_match.group(1).upper()
        
        # Kappa-Casein
        kappa_match = re.search(r'Kappa.?Casein[:\s]*(AA|AB|BB)', text, re.IGNORECASE)
        if kappa_match:
            result['kappa_casein'] = kappa_match.group(1).upper()
        
        return result
    
    def _extract_daughters(self, text: str) -> Optional[int]:
        """Extrai número de filhas"""
        patterns = [
            r'([\d,]+)\s*(?:Filhas|Daughters|D\b)',
            r'Daughters?[:\s]*([\d,]+)',
            r'(\d{1,4})\s*D\b',
        ]
        
        max_daughters = 0
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches:
                try:
                    d = int(m.replace(',', ''))
                    if d > max_daughters:
                        max_daughters = d
                except:
                    pass
        
        return max_daughters if max_daughters > 0 else None
    
    def _validate_value(self, field: str, value) -> bool:
        """Valida se o valor está no range esperado"""
        if field not in self.valid_ranges:
            return True
        min_val, max_val = self.valid_ranges[field]
        try:
            return min_val <= float(value) <= max_val
        except:
            return False


class DataImporter:
    """Importador inteligente de dados"""
    
    def __init__(self, db_session: Session):
        self.session = db_session
        self.bull_parser = UniversalBullParser()
    
    # ========================================================================
    # IMPORTAÇÃO DE FÊMEAS (EXCEL) - SEM MODIFICAÇÕES
    # ========================================================================
    
    def import_females_from_excel(self, excel_path: str, user: str = 'Sistema') -> Dict:
        """Importa fêmeas do Excel - mantém implementação original"""
        print(f"Importando fêmeas de: {excel_path}")
        
        stats = {'added': 0, 'updated': 0, 'unchanged': 0, 'errors': []}
        
        try:
            df = pd.read_excel(excel_path, engine='openpyxl')
            print(f"  Lidas {len(df)} fêmeas do Excel")
            
            for idx, row in df.iterrows():
                try:
                    reg_id = str(row.get('REG ID', ''))
                    internal_id = str(row.get('ID', ''))
                    
                    if not reg_id and not internal_id:
                        continue
                    
                    existing = None
                    if reg_id:
                        existing = self.session.query(Female).filter_by(reg_id=reg_id).first()
                    if not existing and internal_id:
                        existing = self.session.query(Female).filter_by(internal_id=internal_id).first()
                    
                    genetic_data = {}
                    for col in df.columns:
                        val = row[col]
                        if pd.notna(val):
                            if isinstance(val, (int, float)):
                                genetic_data[col] = float(val)
                            else:
                                genetic_data[col] = str(val)
                    
                    data_hash = self._hash_dict(genetic_data)
                    main_indices = self._extract_female_main_indices(row)
                    
                    if existing:
                        existing_hash = self._hash_dict(existing.genetic_data or {})
                        
                        if data_hash != existing_hash:
                            existing.genetic_data = genetic_data
                            existing.name = str(row.get('ID', ''))
                            for key, value in main_indices.items():
                                setattr(existing, key, value)
                            existing.last_updated = datetime.now()
                            stats['updated'] += 1
                        else:
                            stats['unchanged'] += 1
                    else:
                        new_female = Female(
                            reg_id=reg_id if reg_id else None,
                            internal_id=internal_id if internal_id else None,
                            name=str(row.get('ID', '')),
                            breed=str(row.get('BREED', 'HO')),
                            genetic_data=genetic_data,
                            **main_indices
                        )
                        self.session.add(new_female)
                        stats['added'] += 1
                
                except Exception as e:
                    stats['errors'].append(f"Linha {idx}: {str(e)}")
            
            self.session.commit()
            self._log_import('females_excel', excel_path, stats, user)
            
            print(f"\n[OK] Importacao concluida: +{stats['added']}, ~{stats['updated']}, ={stats['unchanged']}")
            return stats
            
        except Exception as e:
            self.session.rollback()
            print(f"[ERRO] {e}")
            raise
    
    def _extract_female_main_indices(self, row: pd.Series) -> Dict:
        return {
            'milk': self._safe_float(row.get('MILK')),
            'protein': self._safe_float(row.get('PROTEIN')),
            'fat': self._safe_float(row.get('FAT')),
            'productive_life': self._safe_float(row.get('PRODUCTIVE LIFE')),
            'scs': self._safe_float(row.get('SOMATIC CELL SCORE')),
            'dpr': self._safe_float(row.get('DAUGHTER PREGNANCY RATE')),
            'fertility_index': self._safe_float(row.get('FERTILITY INDEX')),
            'udc': self._safe_float(row.get('UDC')),
            'flc': self._safe_float(row.get('FLC')),
            'ptat': self._safe_float(row.get('PTAT')),
            'net_merit': self._safe_float(row.get('NET MERIT')),
            'tpi': self._safe_float(row.get('TPI')),
            'genomic_inbreeding': self._safe_float(row.get('gINB')),
        }
    
    # ========================================================================
    # IMPORTAÇÃO DE TOUROS (PDF) - PARSER UNIVERSAL
    # ========================================================================
    
    def import_bulls_from_pdf(self, pdf_path: str, user: str = 'Sistema') -> Dict:
        """Importa touros do PDF usando parser UNIVERSAL"""
        print(f"\n{'='*60}")
        print(f"IMPORTANDO TOUROS DE: {pdf_path}")
        print('='*60)
        
        stats = {'added': 0, 'updated': 0, 'unchanged': 0, 'errors': []}
        
        try:
            # Usar parser universal
            bulls_data = self.bull_parser.parse_pdf(pdf_path)
            print(f"  Extraídos {len(bulls_data)} touros do PDF")
            
            for idx, bull_data in enumerate(bulls_data):
                try:
                    code = bull_data.get('code')
                    if not code:
                        continue
                    
                    print(f"    {idx+1}. {code} - {bull_data.get('name', '?')}")
                    
                    existing = self.session.query(Bull).filter_by(code=code).first()
                    
                    # Preparar dados para inserção
                    main_indices = self._extract_bull_main_indices(bull_data)
                    
                    # Reliabilities JSON
                    reliabilities = {k: v for k, v in bull_data.items() if k.endswith('_rel')}
                    
                    if existing:
                        # ATUALIZAR
                        for key, value in main_indices.items():
                            if value is not None:
                                setattr(existing, key, value)
                        
                        if reliabilities:
                            existing.reliabilities = json.dumps(reliabilities)
                        
                        if bull_data.get('haplotypes'):
                            existing.haplotypes = bull_data['haplotypes']
                        
                        if bull_data.get('num_daughters'):
                            existing.num_daughters = bull_data['num_daughters']
                        
                        existing.is_available = True
                        existing.last_updated = datetime.now()
                        stats['updated'] += 1
                    else:
                        # ADICIONAR NOVO
                        new_bull = Bull(
                            code=code,
                            name=bull_data.get('name', ''),
                            naab_code=code,
                            reg_id=bull_data.get('reg_id'),
                            source=bull_data.get('source', 'PDF Import'),
                            genetic_data=bull_data,
                            haplotypes=bull_data.get('haplotypes'),
                            reliabilities=json.dumps(reliabilities) if reliabilities else None,
                            num_daughters=bull_data.get('num_daughters'),
                            is_available=True,
                            **{k: v for k, v in main_indices.items() if v is not None}
                        )
                        self.session.add(new_bull)
                        stats['added'] += 1
                
                except Exception as e:
                    stats['errors'].append(f"Touro {idx}: {str(e)}")
            
            self.session.commit()
            self._log_import('bulls_pdf', pdf_path, stats, user)
            
            print(f"\n{'='*60}")
            print(f"[OK] IMPORTAÇÃO CONCLUÍDA!")
            print(f"  ✅ Adicionados: {stats['added']}")
            print(f"  🔄 Atualizados: {stats['updated']}")
            print(f"  ⏭️ Sem mudanças: {stats['unchanged']}")
            if stats['errors']:
                print(f"  ❌ Erros: {len(stats['errors'])}")
            print('='*60)
            
            return stats
            
        except Exception as e:
            self.session.rollback()
            print(f"[ERRO] {e}")
            raise
    
    def _extract_bull_main_indices(self, data: Dict) -> Dict:
        """Extrai índices principais do touro"""
        indices = [
            'milk', 'milk_rel', 'protein', 'fat', 'protein_percent', 'fat_percent',
            'net_merit', 'cheese_merit', 'grazing_merit', 'fluid_merit',
            'tpi', 'gtpi', 'udc', 'udc_rel', 'flc', 'flc_rel', 'ptat', 'ptat_rel',
            'productive_life', 'productive_life_rel', 'scs', 'scs_rel',
            'dpr', 'dpr_rel', 'hcr', 'hcr_rel', 'ccr', 'ccr_rel',
            'fertility_index', 'fertility_index_rel',
            'rfi', 'rfi_rel', 'feed_saved', 'feed_saved_rel',
            'sire_calving_ease', 'sire_calving_ease_rel',
            'daughter_calving_ease', 'daughter_calving_ease_rel',
            'sire_stillbirth', 'sire_stillbirth_rel',
            'daughter_stillbirth', 'daughter_stillbirth_rel',
            'gestation_length', 'gestation_length_rel',
            'mastitis', 'mastitis_rel', 'metritis', 'metritis_rel',
            'ketosis', 'ketosis_rel', 'milk_fever', 'milk_fever_rel',
            'displaced_abomasum', 'displaced_abomasum_rel',
            'retained_placenta', 'retained_placenta_rel',
            'livability', 'livability_rel',
            'beta_casein', 'kappa_casein', 'gfi', 'hhp', 'milking_speed', 'milking_speed_rel',
        ]
        
        return {k: data.get(k) for k in indices if data.get(k) is not None}
    
    # ========================================================================
    # UTILITÁRIOS
    # ========================================================================
    
    def _hash_dict(self, data: Dict) -> str:
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(json_str.encode()).hexdigest()
    
    def _safe_float(self, value) -> Optional[float]:
        try:
            if value is None or pd.isna(value):
                return None
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _log_import(self, import_type: str, filename: str, stats: Dict, user: str):
        log = ImportHistory(
            import_type=import_type,
            filename=filename,
            records_added=stats['added'],
            records_updated=stats['updated'],
            records_unchanged=stats['unchanged'],
            status='success' if not stats['errors'] else 'partial',
            error_log='\n'.join(stats['errors'][:100]) if stats['errors'] else None,
            imported_by=user
        )
        self.session.add(log)
        self.session.commit()