// Subscriptions Management JavaScript

// Load all subscriptions - обновленная версия использует SubscriptionManager
async function loadSubscriptions() {
    if (window.subscriptionManager) {
        return await window.subscriptionManager.loadSubscriptions();
    } else {
        // Fallback для совместимости
        try {
            const response = await fetch('/api/subscriptions');
            const subscriptions = await response.json();

            displaySubscriptions(subscriptions);
            return subscriptions;
        } catch (error) {
            console.error('Error loading subscriptions:', error);
        }
    }
}

// Display subscriptions in UI
function displaySubscriptions(subscriptions) {
    const container = document.getElementById('subscriptionsList');
    if (!container) return;

    if (subscriptions.length === 0) {
        container.innerHTML = `
            <div class="feature-card p-8 border-glow-purple text-center max-w-2xl mx-auto">
                <iconify-icon icon="lucide:inbox" class="text-6xl mb-6 glow-purple" style="color: var(--neon-purple);"></iconify-icon>
                <h2 class="font-display text-3xl font-black uppercase tracking-tighter mb-4" style="color: var(--text-primary);">
                    Подписок пока нет
                </h2>
                <p class="text-lg font-bold mb-6" style="color: var(--text-muted);">
                    Используйте кнопки импорта выше или добавьте подписки вручную
                </p>
                <div class="flex justify-center">
                    <button class="px-8 py-4 border-2 font-bold uppercase tracking-wider transition-all hover:bg-pink-600 hover:text-white" style="border-color: #FF006E; color: #FF006E;">
                        <iconify-icon icon="lucide:plus" class="inline-block mr-2"></iconify-icon>
                        Добавить вручную
                    </button>
                </div>
            </div>
        `;
        container.style.display = 'block';
        return;
    }

    container.style.display = 'block';
    container.innerHTML = `
        <div class="mb-6">
            <h2 class="font-display text-4xl font-black uppercase tracking-tighter mb-2" style="color: var(--text-primary);">Ваши Подписки</h2>
            <div class="h-1 w-32" style="background-color: var(--neon-purple);"></div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            ${subscriptions.map(sub => `
                <div class="subscription-card" data-id="${sub.id}">
                    <div class="flex justify-between items-start mb-4">
                        <h3>${sub.name}</h3>
                        <span class="text-sm font-black uppercase px-2 py-1" style="background-color: var(--neon-purple); color: white;">${sub.category}</span>
                    </div>
                    <p class="mb-2"><strong>Стоимость:</strong> ${sub.cost} ${sub.currency}</p>
                    <p class="mb-2"><strong>Период:</strong> ${translatePeriod(sub.billing_period)}</p>
                    <p class="mb-4"><strong>Следующее списание:</strong> ${formatDate(sub.next_billing_date)}</p>
                    <div class="actions flex flex-wrap gap-2">
                        ${sub.payment_url ? `<a href="${sub.payment_url}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center px-4 py-2 border-2 font-bold uppercase text-sm transition-all hover:bg-green-600 hover:text-white hover:border-green-600" style="border-color: #10B981; color: #10B981; text-decoration: none; box-shadow: 0 0 10px rgba(16, 185, 129, 0.2);"><iconify-icon icon="lucide:credit-card" class="mr-2 text-base"></iconify-icon>Оплатить</a>` : ''}
                        <button onclick="editSubscription('${sub.id}')" class="px-4 py-2 border-2 font-bold uppercase text-sm transition-all" style="border-color: var(--neon-purple); color: var(--neon-purple);">Редактировать</button>
                        <button onclick="deleteSubscription('${sub.id}')" class="px-4 py-2 border-2 font-bold uppercase text-sm transition-all hover:bg-red-600 hover:text-white" style="border-color: #FF006E; color: #FF006E;">Удалить</button>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

// Delete subscription
async function deleteSubscription(id) {
    if (!confirm('Вы уверены, что хотите удалить эту подписку?')) {
        return;
    }

    try {
        const response = await fetch(`/api/subscriptions/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            await loadSubscriptions();
        } else {
            alert('Ошибка при удалении подписки');
        }
    } catch (error) {
        console.error('Error deleting subscription:', error);
        alert('Ошибка при удалении подписки');
    }
}

// Edit subscription
async function editSubscription(id) {
    // Получаем данные подписки
    try {
        const response = await fetch(`/api/subscriptions/${id}`);
        if (!response.ok) {
            alert('Ошибка при загрузке данных подписки');
            return;
        }

        const subscription = await response.json();

        // Открываем форму и заполняем её данными
        if (window.manualSubscriptionForm) {
            window.manualSubscriptionForm.showForm();
            window.manualSubscriptionForm.fillForm(subscription);
        }
    } catch (error) {
        console.error('Error loading subscription:', error);
        alert('Ошибка при загрузке данных подписки');
    }
}

// Import from Gmail
async function importFromGmail() {
    // Redirect to Google OAuth
    window.location.href = '/auth/google';
}

// Import from Yandex or Mail.ru - Modal functions
let currentProvider = null;

function openEmailImportModal(provider) {
    currentProvider = provider;
    const modal = document.getElementById('emailImportModal');
    const modalTitle = document.getElementById('emailModalTitle');
    const modalIcon = document.getElementById('emailModalIcon');
    const yandexOauthSection = document.getElementById('yandexOauthSection');
    const emailImportForm = document.getElementById('emailImportForm');
    const emailInput = document.getElementById('emailInput');
    const passwordLink = document.getElementById('passwordLink');
    const oauthBtn = document.getElementById('oauthLoginBtn');

    if (provider === 'yandex') {
        modalTitle.textContent = 'Импорт из Yandex';
        modalIcon.setAttribute('icon', 'simple-icons:yandex');

        // Show OAuth section, hide form
        if (yandexOauthSection) {
            yandexOauthSection.classList.remove('hidden');
        }
        if (emailImportForm) {
            emailImportForm.classList.add('hidden');
        }

        // Setup OAuth button click handler
        if (oauthBtn) {
            oauthBtn.onclick = () => {
                // Redirect to Yandex OAuth
                window.location.href = '/auth/yandex';
            };
        }
    } else if (provider === 'mailru') {
        modalTitle.textContent = 'Импорт из Mail.ru';
        modalIcon.setAttribute('icon', 'simple-icons:maildotru');
        emailInput.placeholder = 'user@mail.ru';
        passwordLink.href = 'https://account.mail.ru/user/2-step-auth/passwords/';

        // Hide OAuth section, show form
        if (yandexOauthSection) {
            yandexOauthSection.classList.add('hidden');
        }
        if (emailImportForm) {
            emailImportForm.classList.remove('hidden');
        }
    }

    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function closeEmailImportModal() {
    const modal = document.getElementById('emailImportModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
    document.getElementById('emailImportForm').reset();
    currentProvider = null;
}

async function importFromEmail(provider, email, password) {
    const statusEl = document.getElementById(`${provider}Status`);
    const btnEl = document.getElementById(`${provider}ImportBtn`);

    try {
        if (statusEl) statusEl.textContent = `Подключение к ${provider === 'yandex' ? 'Yandex' : 'Mail.ru'}...`;
        if (btnEl) btnEl.disabled = true;

        const testResponse = await fetch('/api/email/test-connection', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ provider, email, password })
        });

        const testData = await testResponse.json();

        if (!testResponse.ok || !testData.success) {
            if (statusEl) {
                statusEl.textContent = `✗ ${testData.error || 'Ошибка подключения'}`;
                statusEl.style.color = '#FF006E';
            }
            if (btnEl) btnEl.disabled = false;
            return;
        }

        if (statusEl) statusEl.textContent = 'Поиск подписок в письмах...';

        const importResponse = await fetch('/api/email/import', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ provider, email, password })
        });

        const data = await importResponse.json();

        if (importResponse.ok) {
            if (statusEl) {
                statusEl.textContent = `✓ Импортировано ${data.imported_count} подписок из ${provider === 'yandex' ? 'Yandex' : 'Mail.ru'}`;
                statusEl.style.color = '#00FF00';
            }
            await loadSubscriptions();
            const listEl = document.getElementById('subscriptionsList');
            if (listEl) listEl.style.display = 'block';
            closeEmailImportModal();
        } else {
            if (statusEl) {
                statusEl.textContent = `✗ ${data.error || 'Ошибка импорта'}`;
                statusEl.style.color = '#FF006E';
            }
        }
    } catch (error) {
        console.error(`Error importing from ${provider}:`, error);
        if (statusEl) {
            statusEl.textContent = `✗ Ошибка: ${error.message}`;
            statusEl.style.color = '#FF006E';
        }
    } finally {
        if (btnEl) btnEl.disabled = false;
    }
}

// Helper functions
function translatePeriod(period) {
    const translations = {
        'weekly': 'Еженедельно',
        'monthly': 'Ежемесячно',
        'quarterly': 'Ежеквартально',
        'yearly': 'Ежегодно'
    };
    return translations[period] || period;
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU');
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function () {
    // Инициализируем менеджер подписок
    window.subscriptionManager = new SubscriptionManager();

    // Инициализируем класс управления формой добавления подписок
    window.manualSubscriptionForm = new ManualSubscriptionForm();

    // Auto-load subscriptions on page load
    autoLoadSubscriptions();
    checkAuthStatus();

    // Gmail import button
    const gmailImportBtn = document.getElementById('gmailImportBtn');
    if (gmailImportBtn) {
        gmailImportBtn.addEventListener('click', importFromGmail);
    }

    // Yandex import button
    const yandexImportBtn = document.getElementById('yandexImportBtn');
    if (yandexImportBtn) {
        yandexImportBtn.addEventListener('click', () => openEmailImportModal('yandex'));
    }

    // Mail.ru import button
    const mailruImportBtn = document.getElementById('mailruImportBtn');
    if (mailruImportBtn) {
        mailruImportBtn.addEventListener('click', () => openEmailImportModal('mailru'));
    }

    // Refresh all button
    const refreshAllBtn = document.getElementById('refreshAllBtn');
    if (refreshAllBtn) {
        refreshAllBtn.addEventListener('click', refreshAllSubscriptions);
    }

    // Add subscription button - используем класс ManualSubscriptionForm
    const addSubscriptionBtn = document.getElementById('addSubscriptionBtn');
    if (addSubscriptionBtn) {
        addSubscriptionBtn.addEventListener('click', () => {
            if (window.manualSubscriptionForm) {
                window.manualSubscriptionForm.showForm();
            }
        });
    }

    // Email import form submit
    const emailImportForm = document.getElementById('emailImportForm');
    if (emailImportForm) {
        emailImportForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const email = document.getElementById('emailInput').value;
            const password = document.getElementById('passwordInput').value;
            await importFromEmail(currentProvider, email, password);
        });
    }

    // Close modal on Escape key
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            closeEmailImportModal();
            closeViewModal();
        }
    });
});

// Auto-load subscriptions on page load
async function autoLoadSubscriptions() {
    try {
        const subscriptions = await loadSubscriptions();

        // If no subscriptions found, show helpful message
        if (!subscriptions || subscriptions.length === 0) {
            const subscriptionsList = document.getElementById('subscriptionsList');
            if (subscriptionsList) {
                subscriptionsList.innerHTML = `
                    <div class="feature-card p-8 border-glow-purple text-center max-w-2xl mx-auto">
                        <iconify-icon icon="lucide:inbox" class="text-6xl mb-6 glow-purple" style="color: var(--neon-purple);"></iconify-icon>
                        <h2 class="font-display text-3xl font-black uppercase tracking-tighter mb-4" style="color: var(--text-primary);">
                            Подписок пока нет
                        </h2>
                        <p class="text-lg font-bold mb-6" style="color: var(--text-muted);">
                            Подключи почту выше или нажми "Обновить подписки" для автоматического поиска
                        </p>
                        <div class="flex justify-center">
                            <button onclick="document.getElementById('refreshAllBtn').click()" class="px-8 py-4 border-2 font-bold uppercase tracking-wider transition-all hover:bg-pink-600 hover:text-white" style="border-color: #FF006E; color: #FF006E;">
                                <iconify-icon icon="lucide:search" class="inline-block mr-2"></iconify-icon>
                                Найти подписки
                            </button>
                        </div>
                    </div>
                `;
                subscriptionsList.style.display = 'block';
            }
        }
    } catch (error) {
        console.error('Error auto-loading subscriptions:', error);
    }
}

// Global variable for email filter
let currentEmailFilter = 'all'; // 'all' or 'subscriptions'
let allEmails = [];

// Refresh all subscriptions - NOW SHOWS ALL EMAILS
async function refreshAllSubscriptions() {
    const refreshBtn = document.getElementById('refreshAllBtn');
    const subscriptionsList = document.getElementById('subscriptionsList');
    const refreshStatus = document.getElementById('refreshStatus');

    if (!refreshBtn || !subscriptionsList) return;

    try {
        refreshBtn.disabled = true;
        refreshBtn.innerHTML = '<iconify-icon icon="lucide:loader-2" class="inline-block mr-2 text-xl animate-spin"></iconify-icon>Загрузка...';

        subscriptionsList.innerHTML = `
            <div class="feature-card p-8 border-glow-purple text-center max-w-2xl mx-auto">
                <iconify-icon icon="lucide:loader-2" class="text-6xl mb-6 animate-spin" style="color: var(--neon-purple);"></iconify-icon>
                <h2 class="font-display text-3xl font-black uppercase tracking-tighter mb-4" style="color: var(--text-primary);">
                    Загружаю письма...
                </h2>
            </div>
        `;
        subscriptionsList.style.display = 'block';

        const response = await fetch('/api/subscriptions/refresh-all', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (response.ok && data.success) {
            // Store all emails
            allEmails = data.results.gmail.emails || [];

            // Display emails with filter
            displayEmailsWithFilter();

            if (refreshStatus) {
                refreshStatus.textContent = data.message;
                refreshStatus.style.color = 'var(--neon-purple)';
            }
        } else {
            subscriptionsList.innerHTML = `
                <div class="feature-card p-8 border-glow-pink text-center max-w-2xl mx-auto">
                    <iconify-icon icon="lucide:alert-circle" class="text-6xl mb-6" style="color: #FF006E;"></iconify-icon>
                    <h2 class="font-display text-3xl font-black uppercase tracking-tighter mb-4" style="color: var(--text-primary);">
                        Ошибка
                    </h2>
                    <p class="text-lg font-bold" style="color: var(--text-primary);">
                        ${data.error || 'Не удалось загрузить письма'}
                    </p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error:', error);
        subscriptionsList.innerHTML = `
            <div class="feature-card p-8 border-glow-pink text-center max-w-2xl mx-auto">
                <iconify-icon icon="lucide:alert-triangle" class="text-6xl mb-6" style="color: #FF006E;"></iconify-icon>
                <h2 class="font-display text-3xl font-black uppercase tracking-tighter mb-4" style="color: var(--text-primary);">
                    Ошибка
                </h2>
                <p class="text-lg font-bold" style="color: var(--text-primary);">
                    ${error.message}
                </p>
            </div>
        `;
    } finally {
        refreshBtn.disabled = false;
        refreshBtn.innerHTML = '<iconify-icon icon="lucide:refresh-cw" class="inline-block mr-2 text-xl"></iconify-icon>Обновить подписки';
    }
}

// Display emails with filter
function displayEmailsWithFilter() {
    const subscriptionsList = document.getElementById('subscriptionsList');
    if (!subscriptionsList) return;

    // Filter emails based on current filter
    let filteredEmails = allEmails;
    let subscriptionCount = 0;

    if (currentEmailFilter === 'subscriptions') {
        // Simple filter - check for subscription keywords
        filteredEmails = allEmails.filter(email => {
            const text = (email.subject + ' ' + email.sender).toLowerCase();
            return text.includes('подписк') || text.includes('subscription') ||
                text.includes('netflix') || text.includes('spotify') ||
                text.includes('яндекс') || text.includes('plus') ||
                text.includes('premium') || text.includes('payment') ||
                text.includes('оплата') || text.includes('invoice') ||
                text.includes('счет') || text.includes('квитанц') ||
                text.includes('receipt') || text.includes('чек');
        });
    }

    // Count potential subscriptions for the button label
    subscriptionCount = allEmails.filter(email => {
        const text = (email.subject + ' ' + email.sender).toLowerCase();
        return text.includes('подписк') || text.includes('subscription') ||
            text.includes('netflix') || text.includes('spotify') ||
            text.includes('яндекс') || text.includes('plus') ||
            text.includes('premium') || text.includes('payment') ||
            text.includes('оплата') || text.includes('invoice') ||
            text.includes('счет') || text.includes('квитанц') ||
            text.includes('receipt') || text.includes('чек');
    }).length;

    let html = `
        <div class="feature-card p-8 border-glow-purple">
            <div class="flex items-center justify-between mb-6 flex-wrap gap-3">
                <h2 class="font-display text-3xl font-black uppercase tracking-tighter" style="color: var(--text-primary);">
                    <iconify-icon icon="lucide:mail" class="inline-block mr-3 text-4xl" style="color: var(--neon-purple);"></iconify-icon>
                    Письма из Gmail
                </h2>
                <div class="flex gap-2 flex-wrap">
                    <button onclick="setEmailFilter('all')" class="px-4 py-2 border-2 font-bold uppercase text-sm transition-all ${currentEmailFilter === 'all' ? 'bg-purple-600 text-white' : ''}" style="border-color: var(--neon-purple); color: ${currentEmailFilter === 'all' ? 'white' : 'var(--neon-purple)'};">
                        Все (${allEmails.length})
                    </button>
                    <button onclick="setEmailFilter('subscriptions')" class="px-4 py-2 border-2 font-bold uppercase text-sm transition-all ${currentEmailFilter === 'subscriptions' ? 'bg-pink-600 text-white' : ''}" style="border-color: #FF006E; color: ${currentEmailFilter === 'subscriptions' ? 'white' : '#FF006E'};">
                        Подписки (${subscriptionCount})
                    </button>
                    <button onclick="backToSubscriptions()" class="flex items-center gap-2 px-4 py-2 border-2 font-bold uppercase text-sm transition-all hover:bg-gray-500 hover:text-white" style="border-color: var(--text-muted); color: var(--text-muted);">
                        <iconify-icon icon="lucide:arrow-left"></iconify-icon>Назад к подпискам
                    </button>
                </div>
            </div>
            
            <p class="text-sm font-bold mb-4" style="color: var(--text-muted);">
                Показано: <span style="color: var(--neon-purple);">${filteredEmails.length}</span>
            </p>
            
            <div class="space-y-3 max-h-[600px] overflow-y-auto">
    `;

    filteredEmails.forEach((email, i) => {
        html += `
            <div class="p-4 border-2 hover:border-purple-500 transition-all" style="border-color: var(--border-light); background-color: var(--card-bg);">
                <div class="flex items-start justify-between gap-4">
                    <div class="flex-1">
                        <p class="font-bold text-sm mb-1" style="color: var(--text-muted);">${email.sender}</p>
                        <p class="font-bold" style="color: var(--text-primary);">${email.subject}</p>
                    </div>
                    <button onclick="addEmailAsSubscription('${email.id}')" class="px-4 py-2 border-2 font-bold uppercase text-sm transition-all hover:bg-pink-600 hover:text-white whitespace-nowrap" style="border-color: #FF006E; color: #FF006E;">
                        <iconify-icon icon="lucide:plus" class="inline-block mr-1"></iconify-icon>
                        Добавить
                    </button>
                </div>
            </div>
        `;
    });

    if (filteredEmails.length === 0) {
        html += `
            <div class="p-8 text-center" style="color: var(--text-muted);">
                <iconify-icon icon="lucide:inbox" class="text-5xl mb-4"></iconify-icon>
                <p class="font-bold">Писем не найдено</p>
            </div>
        `;
    }

    html += `
            </div>
        </div>
    `;

    subscriptionsList.innerHTML = html;
}

// Set email filter
function setEmailFilter(filter) {
    currentEmailFilter = filter;
    displayEmailsWithFilter();
}

// Вернуться к списку подписок
async function backToSubscriptions() {
    allEmails = [];
    currentEmailFilter = 'all';
    if (window.subscriptionManager) {
        await window.subscriptionManager.loadSubscriptions();
    }
}

// Add email as subscription manually
async function addEmailAsSubscription(emailId) {
    // Find the email in allEmails array
    const email = allEmails.find(e => e.id === emailId);
    if (!email) {
        alert('Письмо не найдено');
        return;
    }

    // Show a simple prompt to get subscription details
    const name = prompt(`Название подписки:\n(из письма: ${email.subject})`, email.subject.substring(0, 50));
    if (!name) return;

    const costStr = prompt('Стоимость (только число, например 990):');
    if (!costStr) return;

    const cost = parseFloat(costStr);
    if (isNaN(cost) || cost <= 0) {
        alert('Неверная стоимость');
        return;
    }

    const period = prompt('Период оплаты:\n1 - Ежемесячно\n2 - Ежеквартально\n3 - Ежегодно\n4 - Еженедельно', '1');
    const periodMap = {
        '1': 'monthly',
        '2': 'quarterly',
        '3': 'yearly',
        '4': 'weekly'
    };
    const billing_period = periodMap[period] || 'monthly';

    const category = prompt('Категория:\n1 - Развлечения\n2 - Софт\n3 - Образование\n4 - Фитнес\n5 - Другое', '1');
    const categoryMap = {
        '1': 'Развлечения',
        '2': 'Софт',
        '3': 'Образование',
        '4': 'Фитнес',
        '5': 'Другое'
    };
    const categoryName = categoryMap[category] || 'Другое';

    // Create subscription
    try {
        const response = await fetch('/api/subscriptions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                cost: cost,
                currency: 'RUB',
                billing_period: billing_period,
                category: categoryName,
                notes: `Добавлено из письма: ${email.sender}`,
                start_date: new Date().toISOString().split('T')[0]
            })
        });

        if (response.ok) {
            alert('✓ Подписка добавлена!');
            // Reload subscriptions
            await loadSubscriptions();
        } else {
            const data = await response.json();
            alert(`Ошибка: ${data.error || 'Не удалось добавить подписку'}`);
        }
    } catch (error) {
        console.error('Error adding subscription:', error);
        alert(`Ошибка: ${error.message}`);
    }
}

