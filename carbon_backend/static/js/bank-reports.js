document.addEventListener('DOMContentLoaded', function() {
    // Initialize report controls
    initializeReportControls();
    
    // Set up HTMX event listeners
    setupHtmxListeners();
    
    // Set up export buttons
    setupExportButtons();
});

/**
 * Initialize report control elements
 */
function initializeReportControls() {
    const reportTypeSelect = document.getElementById('report-type');
    const dateRangeSelect = document.getElementById('date-range');
    const generateBtn = document.getElementById('generate-report-btn');
    
    // Handle report generation button click
    if (generateBtn) {
        generateBtn.addEventListener('click', function() {
            const reportType = reportTypeSelect.value;
            const dateRange = dateRangeSelect.value;
            
            // Update hidden fields in the form
            document.getElementById('report_type_input').value = reportType;
            document.getElementById('date_range_input').value = dateRange;
            
            // Trigger the form submission via HTMX
            document.getElementById('report-form').dispatchEvent(new Event('submit'));
        });
    }
}

/**
 * Set up HTMX event listeners for dynamic content loading
 */
function setupHtmxListeners() {
    // Listen for htmx:afterSwap event to initialize charts after content is loaded
    document.body.addEventListener('htmx:afterSwap', function(event) {
        if (event.detail.target.id === 'report-content') {
            // Initialize charts based on the loaded report type
            initializeCharts();
        }
    });
    
    // Listen for htmx:beforeRequest to show loading indicator
    document.body.addEventListener('htmx:beforeRequest', function(event) {
        document.getElementById('loading-indicator').classList.remove('d-none');
    });
    
    // Listen for htmx:afterRequest to hide loading indicator
    document.body.addEventListener('htmx:afterRequest', function(event) {
        document.getElementById('loading-indicator').classList.add('d-none');
    });
}

/**
 * Initialize charts based on the current report type
 */
function initializeCharts() {
    // Get the current report type
    const reportType = document.getElementById('report_type_input').value;
    
    // Initialize different charts based on report type
    if (reportType === 'summary') {
        createVolumeChart();
        createPriceChart();
    } else if (reportType === 'transactions') {
        createTransactionChart();
    } else if (reportType === 'price') {
        createPriceHistoryChart();
    } else if (reportType === 'employer_activity') {
        createEmployerVolumeChart();
    }
}

/**
 * Create volume over time chart
 */
function createVolumeChart() {
    const ctx = document.getElementById('volume-chart');
    if (!ctx) return;
    
    // Sample data - would be replaced with real data from the backend
    const data = {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
        datasets: [{
            label: 'Trading Volume',
            data: [65, 59, 80, 81, 56, 55, 40],
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 2,
            tension: 0.4
        }]
    };
    
    new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Volume (credits)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Month'
                    }
                }
            }
        }
    });
}

/**
 * Create price trends chart
 */
function createPriceChart() {
    const ctx = document.getElementById('price-chart');
    if (!ctx) return;
    
    // Sample data - would be replaced with real data from the backend
    const data = {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
        datasets: [{
            label: 'Avg. Price',
            data: [12, 19, 18, 16, 15, 17, 20],
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 2,
            tension: 0.4
        }]
    };
    
    new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: 'Price ($)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Month'
                    }
                }
            }
        }
    });
}

/**
 * Create transaction breakdown chart
 */
function createTransactionChart() {
    const ctx = document.getElementById('transaction-chart');
    if (!ctx) return;
    
    // Sample data - would be replaced with real data from the backend
    const data = {
        labels: ['Buy', 'Sell'],
        datasets: [{
            label: 'Transactions',
            data: [12, 19],
            backgroundColor: [
                'rgba(75, 192, 192, 0.7)',
                'rgba(255, 99, 132, 0.7)'
            ],
            borderColor: [
                'rgba(75, 192, 192, 1)',
                'rgba(255, 99, 132, 1)'
            ],
            borderWidth: 1
        }]
    };
    
    new Chart(ctx, {
        type: 'pie',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                }
            }
        }
    });
}

/**
 * Create price history chart
 */
function createPriceHistoryChart() {
    const ctx = document.getElementById('price-history-chart');
    if (!ctx) return;
    
    // Sample data - would be replaced with real data from the backend
    const data = {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        datasets: [{
            label: 'Price',
            data: [10, 12, 11, 13, 14, 15, 16, 17, 16, 15, 17, 18],
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 2,
            tension: 0.1,
            fill: true
        }]
    };
    
    new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `$${context.raw.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    title: {
                        display: true,
                        text: 'Price ($)'
                    },
                    ticks: {
                        callback: function(value) {
                            return '$' + value;
                        }
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Month'
                    }
                }
            }
        }
    });
}

/**
 * Create employer volume chart
 */
function createEmployerVolumeChart() {
    const ctx = document.getElementById('employer-volume-chart');
    if (!ctx) return;
    
    // Sample data - would be replaced with real data from the backend
    const data = {
        labels: ['Employer A', 'Employer B', 'Employer C', 'Employer D', 'Employer E'],
        datasets: [
            {
                label: 'Buy Volume',
                data: [65, 59, 80, 81, 56],
                backgroundColor: 'rgba(75, 192, 192, 0.7)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            },
            {
                label: 'Sell Volume',
                data: [28, 48, 40, 19, 86],
                backgroundColor: 'rgba(255, 99, 132, 0.7)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1
            }
        ]
    };
    
    new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Volume (credits)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Employer'
                    }
                }
            }
        }
    });
}

/**
 * Set up export buttons functionality
 */
function setupExportButtons() {
    const csvExportBtn = document.getElementById('csv-export-btn');
    const pdfExportBtn = document.getElementById('pdf-export-btn');
    
    if (csvExportBtn) {
        csvExportBtn.addEventListener('click', function() {
            exportReport('csv');
        });
    }
    
    if (pdfExportBtn) {
        pdfExportBtn.addEventListener('click', function() {
            exportReport('pdf');
        });
    }
}

/**
 * Export the current report in the specified format
 * @param {string} format - The export format ('csv' or 'pdf')
 */
function exportReport(format) {
    const reportType = document.getElementById('report_type_input').value;
    const dateRange = document.getElementById('date_range_input').value;
    
    if (!reportType || !dateRange) {
        alert('Please generate a report first before exporting.');
        return;
    }
    
    // Construct the export URL
    const exportUrl = `/bank/export-report/${reportType}/${dateRange}/${format}/`;
    
    // Redirect to the export URL or open in a new tab
    window.open(exportUrl, '_blank');
} 