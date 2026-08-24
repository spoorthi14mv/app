document.addEventListener("DOMContentLoaded", function() {
    fetch('/api/insights/charts')
        .then(response => response.json())
        .then(data => {
            if (data.error) return;

            document.getElementById('insightsChartsRow').style.display = 'flex';

            const commonOptions = {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                }
            };

            // Risk Distribution
            new Chart(document.getElementById('riskDistChart'), {
                type: 'pie',
                data: {
                    labels: data.risk_dist.labels,
                    datasets: [{
                        data: data.risk_dist.data,
                        backgroundColor: ['#1cc88a', '#f6c23e', '#e74a3b'] // Low, Medium, High
                    }]
                },
                options: commonOptions
            });

            // High Risk by Segment
            new Chart(document.getElementById('highRiskSegmentChart'), {
                type: 'bar',
                data: {
                    labels: data.high_risk_segments.labels,
                    datasets: [{
                        label: 'High Risk Count',
                        data: data.high_risk_segments.data,
                        backgroundColor: '#e74a3b'
                    }]
                },
                options: {
                    ...commonOptions,
                    scales: { y: { beginAtZero: true } }
                }
            });

            // Risk Factors
            new Chart(document.getElementById('riskFactorsChart'), {
                type: 'polarArea',
                data: {
                    labels: data.risk_factors.labels,
                    datasets: [{
                        label: 'Customers at Risk',
                        data: data.risk_factors.data,
                        backgroundColor: ['#e74a3b', '#f6c23e', '#36b9cc', '#4e73df', '#858796']
                    }]
                },
                options: commonOptions
            });
        })
        .catch(err => console.log('No chart data available yet for insights.'));
});
