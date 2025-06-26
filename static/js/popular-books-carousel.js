document.addEventListener('DOMContentLoaded', function() {
    const bookList = document.querySelector('.popular-books .book-list');
    const prevBtn = document.querySelector('.popular-books .prev-btn');
    const nextBtn = document.querySelector('.popular-books .next-btn');

    if (bookList && prevBtn && nextBtn) {
        const bookCard = bookList.querySelector('.book-card');
        let scrollAmount = 0;

        if (bookCard) {
            const cardWidth = bookCard.offsetWidth;
            const gap = parseInt(getComputedStyle(bookList).gap) || 20; // Get gap or assume 20px
            scrollAmount = cardWidth + gap;
        } else {
            scrollAmount = 200;
        }

        nextBtn.addEventListener('click', () => {
            bookList.scrollBy({ 
                left: scrollAmount, 
                behavior: 'smooth' 
            });
        });

        prevBtn.addEventListener('click', () => {
            bookList.scrollBy({ 
                left: -scrollAmount, 
                behavior: 'smooth' 
            });
        });
    }
}); 