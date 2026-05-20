document.addEventListener('DOMContentLoaded', function() {

    const phoneInputs = document.querySelectorAll('input[type="text"][placeholder*="+7"]');
    phoneInputs.forEach(function(input) {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/[^\d+]/g, '');
            if (!value.startsWith('+')) {
                value = '+' + value;
            }
            if (value.length > 12) {
                value = value.substring(0, 12);
            }
            e.target.value = value;
        });
    });

    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let valid = true;
            requiredFields.forEach(function(field) {
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    valid = false;
                } else {
                    field.classList.remove('is-invalid');
                }
            });
        });
    });

    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});