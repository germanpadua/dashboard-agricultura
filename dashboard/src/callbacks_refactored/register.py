"""
===============================================================================
                    SISTEMA DE REGISTRO CENTRAL DE CALLBACKS
===============================================================================

Módulo coordinador que centraliza el registro de todos los callbacks modulares
del dashboard agrícola. Implementa un sistema de carga segura con manejo robusto
de errores y logging detallado.

Características principales:
• Registro centralizado y coordinado de callbacks por módulo
• Sistema de importación segura con fallbacks
• Manejo granular de errores por módulo
• Logging detallado para debugging y monitoreo
• Separación de responsabilidades (navegación en main.py)
• Carga condicional de módulos opcionales

Arquitectura modular:
• main.py: Callbacks de navegación principal y routing
• datos_satelitales.py: Análisis y visualización satelital
• detecciones.py: Sistema de detección de enfermedades
• fincas.py: Gestión CRUD de propiedades agrícolas
• historico.py: Análisis de datos meteorológicos históricos
• prediccion.py: Modelos predictivos y pronósticos

Autor: Sistema de Monitoreo Agrícola
Versión: 2.1
Última actualización: 2025

===============================================================================
"""
# ===============================================================================
#                                 IMPORTS
# ===============================================================================

# Librerías estándar
import logging

# Configuración de logging
logger = logging.getLogger(__name__)

# ===============================================================================
#                           FUNCIONES AUXILIARES
# ===============================================================================

def _safe_import(primary_path, primary_name, fallback_path=None, fallback_name=None):
    """
    Realiza importación segura con fallback para builders de layout.
    
    Permite importar funciones o clases desde múltiples rutas posibles,
    proporcionando resilencia ante reorganizaciones de código o módulos
    opcionales que podrían no estar disponibles.
    
    Args:
        primary_path (str): Ruta principal del módulo a importar
        primary_name (str): Nombre de la función/clase a importar
        fallback_path (str, optional): Ruta alternativa en caso de fallo
        fallback_name (str, optional): Nombre alternativo a importar
        
    Returns:
        callable or None: Función/clase importada, o None si ambas fallan
        
    Example:
        >>> builder = _safe_import(
        ...     'src.layouts.layout_main', 'build_layout',
        ...     'app.layouts.main', 'build_main_layout'
        ... )
    """
    try:
        # Intento de importación primaria
        module = __import__(primary_path, fromlist=[primary_name])
        imported_object = getattr(module, primary_name)
        logger.debug(f"✅ Importación exitosa: {primary_path}.{primary_name}")
        return imported_object
        
    except Exception as primary_error:
        logger.debug(f"⚠️ Falló importación primaria {primary_path}.{primary_name}: {primary_error}")
        
        # Intento de fallback si está disponible
        if fallback_path and fallback_name:
            try:
                fallback_module = __import__(fallback_path, fromlist=[fallback_name])
                fallback_object = getattr(fallback_module, fallback_name)
                logger.warning(
                    f"🔄 Usando fallback: {fallback_path}.{fallback_name} "
                    f"(primario falló: {primary_error})"
                )
                return fallback_object
                
            except Exception as fallback_error:
                logger.error(
                    f"❌ También falló fallback {fallback_path}.{fallback_name}: "
                    f"{fallback_error}"
                )
        
        # Ambas importaciones fallaron
        logger.error(f"💥 Importación completamente fallida para {primary_path}.{primary_name}")
        return None

# ===============================================================================
#                     FUNCIÓN PRINCIPAL DE REGISTRO
# ===============================================================================

