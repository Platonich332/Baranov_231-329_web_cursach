document.addEventListener('DOMContentLoaded', () => {
    const sidebarLinks = document.querySelectorAll('.profile-nav a');
    const sections = document.querySelectorAll('.profile-main section');
    const highlightActiveLink = () => {
        const currentPosition = window.scrollY + 100;

        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.offsetHeight;
            const sectionId = section.getAttribute('id');
            
            if (currentPosition >= sectionTop && currentPosition < sectionTop + sectionHeight) {
                sidebarLinks.forEach(link => {
                    link.classList.remove('active');
                    if (link.getAttribute('href') === `#${sectionId}`) {
                        link.classList.add('active');
                    }
                });
            }
        });
    };
    sidebarLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault(); 
            
            const targetId = link.getAttribute('href').substring(1); 
            const targetSection = document.getElementById(targetId);
            
            if (targetSection) {
                window.scrollTo({
                    top: targetSection.offsetTop - 80, // Вычитаем высоту шапки для отступа
                    behavior: 'smooth'
                });

                 sidebarLinks.forEach(item => item.classList.remove('active'));
                 link.classList.add('active');
            }
        });
    });

    window.addEventListener('scroll', highlightActiveLink);

    highlightActiveLink();
}); 