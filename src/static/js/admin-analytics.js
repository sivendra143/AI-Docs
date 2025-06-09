// admin-analytics.js: Animate analytics stat numbers

document.addEventListener('DOMContentLoaded', function() {
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
