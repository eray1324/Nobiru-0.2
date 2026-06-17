// ====================================
// NOBIRU - SCRIPT PRINCIPAL
// ====================================

console.log('✅ Nobiru Script cargado correctamente');

// ====================================
// FUNCIONES AUXILIARES
// ====================================

// Mostrar notificación
function mostrarNotificacion(mensaje, tipo = 'exito') {
    const notif = document.createElement('div');
    notif.className = `notificacion notificacion-${tipo}`;
    notif.textContent = mensaje;
    notif.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${tipo === 'exito' ? '#4CAF50' : '#FF6B6B'};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        z-index: 1000;
        animation: slideInRight 0.3s ease-out;
    `;
    
    document.body.appendChild(notif);
    
    setTimeout(() => {
        notif.remove();
    }, 3000);
}

// Cargar datos del usuario
async function cargarDatosUsuario() {
    try {
        const response = await fetch('/api/usuario');
        if (response.ok) {
            const usuario = await response.json();
            return usuario;
        }
    } catch (error) {
        console.error('Error al cargar datos del usuario:', error);
    }
}

// ====================================
// MANEJO DE FORMULARIOS
// ====================================

// Validar email
function validarEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

// ====================================
// EVENT LISTENERS
// ====================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM cargado - Inicializando aplicación');
    
    // Cargar datos del usuario si existe sesión
    cargarDatosUsuario().then(usuario => {
        if (usuario) {
            console.log('Usuario conectado:', usuario.nombre_usuario);
        }
    });
});

// ====================================
// ANIMACIONES
// ====================================

// Agregar animación a elementos cuando entran en vista
const observador = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.animation = 'slideIn 0.3s ease-out';
        }
    });
}, {
    threshold: 0.1
});

// Observar todas las cards
document.querySelectorAll('.card-cuestionario, .post-card, .reel-card, .archivo-card').forEach(card => {
    observador.observe(card);
});

// ====================================
// FUNCIONES DE FAVORITOS
// ====================================

async function agregarFavorito(tipo, itemId) {

    try {

        const response = await fetch('/api/agregar-favorito', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                tipo: tipo,
                item_id: itemId
            })
        });

        const data = await response.json();

        if (data.success) {

            mostrarNotificacion('Agregado a favoritos');

        } else {

            mostrarNotificacion(data.error, 'error');

        }

    } catch (error) {

        mostrarNotificacion('Error al guardar favorito', 'error');

    }

}

async function eliminarFavorito(idFavorito){

    const response = await fetch(
        `/api/eliminar-favorito/${idFavorito}`,
        {
            method:'DELETE'
        }
    );

    const data = await response.json();

    if(data.success){

        mostrarNotificacion('Favorito eliminado');

        location.reload();

    }

}

// ====================================
// EXPONIR FUNCIONES GLOBALES
// ====================================

window.mostrarNotificacion = mostrarNotificacion;
window.agregarFavorito = agregarFavorito;
window.eliminarFavorito = eliminarFavorito;
