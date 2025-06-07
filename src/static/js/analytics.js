// analytics.js - Admin analytics functionality

document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the admin page
    const adminPanel = document.getElementById('admin-panel');
    if (!adminPanel) return;
    
    // Get token from localStorage
    const token = localStorage.getItem('auth_token');
    if (!token) {
        window.location.href = '/login.html';
        return;
    }
    
    // Fetch analytics data
    fetchAnalytics(token);
    
    // Set up refresh button
    const refreshBtn = document.getElementById('refresh-analytics');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            fetchAnalytics(token);
        });
    }
});

function fetchAnalytics(token) {
    const analyticsContainer = document.getElementById('analytics-data');
    const loadingIndicator = document.getElementById('loading-indicator');
    
    if (loadingIndicator) loadingIndicator.style.display = 'block';
    if (analyticsContainer) analyticsContainer.innerHTML = '';
    
    fetch('/api/analytics', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                localStorage.removeItem('auth_token');
                window.location.href = '/login.html';
                throw new Error('Authentication failed');
            }
            throw new Error('Failed to fetch analytics');
        }
        return response.json();
    })
    .then(data => {
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        displayAnalytics(data);
    })
    .catch(error => {
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        if (analyticsContainer) {
            analyticsContainer.innerHTML = `<div class="error-message">${error.message}</div>`;
        }
        console.error('Error:', error);
    });
}

function displayAnalytics(data) {
    const analyticsContainer = document.getElementById('analytics-data');
    if (!analyticsContainer) return;
    
    // Create summary section
    const summary = document.createElement('div');
    summary.className = 'analytics-summary';
    summary.innerHTML = `
        <div class="analytics-card">
            <h3>Total Queries</h3>
            <p class="analytics-number">${data.total_queries}</p>
        </div>
        <div class="analytics-card">
            <h3>Successful Queries</h3>
            <p class="analytics-number">${data.successful_queries}</p>
        </div>
        <div class="analytics-card">
            <h3>Failed Queries</h3>
            <p class="analytics-number">${data.failed_queries}</p>
        </div>
    `;
    analyticsContainer.appendChild(summary);
    
    // Create top queries section
    const topQueries = document.createElement('div');
    topQueries.className = 'analytics-section';
    topQueries.innerHTML = '<h3>Top Queries</h3>';
    
    const topQueriesList = document.createElement('ul');
    topQueriesList.className = 'top-queries-list';
    
    // Sort queries by count
    const sortedQueries = Object.entries(data.top_queries)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10); // Top 10
    
    if (sortedQueries.length > 0) {
        sortedQueries.forEach(([query, count]) => {
            const item = document.createElement('li');
            item.innerHTML = `<span class="query-text">${escapeHtml(query)}</span> <span class="query-count">${count}</span>`;
            topQueriesList.appendChild(item);
        });
    } else {
        topQueriesList.innerHTML = '<li>No queries yet</li>';
    }
    
    topQueries.appendChild(topQueriesList);
    analyticsContainer.appendChild(topQueries);
    
    // Create recent queries section
    const recentQueries = document.createElement('div');
    recentQueries.className = 'analytics-section';
    recentQueries.innerHTML = '<h3>Recent Queries</h3>';
    
    const recentQueriesTable = document.createElement('table');
    recentQueriesTable.className = 'recent-queries-table';
    recentQueriesTable.innerHTML = `
        <thead>
            <tr>
                <th>Query</th>
                <th>Time</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
        </tbody>
    `;
    
    const tableBody = recentQueriesTable.querySelector('tbody');
    
    // Get last 20 queries in reverse chronological order
    const recentQueriesList = [...data.queries]
        .reverse()
        .slice(0, 20);
    
    if (recentQueriesList.length > 0) {
        recentQueriesList.forEach(query => {
            const row = document.createElement('tr');
            const timestamp = new Date(query.timestamp).toLocaleString();
            const statusClass = query.success ? 'success' : 'failure';
            
            row.innerHTML = `
                <td>${escapeHtml(query.question)}</td>
                <td>${timestamp}</td>
                <td><span class="status ${statusClass}">${query.success ? 'Success' : 'Failed'}</span></td>
            `;
            tableBody.appendChild(row);
        });
    } else {
        tableBody.innerHTML = '<tr><td colspan="3">No recent queries</td></tr>';
    }
    
    recentQueries.appendChild(recentQueriesTable);
    analyticsContainer.appendChild(recentQueries);
}

// Helper function to escape HTML
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

