// profile-menu.js

function toggleProfileMenu() {
    const dropdown = document.querySelector('.profile-dropdown');
    dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
}

// Close when clicking outside
document.addEventListener('click', function(e) {
    const menu = document.querySelector('.profile-menu');
    if (!menu.contains(e.target)) {
        const dropdown = menu.querySelector('.profile-dropdown');
        if (dropdown) dropdown.style.display = 'none';
    }
});
