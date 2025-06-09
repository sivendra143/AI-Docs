// theme.js - Dark/light theme toggle functionality

document.addEventListener('DOMContentLoaded', function() {
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const htmlElement = document.documentElement;
    
    // Check for saved theme preference or use system preference
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Set initial theme
    if (savedTheme) {
        htmlElement.setAttribute('data-theme', savedTheme);
    } else {
        const initialTheme = systemPrefersDark ? 'dark' : 'light';
        htmlElement.setAttribute('data-theme', initialTheme);
        localStorage.setItem('theme', initialTheme);
    }
    
    // Toggle theme when button is clicked
    themeToggleBtn.addEventListener('click', function() {
        const currentTheme = htmlElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        htmlElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Update button appearance
        updateThemeButtonAppearance(newTheme);
    });
    
    // Update button appearance based on current theme
    function updateThemeButtonAppearance(theme) {
        const lightIcon = themeToggleBtn.querySelector('.light-icon');
        const darkIcon = themeToggleBtn.querySelector('.dark-icon');
        
        // Show the icon for the theme you can switch to
        if (theme === 'dark') {
            lightIcon.style.display = 'inline';  // ☀️ sun to switch to light
            darkIcon.style.display = 'none';
        } else {
            lightIcon.style.display = 'none';
            darkIcon.style.display = 'inline';  // 🌙 moon to switch to dark
        }
    }
    
    // Initialize button appearance
    updateThemeButtonAppearance(htmlElement.getAttribute('data-theme'));
});