def register_all_callbacks(app):
    """
    Registra sistemáticamente todos los callbacks modulares del dashboard.
    
    Coordina el proceso de registro de callbacks de todos los módulos
    especializados, implementando un manejo robusto de errores que permite
    al sistema continuar funcionando aunque algunos módulos fallen.
    
    Arquitectura de registro:
    • main.py: Sistema de navegación y routing principal
    • datos_satelitales.py: Análisis de imágenes satelitales
    • detecciones.py: Sistema de detección de enfermedades
    • fincas.py: Gestión CRUD de propiedades agrícolas
    • historico.py: Análisis meteorológico histórico
    • prediccion.py: Modelos predictivos y pronósticos
    
    Args:
        app: Instancia de aplicación Dash donde registrar los callbacks
        
    Note:
        • El callback de navegación principal está en main.py para evitar
          conflictos de Output("main-content", "children")
        • Cada módulo se registra independientemente con manejo de errores
        • Los fallos individuales no impiden el registro de otros módulos
    """
    logger.info("🚀 Iniciando proceso de registro centralizado de callbacks...")
    
    # Contadores para estadísticas de registro
    successful_registrations = 0
    failed_registrations = 0
    
    # ===================================================================
    #                    CALLBACKS PRINCIPALES (NAVEGACIÓN)
    # ===================================================================
    
    # IMPORTANTE: El callback de navegación debe registrarse primero
    # para establecer el Output("main-content", "children") principal
    try:
        logger.info("📍 Registrando callbacks principales (navegación)...")
        from . import main
        main.register_callbacks(app)
        logger.info("✅ Sistema de navegación principal registrado exitosamente")
        successful_registrations += 1
    except Exception as main_error:
        logger.critical(
            f"💥 ERROR CRÍTICO registrando navegación principal: {main_error}\n"
            "El sistema podría no funcionar correctamente sin navegación."
        )
        failed_registrations += 1
    
    # ===================================================================
    #                    CALLBACKS MODULARES ESPECIALIZADOS
    # ===================================================================
    
    # Configuración de módulos con información detallada
    callback_modules = [
        {
            'name': 'datos_satelitales',
            'description': 'Análisis y visualización de datos satelitales',
            'icon': '🛰️',
            'import_path': '.datos_satelitales',
            'register_function': 'register_callbacks',
            'critical': False  # No crítico para funcionalidad básica
        },
        {
            'name': 'detecciones',
            'description': 'Sistema de detección y análisis de enfermedades',
            'icon': '🦠',
            'import_path': '.detecciones',
            'register_function': 'register_callbacks',
            'critical': True   # Funcionalidad core del dashboard
        },
        {
            'name': 'fincas',
            'description': 'Gestión CRUD de propiedades agrícolas',
            'icon': '🏞️',
            'import_path': '.fincas', 
            'register_function': 'register_callbacks',
            'critical': True   # Gestión de fincas es crítica
        },
        {
            'name': 'historico',
            'description': 'Análisis de datos meteorológicos históricos',
            'icon': '📊',
            'import_path': '.historico',
            'register_function': 'register_callbacks',
            'critical': True   # Análisis histórico es core
        },
        {
            'name': 'prediccion',
            'description': 'Modelos predictivos y pronósticos meteorológicos',
            'icon': '🔮',
            'import_path': '.prediccion',
            'register_function': 'register_callbacks',
            'critical': True   # Predicciones son funcionalidad core
        },
        {
            'name': 'help_modals',
            'description': 'Modales de ayuda e información del dashboard',
            'icon': 'ℹ️',
            'import_path': '..components.help_modals',
            'register_function': 'register_modal_callbacks',
            'critical': False  # Funcionalidad auxiliar
        }
    ]
    
    # Registro sistemático de cada módulo
    for module_config in callback_modules:
        module_name = module_config['name']
        description = module_config['description']
        icon = module_config['icon']
        import_path = module_config['import_path']
        register_func = module_config['register_function']
        is_critical = module_config['critical']
        
        try:
            logger.info(f"{icon} Registrando callbacks de {module_name}...")
            logger.debug(f"Descripción: {description}")
            
            # Importación dinámica del módulo
            module = __import__(import_path, fromlist=[register_func], level=1)
            register_function = getattr(module, register_func)
            
            # Registro de callbacks del módulo
            register_function(app)
            
            logger.info(f"✅ Callbacks de {module_name} registrados exitosamente")
            successful_registrations += 1
            
        except ImportError as import_error:
            error_level = logger.error if is_critical else logger.warning
            error_level(
                f"📦 Error de importación en módulo {module_name}: {import_error}\n"
                f"Ruta: {import_path} | Función: {register_func}"
            )
            failed_registrations += 1
            
        except AttributeError as attr_error:
            error_level = logger.error if is_critical else logger.warning  
            error_level(
                f"🔍 Función '{register_func}' no encontrada en {module_name}: "
                f"{attr_error}"
            )
            failed_registrations += 1
            
        except Exception as general_error:
            error_level = logger.error if is_critical else logger.warning
            error_level(
                f"💥 Error general registrando {module_name}: {general_error}\n"
                f"Tipo: {type(general_error).__name__}"
            )
            failed_registrations += 1
    
    # ===================================================================
    #                    MÓDULOS OPCIONALES COMENTADOS
    # ===================================================================
    
    # Módulos que están temporalmente deshabilitados
    logger.debug("ℹ️ Módulos opcionales omitidos: ninguno")
    
    # ===================================================================
    #                    REPORTE FINAL DE REGISTRO
    # ===================================================================
    
    total_modules = successful_registrations + failed_registrations
    success_rate = (successful_registrations / total_modules * 100) if total_modules > 0 else 0
    
    if failed_registrations == 0:
        logger.info(
            f"🎉 ¡Registro completado exitosamente! "
            f"Todos los {successful_registrations} módulos registrados correctamente."
        )
    else:
        logger.warning(
            f"⚠️ Registro completado con advertencias:\n"
            f"   • Exitosos: {successful_registrations}\n"
            f"   • Fallidos: {failed_registrations}\n"
            f"   • Tasa de éxito: {success_rate:.1f}%"
        )
        
        if failed_registrations > successful_registrations:
            logger.error(
                "🚨 ALERTA: Más módulos fallaron que se registraron exitosamente. "
                "El dashboard podría tener funcionalidad limitada."
            )
    
    logger.info(f"📋 Resumen: {successful_registrations}/{total_modules} módulos operativos")