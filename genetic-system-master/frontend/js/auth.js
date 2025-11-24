/**
 * Auth Functions
 * Funções de autenticação compartilhadas
 */

async function logout(e) {
    e.preventDefault();

    if (!confirm('Deseja sair do sistema?')) {
        return;
    }

    try {
        const response = await fetch('/api/auth/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            window.location.href = '/';
        } else {
            alert('Erro ao fazer logout');
        }
    } catch (error) {
        console.error('Erro ao fazer logout:', error);
        alert('Erro ao conectar com o servidor');
    }
}

// Verificar autenticação ao carregar página
async function checkAuth() {
    try {
        const response = await fetch('/api/auth/check');
        const data = await response.json();

        if (!data.authenticated) {
            // Redirecionar para landing page se não estiver autenticado
            window.location.href = '/';
        }
    } catch (error) {
        console.error('Erro ao verificar autenticação:', error);
    }
}
