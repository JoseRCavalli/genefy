"""
Aplicação Principal - Flask
Sistema de Acasalamento de Gado Leiteiro- Genefy
"""

from flask import Flask, render_template, send_from_directory, jsonify
from flask_cors import CORS
import os
import logging
from flask import Flask, render_template, send_from_directory, jsonify
from flask_cors import CORS
import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuração de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar models e inicializar banco
from backend.models.database import init_database, get_session

# ============================================================================
# CONFIGURAÇÃO DE BANCO - SQLITE SEMPRE
# ============================================================================

def get_database_url():
    """
    Retorna URL do banco de dados.
    Prioridade: DATABASE_URL (PostgreSQL) > SQLite local
    """
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Correção para SQLAlchemy (postgres:// -> postgresql://)
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        print("[DB] Usando PostgreSQL (Produção)")
        return database_url
        
    # Fallback para SQLite
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'database', 'cattle_breeding.db')
    sqlite_url = f'sqlite:///{db_path}'
    print("[DB] Usando SQLite (Local)")
    return sqlite_url

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Criar app
app = Flask(__name__,
           template_folder=os.path.join(BASE_DIR, 'frontend', 'pages'),
           static_folder=os.path.join(BASE_DIR, 'frontend'))

# CORS
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}}, supports_credentials=True)

# Configurações
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)  # Sessão dura 30 dias

# Criar pastas sempre
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'database'), exist_ok=True)

# ============================================================================
# INICIALIZAÇÃO DO BANCO
# ============================================================================

DB_URL = get_database_url()
print(f"Banco: {DB_URL}")

try:
    engine = init_database(DB_URL)
    print("[OK] SQLite inicializado!")
except Exception as e:
    print(f"[ERRO] Erro ao inicializar banco: {e}")

# ============================================================================
# BLUEPRINTS HABILITADOS (SQLITE FUNCIONA)
# ============================================================================

try:
    from backend.api.routes import api
    from backend.api.analytics_routes import analytics_api
    from backend.api.routes import api
    from backend.api.analytics_routes import analytics_api
    from backend.api.auth import auth_api
    app.register_blueprint(api)
    app.register_blueprint(analytics_api)
    app.register_blueprint(auth_api)
    print("[OK] Blueprints habilitados - SQLite suporta")
except Exception as e:
    print(f"[AVISO] Erro ao registrar blueprints: {e}")

# ============================================================================
# ROTAS PRINCIPAIS
# ============================================================================

