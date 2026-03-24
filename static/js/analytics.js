// Analytics JavaScript with Chart.js

// Load analytics summary
async function loadAnalyticsSummary() {
    try {
        const response = await fetch('/api/analytics/summary');
        const data = await response.json();
        
        // Update summary cards
        document.getElementById('totalMonthly').textContent = `${data.total_monthly} ₽`;
        document.getElementById('totalYearly').textContent = `${data.total_yearly} ₽`;
        document.getElementById('subscriptionCount').textContent = data.subscription_count;
        document.getElementById('averageMonthly').textContent = `${data.average_monthly} ₽`;
    } catch (error) {
        console.error('Error loading analytics summary:', error);
    }
}

// Load and display category chart
async function loadCategoryChart() {
    try {
        const response = await fetch('/api/analytics/by-category');
        const data = await response.json();
        
        const ctx = document.getElementById('categoryChart');
        if (!ctx) return;
        
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: data.labels,
                datasets: data.datasets
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    title: {
                        display: true,
                        text: 'Расходы по категориям'
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading category chart:', error);
    }
}

// Load and display timeline chart
async function loadTimelineChart() {
    try {
        const response = await fetch('/api/analytics/timeline');
        const data = await response.json();
        
        const ctx = document.getElementById('timelineChart');
        if (!ctx) return;
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: data.datasets
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: true
                    },
                    title: {
                        display: true,
                        text: 'Расходы по времени'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading timeline chart:', error);
    }
}

// Load top expenses
async function loadTopExpenses() {
    try {
        const response = await fetch('/api/analytics/top-expenses');
        const expenses = await response.json();
        
        const container = document.getElementById('topExpensesList');
        if (!container) return;
        
        container.innerHTML = expenses.map((exp, index) => `
            <div class="expense-item">
                <span class="rank">${index + 1}</span>
                <span class="name">${exp.name}</span>
                <span class="cost">${exp.monthly_cost} ₽/мес</span>
                <span class="category">${exp.category}</span>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading top expenses:', error);
    }
}

// Load forecast
async function loadForecast() {
    try {
        const response = await fetch('/api/forecast/monthly?months=12');
        const forecast = await response.json();
        
        const ctx = document.getElementById('forecastChart');
        if (!ctx) return;
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: forecast.map(f => f.month),
                datasets: [{
                    label: 'Прогноз расходов',
                    data: forecast.map(f => f.total),
                    backgroundColor: 'rgba(123, 47, 218, 0.5)',
                    borderColor: 'rgba(123, 47, 218, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: true
                    },
                    title: {
                        display: true,
                        text: 'Прогноз расходов на 12 месяцев'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading forecast:', error);
    }
}

// Initialize analytics on page load
document.addEventListener('DOMContentLoaded', function() {
    loadAnalyticsSummary();
    loadCategoryChart();
    loadTimelineChart();
    loadTopExpenses();
    loadForecast();
});
