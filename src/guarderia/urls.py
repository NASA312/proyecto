from django.urls import path
from . import views

app_name = 'guarderia'

urlpatterns = [
    # =====================================
    # TUTORES
    # =====================================
    path('tutores/', views.lista_tutores, name='lista_tutores'),
    path('tutores/registrar/', views.registrar_tutor, name='registrar_tutor'),
    path('tutores/<int:tutor_id>/', views.detalle_tutor, name='detalle_tutor'),
    path('tutores/<int:tutor_id>/editar/', views.editar_tutor, name='editar_tutor'),
    path('tutores/<int:tutor_id>/registrar-huella/', views.registrar_huella_tutor, name='registrar_huella_tutor'),

    # AJAX
    path('tutores/buscar/', views.buscar_tutores_ajax, name='buscar_tutores_ajax'),

    # =====================================
    # NIÑOS
    # =====================================
    path('ninos/', views.lista_ninos, name='lista_ninos'),
    path('ninos/registrar/', views.registrar_nino, name='registrar_nino'),
    path('ninos/<int:nino_id>/', views.detalle_nino, name='detalle_nino'),
    path('ninos/<int:nino_id>/editar/', views.editar_nino, name='editar_nino'),
    path('ninos/<int:nino_id>/asignar-tutores/', views.asignar_tutores, name='asignar_tutores'),

    # =====================================
    # VERIFICACIÓN PÚBLICA
    # =====================================
    path('verificar-huella/', views.verificar_huella_tutor, name='verificar_huella_tutor'),

    # =====================================
    # REGISTROS
    # =====================================
    path('registros/historial/', views.historial_accesos, name='historial_accesos'),
    path('registros/salida/', views.registrar_salida, name='registrar_salida'),

    # =====================================
    # APIs (.NET)
    # =====================================
    path('api/recibir-huella-tutor/', views.recibir_huella_tutor, name='recibir_huella_tutor'),
    path(
        'api/verificar-captura-tutor/<int:tutor_id>/',
        views.verificar_huella_capturada_tutor,
        name='verificar_huella_capturada_tutor'
    ),
]
