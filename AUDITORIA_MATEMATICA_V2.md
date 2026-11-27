# Auditoría matemática v2 del dirigible híbrido

**Fecha:** 26 de noviembre de 2026. **Versión examinada:** copia de trabajo local con cambios sobre el commit `e1415db`. Ese commit por sí solo reproduce la versión anterior. **Alcance:** modelo simbólico, evaluador numérico, API, optimizador, indicadores, gráficas y pruebas de auditoría.

El candidato de 840 m cumple los límites que evalúa el programa con **1 kg de carga**, pero la ficha le atribuye **2.4194 kg**. Al reintroducir esa carga, la demanda sube a **1836.47 W** frente a 640 W disponibles. También se reprodujeron dos aceptaciones indebidas de diseños: una por reutilizar un límite eléctrico antiguo y otra por comprobar el ángulo de los motores solo durante la maniobra. Estos tres fallos afectan directamente a decisiones de construcción.

El **histórico v1** conserva sus entradas y resultados originales por decisión del proyecto. Los recálculos que siguen usan sus entradas como caso de comparación. Una ficha calculada y guardada en el futuro con el modelo v2 debe poder distinguirse de la ficha v1. [Registro original](especf_optm_hist/historico_dirigible_2026-11-25.json) · [Primera auditoría](AUDITORIA_MATEMATICA.md)

## Casos de referencia

Las potencias de la tabla corresponden a los motores. La batería se dimensiona con las reglas de la versión examinada. Se usa punto decimal para facilitar la reutilización de los números en código.

| Magnitud | Base actual | Entradas del histórico v1 recalculadas | Nuevo candidato |
|---|---:|---:|---:|
| Misión | 3 × 280 m | 2 × 330 m | 3 × 280 m |
| Duración de maniobra por tramo | 18 s | 5 s | 18 s |
| Potencia de maniobra | 1403.76 W | 1808.46 W | 638.01 W |
| Potencia de crucero | 1159.51 W | 935.91 W | 449.10 W |
| Batería requerida | 1.0515 kg | 1.3431 kg | 0.6676 kg |
| Empuje de maniobra | 23.47 N | 31.31 N | 12.79 N |
| Cumple las comprobaciones de hardware actuales | No | No | Sí |

La ficha v1 original indicaba **637.3 W**. Los **734.9 W** de la primera auditoría correspondían a cambiar únicamente la superficie y propagar su efecto a la batería. Los **1808.46 W** de la tabla incorporan además piel exterior, inercia del gas, flotabilidad por regiones y dimensionamiento por fases. Las tres cifras responden a cálculos distintos.

Para reproducir los ensayos que parten del nuevo candidato, ejecutar desde la raíz, con el entorno Python del proyecto:

```python
import diseno
import evaluador
import modelo

base = modelo.valores_iniciales()
resultado = diseno.optimizar_especificaciones(base)
candidato = resultado["entradas_optimo"]
sol = evaluador.evaluar_punto(candidato)
```

En la copia auditada la búsqueda predeterminada devuelve 47.59 puntos. Para repetir el mismo caso aunque cambie el muestreo, conservar las demás entradas de la base actual y fijar las siguientes:

```json
{"lam":3.321376,"v":7.626877396121883,"mflot":3.7514881790392467,"e":0.03195262551440329,"T2":94.990625,"ncapS":2,"ncapI":1,"mp":0.09329101340210347}
```

## Errores pendientes y criterios de corrección

### 1. Un límite de hardware antiguo puede hacer que la API acepte un diseño inviable

**Reproducción.** Guardar la lista de restricciones del nuevo candidato con cuatro motores de 160 W. Enviar al análisis directo las mismas entradas con `Pmax1=100`, `ejecutar_optimizador=False` y `respetar_limites=True`, reenviando la lista guardada. La API devuelve `encontrado=True`, `valido_hardware=False` y una lista vacía de avisos de restricciones activas. El aviso de hardware sí reconoce que se demandan 638.01 W frente a 400 W. Si se omite la lista antigua, la API genera el umbral correcto y rechaza el diseño.

