/**
 * Admin Reports JavaScript
 * Handles report generation and export functionality
 */
document.addEventListener('DOMContentLoaded', function() {
  // Initialize report form elements
  const reportTypeSelect = document.getElementById('report-type');
  const dateRangeSelect = document.getElementById('date-range');
  const formatSelect = document.getElementById('format');
  const generateButton = document.querySelector('button.btn-primary');

  // Handle export format selection
  if (formatSelect && generateButton) {
    formatSelect.addEventListener('change', function() {
      const format = this.value;
      if (format === 'web') {
        // For web view, use HTMX to update the content
        generateButton.setAttribute('hx-get', '/admin/reports/');
        generateButton.setAttribute('hx-target', '#report-content');
      } else {
        // For export formats, redirect to download endpoint
        generateButton.removeAttribute('hx-get');
        generateButton.removeAttribute('hx-target');
      }
    });

    // Handle generate/export button click
    generateButton.addEventListener('click', function(e) {
      const format = formatSelect.value;
      const reportType = reportTypeSelect.value;
      const dateRange = dateRangeSelect.value;

      // If export format is selected (not web view)
      if (format !== 'web') {
        e.preventDefault();
        e.stopPropagation();
        exportReport(reportType, dateRange, format);
      }
    });
  }

  // Function to handle report export
  function exportReport(reportType, dateRange, format) {
    // Show loading indicator
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) {
      loadingIndicator.style.display = 'flex';
    }

    // Build export URL with query parameters
    const params = new URLSearchParams({
      report_type: reportType,
      date_range: dateRange,
      format: format
    });
    
    const exportUrl = `/admin/reports/export/?${params.toString()}`;
    
    // Initiate download by creating a temporary link
    fetch(exportUrl)
      .then(response => {
        if (!response.ok) {
          throw new Error('Export failed');
        }
        
        // For CSV, get the file from response
        if (format === 'csv') {
          return response.blob();
        } else if (format === 'pdf') {
          return response.blob();
        }
      })
      .then(blob => {
        // Create a download link and click it
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `carbon-credits-${reportType}-report.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      })
      .catch(error => {
        console.error('Export error:', error);
        alert('Failed to export report. Please try again.');
      })
      .finally(() => {
        // Hide loading indicator
        if (loadingIndicator) {
          loadingIndicator.style.display = 'none';
        }
      });
  }

  // Initialize charts if they exist on the page
  initializeCharts();
});

/**
 * Initialize charts for the reports page
 */
function initializeCharts() {
  // Check if Chart.js is available
  if (typeof Chart === 'undefined') {
    console.warn('Chart.js is not loaded');
    return;
  }

  // Trips by Transport Mode chart
  const transportModeCtx = document.getElementById('transport-mode-chart');
  if (transportModeCtx) {
    new Chart(transportModeCtx, {
      type: 'pie',
      data: {
        labels: ['Car', 'Public Transport', 'Bike', 'Walk', 'Carpool'],
        datasets: [{
          data: [30, 25, 20, 15, 10],
          backgroundColor: [
            '#FF6384',
            '#36A2EB',
            '#FFCE56',
            '#4BC0C0',
            '#9966FF'
          ]
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right'
          }
        }
      }
    });
  }

  // Carbon Credits Monthly Trend chart
  const creditsMonthlyCtx = document.getElementById('credits-monthly-chart');
  if (creditsMonthlyCtx) {
    new Chart(creditsMonthlyCtx, {
      type: 'line',
      data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [{
          label: 'Credits Earned',
          data: [120, 190, 300, 250, 420, 380],
          borderColor: '#36A2EB',
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true
          }
        }
      }
    });
  }
} 