// Test Gmail search to see what emails are found
async function testGmailSearch() {
    const testBtn = document.getElementById('testGmailBtn');
    const subscriptionsList = document.getElementById('subscriptionsList');
    const refreshStatus = document.getElementById('refreshStatus');

    if (!testBtn || !subscriptionsList) return;

    try {
        testBtn.disabled = true;
        testBtn.innerHTML = '<iconify-icon icon="lucide:loader-2" class="inline-block mr-2 text-xl animate-spin"></iconify-icon>Проверка...';

        if (refreshStatus) {
            refreshStatus.textContent = 'Ищу письма в Gmail...';
            refreshStatus.style.color = 'var(--neon-purple)';
        }

        const response = await fetch('/api/gmail/test-search');
        const data = await response.json();

        if (response.ok && data.success) {
            // Show emails in subscriptionsList
            let emailsHtml = `
                <div class="feature-card p-8 border-glow-purple">
                    <div class="flex items-center justify-between mb-6">
                        <h2 class="font-display text-3xl font-black uppercase tracking-tighter" style="color: var(--text-primary);">
                            <iconify-icon icon="lucide:mail-check" class="inline-block mr-3 text-4xl" style="color: #00FF00;"></iconify-icon>
                            Gmail подключен
                        </h2>
                        <span class="text-lg font-bold" style="color: #00FF00;">✓ Работает</span>
                    </div>
                    
                    <p class="text-lg font-bold mb-6" style="color: var(--text-primary);">
                        Найдено писем за последние 7 дней: <span style="color: var(--neon-purple);">${data.total_found}</span>
                    </p>
            `;

            if (data.emails && data.emails.length > 0) {
                emailsHtml += `
                    <div class="space-y-3">
                        <h3 class="font-bold text-lg mb-4" style="color: var(--text-primary);">Последние письма:</h3>
                `;

                data.emails.forEach((email, i) => {
                    emailsHtml += `
                        <div class="p-4 border-2" style="border-color: var(--border-light); background-color: var(--card-bg);">
                            <div class="flex items-start gap-3">
                                <span class="font-black text-lg" style="color: var(--neon-purple);">${i + 1}.</span>
                                <p class="flex-1 font-bold" style="color: var(--text-primary);">${email.subject}</p>
                            </div>
                        </div>
                    `;
                });

                emailsHtml += `</div>`;
            } else {
                emailsHtml += `
                    <div class="p-6 border-2 text-center" style="border-color: var(--neon-purple); background-color: rgba(123,47,218,0.05);">
                        <iconify-icon icon="lucide:inbox" class="text-5xl mb-4" style="color: var(--text-muted);"></iconify-icon>
                        <p class="font-bold" style="color: var(--text-muted);">Писем не найдено за последние 7 дней</p>
                        <p class="text-sm mt-2" style="color: var(--text-muted);">Отправь себе тестовое письмо с темой "Подписка Netflix 990 руб/месяц"</p>
                    </div>
                `;
            }

            emailsHtml += `</div>`;

            subscriptionsList.innerHTML = emailsHtml;
            subscriptionsList.style.display = 'block';

            if (refreshStatus) {
                refreshStatus.textContent = '✓ Тест завершен. Теперь можешь нажать "Обновить подписки"';
                refreshStatus.style.color = '#00FF00';
            }

            // Show in console too
            console.log('Gmail Test Results:', data);
        } else {
            let errorMsg = data.message || data.error || 'Неизвестная ошибка';

            let errorHtml = `
                <div class="feature-card p-8 border-glow-pink text-center max-w-2xl mx-auto">
                    <iconify-icon icon="lucide:alert-circle" class="text-6xl mb-6" style="color: #FF006E;"></iconify-icon>
                    <h2 class="font-display text-3xl font-black uppercase tracking-tighter mb-4" style="color: var(--text-primary);">
                        Ошибка подключения
                    </h2>
                    <p class="text-lg font-bold mb-6" style="color: var(--text-primary);">
                        ${errorMsg}
                    </p>
            `;

            if (!data.has_token) {
                errorHtml += `
                    <div class="p-6 border-2 mb-6" style="border-color: var(--neon-purple); background-color: rgba(123,47,218,0.05);">
                        <p class="font-bold mb-2" style="color: var(--text-primary);">👉 Что делать:</p>
                        <p class="text-sm" style="color: var(--text-muted);">Нажми кнопку "Gmail" вверху чтобы войти</p>
                    </div>
                `;
            } else if (!data.token_valid) {
                errorHtml += `
                    <div class="p-6 border-2 mb-6" style="border-color: var(--neon-purple); background-color: rgba(123,47,218,0.05);">
                        <p class="font-bold mb-2" style="color: var(--text-primary);">👉 Что делать:</p>
                        <p class="text-sm" style="color: var(--text-muted);">Токен истек. Нажми "Gmail" вверху чтобы войти заново</p>
                    </div>
                `;
            }

            errorHtml += `</div>`;

            subscriptionsList.innerHTML = errorHtml;
            subscriptionsList.style.display = 'block';

            console.error('Gmail Test Error:', data);
        }
    } catch (error) {
        console.error('Error testing Gmail:', error);

        subscriptionsList.innerHTML = `
            <div class="feature-card p-8 border-glow-pink text-center max-w-2xl mx-auto">
                <iconify-icon icon="lucide:alert-triangle" class="text-6xl mb-6" style="color: #FF006E;"></iconify-icon>
                <h2 class="font-display text-3xl font-black uppercase tracking-tighter mb-4" style="color: var(--text-primary);">
                    Ошибка
                </h2>
                <p class="text-lg font-bold mb-6" style="color: var(--text-primary);">
                    ${error.message}
                </p>
                <p class="text-sm" style="color: var(--text-muted);">Проверь консоль браузера (F12) для деталей</p>
            </div>
        `;
        subscriptionsList.style.display = 'block';
    } finally {
        testBtn.disabled = false;
        testBtn.innerHTML = '<iconify-icon icon="lucide:bug" class="inline-block mr-2 text-xl"></iconify-icon>Тест Gmail';
    }
}

