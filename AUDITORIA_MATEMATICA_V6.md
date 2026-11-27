# Auditoría matemática y funcional V6 del dirigible híbrido

Revisión del 27 de noviembre de 2026 sobre la copia de trabajo del modelo v2. V6 identifica la versión del informe.

Las dos correcciones de V5 pasaron las regresiones. La revisión ampliada reprodujo cinco fallos y detectó una hipótesis térmica pendiente de justificar. El fallo de mayor impacto para el diseño está en el intervalo de carga útil. La ficha puede declarar admisible una carga que infringe una restricción activa del usuario.

## Pruebas que pasaron

| Comprobación | Resultado observado |
|---|---|
| Barrido del modelo | 50 de 81 puntos produjeron solución. El residuo relativo máximo en las soluciones aceptadas fue de 4,637 × 10⁻¹³. |
| Regresión V5 del intervalo estrecho | Con potencia motriz entre 607,30 y 607,31 W, ambos extremos publicados, 0,80001 y 0,80007 kg, pasaron la comprobación con batería instalada. |
| Regresión V5 del histórico | Los dos botones que guardan el último óptimo conservaron la puntuación y el costo del análisis después de editar el precio de batería y los pesos. |
| Frontend | Pasaron las cuatro pruebas existentes en Chromium con Playwright, incluidas la lectura de puntos sin solución en la gráfica G7 y la persistencia de las condiciones después de recalcular. Se utilizó un histórico temporal. |

Las suites existentes se ejecutan desde la raíz del proyecto con los siguientes comandos. Los cinco hallazgos siguientes proceden de comprobaciones adicionales.

```bash
venv_sus_d/bin/python -u auditar_modelo.py
venv_sus_d/bin/python -u auditar_frontend.py
```

## 1. Alta · El intervalo de carga admite un costo operativo fuera del límite

**Reproducción.** Obtener el óptimo predeterminado, conservar la batería instalada y añadir la restricción activa `Cop >= 2.046` Bs. Consultar el mínimo de carga de la ficha y evaluarlo de nuevo con el mismo equipo. Calcular el costo para esa carga como `Cpre + Ccomb + Ereq / 1000 * celecU`, usando la energía eléctrica de la misión con la carga modificada.

| Punto evaluado | Costo operativo | Cumple el mínimo de 2,046 Bs |
|---|---:|---|
| Diseño nominal | 2,04655 Bs | Sí |
| Extremo inferior publicado, 0,6716 kg | 2,04173 Bs | No |

