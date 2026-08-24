document.addEventListener("DOMContentLoaded", function() {
    if (!document.getElementById('paymentChurnChart')) return;

    fetch('/api/dashboard/charts')
        .then(response => response.json())
        .then(data => {
            if(Object.keys(data).length === 0) return;

            const commonOptions = {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                },
                scales: {
                    x: { stacked: true },
                    y: { stacked: true, beginAtZero: true }
                }
            };

            const colorChurn = 'rgba(231, 74, 59, 0.8)';
            const colorStayed = 'rgba(78, 115, 223, 0.8)';

            // Payment Churn Chart
            new Chart(document.getElementById('paymentChurnChart'), {
                type: 'bar',
                data: {
                    labels: data.payment_churn.labels,
                    datasets: [
                        {
                            label: 'Churned',
                            data: data.payment_churn.datasets[0].data,
                            backgroundColor: colorChurn
                        },
                        {
                            label: 'Stayed',
                            data: data.payment_churn.datasets[1].data,
                            backgroundColor: colorStayed
                        }
                    ]
                },
                options: commonOptions
            });

            // Internet Churn Chart
            new Chart(document.getElementById('internetChurnChart'), {
                type: 'bar',
                data: {
                    labels: data.internet_churn.labels,
                    datasets: [
                        {
                            label: 'Churned',
                            data: data.internet_churn.datasets[0].data,
                            backgroundColor: colorChurn
                        },
                        {
                            label: 'Stayed',
                            data: data.internet_churn.datasets[1].data,
                            backgroundColor: colorStayed
                        }
                    ]
                },
                options: commonOptions
            });
        });
});
