document.addEventListener('DOMContentLoaded', () => {
    const elements = {
        longLinkInput: document.getElementById('longLink'),
        shortifyButton: document.getElementById('shortifyButton'),
        resultBlock: document.getElementById('result'),
        shortLinkDisplay: document.getElementById('shortLink'),
        copyButton: document.getElementById('copy'),
        errorDisplay: document.getElementById('error')
    };

    const urlRegex = /^(?:http|ftp)s?:\/\/(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|localhost|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?(?:\/?|[\/?]\S+)$/i;

    function isValidUrl(url) {
        return urlRegex.test(url.trim());
    }

    function showError(message) {
        elements.errorDisplay.textContent = message;
        elements.errorDisplay.style.display = 'block';
        elements.resultBlock.style.display = 'none';
    }

    function showResult(shortLink) {
        elements.shortLinkDisplay.textContent = shortLink;
        elements.resultBlock.style.display = 'block';
        elements.errorDisplay.style.display = 'none';
        elements.longLinkInput.value = '';
    }

    function setLoadingState(isLoading) {
        elements.shortifyButton.disabled = isLoading;
        elements.shortifyButton.textContent = isLoading ? 'Загрузка...' : 'Сократить';
    }

    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    const handleShorten = debounce(async () => {
        const longUrl = elements.longLinkInput.value.trim();

        elements.errorDisplay.style.display = 'none';
        elements.resultBlock.style.display = 'none';

        if (!longUrl) {
            showError('Пожалуйста, введите URL.');
            return;
        }

        if (!isValidUrl(longUrl)) {
            showError('Пожалуйста, введите корректный URL, начинающийся с http:// или https://.');
            return;
        }

        setLoadingState(true);

        try {
            const response = await fetch('/shorten', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ url: longUrl })
            });

            const data = await response.json();

            if (response.ok) {
                showResult(data.short_link);
            } else {
                showError(data.error || 'Произошла ошибка при сокращении ссылки.');
            }
        } catch (error) {
            console.error('Ошибка запроса:', error);
            showError('Не удалось подключиться к серверу. Попробуйте позже.');
        } finally {
            setLoadingState(false);
        }
    }, 300);

    const handleCopy = async () => {
        const shortLink = elements.shortLinkDisplay.textContent;
        try {
            await navigator.clipboard.writeText(shortLink);
            elements.copyButton.textContent = 'Скопировано!';
            setTimeout(() => {
                elements.copyButton.textContent = 'Копировать';
            }, 1500);
        } catch (error) {
            console.error('Ошибка копирования:', error);
            showError('Не удалось скопировать ссылку.');
        }
    };

    elements.shortifyButton.addEventListener('click', handleShorten);
    elements.copyButton.addEventListener('click', handleCopy);

    elements.longLinkInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            handleShorten();
        }
    });
});