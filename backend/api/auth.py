# -*- coding: utf-8 -*-
"""
API de Autenticacao
Sistema de Acasalamento de Gado Leiteiro
"""

from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps

from backend.models.database import get_session, User

# Criar blueprint
auth_api = Blueprint('auth', __name__, url_prefix='/api/auth')


def get_db():
    """Helper para pegar sess�o do banco"""
    from app import engine
    return get_session(engine)


def login_required(f):
    """Decorator para proteger rotas que requerem autentica��o"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Autentica��o necess�ria'}), 401
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# ROTAS DE AUTENTICA��O
# ============================================================================

@auth_api.route('/register', methods=['POST'])
def register():
    """
    POST /api/auth/register
    Registra um novo usu�rio

    Body:
        - name: nome do usu�rio
        - email: email do usu�rio
        - password: senha do usu�rio
    """
    try:
        data = request.get_json()

        # Validar dados
        if not data or not data.get('name') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Nome, email e senha s�o obrigat�rios'}), 400

        name = data['name'].strip()
        email = data['email'].strip().lower()
        password = data['password']

        # Validar email
        if '@' not in email or '.' not in email:
            return jsonify({'error': 'Email inv�lido'}), 400

        # Validar senha (m�nimo 6 caracteres)
        if len(password) < 6:
            return jsonify({'error': 'Senha deve ter no m�nimo 6 caracteres'}), 400

        db = get_db()

        # Verificar se email j� existe
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            db.close()
            return jsonify({'error': 'Email j� cadastrado'}), 400

        # Criar hash da senha
        password_hash = generate_password_hash(password)

        # Criar usu�rio
        new_user = User(
            name=name,
            email=email,
            password_hash=password_hash,
            created_at=datetime.now(),
            is_active=True
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        user_dict = new_user.to_dict()
        db.close()

        return jsonify({
            'message': 'Usu�rio registrado com sucesso',
            'user': user_dict
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_api.route('/login', methods=['POST'])
def login():
    """
    POST /api/auth/login
    Faz login do usu�rio

    Body:
        - email: email do usu�rio
        - password: senha do usu�rio
    """
    try:
        data = request.get_json()

        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email e senha s�o obrigat�rios'}), 400

        email = data['email'].strip().lower()
        password = data['password']

        db = get_db()

        # Buscar usu�rio
        user = db.query(User).filter(User.email == email).first()

        if not user:
            db.close()
            return jsonify({'error': 'Email ou senha incorretos'}), 401

        # Verificar senha
        if not check_password_hash(user.password_hash, password):
            db.close()
            return jsonify({'error': 'Email ou senha incorretos'}), 401

        # Verificar se usu�rio est� ativo
        if not user.is_active:
            db.close()
            return jsonify({'error': 'Usu�rio desativado'}), 401

        # Atualizar �ltimo login
        user.last_login = datetime.now()
        db.commit()

        # Criar sess�o
        session['user_id'] = user.id
        session['user_name'] = user.name
        session['user_email'] = user.email

        user_dict = user.to_dict()
        db.close()

        return jsonify({
            'message': 'Login realizado com sucesso',
            'user': user_dict
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_api.route('/logout', methods=['POST'])
def logout():
    """
    POST /api/auth/logout
    Faz logout do usu�rio
    """
    try:
        session.clear()
        return jsonify({'message': 'Logout realizado com sucesso'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_api.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """
    GET /api/auth/me
    Retorna dados do usu�rio logado
    """
    try:
        user_id = session.get('user_id')

        db = get_db()
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            db.close()
            return jsonify({'error': 'Usu�rio n�o encontrado'}), 404

        user_dict = user.to_dict()
        db.close()

        return jsonify({'user': user_dict}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_api.route('/check', methods=['GET'])
def check_auth():
    """
    GET /api/auth/check
    Verifica se usu�rio est� autenticado
    """
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': session.get('user_id'),
                'name': session.get('user_name'),
                'email': session.get('user_email')
            }
        }), 200
    else:
        return jsonify({'authenticated': False}), 200
