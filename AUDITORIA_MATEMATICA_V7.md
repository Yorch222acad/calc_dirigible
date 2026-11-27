# Auditoría matemática y funcional V7 del dirigible híbrido

Revisión del 27 de noviembre de 2026 sobre el modelo v2. Las cinco correcciones de V6 pasaron sus pruebas de regresión. Este informe documenta cinco hallazgos adicionales y propone cómo corregirlos y verificar su cierre. El de mayor prioridad permite que el optimizador devuelva una temperatura superior al techo de búsqueda.

## Resultados confirmados en la revisión

| Comprobación | Resultado |
|---|---|
| Restricción de costo operativo con batería instalada, sobre el candidato de referencia a 95 °C | Con `Cop >= 2.046` Bs, la carga admisible fue de 0,9719 a 1,0000 kg. Con `Cop <= 2.045` Bs, fue de 0,6716 a 0,9172 kg. |
| Casos Tipo | Las pruebas de porcentajes de sustentación y de títulos para trayectos de 280 y 330 m pasaron. |
| Chromium con Playwright | Pasaron las cuatro pruebas, incluidas la conservación del caso mostrado al guardar y la actualización de la base después de aplicar el óptimo. |
| Enfriamiento del diseño base | Para una caída de 20 K, el modelo simbólico y el evaluador numérico coincidieron al usar la capacidad térmica efectiva regional `Q / dT`. La energía extraída fue de 264,77 kJ y el tiempo de 157,98 s. |
| Optimizador con configuración predeterminada | Con el límite activo de 130 °C, encontró un candidato de 129,57 °C, 638,23 W de potencia pico y 48,28 puntos. |

La concordancia térmica verifica la implementación de la hipótesis adoptada. La temperatura admisible del conjunto construido y el tiempo real de enfriamiento requieren validación experimental.

## 1. Alta · El candidato inicial puede superar el techo de búsqueda

**Reproducción.** Obtener el candidato predeterminado. Conservar sus entradas, cambiar la temperatura inicial a 150 °C, desactivar la restricción editable de 130 °C y dejar solo `T2` como variable libre. Asignar todo el peso al indicador de costo de recambio. El optimizador devuelve 150 °C aunque el intervalo de búsqueda de `T2` termine en 140 °C.

