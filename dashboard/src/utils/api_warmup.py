"""
===============================================================================
                     SISTEMA DE WARMUP PARA APIS EXTERNAS
===============================================================================

🚀 DESCRIPCIÓN:
    Sistema inteligente de precalentamiento para APIs externas que realiza
    conexiones de prueba en segundo plano para evitar timeouts y fallos 
    en la primera carga del dashboard.

⚡ FUNCIONALIDADES:
    - Warmup automático de la API de AEMET
    - Ejecución en hilos separados (no bloquea inicio)
    - Manejo robusto de errores sin afectar el dashboard
    - Logging detallado del proceso de warmup
    - Configuración por defecto con municipio Benalúa

🎯 PROPÓSITO:
    - Reducir tiempo de primera carga de predicciones
    - Evitar errores de timeout en cold starts
    - Mejorar experiencia de usuario
    - Preparar conexiones SSL/TLS

🔧 USO:
    Se ejecuta automáticamente al importar el módulo dashboard.
    También puede ser invocado manualmente para testing.

👨‍💻 AUTOR: Sistema de Monitoreo Agrícola
📅 VERSION: 2024
🎯 PROPÓSITO: Optimización de APIs - Dashboard Agrícola

===============================================================================
"""

# ==============================================================================
# IMPORTS Y CONFIGURACIÓN
# ==============================================================================

import logging
import threading
import time
from .weather_utils import get_prediccion_diaria, get_municipio_code

# Logger específico para el sistema de warmup
logger = logging.getLogger(__name__)

# ==============================================================================
# FUNCIONES DE WARMUP ESPECÍFICAS
# ==============================================================================

def warmup_aemet_api():
    """
    🌡️ Precalienta la API de AEMET con una conexión de prueba
    
    Ejecuta una conexión de prueba a la API de AEMET usando el municipio
    por defecto (Benalúa) para preparar las conexiones SSL/TLS y reducir
    la latencia en la primera petición real del usuario.
    
    El proceso se ejecuta en un hilo separado para no bloquear el inicio
    del dashboard y maneja los errores de forma silenciosa.
    
    Note:
        - Se ejecuta en segundo plano (thread daemon)
        - No afecta el funcionamiento si falla
        - Usa municipio Benalúa como referencia por defecto
        - Los errores se registran pero no se propagan
        
    Example:
        >>> warmup_aemet_api()  # Inicia warmup en segundo plano
        🔥 Warmup de API iniciado en segundo plano
    """
    def _warmup_task():
        """
        Tarea interna que ejecuta el warmup real de AEMET
        
        Note:
            - Función interna ejecutada en hilo separado
            - Maneja todos los errores sin propagarlos
            - Registra el progreso completo del warmup
        """
        try:
            logger.info("🔥 Iniciando proceso de warmup para API AEMET...")
            
            # Paso 1: Obtener código del municipio por defecto
            cod_muni = get_municipio_code("Benalúa")
            if cod_muni:
                logger.info(f"🌡️ Realizando conexión de prueba para municipio {cod_muni} (Benalúa)")
                
                # Paso 2: Ejecutar petición de prueba sin guardar resultado
                test_data = get_prediccion_diaria(cod_muni)
                
                # Paso 3: Evaluar resultado del warmup
                if test_data:
                    logger.info("✅ Warmup completado exitosamente - API AEMET precalentada")
                else:
                    logger.warning("⚠️ Warmup parcial - API respondió pero sin datos válidos")
            else:
                logger.warning("⚠️ No se pudo obtener código de municipio para warmup")
                
        except Exception as e:
            # Los errores de warmup son normales y no deben afectar la aplicación
            logger.warning(f"⚠️ Warmup falló (comportamiento normal en algunos casos): {e}")
            logger.debug(f"Detalles del error de warmup: {type(e).__name__}: {str(e)}")
    
    # Configurar y lanzar hilo de warmup (daemon para no bloquear cierre)
    warmup_thread = threading.Thread(
        target=_warmup_task, 
        name="AemetWarmupThread",
        daemon=True
    )
    warmup_thread.start()
    logger.info("🚀 Warmup de API AEMET iniciado en segundo plano")

# ==============================================================================
# FUNCIÓN PRINCIPAL DE WARMUP
# ==============================================================================

def warmup_all_apis():
    """
    🚀 Inicia el warmup para todas las APIs externas del sistema
    
    Función orquestadora que coordina el precalentamiento de todas
    las APIs externas utilizadas por el dashboard. Incluye un delay
    inicial para permitir que el dashboard termine de inicializarse.
    
    APIs incluidas:
        - AEMET (Agencia Estatal de Meteorología)
        - Futuras APIs podrán agregarse aquí
    
    Note:
        - Se ejecuta con delay de 2 segundos tras inicio del dashboard
        - Cada API se precalienta en su propio hilo
        - Los errores no afectan el funcionamiento principal
        - Registra el progreso completo del proceso
        
    Example:
        >>> warmup_all_apis()
        🔥 Iniciando warmup de todas las APIs...
        🚀 Sistema de warmup configurado
    """
    logger.info("🔥 Iniciando sistema de warmup para todas las APIs externas...")
    
    # Delay inicial para permitir inicialización completa del dashboard
    logger.debug("⏱️ Esperando inicialización completa del dashboard...")
    time.sleep(2)
    
    # Warmup de API AEMET
    logger.info("🌡️ Iniciando warmup de API AEMET...")
    warmup_aemet_api()
    
    # Aquí se pueden agregar más APIs en el futuro:
    # warmup_satelite_api()
    
    logger.info("🚀 Sistema de warmup completamente configurado y activo")
    logger.debug("Todas las APIs externas están siendo precalentadas en segundo plano")


# ==============================================================================
# EJECUCIÓN DIRECTA PARA TESTING
# ==============================================================================

if __name__ == "__main__":
    """
    🧪 Modo de testing del sistema de warmup
    
    Permite probar el sistema de warmup de forma independiente
    con logging detallado para diagnóstico.
    """
    # Configurar logging más detallado para testing
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🧪 === TEST DEL SISTEMA DE WARMUP ===")
    print()
    
    # Test del warmup completo
    warmup_all_apis()
    
    # Esperar un poco para ver los resultados
    print("⏱️ Esperando resultados del warmup...")
    time.sleep(10)
    
    print()
    print("✅ Test completado - Revisar logs para detalles")
    print("🧪 === FIN DE TEST ===")
