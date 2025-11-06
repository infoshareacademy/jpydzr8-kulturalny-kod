<script>
  (function () {
    const buttons = document.querySelectorAll('.filters .btn');
    const items   = document.querySelectorAll('.booking-item');

    function applyFilter(value) {
      items.forEach(el => {
        const st = el.getAttribute('data-status');
        el.style.display = (value === 'all' || st === value) ? '' : 'none';
      });
      buttons.forEach(b => b.classList.toggle('active', b.dataset.filter === value));
    }

    // Przy inicjalizacji – respektuj ?status=...
    const url = new URL(window.location.href);
    const current = url.searchParams.get('status') || 'all';
    applyFilter(current);

    // Klik bez przeładowania, ale z aktualizacją adresu
    buttons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const val = btn.dataset.filter || 'all';
        applyFilter(val);
        url.searchParams.set('status', val);
        window.history.replaceState({}, '', url);
      });
    });
  })();
</script>
