async function logout(event) {
    if (event) event.preventDefault();

    try {
        const response = await fetch('/api/auth/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            // Redirect to React Landing Page
            window.location.href = 'http://localhost:5173/';
        } else {
            console.error('Logout failed');
            // Force redirect anyway
            window.location.href = 'http://localhost:5173/';
        }
    } catch (error) {
        console.error('Error during logout:', error);
        window.location.href = 'http://localhost:5173/';
    }
}
