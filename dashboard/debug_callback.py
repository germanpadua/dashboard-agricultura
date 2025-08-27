#!/usr/bin/env python3
"""Debug específico del callback run_analysis"""

import sys
import os
sys.path.append('src')

def debug_callback():
    """Debug detallado del callback run_analysis"""
    print("=== DEBUG DEL CALLBACK RUN_ANALYSIS ===")
    
    try:
        from callbacks_refactored.datos_satelitales import register_callbacks
        from dash import Dash
        
        app = Dash(__name__)
        register_callbacks(app)
        
        print(f"Total callbacks registrados: {len(app.callback_map)}")
        
        # Listar todos los callbacks para ver cuáles están registrados
        print("\n--- TODOS LOS CALLBACKS REGISTRADOS ---")
        for i, (callback_id, callback_info) in enumerate(app.callback_map.items()):
            inputs = callback_info.get('inputs', [])
            outputs = callback_info.get('outputs', [])
            
            # Obtener IDs de inputs
            input_ids = []
            for inp in inputs:
                if hasattr(inp, 'component_id'):
                    input_ids.append(inp.component_id)
            
            # Obtener IDs de outputs  
            output_ids = []
            for out in outputs:
                if hasattr(out, 'component_id'):
                    output_ids.append(out.component_id)
            
            print(f"{i+1:2d}. Input IDs: {input_ids}")
            print(f"     Output IDs: {output_ids}")
            
            # Verificar si este es nuestro callback
            if 'run-analysis-btn' in input_ids:
                print(f"     *** ESTE ES EL CALLBACK QUE BUSCAMOS ***")
                
                # Verificar función del callback
                callback_func = callback_info.get('callback')
                if hasattr(callback_func, '__name__'):
                    print(f"     Funcion: {callback_func.__name__}")
                else:
                    print(f"     Funcion: {callback_func}")
                
                # Verificar estados
                states = callback_info.get('state', [])
                state_ids = []
                for state in states:
                    if hasattr(state, 'component_id'):
                        state_ids.append(state.component_id)
                print(f"     State IDs: {state_ids}")
                
                return True
            print()
        
        print("No se encontro callback con input 'run-analysis-btn'")
        return False
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_manual_callback():
    """Test manual del callback importando directamente la función"""
    print("\n=== TEST MANUAL DE LA FUNCION ===")
    
    try:
        # Intentar importar directamente la función
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "datos_satelitales", 
            "src/callbacks_refactored/datos_satelitales.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Buscar la función run_analysis
        if hasattr(module, 'run_analysis'):
            print("Funcion run_analysis encontrada en el módulo")
            func = getattr(module, 'run_analysis')
            print(f"Funcion: {func}")
            
            # Verificar que es callable
            if callable(func):
                print("La funcion es callable")
                return True
            else:
                print("ERROR: La funcion no es callable")
                return False
        else:
            print("ERROR: No se encontro la funcion run_analysis")
            return False
            
    except Exception as e:
        print(f"Error importando manualmente: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("INICIANDO DEBUG...")
    
    # Debug 1: Listar todos los callbacks
    callback_found = debug_callback()
    
    # Debug 2: Test manual de la función
    function_ok = test_manual_callback()
    
    print(f"\n{'='*50}")
    print("RESULTADO DEBUG:")
    print(f"  Callback registrado: {'SI' if callback_found else 'NO'}")
    print(f"  Funcion existe: {'SI' if function_ok else 'NO'}")
    
    if callback_found and function_ok:
        print("\nTODO CORRECTO: El callback está funcionando")
    elif function_ok and not callback_found:
        print("\nPROBLEMA: La función existe pero no se registra como callback")
        print("Posible causa: Error en la definición del decorator @app.callback")
    else:
        print("\nPROBLEMA: Hay errores en el código del callback")