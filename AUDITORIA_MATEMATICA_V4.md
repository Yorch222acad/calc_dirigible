# Auditoría matemática v4 del dirigible híbrido

**Fecha:** 27 de noviembre de 2026. **Objeto:** modelo de diseño v2 en la copia de trabajo local basada en `e1415db`. V4 identifica este informe. La copia examinada incluye cambios locales posteriores al commit.

Los cuatro casos de la [auditoría v3](AUDITORIA_MATEMATICA_V3.md) pasan las pruebas de regresión. Persisten dos fallos que afectan al uso de restricciones personalizadas. Primero, el cálculo de capacidad puede descartar una carga que el propio evaluador acepta con el mismo equipo. Segundo, guardar una ficha puede cambiar el intervalo de carga que el usuario acababa de aprobar. Ambos se reprodujeron sobre el candidato predeterminado de 840 m.

## 1. La búsqueda de carga puede pasar por alto todo un intervalo factible

| Condición del ensayo | Resultado |
|---|---|
| Equipo | Casco, motores, combustible y batería instalada del candidato predeterminado |
| Restricción adicional | Potencia motriz máxima de las fases entre 607 y 608 W |
| Ficha de capacidad | `carga_factible_instalada=False`, capacidad publicada de 0 kg |
| Evaluación directa con 0.8000 kg de carga | `valido=True`, potencia de maniobra de 607.30 W |

**Qué demuestra el ensayo.** Basta una carga aceptada para refutar la conclusión de que el intervalo está vacío. La batería se mantiene fija en las dos evaluaciones. La restricción inferior de potencia es una opción admitida por la interfaz y permite reproducir el problema sin modificar el hardware.

