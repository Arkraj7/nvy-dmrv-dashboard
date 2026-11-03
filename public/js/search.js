(function () {
    'use strict';

    var jobs = [];
    var filtered = [];

    var qInput = document.getElementById('q');
    var catSel = document.getElementById('f-category');
    var citySel = document.getElementById('f-city');
    var expSel = document.getElementById('f-experience');
    var typeSel = document.getElementById('f-type');
    var countEl = document.getElementById('search-count');
    var resultsEl = document.getElementById('search-results');

    function esc(s) { return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }

    function jobUrl(j) { return '/jobs/' + (j.id || ''); }

    function card(j) {
        var cat = j.category || 'Other';
        var pt = j.position_type || 'Role';
        var state = j.state || j.country || '';
        var org = j.organization || 'Organisation not specified';
        var city = j.city || '';
        var title = j.clean_title || j.title || 'Untitled';
        var skills = (j.must_have_skills || []).slice(0, 3).map(function (s) { return '<span class="badge badge-type">' + esc(s) + '</span>'; }).join('');
        return '<article class="hub-card">' +
            '<div class="hub-card-top">' +
            '<span class="badge badge-cat">' + esc(cat) + '</span>' +
            '<span class="badge badge-type">' + esc(pt) + '</span>' +
            '</div>' +
            '<h3 class="hub-card-title"><a href="' + jobUrl(j) + '">' + esc(title.length > 68 ? title.slice(0, 67) + '\u2026' : title) + '</a></h3>' +
            '<p class="hub-card-org">' + esc(org) + (city && city.toLowerCase() !== org.toLowerCase() ? ' \u00b7 ' + esc(city) : '') + '</p>' +
            (skills ? '<div class="hub-card-skills">' + skills + '</div>' : '') +
            '<p class="hub-card-foot"><span>View details &rarr;</span></p>' +
            '</article>';
    }

    function matches(j, query) {
        if (!query) return true;
        var hay = [j.clean_title, j.title, j.organization, j.city, j.state, j.category, j.position_type, j.role_summary, j.qualification_summary, (j.must_have_skills || []).join(' ')].join(' ').toLowerCase();
        var terms = query.toLowerCase().split(/\s+/).filter(function (t) { return t.length > 0; });
        return terms.every(function (t) { return hay.indexOf(t) !== -1; });
    }

    function applyFilters() {
        var query = qInput.value.trim();
        var cat = catSel.value;
        var city = citySel.value;
        var exp = expSel.value;
        var type = typeSel.value;

        filtered = jobs.filter(function (j) {
            if (!matches(j, query)) return false;
            if (cat && j.category !== cat) return false;
            if (city && j.city !== city && j.state !== city) return false;
            if (exp && j.experience_level !== exp) return false;
            if (type === 'india' && j._registry !== 'india') return false;
            if (type === 'global' && j._registry !== 'global') return false;
            return true;
        });

        // sort by deadline
        filtered.sort(function (a, b) {
            var da = a.valid_through || '9999-12-31';
            var db = b.valid_through || '9999-12-31';
            return da < db ? -1 : da > db ? 1 : 0;
        });

        render();
        updateUrl();
    }

    function render() {
        countEl.textContent = filtered.length + ' result' + (filtered.length === 1 ? '' : 's') + ' found';
        if (filtered.length === 0) {
            resultsEl.innerHTML = '<div class="search-empty"><p>No jobs match your search. Try different keywords or clear the filters.</p></div>';
            return;
        }
        resultsEl.innerHTML = filtered.slice(0, 60).map(card).join('');
        if (filtered.length > 60) {
            resultsEl.innerHTML += '<div class="search-empty"><p>Showing first 60 of ' + filtered.length + ' results. Narrow your search for more.</p></div>';
        }
    }

    function updateUrl() {
        var params = new URLSearchParams();
        if (qInput.value.trim()) params.set('q', qInput.value.trim());
        if (catSel.value) params.set('cat', catSel.value);
        if (citySel.value) params.set('city', citySel.value);
        if (expSel.value) params.set('exp', expSel.value);
        if (typeSel.value) params.set('type', typeSel.value);
        var qs = params.toString();
        history.replaceState(null, '', qs ? '/search?' + qs : '/search');
    }

    function populateFilters() {
        var cats = {}, cities = {}, exps = {};
        jobs.forEach(function (j) {
            if (j.category) cats[j.category] = true;
            if (j.city) cities[j.city] = true;
            if (j.experience_level) exps[j.experience_level] = true;
        });
        Object.keys(cats).sort().forEach(function (c) {
            var o = document.createElement('option');
            o.value = c; o.textContent = c;
            catSel.appendChild(o);
        });
        Object.keys(cities).sort().forEach(function (c) {
            var o = document.createElement('option');
            o.value = c; o.textContent = c;
            citySel.appendChild(o);
        });
        Object.keys(exps).sort().forEach(function (e) {
            var o = document.createElement('option');
            o.value = e; o.textContent = e;
            expSel.appendChild(o);
        });
    }

    function loadFromUrl() {
        var params = new URLSearchParams(window.location.search);
        if (params.get('q')) qInput.value = params.get('q');
        if (params.get('cat')) catSel.value = params.get('cat');
        if (params.get('city')) citySel.value = params.get('city');
        if (params.get('exp')) expSel.value = params.get('exp');
        if (params.get('type')) typeSel.value = params.get('type');
    }

    // Debounce
    var timer = null;
    qInput.addEventListener('input', function () {
        clearTimeout(timer);
        timer = setTimeout(applyFilters, 200);
    });
    catSel.addEventListener('change', applyFilters);
    citySel.addEventListener('change', applyFilters);
    expSel.addEventListener('change', applyFilters);
    typeSel.addEventListener('change', applyFilters);

    // Load data
    countEl.textContent = 'Loading jobs...';
    Promise.all([
        fetch('/jobs.json').then(function (r) { return r.json(); }),
        fetch('/global_jobs.json').then(function (r) { return r.json(); })
    ]).then(function (results) {
        var india = results[0] || [];
        var global = results[1] || [];
        india.forEach(function (j) { j._registry = 'india'; });
        global.forEach(function (j) { j._registry = 'global'; });
        jobs = india.concat(global);
        populateFilters();
        loadFromUrl();
        applyFilters();
    }).catch(function (err) {
        countEl.textContent = 'Failed to load jobs. Please refresh.';
        console.error(err);
    });
})();
