document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.auth-tabs .tab');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            
            tab.classList.add('active');
            
            const targetForm = tab.dataset.form;
            
            loginForm.style.display = 'none';
            registerForm.style.display = 'none';
            
            if (targetForm === 'login') {
                loginForm.style.display = 'block';
            } else if (targetForm === 'register') {
                registerForm.style.display = 'block';
            }
        });
    });
}); 