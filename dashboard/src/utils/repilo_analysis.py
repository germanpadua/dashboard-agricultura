"""
Sistema de Análisis de Riesgo de Repilo (Venturia oleaginea).

Basado en condiciones científicas para olivicultura. Este módulo proporciona
herramientas para analizar el riesgo de desarrollo del hongo Venturia oleaginea
en base a condiciones meteorológicas.

Autor: Sistema de Monitoreo Agrícola
Fecha: 2024
"""

# Librerías estándar
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Librerías de terceros
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class RepiloRiskAnalyzer:
    """
    Analizador de riesgo de repilo basado en condiciones meteorológicas.
    
    Implementa las condiciones científicas de Venturia oleaginea según
    literatura especializada en fitopatología de olivos.
    """
    
    def __init__(self) -> None:
        """
        Inicializa el analizador con condiciones de riesgo basadas en evidencia científica.
        """
        # Definición de condiciones de riesgo basadas en la tabla científica
        self.risk_conditions = {
            'alto': [
                {
                    'name': 'Optimal_Wet_Continuous',
                    'description': '15-20°C y mojado continuo',
                    'temp_range': (15, 20),
                    'wet_hours_min': 18,
                    'humidity_threshold': 95,
                    'action': 'Tratamiento preventivo/pos-evento'
                },
                {
                    'name': 'Consecutive_Wet_Episodes',
                    'description': 'Episodios consecutivos con mojado',
                    'temp_range': (12, 22),
                    'consecutive_days': 2,
                    'wet_hours_per_day': 8,
                    'action': 'Activar plan de control; priorizar focos históricos'
                }
            ],
            'moderado': [
                {
                    'name': 'Suboptimal_Temperature',
                    'description': '12-15°C (o 20-22°C) con mojado',
                    'temp_ranges': [(12, 15), (20, 22)],
                    'wet_hours_min': 12,
                    'humidity_threshold': 95,
                    'action': 'Vigilancia estrecha; intervenir si se repite'
                },
                {
                    'name': 'High_Humidity_Nocturnal',
                    'description': 'Hum. rel. >95% y 12-20°C nocturno',
                    'temp_range': (12, 20),
                    'humidity_threshold': 95,
                    'nocturnal_hours': 10,
                    'action': 'Alerta local; mejora de aireación (poda)'
                }
            ],
            'bajo': [
                {
                    'name': 'Unfavorable_Temperature',
                    'description': '<5°C o >25-28°C y mojado limitado',
                    'temp_ranges': [(float('-inf'), 5), (28, float('inf'))],
                    'wet_hours_max': 6,
                    'action': 'Seguimiento rutinario; sin intervención'
                }
            ]
        }
    
    def analyze_repilo_risk(
        self, df: pd.DataFrame, hours_window: int = 48
    ) -> Dict:
        """
        Analiza el riesgo de repilo en las últimas horas.
        
        Args:
            df: DataFrame con datos meteorológicos
                Debe contener columnas: 'Dates', 'Air_Temp', 'Air_Relat_Hum', 'Rain'
            hours_window: Ventana de análisis en horas (por defecto 48h)
            
        Returns:
            Diccionario con análisis completo de riesgo de repilo
        """
        # Validar entrada
        if df.empty or 'Dates' not in df.columns:
            return self._get_no_data_result()
            
        try:
            # Preparar datos
            df_recent = self._prepare_recent_data(df, hours_window)
            
            if df_recent.empty:
                return self._get_no_data_result()
            
            # Analizar cada tipo de riesgo
            risk_analysis = {
                'overall_risk': 'bajo',
                'risk_level_numeric': 0,  # 0=bajo, 1=moderado, 2=alto
                'active_conditions': [],
                'recommendations': [],
                'risk_periods': [],
                'current_status': self._get_current_status(df_recent),
                'trends': self._analyze_trends(df_recent),
                'analysis_period': {
                    'start': df_recent['Dates'].min().strftime('%Y-%m-%d %H:%M'),
                    'end': df_recent['Dates'].max().strftime('%Y-%m-%d %H:%M'),
                    'hours': len(df_recent)
                }
            }
            
            # Evaluar condiciones de alto riesgo
            high_risk_found = self._evaluate_high_risk(df_recent, risk_analysis)
            
            # Evaluar condiciones de riesgo moderado si no hay alto riesgo
            if not high_risk_found:
                moderate_risk_found = self._evaluate_moderate_risk(df_recent, risk_analysis)
                
                # Si no hay riesgo moderado, evaluar bajo riesgo
                if not moderate_risk_found:
                    self._evaluate_low_risk(df_recent, risk_analysis)
            
            # Agregar zonas de riesgo para gráficos
            risk_analysis['risk_zones'] = self._identify_risk_zones(df_recent)
            
            return risk_analysis
            
        except Exception as e:
            logger.error(f"Error en análisis de riesgo de repilo: {e}")
            return self._get_error_result(str(e))
    
    def _prepare_recent_data(
        self, df: pd.DataFrame, hours_window: int
    ) -> pd.DataFrame:
        """Prepara datos recientes para análisis.
        
        Args:
            df: DataFrame con datos meteorológicos
            hours_window: Ventana de horas a considerar
            
        Returns:
            DataFrame filtrado y procesado con columnas adicionales
        """
        df = df.copy()
        
        # Asegurar que Dates es datetime
        if not pd.api.types.is_datetime64_any_dtype(df['Dates']):
            df['Dates'] = pd.to_datetime(df['Dates'], errors='coerce')
        
        # Filtrar últimas horas
        cutoff_time = df['Dates'].max() - timedelta(hours=hours_window)
        df_recent = df[df['Dates'] >= cutoff_time].copy()
        
        # Agregar columnas calculadas
        df_recent['is_wet'] = (df_recent['Air_Relat_Hum'] >= 95) | (df_recent['Rain'] > 0)
        df_recent['hour'] = df_recent['Dates'].dt.hour
        df_recent['is_nocturnal'] = (df_recent['hour'] >= 20) | (df_recent['hour'] <= 6)
        
        return df_recent.sort_values('Dates')
    
    def _evaluate_high_risk(self, df: pd.DataFrame, analysis: Dict) -> bool:
        """Evalúa condiciones de alto riesgo.
        
        Args:
            df: DataFrame con datos meteorológicos procesados
            analysis: Diccionario de análisis a actualizar
            
        Returns:
            True si se encontró condición de alto riesgo
        """
        high_risk_found = False
        
        for condition in self.risk_conditions['alto']:
            if condition['name'] == 'Optimal_Wet_Continuous':
                if self._check_optimal_wet_continuous(df, condition):
                    analysis['overall_risk'] = 'alto'
                    analysis['risk_level_numeric'] = 2
                    analysis['active_conditions'].append(condition['description'])
                    analysis['recommendations'].append(condition['action'])
                    high_risk_found = True
                    
            elif condition['name'] == 'Consecutive_Wet_Episodes':
                if self._check_consecutive_wet_episodes(df, condition):
                    analysis['overall_risk'] = 'alto'
                    analysis['risk_level_numeric'] = 2
                    analysis['active_conditions'].append(condition['description'])
                    analysis['recommendations'].append(condition['action'])
                    high_risk_found = True
        
        return high_risk_found
    
    def _evaluate_moderate_risk(self, df: pd.DataFrame, analysis: Dict) -> bool:
        """Evalúa condiciones de riesgo moderado.
        
        Args:
            df: DataFrame con datos meteorológicos procesados
            analysis: Diccionario de análisis a actualizar
            
        Returns:
            True si se encontró condición de riesgo moderado
        """
        moderate_risk_found = False
        
        for condition in self.risk_conditions['moderado']:
            if condition['name'] == 'Suboptimal_Temperature':
                if self._check_suboptimal_temperature(df, condition):
                    analysis['overall_risk'] = 'moderado'
                    analysis['risk_level_numeric'] = 1
                    analysis['active_conditions'].append(condition['description'])
                    analysis['recommendations'].append(condition['action'])
                    moderate_risk_found = True
                    
            elif condition['name'] == 'High_Humidity_Nocturnal':
                if self._check_high_humidity_nocturnal(df, condition):
                    analysis['overall_risk'] = 'moderado'
                    analysis['risk_level_numeric'] = 1
                    analysis['active_conditions'].append(condition['description'])
                    analysis['recommendations'].append(condition['action'])
                    moderate_risk_found = True
        
        return moderate_risk_found
    
    def _evaluate_low_risk(self, df: pd.DataFrame, analysis: Dict) -> None:
        """Evalúa condiciones de bajo riesgo.
        
        Args:
            df: DataFrame con datos meteorológicos procesados
            analysis: Diccionario de análisis a actualizar
        """
        analysis['overall_risk'] = 'bajo'
        analysis['risk_level_numeric'] = 0
        analysis['recommendations'].append('Seguimiento rutinario; sin intervención urgente')
    
    def _check_optimal_wet_continuous(
        self, df: pd.DataFrame, condition: Dict
    ) -> bool:
        """Verifica condición: 15-20°C y mojado continuo ≥18-24h.
        
        Args:
            df: DataFrame con datos meteorológicos
            condition: Diccionario con condiciones a verificar
            
        Returns:
            True si se cumple la condición de riesgo
        """
        temp_min, temp_max = condition['temp_range']
        
        # Identificar períodos con temperatura óptima y humedad alta
        optimal_conditions = (
            (df['Air_Temp'] >= temp_min) & 
            (df['Air_Temp'] <= temp_max) & 
            (df['is_wet'])
        )
        
        if not optimal_conditions.any():
            return False
        
        # Buscar períodos continuos
        continuous_hours = self._find_continuous_periods(optimal_conditions)
        return max(continuous_hours, default=0) >= condition['wet_hours_min']
    
    def _check_consecutive_wet_episodes(
        self, df: pd.DataFrame, condition: Dict
    ) -> bool:
        """Verifica episodios consecutivos con mojado ≥2-3 días con ≥8-12h/día.
        
        Args:
            df: DataFrame con datos meteorológicos
            condition: Diccionario con condiciones a verificar
            
        Returns:
            True si se cumple la condición de riesgo
        """
        # Agrupar por día
        df['date'] = df['Dates'].dt.date
        daily_wet_hours = df.groupby('date')['is_wet'].sum()
        
        # Días con suficientes horas húmedas
        wet_days = daily_wet_hours >= condition['wet_hours_per_day']
        
        if wet_days.sum() < condition['consecutive_days']:
            return False
        
        # Buscar días consecutivos
        consecutive_days = self._find_consecutive_days(wet_days)
        return max(consecutive_days, default=0) >= condition['consecutive_days']
    
    def _check_suboptimal_temperature(
        self, df: pd.DataFrame, condition: Dict
    ) -> bool:
        """Verifica temperatura subóptima con mojado 12-18h.
        
        Args:
            df: DataFrame con datos meteorológicos
            condition: Diccionario con condiciones a verificar
            
        Returns:
            True si se cumple la condición de riesgo
        """
        temp_ranges = condition['temp_ranges']
        
        for temp_min, temp_max in temp_ranges:
            suboptimal_conditions = (
                (df['Air_Temp'] >= temp_min) & 
                (df['Air_Temp'] <= temp_max) & 
                (df['is_wet'])
            )
            
            if suboptimal_conditions.any():
                continuous_hours = self._find_continuous_periods(suboptimal_conditions)
                if max(continuous_hours, default=0) >= condition['wet_hours_min']:
                    return True
        
        return False
    
    def _check_high_humidity_nocturnal(
        self, df: pd.DataFrame, condition: Dict
    ) -> bool:
        """Verifica humedad >95% nocturna con temperatura 12-20°C ≥10-12h.
        
        Args:
            df: DataFrame con datos meteorológicos
            condition: Diccionario con condiciones a verificar
            
        Returns:
            True si se cumple la condición de riesgo
        """
        temp_min, temp_max = condition['temp_range']
        
        nocturnal_high_humidity = (
            (df['Air_Temp'] >= temp_min) & 
            (df['Air_Temp'] <= temp_max) & 
            (df['Air_Relat_Hum'] > condition['humidity_threshold']) &
            (df['is_nocturnal'])
        )
        
        if not nocturnal_high_humidity.any():
            return False
        
        continuous_hours = self._find_continuous_periods(nocturnal_high_humidity)
        return max(continuous_hours, default=0) >= condition['nocturnal_hours']
    
    def _find_continuous_periods(self, condition_series: pd.Series) -> List[int]:
        """Encuentra períodos continuos donde la condición es True.
        
        Args:
            condition_series: Serie booleana con condiciones
            
        Returns:
            Lista con duración de períodos continuos
        """
        periods = []
        current_period = 0
        
        for value in condition_series:
            if value:
                current_period += 1
            else:
                if current_period > 0:
                    periods.append(current_period)
                    current_period = 0
        
        if current_period > 0:
            periods.append(current_period)
        
        return periods
    
    def _find_consecutive_days(self, wet_days_series: pd.Series) -> List[int]:
        """Encuentra días consecutivos con condiciones de riesgo.
        
        Args:
            wet_days_series: Serie booleana con días de riesgo
            
        Returns:
            Lista con duración de períodos consecutivos
        """
        periods = []
        current_period = 0
        
        for value in wet_days_series:
            if value:
                current_period += 1
            else:
                if current_period > 0:
                    periods.append(current_period)
                    current_period = 0
        
        if current_period > 0:
            periods.append(current_period)
        
        return periods
    
    def _get_current_status(self, df: pd.DataFrame) -> Dict:
        """Obtiene el estado actual de las condiciones.
        
        Args:
            df: DataFrame con datos meteorológicos
            
        Returns:
            Diccionario con estado actual de las variables meteorológicas
        """
        if df.empty:
            return {}
        
        latest = df.iloc[-1]
        return {
            'temperature': float(latest['Air_Temp']),
            'humidity': float(latest['Air_Relat_Hum']),
            'is_wet': bool(latest['is_wet']),
            'timestamp': latest['Dates'].strftime('%Y-%m-%d %H:%M')
        }
    
    def _analyze_trends(self, df: pd.DataFrame) -> Dict:
        """Analiza tendencias en las variables clave.
        
        Args:
            df: DataFrame con datos meteorológicos
            
        Returns:
            Diccionario con tendencias de temperatura, humedad y horas húmedas
        """
        if len(df) < 2:
            return {}
        
        return {
            'temperature_trend': 'increasing' if df['Air_Temp'].iloc[-1] > df['Air_Temp'].iloc[0] else 'decreasing',
            'humidity_trend': 'increasing' if df['Air_Relat_Hum'].iloc[-1] > df['Air_Relat_Hum'].iloc[0] else 'decreasing',
            'wet_hours_last_24h': int(df.tail(24)['is_wet'].sum()) if len(df) >= 24 else int(df['is_wet'].sum())
        }
    
    def _identify_risk_zones(self, df: pd.DataFrame) -> List[Dict]:
        """Identifica zonas de riesgo para resaltar en gráficos.
        
        Args:
            df: DataFrame con datos meteorológicos
            
        Returns:
            Lista de diccionarios con zonas de riesgo identificadas
        """
        risk_zones = []
        
        # Zona de humedad alta (>95%)
        high_humidity_mask = df['Air_Relat_Hum'] > 95
        if high_humidity_mask.any():
            risk_zones.append({
                'type': 'humidity_risk',
                'description': 'Humedad > 95% (Riesgo Repilo)',
                'color': 'rgba(255, 193, 7, 0.3)',  # Amarillo warning
                'data': df[high_humidity_mask]
            })
        
        # Zona de temperatura óptima para repilo (15-20°C)
        optimal_temp_mask = (df['Air_Temp'] >= 15) & (df['Air_Temp'] <= 20)
        if optimal_temp_mask.any():
            risk_zones.append({
                'type': 'temperature_optimal',
                'description': 'Temp. óptima repilo (15-20°C)',
                'color': 'rgba(220, 53, 69, 0.2)',  # Rojo danger
                'data': df[optimal_temp_mask]
            })
        
        # Zona de condiciones combinadas críticas
        critical_mask = (
            (df['Air_Temp'] >= 15) & (df['Air_Temp'] <= 20) & 
            (df['Air_Relat_Hum'] > 95)
        )
        if critical_mask.any():
            risk_zones.append({
                'type': 'critical_combined',
                'description': 'Condiciones críticas combinadas',
                'color': 'rgba(220, 53, 69, 0.4)',  # Rojo intenso
                'data': df[critical_mask]
            })
        
        return risk_zones
    
    def _get_no_data_result(self) -> Dict:
        """Resultado cuando no hay datos suficientes.
        
        Returns:
            Diccionario con estructura estándar indicando falta de datos
        """
        return {
            'overall_risk': 'desconocido',
            'risk_level_numeric': -1,
            'active_conditions': [],
            'recommendations': ['No hay datos suficientes para evaluar riesgo'],
            'risk_periods': [],
            'current_status': {},
            'trends': {},
            'risk_zones': [],
            'error': 'Datos insuficientes'
        }
    
    def _get_error_result(self, error_message: str) -> Dict:
        """Resultado en caso de error.
        
        Args:
            error_message: Mensaje de error descriptivo
            
        Returns:
            Diccionario con estructura estándar indicando error
        """
        return {
            'overall_risk': 'error',
            'risk_level_numeric': -1,
            'active_conditions': [],
            'recommendations': ['Error en el análisis de riesgo'],
            'risk_periods': [],
            'current_status': {},
            'trends': {},
            'risk_zones': [],
            'error': error_message
        }

# Instancia global del analizador para uso conveniente
repilo_analyzer = RepiloRiskAnalyzer()

def analyze_repilo_risk(df: pd.DataFrame, hours_window: int = 48) -> Dict:
    """
    Función de conveniencia para analizar riesgo de repilo.
    
    Esta función utiliza la instancia global del analizador para
    proporcionar un análisis rápido del riesgo de repilo.
    
    Args:
        df: DataFrame con datos meteorológicos
        hours_window: Ventana de análisis en horas (por defecto 48)
        
    Returns:
        Diccionario con análisis completo de riesgo
    """
    return repilo_analyzer.analyze_repilo_risk(df, hours_window)