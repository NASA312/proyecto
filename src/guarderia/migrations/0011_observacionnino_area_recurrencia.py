# Generated manually - 2026-05-16
# Puntos 6 y 7: FK área + campos de recurrencia/atención en ObservacionNino

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('guarderia', '0010_areaobservacion'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [

        # ── Punto 6 ── FK área (nullable para no romper registros existentes)
        migrations.AddField(
            model_name='observacionnino',
            name='area',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='observaciones',
                to='guarderia.areaobservacion',
                help_text='Área responsable de la observación',
            ),
        ),

        # ── Punto 7 ── Campo recurrente
        migrations.AddField(
            model_name='observacionnino',
            name='es_recurrente',
            field=models.BooleanField(
                default=False,
                help_text='Si es True, se muestra en cada entrada del niño hasta ser atendida',
            ),
        ),

        # ── Punto 7 ── Campo atendida
        migrations.AddField(
            model_name='observacionnino',
            name='atendida',
            field=models.BooleanField(
                default=False,
                help_text='Indica que la observación recurrente fue vista/atendida',
            ),
        ),

        # ── Punto 7 ── Fecha en que se atendió
        migrations.AddField(
            model_name='observacionnino',
            name='fecha_atendida',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Fecha y hora en que se marcó como atendida',
            ),
        ),

        # ── Punto 7 ── Quién la atendió
        migrations.AddField(
            model_name='observacionnino',
            name='atendida_por',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='observaciones_atendidas',
                to=settings.AUTH_USER_MODEL,
                help_text='Usuario que marcó la observación como atendida',
            ),
        ),
    ]
