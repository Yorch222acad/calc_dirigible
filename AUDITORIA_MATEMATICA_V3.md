# Auditoría matemática v3 del dirigible híbrido

**27 de noviembre de 2026.** Tercera revisión del modelo de diseño v2, ejecutada sobre la copia de trabajo local con cambios sobre `e1415db`. La numeración v3 corresponde al informe. El histórico v1 conserva su valor como registro de los resultados calculados en su momento.

Los ocho casos de la [auditoría v2](AUDITORIA_MATEMATICA_V2.md) superan las pruebas actuales. Esta revisión reproduce cuatro problemas adicionales. Los dos primeros afectan a la aceptación de diseños y a la carga útil publicada; los otros dos afectan a la conservación de resultados y a la interpretación de la comparativa con el dron.

## Referencia para repetir las pruebas

Desde la raíz del proyecto, ejecutar `venv_sus_d/bin/python auditar_modelo.py` para reproducir las pruebas de v2. Los cuatro ensayos adicionales que se documentan abajo se ejecutaron por separado. Para obtener el candidato y sus restricciones con el mismo intérprete:

```python
import app
import diseno
import evaluador
import modelo

base = modelo.valores_iniciales()
resultado = diseno.optimizar_especificaciones(base, respetar_limites=True)
candidato = resultado["entradas_optimo"]
reglas = resultado["restricciones"]
sol = evaluador.evaluar_punto(candidato)
```

| Magnitud del candidato de referencia | Resultado |
|---|---:|
| Misión y carga nominal | 840 m con 1.0000 kg |
| Potencia motriz de maniobra / crucero | 639.63 / 450.50 W |
| Potencia motriz disponible | 640 W |
| Masa de batería instalada | 0.6375 kg |
| Intervalo de carga con esa batería | 0.6716–1.0000 kg |
| Máximo con batería redimensionable | 1.0015 kg |
| Puntuación del candidato | 43.88 puntos |

La carga nominal pasa al reintroducirla con el equipo instalado. El margen de potencia en maniobra es **0.37 W**, cerca del 0.06 % del límite. Es un margen calculado. Su suficiencia en vuelo depende, entre otras cosas, de la potencia y el empuje medidos para la hélice y el motor a la densidad de operación.

## 1. Una regla editable permite invertir el máximo físico de potencia

**Reproducción.** Partir del candidato anterior. Cambiar `Pmax1` a 100 W manteniendo cuatro motores y modificar el operador de la regla activa `hw_Pelec` de `<=` a `>=`, opción que ofrece el selector de la interfaz. Enviar la petición de análisis directo con `respetar_limites=True`, `ejecutar_optimizador=False`, `variables=[]`, las entradas modificadas en `base_overrides` y la lista modificada en `restricciones`.

**Resultado.** El equipo dispone de 400 W. El cálculo requiere 639.63 W en maniobra y 450.50 W en crucero. La API devuelve simultáneamente `encontrado=True`, `actual.valido_hardware=False` y `avisos_restricciones_actual=[]`. La ficha sí avisa de déficits de 239.6 W y 50.5 W. Así, una configuración expresamente evaluada con límites de hardware activos puede aparecer como encontrada aun excediendo ambos límites de fase.

