"""
API REST - Rotas Principais
Sistema de Acasalamento de Gado Leiteiro
"""

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from sqlalchemy.orm import Session
from sqlalchemy import or_
import os
from datetime import datetime

from backend.models.database import get_session, Female, Bull, Mating, BatchMating
from backend.services.importer import DataImporter
from backend.services.matching import MatchingService
from backend.services.analytics import AnalyticsService
from backend.services.genetics import genetic_calculator
from backend.services.genetics import genetic_calculator_complete


# Criar blueprints
api = Blueprint('api', __name__, url_prefix='/api')


def get_db():
    """Helper para pegar sessão do banco"""
    from app import engine
    return get_session(engine)


# ============================================================================
# FÊMEAS (FEMALES)
# ============================================================================

@api.route('/females', methods=['GET'])
def get_females():
    """
    GET /api/females
    Lista todas as fêmeas com filtros e paginação
    
    Query params:
        - page: número da página (default: 1)
        - per_page: itens por página (default: 50)
        - active_only: apenas ativas (default: true)
        - search: busca por ID ou nome
        - sort_by: campo para ordenar (default: reg_id)
    """
    db = get_db()
    
    # Parâmetros
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    search = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'reg_id')
    
    # Query base
    query = db.query(Female)
    
    # Filtros
    if active_only:
        query = query.filter(Female.is_active == True)
    
    if search:
        query = query.filter(
            or_(
                Female.reg_id.like(f'%{search}%'),
                Female.internal_id.like(f'%{search}%'),
                Female.name.like(f'%{search}%')
            )
        )
    
    # Ordenação
    if hasattr(Female, sort_by):
        query = query.order_by(getattr(Female, sort_by))
    
    # Paginação
    total = query.count()
    females = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return jsonify({
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page,
        'females': [f.to_dict() for f in females]
    })


@api.route('/females/<int:female_id>', methods=['GET'])
def get_female(female_id):
    """
    GET /api/females/:id
    Detalhes de uma fêmea específica

    Query params:
        - complete: retorna todos os índices (default: true)
    """
    db = get_db()
    female = db.query(Female).get(female_id)

    if not female:
        return jsonify({'error': 'Fêmea não encontrada'}), 404

    # Verificar se deve retornar dados completos
    complete = request.args.get('complete', 'true').lower() == 'true'

    # Buscar histórico de acasalamentos
    matings = db.query(Mating).filter(Mating.female_id == female_id).all()

    return jsonify({
        'female': female.to_dict(complete=complete),
        'matings_count': len(matings),
        'recent_matings': [m.to_dict() for m in matings[:5]]
    })


@api.route('/females/import', methods=['POST'])
def import_females():
    """
    POST /api/females/import
    Importa fêmeas de arquivo Excel
    
    Form data:
        - file: arquivo Excel
        - user: nome do usuário (default: 'Pedro')
    """
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    user = request.form.get('user', 'Pedro')
    
    if file.filename == '':
        return jsonify({'error': 'Nome de arquivo inválido'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'Arquivo deve ser Excel (.xlsx ou .xls)'}), 400
    
    # Salvar temporariamente
    filename = secure_filename(file.filename)
    filepath = os.path.join('uploads', filename)
    os.makedirs('uploads', exist_ok=True)
    file.save(filepath)
    
    try:
        # Importar
        db = get_db()
        importer = DataImporter(db)
        stats = importer.import_females_from_excel(filepath, user)
        
        # Remover arquivo temporário
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'message': 'Importação concluída',
            'stats': stats
        })
        
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# TOUROS (BULLS)
# ============================================================================

