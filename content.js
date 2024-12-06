// Функция для автоматического запуска видео
function autoPlayVideo() {
    // Находим кнопку воспроизведения
    const playButton = document.querySelector("button[class='plyr__control plyr__control--overlaid']");
    
    if (playButton) {
        // Имитируем клик по кнопке
        playButton.click();
        console.log('Video autoplay triggered');
    }
}

// Функция для периодической проверки наличия кнопки воспроизведения
function checkForPlayButton() {
    const maxAttempts = 10;
    let attempts = 0;
    
    const checkInterval = setInterval(() => {
        if (attempts >= maxAttempts) {
            clearInterval(checkInterval);
            console.log('Max attempts reached, stopping check');
            return;
        }
        
        const playButton = document.querySelector("button[class='plyr__control plyr__control--overlaid']");
        if (playButton) {
            clearInterval(checkInterval);
            autoPlayVideo();
        }
        
        attempts++;
    }, 1000); // Проверяем каждую секунду
}

// Запускаем проверку при загрузке страницы
document.addEventListener('DOMContentLoaded', checkForPlayButton);

// Запускаем проверку при изменении URL (для SPA)
let lastUrl = location.href;
new MutationObserver(() => {
    const url = location.href;
    if (url !== lastUrl) {
        lastUrl = url;
        checkForPlayButton();
    }
}).observe(document, { subtree: true, childList: true });
