"""
Módulo de Cálculos Genéticos Básicos
Mantido para compatibilidade com código legado
"""

from backend.services.genetics_complete import genetic_calculator_complete

# Exportar calculadora completa como alias
genetic_calculator = genetic_calculator_complete

# Exportar funções individuais
calculate_pppv = genetic_calculator_complete.calculate_pppv_complete
calculate_inbreeding = genetic_calculator_complete.analyze_inbreeding_complete
calculate_compatibility = genetic_calculator_complete.calculate_compatibility_score_complete
