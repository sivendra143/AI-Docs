// admin-analytics.js: Admin interface enhancements including button styling and animations

document.addEventListener('DOMContentLoaded', function() {
    // Dark mode detection
    function isDarkMode() {
        const htmlElement = document.documentElement;
        return htmlElement.classList.contains('dark') || 
               htmlElement.getAttribute('data-theme') === 'dark' ||
               (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches &&
               localStorage.getItem('theme') === 'system');
    }
    
    // Apply styling to action buttons - both standard and admin-specific
    const styleActionButtons = () => {
        // Target multiple button classes for consistent styling
        const actionButtons = document.querySelectorAll('.admin-action-btn, .action-btn, .btn-primary, .btn-secondary, .btn-danger');
        
        actionButtons.forEach(btn => {
            // Skip if already styled
            if (btn.dataset.styled) return;
            
            // Add base styles directly for consistency
            btn.style.transition = 'all 0.2s ease';
            btn.style.cursor = 'pointer';
            btn.style.outline = 'none';
            btn.style.fontWeight = '500';
            
            // Default styles based on button type
            const isDanger = btn.classList.contains('btn-danger');
            const isPrimary = btn.classList.contains('btn-primary');
            const isSecondary = btn.classList.contains('btn-secondary');
            
            // Set base styles according to button type
            if (isDanger) {
                btn.style.backgroundColor = isDarkMode() ? '#b91c1c' : '#ef4444';
                btn.style.color = 'white';
            } else if (isPrimary) {
                btn.style.backgroundColor = isDarkMode() ? '#1d4ed8' : '#3b82f6';
                btn.style.color = 'white';
            } else if (isSecondary) {
                btn.style.backgroundColor = isDarkMode() ? '#4b5563' : '#e5e7eb';
                btn.style.color = isDarkMode() ? 'white' : '#1f2937';
            }
            
            // Add hover styles with event listeners
            btn.addEventListener('mouseenter', () => {
                btn.style.transform = 'translateY(-2px) scale(1.02)';
                btn.style.boxShadow = isDarkMode() ? 
                    '0 4px 12px rgba(0,0,0,0.4)' : 
                    '0 4px 12px rgba(0,0,0,0.15)';
                
                // Change hover background color based on button type
                if (isDanger) {
                    btn.style.backgroundColor = isDarkMode() ? '#991b1b' : '#dc2626';
                } else if (isPrimary) {
                    btn.style.backgroundColor = isDarkMode() ? '#1e40af' : '#2563eb';
                } else if (isSecondary) {
                    btn.style.backgroundColor = isDarkMode() ? '#374151' : '#d1d5db';
                }
            });
            
            btn.addEventListener('mouseleave', () => {
                btn.style.transform = 'translateY(0) scale(1)';
                btn.style.boxShadow = isDarkMode() ? 
                    '0 1px 3px rgba(0,0,0,0.3)' : 
                    '0 1px 3px rgba(0,0,0,0.1)';
                
                // Reset to original color
                if (isDanger) {
                    btn.style.backgroundColor = isDarkMode() ? '#b91c1c' : '#ef4444';
                } else if (isPrimary) {
                    btn.style.backgroundColor = isDarkMode() ? '#1d4ed8' : '#3b82f6';
                } else if (isSecondary) {
                    btn.style.backgroundColor = isDarkMode() ? '#4b5563' : '#e5e7eb';
                }
            });
            
            // Add active/click effect
            btn.addEventListener('mousedown', () => {
                btn.style.transform = 'translateY(1px) scale(0.98)';
                btn.style.boxShadow = isDarkMode() ? 
                    '0 1px 2px rgba(0,0,0,0.4)' : 
                    '0 1px 2px rgba(0,0,0,0.15)';
            });
            
            btn.addEventListener('mouseup', () => {
                btn.style.transform = 'translateY(-1px) scale(1)';
            });
            
            // Mark as styled
            btn.dataset.styled = 'true';
        });
    };
    
    // Listen for theme changes to update button styling
    window.addEventListener('themeChanged', () => {
        setTimeout(styleActionButtons, 100);
    });
    
    // Call once on load
    styleActionButtons();
    
    // Set up MutationObserver to monitor DOM changes
    const buttonObserver = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'childList' && mutation.addedNodes.length) {
                setTimeout(styleActionButtons, 100);
            }
        });
    });
    
    // Start observing tables that will have action buttons
    const userList = document.getElementById('user-list');
    const docList = document.getElementById('document-list');
    
    if (userList) {
        buttonObserver.observe(userList, { childList: true, subtree: true });
    }
    
    if (docList) {
        buttonObserver.observe(docList, { childList: true, subtree: true });
    }

    // Helper: animate count up
    function animateCountUp(element, endValue, duration = 900) {
        const startValue = 0;
        const increment = Math.ceil(endValue / (duration / 18));
        let current = startValue;
        element.textContent = '0';
        const timer = setInterval(() => {
            current += increment;
            if (current >= endValue) {
                element.textContent = endValue;
                clearInterval(timer);
            } else {
                element.textContent = current;
            }
        }, 18);
    }

    // Wait for stats to be filled in by backend JS
    function animateStatsIfReady() {
        const users = document.getElementById('stat-users');
        const docs = document.getElementById('stat-docs');
        const conv = document.getElementById('stat-conv');
        const msgs = document.getElementById('stat-msgs');
        if (!users || !docs || !conv || !msgs) return;
        // Only animate if numbers are present and not already animated
        if ([users, docs, conv, msgs].some(el => el.dataset.animated)) return;
        const vals = [users, docs, conv, msgs].map(el => parseInt(el.textContent, 10));
        if (vals.some(isNaN)) return;
        [users, docs, conv, msgs].forEach((el, i) => {
            el.dataset.animated = '1';
            animateCountUp(el, vals[i]);
        });
    }
    // Observe changes to stats
    const observer = new MutationObserver(animateStatsIfReady);
    ['stat-users','stat-docs','stat-conv','stat-msgs'].forEach(id => {
        const el = document.getElementById(id);
        if (el) observer.observe(el, { childList: true });
    });
    // Try once on load too
    setTimeout(animateStatsIfReady, 400);
});
