document.addEventListener('DOMContentLoaded', function() {
    const addToCartForm = document.querySelector('.add-to-cart-form');

    if (addToCartForm) {
        addToCartForm.addEventListener('submit', async function(event) {
            event.preventDefault(); 

            const form = event.target;
            const formData = new FormData(form);
            const url = form.action; 

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    body: formData,
                    headers: {
                    }
                });

                const data = await response.json();

                // Отображаем сообщение пользователю
                const messageContainer = document.querySelector('.book-page .container');
                if (messageContainer) {
                    const alertDiv = document.createElement('div');
                    alertDiv.classList.add('alert', `alert-${data.status}`);
                    alertDiv.textContent = data.message;
                    messageContainer.prepend(alertDiv);

                    // Удаляем сообщение через несколько секунд
                    setTimeout(() => {
                        alertDiv.remove();
                    }, 3000);
                }

            } catch (error) {
                console.error('Ошибка при добавлении в корзину:', error);
                const messageContainer = document.querySelector('.book-page .container');
                if (messageContainer) {
                    const alertDiv = document.createElement('div');
                    alertDiv.classList.add('alert', 'alert-error');
                    alertDiv.textContent = 'Произошла ошибка при добавлении в корзину.';
                    messageContainer.prepend(alertDiv);
                    setTimeout(() => {
                        alertDiv.remove();
                    }, 3000);
                }
            }
        });
    }
}); 