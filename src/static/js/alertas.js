// Función para mostrar alerta de éxito
function mostrarAlertaGuardado() {
    Swal.fire({
        title: "¡Éxito!",
        text: "Los datos se guardaron correctamente.",
        icon: "success",
        confirmButtonText: "OK"
    }).then(() => {
        location.reload();
    });
}

// Función para mostrar alerta de error
function mostrarAlertaError(mensaje) {
    Swal.fire({
        title: "Error",
        text: mensaje || "Ocurrió un error al guardar los datos.",
        icon: "error",
        confirmButtonText: "Intentar de nuevo"
    });
}

// Función genérica para manejar acciones con confirmación
function manejarAccionConfirmada(selector, config) {
    // Configuración por defecto
    const defaults = {
        title: '¿Confirmar acción?',
        text: '¿Estás seguro de realizar esta acción?',
        icon: 'question',
        confirmButtonText: 'Sí, continuar',
        cancelButtonText: 'Cancelar',
        confirmColor: '#3085d6',
        cancelColor: '#d33'
    };
    
    const options = {...defaults, ...config};
    
    // Configuración para elementos existentes
    document.querySelectorAll(selector).forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const url = this.getAttribute('href') || this.getAttribute('data-url');
            
            Swal.fire({
                title: options.title,
                text: options.text,
                icon: options.icon,
                showCancelButton: true,
                confirmButtonColor: options.confirmColor,
                cancelButtonColor: options.cancelColor,
                confirmButtonText: options.confirmButtonText,
                cancelButtonText: options.cancelButtonText
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = url;
                }
            });
        });
    });
    
    // Delegación de eventos para contenido dinámico
    document.body.addEventListener('click', function(e) {
        if (e.target && e.target.closest(selector)) {
            e.preventDefault();
            const btn = e.target.closest(selector);
            const url = btn.getAttribute('href') || btn.getAttribute('data-url');
            
            Swal.fire({
                title: options.title,
                text: options.text,
                icon: options.icon,
                showCancelButton: true,
                confirmButtonColor: options.confirmColor,
                cancelButtonColor: options.cancelColor,
                confirmButtonText: options.confirmButtonText,
                cancelButtonText: options.cancelButtonText
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = url;
                }
            });
        }
    });
}

// Cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Configurar todas las acciones
    manejarAccionConfirmada('.btn-eliminar-permanentemente', {
        title: '¿Eliminar permanentemente?',
        text: '¡Esta acción no se puede deshacer!',
        icon: 'warning',
        confirmButtonText: 'Sí, eliminar',
        confirmColor: '#3085d6'
    });
    
    manejarAccionConfirmada('.btn-eliminar', {
        title: '¿Mover a papelera?',
        text: 'El registro se moverá a la papelera de reciclaje.',
        icon: 'question',
        confirmButtonText: 'Sí, mover',
        confirmColor: '#3085d6'
    });
    
    manejarAccionConfirmada('.btn-restaurar', {
        title: '¿Restaurar registro?',
        text: 'El registro volverá a estar activo.',
        icon: 'info',
        confirmButtonText: 'Sí, restaurar',
        confirmColor: '#3085d6'
    });

    // Manejo de formularios (manteniendo tu código existente)
    document.querySelectorAll("form").forEach((formulario) => {
        formulario.addEventListener("submit", function(event) {
            event.preventDefault();
            const datosFormulario = new FormData(formulario);
            const url = formulario.action;
            const method = formulario.method;

            fetch(url, {
                method: method,
                body: datosFormulario,
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire({
                        icon: "success",
                        title: "Éxito",
                        text: data.message || "Registro guardado correctamente",
                        timer: 2000,
                        showConfirmButton: false
                    }).then(() => {
                        location.reload();
                    });
                    formulario.reset();
                } else {
                    Swal.fire({
                        icon: "error",
                        title: "Error",
                        text: data.message || "No se pudo guardar el registro.",
                    });
                }
            })
            .catch(error => {
                console.error("Error en la petición:", error);
                Swal.fire({
                    icon: "error",
                    title: "Error",
                    text: "Ocurrió un problema al guardar el registro.",
                });
            });
        });
    });

    // Mostrar alertas de URL (éxito/error)
    const urlParams = new URLSearchParams(window.location.search);
    const success = urlParams.get('success');
    const message = urlParams.get('message');

    if (success === 'true' && message) {
        Swal.fire({
            icon: 'success',
            title: '¡Éxito!',
            text: message,
            timer: 3000,
            showConfirmButton: false
        });
        history.replaceState({}, document.title, window.location.pathname);
    } else if (success === 'false' && message) {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: message
        });
        history.replaceState({}, document.title, window.location.pathname);
    }
});

// Funciones auxiliares (manteniendo las existentes)
function buscarTablaRelacionada(formulario) {
    const contenedor = formulario.closest("div, section, form");
    return contenedor.querySelector("table tbody") || null;
}

function agregarFilaDinamica(tabla, datos) {
    if (!tabla) {
        console.warn("Tabla no encontrada");
        return;
    }

    const nuevaFila = document.createElement("tr");
    Object.values(datos).forEach(valor => {
        const celda = document.createElement("td");
        celda.textContent = valor;
        nuevaFila.appendChild(celda);
    });

    if (datos.ID) {
        const acciones = document.createElement("td");
        acciones.innerHTML = `
            <a href="/editar/${datos.ID}/" class="btn btn-warning">Editar</a>
            <a href="/eliminar/${datos.ID}/" class="btn btn-danger btn-eliminar">Eliminar</a>
        `;
        nuevaFila.appendChild(acciones);
    }

    tabla.appendChild(nuevaFila);
}