@api.route('/bulls', methods=['GET'])
def get_bulls():
    """
    GET /api/bulls
    Lista todos os touros com filtros
    
    Query params:
        - page, per_page: paginação
        - available_only: apenas disponíveis (default: true)
        - search: busca por código ou nome
        - min_milk, min_net_merit, etc: filtros por índices
        - sort_by: campo para ordenar (default: net_merit desc)
    """
    db = get_db()
    
    # Parâmetros
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    available_only = request.args.get('available_only', 'true').lower() == 'true'
    search = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'net_merit')
    sort_order = request.args.get('sort_order', 'desc')
    
    # Query base
    query = db.query(Bull)
    
    # Filtros
    if available_only:
        query = query.filter(Bull.is_available == True)
    
    if search:
        query = query.filter(
            or_(
                Bull.code.like(f'%{search}%'),
                Bull.name.like(f'%{search}%')
            )
        )
    
    # Filtros por índices
    filters = ['min_milk', 'min_net_merit', 'min_productive_life', 
               'beta_casein', 'max_gfi']
    
    for filter_name in filters:
        value = request.args.get(filter_name)
        if value:
            if filter_name.startswith('min_'):
                index = filter_name[4:]  # Remove 'min_'
                if hasattr(Bull, index):
                    query = query.filter(getattr(Bull, index) >= float(value))
            elif filter_name.startswith('max_'):
                index = filter_name[4:]  # Remove 'max_'
                if hasattr(Bull, index):
                    query = query.filter(getattr(Bull, index) <= float(value))
            else:
                if hasattr(Bull, filter_name):
                    query = query.filter(getattr(Bull, filter_name) == value)
    
    # Ordenação
    if hasattr(Bull, sort_by):
        order_col = getattr(Bull, sort_by)
        if sort_order == 'desc':
            order_col = order_col.desc()
        query = query.order_by(order_col)
    
    # Paginação
    total = query.count()
    bulls = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return jsonify({
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page,
        'bulls': [b.to_dict() for b in bulls]
    })


@api.route('/bulls/<bull_code>', methods=['GET'])
def get_bull(bull_code):
    """
    GET /api/bulls/:code
    Detalhes de um touro específico
    """
    db = get_db()
    bull = db.query(Bull).filter(Bull.code == bull_code).first()
    
    if not bull:
        return jsonify({'error': 'Touro não encontrado'}), 404
    
    # Buscar histórico de uso
    matings = db.query(Mating).filter(Mating.bull_id == bull.id).all()
    
    # Estatísticas de uso
    total_matings = len(matings)
    successful = sum(1 for m in matings if m.success)
    avg_score = sum(m.compatibility_score for m in matings if m.compatibility_score) / total_matings if total_matings > 0 else 0
    
    return jsonify({
        'bull': bull.to_dict(),
        'usage_stats': {
            'total_matings': total_matings,
            'successful_matings': successful,
            'success_rate': round(successful / total_matings * 100, 1) if total_matings > 0 else 0,
            'avg_compatibility_score': round(avg_score, 1)
        },
        'recent_matings': [m.to_dict() for m in matings[:5]]
    })


@api.route('/bulls/import', methods=['POST'])
def import_bulls():
    """
    POST /api/bulls/import
    Importa touros de arquivo PDF
    """
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    user = request.form.get('user', 'Pedro')
    
    if not file.filename.endswith('.pdf'):
        return jsonify({'error': 'Arquivo deve ser PDF'}), 400
    
    # Salvar temporariamente
    filename = secure_filename(file.filename)
    filepath = os.path.join('uploads', filename)
    os.makedirs('uploads', exist_ok=True)
    file.save(filepath)
    
    try:
        # Importar
        db = get_db()
        importer = DataImporter(db)
        stats = importer.import_bulls_from_pdf(filepath, user)
        
        # Remover arquivo temporário
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'message': 'Importação concluída',
            'stats': stats
        })
        
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ACASALAMENTOS (MATINGS)
# ============================================================================

