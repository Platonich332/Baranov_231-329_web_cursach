document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 3000);
    });
});

function confirmAction(message) {
    return confirm(message);
}

document.addEventListener('DOMContentLoaded', function() {
    const confirmForms = document.querySelectorAll('form[data-confirm]');
    confirmForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirmAction(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

    const ratingInputs = document.querySelectorAll('.rating-input');
    ratingInputs.forEach(container => {
        const labels = container.querySelectorAll('label');
        const inputs = container.querySelectorAll('input');

        labels.forEach((label, index) => {
            label.addEventListener('mouseover', () => {
                for (let i = 0; i <= index; i++) {
                    labels[i].style.color = '#ffc107';
                }
            });

            label.addEventListener('mouseout', () => {
                const checkedInput = container.querySelector('input:checked');
                if (checkedInput) {
                    const checkedIndex = Array.from(inputs).indexOf(checkedInput);
                    labels.forEach((l, i) => {
                        l.style.color = i <= checkedIndex ? '#ffc107' : '#ddd';
                    });
                } else {
                    labels.forEach(l => l.style.color = '#ddd');
                }
            });
        });

        inputs.forEach((input, index) => {
            input.addEventListener('change', () => {
                labels.forEach((l, i) => {
                    l.style.color = i <= index ? '#ffc107' : '#ddd';
                });
            });
        });
    });

    const searchInput = document.querySelector('.search-bar input');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                const query = this.value.trim();
                if (query.length >= 2) {
                    window.location.href = `/catalog?search=${encodeURIComponent(query)}`;
                }
            }, 500);
        });
    }

    const filterForm = document.querySelector('.filters-form');
    if (filterForm) {
        const inputs = filterForm.querySelectorAll('input, select');
        inputs.forEach(input => {
            input.addEventListener('change', () => {
                filterForm.submit();
            });
        });
    }

    const addToCartForms = document.querySelectorAll('.add-to-cart-form');
    addToCartForms.forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            try {
                const response = await fetch(this.action, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        book_id: this.dataset.bookId
                    })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    const cartCount = document.querySelector('.cart-count');
                    if (cartCount) {
                        cartCount.textContent = data.cart_count;
                    }
                    showMessage('Книга добавлена в корзину', 'success');
                } else {
                    throw new Error('Ошибка при добавлении в корзину');
                }
            } catch (error) {
                showMessage('Произошла ошибка при добавлении в корзину', 'error');
            }
        });
    });
});

function showMessage(message, type = 'info') {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    
    document.body.appendChild(alert);
    
    setTimeout(() => {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
    }, 3000);
}

async function updateOrderStatus(orderId, status) {
    if (!confirmAction('Вы уверены, что хотите изменить статус заказа?')) {
        return;
    }

    try {
        const response = await fetch(`/order/${orderId}/status`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ status })
        });

        if (response.ok) {
            window.location.reload();
        } else {
            throw new Error('Ошибка при обновлении статуса');
        }
    } catch (error) {
        showMessage('Произошла ошибка при обновлении статуса заказа', 'error');
    }
} 