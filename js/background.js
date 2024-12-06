const SERVER_URL = 'http://127.0.0.1:5000';
let foundLinks = new Set();
let videoData = new Map();
let links = new Set();
let currentTitle = '';
let currentHTML = '';

// Проверяем доступность сервера
async function checkServer() {
    try {
        const response = await fetch(`${SERVER_URL}/ping`);
        return response.ok;
    } catch (error) {
        console.error('Server check failed:', error);
        return false;
    }
}

// Обновление значка расширения
function updateBadge() {
    chrome.action.setBadgeText({
        text: videoData.size.toString()
    });
}

// Функция для добавления информации о видео
function addVideoData(url, title, html) {
    if (url && url.includes('playlist.json')) {
        videoData.set(url, { url, title, html });
        updateBadge();
        return true;
    }
    return false;
}

// Функция для сохранения данных
async function saveData() {
    try {
        if (videoData.size === 0) {
            console.error('No videos to save');
            return { success: false, error: 'No videos to save' };
        }

        // Проверяем доступность сервера
        const serverAvailable = await checkServer();
        if (!serverAvailable) {
            return { success: false, error: 'Server is not available' };
        }

        // Создаем массив данных для отправки
        const videosToSave = Array.from(videoData.values()).map(data => ({
            url: data.url,
            title: data.title,
            html: data.html
        }));

        // Отправляем данные на сервер
        const response = await fetch(`${SERVER_URL}/download`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ videos: videosToSave })
        });

        const result = await response.json();

        if (!response.ok) {
            return { success: false, error: result.error || 'Failed to save data' };
        }

        // Очищаем данные после успешного сохранения
        videoData.clear();
        updateBadge();
        
        return { success: true, message: 'Videos saved successfully' };
    } catch (error) {
        console.error('Error saving data:', error);
        return { success: false, error: error.message };
    }
}

// Слушаем сообщения от content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    try {
        if (message.action === 'addLink') {
            const result = addVideoData(message.url, message.title, message.html);
            sendResponse({ success: result });
        }
        else if (message.action === 'saveAll') {
            saveData().then(result => {
                sendResponse(result);
            }).catch(error => {
                sendResponse({ success: false, error: error.message });
            });
            return true; // Важно для асинхронного ответа
        }
        else if (message.action === 'clearAll') {
            videoData.clear();
            updateBadge();
            sendResponse({ success: true });
        }
        else if (message.action === 'videoInfo') {
            const { url, title, html } = message;
            videoData.set(url, { title, html });
            currentTitle = title;
            currentHTML = html;
        }
        else if (message.action === 'saveData') {
            saveData().then(result => {
                sendResponse(result);
            }).catch(error => {
                sendResponse({ success: false, error: error.message });
            });
            return true; // Важно для асинхронного ответа
        }
    } catch (error) {
        console.error('Error processing message:', error);
        sendResponse({ success: false, error: error.message });
    }
    return true; // Предотвращаем закрытие порта сообщений
});

// Слушаем сетевые запросы
chrome.webRequest.onBeforeRequest.addListener(
    function(details) {
        if (details.url.includes('playlist.json')) {
            const fullUrl = details.url;
            const hasExp = fullUrl.includes('exp=');
            const hasHmac = fullUrl.includes('hmac=');
            
            if (hasExp && hasHmac && !foundLinks.has(details.url)) {
                foundLinks.add(details.url);
                links.add(details.url);
                chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
                    if (tabs[0]) {
                        chrome.tabs.sendMessage(tabs[0].id, {
                            action: 'getVideoInfo',
                            url: details.url
                        }).catch(error => {
                            console.error('Error sending message to tab:', error);
                        });
                    }
                });
                updateBadge();
            }
        }
        return { cancel: false };
    },
    { urls: ["<all_urls>"] }
);

// Слушаем сетевые запросы
chrome.webRequest.onBeforeRequest.addListener(
    function(details) {
        if (details.url.includes('playlist.json')) {
            // При обнаружении playlist.json запрашиваем информацию со страницы
            chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
                if (tabs[0]) {
                    chrome.tabs.sendMessage(tabs[0].id, {action: 'getPageInfo'}, function(response) {
                        if (response) {
                            addVideoData(details.url, response.title, response.html);
                        }
                    });
                }
            });
        }
    },
    { urls: ["<all_urls>"] }
);