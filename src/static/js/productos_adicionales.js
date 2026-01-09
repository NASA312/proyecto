// Script para manejar productos adicionales en formularios de variantes de paquetes
// Este script se puede incluir en múltiples páginas
(function() {
    // Función para inicializar la gestión de productos adicionales
    function initProductosAdicionales(options = {}) {
        // Configuración predeterminada
        const config = {
            containerSelector: '#productos-adicionales-container',  // Contenedor donde se agregarán los productos
            addButtonSelector: '#agregar-producto-btn',            // Botón para agregar nuevo producto
            productsDataSelector: '#productos-disponibles-data',   // Elemento con datos JSON de productos
            cantidadesFieldSelector: '#id_cantidades_adicionales',  // Campo oculto que guarda las cantidades
            editMode: false,                                       // Si estamos en modo edición
            editButtonSelector: '.editar-btn',                     // Selectores para botones de edición
            modalSelector: '#editarModal',                         // Selector del modal de edición
            formSelector: '#editarForm',                           // Selector del formulario en el modal
            ...options                                             // Sobreescribir con opciones proporcionadas
        };

        // Variables para seguimiento interno
        let productosDisponibles = [];
        let cantidadesAdicionales = {};
        let productosSeleccionados = [];
        
        // Obtener elementos DOM
        const container = document.querySelector(config.containerSelector);
        const addButton = document.querySelector(config.addButtonSelector);
        const cantidadesInput = document.querySelector(config.cantidadesFieldSelector);
        const productosDataElement = document.querySelector(config.productsDataSelector);
        
        // Verificar elementos esenciales
        if (!container || !addButton) {
            console.error('No se encontraron elementos esenciales para la gestión de productos adicionales');
            return;
        }
        
        // Cargar productos disponibles
        if (productosDataElement) {
            try {
                productosDisponibles = JSON.parse(productosDataElement.textContent);
            } catch (e) {
                console.error('Error al parsear productos disponibles:', e);
            }
        }
        
        // Cargar cantidades adicionales existentes
        if (cantidadesInput && cantidadesInput.value) {
            try {
                cantidadesAdicionales = JSON.parse(cantidadesInput.value);
                // Convertir las claves a enteros para mantener consistencia
                Object.keys(cantidadesAdicionales).forEach(key => {
                    const intKey = parseInt(key);
                    if (!isNaN(intKey)) {
                        productosSeleccionados.push(intKey);
                    }
                });
            } catch (e) {
                console.error('Error al cargar cantidades adicionales:', e);
            }
        }
        
        // Función para actualizar el campo oculto con las cantidades
        function actualizarCantidades() {
            if (cantidadesInput) {
                // Crear copia limpia del objeto
                const cleanData = {};
                Object.keys(cantidadesAdicionales).forEach(key => {
                    const numKey = Number(key);
                    if (!isNaN(numKey)) {
                        cleanData[numKey] = Number(cantidadesAdicionales[key]) || 1;
                    }
                });
                
                // Convertir a JSON con formato estricto
                const jsonStr = JSON.stringify(cleanData, null, 0);
                
                // Debug en consola
                console.log("JSON a enviar:", jsonStr);
                console.log("Validación:", JSON.parse(jsonStr)); // Debería pasar sin errores
                
                // Asignar al campo oculto
                cantidadesInput.value = jsonStr;
            }
        }
        
        // Función para agregar un nuevo producto al DOM
        function agregarProductoHTML(productoId = null, cantidad = 1) {
            const id = Date.now(); // ID único para este elemento del DOM
            
            // Filtrar productos que ya han sido seleccionados
            const productosNoSeleccionados = productosDisponibles.filter(
                p => !productosSeleccionados.includes(parseInt(p.idpr))
            );
            
            if (productosNoSeleccionados.length === 0 && !productoId) {
                alert('No hay más productos disponibles para agregar');
                return;
            }
            
            // Crear el nuevo elemento
            const nuevoProducto = document.createElement('div');
            nuevoProducto.className = 'form-group row producto-adicional';
            nuevoProducto.dataset.rowId = id;
            
            // Crear opciones para el select
            let opcionesHTML = '<option value="">-- Seleccione un producto --</option>';
            
            // Si estamos agregando un producto específico que ya no está en la lista de disponibles,
            // necesitamos incluirlo en las opciones
            let productoEspecifico = null;
            if (productoId) {
                const existeEnDisponibles = productosDisponibles.some(p => parseInt(p.idpr) === parseInt(productoId));
                if (!existeEnDisponibles) {
                    // Buscar información del producto en los datos adicionales
                    const productosAdicionalesData = window.productosAdicionalesData || [];
                    productoEspecifico = productosAdicionalesData.find(p => parseInt(p.idpr) === parseInt(productoId));
                }
            }
            
            // Agrega todos los productos no seleccionados a las opciones
            productosNoSeleccionados.forEach(function(producto) {
                const selected = parseInt(producto.idpr) === parseInt(productoId) ? 'selected' : '';
                opcionesHTML += `<option value="${producto.idpr}" ${selected}>${producto.nomb}</option>`;
            });
            
            // Si tenemos un producto específico que no está en la lista, añadirlo también
            if (productoEspecifico) {
                opcionesHTML += `<option value="${productoEspecifico.idpr}" selected>${productoEspecifico.nomb}</option>`;
            }
            
            // Construir HTML interno
            nuevoProducto.innerHTML = `
                <div class="col-sm-5">
                    <select class="form-control producto-select" data-row-id="${id}">
                        ${opcionesHTML}
                    </select>
                </div>
                <div class="col-sm-5">
                    <input type="number" value="${cantidad}" min="1" 
                        class="form-control cantidad-input" data-row-id="${id}">
                </div>
                <div class="col-sm-2">
                    <button type="button" class="btn btn-danger eliminar-producto" data-row-id="${id}">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            
            // Agregar el nuevo elemento al contenedor
            container.appendChild(nuevoProducto);
            
            // Si se proporciona un ID de producto, marcarlo como seleccionado
            if (productoId) {
                productosSeleccionados.push(parseInt(productoId));
                cantidadesAdicionales[productoId] = cantidad;
                actualizarCantidades();
                
                // Marcar el producto como seleccionado en el select
                const select = nuevoProducto.querySelector(`.producto-select[data-row-id="${id}"]`);
                if (select) {
                    select.value = productoId;
                    select.dataset.productId = productoId;
                }
            }
            
            // Añadir evento al select de producto
            const select = nuevoProducto.querySelector(`.producto-select[data-row-id="${id}"]`);
            if (select) {
                select.addEventListener('change', function() {
                    const rowId = this.dataset.rowId;
                    const oldProductId = this.dataset.productId;
                    const newProductId = this.value;
                    
                    // Si había un producto seleccionado anteriormente, quitarlo de la lista
                    if (oldProductId) {
                        const index = productosSeleccionados.indexOf(parseInt(oldProductId));
                        if (index > -1) {
                            productosSeleccionados.splice(index, 1);
                            delete cantidadesAdicionales[oldProductId];
                        }
                    }
                    
                    // Agregar el nuevo producto seleccionado
                    if (newProductId) {
                        productosSeleccionados.push(parseInt(newProductId));
                        this.dataset.productId = newProductId;
                        
                        // Obtener la cantidad actual
                        const cantidadInput = document.querySelector(`.cantidad-input[data-row-id="${rowId}"]`);
                        const cantidad = cantidadInput ? parseInt(cantidadInput.value) || 1 : 1;
                        cantidadesAdicionales[newProductId] = cantidad;
                    }
                    
                    actualizarCantidades();
                });
            }
            
            // Añadir evento al input de cantidad
            const cantidadInput = nuevoProducto.querySelector(`.cantidad-input[data-row-id="${id}"]`);
            if (cantidadInput) {
                cantidadInput.addEventListener('change', function() {
                    const rowId = this.dataset.rowId;
                    const productoSelect = document.querySelector(`.producto-select[data-row-id="${rowId}"]`);
                    const productoId = productoSelect ? productoSelect.value : null;
                    
                    if (productoId) {
                        cantidadesAdicionales[productoId] = parseInt(this.value) || 1;
                        actualizarCantidades();
                    }
                });
            }
            
            // Añadir evento al botón de eliminar
            const btnEliminar = nuevoProducto.querySelector(`.eliminar-producto[data-row-id="${id}"]`);
            if (btnEliminar) {
                btnEliminar.addEventListener('click', function() {
                    const rowId = this.dataset.rowId;
                    const productoSelect = document.querySelector(`.producto-select[data-row-id="${rowId}"]`);
                    const productoId = productoSelect ? productoSelect.value : null;
                    
                    if (productoId) {
                        const index = productosSeleccionados.indexOf(parseInt(productoId));
                        if (index > -1) {
                            productosSeleccionados.splice(index, 1);
                            delete cantidadesAdicionales[productoId];
                            actualizarCantidades();
                        }
                    }
                    
                    const productoRow = document.querySelector(`.producto-adicional[data-row-id="${rowId}"]`);
                    if (productoRow) {
                        productoRow.remove();
                    }
                });
            }
        }
        
        // Agregar evento al botón de agregar producto
        if (addButton) {
            addButton.addEventListener('click', function() {
                agregarProductoHTML();
            });
        }
        
        // Configurar el modo de edición si está habilitado
        if (config.editMode) {
            // Agregar manejador para botones de edición
            document.querySelectorAll(config.editButtonSelector).forEach(function(button) {
                button.addEventListener('click', function(event) {
                    event.preventDefault();
                    
                    var url = this.getAttribute('href');
                    
                    // Realizar solicitud AJAX para obtener datos
                    fetch(url, {
                        method: 'GET',
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                            'Accept': 'application/json'
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        console.log("Datos recibidos:", data);
                        
                        // Limpiar productos adicionales existentes
                        const container = document.querySelector(config.containerSelector);
                        if (container) {
                            container.innerHTML = '';
                        }
                        
                        // Guardar datos de productos adicionales para referencia
                        window.productosAdicionalesData = data.productos_adicionales || [];
                        
                        // Resetear el tracking de productos
                        productosSeleccionados = [];
                        cantidadesAdicionales = {};
                        
                        // Configurar el formulario del modal
                        const form = document.querySelector(`${config.modalSelector} form`);
                        if (form) {
                            form.id = 'editarForm';
                            form.action = url;
                        }
                        
                        // Rellenar campos básicos del formulario
                        Object.keys(data).forEach(function(key) {
                            // Excluir objetos complejos
                            if (typeof data[key] !== 'object') {
                                const input = form.querySelector(`[name="${key}"]`) || 
                                            form.querySelector(`[id="id_${key}"]`);
                                
                                if (input) {
                                    if (input.type === 'checkbox') {
                                        input.checked = Boolean(data[key]);
                                    } else {
                                        input.value = data[key] || '';
                                    }
                                }
                            }
                        });
                        
                        // Agregar productos adicionales al formulario
                        if (data.productos_adicionales && Array.isArray(data.productos_adicionales)) {
                            data.productos_adicionales.forEach(function(producto) {
                                agregarProductoHTML(producto.idpr, producto.cant);
                            });
                        }
                        
                        // Actualizar campo de cantidades adicionales
                        actualizarCantidades();
                        
                        // Mostrar el modal
                        const modalElement = document.querySelector(config.modalSelector);
                        if (modalElement && typeof $('#' + modalElement.id).modal === 'function') {
                            $('#' + modalElement.id).modal('show');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('Error al cargar los datos. Por favor, intente de nuevo.');
                    });
                });
            });
            
            // Manejar envío del formulario de edición
            document.body.addEventListener('submit', function(e) {
                var form = e.target;
                
                // Solo procesar si es el formulario de edición
                if (form.id === 'editarForm') {
                    e.preventDefault();
                    
                    var formData = new FormData(form);
                    
                    fetch(form.action, {
                        method: 'POST',
                        body: formData,
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    })
                    .then(response => response.json())
                    .then(result => {
                        if (result.success) {
                            const modalElement = document.querySelector(config.modalSelector);
                            if (modalElement && typeof $('#' + modalElement.id).modal === 'function') {
                                $('#' + modalElement.id).modal('hide');
                            }
                            window.location.reload();
                        } else {
                            alert('Error al guardar: ' + JSON.stringify(result.errors || result.message));
                        }
                    })
                    .catch(error => {
                        console.error('Error al enviar el formulario:', error);
                        alert('Error al guardar los cambios. Por favor, intente de nuevo.');
                    });
                }
            });
        }
        
        // Cargar productos adicionales previos si existen
        if (Object.keys(cantidadesAdicionales).length > 0) {
            Object.keys(cantidadesAdicionales).forEach(function(productoId) {
                agregarProductoHTML(productoId, cantidadesAdicionales[productoId]);
            });
        }
        
        // Devolver API pública
        return {
            agregarProducto: agregarProductoHTML,
            actualizarCantidades: actualizarCantidades,
            getProductosSeleccionados: () => productosSeleccionados.slice(),
            getCantidades: () => ({...cantidadesAdicionales})
        };
    }
    
    // Exponer la función de inicialización globalmente
    window.initProductosAdicionales = initProductosAdicionales;
})();