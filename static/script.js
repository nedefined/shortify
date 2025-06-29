document.addEventListener('DOMContentLoaded', () => {
    const longLinkInput = document.getElementById('longLink');
    const shortifyButton = document.getElementById('shortifyButton');
    const resultBlock = document.getElementById('result');
    const shortLinkDisplay = document.getElementById('shortLink');
    const copyButton = document.getElementById('copy');
    const errorDisplay = document.getElementById('error');

    shortifyButton.addEventListener('click', async () => {
        const longUrl = longLinkInput.value.trim();

        errorDisplay.style.display = 'none';
        errorDisplay.textContent = '';
        resultBlock.style.display = 'none';

        if (!longUrl) {
            errorDisplay.textContent = "Пожалуйста, введите URL.";
            errorDisplay.style.display = 'block';
            return;
        }

        try {
            const response = await fetch('/shorten', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url: longUrl })
            });

            const data = await response.json();

            if (response.ok) {
                shortLinkDisplay.textContent = data.short_link;
                resultBlock.style.display = 'block';
                longLinkInput.value = '';
            } else {
                errorDisplay.textContent = data.error || "Произошла неизвестная ошибка при сокращении ссылки";
                errorDisplay.style.display = 'block';
            }
        } catch (error) {
            console.error(error);
            errorDisplay.textContent = "Сервер не отвечает";
            errorDisplay.style.display = 'block';
        }
    });

    copyButton.addEventListener('click', () => {
        const shortLink = shortLinkDisplay.textContent;
        navigator.clipboard.writeText(shortLink).then(() => {
            copyButton.textContent = 'Скопировано!';
            setTimeout(() => {
                copyButton.textContent = 'Копировать';
            }, 1500);
        }).catch(err => {
            console.error(err);
            alert('Не удалось скопировать ссылку');
        });
    });
});