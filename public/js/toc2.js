(function () {
    'use strict';

    function init() {
        var main = document.getElementById('main') || document.getElementById('job-content') || document.querySelector('main');
        if (!main) return;

        var headings = Array.prototype.slice.call(main.querySelectorAll('h2'));
        if (headings.length < 3) return;

        // Reading time
        var text = main.innerText || '';
        var words = text.trim().split(/\s+/).length;
        var minutes = Math.max(1, Math.round(words / 200));

        // Insert reading time badge
        var hero = main.querySelector('.hub-hero, .job-page-hero');
        if (hero) {
            var badge = document.createElement('p');
            badge.className = 'reading-time';
            badge.textContent = minutes + ' min read';
            hero.appendChild(badge);
        }

        // Build TOC
        var toc = document.createElement('nav');
        toc.className = 'toc';
        toc.setAttribute('aria-label', 'Table of contents');
        var tocTitle = document.createElement('p');
        tocTitle.className = 'toc-title';
        tocTitle.textContent = 'On this page';
        toc.appendChild(tocTitle);
        var ul = document.createElement('ul');
        headings.forEach(function (h, i) {
            if (!h.id) h.id = 'section-' + (i + 1);
            var li = document.createElement('li');
            var a = document.createElement('a');
            a.href = '#' + h.id;
            a.textContent = h.textContent;
            li.appendChild(a);
            ul.appendChild(li);
        });
        toc.appendChild(ul);

        // Insert TOC after hero
        if (hero && hero.parentNode) {
            hero.parentNode.insertBefore(toc, hero.nextSibling);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

/* v2 */
