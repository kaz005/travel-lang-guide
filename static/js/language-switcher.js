document.addEventListener('DOMContentLoaded', () => {
    const buttons = document.querySelectorAll('.flag-icon');
    
    buttons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const newLang = button.getAttribute('data-lang');
            if (newLang === window.TRAVEL_GUIDE.currentLang) {
                return; // 同じ言語の場合は何もしない
            }
            
            // URLを更新して遷移
            const url = new URL(window.location.href);
            url.searchParams.set('lang', newLang);
            window.location.href = url.toString();
        });
    });
});