@app.route('/')
def index():
    """Landing Page (React)"""
    return send_from_directory('frontend/react_app', 'index.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard do sistema (requer autenticação)"""
    return send_from_directory('frontend/pages', 'index.html')

@app.route('/react-static/<path:filename>')
def serve_react_static(filename):
    """Arquivos estáticos do React"""
    return send_from_directory('frontend/react_app', filename)

@app.route('/api/health')
def health_check():
    """Health check"""
    try:
        db = get_session(engine)
        from backend.models.database import Female
        count = db.query(Female).count()
        db.close()
        
        return jsonify({
            'status': 'ok',
            'database': 'connected',
            'database_type': 'SQLite',
            'females_count': count,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/dashboard')
def dashboard_api():
    """Dashboard API"""
    try:
        db = get_session(engine)
        from backend.models.database import Female, Bull, Mating
        
        total_femeas = db.query(Female).count()
        total_touros = db.query(Bull).count() 
        total_acasalamentos = db.query(Mating).count()
        
        taxa_sucesso = 85 if total_acasalamentos > 0 else 0
        
        db.close()
        
        return jsonify({
            "total_femeas": total_femeas,
            "total_touros": total_touros, 
            "total_acasalamentos": total_acasalamentos,
            "taxa_sucesso": taxa_sucesso,
            "status": "success",
            "database_type": "SQLite"
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "total_femeas": 0,
            "total_touros": 0,
            "total_acasalamentos": 0,
            "taxa_sucesso": 0,
            "status": "error"
        }), 500

@app.route('/api/dashboard-full')
def dashboard_full_api():
    """API completa do dashboard - compatível com o frontend"""
    try:
        db = get_session(engine)
        from backend.models.database import Female, Bull, Mating
        
        # Estatísticas básicas
        total_females = db.query(Female).count()
        active_females = db.query(Female).filter(Female.is_active == True).count()
        total_bulls = db.query(Bull).count()
        available_bulls = db.query(Bull).filter(Bull.is_available == True).count()
        total_matings = db.query(Mating).count()
        
        # Médias do rebanho (simples por agora)
        avg_milk = db.query(Female.milk).filter(Female.milk.isnot(None)).all()
        avg_pl = db.query(Female.productive_life).filter(Female.productive_life.isnot(None)).all()
        avg_inb = db.query(Female.genomic_inbreeding).filter(Female.genomic_inbreeding.isnot(None)).all()
        
        # Calcular médias
        milk_avg = sum(x[0] for x in avg_milk) / len(avg_milk) if avg_milk else 0
        pl_avg = sum(x[0] for x in avg_pl) / len(avg_pl) if avg_pl else 0
        inb_avg = sum(x[0] for x in avg_inb) / len(avg_inb) if avg_inb else 0
        
        # Top touros (placeholder)
        top_bulls = []
        
        db.close()
        
        return jsonify({
            "summary": {
                "total_females": total_females,
                "active_females": active_females,
                "total_bulls": total_bulls,
                "available_bulls": available_bulls,
                "total_matings": total_matings,
                "recent_matings": 0,  # placeholder
                "success_rate": 85.0  # placeholder
            },
            "herd_averages": {
                "milk": round(milk_avg, 0),
                "productive_life": round(pl_avg, 2),
                "genomic_inbreeding": round(inb_avg, 2)
            },
            "top_bulls": top_bulls,
            "last_updated": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Erro na dashboard full API: {str(e)}")
        return jsonify({
            "summary": {
                "total_females": 0,
                "active_females": 0,
                "total_bulls": 0,
                "available_bulls": 0,
                "total_matings": 0,
                "recent_matings": 0,
                "success_rate": 0
            },
            "herd_averages": {
                "milk": 0,
                "productive_life": 0,
                "genomic_inbreeding": 0
            },
            "top_bulls": [],
            "last_updated": datetime.now().isoformat()
        }), 500

@app.route('/api/init-database')
def init_database_api():
    """Inicializar banco"""
    try:
        from backend.models.database import Base
        Base.metadata.create_all(engine)
        
        # SQLite
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
        
        return jsonify({
            "status": "success",
            "tables_created": tables,
            "database_type": "SQLite"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

# ============================================================================
# ROTAS DE FRONTEND
# ============================================================================

@app.route('/manual')
def manual():
    return send_from_directory('frontend/pages', 'manual.html')

@app.route('/herd')
def herd():
    return send_from_directory('frontend/pages', 'herd.html')

@app.route('/batch')
def batch():
    return send_from_directory('frontend/pages', 'batch.html')

@app.route('/history')
def history():
    return send_from_directory('frontend/pages', 'history.html')

@app.route('/analytics')
def analytics():
    return send_from_directory('frontend/pages', 'analytics.html')

@app.route('/import')
def import_data():
    return send_from_directory('frontend/pages', 'import.html')

# ============================================================================
# ARQUIVOS ESTÁTICOS
# ============================================================================

@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'frontend', 'css'), filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'frontend', 'js'), filename)

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'frontend', 'assets'), filename)

# ============================================================================
# EXECUTAR
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("GENEFY - SERVER STARTING")
    print("="*60)
    print(f"Banco: {'PostgreSQL' if os.environ.get('DATABASE_URL') else 'SQLite'}")
    print(f"Porta: {os.environ.get('PORT', 8003)}")
    print("="*60)

    port = int(os.environ.get('PORT', 8003))
    app.run(host='0.0.0.0', port=port, debug=False)
