document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('search-form');
    const barcodeInput = document.getElementById('barcode-input');
    const searchBtn = document.getElementById('search-btn');
    const loadingBox = document.getElementById('loading-box');
    const errorBox = document.getElementById('error-box');
    const favoriteBtn = document.getElementById('favorite-btn');
    const resetScanBtn = document.getElementById('reset-scan-btn');

    // Camera Scanner DOM Elements
    const startScanBtn = document.getElementById('start-scan-btn');
    const stopScanBtn = document.getElementById('stop-scan-btn');
    const scannerContainer = document.getElementById('scanner-container');
    const cameraStatusMsg = document.getElementById('camera-status-msg');

    // DOM Elements for Product Details
    const productNameEl = document.getElementById('product-name');
    const productBrandEl = document.getElementById('product-brand');
    const productBarcodeEl = document.getElementById('product-barcode');
    const productSourceFooter = document.getElementById('product-source-footer');
    const ingredientsEl = document.getElementById('ingredients');

    // Nutrition DOM Elements
    const caloriesEl = document.getElementById('val-calories');
    const proteinEl = document.getElementById('val-protein');
    const carbsEl = document.getElementById('val-carbs');
    const fatEl = document.getElementById('val-fat');
    const satFatEl = document.getElementById('val-sat-fat');
    const sugarEl = document.getElementById('val-sugar');
    const fiberEl = document.getElementById('val-fiber');
    const sodiumEl = document.getElementById('val-sodium');

    // Analysis Action & Results DOM Elements
    const analyzeBtn = document.getElementById('analyze-btn');
    const analysisLoadingBox = document.getElementById('analysis-loading-box');
    const analysisErrorBox = document.getElementById('analysis-error-box');
    const analysisContainer = document.getElementById('analysis-container');
    const overallRatingBadge = document.getElementById('overall-rating-badge');
    const analysisSummary = document.getElementById('analysis-summary');
    const analysisDisclaimer = document.getElementById('analysis-disclaimer');

    let currentBarcode = '';
    let html5QrCode = null;
    let nutritionChart = null;

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function updateFavoriteButtonUI(isSaved) {
        if (!favoriteBtn) return;
        if (isSaved) {
            favoriteBtn.innerHTML = '⭐ Saved';
            favoriteBtn.classList.add('active');
        } else {
            favoriteBtn.innerHTML = '☆ Save Product';
            favoriteBtn.classList.remove('active');
        }
    }

    function destroyNutritionChart() {
        if (nutritionChart) {
            nutritionChart.destroy();
            nutritionChart = null;
        }
        const chartSection = document.getElementById('nutrition-chart-section');
        if (chartSection) {
            chartSection.style.display = 'none';
        }
    }

    function parseNutrientValue(val) {
        if (val === null || val === undefined || val === '') return null;
        const num = parseFloat(val);
        return isNaN(num) ? null : num;
    }

    function renderNutritionChart(product) {
        destroyNutritionChart();

        const chartSection = document.getElementById('nutrition-chart-section');
        const canvas = document.getElementById('nutritionChartCanvas');

        if (!chartSection || !canvas) return;

        if (typeof Chart === 'undefined') {
            console.warn('Chart.js library is not loaded.');
            return;
        }

        const nutrientDefs = [
            { label: 'Protein', key: 'protein', color: '#38bdf8' },
            { label: 'Carbohydrates', key: 'carbohydrates', color: '#10b981' },
            { label: 'Fat', key: 'fat', color: '#f59e0b' },
            { label: 'Saturated Fat', key: 'saturated_fat', color: '#ef4444' },
            { label: 'Sugar', key: 'sugar', color: '#a855f7' },
            { label: 'Fiber', key: 'fiber', color: '#34d399' }
        ];

        const chartLabels = [];
        const chartData = [];
        const chartColors = [];

        nutrientDefs.forEach(def => {
            const val = parseNutrientValue(product[def.key]);
            if (val !== null) {
                chartLabels.push(def.label);
                chartData.push(val);
                chartColors.push(def.color);
            }
        });

        if (chartData.length === 0) {
            chartSection.style.display = 'none';
            return;
        }

        chartSection.style.display = 'block';

        const ctx = canvas.getContext('2d');
        nutritionChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: chartLabels,
                datasets: [{
                    label: 'Grams per 100g',
                    data: chartData,
                    backgroundColor: chartColors,
                    borderRadius: 6,
                    borderWidth: 0,
                    maxBarThickness: 45
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label || ''}: ${context.parsed.y}g`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: '#64748b',
                            font: {
                                family: 'Inter',
                                size: 11,
                                weight: '500'
                            }
                        },
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Grams per 100g',
                            color: '#64748b',
                            font: {
                                family: 'Inter',
                                size: 12,
                                weight: '600'
                            }
                        },
                        ticks: {
                            color: '#64748b',
                            font: {
                                family: 'Inter',
                                size: 11
                            }
                        },
                        grid: {
                            color: '#e2e8f0'
                        },
                        beginAtZero: true
                    }
                }
            }
        });
    }

    function formatVal(val, unit = '') {
        if (val === null || val === undefined || val === '') {
            return 'N/A';
        }
        return `${val} ${unit}`.trim();
    }

    function showError(message) {
        errorBox.textContent = message;
        errorBox.style.display = 'block';
    }

    function showCameraStatus(message, type = 'info') {
        cameraStatusMsg.textContent = message;
        cameraStatusMsg.className = `camera-status-msg ${type}`;
        cameraStatusMsg.style.display = 'block';
    }

    function hideCameraStatus() {
        cameraStatusMsg.style.display = 'none';
        cameraStatusMsg.textContent = '';
    }

    function resetAnalysisUI() {
        const allergyAlertCard = document.getElementById('allergy-alert-card');
        if (allergyAlertCard) allergyAlertCard.style.display = 'none';
        analysisContainer.style.display = 'none';
        analysisErrorBox.style.display = 'none';
        analysisErrorBox.textContent = '';
        analysisLoadingBox.style.display = 'none';
        analyzeBtn.disabled = false;
        analyzeBtn.style.display = 'inline-block';
        analyzeBtn.textContent = 'Analyze Health Impact with AI';
    }

    function clearUI() {
        errorBox.style.display = 'none';
        errorBox.textContent = '';
        resultCard.style.display = 'none';
        destroyNutritionChart();
        resetAnalysisUI();
    }

    function renderListSection(sectionId, listId, itemsArray) {
        const sectionEl = document.getElementById(sectionId);
        const listEl = document.getElementById(listId);

        if (Array.isArray(itemsArray) && itemsArray.length > 0) {
            listEl.innerHTML = '';
            itemsArray.forEach(item => {
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

    // --- CAMERA SCANNER LOGIC ---

    async function stopCameraScanner() {
        if (html5QrCode) {
            try {
                if (html5QrCode.isScanning) {
                    await html5QrCode.stop();
                }
            } catch (e) {}
            html5QrCode = null;
        }
        scannerContainer.style.display = 'none';
    }

    async function startCameraScanner() {
        await stopCameraScanner();
        hideCameraStatus();
        clearUI();

        scannerContainer.style.display = 'block';

        if (typeof Html5Qrcode === 'undefined') {
            showCameraStatus('Scanner library failed to load. Please enter barcode manually.', 'error');
            scannerContainer.style.display = 'none';
            return;
        }

        html5QrCode = new Html5Qrcode("reader");

        const config = {
            fps: 10,
            qrbox: { width: 260, height: 160 },
            formatsToSupport: [
                Html5QrcodeSupportedFormats.EAN_13,
                Html5QrcodeSupportedFormats.EAN_8,
                Html5QrcodeSupportedFormats.UPC_A,
                Html5QrcodeSupportedFormats.UPC_E,
                Html5QrcodeSupportedFormats.CODE_128,
            ]
        };

        try {
            await html5QrCode.start(
                { facingMode: "environment" },
                config,
                onBarcodeDetected,
                onScanFailure
            );
        } catch (err) {
            scannerContainer.style.display = 'none';
            const errStr = (err && err.toString()) ? err.toString().toLowerCase() : '';
            const errName = (err && err.name) ? err.name : '';

            if (errName === 'NotAllowedError' || errStr.includes('permission') || errStr.includes('denied')) {
                showCameraStatus('Camera permission was denied. You can still enter the barcode manually.', 'error');
            } else if (errName === 'NotFoundError' || errStr.includes('not found') || errStr.includes('no camera')) {
                showCameraStatus('No camera was found on this device. Please enter the barcode manually.', 'error');
            } else {
                showCameraStatus('Unable to access camera. Please enter the barcode manually.', 'error');
            }
        }
    }

    async function onBarcodeDetected(decodedText) {
        await stopCameraScanner();
        const barcode = decodedText.trim();
        barcodeInput.value = barcode;
        showCameraStatus(`Barcode detected: ${barcode}`, 'success');

        performProductSearch(barcode);
    }

    function onScanFailure(error) {}

    // --- PRODUCT SEARCH LOGIC ---

    async function performProductSearch(barcode) {
        clearUI();

        if (!barcode) {
            showError('Please enter a barcode number.');
            return;
        }

        if (!/^\d+$/.test(barcode)) {
            showError('Barcode must contain digits only.');
            return;
        }

        currentBarcode = barcode;
        loadingBox.style.display = 'flex';
        searchBtn.disabled = true;

        try {
            const targetUrl = `/products/lookup/${encodeURIComponent(barcode)}/`;
            console.log("Searching product from URL:", targetUrl);
            const response = await fetch(targetUrl);
            const data = await response.json();

            if (response.ok && data.success) {
                const product = data.product;

                productNameEl.textContent = product.product_name || 'Unknown Product';
                productBrandEl.textContent = product.brand ? `Brand: ${product.brand}` : 'Brand: Not available';
                productBarcodeEl.textContent = product.barcode || barcode;
                
                if (product.ingredients && product.ingredients.trim()) {
                    ingredientsEl.textContent = product.ingredients;
                } else {
                    ingredientsEl.textContent = 'Ingredient information is not available for this product.';
                }

                const source = data.source || 'database';
                if (productSourceFooter) {
                    if (source === 'open_food_facts') {
                        productSourceFooter.textContent = 'Product information source: Open Food Facts';
                    } else {
                        productSourceFooter.textContent = 'Product information source: Saved Database';
                    }
                }

                caloriesEl.textContent = formatVal(product.calories, 'kcal');
                proteinEl.textContent = formatVal(product.protein, 'g');
                carbsEl.textContent = formatVal(product.carbohydrates, 'g');
                fatEl.textContent = formatVal(product.fat, 'g');
                satFatEl.textContent = formatVal(product.saturated_fat, 'g');
                sugarEl.textContent = formatVal(product.sugar, 'g');
                fiberEl.textContent = formatVal(product.fiber, 'g');
                sodiumEl.textContent = formatVal(product.sodium, 'g');

                resultCard.style.display = 'block';
                updateFavoriteButtonUI(data.is_saved || false);
                renderNutritionChart(product);

            } else if (response.status === 404 || !data.success) {
                showError('Product not found. Please check the barcode and try again.');
            } else {
                showError('Something went wrong while fetching the product. Please try again.');
            }

        } catch (error) {
            showError('Something went wrong while fetching the product. Please try again.');
        } finally {
            loadingBox.style.display = 'none';
            searchBtn.disabled = false;
        }
    }

    // --- EVENT LISTENERS ---

    if (favoriteBtn) {
        favoriteBtn.addEventListener('click', async () => {
            if (!currentBarcode) return;
            favoriteBtn.disabled = true;
            try {
                const csrftoken = getCookie('csrftoken');
                const response = await fetch(`/products/saved/toggle/${encodeURIComponent(currentBarcode)}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken || ''
                    }
                });
                const data = await response.json();
                if (response.ok && data.success) {
                    updateFavoriteButtonUI(data.is_saved);
                }
            } catch (err) {
                console.error('Error toggling favorite:', err);
            } finally {
                favoriteBtn.disabled = false;
            }
        });
    }

    startScanBtn.addEventListener('click', () => {
        startCameraScanner();
    });

    stopScanBtn.addEventListener('click', () => {
        stopCameraScanner();
        hideCameraStatus();
    });

    if (resetScanBtn) {
        resetScanBtn.addEventListener('click', () => {
            stopCameraScanner();
            hideCameraStatus();
            barcodeInput.value = '';
            currentBarcode = '';
            clearUI();
            window.scrollTo({ top: 0, behavior: 'smooth' });
            barcodeInput.focus();
        });
    }

    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        stopCameraScanner();
        hideCameraStatus();
        const barcode = barcodeInput.value.trim();
        performProductSearch(barcode);
    });

    // --- AI HEALTH IMPACT ANALYSIS BUTTON LOGIC ---

    analyzeBtn.addEventListener('click', async () => {
        if (!currentBarcode) {
            const inputVal = barcodeInput.value.trim();
            if (inputVal && /^\d+$/.test(inputVal)) {
                currentBarcode = inputVal;
            }
        }

        if (!currentBarcode) {
            analysisErrorBox.textContent = 'Please enter or search a valid barcode first.';
            analysisErrorBox.style.display = 'block';
            return;
        }

        analyzeBtn.disabled = true;
        analyzeBtn.textContent = 'Analyzing...';
        analysisErrorBox.style.display = 'none';
        analysisErrorBox.textContent = '';
        analysisContainer.style.display = 'none';
        analysisLoadingBox.style.display = 'flex';

        try {
            const targetUrl = `/health-analysis/product/${encodeURIComponent(currentBarcode)}/`;
            console.log("Fetching AI health analysis from:", targetUrl);
            const response = await fetch(targetUrl);
            const data = await response.json();

            if (response.ok && data.success && data.analysis) {
                const analysis = data.analysis;

                // 1. Overall Rating Badge
                const rating = analysis.overall_rating || 'Moderate';
                overallRatingBadge.textContent = rating;

                if (rating === 'Good Choice') {
                    overallRatingBadge.className = 'rating-badge rating-good';
                } else if (rating === 'Limit Intake') {
                    overallRatingBadge.className = 'rating-badge rating-limit';
                } else {
                    overallRatingBadge.className = 'rating-badge rating-moderate';
                }

                // 2. Summary
                analysisSummary.textContent = analysis.summary || 'Nutritional evaluation completed.';

                // 3. Personalized Guidance Note
                const sectionPersonalized = document.getElementById('section-personalized');
                const personalizedNoteEl = document.getElementById('analysis-personalized-note');

                if (analysis.personalized_note && analysis.personalized_note.trim()) {
                    personalizedNoteEl.textContent = analysis.personalized_note;
                    sectionPersonalized.style.display = 'block';
                } else {
                    sectionPersonalized.style.display = 'none';
                }

                // 4. Positive Points
                renderListSection('section-positives', 'list-positives', analysis.positive_points);

                // 5. Nutritional Concerns
                renderListSection('section-concerns', 'list-concerns', analysis.concerns);

                // 6. Body Impacts
                renderListSection('section-impacts', 'list-impacts', analysis.body_impacts);

                // 7. Health Condition Guidance
                renderListSection('section-condition-notes', 'list-condition-notes', analysis.condition_specific_notes);

                // 8. Possible Long-Term Health Risks
                renderListSection('section-risks', 'list-risks', analysis.possible_long_term_risks);

                // 9. Who Should Be Careful
                renderListSection('section-caution', 'list-caution', analysis.who_should_be_careful);

                // 10. Consumption Advice
                renderListSection('section-advice', 'list-advice', analysis.consumption_advice);

                // 11. Allergy Alert Card
                const allergyAlertCard = document.getElementById('allergy-alert-card');
                const allergyWarningText = document.getElementById('allergy-warning-text');

                if (analysis.allergy_alert && analysis.allergy_warning && analysis.allergy_warning.trim()) {
                    allergyWarningText.textContent = analysis.allergy_warning;
                    allergyAlertCard.style.display = 'block';
                } else {
                    allergyAlertCard.style.display = 'none';
                }

                // 12. Medical Disclaimer
                analysisDisclaimer.textContent = analysis.disclaimer || 'This is general educational nutrition information and does not constitute medical advice. Always verify allergen information on the product packaging before consumption.';

                analysisContainer.style.display = 'block';

            } else {
                analysisErrorBox.textContent = data.message || 'Unable to analyze this product right now. Please try again.';
                analysisErrorBox.style.display = 'block';
            }

        } catch (error) {
            console.error("Fetch error:", error);
            analysisErrorBox.textContent = 'Unable to analyze this product right now. Please try again.';
            analysisErrorBox.style.display = 'block';
        } finally {
            analysisLoadingBox.style.display = 'none';
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = 'Analyze Health Impact with AI';
        }
    });

    // Check if barcode parameter exists in URL (e.g. from Scan History "View Product" or "Analyze Again")
    const urlParams = new URLSearchParams(window.location.search);
    const barcodeFromUrl = urlParams.get('barcode');
    const autoAnalyze = urlParams.get('analyze') === 'true' || urlParams.get('auto_analyze') === 'true';

    if (barcodeFromUrl && barcodeFromUrl.trim()) {
        const cleanBarcode = barcodeFromUrl.trim();
        barcodeInput.value = cleanBarcode;
        performProductSearch(cleanBarcode).then(() => {
            if (autoAnalyze) {
                setTimeout(() => {
                    const analyzeBtn = document.getElementById('analyze-btn');
                    if (analyzeBtn && !analyzeBtn.disabled) {
                        analyzeBtn.click();
                        analyzeBtn.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }, 300);
            }
        });
    }
});