El evaluador devuelve `valido=True` para el extremo inferior. La función que prepara las cotas del intervalo recoge, entre otras, potencia y energía total, pero omite el costo operativo, que varía con la energía requerida. [Construcción de límites](evaluador.py#L1085) · [Cálculo de costo](evaluador.py#L747)

**Criterio de aceptación.** Aplicar la restricción económica al buscar el intervalo y al comprobar los extremos. Con el caso anterior, ambos extremos publicados deben satisfacer `Cop >= 2.046` al recalcular el costo de forma independiente. Cubrir también una cota superior de costo.

## 2. Alta · Aplicar el óptimo deja una base anterior en el panel de diseño

**Reproducción en Chromium.** Abrir el panel de diseño con los valores iniciales, pulsar **Recalcular** y después **Aplicar óptimo al sistema**. Comparar la respuesta de `/api/modificar` con `entradas_actual` de la petición automática posterior a `/api/diseno/analizar`.

| Variable | Valor aplicado en el backend | Base del análisis posterior |
|---|---:|---:|
| Temperatura interior T2 | 94,990625 °C | 85 °C |
| Esbeltez λ | 3,764176 | 2,3 |
| Masa sustentada por aire caliente | 3,705695 kg | 3,2 kg |

El sistema sí aplica el óptimo. La discrepancia aparece cuando el panel reutiliza la petición del cálculo anterior, que contiene los valores base previos. Esto afecta a la comparación que el usuario ve inmediatamente después de aplicar el resultado. [Actualización del panel](frontend/js/main.js#L229)

**Criterio de aceptación.** Tras aplicar el óptimo, iniciar el análisis con las entradas que el backend acaba de confirmar. La respuesta y la columna de valores actuales del panel deben coincidir con ese estado en las tres variables del ejemplo, manteniendo los pesos y restricciones elegidos.

## 3. Alta · Guardar desde Casos Tipo cambia los valores archivados

**Reproducción en Chromium.** Calcular con una batería de 750 Bs/kg. Editar el precio a 1500 Bs/kg, abrir **Casos Tipo** sin recalcular y guardar la fila **Punto óptimo base**. Volver a leer el registro del histórico.

| Magnitud | Análisis de la fila guardada | Registro leído del histórico |
|---|---:|---:|
| Precio de batería | 750 Bs/kg | 1500 Bs/kg |
| Costo de recambio | 479,72 Bs | 957,84 Bs |
| Puntuación | 43,88 (43,9 en la tabla) | 39,35 |

El botón de la fila combina las entradas del caso con el precio y los pesos editables del formulario. La reproducción cambió únicamente el precio. Esta ruta de guardado es distinta de los dos botones del último óptimo ya corregidos en V5. [Guardado de una fila de Casos Tipo](frontend/js/components/designStudio.js#L1245)

**Criterio de aceptación.** Guardar cada caso con el precio y los pesos que generaron su fila. Al repetir la secuencia, el registro debe conservar 750 Bs/kg, 479,72 Bs y 43,88 puntos. Tras recalcular a 1500 Bs/kg, el siguiente registro debe coincidir con la nueva fila.

## 4. Media · El caso anunciado como 35 % de aire caliente solo alcanza el 21,7 %

**Reproducción.** Generar los casos tipo desde el óptimo predeterminado. En **Mayoría eléctrica (35% aire caliente)**, comparar el nombre con `especificaciones.frac_aire_pct`, calculado como `100 * mflot / mtot`. El valor obtenido es **21,7 %**, una diferencia de 13,3 puntos porcentuales.

Cuando la búsqueda de la masa correspondiente al porcentaje objetivo falla, el generador adopta 1,2 kg y conserva el título del 35 %. Esto altera la interpretación de la comparación entre sustentación térmica y eléctrica. [Búsqueda de la fracción](diseno.py#L1082) · [Valor de sustitución](diseno.py#L1139)

**Criterio de aceptación.** Verificar la fracción con la solución final antes de publicar el caso. Si el objetivo resulta inalcanzable, indicarlo en la fila. Si se ofrece una aproximación, mostrar el porcentaje alcanzado y distinguirlo del solicitado.

## 5. Baja · Los títulos de viajes conservan la distancia del trayecto predeterminado

**Reproducción.** Generar los casos con las entradas del histórico v1, cuyo trayecto individual mide 330 m. El título de la fila dice **3 viajes (840 m)** y su ficha calcula **990 m**, coherentes con tres trayectos de 330 m. Los títulos de uno, tres, cinco y siete viajes se construyen con distancias literales correspondientes a 280 m por trayecto. [Definición de los casos de viajes](diseno.py#L1202)

**Criterio de aceptación.** Formar el título con la distancia de misión del caso evaluado. Para tres viajes, verificar que el título y la ficha muestran 840 m con trayectos de 280 m y 990 m con trayectos de 330 m.

## Hipótesis térmica pendiente de justificar

En el cálculo de calentamiento, el incremento de temperatura de las celdas equivale a la mitad del incremento del núcleo. En el enfriamiento, las ecuaciones de energía extraída (`Qc`), velocidad inicial de enfriamiento (`vT`) y tiempo (`tc`) usan la capacidad térmica de toda la masa de aire. [Energía de calentamiento](evaluador.py#L589) · [Ecuaciones de enfriamiento](evaluador.py#L681)

Para el diseño base y una caída de **20 K** en el núcleo, la ecuación actual de enfriamiento da **274,52 kJ**. Si se conserva durante el enfriamiento la misma relación de temperaturas regionales que en el calentamiento, se obtienen **264,77 kJ**. La diferencia es de **9,75 kJ**.

**Verificación pendiente.** Definir qué temperatura representa la caída de 20 K y cómo evolucionan las celdas durante esa fase. Con esa hipótesis explícita, comprobar que energía, velocidad y tiempo de enfriamiento proceden del mismo balance. El residuo del barrido mide la precisión numérica con que se resuelven las ecuaciones. Para determinar qué hipótesis reproduce mejor el enfriamiento real hacen falta mediciones.