**Causa e impacto.** La interfaz reenvía un umbral numérico. El ajuste automático del límite contempla determinados cambios de número de motores, pero en este caso solo cambia la potencia unitaria. Dos partes de la aplicación juzgan el mismo candidato con límites distintos. [Umbral efectivo](diseno.py#L208) · [Petición de la interfaz](frontend/js/components/designStudio.js#L1212)

**Corrección y aceptación.** Guardar por separado la elección «usar límite del equipo» y el eventual tope manual. Para cada candidato, calcular el límite del equipo con `N*Pmax1` y aplicar también cualquier tope más restrictivo. La misma comprobación debe alimentar la ficha, la API, los barridos y el optimizador. En el ensayo anterior todos deben informar un déficit de aproximadamente 238 W. La opción de explorar candidatos fuera de límite puede conservarse con su estado de hardware explícito.

### 2. La carga anunciada supera la que permite la misión

**Reproducción.** El candidato de referencia publica 2.4194 kg de capacidad útil. Introducir `mcarga=2.4194` en sus entradas eleva la demanda a 1836.47 W. Una búsqueda local entre 1.0 y 1.1 kg sitúa el límite en unos 1.0090 kg **con redimensionamiento de batería**, manteniendo las demás entradas.

**Causa e impacto.** La ficha suma `Fexc/g` a la carga actual. Ese cociente expresa el excedente de fuerza en unidades de masa en un punto de operación. Al aumentar la carga cambian también la fuerza de maniobra, la potencia y el consumo. El indicador entra en la puntuación del optimizador, de modo que el sesgo puede cambiar la arquitectura seleccionada. [Cálculo de capacidad útil](diseno.py#L352)

**Corrección y aceptación.** Para una ficha de construcción, fijar casco, propulsión, batería instalada y combustible embarcado. Variar la carga, resolver la misión completa y obtener el intervalo de cargas que cumple todos los límites. Explorar primero el intervalo permite detectar casos de exceso de flotación con poca carga. Al reintroducir la capacidad máxima publicada con el mismo equipo y misión, deben cumplirse los límites. Si se ofrece un estudio con batería redimensionable, etiquetarlo como tal.

### 3. Se omite el tope de inclinación durante el crucero

**Reproducción.** Partir del candidato y cambiar `mflot=4.171488179039247` kg, `mp=0.16` kg y `ta=30` s. Con el tope en 75°, la maniobra requiere 74.605°. Para el crucero horizontal, `atan2(FD, mres*g)` da **75.122°**. El evaluador marca el candidato como válido y el estudio con variables fijas lo acepta.

**Causa e impacto.** El ángulo que determina la aceptación se calcula con las componentes de fuerza de maniobra. En crucero cambia la proporción entre fuerza horizontal y vertical, incluso si disminuye el empuje total. [Ángulo y validez](evaluador.py#L702)

**Corrección y aceptación.** Calcular componentes horizontal y vertical, empuje, ángulo y potencia por fase. Comprobar todos los márgenes e identificar la fase limitante. El caso anterior debe quedar rechazado por el ángulo de crucero.

### 4. El casco sin aislamiento se acepta o se rechaza según la ruta

**Reproducción.** Usar la base con `ncapS=0` y `ncapI=0`. El evaluador usado en los barridos devuelve `U=U0=4.32577 W/(m²·K)`. El solucionador principal rechaza la misma configuración por inconsistencia en la caída térmica de la celda.

**Causa.** El evaluador fija `dTcel=0` cuando desaparecen las cámaras. La ecuación simbólica todavía exige una caída positiva y la correlación de Nusselt contiene una división por Rayleigh. Esto impide usar de manera coherente la piel simple como referencia para comparar arquitectura y costo. [Rama numérica](evaluador.py#L603) · [Ecuación de celda](modelo.py#L554)

**Corrección y aceptación.** Activar las ecuaciones de cada cámara solo cuando exista en la mitad correspondiente. Probar ambas rutas con 0/0, 1/0 y 0/1 capas. Para 0/0 deben coincidir `Vcel=0`, `Vnuc=V`, `Sc=S`, `U=U0` y `Qp=Qp0`, sin singularidades.

### 5. El precalentamiento usa temperaturas incompatibles con el balance de masas

**Reproducción.** La flotabilidad sitúa el núcleo a `T2` y las cámaras a una temperatura media `Tcel`. El cálculo de calor multiplica toda la masa de aire por `cp*(T2-T1)`. Usando las mismas masas finales y el mismo calor específico, el cálculo coherente con esas dos temperaturas es:

```text
m_nuc = rho2 * Vnuc
m_cel = rhocel * Vcel
Q = cp * (m_nuc * (T2 - T1) + m_cel * (Tcel - T1))
```

| Calor sensible | Base | Histórico recalculado |
|---|---:|---:|
| Programa | 960.82 kJ | 1190.90 kJ |
| Suma por regiones | 926.69 kJ | 1079.87 kJ |

**Impacto y aceptación.** La diferencia pasa a la energía y al costo de precalentamiento. Usar el mismo balance por regiones en el modelo simbólico y el evaluador. La suma anterior es una referencia computacional a masas finales. El consumo real depende además de cómo se llene el casco y de las pérdidas durante el calentamiento. [Ecuaciones de masa y calor](modelo.py#L468) · [Evaluador](evaluador.py#L535)

### 6. La sensibilidad térmica de G7 y el auxiliar de temperatura conservan el modelo de una región

**Reproducción.** En la base, G7 estima que una caída de 10 K reduce la flotabilidad un **11.8237 %**. Al mantener el casco fijo y actualizar las densidades del núcleo y las cámaras según la regla de temperatura media del propio modelo, la pérdida es **11.8648 %**. También se puede llamar a `evaluar_termica_T2(sol_base, sol_base["T2"])` en el punto base: devuelve **13.5629 kg** de aire frente a los **13.6577 kg** del evaluador principal a idéntica temperatura.

**Causa e impacto.** G7 calcula la pérdida con la diferencia de densidad del núcleo. El auxiliar aplica esa densidad al volumen completo. La discrepancia porcentual del ejemplo es pequeña, pero la curva interviene en la selección de temperaturas y el volumen de cámaras cambia con la arquitectura. [Sensibilidad de G7](graficas.py#L841) · [Masa del auxiliar](evaluador.py#L379)

**Corrección y aceptación.** Reutilizar el balance regional a geometría fija para ambas rutas. A la temperatura de referencia debe recuperarse la masa del modelo principal y la pérdida de empuje debe ser cero. Para una caída de 10 K, la gráfica debe coincidir con la diferencia de fuerzas calculadas antes y después en el mismo casco.

### 7. G7 compara vehículos con distinta contabilidad de energía

**Reproducción.** En el panel de escalabilidad, la fuerza horizontal del dron usa `map*ax` con la masa aparente del dirigible, que incluye su gas. Después calcula la energía del dron como potencia de maniobra por tiempo total. Para el dirigible ya se integran por separado maniobra y crucero.

**Impacto.** La batería calculada para el dron incorpora la inercia de otro vehículo y una duración de potencia pico incompatible con la comparación. La curva resulta insuficiente para sostener una conclusión sobre qué arquitectura consume menos para la misma misión. [Fuerza horizontal del dron](graficas.py#L856) · [Energía de misión](graficas.py#L862)

**Corrección y aceptación.** Compartir carga útil, recorrido, viento y duración de fases. Dar al dron masa, arrastre, propulsión y batería propios. Comprobar en ambos vehículos que la energía es la suma de potencia por duración de cada fase. Identificar los parámetros estimados del dron de referencia.

### 8. El script de la primera auditoría se detiene ante un rechazo correcto

**Reproducción.** Ejecutar `venv_sus_d/bin/python auditar_modelo.py`. En la prueba de cuatro motores de 100 W con restricciones recién generadas, el análisis ahora devuelve `optimo=None`. El script intenta leer `prueba["optimo"]["avisos"]` y termina con `TypeError`. Además, el antiguo escenario que añadía una piel al casco debe interpretarse como una segunda piel en la versión actual, que ya incluye la exterior.

**Corrección y aceptación.** Convertir los casos de esta auditoría en aserciones para v2. Comprobar explícitamente tanto los rechazos esperados como los candidatos factibles y conservar la integración geométrica independiente. La ejecución completa debe llegar al resumen aun cuando una prueba espere una excepción de dominio o un óptimo vacío. [Prueba original](auditar_modelo.py#L84)

## Hallazgos de la primera auditoría ya atendidos

| Hallazgo original | Estado verificado en la copia actual |
|---|---|
| Área curva insuficiente y piel exterior ausente del cálculo explícito | La integral independiente coincide con 40.6477 m² en la base y 46.4293 m² en el histórico recalculado. La masa incluye una piel exterior y el casco distingue núcleo y cámaras. |
| Inercia del gas omitida y maniobra cobrada durante todo el vuelo | El gas entra en la masa inercial del dirigible y la misión usa potencias y duraciones por fase. Sigue pendiente extender las comprobaciones de fase y corregir la comparación del dron. |
| Trabajo de arrastre calculado con distancia sobre el suelo | Se usa el recorrido respecto al aire, con 35.23 kJ para la base. |
| Enfriamiento lineal y entradas imposibles | El tiempo de enfriamiento usa la solución logarítmica a transmitancia constante. Se rechazan 3.5 motores, eficiencia de 150 % y caída de 80 K con diferencia inicial de 70 K. |
| Signos físicos invertidos por alertas | La fuerza de 31.28 N conserva su signo en los valores calculado y visible. |
| Combustible insuficiente aceptado en las gráficas y límite de temperatura omitido en análisis directo | La falta de combustible invalida el candidato. El análisis directo rechaza 100 °C ante el límite activo de 95 °C. |
| Resultado dependiente del orden de las variables libres | El orden original y el inverso devuelven el mismo candidato y 47.59 puntos en la prueba. La búsqueda sigue siendo heurística. |
| Documentación de otra configuración | El README actualizado describe las 169 variables, 62 entradas y 107 ecuaciones actuales, así como los nuevos valores de la base. |

En el barrido de 81 combinaciones, el evaluador estricto devolvió 41 soluciones y descartó 40. En las 41 soluciones, el máximo residuo escalado de las 107 ecuaciones fue **4.64e-13**. Los despejes de viajes a partir de distancia, de temperatura a partir de densidad y de masa compensada a partir de volumen recuperaron las entradas del ensayo. Fijar la transmitancia todavía admite dos espesores, aproximadamente **14.082 mm y 16.000 mm**. Ambos reproducen el objetivo en el cálculo directo. Asimismo, intercambiar las fracciones de nariz 0.35 y 0.65 conserva la superficie. Estas ambigüedades físicas requieren identificar la rama usada cuando se presenta una solución inversa. [Modelo y verificación de residuos](modelo.py#L1607) · [Descripción del modelo actual](README.md)

## Interpretación de márgenes y validación del prototipo

El nuevo candidato dispone de **1.99 W de margen de potencia** y **2.86 g de margen de combustible** según el modelo. La autonomía se obtiene extrapolando los consumos de la misión de referencia. Esa cifra depende de que al prolongar el vuelo se mantenga el perfil supuesto de tramos y maniobras. La carga útil y la autonomía deben acompañarse de la misión, el equipo instalado y los límites concretos que las determinan. [Indicadores de autonomía](diseno.py#L354)

La geometría corregida y la precisión del solucionador verifican el cálculo dentro de sus hipótesis. Para evaluar márgenes de construcción faltan la masa real de envolvente con uniones y refuerzos, las pérdidas térmicas medidas y la curva empuje–potencia de motor y hélice a la densidad de operación. También quedan por contrastar la temperatura media de las cámaras, el efecto de su inclinación sobre la convección, el arrastre de los accesorios y el factor común de masa añadida para ambos ejes. La correlación de casco y el modelo de hélice sirven como estimaciones preliminares; ninguna de esas mediciones se realizó en esta auditoría.

El criterio de cierre para el software v2 es que un candidato publicado como factible reproduzca su resultado al recargar sus entradas, que acepte la carga que anuncia con el equipo instalado y que indique qué fase y componente limitan la misión. El criterio experimental es contrastar esos márgenes con las mediciones del vehículo elegido.
