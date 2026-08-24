document.addEventListener("DOMContentLoaded", function() {
    // Only run on dashboard page
    if (!document.getElementById('churnDistChart')) return;

    fetch('/api/dashboard/charts')
        .then(response => response.json())
        .then(data => {
            if(Object.keys(data).length === 0) return;

            // Common Chart.js Options
            const commonOptions = {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                }
            };

            // Colors
            const colorChurn = 'rgba(231, 74, 59, 0.8)';
            const colorStayed = 'rgba(28, 200, 138, 0.8)';

            // 1. Churn Distribution (Pie)
            new Chart(document.getElementById('churnDistChart'), {
                type: 'doughnut',
                data: {
                    labels: data.churn_dist.labels,
                    datasets: [{
                        data: data.churn_dist.data,
                        backgroundColor: [colorChurn, colorStayed],
                        hoverOffset: 4
                    }]
                },
                options: commonOptions
            });

            // 2. Churn by Contract
            new Chart(document.getElementById('contractChurnChart'), {
                type: 'bar',
                data: {
                    labels: data.contract_churn.labels,
                    datasets: [
                        {
                            label: 'Churned',
                            data: data.contract_churn.datasets[0].data,
                            backgroundColor: colorChurn
                        },
                        {
                            label: 'Stayed',
                            data: data.contract_churn.datasets[1].data,
                            backgroundColor: colorStayed
                        }
                    ]
                },
                options: {
                    ...commonOptions,
                    scales: { y: { beginAtZero: true } }
                }
            });

            // 3. Churn by Tenure
            new Chart(document.getElementById('tenureChurnChart'), {
                type: 'line',
                data: {
                    labels: data.tenure_churn.labels,
                    datasets: [
                        {
                            label: 'Churned',
                            data: data.tenure_churn.datasets[0].data,
                            borderColor: colorChurn,
                            tension: 0.1,
                            fill: false
                        },
                        {
                            label: 'Stayed',
                            data: data.tenure_churn.datasets[1].data,
                            borderColor: colorStayed,
                            tension: 0.1,
                            fill: false
                        }
                    ]
                },
                options: {
                    ...commonOptions,
                    scales: { y: { beginAtZero: true } }
                }
            });

            // 4. Monthly Charges vs Churn
            new Chart(document.getElementById('chargesChurnChart'), {
                type: 'bar',
                data: {
                    labels: data.avg_charges_churn.labels,
                    datasets: [{
                        label: 'Avg Monthly Charges ($)',
                        data: data.avg_charges_churn.data,
                        backgroundColor: [colorChurn, colorStayed]
                    }]
                },
                options: {
                    ...commonOptions,
                    scales: { y: { beginAtZero: true } }
                }
            });
        });
});