**Causa.** El muestreo usa el intervalo calculado. El candidato inicial, en cambio, entra directamente en la clasificación cuando satisface las restricciones activas. [Admisión del candidato inicial](diseno.py#L911)

**Corrección propuesta.** Conservar la base original para la comparación «actual». Antes de admitir cualquier punto como candidato al óptimo, comprobar que todas sus variables libres estén dentro de sus intervalos efectivos. Una base fuera de rango puede seguir mostrándose al usuario y la búsqueda puede continuar dentro del intervalo.

**Prueba de aceptación.** Repetir el caso a 150 °C y comprobar que la base mostrada sigue siendo 150 °C y que cualquier óptimo devuelto cumple `T2 <= 140`. Volver a activar el límite de 130 °C y exigir `T2 <= 130`. Verificar también que un candidato inicial exactamente en el límite pueda participar si cumple las demás restricciones.

## 2. Media · El intervalo de carga omite la restricción de autonomía

**Reproducción.** Obtener el candidato predeterminado, mantener la batería instalada y activar `dm_aut <= 850` m. La autonomía nominal es de 840 m. En el extremo inferior publicado, 0,6668 kg, el evaluador de equipo fijo devuelve `valido=True`. Al recalcular la autonomía con esa carga se obtienen 914,84 m, por encima de la cota.

**Causa.** La preparación de límites para la búsqueda de carga incluye el costo operativo corregido en V6, pero omite `dm_aut`. [Límites del intervalo de carga](evaluador.py#L1097)

**Corrección propuesta.** Calcular la autonomía para cada carga ensayada con el combustible, la batería y la demanda eléctrica de ese punto. Reutilizar la relación que emplea la ficha, `min(dm * mp / mgm, dm * mbat / mbe)`. Incorporar las cotas inferior y superior de autonomía tanto en la búsqueda de extremos como en el evaluador de equipo fijo.

**Prueba de aceptación.** Para el máximo de 850 m, la carga nominal de 1 kg debe seguir admitiéndose y la de 0,6668 kg debe quedar excluida. Reintroducir los dos extremos publicados y verificar su autonomía de forma independiente. Repetir con una cota mínima para detectar una inversión del sentido de la desigualdad.

## 3. Media · La etiqueta «Óptimo seguro» de G7 excede lo que verifica la gráfica

**Reproducción.** Partir del candidato predeterminado y cambiar su temperatura inicial a 150 °C. En el panel A de G7, el punto marcado como «Óptimo seguro» resulta ser 130,8 °C. El filtro comprueba la viabilidad del equipo y una pérdida de sustentación de hasta el 16 % ante una caída de 10 K. La selección minimiza la energía de misión entre los puntos que pasan ese filtro. [Selección del punto en G7](graficas.py#L863)

**Corrección propuesta.** Si G7 conserva su función de análisis independiente, usar una etiqueta como «Mínima energía con equipo viable y pérdida de sustentación ≤ 16 % ante −10 K». Si el marcador debe representar el diseño admisible del usuario, pasarle también las restricciones activas del panel de diseño y aplicarlas antes de seleccionar el punto.

**Prueba de aceptación.** Mantener visible el barrido hasta 140 °C. En la modalidad independiente, el marcador debe identificar sus criterios. En la modalidad vinculada al diseño, con `T2 <= 130` activo, cualquier marcador debe estar a 130 °C o menos. Si ningún punto cumple, omitir el marcador.

## 4. Baja · La ficha atribuye el tiempo de enfriamiento a una caída fija de 20 K

**Reproducción.** En el diseño base, cambiar `dTc` de 20 K a 10 K. El tiempo calculado pasa de 157,98 s a 72,38 s. La ficha sigue mostrando «Enfriamiento 20K» junto al nuevo tiempo. [Rótulo de la ficha](frontend/js/components/designStudio.js#L792)

**Corrección propuesta.** Incluir la caída evaluada en las especificaciones que acompañan a `tc_s` y construir el rótulo con ambos valores del mismo análisis.

**Prueba de aceptación.** Comprobar en Chromium que la ficha del diseño base muestra 10 K junto a 72,38 s y, tras recalcular con 20 K, muestra 20 K junto a 157,98 s, con el redondeo propio de la interfaz.

## 5. Baja · El README conserva el límite y el tiempo de enfriamiento anteriores

| Dato del modelo vigente | Valor en el README | Valor verificado |
|---|---:|---:|
| Restricción inicial de temperatura | 95 °C | 130 °C |
| Tiempo de enfriamiento del diseño base para 20 K | 163,8 s | 157,98 s |

**Corrección propuesta.** Actualizar el ejemplo vigente y distinguir el límite editable de 130 °C del techo de búsqueda de 140 °C. Mantener la mención de 95 °C en las referencias históricas que efectivamente usen esa configuración. [Límite documentado](README.md#L41) · [Tiempo documentado](README.md#L62)

**Prueba de aceptación.** Contrastar el límite con la lista de restricciones predeterminadas y el tiempo con el resultado de resolver el diseño base. Si la tabla conserva una sola cifra decimal, el tiempo que corresponde publicar es 158,0 s.

## Comandos de regresión

Ejecutar desde la raíz del proyecto. Las suites cubren las regresiones hasta V6. Los casos de aceptación anteriores describen la cobertura adicional necesaria para cerrar V7.

```bash
venv_sus_d/bin/python -u auditar_modelo.py
venv_sus_d/bin/python -u auditar_frontend.py
```
