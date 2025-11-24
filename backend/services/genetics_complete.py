"""
Módulo de Genética COMPLETO
Cálculos precisos de PPPV, consanguinidade, compatibilidade e análise de haplótipos
"""

from typing import Dict, List, Optional, Tuple
import math

class GeneticCalculatorComplete:
    """Calculadora avançada de índices genéticos"""

    def __init__(self):
        # Índices principais por categoria
        self.production_indices = ['milk', 'protein', 'fat', 'fat_percent', 'protein_percent']
        self.fertility_indices = ['dpr', 'heifer_conception_rate', 'cow_conception_rate',
                                 'fertility_index', 'early_first_calving']
        self.health_indices = ['health_index', 'heifer_livability', 'livability', 'scs',
                              'mastitis', 'metritis', 'displaced_abomasum',
                              'milk_fever', 'retained_placenta', 'ketosis']
        self.type_indices = ['ptat', 'udc', 'flc', 'bde', 'dfm', 'sta', 'str']
        self.efficiency_indices = ['feed_efficiency', 'rfi', 'ecofeed_life',
                                  'ecofeed_heifer', 'ecofeed_cow']
        self.economic_indices = ['net_merit', 'tpi', 'cheese_merit', 'fluid_merit',
                                'grazing_merit', 'jpi', 'eco_dollars']

        # Haplótipos recessivos letais
        self.lethal_haplotypes = {
            'Holstein': ['HH1', 'HH2', 'HH3', 'HH4', 'HH5', 'HH6'],
            'Jersey': ['JH1', 'JH2'],
            'Ayrshire': ['AH1', 'AH2'],
            'Brown Swiss': ['BH1', 'BH2']
        }

    # ========================================================================
    # PPPV - PREDICTED PRODUCING VALUE (COMPLETO)
    # ========================================================================

    def calculate_pppv_complete(self, female_data: Dict, bull_data: Dict) -> Dict:
        """
        Calcula PPPV para TODOS os índices disponíveis

        Returns:
            Dict com PPPV por categoria
        """
        results = {
            'production': {},
            'fertility': {},
            'health': {},
            'type': {},
            'efficiency': {},
            'economic': {},
            'sustainability': {},
            'calving': {}
        }

        # Produção
        for index in self.production_indices:
            pppv = self._calculate_single_pppv(female_data, bull_data, index)
            if pppv:
                results['production'][index] = pppv

        # Fertilidade
        for index in self.fertility_indices:
            pppv = self._calculate_single_pppv(female_data, bull_data, index)
            if pppv:
                results['fertility'][index] = pppv

        # Saúde
        for index in self.health_indices:
            pppv = self._calculate_single_pppv(female_data, bull_data, index)
            if pppv:
                results['health'][index] = pppv

        # Tipo
        for index in self.type_indices:
            pppv = self._calculate_single_pppv(female_data, bull_data, index)
            if pppv:
                results['type'][index] = pppv

        # Eficiência
        for index in self.efficiency_indices:
            pppv = self._calculate_single_pppv(female_data, bull_data, index)
            if pppv:
                results['efficiency'][index] = pppv

        # Econômicos
        for index in self.economic_indices:
            pppv = self._calculate_single_pppv(female_data, bull_data, index)
            if pppv:
                results['economic'][index] = pppv

        # Sustentabilidade
        for index in ['vei', 'vea', 'eco2feed', 'bt']:
            pppv = self._calculate_single_pppv(female_data, bull_data, index)
            if pppv:
                results['sustainability'][index] = pppv

        # Facilidade de parto
        for index in ['daughter_calving_ease', 'sire_calving_ease',
                     'daughter_stillbirth', 'sire_stillbirth']:
            pppv = self._calculate_single_pppv(female_data, bull_data, index)
            if pppv:
                results['calving'][index] = pppv

        return results

    def _calculate_single_pppv(self, female_data: Dict, bull_data: Dict,
                               index: str) -> Optional[Dict]:
        """Calcula PPPV para um único índice"""
        female_val = self._get_value(female_data, index)
        bull_val = self._get_value(bull_data, index)

        if female_val is None or bull_val is None:
            return None

        # PPPV = média dos pais
        pppv = (female_val + bull_val) / 2

        return {
            'female': round(female_val, 2),
            'bull': round(bull_val, 2),
            'pppv': round(pppv, 2),
            'interpretation': self._interpret_value(index, pppv)
        }

    def _get_value(self, data: Dict, index: str) -> Optional[float]:
        """Extrai valor de um índice"""
        # Tentar direto
        if index in data and data[index] is not None:
            try:
                return float(data[index])
            except (ValueError, TypeError):
                pass

        # Tentar no genetic_data
        if 'genetic_data' in data and data['genetic_data']:
            genetic = data['genetic_data']
            if isinstance(genetic, dict):
                if index in genetic and genetic[index] is not None:
                    try:
                        return float(genetic[index])
                    except (ValueError, TypeError):
                        pass

        return None

    def _interpret_value(self, index: str, value: float) -> str:
        """Interpreta valor do índice"""
        # Interpretações baseadas em ranges típicos
        interpretations = {
            'milk': [(-1000, 'Muito Baixo'), (0, 'Baixo'), (500, 'Médio'),
                    (1000, 'Alto'), (1500, 'Muito Alto'), (float('inf'), 'Excepcional')],
            'net_merit': [(0, 'Baixo'), (300, 'Médio'), (600, 'Alto'),
                         (900, 'Muito Alto'), (float('inf'), 'Excepcional')],
            'tpi': [(2000, 'Baixo'), (2400, 'Médio'), (2800, 'Alto'),
                   (3200, 'Muito Alto'), (float('inf'), 'Excepcional')],
            'productive_life': [(-2, 'Muito Baixo'), (0, 'Baixo'), (2, 'Médio'),
                               (4, 'Alto'), (6, 'Muito Alto'), (float('inf'), 'Excepcional')],
            'scs': [(float('-inf'), 'Excepcional'), (2.5, 'Muito Bom'), (2.8, 'Bom'),
                   (3.0, 'Médio'), (3.2, 'Ruim'), (float('inf'), 'Muito Ruim')],
        }

        ranges = interpretations.get(index, [(float('-inf'), 'N/A')])

        for threshold, label in ranges:
            if value < threshold:
                return label

        return 'N/A'

    # ========================================================================
    # ANÁLISE DE CONSANGUINIDADE AVANÇADA
    # ========================================================================

    def analyze_inbreeding_complete(self, female_data: Dict, bull_data: Dict) -> Dict:
        """
        Análise completa de consanguinidade incluindo:
        - Consanguinidade genômica (gINB/gEFI)
        - Detecção de haplótipos recessivos
        - Cálculo de risco genético
        """
        # Consanguinidade básica
        female_ginb = self._get_value(female_data, 'genomic_inbreeding')
        bull_gfi = self._get_value(bull_data, 'gfi') or self._get_value(bull_data, 'genomic_future_inbreeding')

        if female_ginb is not None and bull_gfi is not None:
            # Estimativa de consanguinidade esperada
            expected_inbreeding = (female_ginb + bull_gfi) / 4 + 1.0
            method = 'genomic'
        else:
            # Sem dados genômicos
            expected_inbreeding = 3.0
            method = 'estimated'

        # Detectar haplótipos de risco
        haplotype_risks = self.detect_haplotype_risks(female_data, bull_data)

        # Classificar risco
        risk_level = self._classify_inbreeding_risk(expected_inbreeding, haplotype_risks)

        return {
            'expected_inbreeding': round(expected_inbreeding, 2),
            'method': method,
            'female_ginb': round(female_ginb, 2) if female_ginb else None,
            'bull_gfi': round(bull_gfi, 2) if bull_gfi else None,
            'risk_level': risk_level,
            'haplotype_risks': haplotype_risks,
            'acceptable': expected_inbreeding <= 6.0 and len(haplotype_risks) == 0,
            'recommendation': self._inbreeding_recommendation(expected_inbreeding, haplotype_risks)
        }

    def detect_haplotype_risks(self, female_data: Dict, bull_data: Dict) -> List[Dict]:
        """
        Detecta riscos de haplótipos recessivos letais
        Risco ocorre quando AMBOS os pais são portadores (Carrier)
        """
        risks = []

        # Obter raça
        breed = female_data.get('breed', 'HO')
        breed_map = {'HO': 'Holstein', 'JE': 'Jersey', 'AY': 'Ayrshire', 'BS': 'Brown Swiss'}
        breed_name = breed_map.get(breed, 'Holstein')

        # Verificar cada haplótipo relevante
        haplotypes = self.lethal_haplotypes.get(breed_name, [])

        for hap in haplotypes:
            hap_lower = hap.lower()

            # Obter status dos pais
            female_status = self._get_haplotype_status(female_data, hap_lower)
            bull_status = self._get_haplotype_status(bull_data, hap_lower)

            # Risco se ambos são carriers
            if female_status == 'Carrier' and bull_status == 'Carrier':
                risks.append({
                    'haplotype': hap,
                    'female_status': female_status,
                    'bull_status': bull_status,
                    'risk': 'ALTO - 25% chance de bezerro afetado (letal)',
                    'recommendation': f'EVITAR este acasalamento - risco de {hap} letal'
                })
            elif female_status == 'Carrier' or bull_status == 'Carrier':
                # Apenas um é carrier - sem risco letal mas filhos podem ser carriers
                risks.append({
                    'haplotype': hap,
                    'female_status': female_status,
                    'bull_status': bull_status,
                    'risk': 'BAIXO - Progênie pode ser portadora',
                    'recommendation': f'Aceitável - monitorar {hap} na progênie'
                })

        return risks

    def _get_haplotype_status(self, data: Dict, haplotype: str) -> str:
        """Obtém status do haplótipo (Free, Carrier, etc)"""
        value = self._get_value(data, haplotype)
        if value is None:
            # Tentar como string
            value = data.get(haplotype)
            if isinstance(value, str):
                return value

        # Interpretar valor numérico
        # Geralmente: 0 = Free, 1 = Carrier, 2 = Affected (muito raro)
        if value == 0:
            return 'Free'
        elif value == 1:
            return 'Carrier'
        elif value == 2:
            return 'Affected'
        else:
            return 'Unknown'

    def _classify_inbreeding_risk(self, inbreeding: float, haplotype_risks: List) -> str:
        """Classifica risco de consanguinidade"""
        if len(haplotype_risks) > 0:
            # Se há riscos de haplótipos, sempre é alto
            has_high_risk = any(r['risk'].startswith('ALTO') for r in haplotype_risks)
            if has_high_risk:
                return 'Crítico'

        if inbreeding < 6.0:
            return 'Baixo'
        elif inbreeding < 8.0:
            return 'Moderado'
        elif inbreeding < 10.0:
            return 'Alto'
        else:
            return 'Muito Alto'

    def _inbreeding_recommendation(self, inbreeding: float, haplotype_risks: List) -> str:
        """Recomendação baseada em consanguinidade e haplótipos"""
        if any(r['risk'].startswith('ALTO') for r in haplotype_risks):
            return 'EVITAR - Risco de haplótipos letais'

        if inbreeding < 6.0:
            return 'Recomendado - Consanguinidade ideal'
        elif inbreeding < 8.0:
            return 'Aceitável - Monitorar progênie'
        elif inbreeding < 10.0:
            return 'Cautela - Considerar outras opções'
        else:
            return 'NÃO RECOMENDADO - Alto risco genético'

    # ========================================================================
    # SCORE DE COMPATIBILIDADE EXPANDIDO
    # ========================================================================

    def calculate_compatibility_score_complete(self, female_data: Dict, bull_data: Dict,
                                               priorities: Optional[Dict] = None) -> Dict:
        """
        Score de compatibilidade expandido incluindo:
        - Produção, fertilidade, saúde, tipo
        - Eficiência alimentar
        - Sustentabilidade
        - Genótipos desejáveis
        - Penalidade por consanguinidade/haplótipos
        """
        if priorities is None:
            priorities = {
                'net_merit': 2.0,
                'milk': 1.5,
                'productive_life': 1.8,
                'fertility_index': 1.5,
                'health_index': 1.3,
                'feed_efficiency': 1.2,
                'scs': -1.0,  # Negativo = menor é melhor
            }

        # Score base (produção + funcionalidade)
        base_score = self._calculate_base_compatibility(bull_data, priorities)

        # Ajustes
        adjustments = {}
        final_score = base_score

        # 1. Análise de consanguinidade
        inbreeding_analysis = self.analyze_inbreeding_complete(female_data, bull_data)
        inbreeding = inbreeding_analysis['expected_inbreeding']
        haplotype_risks = inbreeding_analysis['haplotype_risks']

        if len(haplotype_risks) > 0:
            # Penalidade severa por risco de haplótipos
            has_high_risk = any(r['risk'].startswith('ALTO') for r in haplotype_risks)
            if has_high_risk:
                penalty = 50  # Penalidade de 50 pontos!
                adjustments['haplotype_risk'] = -penalty
                final_score -= penalty
            else:
                penalty = 10
                adjustments['haplotype_risk'] = -penalty
                final_score -= penalty

        if inbreeding > 6.0:
            penalty = (inbreeding - 6.0) * 5
            adjustments['inbreeding_penalty'] = -round(penalty, 1)
            final_score -= penalty

        # 2. Bônus por genótipos desejáveis
        genotype_bonus = self._calculate_genotype_bonus(bull_data)
        if genotype_bonus > 0:
            adjustments['genotype_bonus'] = genotype_bonus
            final_score += genotype_bonus

        # 3. Bônus por complementaridade
        complementarity = self._calculate_complementarity(female_data, bull_data)
        if complementarity > 0:
            adjustments['complementarity_bonus'] = complementarity
            final_score += complementarity

        # 4. Bônus por eficiência/sustentabilidade
        sustainability_bonus = self._calculate_sustainability_bonus(bull_data)
        if sustainability_bonus > 0:
            adjustments['sustainability_bonus'] = sustainability_bonus
            final_score += sustainability_bonus

        # Limitar 0-100
        final_score = max(0, min(100, final_score))

        return {
            'score': round(final_score, 1),
            'base_score': round(base_score, 1),
            'adjustments': adjustments,
            'grade': self._grade_score(final_score),
            'inbreeding_analysis': inbreeding_analysis
        }

    def _calculate_base_compatibility(self, bull_data: Dict, priorities: Dict) -> float:
        """Calcula score base de compatibilidade"""
        total_contribution = 0
        max_possible = 0

        for index, weight in priorities.items():
            value = self._get_value(bull_data, index)
            if value is None:
                continue

            # Normalizar
            normalized = self._normalize_value(index, value)

            # Contribuição
            contribution = normalized * abs(weight) * 100
            total_contribution += contribution
            max_possible += abs(weight) * 100

        if max_possible > 0:
            return (total_contribution / max_possible) * 100
        return 50

    def _normalize_value(self, index: str, value: float) -> float:
        """Normaliza valor para 0-1"""
        ranges = {
            'milk': (-1000, 2000),
            'protein': (-30, 80),
            'fat': (-30, 150),
            'productive_life': (-3, 8),
            'scs': (3.5, 2.5),  # Invertido
            'fertility_index': (-2, 4),
            'net_merit': (-500, 1500),
            'tpi': (1800, 3500),
            'health_index': (90, 115),
            'feed_efficiency': (85, 115),
        }

        range_min, range_max = ranges.get(index, (0, 100))

        if range_min > range_max:  # Invertido
            normalized = 1 - ((value - range_max) / (range_min - range_max))
        else:
            normalized = (value - range_min) / (range_max - range_min)

        return max(0, min(1, normalized))

    def _calculate_genotype_bonus(self, bull_data: Dict) -> float:
        """Bônus por genótipos desejáveis"""
        bonus = 0

        # A2A2 Beta Casein
        beta_casein = bull_data.get('beta_casein')
        if beta_casein == 'A2A2':
            bonus += 5  # +5 pontos
        elif beta_casein == 'A1A2':
            bonus += 2  # +2 pontos

        # Kappa Casein BB (melhor para queijo)
        kappa_casein = bull_data.get('kappa_casein')
        if kappa_casein == 'BB':
            bonus += 3
        elif kappa_casein == 'AB':
            bonus += 1

        # Livre de haplótipos (todos Free)
        haplotype_free = True
        for hap in ['hh1', 'hh2', 'hh3', 'hh4', 'hh5', 'hh6']:
            status = self._get_haplotype_status(bull_data, hap)
            if status != 'Free':
                haplotype_free = False
                break

        if haplotype_free:
            bonus += 5  # +5 pontos

        return bonus

    def _calculate_complementarity(self, female_data: Dict, bull_data: Dict) -> float:
        """Bônus se touro compensa fraquezas da fêmea"""
        bonus = 0

        # Índices para analisar
        indices = ['milk', 'productive_life', 'fertility_index', 'health_index']

        for index in indices:
            female_val = self._get_value(female_data, index)
            bull_val = self._get_value(bull_data, index)

            if female_val is None or bull_val is None:
                continue

            female_norm = self._normalize_value(index, female_val)
            bull_norm = self._normalize_value(index, bull_val)

            # Se fêmea é fraca e touro é forte
            if female_norm < 0.4 and bull_norm > 0.6:
                bonus += 2

        return bonus

    def _calculate_sustainability_bonus(self, bull_data: Dict) -> float:
        """Bônus por eficiência e sustentabilidade"""
        bonus = 0

        # Feed Efficiency alto
        feed_eff = self._get_value(bull_data, 'feed_efficiency')
        if feed_eff and feed_eff > 105:
            bonus += 3

        # RFI negativo (eficiente)
        rfi = self._get_value(bull_data, 'rfi')
        if rfi and rfi < -100:
            bonus += 3

        # Eco$ alto
        eco = self._get_value(bull_data, 'eco_dollars')
        if eco and eco > 200:
            bonus += 2

        return bonus

    def _grade_score(self, score: float) -> str:
        """Classifica o score"""
        if score >= 90:
            return 'A+ Excelente'
        elif score >= 80:
            return 'A Muito Bom'
        elif score >= 70:
            return 'B+ Bom'
        elif score >= 60:
            return 'B Regular'
        elif score >= 50:
            return 'C Mediano'
        elif score >= 35:
            return 'D Fraco'
        else:
            return 'F Inadequado'


# Instância global
genetic_calculator_complete = GeneticCalculatorComplete()
