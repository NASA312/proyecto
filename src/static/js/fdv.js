$(document).ready(
    setTimeout(function(){
        $('#message').css('display','none');
        console.log("entramos");
    },5000)
);

function parseDateForSorting(input) {
    if(input.match(/^\d{2}\/\d{2}\/\d{4}$/)) {
        var parts = input.split('/');
        return parts[2] + parts[1] + parts[0]; // Reordenamos a YYYYMMDD
    }
    return input; // Si no es una fecha, retornamos el valor original
}


function initializeDataTable(index, order, filename, domString) {
    /* valores por default */
    index = typeof index !== 'undefined' ? index : 0;
    order = typeof order !== 'undefined' ? order : "desc";
    filename = typeof filename !== 'undefined' ? filename : "ArchivoDatosTecuala";
    domString = typeof domString !== 'undefined' ? domString : "fgBpirtp";
    
    // Verificar si la tabla ya ha sido inicializada con DataTables
    var table = $('.dataTables-example').DataTable({
        pageLength: 25,
        lengthMenu: [ [25, 50, 100, 200, 300, 500, 1000, -1], [25, 50, 100, 200, 300, 500, 1000, "Todos"] ],
        fixedHeader: true,
        columnDefs: [
            {
                targets: "_all",
                render: function(data, type, row) {
                    return type === 'sort' ? parseDateForSorting(data) : data;
                }
            }
        ],
        responsive: true,
        dom: '<l><"top-dt"' + domString + ">",
        order: [[ index, order ]],
        buttons: [
            { extend: 'copy', text:'<i class="fa fa-files-o fa-2x"></i> Copy', className:'dim'},
            {extend: 'excel', text:'<i class="fa fa-file-excel-o fa-2x"></i> Excel', title: filename, className:'dim'},
            {extend: 'pdf', text:'<i class="fa fa-file-pdf-o fa-2x"></i> PDF', title: filename, className:'dim'},
            {extend: 'print', text:'<i class="fa fa-print fa-2x"></i> Print', className:'dim',
             customize: function (win){
                    $(win.document.body).addClass('white-bg');
                    $(win.document.body).css('font-size', '10px');
                    $(win.document.body).find('table')
                            .addClass('compact')
                            .css('font-size', 'inherit');
            }}
        ],
        language: {
            "sProcessing":     "Procesando...",
            "sLengthMenu":     "Mostrar _MENU_ registros",
            "sZeroRecords":    "No se encontraron resultados",
            "sEmptyTable":     "Ningún dato disponible en esta tabla",
            "sInfo":           "Mostrando registros del _START_ al _END_ de un total de _TOTAL_ registros",
            "sInfoEmpty":      "Mostrando registros del 0 al 0 de un total de 0 registros",
            "sInfoFiltered":   "(filtrado de un total de _MAX_ registros)",
            "sSearch":         "Buscar:",
            "sLoadingRecords": "Cargando...",
            "oPaginate": {
                "sFirst":    "Primero",
                "sLast":     "Último",
                "sNext":     "Siguiente",
                "sPrevious": "Anterior"
            },
            "oAria": {
                "sSortAscending":  ": Activar para ordenar la columna de manera ascendente",
                "sSortDescending": ": Activar para ordenar la columna de manera descendente"
            }
        }
    });

    // Comprobar si FixedHeader ya ha sido inicializado y evitar sobreinicialización
    if ($.fn.DataTable.FixedHeader && !table.fixedHeader) {
        new $.fn.dataTable.FixedHeader(table);
    }

    $('.dataTables-example tbody').on('mouseenter', 'tr', function () {
        $(this).find('td').css('background-color', '#27ff00'); // Estiliza todas las celdas
    });
    
    $('.dataTables-example tbody').on('mouseleave', 'tr', function () {
        $(this).find('td').css('background-color', ''); // Restaura todas las celdas
    });
    
}
