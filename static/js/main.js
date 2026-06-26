// JavaScript adicional para el sistema

// Confirmar eliminación con SweetAlert
function confirmarEliminacion(url) {
    if (confirm('¿Está seguro de eliminar este registro? Esta acción no se puede deshacer.')) {
        window.location.href = url;
    }
}

// Auto-cálculo de puntaje total en tiempo real
document.addEventListener('DOMContentLoaded', function() {
    // Para la página de calificaciones
    const calificaciones = document.querySelectorAll('.calificacion');
    calificaciones.forEach(input => {
        input.addEventListener('input', function() {
            const row = this.closest('tr');
            const jurado1 = parseFloat(row.querySelector('[name="jurado1"]').value) || 0;
            const jurado2 = parseFloat(row.querySelector('[name="jurado2"]').value) || 0;
            const jurado3 = parseFloat(row.querySelector('[name="jurado3"]').value) || 0;
            const total = jurado1 + jurado2 + jurado3;
            const totalSpan = row.querySelector('.puntaje-total');
            if (totalSpan) {
                totalSpan.textContent = total.toFixed(2);
            }
        });
    });
});

// Función para imprimir reporte
function imprimirReporte() {
    window.print();
}

// Función para refrescar datos
function refrescarPagina() {
    location.reload();
}

// Validación de campos numéricos
function validarNumero(input) {
    const valor = parseFloat(input.value);
    if (isNaN(valor) || valor < 0 || valor > 10) {
        input.classList.add('is-invalid');
        return false;
    } else {
        input.classList.remove('is-invalid');
        return true;
    }
}

// Agregar validación a campos de calificación
document.addEventListener('DOMContentLoaded', function() {
    const inputsCalificacion = document.querySelectorAll('input[type="number"]');
    inputsCalificacion.forEach(input => {
        input.addEventListener('blur', function() {
            validarNumero(this);
        });
    });
});