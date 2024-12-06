// Когда приходит сообщение из content.js
chrome.runtime.onMessage.addListener(function (data, sender, sendResponse) {
    //сообщение из content.js
    parseMessage(data)

    // Если нужно отправить ответ в popup.js
    sendResponse({"data": "Popup принял"});
});

// Обрабатываем входящии сообщение
function parseMessage(data) {
    console.log(data);
    if (data.data.type) {
        var messageData = data.data;
        console.log(messageData.type);
        // Меняем фон
        if (messageData.type == 'html') {
            var html = messageData.html;
            document.getElementById('popupContent').innerHTML = html;
        }
    }
}

// Отправляю сообщение в content.js в открытую вкладку
function sendContent(data) {
    chrome.tabs.query({currentWindow: true, active: true}, function (tabs) {
        var activeTab = tabs[0];
        //chrome.tabs.sendMessage(activeTab.id, {"message": message});
        // Если нужен ответ
        chrome.tabs.sendMessage(activeTab.id, {"data": data}, function (response) {
            console.log(response);
        });
    });
}

// При клике на цвет, передаем цвет в content.js
window.addEventListener('DOMContentLoaded', function (evt) {
    var setColorArr = document.querySelectorAll('.setColor');
    if (setColorArr.length) {
        setColorArr.forEach(function (setColor) {
            setColor.onclick = function onClick(event) {
                //event.preventDefault();
                $this = event.target;

                var color = $this.getAttribute('data-color');
                sendContent({"type": 'color', 'color': color});

                //chrome.runtime.sendMessage({color: color});

                return false;
            };
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const saveButton = document.getElementById('saveButton');
    const clearButton = document.getElementById('clearButton');
    const statusText = document.getElementById('status');

    function updateStatus(message, isError = false) {
        statusText.textContent = message;
        statusText.style.color = isError ? 'red' : 'green';
    }

    saveButton.addEventListener('click', function() {
        updateStatus('Saving videos...');
        chrome.runtime.sendMessage({ action: 'saveAll' }, function(response) {
            if (response.success) {
                updateStatus('Videos saved successfully!');
            } else {
                updateStatus(response.error || 'Failed to save videos', true);
            }
        });
    });

    clearButton.addEventListener('click', function() {
        chrome.runtime.sendMessage({ action: 'clearAll' }, function(response) {
            if (response.success) {
                updateStatus('All links cleared');
            } else {
                updateStatus('Failed to clear links', true);
            }
        });
    });
});