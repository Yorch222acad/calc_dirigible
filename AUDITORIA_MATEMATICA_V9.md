# Auditoría matemática y funcional V9 del dirigible híbrido

Revisión del 27 de noviembre de 2026 sobre el modelo v2. Los tres casos de V8 pasaron sus regresiones. Quedan dos discrepancias reproducibles. La primera afecta a la decisión de cuánta carga admite el candidato predeterminado cuando el usuario limita el empuje. La segunda afecta a la duración y al sentido de avance de misiones evaluadas a baja velocidad.

## 1. Alta · El análisis nominal y el intervalo de carga discrepan sobre la misma carga de 1 kg

**Reproducción.** Obtener el candidato predeterminado con la restricción de temperatura de 130 °C. Usarlo como base para un análisis directo, conservar su batería instalada y su carga de 1 kg, y activar dos reglas personalizadas: `Ttot <= 13` N y `Fexc >= 10` N. Comparar el resultado nominal con `carga_factible_instalada` y los extremos de carga de la misma respuesta.

| Resultado para 1 kg | Análisis nominal | Evaluación con batería instalada |
|---|---:|---:|
| Empuje máximo usado al calcular la reserva vertical | 22 N | 13 N |
| Excedente de sustentación calculado (`Fexc`) | 13,90 N | 2,22 N |
| Cumplimiento de `Fexc >= 10` N | Sí | No |

El empuje requerido es **12,22 N** y satisface el límite de 13 N. El análisis devuelve `encontrado=True` sin avisos de restricciones. La ficha devuelve `carga_factible_instalada=False` y ambos extremos en 0 kg. Esos ceros representan un intervalo vacío.

**Causa.** La ecuación nominal calcula la reserva con el empuje máximo instalado, `N * Tmax1`. El evaluador de carga introduce en la misma ecuación el menor valor entre el máximo instalado y el tope operativo de `Ttot`. Con cuatro motores de 5,5 N, cambiar de 22 N a 13 N en ese cálculo invierte el veredicto para el mismo equipo y la misma misión. [Ecuaciones de reserva vertical y excedente](modelo.py#L710) · [Cálculo del excedente para cada carga](evaluador.py#L974) · [Aplicación del tope operativo](evaluador.py#L1143)

**Corrección propuesta.** Conservar la definición de `Fexc` del modelo simbólico en las dos rutas. Calcular la reserva con el empuje instalado y aplicar por separado la regla de 13 N al empuje requerido en cada fase. Si el proyecto necesita medir también la reserva que queda bajo un tope operativo, identificar esa magnitud explícitamente.

**Prueba de aceptación.** Con esa definición, el análisis nominal y el evaluador de equipo fijo deben obtener aproximadamente 13,90 N de excedente para 1 kg. La ficha debe incluir 1 kg en el intervalo y ambos extremos publicados deben cumplir las dos reglas al reevaluarse. Como control, bajar el tope de empuje a 12 N: ambas rutas deben rechazar la carga nominal, cuyo empuje requerido es 12,22 N.

## 2. Media · El análisis directo eleva la velocidad solicitada a 0,2 m/s

**Reproducción.** Partir del candidato predeterminado, fijar `nv = 1`, `d1 = 0.5` m y `v = 0.1` m/s. Ejecutar un análisis directo con `ejecutar_optimizador=False`. Repetir con los dos valores de viento de la tabla. Comparar la entrada `v`, la velocidad de la ficha, la velocidad respecto al suelo `vg = v - vv` y el tiempo `tm`.

| Viento en contra | Resultado con la velocidad solicitada | Ficha del análisis directo |
|---:|---|---|
| 0 m/s | El modelo simbólico obtiene 0,1 m/s respecto al suelo y 5 s para recorrer 0,5 m. | Usa 0,2 m/s y muestra 2,5 s. |
| 0,12 m/s | La velocidad respecto al suelo es −0,02 m/s. El modelo simbólico rechaza la misión de avance. | Usa 0,2 m/s, obtiene +0,08 m/s respecto al suelo y muestra 6,25 s. |

**Causa.** La ruta rápida aplica `max(0.2, v)` antes de restar el viento, aunque la respuesta conserva 0,1 m/s como entrada del usuario. Así, una sola ficha puede combinar la velocidad solicitada con la duración de otra misión. [Cálculo de la velocidad en el evaluador](evaluador.py#L593)

**Corrección propuesta.** Conservar la velocidad solicitada al calcular `vg` y `tm`. Si existe un mínimo operativo, validarlo explícitamente e indicar en la respuesta el valor recibido y el mínimo exigido.

**Prueba de aceptación.** Para 0,1 m/s sin viento, comprobar que la duración sea 5 s si el dominio admite esa entrada, o que la API explique su rechazo si se establece un mínimo. Con viento en contra de 0,12 m/s, la misión debe quedar rechazada sin publicar una duración de avance. Probar también el valor exacto de 0,2 m/s sin viento, que debe conservarse y producir 2,5 s.

## Regresiones confirmadas en la revisión

- Con el presupuesto de recambio de 424,15 Bs, el máximo con batería redimensionada fue de 1,0000 kg y su costo recalculado fue de 424,14 Bs. Al desactivar la regla se recuperaron 1,0073 kg.
- Las misiones de 0,5, 1 y 2 m conservaron distancia, duración y costo por kilómetro en los casos de V8.
- El modelo, el evaluador y la ruta de diseño rechazaron espesores de −0,01 m y 0 m. La API devolvió el estado 400.
- Pasaron la suite matemática hasta V8 y las cinco pruebas de Chromium. Los casos de aceptación de V9 quedan pendientes de implementación y verificación.

Para repetir las regresiones existentes desde la raíz del proyecto:

```bash
venv_sus_d/bin/python -u auditar_modelo.py
venv_sus_d/bin/python -u auditar_frontend.py
```
