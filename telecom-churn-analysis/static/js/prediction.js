document.addEventListener("DOMContentLoaded", function() {

    // Get CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    // Form submission for single prediction
    const form = document.getElementById('singlePredictionForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(form);

            fetch('/predict', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showAlert(data.error, 'danger');
                    return;
                }

                // Show results
                document.getElementById('predictionResultCard').style.display = 'block';

                const probText = document.getElementById('probabilityText');
                const riskLabel = document.getElementById('riskLabel');
                const probBar = document.getElementById('probabilityBar');
                const predText = document.getElementById('predictionText');

                probText.textContent = data.probability + '%';
                riskLabel.textContent = data.risk_level + ' RISK';
                probBar.style.width = data.probability + '%';

                let textStr = "";

                // Reset classes
                probBar.className = 'progress-bar progress-bar-striped progress-bar-animated';
                riskLabel.className = 'mb-3';

                const riskLevelLower = data.risk_level.toLowerCase();
                if (riskLevelLower === 'high') {
                    probBar.classList.add('bg-danger');
                    riskLabel.classList.add('text-danger');
                    textStr = "Customer is highly likely to churn.";
                } else if (riskLevelLower === 'medium') {
                    probBar.classList.add('bg-warning', 'text-dark');
                    riskLabel.classList.add('text-warning');
                    textStr = "Customer has a moderate risk of churning.";
                } else {
                    probBar.classList.add('bg-success');
                    riskLabel.classList.add('text-success');
                    textStr = "Customer is likely to stay.";
                }

                predText.textContent = textStr;
            })
            .catch(error => {
                showAlert('An error occurred during prediction.', 'danger');
            });
        });
    }

    // Chart instances store to destroy them before rendering new ones
    let bulkChurnChartInstance = null;
    let bulkRiskChartInstance = null;
    let bulkContractChartInstance = null;

    // Bulk prediction form
    const bulkForm = document.getElementById('bulkPredictionForm');
    if (bulkForm) {
        bulkForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const btn = bulkForm.querySelector('button');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            btn.disabled = true;

            const formData = new FormData(bulkForm);

            fetch('/bulk-predict', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                btn.innerHTML = originalText;
                btn.disabled = false;

                if (data.error) {
                    showAlert(data.error, 'danger');
                } else {
                    showAlert(data.success, 'success');

                    // Render charts
                    if (data.stats && document.getElementById('bulkChartsRow')) {
                        document.getElementById('bulkChartsRow').style.display = 'flex';

                        const commonOptions = {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: { position: 'bottom' }
                            }
                        };

                        // Destroy old charts if they exist
                        if(bulkChurnChartInstance) bulkChurnChartInstance.destroy();
                        if(bulkRiskChartInstance) bulkRiskChartInstance.destroy();
                        if(bulkContractChartInstance) bulkContractChartInstance.destroy();

                        // Churn Distribution
                        bulkChurnChartInstance = new Chart(document.getElementById('bulkChurnDistChart'), {
                            type: 'doughnut',
                            data: {
                                labels: data.stats.churn_dist.labels,
                                datasets: [{
                                    data: data.stats.churn_dist.data,
                                    backgroundColor: ['#e74a3b', '#1cc88a']
                                }]
                            },
                            options: commonOptions
                        });

                        // Risk Distribution
                        bulkRiskChartInstance = new Chart(document.getElementById('bulkRiskDistChart'), {
                            type: 'pie',
                            data: {
                                labels: data.stats.risk_dist.labels,
                                datasets: [{
                                    data: data.stats.risk_dist.data,
                                    backgroundColor: ['#e74a3b', '#f6c23e', '#1cc88a']
                                }]
                            },
                            options: commonOptions
                        });

                        // Contract Distribution
                        if (data.stats.contract_dist.labels.length > 0) {
                            bulkContractChartInstance = new Chart(document.getElementById('bulkContractChart'), {
                                type: 'bar',
                                data: {
                                    labels: data.stats.contract_dist.labels,
                                    datasets: [
                                        {
                                            label: 'High Risk',
                                            data: data.stats.contract_dist.datasets[0].data,
                                            backgroundColor: '#e74a3b'
                                        },
                                        {
                                            label: 'Medium Risk',
                                            data: data.stats.contract_dist.datasets[1].data,
                                            backgroundColor: '#f6c23e'
                                        },
                                        {
                                            label: 'Low Risk',
                                            data: data.stats.contract_dist.datasets[2].data,
                                            backgroundColor: '#1cc88a'
                                        }
                                    ]
                                },
                                options: {
                                    ...commonOptions,
                                    scales: {
                                        x: { stacked: true },
                                        y: { stacked: true, beginAtZero: true }
                                    }
                                }
                            });
                        }
                    }
                }
            })
            .catch(error => {
                btn.innerHTML = originalText;
                btn.disabled = false;
                showAlert('An error occurred during bulk prediction.', 'danger');
            });
        });
    }

    // Train Model Button
    const trainBtn = document.getElementById('trainBtn');
    if (trainBtn) {
        trainBtn.addEventListener('click', function() {
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Training Models...';
            this.disabled = true;

            fetch('/train', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                this.innerHTML = originalText;
                this.disabled = false;

                if (data.error) {
                    showAlert(data.error, 'danger');
                } else {
                    showAlert(data.message, 'success');
                }
            })
            .catch(error => {
                this.innerHTML = originalText;
                this.disabled = false;
                showAlert('An error occurred while training models.', 'danger');
            });
        });
    }

    function showAlert(message, type) {
        const placeholder = document.getElementById('alertPlaceholder');
        if (placeholder) {
            placeholder.innerHTML = `
                <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `;
        }
    }
});
