document.addEventListener('DOMContentLoaded', () => {
    // 1. Date Range Dropdown Change
    const rangeSelect = document.getElementById('date-range-select');
    if (rangeSelect) {
        rangeSelect.addEventListener('change', (e) => {
            const selectedVal = e.target.value;
            window.location.href = `?range=${encodeURIComponent(selectedVal)}`;
        });
    }

    // 2. Render Chart.js Bar & Doughnut Charts
    const data = window.INSIGHTS_DATA || {};

    // Bar Chart: Average Nutrition Overview (Protein, Carbs, Fat, Sugar, Fiber)
    const barCanvas = document.getElementById('avgNutritionChartCanvas');
    if (barCanvas && typeof Chart !== 'undefined') {
        const barLabels = ['Protein', 'Carbs', 'Fat', 'Sugar', 'Fiber'];
        const barValues = [
            data.avgProtein || 0,
            data.avgCarbs || 0,
            data.avgFat || 0,
            data.avgSugar || 0,
            data.avgFiber || 0
        ];
        const barColors = ['#38bdf8', '#10b981', '#f59e0b', '#a855f7', '#34d399'];

        new Chart(barCanvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: barLabels,
                datasets: [{
                    label: 'Average Grams per 100g',
                    data: barValues,
                    backgroundColor: barColors,
                    borderRadius: 6,
                    maxBarThickness: 45
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y}g`
                        }
                    }
                },
                scales: {
                    x: { ticks: { color: '#64748b', font: { family: 'Inter', size: 11, weight: '500' } }, grid: { display: false } },
                    y: {
                        title: { display: true, text: 'Average grams per 100g', color: '#64748b', font: { family: 'Inter', size: 12, weight: '600' } },
                        ticks: { color: '#64748b', font: { family: 'Inter', size: 11 } },
                        grid: { color: '#e2e8f0' },
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // Doughnut Chart: Rating Distribution
    const doughnutCanvas = document.getElementById('ratingDoughnutCanvas');
    if (doughnutCanvas && typeof Chart !== 'undefined' && data.hasAnalyzed) {
        new Chart(doughnutCanvas.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Good Choice', 'Moderate', 'Limit Intake'],
                datasets: [{
                    data: [data.ratingGood || 0, data.ratingModerate || 0, data.ratingLimit || 0],
                    backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#475569', font: { family: 'Inter', size: 12, weight: '600' } }
                    }
                },
                cutout: '65%'
            }
        });
    }

    // 3. Generate AI Insights Button Handler
    const generateAiBtn = document.getElementById('generate-ai-btn');
    const aiLoadingBox = document.getElementById('ai-loading-box');
    const aiErrorBox = document.getElementById('ai-error-box');
    const aiInsightsContainer = document.getElementById('ai-insights-container');

    const aiSummaryText = document.getElementById('ai-summary-text');
    const sectionAiPositives = document.getElementById('section-ai-positives');
    const listAiPositives = document.getElementById('list-ai-positives');
    const sectionAiConcerns = document.getElementById('section-ai-concerns');
    const listAiConcerns = document.getElementById('list-ai-concerns');
    const sectionAiShopping = document.getElementById('section-ai-shopping');
    const listAiShopping = document.getElementById('list-ai-shopping');
    const sectionAiComparison = document.getElementById('section-ai-comparison');
    const aiComparisonText = document.getElementById('ai-comparison-text');
    const aiDisclaimerBox = document.getElementById('ai-disclaimer-box');

    function renderList(sectionEl, listEl, items) {
        if (Array.isArray(items) && items.length > 0) {
            listEl.innerHTML = '';
            items.forEach(item => {
                if (item && item.trim()) {
                    const li = document.createElement('li');
                    li.textContent = item;
                    listEl.appendChild(li);
                }
            });
            sectionEl.style.display = 'block';
        } else {
            sectionEl.style.display = 'none';
        }
    }

    if (generateAiBtn) {
        generateAiBtn.addEventListener('click', async () => {
            const rangeVal = generateAiBtn.getAttribute('data-range') || '30';
            
            generateAiBtn.disabled = true;
            generateAiBtn.textContent = 'Generating insights...';
            aiErrorBox.style.display = 'none';
            aiErrorBox.textContent = '';
            aiInsightsContainer.style.display = 'none';
            aiLoadingBox.style.display = 'flex';

            try {
                const response = await fetch(`/health-analysis/ai-insights/?range=${encodeURIComponent(rangeVal)}`);
                const data = await response.json();

                if (response.ok && data.success && data.insights) {
                    const ins = data.insights;

                    // Summary
                    aiSummaryText.textContent = ins.summary || 'Educational summary completed.';

                    // Positive Patterns
                    renderList(sectionAiPositives, listAiPositives, ins.positive_patterns);

                    // Areas to Consider
                    renderList(sectionAiConcerns, listAiConcerns, ins.areas_to_consider);

                    // Shopping Tips
                    renderList(sectionAiShopping, listAiShopping, ins.shopping_tip);

                    // Comparison Guidance
                    if (ins.comparison_tip && ins.comparison_tip.trim()) {
                        aiComparisonText.textContent = ins.comparison_tip;
                        sectionAiComparison.style.display = 'block';
                    } else {
                        sectionAiComparison.style.display = 'none';
                    }

                    // Disclaimer
                    aiDisclaimerBox.textContent = ins.disclaimer || 'Educational summary based on scanned packaged product information per 100g. This does not represent total dietary intake and is not medical advice.';

                    aiInsightsContainer.style.display = 'block';
                } else {
                    aiErrorBox.textContent = data.message || 'Unable to generate AI insights right now. Please try again.';
                    aiErrorBox.style.display = 'block';
                }
            } catch (err) {
                console.error('Error fetching AI insights:', err);
                aiErrorBox.textContent = 'Unable to generate AI insights right now. Please try again.';
                aiErrorBox.style.display = 'block';
            } finally {
                aiLoadingBox.style.display = 'none';
                generateAiBtn.disabled = false;
                generateAiBtn.textContent = '✨ Regenerate AI Insights';
            }
        });
    }
});