**Causa.** El algoritmo prueba primero 25 puntos uniformes, el entorno de la carga nominal y algunos puntos derivados de las cotas de masa. Si toda la malla falla, devuelve inmediatamente una capacidad de cero. El refinamiento por bisección empieza solo después de encontrar una muestra factible. Las dos fronteras de potencia pueden quedar entre muestras consecutivas. [Malla inicial](evaluador.py#L1171) · [Salida cuando falla la malla](evaluador.py#L1189) · [Evaluación directa del equipo instalado](evaluador.py#L1086)

**Corrección propuesta.** Para el equipo instalado, usar las fronteras de las restricciones activas para delimitar el intervalo de carga. En los tramos donde la potencia varíe monótonamente con la carga, se pueden localizar por separado los cruces de 607 y 608 W, intersectarlos con el resto de las cotas y verificar los extremos antes de publicarlos. Si la búsqueda agota sus muestras sin poder demostrar inviabilidad, distinguir «búsqueda inconclusa» de «intervalo vacío». Aumentar la densidad de la misma malla solo reduce la probabilidad de repetir el error.

**Criterio de cierre.** Con las reglas originales en cualquier orden, la ficha debe devolver un intervalo factible que incluya 0.8000 kg. Sus extremos publicados deben pasar el evaluador directo con las mismas reglas y la misma batería. Conviene conservar también un caso cuyas cotas sean incompatibles y produzcan efectivamente un intervalo vacío.

## 2. El histórico v2 cambia la ficha al guardarla con restricciones personalizadas

| Operación sobre el mismo candidato | Carga mínima publicada con batería fija |
|---|---:|
| Analizar y aceptar con masa total `mtot >= 4.1 kg` | 0.8423 kg |
| Guardar desde la ruta de histórico y leer el registro creado | 0.6716 kg |

**Qué cambia para el usuario.** El diseño nominal con 1 kg cumple la restricción. El error afecta a lo que después se consulta en su ficha: el histórico indica que se puede operar con unos 171 g menos de carga que el mínimo aprobado. Preservar una ficha v1 al importarla, que ya funciona, y preservar el análisis vigente al guardar un diseño v2 son operaciones distintas.

**Causa.** La petición de guardado transmite las entradas físicas, los pesos y el costo de batería. Omite las restricciones del análisis. El constructor del registro vuelve a evaluar las entradas con sus valores predeterminados y guarda esa nueva ficha. Se pierde tanto el límite de masa como la información necesaria para reproducir el resultado aprobado. [Petición de guardado](app.py#L244) · [Ruta de guardado](app.py#L415) · [Constructor del registro](diseno.py#L1288)

**Corrección propuesta.** Guardar la ficha que el backend validó junto con las entradas, la versión del modelo y las restricciones normalizadas que utilizó. Si el backend recalcula al guardar, debe recibir las mismas restricciones activas, operadores, unidades y topes de equipo o manuales.

**Criterio de cierre.** Analizar, guardar y recuperar el caso de 4.1 kg debe conservar la regla y el mismo intervalo de carga, incluida la cota de 0.8423 kg a la precisión publicada. Repetir el ciclo después de exportar e importar la ficha debe conservar también la procedencia del registro.

## Reproducción de los dos hallazgos

Ejecutar este bloque desde la raíz del proyecto con `venv_sus_d/bin/python`. El guardado usa exclusivamente un directorio temporal. Las salidas de referencia están en las tablas anteriores.

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import app
import diseno
import evaluador
import modelo

resultado = diseno.optimizar_especificaciones(modelo.valores_iniciales())
candidato = resultado["entradas_optimo"]
equipo = evaluador.evaluar_punto(candidato)
reglas_equipo = resultado["restricciones"]

def regla(variable, operador, valor):
    return dict(variable=variable, op=operador, valor=valor, activa=True, grupo="custom")

reglas = reglas_equipo + [regla("Pelec", ">=", 607), regla("Pelec", "<=", 608)]
ficha = diseno.evaluar_indicadores(equipo, restricciones=reglas)["especificaciones"]
limites = diseno._limites_efectivos_mapa(equipo, reglas)
directo = evaluador.evaluar_punto_equipo_fijo(equipo, 0.8, limites)
print("Capacidad en ficha (kg)", ficha["carga_factible_instalada"], ficha["capacidad_util_kg"])
print("Prueba directa con 0.8 kg", directo["valido"], round(directo["Pelec"], 2), "W")

peticion = app.PeticionAnalisisDiseno(
    variables=[], base_overrides=candidato, ejecutar_optimizador=False,
    respetar_limites=True, restricciones=reglas_equipo + [regla("mtot", ">=", 4.1)],
)
analisis = app.analizar_diseno(peticion)
print("Aceptado y mínimo analizado (kg)", analisis["encontrado"],
      analisis["actual"]["especificaciones"]["mcarga_min_kg"])
with TemporaryDirectory() as carpeta:
    with patch.object(diseno, "HISTORICO_PATH", Path(carpeta) / "historico.json"):
        app.guardar_en_historico(app.PeticionGuardarHistorico(nombre="Prueba v4", entradas=candidato))
        guardado = diseno.cargar_historico()[0]
        print("Mínimo recuperado del histórico (kg)", guardado["especificaciones"]["mcarga_min_kg"])
```

## Resultados anteriores que se mantienen

El [script de regresión](auditar_modelo.py) completa las pruebas de v2 y v3. Se comprobaron el sentido físico de los límites de hardware, la coexistencia de cotas mínimas y máximas de masa, la importación intacta de v1 y la creación de una reevaluación v2 separada. G7 identifica al dron que excede el equipo y conserva los huecos cuando faltan datos. El barrido produjo 50 soluciones en 81 combinaciones, con residuo escalado máximo de 4.637e-13 en las 108 ecuaciones evaluadas.

En la misión predeterminada, la ficha admite **1.0000 kg** con batería instalada de **0.6375 kg**. Calcula **639.63 W** de maniobra y **450.50 W** de crucero frente a **640 W** disponibles. Los dos hallazgos de esta revisión aparecieron al aplicar restricciones personalizadas. El margen nominal de **0.37 W** sigue siendo una predicción cuya suficiencia para el vehículo real depende de las mediciones del conjunto motor–hélice.
