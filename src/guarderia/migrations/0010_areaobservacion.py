# Generated manually - 2026-05-16
# Punto 5: Crear catálogo AreaObservacion + seeder de áreas iniciales

from django.db import migrations, models


def sembrar_areas(apps, schema_editor):
    """Inserta las 5 áreas institucionales iniciales."""
    AreaObservacion = apps.get_model('guarderia', 'AreaObservacion')
    areas = [
        {'nombre': 'Médica',         'descripcion': 'Observaciones del área médica y de salud',  'orden': 1},
        {'nombre': 'Psicología',     'descripcion': 'Observaciones conductuales y emocionales',   'orden': 2},
        {'nombre': 'Pedagogía',      'descripcion': 'Observaciones académicas y de aprendizaje',  'orden': 3},
        {'nombre': 'Trabajo Social', 'descripcion': 'Observaciones de contexto familiar y social','orden': 4},
        {'nombre': 'Nutrición',      'descripcion': 'Observaciones de alimentación y nutrición',  'orden': 5},
    ]
    for area in areas:
        AreaObservacion.objects.get_or_create(
            nombre=area['nombre'],
            defaults={
                'descripcion': area['descripcion'],
                'orden':       area['orden'],
                'activo':      True,
            }
        )


def revertir_areas(apps, schema_editor):
    """Elimina solo las áreas sembradas (reversible)."""
    AreaObservacion = apps.get_model('guarderia', 'AreaObservacion')
    nombres = ['Médica', 'Psicología', 'Pedagogía', 'Trabajo Social', 'Nutrición']
    AreaObservacion.objects.filter(nombre__in=nombres).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('guarderia', '0009_merge_20260424_0805'),
    ]

    operations = [
        # 1 — Crear la tabla catálogo
        migrations.CreateModel(
            name='AreaObservacion',
            fields=[
                ('id',          models.BigAutoField(auto_created=True, primary_key=True,
                                    serialize=False, verbose_name='ID')),
                ('nombre',      models.CharField(max_length=60, unique=True,
                                    help_text='Nombre del área responsable')),
                ('descripcion', models.TextField(blank=True, default='',
                                    help_text='Descripción del área')),
                ('activo',      models.BooleanField(default=True,
                                    help_text='Indica si el área está disponible para nuevas observaciones')),
                ('orden',       models.PositiveSmallIntegerField(default=0,
                                    help_text='Orden de aparición en el selector')),
            ],
            options={
                'verbose_name':        'Área de Observación',
                'verbose_name_plural': 'Áreas de Observación',
                'ordering':            ['orden', 'nombre'],
            },
        ),

        # 2 — Seeder con las 5 áreas iniciales
        migrations.RunPython(sembrar_areas, revertir_areas),
    ]