**Causa y corrección.** La regla de búsqueda utiliza el operador elegido en el panel; el aviso físico sigue comparando la demanda con la potencia disponible. La dirección del límite de placa pertenece al equipo. Una potencia mínima solicitada por el usuario debe ser una regla adicional que coexista con el máximo físico. Aplicar esta semántica también en el backend para peticiones directas. [Selector](frontend/js/components/designStudio.js#L363) · [Umbral efectivo](diseno.py#L256) · [Avisos de hardware](diseno.py#L537)

**Criterio de cierre.** Con el hardware exigido, el caso de 400 W debe quedar rechazado tanto en el análisis directo como en la búsqueda, con el déficit visible. Conservar la prueba existente en la que un máximo manual de 500 W restringe un equipo de 640 W.

## 2. Una masa total mínima se interpreta como máxima al calcular la carga útil

**Reproducción.** Mantener el equipo y la misión del candidato y añadir a las reglas activas esta restricción personalizada:

```json
{"variable":"mtot","grupo":"custom","op":">=","valor":1.0,"activa":true}
```

**Resultado.** La masa total es 4.2578 kg y satisface la regla. La API devuelve `encontrado=True` y `valido_hardware=True` con 1 kg de carga a bordo, pero `actual.especificaciones.capacidad_util_kg` cae a **0.0 kg**. Un límite inferior de 1 kg sobre la masa **total** no justifica descartar la carga nominal de ese mismo vehículo.

**Causa y corrección.** El mapa de límites conserva un único par operador–valor por variable. El cálculo del intervalo toma el valor asociado a `mtot` y lo usa como máximo. Conservar por separado las cotas inferior y superior, y comprobar ambas para cada carga. Esto permite también representar un intervalo cuando el usuario impone dos reglas de sentido opuesto. [Consolidación de reglas](diseno.py#L283) · [Cálculo del intervalo](evaluador.py#L1045)

**Criterio de cierre.** Al añadir `mtot >= 1 kg`, el intervalo publicado debe seguir incluyendo la carga nominal de 1 kg. Añadir también una cota superior y repetir con las reglas en orden inverso debe dar el mismo intervalo. Sus extremos publicados deben pasar al reintroducirlos con la batería instalada.

## 3. Importar una ficha v1 la recalcula como v2 bajo la misma identidad

**Reproducción.** En un proceso de prueba, apuntar `diseno.HISTORICO_PATH` a un archivo nuevo dentro de un directorio temporal. Leer el [JSON exportado de v1](especf_optm_hist/historico_dirigible_2026-11-25.json) y pasar su lista de registros a `diseno.importar_historico`. Se usó un histórico vacío para que el filtro de identificadores duplicados no ocultara el comportamiento.

| Campo | Exportación v1 | Tras importar en un histórico vacío |
|---|---|---|
| Identificador y nombre | Originales | Los mismos |
| Potencia motriz almacenada | 637.3 W | 1808.5 W |
| Versión del registro importado | Ficha histórica de v1 | Marcada como v2 |

**Causa e impacto.** El importador llama al constructor de registros nuevos, que evalúa las entradas con el modelo actual y asigna la versión v2. La diferencia de potencia es esperable al recalcular. El defecto es que una operación de importación altera los resultados archivados mientras conserva la identidad anterior. Una copia de respaldo restaurada deja de representar el resultado guardado. [Importación](diseno.py#L1304) · [Construcción del registro](diseno.py#L1241)

**Criterio de cierre.** Exportar e importar en vacío debe conservar identificador, fecha, resultados y procedencia del registro v1. Una reevaluación solicitada expresamente debe producir una ficha v2 separada, con un identificador nuevo y una referencia a la ficha de origen. Ambas deben poder consultarse juntas.

## 4. G7 puede dibujar una batería de dron inviable o un cero sin solución

**Balance matemático frente a capacidad del equipo.** Para la misma misión del candidato, `evaluar_dron_referencia(sol)` encuentra una batería de **2.1303 kg** que cierra su cálculo de energía y potencia. Sin embargo, el dron requiere **1706.31 W motrices** de maniobra frente a **640 W** disponibles, y **39.02 N** de empuje frente a **22 N**. Para comparar potencias equivalentes se restan los 45 W auxiliares de los 1751.31 W eléctricos totales. G7 decide dibujar la batería a partir de `factible_cierre`, que solo informa de la raíz del balance. La curva puede así sugerir que bastaría con instalar esa batería. [Evaluación del dron](evaluador.py#L1177) · [Selección de puntos de G7](graficas.py#L876)

**Tratamiento del dato ausente.** En la gráfica de la configuración **base**, el barrido devuelve `null` para la batería del dron en la muestra `nv=4.37`. El frontend pasa ese valor a la transformación numérica de coordenadas; JavaScript lo convierte en cero en la resta. La polilínea conecta el punto con sus vecinos. El dato representa una muestra sin solución calculada, no una batería de 0 g. Este hallazgo se comprobó en los datos del backend y en el código del trazado. [Transformación del eje](frontend/js/components/charts.js#L153) · [Construcción de la polilínea](frontend/js/components/charts.js#L368)

**Criterio de cierre.** Entregar por muestra tanto el estado del cierre de batería como la factibilidad de potencia, empuje y masa de batería respecto al equipo utilizado. La vista puede mostrar una estimación teórica si identifica que ese equipo no permite volar. Para muestras sin solución, interrumpir la curva y omitir el marcador. Un valor numérico de cero y un dato ausente deben conservar significados distintos.

## Qué quedó verificado respecto de v2

- **Hardware y carga de la configuración predeterminada.** Se rechazaron la regla reenviada de 640 W al bajar los motores a 400 W y el tope manual más restrictivo de 500 W. La ficha distingue capacidad con batería instalada y con batería redimensionable.
- **Ángulo por fase y aislamiento.** El caso de 74.605° en maniobra y 75.122° en crucero se rechazó ante un máximo de 75°. Las rutas simbólica y numérica coincidieron con 0/0, 1/0 y 0/1 capas.
- **Cálculos térmicos.** El calor sensible regional dio 926.69 kJ en la base y 1079.87 kJ al recalcular las entradas históricas. El auxiliar térmico recuperó los 13.6577 kg de aire de la base. La disminución de flotabilidad calculada para una caída de 10 K fue del 11.8648 %.
- **Comparación energética y ejecución completa.** El dron usa masa propia y energía por fases. El script llegó al resumen final. En 81 combinaciones, el evaluador estricto devolvió 50 soluciones y descartó 31. En las soluciones, el máximo residuo escalado de las 108 ecuaciones fue 4.637e-13. Estos resultados comprueban la consistencia numérica en el barrido; la medición del comportamiento del prototipo sigue pendiente. [Pruebas de auditoría](auditar_modelo.py)

Para cerrar esta revisión deben coincidir la decisión de factibilidad, la carga que anuncia la ficha y los límites del equipo al reproducir los casos 1 y 2. Los casos 3 y 4 requieren además que la procedencia de un registro y el estado de una muestra sobrevivan al paso desde el cálculo hasta la información que consulta el usuario.
