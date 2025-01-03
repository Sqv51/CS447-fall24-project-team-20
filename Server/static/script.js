async function login(event) {
    event.preventDefault(); // Formun otomatik olarak gönderilmesini engelle

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: username, password: password }) // JSON olarak gönder
    });

    const result = await response.json();
    if (response.ok) {
        alert(result.message);
        window.location.href = '/main_page'; // Başarılı girişte yönlendirme
    } else {
        alert(result.error + " başarısız giriş denemesi");
        window.location.href = '/'; // Başarısız girişte yönlendirme
    }
}

async function register(event){
    event.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email: email, password: password})
    });

    const result = await response.json();
    if(response.ok) {
        alert(result.message);
        window.location.href = '/';
    } else {
        alert(result.error);
        window.location.href = '/register.html';
    }
}