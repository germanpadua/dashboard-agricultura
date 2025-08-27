#!/usr/bin/env python3
"""
🧹 Utilidad de gestión de caché satelital

Herramienta simple para gestionar el caché inteligente de datos satelitales.
Los datos satelitales son inmutables (una imagen de una fecha nunca cambia),
por lo que solo se limpia por espacio, no por tiempo.

Uso:
    python cache_manager.py stats          # Mostrar estadísticas
    python cache_manager.py clean          # Limpiar caché (1GB límite)
    python cache_manager.py clean --size 500  # Limpiar hasta 500MB
    python cache_manager.py clean --corrupted  # Solo archivos corruptos
"""

import argparse
import sys
from pathlib import Path

# Agregar el directorio src al path para importar los módulos
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from utils.api_quota_manager import get_intelligent_cache, manual_cache_cleanup
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    print("Asegúrate de ejecutar desde el directorio raíz del proyecto")
    sys.exit(1)


def show_stats():
    """Muestra estadísticas del caché."""
    try:
        cache_manager = get_intelligent_cache()
        stats = cache_manager.get_cache_stats()
        
        print("📊 Estadísticas del Caché Satelital")
        print("=" * 40)
        print(f"Entradas totales: {stats['total_entries']}")
        print(f"En memoria: {stats['memory_entries']}")
        print(f"Tamaño total: {stats['total_size_mb']} MB")
        print(f"Cache hits: {stats['cache_hits']}")
        print(f"Cache misses: {stats['cache_misses']}")
        print(f"Hit rate: {stats['hit_rate_percent']}%")
        print(f"Última limpieza: {stats['last_cleanup']}")
        print()
        
        # Información adicional
        if stats['total_size_mb'] > 1000:
            print("⚠️  Caché > 1GB - considera hacer limpieza")
        elif stats['total_size_mb'] > 500:
            print("💡 Caché moderadamente grande")
        else:
            print("✅ Caché en tamaño óptimo")
            
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {e}")


def clean_cache(max_size_mb=1000, corrupted_only=False):
    """Limpia el caché."""
    try:
        print(f"🧹 Iniciando limpieza del caché...")
        
        if corrupted_only:
            print("🔧 Solo limpiando archivos corruptos...")
            cache_manager = get_intelligent_cache()
            cache_manager.cleanup_corrupted_cache()
            print("✅ Limpieza de archivos corruptos completada")
        else:
            print(f"🗂️  Limpiando hasta {max_size_mb} MB...")
            result = manual_cache_cleanup(max_size_mb, clean_corrupted=True)
            
            if result['success']:
                print("✅ Limpieza completada:")
                print(f"   • Liberados: {result['freed_mb']:.1f} MB")
                print(f"   • Archivos eliminados: {result['removed_entries']}")
                print(f"   • Tamaño final: {result['after']['total_size_mb']} MB")
            else:
                print(f"❌ Error en limpieza: {result['error']}")
                
    except Exception as e:
        print(f"❌ Error durante limpieza: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="🧹 Gestor de caché satelital",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python cache_manager.py stats                    # Ver estadísticas
  python cache_manager.py clean                    # Limpiar hasta 1GB
  python cache_manager.py clean --size 500         # Limpiar hasta 500MB
  python cache_manager.py clean --corrupted        # Solo archivos corruptos
        """
    )
    
    parser.add_argument('action', choices=['stats', 'clean'], 
                       help='Acción a realizar')
    parser.add_argument('--size', type=int, default=1000,
                       help='Tamaño máximo del caché en MB (default: 1000)')
    parser.add_argument('--corrupted', action='store_true',
                       help='Solo limpiar archivos corruptos')
    
    args = parser.parse_args()
    
    print("🛰️  Dashboard Agricultura - Gestor de Caché")
    print("=" * 50)
    
    if args.action == 'stats':
        show_stats()
    elif args.action == 'clean':
        clean_cache(args.size, args.corrupted)


if __name__ == '__main__':
    main()