@api.route('/matings/manual', methods=['POST'])
def create_manual_mating():
    """
    POST /api/matings/manual
    Cria acasalamento manual e retorna análise completa

    Body:
        - female_id: ID da fêmea
        - bull_id: ID do touro
        - save: se deve salvar no histórico (default: true)
    """
    data = request.json

    female_id = data.get('female_id')
    bull_id = data.get('bull_id')
    save = data.get('save', True)

    if not female_id or not bull_id:
        return jsonify({'error': 'female_id e bull_id são obrigatórios'}), 400

    try:
        db = get_db()
        matching_service = MatchingService(db)

        # Analisar acasalamento
        result = matching_service.match_single(female_id, bull_id)

        # Salvar no histórico se solicitado
        if save:
            female = db.query(Female).get(female_id)
            bull = db.query(Bull).get(bull_id)

            mating = Mating(
                female_id=female_id,
                bull_id=bull_id,
                mating_type='manual',
                predicted_pppv=result['analysis']['pppv'],
                predicted_inbreeding=result['analysis']['inbreeding']['expected_inbreeding'],
                compatibility_score=result['analysis']['compatibility']['score'],
                status='planned',
                created_by=data.get('user', 'Pedro')
            )

            db.add(mating)
            db.commit()

            result['mating_id'] = mating.id
            result['saved'] = True

        return jsonify(result)

    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/matings/analyze_complete', methods=['POST'])
def analyze_mating_complete():
    """
    POST /api/matings/analyze_complete
    Análise COMPLETA de acasalamento usando genetic_calculator_complete

    Retorna:
        - PPPV para TODOS os índices (por categoria)
        - Análise avançada de consanguinidade com detecção de haplótipos
        - Score de compatibilidade expandido
        - Recomendações detalhadas

    Body:
        - female_id: ID da fêmea
        - bull_id: ID do touro
    """
    data = request.json

    female_id = data.get('female_id')
    bull_id = data.get('bull_id')

    if not female_id or not bull_id:
        return jsonify({'error': 'female_id e bull_id são obrigatórios'}), 400

    try:
        db = get_db()

        # Buscar fêmea e touro
        female = db.query(Female).get(female_id)
        bull = db.query(Bull).get(bull_id)

        if not female:
            return jsonify({'error': 'Fêmea não encontrada'}), 404
        if not bull:
            return jsonify({'error': 'Touro não encontrado'}), 404

        # Converter para dicts
        female_data = female.to_dict(complete=True)
        bull_data = bull.to_dict()

        # Análise completa
        calc = genetic_calculator_complete

        # 1. PPPV completo
        pppv_complete = calc.calculate_pppv_complete(female_data, bull_data)

        # 2. Análise de consanguinidade com haplótipos
        inbreeding_analysis = calc.analyze_inbreeding_complete(female_data, bull_data)

        # 3. Score de compatibilidade expandido
        priorities = data.get('priorities')
        compatibility = calc.calculate_compatibility_score_complete(
            female_data, bull_data, priorities
        )

        # Resultado
        result = {
            'female': {
                'id': female.id,
                'reg_id': female.reg_id,
                'internal_id': female.internal_id
            },
            'bull': {
                'id': bull.id,
                'code': bull.code,
                'name': bull.name
            },
            'analysis': {
                'pppv_complete': pppv_complete,
                'inbreeding_analysis': inbreeding_analysis,
                'compatibility': compatibility
            },
            'recommendation': {
                'acceptable': inbreeding_analysis['acceptable'] and compatibility['score'] >= 60,
                'score': compatibility['score'],
                'grade': compatibility['grade'],
                'warnings': [],
                'highlights': []
            }
        }

        # Adicionar avisos
        if not inbreeding_analysis['acceptable']:
            result['recommendation']['warnings'].append({
                'type': 'inbreeding',
                'message': inbreeding_analysis['recommendation']
            })

        if len(inbreeding_analysis['haplotype_risks']) > 0:
            for risk in inbreeding_analysis['haplotype_risks']:
                if risk['risk'].startswith('ALTO'):
                    result['recommendation']['warnings'].append({
                        'type': 'haplotype',
                        'haplotype': risk['haplotype'],
                        'message': risk['recommendation']
                    })

        # Adicionar destaques
        if compatibility['score'] >= 85:
            result['recommendation']['highlights'].append('Excelente compatibilidade genética')

        if 'genotype_bonus' in compatibility['adjustments']:
            result['recommendation']['highlights'].append('Genótipos desejáveis (A2A2, Kappa BB, etc)')

        if 'sustainability_bonus' in compatibility['adjustments']:
            result['recommendation']['highlights'].append('Alta eficiência alimentar e sustentabilidade')

        return jsonify(result)

    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@api.route('/matings/batch', methods=['POST'])
