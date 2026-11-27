# Auditoría matemática v5 del dirigible híbrido

**Fecha:** 27 de noviembre de 2026. **Modelo examinado:** v2, en la copia de trabajo local con cambios sobre `e1415db`. V5 es la versión del informe.

Las pruebas de las auditorías v2, v3 y v4 pasaron en la última revisión. Quedan dos problemas de consistencia entre el cálculo y su uso: una carga que se vuelve inviable al redondearla para la ficha y un registro histórico que puede combinar el último óptimo con parámetros económicos editados después del análisis.

## 1. La ficha publica una carga que el propio evaluador rechaza

**Cómo reproducirlo.** Obtener el candidato predeterminado para 840 m y 1 kg. Mantener fija su batería instalada y añadir dos restricciones activas de potencia motriz: `Pelec >= 607.30 W` y `Pelec <= 607.31 W`. Consultar el intervalo de carga publicado. Reintroducir los extremos con el evaluador de equipo fijo y las mismas restricciones.

| Carga útil | Potencia de maniobra | Resultado |
|---:|---:|---|
| 0.80000 kg | 607.299365 W | Inferior al mínimo |
| 0.80004 kg | 607.304811 W | Cumple |
| 0.80010 kg | 607.312980 W | Superior al máximo |

**Resultado observado.** La ficha marca el intervalo como factible y publica **0.8001 kg en ambos extremos**. Ese valor excede el límite en 0.002980 W. La banda contiene una solución, pero ninguno de los dos valores contiguos representables con cuatro decimales (0.8000 y 0.8001 kg) permite reproducirla.

**Origen.** La búsqueda intenta redondear los extremos y, en ciertos casos, conserva seis decimales. Al construir la ficha, se aplica de nuevo un redondeo fijo a cuatro decimales. Una comprobación realizada antes de esa última transformación no garantiza que la cifra publicada cumpla los límites. [Redondeo en el evaluador](evaluador.py#L1423) · [Construcción de la ficha](diseno.py#L662)

**Corrección y criterio de aceptación.** Conservar los extremos factibles en los datos del resultado y elegir suficientes decimales al mostrarlos. Validar cada extremo **después** de darle la precisión con la que se podrá copiar, guardar o reintroducir. Para la banda anterior, ambos valores publicados deben pasar el cálculo de equipo fijo y el intervalo debe contener 0.80004 kg. Conservar asimismo la prueba de v4 para 607–608 W, cuya solución publicada de 0.7978–0.8051 kg ya es reproducible.

## 2. Guardar el último óptimo puede cambiar su puntuación y costo de recambio

**Cómo reproducirlo.** Calcular el óptimo con precio de batería de 750 Bs/kg. Anotar la puntuación y el costo de recambio. Cambiar el precio a 1500 Bs/kg y pulsar «Guardar último óptimo» antes de ejecutar otro análisis. Volver a leer el registro. En la revisión se inspeccionó el manejador del botón y se reprodujo su petición contra la API con almacenamiento temporal.

| Magnitud | Último análisis mostrado | Registro guardado |
|---|---:|---:|
| Precio utilizado | 750 Bs/kg | 1500 Bs/kg |
| Costo de recambio | 479.72 Bs | 957.84 Bs |
| Puntuación total | 43.88 | 39.35 |

**Origen.** El botón toma las entradas y restricciones del análisis previo, junto con los pesos y el precio de batería presentes en el formulario en el instante del guardado. El backend recalcula con la combinación recibida. El ensayo numérico cambió solo el precio; la lectura del código muestra que los pesos se toman del mismo estado editable. Los dos botones que permiten guardar el óptimo siguen este patrón. [Guardado desde la ficha](frontend/js/components/designStudio.js#L818) · [Guardado desde el histórico](frontend/js/components/designStudio.js#L897)

**Corrección y criterio de aceptación.** Guardar entradas, restricciones, pesos y precio desde el mismo resultado aprobado. Si el usuario cambia el precio o los pesos sin recalcular, guardar el último óptimo debe conservar íntegra la ficha anterior. Si luego recalcula y guarda, el nuevo registro debe coincidir con el nuevo resultado. Probar ambas secuencias desde los dos botones, verificando costo, puntuación y parámetros después de leer el archivo histórico.

## Bloque de reproducción

Ejecutar con `venv_sus_d/bin/python` desde la raíz del proyecto. La segunda prueba imita la petición de guardado observada en el frontend. Usa un archivo temporal para poder comparar el resultado aprobado con el registro leído desde disco.

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import app
import diseno
import evaluador
import modelo

opt = diseno.optimizar_especificaciones(modelo.valores_iniciales(), cbat_kg=750)
entradas = opt["entradas_optimo"]
equipo = evaluador.evaluar_punto(entradas)
reglas = opt["restricciones"] + [
    dict(variable="Pelec", op=op, valor=valor, activa=True, grupo="custom")
    for op, valor in ((">=", 607.30), ("<=", 607.31))
]
limites = diseno._limites_efectivos_mapa(equipo, reglas)
ficha = diseno.evaluar_indicadores(equipo, restricciones=reglas)["especificaciones"]
print("Extremos publicados (kg)", ficha["mcarga_min_kg"], ficha["capacidad_util_kg"])
for carga in (0.80000, 0.80004, ficha["capacidad_util_kg"]):
    potencia = evaluador.evaluar_punto_equipo_fijo(equipo, carga)["Pelec"]
    aceptada = evaluador.evaluar_punto_equipo_fijo(equipo, carga, limites) is not None
    print("Carga (kg), potencia (W), cumple", carga, round(potencia, 6), aceptada)

ultimo = opt["optimo"]
print("Análisis: puntos y Bs", ultimo["score_total"], ultimo["especificaciones"]["c_recambio"])
with TemporaryDirectory() as carpeta:
    with patch.object(diseno, "HISTORICO_PATH", Path(carpeta) / "historico.json"):
        app.guardar_en_historico(app.PeticionGuardarHistorico(
            nombre="Prueba v5", entradas=entradas, cbat_kg=1500,
            restricciones=opt["restricciones"], respetar_limites=True,
        ))
        registro = diseno.cargar_historico()[0]
        print("Histórico: puntos y Bs", registro["score_total"],
              registro["especificaciones"]["c_recambio"])
```

## Estado de la auditoría anterior

La [auditoría v4](AUDITORIA_MATEMATICA_V4.md) comprobaba la búsqueda de intervalos de carga estrechos y la conservación de restricciones al guardar. Sus dos casos originales pasan. Con `mtot >= 4.1 kg`, la carga mínima de 0.8423 kg se conserva al guardar, leer, exportar, importar y reevaluar. También pasan las pruebas de v2 y v3, incluida la conservación del histórico v1 al importarlo. [Script de regresión](auditar_modelo.py)

Para la misión predeterminada de 840 m con 1 kg, el candidato sigue calculando **639.63 W en maniobra y 450.50 W en crucero** frente a un límite de 640 W. El margen calculado de 0.37 W sigue pendiente de contraste con mediciones del equipo.
