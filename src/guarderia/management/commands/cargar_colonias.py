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
            help='Eliminar colonias existentes antes de cargar'
        )

    def handle(self, *args, **options):
        archivo_path = os.path.join(settings.BASE_DIR, options['archivo'])
        
        if not os.path.exists(archivo_path):
            self.stdout.write(self.style.ERROR(f'No se encontró el archivo: {archivo_path}'))
            return
        
        self.stdout.write(f'Leyendo archivo: {archivo_path}')
        
        try:
            # Leer Excel
            df = pd.read_excel(archivo_path)
            
            # Limpiar datos
            df['d_codigo'] = df['d_codigo'].fillna(0).astype(int).astype(str).str.zfill(5)
            df = df[df['d_codigo'] != '00000']  # Eliminar registros inválidos
            
            self.stdout.write(f'Registros a procesar: {len(df)}')
            
            # Limpiar tabla si se solicita
            if options['limpiar']:
                count = Colonia.objects.all().count()
                Colonia.objects.all().delete()
                self.stdout.write(self.style.WARNING(f'Eliminados {count} registros existentes'))
            
            # Cargar en lotes para mejor rendimiento
            batch_size = 1000
            colonias_crear = []
            total_creadas = 0
            total_actualizadas = 0
            
            with transaction.atomic():
                for index, row in df.iterrows():
                    # Preparar datos
                    colonia_data = {
                        'd_codigo': str(row['d_codigo']).zfill(5),
                        'd_asenta': str(row['d_asenta']),
                        'd_tipo_asenta': str(row['d_tipo_asenta']) if pd.notna(row['d_tipo_asenta']) else '',
                        'D_mnpio': str(row['D_mnpio']) if pd.notna(row['D_mnpio']) else '',
                        'd_estado': str(row['d_estado']) if pd.notna(row['d_estado']) else '',
                        'd_ciudad': str(row['d_ciudad']) if pd.notna(row['d_ciudad']) else None,
                        'd_CP': str(row['d_CP']) if pd.notna(row['d_CP']) else None,
                        'c_estado': str(row['c_estado']) if pd.notna(row['c_estado']) else None,
                        'c_oficina': str(row['c_oficina']) if pd.notna(row['c_oficina']) else None,
                        'c_tipo_asenta': str(row['c_tipo_asenta']) if pd.notna(row['c_tipo_asenta']) else None,
                        'c_mnpio': str(row['c_mnpio']) if pd.notna(row['c_mnpio']) else None,
                        'id_asenta_cpcons': str(row['id_asenta_cpcons']) if pd.notna(row['id_asenta_cpcons']) else f"{row['d_codigo']}-{index}",
                    }
                    
                    colonias_crear.append(Colonia(**colonia_data))
                    
                    # Insertar en lotes
                    if len(colonias_crear) >= batch_size:
                        Colonia.objects.bulk_create(colonias_crear, ignore_conflicts=True)
                        total_creadas += len(colonias_crear)
                        self.stdout.write(f'Procesados {total_creadas} registros...')
                        colonias_crear = []
                
                # Insertar los restantes
                if colonias_crear:
                    Colonia.objects.bulk_create(colonias_crear, ignore_conflicts=True)
                    total_creadas += len(colonias_crear)
            
            self.stdout.write(self.style.SUCCESS(f'✓ Carga completada exitosamente'))
            self.stdout.write(self.style.SUCCESS(f'  Total registros creados: {total_creadas}'))
            self.stdout.write(self.style.SUCCESS(f'  Total en base de datos: {Colonia.objects.count()}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al cargar colonias: {str(e)}'))
            import traceback
            traceback.print_exc()