def create_batch_mating():
    """
    POST /api/matings/batch
    Acasalamento em lote: encontra melhores touros para múltiplas fêmeas
    
    Body:
        - female_ids: Lista de IDs das fêmeas
        - priorities: Dict com pesos {index: weight}
        - max_inbreeding: Limite de consanguinidade (default: 6.0)
        - top_n: Quantos touros retornar por fêmea (default: 5)
        - filters: Filtros para touros
        - save: se deve salvar (default: false)
    """
    data = request.json
    
    female_ids = data.get('female_ids', [])
    
    if not female_ids:
        return jsonify({'error': 'female_ids é obrigatório'}), 400
    
    if len(female_ids) > 100:
        return jsonify({'error': 'Máximo de 100 fêmeas por lote'}), 400
    
    try:
        db = get_db()
        matching_service = MatchingService(db)
        
        result = matching_service.match_batch(
            female_ids=female_ids,
            priorities=data.get('priorities'),
            max_inbreeding=data.get('max_inbreeding', 6.0),
            top_n=data.get('top_n', 5),
            filters=data.get('filters')
        )
        
        # Salvar lote se solicitado
        if data.get('save', False):
            batch = BatchMating(
                batch_name=data.get('batch_name', f'Lote {datetime.now().strftime("%Y-%m-%d %H:%M")}'),
                description=data.get('description'),
                priorities=data.get('priorities'),
                max_inbreeding=data.get('max_inbreeding', 6.0),
                female_ids=female_ids,
                recommendations=result,
                created_by=data.get('user', 'Pedro')
            )
            
            db.add(batch)
            db.commit()
            
            result['batch_id'] = batch.id
            result['saved'] = True
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/matings', methods=['GET'])
def get_matings():
    """
    GET /api/matings
    Lista acasalamentos com filtros
    """
    db = get_db()
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    female_id = request.args.get('female_id', type=int)
    bull_id = request.args.get('bull_id', type=int)
    
    query = db.query(Mating)
    
    if status:
        query = query.filter(Mating.status == status)
    if female_id:
        query = query.filter(Mating.female_id == female_id)
    if bull_id:
        query = query.filter(Mating.bull_id == bull_id)
    
    query = query.order_by(Mating.created_at.desc())
    
    total = query.count()
    matings = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return jsonify({
        'total': total,
        'page': page,
        'per_page': per_page,
        'matings': [m.to_dict() for m in matings]
    })


@api.route('/matings/<int:mating_id>', methods=['GET'])
def get_mating(mating_id):
    """GET /api/matings/:id - Detalhes de um acasalamento"""
    db = get_db()
    mating = db.query(Mating).get(mating_id)
    
    if not mating:
        return jsonify({'error': 'Acasalamento não encontrado'}), 404
    
    return jsonify(mating.to_dict())


@api.route('/matings/<int:mating_id>', methods=['PUT'])
def update_mating(mating_id):
    """
    PUT /api/matings/:id
    Atualiza um acasalamento (ex: adicionar dados reais do bezerro)
    """
    db = get_db()
    mating = db.query(Mating).get(mating_id)
    
    if not mating:
        return jsonify({'error': 'Acasalamento não encontrado'}), 404
    
    data = request.json
    
    # Atualizar campos permitidos
    if 'status' in data:
        mating.status = data['status']
    if 'success' in data:
        mating.success = data['success']
    if 'actual_calving_date' in data:
        mating.actual_calving_date = datetime.fromisoformat(data['actual_calving_date'])
    if 'actual_genetic_data' in data:
        mating.actual_genetic_data = data['actual_genetic_data']
    if 'calf_id' in data:
        mating.calf_id = data['calf_id']
    if 'calf_sex' in data:
        mating.calf_sex = data['calf_sex']
    if 'notes' in data:
        mating.notes = data['notes']
    
    db.commit()
    
    return jsonify({
        'success': True,
        'mating': mating.to_dict()
    })


# Continua na parte 2...