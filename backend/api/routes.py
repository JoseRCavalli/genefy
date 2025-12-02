"""
API REST - Rotas Principais
Sistema de Acasalamento de Gado Leiteiro
"""

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from sqlalchemy import or_, create_engine
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

from backend.models.database import Female, Bull, Mating, BatchMating, Base
from backend.services.importer import DataImporter
from backend.services.matching import MatchingService
from backend.services.genetics import genetic_calculator, genetic_calculator_complete


# Criar blueprint
api = Blueprint('api', __name__, url_prefix='/api')


# ============================================================================
# ENGINE E SESSÃO - INDEPENDENTE DO APP.PY
# ============================================================================

_engine = None
_SessionLocal = None


def get_engine():
    """Obtém ou cria o engine do banco de dados"""
    global _engine, _SessionLocal
    
    if _engine is None:
        # Determinar URL do banco
        database_url = os.environ.get('DATABASE_URL')
        
        if database_url:
            # PostgreSQL (produção)
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)
        else:
            # SQLite (local)
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(base_dir, 'database', 'cattle_breeding.db')
            database_url = f'sqlite:///{db_path}'
        
        _engine = create_engine(database_url, echo=False)
        _SessionLocal = sessionmaker(bind=_engine)
        
        # Criar tabelas se não existirem
        Base.metadata.create_all(_engine)
    
    return _engine


def get_db():
    """Helper para pegar sessão do banco"""
    engine = get_engine()
    if _SessionLocal is None:
        get_engine()  # Inicializa se necessário
    return _SessionLocal()


# ============================================================================
# FÊMEAS (FEMALES)
# ============================================================================

@api.route('/females', methods=['GET'])
def get_females():
    """Lista todas as fêmeas com filtros e paginação"""
    db = get_db()
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        search = request.args.get('search', '')
        sort_by = request.args.get('sort_by', 'reg_id')
        
        query = db.query(Female)
        
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
        
        if hasattr(Female, sort_by):
            query = query.order_by(getattr(Female, sort_by))
        
        total = query.count()
        females = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return jsonify({
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
            'females': [f.to_dict() for f in females]
        })
    finally:
        db.close()


@api.route('/females/<int:female_id>', methods=['GET'])
def get_female(female_id):
    """Detalhes de uma fêmea específica"""
    db = get_db()
    
    try:
        female = db.query(Female).get(female_id)
        
        if not female:
            return jsonify({'error': 'Fêmea não encontrada'}), 404
        
        complete = request.args.get('complete', 'true').lower() == 'true'
        matings = db.query(Mating).filter(Mating.female_id == female_id).all()
        
        return jsonify({
            'female': female.to_dict(complete=complete),
            'matings_count': len(matings),
            'recent_matings': [m.to_dict() for m in matings[:5]]
        })
    finally:
        db.close()


