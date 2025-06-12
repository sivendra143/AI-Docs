// theme.js - Dark/light theme toggle functionality

document.addEventListener('DOMContentLoaded', function() {
    const htmlElement = document.documentElement;
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const themeSelect = document.getElementById('theme-select');
    
    // Get theme from localStorage or use system default
    const savedTheme = localStorage.getItem('theme') || 'system';
    
    // Helper: Set theme globally and save preference
    function setTheme(theme) {
        // Save to localStorage
        localStorage.setItem('theme', theme);
        
        if (theme === 'dark') {
            htmlElement.setAttribute('data-theme', 'dark');
            htmlElement.classList.add('dark');
        } else if (theme === 'light') {
            htmlElement.setAttribute('data-theme', 'light');
            htmlElement.classList.remove('dark');
        } else if (theme === 'system') {
            // Use system preference
            const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            const systemTheme = systemPrefersDark ? 'dark' : 'light';
            
            htmlElement.setAttribute('data-theme', systemTheme);
            if (systemPrefersDark) {
                htmlElement.classList.add('dark');
            } else {
                htmlElement.classList.remove('dark');
            }
        }
        
        // Update button appearance if it exists
        updateThemeButtonAppearance();
        
        // Update select dropdown if it exists
        if (themeSelect) {
            themeSelect.value = theme;
        }
    }
    
    // Update theme toggle button appearance
    function updateThemeButtonAppearance() {
        if (!themeToggleBtn) return;
        
        const lightIcon = themeToggleBtn.querySelector('.light-icon');
        const darkIcon = themeToggleBtn.querySelector('.dark-icon');
        const currentTheme = htmlElement.getAttribute('data-theme');
        
        // Show the icon for the opposite theme (what you can switch to)
        if (currentTheme === 'dark') {
            if (lightIcon) lightIcon.style.display = 'inline';
            if (darkIcon) darkIcon.style.display = 'none';
        } else {
            if (lightIcon) lightIcon.style.display = 'none';
            if (darkIcon) darkIcon.style.display = 'inline';
        }
    }
    
    // Apply saved theme on page load
    setTheme(savedTheme);
    
    // Toggle theme when button is clicked
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function() {
            const currentTheme = htmlElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            setTheme(newTheme);
        });
    }
    
    // Handle theme dropdown changes
    if (themeSelect) {
        themeSelect.addEventListener('change', function() {
            setTheme(this.value);
        });
    }
    
    // Listen for system preference changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (localStorage.getItem('theme') === 'system') {
            setTheme('system');
        }
    });
    
    // Sidebar toggle (for chat interface)
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    const closeSidebar = document.getElementById('close-sidebar');
    
    if (sidebarToggle && sidebar && mainContent) {
        // Check localStorage for sidebar state
        const sidebarOpen = localStorage.getItem('sidebar-open') !== 'false';
        
        // Set initial state
        if (!sidebarOpen) {
            sidebar.classList.add('collapsed');
            mainContent.classList.add('expanded');
        }
        
        // Toggle sidebar
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('expanded');
            localStorage.setItem('sidebar-open', !sidebar.classList.contains('collapsed'));
        });
        
        // Close sidebar button (mobile)
        if (closeSidebar) {
            closeSidebar.addEventListener('click', () => {
                sidebar.classList.add('collapsed');
                mainContent.classList.add('expanded');
                localStorage.setItem('sidebar-open', false);
            });
        }
    }
    
    // Help modal toggle
    const helpBtn = document.getElementById('help-btn');
    const helpModal = document.getElementById('help-modal');
    const closeHelpModal = document.getElementById('close-help-modal');
    
    if (helpBtn && helpModal) {
        helpBtn.addEventListener('click', () => {
            helpModal.style.display = 'flex';
        });
        
        if (closeHelpModal) {
            closeHelpModal.addEventListener('click', () => {
                helpModal.style.display = 'none';
            });
        }
        
        // Close on click outside
        helpModal.addEventListener('click', (e) => {
            if (e.target === helpModal) {
                helpModal.style.display = 'none';
            }
        });
        
        // Close on Esc key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && helpModal.style.display === 'flex') {
                helpModal.style.display = 'none';
            }
        });
    }
});
