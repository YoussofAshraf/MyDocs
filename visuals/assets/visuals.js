// Starts each figure's @keyframes when it scrolls into view, and wires the replay / pause / speed controls.
(function () {
    var figs = Array.prototype.slice.call(document.querySelectorAll('.fig'));

    function restart(fig) {
        fig.classList.remove('play', 'paused');
        void fig.offsetWidth; // force reflow so the animations start again from 0
        fig.classList.add('play');
        var p = fig.querySelector('.pause');
        if (p) p.textContent = '⏸';
    }

    figs.forEach(function (fig) {
        var k = 1;
        try { k = Number(localStorage.getItem('visuals-speed')) || 1; } catch (e) {}
        fig.style.setProperty('--k', k);
        var sel = fig.querySelector('.speed');
        if (sel) sel.value = String(k);

        fig.querySelector('.replay').addEventListener('click', function () { restart(fig); });
        fig.querySelector('.pause').addEventListener('click', function (ev) {
            var paused = fig.classList.toggle('paused');
            ev.currentTarget.textContent = paused ? '▶' : '⏸';
        });
        sel.addEventListener('change', function () {
            fig.style.setProperty('--k', sel.value);
            try { localStorage.setItem('visuals-speed', sel.value); } catch (e) {}
            restart(fig);
        });
    });

    if (!('IntersectionObserver' in window)) return;
    var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
            if (en.isIntersecting) {
                restart(en.target);
                io.unobserve(en.target);
            }
        });
    }, { threshold: 0.25 });
    figs.forEach(function (fig) {
        fig.classList.remove('play');
        io.observe(fig);
    });
})();
