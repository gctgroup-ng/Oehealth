// Navigation Management for intarvas Patient Portal
// Handles active navigation state and link management

(function() {
    'use strict';
    
    // Navigation state management
    function updateActiveNavigation() {
        try {
            const currentPath = window.location.pathname;
            if (!currentPath) return;
            
            const navLinks = document.querySelectorAll('.patient-sidebar .nav-link');
            if (!navLinks || navLinks.length === 0) return;
            
            navLinks.forEach(function(link) {
                try {
                    if (!link || !link.classList) return;
                    
                    // Remove active class safely
                    link.classList.remove('active');
                    
                    // Safely check href - this is where the error was occurring
                    if (link && typeof link.href === 'string' && link.href.length > 0) {
                        try {
                            const linkUrl = new URL(link.href);
                            const linkPath = linkUrl.pathname;
                            
                            if (linkPath && typeof linkPath === 'string' && linkPath.length > 0) {
                                if (currentPath === linkPath || 
                                    (currentPath.indexOf(linkPath) === 0 && linkPath !== '/patient/portal' && linkPath.length > 1)) {
                                    link.classList.add('active');
                                }
                            }
                        } catch (urlError) {
                            // Skip invalid URLs
                        }
                    }
                } catch (linkError) {
                    // Skip problematic links
                }
            });
            
            // Special case for home page
            if (currentPath === '/patient/portal' || currentPath === '/patient/portal/') {
                const homeLink = document.querySelector('.patient-sidebar .nav-link[href="/patient/portal"]');
                if (homeLink && homeLink.classList) {
                    homeLink.classList.add('active');
                }
            }
        } catch (error) {
            // Silently handle any navigation errors
        }
    }
    
    // Initialize navigation
    function initializeNavigation() {
        try {
            updateActiveNavigation();
        } catch (error) {
            // Handle initialization errors gracefully
        }
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeNavigation);
    } else {
        initializeNavigation();
    }
    
    // Re-initialize on page changes
    window.addEventListener('popstate', function() {
        setTimeout(initializeNavigation, 100);
    });
    
})();