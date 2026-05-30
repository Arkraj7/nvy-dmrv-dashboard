/**
 * UI Enhancements for Nagar Van DMRV Dashboard
 * - Scroll Progress Bar
 * - Intersection Observer for Scroll Animations
 * - Number Counting Animation for Metrics
 */

(function() {
    'use strict';

    // Initialize UI Enhancements
    function init() {
        createScrollProgressBar();
        setupScrollAnimations();
        setupNumberCounting();
        enhanceInteractiveElements();
    }

    // 1. Scroll Progress Bar
    function createScrollProgressBar() {
        const bar = document.createElement('div');
        bar.id = 'scroll-progress-bar';
        Object.assign(bar.style, {
            position: 'fixed',
            top: '0',
            left: '0',
            height: '4px',
            backgroundColor: '#5dc48a',
            zIndex: '10000',
            width: '0%',
            transition: 'width 0.1s ease-out'
        });
        document.body.appendChild(bar);

        window.addEventListener('scroll', () => {
            const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
            const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
            const scrolled = (winScroll / height) * 100;
            bar.style.width = scrolled + '%';
        });
    }

    // 2. Intersection Observer for Scroll Animations
    function setupScrollAnimations() {
        const options = {
            threshold: 0.1
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    observer.unobserve(entry.target);
                }
            });
        }, options);

        // Add 'reveal' class to sections and panels
        const targets = document.querySelectorAll('.glass-panel, section, .metric-card');
        targets.forEach(target => {
            target.classList.add('reveal-hidden');
            observer.observe(target);
        });

        // Add necessary CSS for reveal
        const style = document.createElement('style');
        style.innerHTML = `
            .reveal-hidden {
                opacity: 0;
                transform: translateY(30px);
                transition: opacity 0.8s ease-out, transform 0.8s ease-out;
            }
            .reveal-hidden.animate-in {
                opacity: 1;
                transform: translateY(0);
            }
        `;
        document.head.appendChild(style);
    }

    // 3. Number Counting Animation
    function setupNumberCounting() {
        const metrics = [
            { id: 'metric-aqi', target: 42, suffix: '' },
            { id: 'metric-carbon', target: 1240, suffix: '' },
            { id: 'metric-water', target: 45, suffix: 'k' },
            { id: 'metric-eco', target: 7.8, suffix: '', decimals: 1 },
            { id: 'metric-heat', target: -2.4, suffix: '°C', decimals: 1 },
            { id: 'metric-wtp', target: 25, prefix: '₹', suffix: '/ mo' }
        ];

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const metric = metrics.find(m => m.id === entry.target.id);
                    if (metric) {
                        animateValue(entry.target, 0, metric.target, 2000, metric.suffix, metric.decimals || 0, metric.prefix || '');
                        observer.unobserve(entry.target);
                    }
                }
            });
        }, { threshold: 0.5 });

        metrics.forEach(m => {
            const el = document.getElementById(m.id);
            if (el) observer.observe(el);
        });
    }

    function animateValue(obj, start, end, duration, suffix, decimals, prefix = '') {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const value = (progress * (end - start) + start).toFixed(decimals);
            obj.innerHTML = prefix + value + suffix;
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }

    // 4. Enhance Interactive Elements
    function enhanceInteractiveElements() {
        const buttons = document.querySelectorAll('button, .btn-hover-effect');
        buttons.forEach(btn => {
            btn.addEventListener('mousedown', () => {
                btn.style.transform = 'scale(0.95)';
            });
            btn.addEventListener('mouseup', () => {
                btn.style.transform = 'scale(1)';
            });
            btn.addEventListener('mouseleave', () => {
                btn.style.transform = 'scale(1)';
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