@api.route('/females/import', methods=['POST'])
def import_females():
    """Importa fêmeas de arquivo Excel"""
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    user = request.form.get('user', 'Sistema')
    
    if file.filename == '':
        return jsonify({'error': 'Nome de arquivo inválido'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'Arquivo deve ser Excel (.xlsx ou .xls)'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join('uploads', filename)
    os.makedirs('uploads', exist_ok=True)
    file.save(filepath)
    
    try:
        db = get_db()
        importer = DataImporter(db)
        stats = importer.import_females_from_excel(filepath, user)
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
    """Lista todos os touros com filtros"""
    db = get_db()
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        available_only = request.args.get('available_only', 'true').lower() == 'true'
        search = request.args.get('search', '')
        sort_by = request.args.get('sort_by', 'net_merit')
        sort_order = request.args.get('sort_order', 'desc')
        
        query = db.query(Bull)
        
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
        for filter_name in ['min_milk', 'min_net_merit', 'min_productive_life', 'beta_casein', 'max_gfi']:
            value = request.args.get(filter_name)
            if value:
                if filter_name.startswith('min_'):
                    index = filter_name[4:]
                    if hasattr(Bull, index):
                        query = query.filter(getattr(Bull, index) >= float(value))
                elif filter_name.startswith('max_'):
                    index = filter_name[4:]
                    if hasattr(Bull, index):
                        query = query.filter(getattr(Bull, index) <= float(value))
                else:
                    if hasattr(Bull, filter_name):
                        query = query.filter(getattr(Bull, filter_name) == value)
        
        if hasattr(Bull, sort_by):
            order_col = getattr(Bull, sort_by)
            if sort_order == 'desc':
                order_col = order_col.desc()
            query = query.order_by(order_col)
        
        total = query.count()
        bulls = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return jsonify({
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
            'bulls': [b.to_dict() for b in bulls]
        })
    finally:
        db.close()


@api.route('/bulls/<bull_code>', methods=['GET'])
def get_bull(bull_code):
    """Detalhes de um touro específico"""
    db = get_db()
    
    try:
        bull = db.query(Bull).filter(Bull.code == bull_code).first()
        
        if not bull:
            return jsonify({'error': 'Touro não encontrado'}), 404
        
        matings = db.query(Mating).filter(Mating.bull_id == bull.id).all()
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
    finally:
        db.close()


@api.route('/bulls/import', methods=['POST'])
def import_bulls():
    """Importa touros de arquivo PDF"""
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    user = request.form.get('user', 'Sistema')
    
    if not file.filename.endswith('.pdf'):
        return jsonify({'error': 'Arquivo deve ser PDF'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join('uploads', filename)
    os.makedirs('uploads', exist_ok=True)
    file.save(filepath)
    
    try:
        db = get_db()
        importer = DataImporter(db)
        stats = importer.import_bulls_from_pdf(filepath, user)
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
    """Cria acasalamento manual e retorna análise completa"""
    data = request.json
    
    female_id = data.get('female_id')
    bull_id = data.get('bull_id')
    save = data.get('save', True)
    
    if not female_id or not bull_id:
        return jsonify({'error': 'female_id e bull_id são obrigatórios'}), 400
    
    db = get_db()
    
    try:
        matching_service = MatchingService(db)
        result = matching_service.match_single(female_id, bull_id)
        
        if save:
            mating = Mating(
                female_id=female_id,
                bull_id=bull_id,
                mating_type='manual',
                predicted_pppv=result['analysis']['pppv'],
                predicted_inbreeding=result['analysis']['inbreeding']['expected_inbreeding'],
                compatibility_score=result['analysis']['compatibility']['score'],
                status='planned',
                created_by=data.get('user', 'Sistema')
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
    finally:
        db.close()


@api.route('/matings/analyze_complete', methods=['POST'])
def analyze_mating_complete():
    """Análise COMPLETA de acasalamento"""
    data = request.json
    
    female_id = data.get('female_id')
    bull_id = data.get('bull_id')
    
    if not female_id or not bull_id:
        return jsonify({'error': 'female_id e bull_id são obrigatórios'}), 400
    
    db = get_db()
    
    try:
        female = db.query(Female).get(female_id)
        bull = db.query(Bull).get(bull_id)
        
        if not female:
            return jsonify({'error': 'Fêmea não encontrada'}), 404
        if not bull:
            return jsonify({'error': 'Touro não encontrado'}), 404
        
        female_data = female.to_dict(complete=True)
        bull_data = bull.to_dict()
        
        calc = genetic_calculator_complete
        
        # Cálculos
        pppv = calc.calculate_pppv(female_data, bull_data)
        inbreeding = calc.calculate_inbreeding(female_data, bull_data)
        compatibility = calc.calculate_compatibility_score(female_data, bull_data, data.get('priorities'))
        
        result = {
            'female': {'id': female.id, 'reg_id': female.reg_id, 'internal_id': female.internal_id},
            'bull': {'id': bull.id, 'code': bull.code, 'name': bull.name},
            'analysis': {
                'pppv': pppv,
                'inbreeding': inbreeding,
                'compatibility': compatibility
            },
            'recommendation': {
                'acceptable': inbreeding['acceptable'] and compatibility['score'] >= 60,
                'score': compatibility['score'],
                'grade': compatibility['grade'],
                'warnings': [],
                'highlights': []
            }
        }
        
        if not inbreeding['acceptable']:
            result['recommendation']['warnings'].append({
                'type': 'inbreeding',
                'message': inbreeding['recommendation']
            })
        
        if compatibility['score'] >= 85:
            result['recommendation']['highlights'].append('Excelente compatibilidade genética')
        
        return jsonify(result)
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500
    finally:
        db.close()


@api.route('/matings/batch', methods=['POST'])
def create_batch_mating():
    """Acasalamento em lote"""
    data = request.json
    female_ids = data.get('female_ids', [])
    
    if not female_ids:
        return jsonify({'error': 'female_ids é obrigatório'}), 400
    
    if len(female_ids) > 100:
        return jsonify({'error': 'Máximo de 100 fêmeas por lote'}), 400
    
    db = get_db()
    
    try:
        matching_service = MatchingService(db)
        
        result = matching_service.match_batch(
            female_ids=female_ids,
            priorities=data.get('priorities'),
            max_inbreeding=data.get('max_inbreeding', 6.0),
            top_n=data.get('top_n', 5),
            filters=data.get('filters')
        )
        
        if data.get('save', False):
            batch = BatchMating(
                batch_name=data.get('batch_name', f'Lote {datetime.now().strftime("%Y-%m-%d %H:%M")}'),
                description=data.get('description'),
                priorities=data.get('priorities'),
                max_inbreeding=data.get('max_inbreeding', 6.0),
                female_ids=female_ids,
                recommendations=result,
                created_by=data.get('user', 'Sistema')
            )
            db.add(batch)
            db.commit()
            result['batch_id'] = batch.id
            result['saved'] = True
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@api.route('/matings', methods=['GET'])
def get_matings():
    """Lista acasalamentos com filtros"""
    db = get_db()
    
    try:
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
    finally:
        db.close()


@api.route('/matings/<int:mating_id>', methods=['GET'])
def get_mating(mating_id):
    """Detalhes de um acasalamento"""
    db = get_db()
    
    try:
        mating = db.query(Mating).get(mating_id)
        
        if not mating:
            return jsonify({'error': 'Acasalamento não encontrado'}), 404
        
        return jsonify(mating.to_dict())
    finally:
        db.close()


@api.route('/matings/<int:mating_id>', methods=['PUT'])
def update_mating(mating_id):
    """Atualiza um acasalamento"""
    db = get_db()
    
    try:
        mating = db.query(Mating).get(mating_id)
        
        if not mating:
            return jsonify({'error': 'Acasalamento não encontrado'}), 404
        
        data = request.json
        
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
        
        return jsonify({'success': True, 'mating': mating.to_dict()})
    finally:
        db.close()