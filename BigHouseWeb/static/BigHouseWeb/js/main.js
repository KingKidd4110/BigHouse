document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('theme-toggle');
    const htmlElement = document.documentElement;
            
            // Check for saved theme preference or use OS preference
    const savedTheme = localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
            
    if (savedTheme === 'dark') {
        htmlElement.classList.add('dark');
        themeToggle.checked = true;
    } else {
        htmlElement.classList.remove('dark');
        themeToggle.checked = false;
    }
            
            // Listen for toggle changes
    themeToggle.addEventListener('change', function() {
        if (this.checked) {
            htmlElement.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        } else {
            htmlElement.classList.remove('dark');
            localStorage.setItem('theme', 'light');
        }
    });
});
