# Auditoría matemática y funcional V8 del dirigible híbrido

Revisión del 27 de noviembre de 2026 sobre el modelo v2. Los cinco hallazgos de V7 pasaron sus regresiones, junto con las cinco pruebas de Chromium. Esta revisión identificó tres mejoras pendientes. La de mayor prioridad afecta a la capacidad de carga que publica la ficha y que el optimizador usa para puntuar diseños.

## 1. Alta · Aplicar el límite de costo de recambio al redimensionar la batería

**Reproducción.** Obtener el candidato predeterminado con el límite de temperatura de 130 °C. Mantener el precio de batería en 750 Bs/kg y añadir la restricción activa `c_recambio <= 424.15` Bs. Leer la capacidad con batería redimensionada. Para comprobarla de forma independiente, sustituir la carga nominal por la capacidad publicada, resolver de nuevo la masa de batería y calcular `mp * ccomb + mbat * cbat_kg`.

| Configuración | Carga útil | Costo de recambio recalculado | Cumple el presupuesto |
|---|---:|---:|---|
| Candidato nominal | 1,0000 kg | 424,14 Bs | Sí |
| Extremo publicado con batería redimensionada | 1,0073 kg | 425,43 Bs | No |

**Causa e impacto.** El diseño nominal cumple el presupuesto. Al ensayar cargas mayores, cambia la masa de batería necesaria. La búsqueda del extremo omite la restricción de recambio y el indicador de masa elevable usa esa capacidad. Esto puede afectar tanto a la ficha como a la comparación de candidatos. [Fórmula del costo](diseno.py#L464) · [Límites del intervalo](evaluador.py#L1110) · [Indicador de masa elevable](diseno.py#L514)

**Mejora propuesta.** Pasar el precio de batería del análisis al cálculo del intervalo. Para cada carga candidata, evaluar el costo con la masa de batería correspondiente y aplicar las cotas económicas activas. Comprobar el extremo con la precisión que se publica en la ficha.

**Prueba de aceptación.** En el caso anterior, 1 kg debe seguir siendo admisible y 1,0073 kg debe quedar excluido. El nuevo máximo publicado debe costar como máximo 424,15 Bs al recalcularlo de forma independiente. Cubrir también una cota inferior de recambio y comprobar que, con la restricción desactivada, se recupera la capacidad anterior.

## 2. Media · Conservar la distancia solicitada en misiones de menos de un metro

**Reproducción.** Partir del mismo candidato y ejecutar el análisis directo con `nv = 1` y `d1 = 0.5` m. El modelo simbólico obtiene `dm = 0.5` m mediante `dm = nv * d1`. El análisis de diseño devuelve una configuración factible cuya ficha indica `dm = 1.0` m.

**Causa e impacto.** El evaluador rápido eleva a un metro la distancia antes de calcular el tiempo de misión. El cálculo de indicadores también impone un mínimo de un metro a la distancia de misión y a la de un viaje. Corregir solo la cifra mostrada dejaría el tiempo o los indicadores calculados para otra distancia. [Distancia y duración](evaluador.py#L617) · [Distancias usadas por los indicadores](diseno.py#L456)

**Mejora propuesta.** Usar la distancia positiva validada en ambas rutas y conservar las identidades `dm = nv * d1` y `tm = dm / vg`. Proteger las divisiones comprobando que sus denominadores sean positivos.

**Prueba de aceptación.** Ejecutar el modelo simbólico y el análisis directo con un viaje de 0,5 m, 1 m y 2 m. Para cada caso, verificar que la ficha y los cálculos de duración usan la distancia solicitada. En el caso de 0,5 m, comprobar además que el costo por kilómetro usa 0,0005 km como divisor.

## 3. Media · Rechazar el espesor negativo antes de calcular la ficha

**Reproducción.** Enviar al análisis directo el candidato predeterminado con `e = -0.01` m. El modelo simbólico rechaza el espesor por estar fuera de dominio. El análisis de diseño conserva −0,01 m en las entradas y produce una ficha tras sustituir internamente el espesor por 0,00001 m. La respuesta marca el diseño como no factible, pero los valores mostrados corresponden a un espesor diferente del enviado. [Tratamiento del espesor en el evaluador rápido](evaluador.py#L496)

**Mejora propuesta.** Validar el dominio de `e` antes del cálculo de diseño y devolver un error que identifique la variable y el valor recibido. Aplicar el mismo criterio en el modelo simbólico y en el evaluador rápido.

**Prueba de aceptación.** Con `e = -0.01` y `e = 0`, ambas rutas deben rechazar la entrada y el análisis debe terminar sin generar una ficha calculada. Con el espesor positivo del candidato predeterminado, ambas rutas deben conservar el valor recibido y producir el resultado de referencia.

## Regresiones que deben seguir pasando

Ejecutar desde la raíz del proyecto después de implementar las mejoras. En la revisión previa, la suite matemática confirmó el límite editable de 130 °C, el techo de búsqueda de 140 °C y las cotas de autonomía corregidas en V7. En Chromium se comprobó, entre otros recorridos, que la ficha muestra 72,4 s para una caída de 10 K y 158,0 s para 20 K en el diseño base.

```bash
venv_sus_d/bin/python -u auditar_modelo.py
venv_sus_d/bin/python -u auditar_frontend.py
```
