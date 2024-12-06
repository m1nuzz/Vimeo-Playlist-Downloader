// Когда приходит сообщение из popup.js
chrome.runtime.onMessage.addListener(
    function (data, sender, sendResponse) {
        //сообщение из popup.js
        parseMessage(data)

        // Если нужно отправить ответ в popup.js
        sendResponse({"data": "Content принял"});
    }
);

// Обрабатываем входящии сообщение
function parseMessage(data) {
    console.log(data);
    if (data.data.type) {
        var messageData = data.data;
        console.log(messageData.type);
        // Меняем фон
        if (messageData.type == 'color') {
            var color = messageData.color;
            document.body.style.background = color;
        }
    }
}

// Отправить сообщение в popup.js
function sendPopup(data) {
    chrome.runtime.sendMessage({"data": data}, function (response) {
        console.log(response);
    });
}

// Слушаем сообщения от background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'getPageInfo') {
        const videoTitle = document.querySelector('.education-name')?.textContent?.trim() || 'untitled_video';
        const pageHtml = document.documentElement.outerHTML;
        
        sendResponse({
            title: videoTitle,
            html: pageHtml
        });
    }
});

// Функция для поиска ссылок playlist.json
function findPlaylistLinks() {
    const links = performance.getEntriesByType('resource')
        .filter(entry => entry.name.includes('playlist.json'))
        .map(entry => entry.name);

    if (links.length > 0) {
        // Отправляем ссылку и информацию о странице
        chrome.runtime.sendMessage({
            action: 'addLink',
            url: links[0],
            title: document.querySelector('.education-name')?.textContent?.trim() || 'untitled_video',
            html: document.documentElement.outerHTML
        });
    }
}

// Наблюдаем за загрузкой ресурсов
const observer = new PerformanceObserver((list) => {
    list.getEntries().forEach(entry => {
        if (entry.name.includes('playlist.json')) {
            findPlaylistLinks();
        }
    });
});

observer.observe({ entryTypes: ['resource'] });

// Также проверяем существующие ресурсы
findPlaylistLinks();

// Функция для перехвата XMLHttpRequest
(function(xhr) {
    const XHR = XMLHttpRequest.prototype;
    
    // Сохраняем оригинальные методы
    const open = XHR.open;
    const send = XHR.send;
    
    // Переопределяем open
    XHR.open = function(method, url) {
        this._url = url;
        return open.apply(this, arguments);
    };
    
    // Переопределяем send
    XHR.send = function(data) {
        // Добавляем обработчик для отслеживания ответа
        this.addEventListener('load', function() {
            if (this._url && this._url.includes('playlist.json')) {
                console.log('XHR intercepted:', this._url);
                checkUrl(this._url);
            }
        });
        return send.apply(this, arguments);
    };
})(XMLHttpRequest);

// Функция для перехвата Fetch
(function(fetch) {
    window.fetch = async function(url, options) {
        const response = await fetch.apply(this, arguments);
        
        // Создаем копию response, так как оригинал может быть прочитан только один раз
        response.clone().text().then(text => {
            if (response.url && response.url.includes('playlist.json')) {
                console.log('Fetch intercepted:', response.url);
                checkUrl(response.url);
            }
        });
        
        return response;
    };
})(window.fetch);

// Создаем перехватчик запросов через Performance API
const observer2 = new PerformanceObserver((list) => {
    list.getEntries().forEach(entry => {
        if (entry.name && entry.name.includes('playlist.json')) {
            console.log('Performance entry:', entry.name);
            checkUrl(entry.name);
        }
    });
});

observer2.observe({ entryTypes: ['resource'] });

// Функция проверки URL и отправки в background script
function checkUrl(url) {
    try {
        if (url.includes('playlist.json') && 
            url.includes('exp=') && 
            url.includes('hmac=')) {
            console.log('Valid URL found:', url);
            chrome.runtime.sendMessage({
                action: 'foundUrl',
                url: url
            });
            // Получаем информацию о видео
            getVideoInfo(url);
        }
    } catch (e) {
        console.error('Error processing URL:', e);
    }
}

// Функция для получения названия видео
function getVideoTitle() {
    const titleElement = document.evaluate(
        "//div[@class='education-name']",
        document,
        null,
        XPathResult.FIRST_ORDERED_NODE_TYPE,
        null
    ).singleNodeValue;

    if (titleElement) {
        return titleElement.textContent.trim();
    }
    
    // Запасной вариант - пробуем получить заголовок из других мест
    const h1Title = document.querySelector('h1');
    if (h1Title) {
        return h1Title.textContent.trim();
    }
    
    return 'untitled_video';
}

// Функция для получения HTML страницы
function getPageHTML() {
    return document.documentElement.outerHTML;
}

// Функция для получения названия видео и HTML страницы
function getVideoInfo(url) {
    // Получаем название видео
    let title = getVideoTitle();
    // Получаем HTML страницы
    const html = getPageHTML();

    // Отправляем данные в background script
    chrome.runtime.sendMessage({
        action: 'videoInfo',
        url: url,
        title: title,
        html: html
    });
}

// Функция для проверки всех сетевых запросов на странице
function checkExistingRequests() {
    if (window.performance && window.performance.getEntries) {
        window.performance.getEntries().forEach(entry => {
            if (entry.name && entry.name.includes('playlist.json')) {
                checkUrl(entry.name);
            }
        });
    }
}

// Запускаем проверку при загрузке страницы
window.addEventListener('load', checkExistingRequests);

// Добавляем MutationObserver для отслеживания динамически добавляемых элементов
const mutationObserver = new MutationObserver((mutations) => {
    mutations.forEach(mutation => {
        mutation.addedNodes.forEach(node => {
            if (node.nodeName === 'VIDEO' || node.nodeName === 'IFRAME') {
                console.log('Video/iframe element added, checking requests...');
                checkExistingRequests();
            }
        });
    });
});

mutationObserver.observe(document.documentElement, {
    childList: true,
    subtree: true
});

// При клике на любой div передаем его html в popup
var ElemArr = document.querySelectorAll('div');
if (ElemArr.length) {
    ElemArr.forEach(function (Elem) {
        Elem.onclick = function onClick(event) {
            //event.preventDefault();
            $this = event.target;

            sendPopup({"type": 'html', 'html': $this.innerHTML});

            //chrome.runtime.sendMessage({color: color});

            //return false;
        };
    });
}

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
