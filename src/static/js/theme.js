// theme.js - Dark/light theme toggle functionality

// theme.js - Enhanced global dark/light theme toggle for all pages

document.addEventListener('DOMContentLoaded', function() {
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const htmlElement = document.documentElement;

    // Helper: Set theme globally and dispatch event for other scripts
    function setTheme(theme) {
        htmlElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        // Dispatch a custom event so other scripts can react
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));
    }

    // Check for saved theme preference or use system preference
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    // Set initial theme
    if (savedTheme) {
        setTheme(savedTheme);
    } else {
        const initialTheme = systemPrefersDark ? 'dark' : 'light';
        setTheme(initialTheme);
    }

    // Toggle theme when button is clicked
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function() {
            const currentTheme = htmlElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            setTheme(newTheme);
            updateThemeButtonAppearance(newTheme);
        });
    }

    // Update button appearance based on current theme
    function updateThemeButtonAppearance(theme) {
        if (!themeToggleBtn) return;
        const lightIcon = themeToggleBtn.querySelector('.light-icon');
        const darkIcon = themeToggleBtn.querySelector('.dark-icon');
        // Show the icon for the theme you can switch to
        if (theme === 'dark') {
            lightIcon && (lightIcon.style.display = 'inline');  // ☀️ sun to switch to light
            darkIcon && (darkIcon.style.display = 'none');
        } else {
            lightIcon && (lightIcon.style.display = 'none');
            darkIcon && (darkIcon.style.display = 'inline');  // 🌙 moon to switch to dark
        }
    }

    // Initialize button appearance
    updateThemeButtonAppearance(htmlElement.getAttribute('data-theme'));

    // Listen for system preference changes and update theme
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        const systemTheme = e.matches ? 'dark' : 'light';
        setTheme(systemTheme);
        updateThemeButtonAppearance(systemTheme);
    });
});


