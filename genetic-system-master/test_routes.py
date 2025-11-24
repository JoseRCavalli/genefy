"""Teste rápido de rotas"""
from app import app

with app.test_client() as client:
    # Testar /api/health
    response = client.get('/api/health')
    print(f"GET /api/health: {response.status_code}")

    # Testar /api/females
    response = client.get('/api/females')
    print(f"GET /api/females: {response.status_code}")
    if response.status_code != 200:
        print(f"  Erro: {response.data[:200]}")

    # Listar todas as rotas
    print("\nRotas registradas no app:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.rule} -> {rule.endpoint}")
