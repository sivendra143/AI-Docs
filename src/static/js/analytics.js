
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

