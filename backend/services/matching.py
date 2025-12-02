"""
Serviço de Matching e Recomendação AVANÇADO
Sistema Genefy - Usa cálculos genéticos com ~80% acurácia
"""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from backend.models.database import Female, Bull
from backend.services.genetics import genetic_calculator, GeneticCalculator


class MatchingService:
    """Serviço de matching entre fêmeas e touros"""
    
    def __init__(self, db_session: Session):
        self.session = db_session
        self.calculator = genetic_calculator
    
    def match_single(self, female_id: int, bull_id: int) -> Dict:
        """Analisa um acasalamento específico"""
        female = self.session.query(Female).get(female_id)
        bull = self.session.query(Bull).get(bull_id)
        
        if not female:
            raise ValueError(f"Fêmea {female_id} não encontrada")
        if not bull:
            raise ValueError(f"Touro {bull_id} não encontrado")
        
        female_data = self._prepare_female_data(female)
        bull_data = self._prepare_bull_data(bull)
        
        pppv = self.calculator.calculate_pppv(female_data, bull_data)
        inbreeding = self.calculator.calculate_inbreeding(female_data, bull_data)
        compatibility = self.calculator.calculate_compatibility_score(female_data, bull_data)
        
        return {
            'female': {
                'id': female.id, 'reg_id': female.reg_id,
                'internal_id': female.internal_id, 'name': female.name,
                'main_indices': self._get_main_indices(female_data)
            },
            'bull': {
                'id': bull.id, 'code': bull.code, 'name': bull.name,
                'source': bull.source, 'main_indices': self._get_main_indices(bull_data)
            },
            'analysis': {'pppv': pppv, 'inbreeding': inbreeding, 'compatibility': compatibility},
            'recommendation': self._generate_recommendation(compatibility, inbreeding)
        }
    
    def match_batch(self, female_ids: List[int], priorities: Optional[Dict] = None,
                   max_inbreeding: float = 6.0, top_n: int = 5, filters: Optional[Dict] = None) -> Dict:
        """Encontra os melhores touros para um lote de fêmeas"""
        results = []
        
        females = self.session.query(Female).filter(Female.id.in_(female_ids)).all()
        bulls_query = self.session.query(Bull).filter(Bull.is_available == True)
        
        if filters:
            bulls_query = self._apply_bull_filters(bulls_query, filters)
        
        bulls = bulls_query.all()
        
        if not bulls:
            raise ValueError("Nenhum touro disponível")
        
        bulls_data = [self._prepare_bull_data(bull) for bull in bulls]
        
        for female in females:
            female_data = self._prepare_female_data(female)
            
            top_bulls = self.calculator.rank_bulls_for_female(
                female_data=female_data, bulls=bulls_data,
                top_n=top_n, max_inbreeding=max_inbreeding, custom_weights=priorities
            )
            
            formatted_bulls = []
            for item in top_bulls:
                formatted_bulls.append({
                    'rank': item['rank'], 'bull': item['bull'],
                    'score': item['iep'], 'grade': item['grade'],
                    'inbreeding': {'expected_inbreeding': item['inbreeding'], 'risk_level': item['inbreeding_risk']},
                    'reliability': item['reliability'], 'categories': item['categories']
                })
            
            results.append({
                'female': {
                    'id': female.id, 'reg_id': female.reg_id,
                    'internal_id': female.internal_id, 'name': female.name,
                    'main_indices': self._get_main_indices(female_data)
                },
                'top_bulls': formatted_bulls
            })
        
        all_scores = []
        all_inbreeding = []
        bulls_used = set()
        
        for result in results:
            for bull in result['top_bulls']:
                all_scores.append(bull['score'])
                all_inbreeding.append(bull['inbreeding']['expected_inbreeding'])
                bulls_used.add(bull['bull']['code'])
        
        return {
            'summary': {
                'total_females': len(females), 'total_bulls_analyzed': len(bulls),
                'top_n': top_n, 'max_inbreeding': max_inbreeding,
                'priorities_used': priorities or 'default',
                'average_iep': round(sum(all_scores) / len(all_scores), 1) if all_scores else 0,
                'average_inbreeding': round(sum(all_inbreeding) / len(all_inbreeding), 2) if all_inbreeding else 0,
                'unique_bulls_recommended': len(bulls_used)
            },
            'results': results
        }
    
    def _prepare_female_data(self, female: Female) -> Dict:
        """Prepara dados da fêmea"""
        data = {'id': female.id, 'reg_id': female.reg_id, 'internal_id': female.internal_id, 'genetic_data': female.genetic_data or {}}
        
        indices = ['milk', 'protein', 'fat', 'productive_life', 'scs', 'dpr', 'fertility_index',
                   'udc', 'flc', 'ptat', 'net_merit', 'tpi', 'genomic_inbreeding', 'hcr', 'ccr',
                   'cow_livability', 'heifer_livability']
        
        for index in indices:
            value = getattr(female, index, None)
            if value is not None:
                data[index] = value
        
        for field in ['sire_reg', 'sire_naab', 'mgs_reg', 'mgs_naab']:
            value = getattr(female, field, None)
            if value:
                data[field] = value
        
        for field in ['hh1', 'hh2', 'hh3', 'hh4', 'hh5', 'hh6']:
            value = getattr(female, field, None)
            if value is not None:
                data[field] = value
        
        return data
    
    def _prepare_bull_data(self, bull: Bull) -> Dict:
        """Prepara dados do touro"""
        data = {
            'id': bull.id, 'code': bull.code, 'name': bull.name,
            'source': bull.source, 'naab_code': bull.naab_code,
            'genetic_data': bull.genetic_data or {}
        }
        
        indices = ['milk', 'protein', 'fat', 'net_merit', 'cheese_merit', 'grazing_merit',
                   'tpi', 'gtpi', 'udc', 'flc', 'ptat', 'productive_life', 'scs', 'dpr',
                   'fertility_index', 'rfi', 'feed_saved', 'beta_casein', 'kappa_casein', 'gfi',
                   'hcr', 'ccr', 'cow_livability', 'heifer_livability', 'sire_calving_ease',
                   'daughter_calving_ease', 'sire_stillbirth', 'daughter_stillbirth',
                   'milk_rel', 'dpr_rel', 'productive_life_rel', 'num_daughters']
        
        for index in indices:
            value = getattr(bull, index, None)
            if value is not None:
                data[index] = value
        
        # Reliabilities
        reliabilities = getattr(bull, 'reliabilities', None)
        if reliabilities:
            data['reliabilities'] = reliabilities
        
        # Haplótipos
        haplotypes = bull.haplotypes or {}
        if isinstance(haplotypes, dict):
            data['haplotypes'] = haplotypes
            for hap, status in haplotypes.items():
                data[hap.lower()] = status
        
        return data
    
    def _get_main_indices(self, data: Dict) -> Dict:
        indices = {}
        keys = ['milk', 'protein', 'fat', 'net_merit', 'productive_life', 'fertility_index',
                'udc', 'scs', 'ptat', 'gfi', 'genomic_inbreeding']
        
        for key in keys:
            value = data.get(key)
            if value is not None:
                indices[key] = round(value, 2) if isinstance(value, float) else value
        
        return indices
    
    def _apply_bull_filters(self, query, filters: Dict):
        if 'min_milk' in filters and filters['min_milk']:
            query = query.filter(Bull.milk >= filters['min_milk'])
        if 'min_net_merit' in filters and filters['min_net_merit']:
            query = query.filter(Bull.net_merit >= filters['min_net_merit'])
        if 'min_productive_life' in filters and filters['min_productive_life']:
            query = query.filter(Bull.productive_life >= filters['min_productive_life'])
        if 'beta_casein' in filters and filters['beta_casein']:
            query = query.filter(Bull.beta_casein == filters['beta_casein'])
        if 'max_gfi' in filters and filters['max_gfi']:
            query = query.filter(Bull.gfi <= filters['max_gfi'])
        if 'source' in filters and filters['source']:
            query = query.filter(Bull.source == filters['source'])
        return query
    
    def _generate_recommendation(self, compatibility: Dict, inbreeding: Dict) -> Dict:
        score = compatibility['score']
        inb = inbreeding['expected_inbreeding']
        haplotype_risks = inbreeding.get('haplotype_risks', [])
        critical_risks = [r for r in haplotype_risks if r.get('severity') == 'critical']
        
        if critical_risks:
            status, message, color = 'not_recommended', '❌ Acasalamento NÃO recomendado - Risco letal', 'red'
        elif score >= 75 and inb <= 6.0:
            status, message, color = 'highly_recommended', '✅ Altamente recomendado!', 'green'
        elif score >= 60 and inb <= 6.0:
            status, message, color = 'recommended', '✅ Recomendado', 'blue'
        elif score >= 50 or inb <= 8.0:
            status, message, color = 'acceptable', '⚠️ Aceitável - monitorar resultados', 'yellow'
        else:
            status, message, color = 'not_recommended', '❌ Não recomendado', 'red'
        
        positives, negatives = [], []
        
        if score >= 70:
            positives.append('Excelente compatibilidade genética')
        if inb <= 6.25:
            positives.append(f'Consanguinidade ideal ({inb:.1f}%)')
        if not haplotype_risks:
            positives.append('Sem riscos de haplótipos')
        
        if score < 50:
            negatives.append(f'Compatibilidade baixa (IEP: {score:.0f})')
        if inb > 6.25:
            negatives.append(f'Consanguinidade acima do ideal ({inb:.1f}%)')
        for risk in critical_risks:
            negatives.append(f"Risco crítico: {risk['haplotype']}")
        
        return {
            'status': status, 'message': message, 'color': color,
            'positives': positives, 'negatives': negatives,
            'grade': compatibility['grade'], 'confidence': compatibility.get('reliability', 60)
        }