from django.core.management.base import BaseCommand
from django.conf import settings
from guarderia.models import Colonia
import pandas as pd
import os
from django.db import transaction

class Command(BaseCommand):
    help = 'Carga las colonias desde el archivo Excel a la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--archivo',
            type=str,
            default='guarderia/data/Colonias.xlsx',
            help='Ruta al archivo Excel (relativo a BASE_DIR)'
        )
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Eliminar colonias existentes antes de cargar (recomendado)'
        )

    def handle(self, *args, **options):
        archivo_path = os.path.join(settings.BASE_DIR, options['archivo'])

        if not os.path.exists(archivo_path):
            self.stdout.write(self.style.ERROR(f'No se encontró el archivo: {archivo_path}'))
            return

        self.stdout.write(f'Leyendo archivo: {archivo_path}')

        try:
            df = pd.read_excel(archivo_path)

            # ── Columnas requeridas ──────────────────────────────────────────
            columnas_requeridas = ['d_codigo', 'd_asenta', 'D_mnpio', 'd_estado']
            faltantes = [c for c in columnas_requeridas if c not in df.columns]
            if faltantes:
                self.stdout.write(self.style.ERROR(
                    f'Faltan columnas en el Excel: {faltantes}\n'
                    f'Columnas disponibles: {list(df.columns)}'
                ))
                return

            # ── Limpiar y normalizar ─────────────────────────────────────────
            df['d_codigo'] = (
                df['d_codigo']
                .fillna(0)
                .astype(float)   # evita error si viene como float de Excel
                .astype(int)
                .astype(str)
                .str.zfill(5)
            )
            df = df[df['d_codigo'] != '00000']
            df['d_asenta']  = df['d_asenta'].fillna('Sin nombre').astype(str).str.strip()
            df['D_mnpio']   = df['D_mnpio'].fillna('Sin municipio').astype(str).str.strip()
            df['d_estado']  = df['d_estado'].fillna('Sin estado').astype(str).str.strip()

            self.stdout.write(f'Registros válidos a procesar: {len(df)}')

            # ── Limpiar tabla ────────────────────────────────────────────────
            if options['limpiar']:
                count = Colonia.objects.count()
                self.stdout.write(self.style.WARNING(
                    f'Eliminando {count} colonias existentes...'
                ))
                Colonia.objects.all().delete()
                self.stdout.write(self.style.WARNING('Tabla vaciada.'))
            else:
                self.stdout.write(self.style.WARNING(
                    'AVISO: No se usó --limpiar. Se insertarán registros sobre los existentes.'
                ))

            # ── Insertar en lotes ────────────────────────────────────────────
            batch_size  = 1000
            lote        = []
            total_creadas = 0

            with transaction.atomic():
                for _, row in df.iterrows():
                    lote.append(Colonia(
                        d_codigo = row['d_codigo'],
                        d_asenta = row['d_asenta'],
                        D_mnpio  = row['D_mnpio'],
                        d_estado = row['d_estado'],
                    ))

                    if len(lote) >= batch_size:
                        Colonia.objects.bulk_create(lote)
                        total_creadas += len(lote)
                        self.stdout.write(f'  → Procesados {total_creadas} registros...')
                        lote = []

                if lote:
                    Colonia.objects.bulk_create(lote)
                    total_creadas += len(lote)

            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Carga completada exitosamente'
                f'\n  Registros insertados : {total_creadas}'
                f'\n  Total en base de datos: {Colonia.objects.count()}'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al cargar colonias: {str(e)}'))
            import traceback
            traceback.print_exc()