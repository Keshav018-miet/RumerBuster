document.addEventListener('DOMContentLoaded', () => {
    // Theme Toggle Handler
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    const themeToggleIcon = document.getElementById('themeToggleIcon');

    function updateThemeUI(theme) {
        if (themeToggleIcon) {
            themeToggleIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
        }
        if (themeToggleBtn) {
            themeToggleBtn.setAttribute('title', theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode');
            themeToggleBtn.setAttribute('aria-label', theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode');
        }
    }

    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    updateThemeUI(currentTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const activeTheme = document.documentElement.getAttribute('data-theme') || 'light';
            const newTheme = activeTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('rumorbuster_theme', newTheme);
            updateThemeUI(newTheme);
        });
    }

    const uploadForms = document.querySelectorAll('form[enctype="multipart/form-data"]');
    uploadForms.forEach(form => {
        form.addEventListener('submit', function() {
            const btn = this.querySelector('button[type="submit"]');
            if (btn) {
                btn.innerHTML = 'Processing... <span class="spinner"></span>';
                btn.disabled = true;
                
                setTimeout(() => {
                    this.submit();
                }, 50);
            }
        });
    });

    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const label = this.nextElementSibling;
            if (label && label.classList.contains('file-label')) {
                if (this.files && this.files.length > 1) {
                    label.innerHTML = (this.getAttribute('data-multiple-caption') || '').replace('{count}', this.files.length);
                } else if (this.files && this.files[0]) {
                    label.innerHTML = this.files[0].name;
                }
            }
        });
    });
});