// SubscriptionManager класс для управления отображением списка подписок
class SubscriptionManager {
    constructor() {
        this.container = document.getElementById('subscriptionsList');
        this.subscriptions = [];
    }

    async loadSubscriptions() {
        try {
            const response = await fetch('/api/subscriptions');
            const subscriptions = await response.json();

            this.subscriptions = subscriptions;
            this.displaySubscriptions(subscriptions);
            this.updateSubscriptionCount();

            return subscriptions;
        } catch (error) {
            console.error('Error loading subscriptions:', error);
            return [];
        }
    }

    addSubscriptionToList(subscription) {
        this.subscriptions.push(subscription);
        this.displaySubscriptions(this.subscriptions);
        this.updateSubscriptionCount();

        // Выделяем новую подписку
        setTimeout(() => {
            const newCard = document.querySelector(`[data-id="${subscription.id}"]`);
            if (newCard) {
                newCard.style.transform = 'scale(1.05)';
                newCard.style.boxShadow = '0 0 20px rgba(255, 0, 110, 0.5)';

                setTimeout(() => {
                    newCard.style.transform = '';
                    newCard.style.boxShadow = '';
                }, 2000);
            }
        }, 100);
    }

    displaySubscriptions(subscriptions) {
        if (!this.container) return;

        if (subscriptions.length === 0) {
            this.container.innerHTML = `
                <div class="feature-card p-8 border-glow-purple text-center max-w-2xl mx-auto">
                    <iconify-icon icon="lucide:inbox" class="text-6xl mb-6 glow-purple" style="color: var(--neon-purple);"></iconify-icon>
                    <h2 class="font-display text-3xl font-black uppercase tracking-tighter mb-4" style="color: var(--text-primary);">Подписок пока нет</h2>
                    <p class="text-lg font-bold mb-6" style="color: var(--text-muted);">Добавьте подписку вручную или импортируйте из почты</p>
                    <button onclick="window.manualSubscriptionForm?.showForm()" class="px-8 py-4 border-2 font-bold uppercase tracking-wider transition-all hover:bg-pink-600 hover:text-white" style="border-color: #FF006E; color: #FF006E;">
                        <iconify-icon icon="lucide:plus" class="inline-block mr-2"></iconify-icon>
                        Добавить подписку
                    </button>
                </div>
            `;
            this.container.style.display = 'block';
            return;
        }

        this.container.style.display = 'block';
        this.container.innerHTML = `
            <div class="mb-3">
                <h2 class="font-display text-2xl font-black uppercase tracking-tighter" style="color: var(--text-primary);">Ваши подписки</h2>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                ${subscriptions.map(sub => `
                    <div class="subscription-card flex flex-col p-5" data-id="${sub.id}">
                        <div class="flex justify-between items-start mb-3">
                            <h3 class="text-xl font-black" style="margin-bottom:0;">${sub.name}</h3>
                            <span class="text-xs font-black uppercase px-2 py-1 ml-2 flex-shrink-0" style="background-color: var(--neon-purple); color: white;">${sub.category}</span>
                        </div>
                        <div class="flex items-baseline gap-2 mb-3">
                            <span class="text-3xl font-black font-display" style="color: #FF006E;">${sub.cost}</span>
                            <span class="text-sm font-bold" style="color: var(--text-muted);">${sub.currency} / ${translatePeriod(sub.billing_period)}</span>
                        </div>
                        <p class="text-sm mb-4" style="color: var(--text-muted);">
                            <iconify-icon icon="lucide:calendar" class="inline mr-1"></iconify-icon>
                            Следующее списание: <span style="color: var(--text-primary); font-weight:bold;">${formatDate(sub.next_billing_date)}</span>
                        </p>
                        <div class="mt-auto flex flex-wrap gap-2">
                            ${sub.payment_url ? `
                                <a href="${sub.payment_url}" target="_blank" rel="noopener noreferrer"
                                   class="flex-1 inline-flex items-center justify-center px-4 py-2.5 border-2 font-bold uppercase text-sm transition-all hover:bg-green-600 hover:text-white hover:border-green-600"
                                   style="border-color: #10B981; color: #10B981; text-decoration: none;">
                                    <iconify-icon icon="lucide:credit-card" class="mr-1"></iconify-icon>Оплатить
                                </a>` : ''}
                            <button onclick="viewSubscription('${sub.id}')"
                                class="flex-1 px-4 py-2.5 border-2 font-bold uppercase text-sm transition-all hover:bg-purple-600 hover:text-white"
                                style="border-color: var(--neon-purple); color: var(--neon-purple);">
                                <iconify-icon icon="lucide:eye" class="mr-1"></iconify-icon>Подробнее
                            </button>
                            <button onclick="editSubscription('${sub.id}')"
                                class="px-4 py-2.5 border-2 font-bold uppercase text-sm transition-all hover:bg-purple-600 hover:text-white"
                                style="border-color: var(--neon-purple); color: var(--neon-purple);">
                                <iconify-icon icon="lucide:edit-2"></iconify-icon>
                            </button>
                            <button onclick="deleteSubscription('${sub.id}')"
                                class="px-4 py-2.5 border-2 font-bold uppercase text-sm transition-all hover:bg-red-600 hover:text-white"
                                style="border-color: #FF006E; color: #FF006E;">
                                <iconify-icon icon="lucide:trash-2"></iconify-icon>
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    updateSubscriptionCount() {
        // Обновляем счетчик в аналитике
        const countElement = document.getElementById('subscriptionCount');
        if (countElement) {
            countElement.textContent = this.subscriptions.length;
        }

        // Обновляем общие расходы
        this.updateTotalExpenses();
    }

    updateTotalExpenses() {
        // Курсы конвертации в рубли (приблизительные)
        const rates = { RUB: 1, USD: 90, EUR: 100 };
        let monthlyRub = 0;

        this.subscriptions.forEach(sub => {
            const cost = parseFloat(sub.cost) || 0;
            const rate = rates[sub.currency] || 1;
            let monthly = 0;

            switch (sub.billing_period) {
                case 'weekly':    monthly = cost * 52 / 12; break;
                case 'monthly':   monthly = cost; break;
                case 'quarterly': monthly = cost / 3; break;
                case 'yearly':    monthly = cost / 12; break;
            }

            monthlyRub += monthly * rate;
        });

        const yearlyRub = monthlyRub * 12;
        const avg = this.subscriptions.length > 0 ? monthlyRub / this.subscriptions.length : 0;

        const monthlyElement = document.getElementById('totalMonthly');
        const yearlyElement = document.getElementById('totalYearly');
        const averageElement = document.getElementById('averageMonthly');

        if (monthlyElement) monthlyElement.textContent = Math.round(monthlyRub) + ' ₽';
        if (yearlyElement) yearlyElement.textContent = Math.round(yearlyRub) + ' ₽';
        if (averageElement) averageElement.textContent = Math.round(avg) + ' ₽';
    }

    showNotification(message, type) {
        // Удаляем предыдущие уведомления
        const existingNotifications = document.querySelectorAll('.notification-toast');
        existingNotifications.forEach(n => n.remove());

        // Создаем уведомление
        const notification = document.createElement('div');
        notification.className = `notification-toast fixed top-20 right-4 z-[70] px-6 py-4 border-2 font-bold uppercase tracking-wider transition-all transform translate-x-full max-w-md`;

        if (type === 'success') {
            notification.style.borderColor = '#10B981';
            notification.style.backgroundColor = 'rgba(16, 185, 129, 0.95)';
            notification.style.color = 'white';
        } else {
            notification.style.borderColor = '#FF006E';
            notification.style.backgroundColor = 'rgba(255, 0, 110, 0.95)';
            notification.style.color = 'white';
        }

        notification.innerHTML = `
            <div class="flex items-center gap-3">
                <iconify-icon icon="${type === 'success' ? 'lucide:check-circle' : 'lucide:alert-circle'}" class="text-2xl flex-shrink-0"></iconify-icon>
                <span class="text-sm break-words">${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        // Анимация появления
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);

        // Автоматическое скрытие через 5 секунд
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 5000);
    }
}

// ManualSubscriptionForm класс для управления формой добавления подписок
class ManualSubscriptionForm {
    constructor() {
        this.modal = document.getElementById('manualSubscriptionModal');
        this.form = document.getElementById('manualSubscriptionForm');
        this.submitBtn = document.getElementById('submitSubscriptionBtn');
        this.loadingIndicator = document.getElementById('loadingIndicator');
        this.editingId = null; // ID редактируемой подписки

        this.fields = {
            name: document.getElementById('subscriptionName'),
            cost: document.getElementById('subscriptionCost'),
            currency: document.getElementById('subscriptionCurrency'),
            billing_period: document.getElementById('subscriptionPeriod'),
            start_date: document.getElementById('subscriptionStartDate'),
            category: document.getElementById('subscriptionCategory'),
            payment_url: document.getElementById('subscriptionPaymentUrl'),
            notes: document.getElementById('subscriptionNotes')
        };

        this.errorElements = {
            name: document.getElementById('nameError'),
            cost: document.getElementById('costError'),
            start_date: document.getElementById('dateError')
        };

        this.init();
    }

    init() {
        // Привязываем обработчики событий
        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        // Валидация в реальном времени
        Object.keys(this.fields).forEach(fieldName => {
            const field = this.fields[fieldName];
            if (field) {
                field.addEventListener('input', () => {
                    this.validateField(fieldName);
                    this.updateSubmitButton();
                });
                field.addEventListener('change', () => {
                    this.validateField(fieldName);
                    this.updateSubmitButton();
                });
                field.addEventListener('blur', () => {
                    this.validateField(fieldName);
                    this.updateSubmitButton();
                });
            }
        });

        // Клавиатурные события
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
    }

    showForm() {
        if (!this.modal) return;

        this.modal.classList.remove('hidden');
        this.modal.style.display = 'flex';

        // Обновляем заголовок для добавления
        const modalTitleText = document.getElementById('modalTitleText');
        const modalIcon = document.getElementById('modalIcon');
        if (modalTitleText) modalTitleText.textContent = 'Добавить подписку';
        if (modalIcon) modalIcon.setAttribute('icon', 'lucide:plus');

        // Устанавливаем фокус на первое поле
        setTimeout(() => {
            if (this.fields.name) {
                this.fields.name.focus();
            }
        }, 100);

        // Устанавливаем текущую дату как дату начала
        this.setDefaultDate();

        // Сбрасываем состояние формы
        this.resetValidation();
        this.updateSubmitButton();
    }

    hideForm() {
        if (!this.modal) return;

        this.modal.classList.add('hidden');
        this.modal.style.display = 'none';

        // Скрываем индикатор загрузки и показываем форму
        this.hideLoadingState();

        // Сбрасываем форму
        this.resetForm();
    }

    resetForm() {
        if (this.form) {
            this.form.reset();
        }
        this.editingId = null;
        this.resetValidation();
        this.updateSubmitButton();

        // Обновляем текст кнопки
        const submitBtnText = document.getElementById('submitBtnText');
        if (submitBtnText) {
            submitBtnText.textContent = 'Добавить';
        }
    }

    fillForm(subscription) {
        // Заполняем форму данными подписки
        this.editingId = subscription.id;

        // Обновляем заголовок для редактирования
        const modalTitleText = document.getElementById('modalTitleText');
        const modalIcon = document.getElementById('modalIcon');
        if (modalTitleText) modalTitleText.textContent = 'Редактировать подписку';
        if (modalIcon) modalIcon.setAttribute('icon', 'lucide:edit');

        if (this.fields.name) this.fields.name.value = subscription.name || '';
        if (this.fields.cost) this.fields.cost.value = subscription.cost || '';
        if (this.fields.currency) this.fields.currency.value = subscription.currency || 'RUB';
        if (this.fields.billing_period) this.fields.billing_period.value = subscription.billing_period || 'monthly';
        if (this.fields.start_date) this.fields.start_date.value = subscription.start_date || '';
        if (this.fields.payment_url) this.fields.payment_url.value = subscription.payment_url || '';
        if (this.fields.notes) this.fields.notes.value = subscription.notes || '';

        // Переводим категорию с английского на русский
        const categoryMapReverse = {
            'Entertainment': 'Развлечения',
            'Software': 'Работа',
            'Education': 'Образование',
            'Health': 'Здоровье',
            'Finance': 'Финансы',
            'Other': 'Другое'
        };

        if (this.fields.category) {
            this.fields.category.value = categoryMapReverse[subscription.category] || 'Другое';
        }

        // Обновляем текст кнопки
        const submitBtnText = document.getElementById('submitBtnText');
        if (submitBtnText) {
            submitBtnText.textContent = 'Сохранить';
        }

        // Валидируем форму
        this.validateForm();
        this.updateSubmitButton();
    }

    setDefaultDate() {
        if (!this.fields.start_date) return;

        const today = new Date().toISOString().split('T')[0];
        this.fields.start_date.value = today;

        // Устанавливаем максимальную дату (1 год в будущем)
        const maxDate = new Date();
        maxDate.setFullYear(maxDate.getFullYear() + 1);
        this.fields.start_date.max = maxDate.toISOString().split('T')[0];
    }

    validateField(fieldName) {
        const field = this.fields[fieldName];
        const errorElement = this.errorElements[fieldName];

        if (!field) return true;

        let isValid = true;
        let errorMessage = '';

        switch (fieldName) {
            case 'name':
                const name = field.value.trim();
                if (!name) {
                    isValid = false;
                    errorMessage = 'Название обязательно для заполнения';
                } else if (name.length < 1 || name.length > 255) {
                    isValid = false;
                    errorMessage = 'Название должно содержать от 1 до 255 символов';
                }
                break;

            case 'cost':
                const cost = parseFloat(field.value);
                if (!field.value || isNaN(cost)) {
                    isValid = false;
                    errorMessage = 'Стоимость обязательна для заполнения';
                } else if (cost <= 0) {
                    isValid = false;
                    errorMessage = 'Стоимость должна быть положительным числом';
                } else if (!/^\d+(\.\d{1,2})?$/.test(field.value)) {
                    isValid = false;
                    errorMessage = 'Максимум 2 знака после запятой';
                }
                break;

            case 'start_date':
                if (!field.value) {
                    isValid = false;
                    errorMessage = 'Выберите дату начала подписки';
                } else {
                    const selectedDate = new Date(field.value);
                    const maxDate = new Date();
                    maxDate.setFullYear(maxDate.getFullYear() + 1);

                    if (selectedDate > maxDate) {
                        isValid = false;
                        errorMessage = 'Дата не может быть более чем на год в будущем';
                    }
                }
                break;
        }

        // Показываем/скрываем ошибку
        if (errorElement) {
            if (isValid) {
                this.hideFieldError(errorElement);
            } else {
                this.showFieldError(errorElement, errorMessage);
            }
        }

        return isValid;
    }

    validateForm() {
        let isValid = true;

        // Валидируем обязательные поля с валидацией
        if (!this.validateField('name')) {
            isValid = false;
        }
        if (!this.validateField('cost')) {
            isValid = false;
        }
        if (!this.validateField('start_date')) {
            isValid = false;
        }

        // Проверяем обязательные поля без специальной валидации
        if (!this.fields.category?.value) {
            isValid = false;
        }
        if (!this.fields.currency?.value) {
            isValid = false;
        }
        if (!this.fields.billing_period?.value) {
            isValid = false;
        }

        return isValid;
    }

    showFieldError(errorElement, message) {
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.classList.remove('hidden');
        }
    }

    hideFieldError(errorElement) {
        if (errorElement) {
            errorElement.classList.add('hidden');
        }
    }

    resetValidation() {
        Object.values(this.errorElements).forEach(errorElement => {
            if (errorElement) {
                this.hideFieldError(errorElement);
            }
        });
    }

    updateSubmitButton() {
        if (!this.submitBtn) return;

        const isValid = this.validateForm();
        this.submitBtn.disabled = !isValid;

        if (isValid) {
            this.submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        } else {
            this.submitBtn.classList.add('opacity-50', 'cursor-not-allowed');
        }
    }

    async handleSubmit(event) {
        event.preventDefault();

        if (!this.validateForm()) {
            return;
        }

        const formData = new FormData(this.form);
        const data = Object.fromEntries(formData.entries());

        // Переводим категорию с русского на английский для API
        const categoryMap = {
            'Развлечения': 'Entertainment',
            'Музыка': 'Entertainment',
            'Видео': 'Entertainment',
            'Игры': 'Entertainment',
            'Образование': 'Education',
            'Работа': 'Software',
            'Здоровье': 'Health',
            'Финансы': 'Finance',
            'Покупки': 'Other',
            'Другое': 'Other'
        };

        data.category = categoryMap[data.category] || 'Other';

        // Показываем индикатор загрузки
        this.showLoadingState();

        try {
            let response;

            if (this.editingId) {
                // Редактирование существующей подписки
                response = await fetch(`/api/subscriptions/${this.editingId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
            } else {
                // Создание новой подписки
                response = await fetch('/api/subscriptions', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        ...data,
                        manually_added: true
                    })
                });
            }

            if (response.ok) {
                const subscription = await response.json();

                // Показываем уведомление об успехе
                const message = this.editingId ? 'Подписка успешно обновлена!' : 'Подписка успешно добавлена!';
                this.showNotification(message, 'success');

                // Скрываем загрузку и закрываем модальное окно
                this.hideLoadingState();
                this.hideForm();

                // Обновляем список подписок через SubscriptionManager
                if (window.subscriptionManager) {
                    await window.subscriptionManager.loadSubscriptions();
                    window.subscriptionManager.updateSubscriptionCount();
                }

            } else {
                const error = await response.json();

                if (response.status === 409 && !this.editingId) {
                    // Дубликат подписки (только при создании)
                    if (confirm('Подписка с таким названием и стоимостью уже существует. Добавить дубликат?')) {
                        await this.createDuplicate(data);
                    } else {
                        this.hideLoadingState();
                    }
                } else {
                    throw new Error(error.error || 'Ошибка при сохранении подписки');
                }
            }

        } catch (error) {
            console.error('Error saving subscription:', error);
            this.showNotification(error.message, 'error');
            this.hideLoadingState();
        }
    }

    async createDuplicate(data) {
        try {
            const response = await fetch('/api/subscriptions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ...data,
                    manually_added: true,
                    force_duplicate: true
                })
            });

            if (response.ok) {
                this.showNotification('Подписка успешно добавлена!', 'success');
                this.hideForm();

                if (typeof loadSubscriptions === 'function') {
                    await loadSubscriptions();
                }
            } else {
                throw new Error('Ошибка при создании дубликата');
            }
        } catch (error) {
            this.showNotification('Ошибка при создании дубликата: ' + error.message, 'error');
        }
    }

    showLoadingState() {
        if (this.form && this.loadingIndicator) {
            this.form.classList.add('hidden');
            this.loadingIndicator.classList.remove('hidden');
        }
    }

    hideLoadingState() {
        if (this.form && this.loadingIndicator) {
            this.form.classList.remove('hidden');
            this.loadingIndicator.classList.add('hidden');
        }
    }

    showNotification(message, type) {
        // Удаляем предыдущие уведомления
        const existingNotifications = document.querySelectorAll('.notification-toast');
        existingNotifications.forEach(n => n.remove());

        // Создаем уведомление
        const notification = document.createElement('div');
        notification.className = `notification-toast fixed top-20 right-4 z-[70] px-6 py-4 border-2 font-bold uppercase tracking-wider transition-all transform translate-x-full max-w-md`;

        if (type === 'success') {
            notification.style.borderColor = '#10B981';
            notification.style.backgroundColor = 'rgba(16, 185, 129, 0.95)';
            notification.style.color = 'white';
        } else {
            notification.style.borderColor = '#FF006E';
            notification.style.backgroundColor = 'rgba(255, 0, 110, 0.95)';
            notification.style.color = 'white';
        }

        notification.innerHTML = `
            <div class="flex items-center gap-3">
                <iconify-icon icon="${type === 'success' ? 'lucide:check-circle' : 'lucide:alert-circle'}" class="text-2xl flex-shrink-0"></iconify-icon>
                <span class="text-sm break-words">${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        // Анимация появления
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);

        // Автоматическое скрытие через 5 секунд
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 5000);
    }

    handleKeyboard(event) {
        if (event.key === 'Escape') {
            if (!this.modal?.classList.contains('hidden')) {
                this.hideForm();
            }
        }

        if (event.key === 'Enter' && event.target === this.fields.notes) {
            if (this.validateForm()) {
                this.form?.dispatchEvent(new Event('submit'));
            }
        }
    }
}

// View subscription details modal
async function viewSubscription(id) {
    try {
        const response = await fetch(`/api/subscriptions/${id}`);
        if (!response.ok) return;
        const sub = await response.json();

        const modal = document.getElementById('viewSubscriptionModal');
        if (!modal) return;

        document.getElementById('viewSubName').textContent = sub.name;
        document.getElementById('viewSubCategory').textContent = sub.category;
        document.getElementById('viewSubCost').textContent = `${sub.cost} ${sub.currency}`;
        document.getElementById('viewSubPeriod').textContent = translatePeriod(sub.billing_period);
        document.getElementById('viewSubStart').textContent = formatDate(sub.start_date);
        document.getElementById('viewSubNext').textContent = formatDate(sub.next_billing_date);
        document.getElementById('viewSubNotes').textContent = sub.notes || '—';
        document.getElementById('viewSubStatus').textContent = sub.is_active ? 'Активна' : 'Неактивна';

        const payBtn = document.getElementById('viewSubPayBtn');
        if (sub.payment_url) {
            payBtn.href = sub.payment_url;
            payBtn.classList.remove('hidden');
        } else {
            payBtn.classList.add('hidden');
        }

        const editBtn = document.getElementById('viewSubEditBtn');
        editBtn.onclick = () => { closeViewModal(); editSubscription(id); };

        modal.classList.remove('hidden');
        modal.style.display = 'flex';
    } catch (e) {
        console.error('Error loading subscription details:', e);
    }
}

function closeViewModal() {
    const modal = document.getElementById('viewSubscriptionModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.style.display = 'none';
    }
}

// Check authentication status
async function checkAuthStatus() {
    try {
        const response = await fetch('/api/auth/status');
        if (response.ok) {
            const status = await response.json();
            updateImportButtons(status);
        }
    } catch (error) {
        console.error('Error checking auth status:', error);
    }
}

// Update import buttons based on auth status
function updateImportButtons(status) {
    const gmailBtn = document.getElementById('gmailImportBtn');
    const yandexBtn = document.getElementById('yandexImportBtn');
    const mailruBtn = document.getElementById('mailruImportBtn');

    // Gmail button - allow reconnection
    if (gmailBtn && status.google_connected) {
        gmailBtn.innerHTML = `
            <iconify-icon icon="lucide:check-circle" class="inline-block mr-2 text-xl"></iconify-icon>
            Gmail (Подключен)
        `;
        gmailBtn.style.setProperty('border-color', '#00FF00', 'important');
        gmailBtn.style.setProperty('color', '#00FF00', 'important');
        // Don't disable - allow reconnection
        gmailBtn.disabled = false;
        gmailBtn.onclick = () => {
            if (confirm('Переподключить Gmail для обновления разрешений?')) {
                window.location.href = '/auth/google';
            }
        };
    }

    // Yandex button - allow reconnection
    if (yandexBtn && status.yandex_connected) {
        yandexBtn.innerHTML = `
            <iconify-icon icon="lucide:check-circle" class="inline-block mr-2 text-xl"></iconify-icon>
            Yandex (Подключен)
        `;
        yandexBtn.style.setProperty('border-color', '#00FF00', 'important');
        yandexBtn.style.setProperty('color', '#00FF00', 'important');
        // Don't disable - allow reconnection
        yandexBtn.disabled = false;
        yandexBtn.onclick = () => {
            if (confirm('Переподключить Yandex для обновления разрешений?')) {
                window.location.href = '/auth/yandex';
            }
        };
    }
}
