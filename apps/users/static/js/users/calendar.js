document.addEventListener('DOMContentLoaded', function () {
    var calendarEl = document.getElementById('calendar');
    if (!calendarEl) return; // Safety check

    // Parse booking dates from Django template
    const bookingEvents = JSON.parse(calendarEl.dataset.bookingEvents || '[]');

    const events = bookingEvents.map(ev => ({
        title: ev.title,
        start: ev.date,
        color: new Date(ev.date) >= new Date() ? '#4caf50' : '#9e9e9e',
        textColor: '#fff',
        extendedProps: {
            description: `${ev.title} - ${ev.city} - ${ev.venue}`
        },
        allDay: false
    }));

    // Initialize FullCalendar
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'pl',
        eventDidMount: function(info) {
            // Add custom attribute for CSS tooltip
            info.el.setAttribute('data-description', info.event.extendedProps.description);
            info.el.style.backgroundColor = '';
            info.el.style.color = '';
        },
        
        // height: 'auto',
        events: events,
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,listMonth'
        },
        contentHeight: 'auto',
        dayMaxEventRows: true, // show multiple events in a day nicely
        navLinks: true          // clickable day/week names
    });

    calendar.render();
});
