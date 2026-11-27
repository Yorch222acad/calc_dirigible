# Auditoría matemática del dirigible híbrido de aire caliente

El diseño guardado el 25 de noviembre de 2026 aparece como viable con **637,3 W de potencia motriz frente a 640 W disponibles**. La ecuación de superficie omite parte del área curva de ambos extremos del casco. Al incorporar esa área al cálculo de la masa de película y resolver de nuevo la batería y la propulsión, la potencia estimada sube a **734,9 W**. El diseño guardado excede así el límite continuo en **94,9 W** bajo las demás hipótesis originales. La potencia real en vuelo requiere mediciones.

## Alcance y reproducción

La revisión corresponde al código local basado en el commit `e1415db`, al [histórico exportado](especf_optm_hist/historico_dirigible_2026-11-25.json) y al [generador CAD local](generar_cad_solidworks.py). El estado de la API contiene 163 variables, 62 entradas fijas, 101 ecuaciones distintas, 13 categorías y 7 gráficas. La auditoría incluye cálculos directos e inversos, restricciones, datos enviados a la interfaz y un contraste geométrico independiente. Los números siguientes usan punto decimal para facilitar su extracción. Las cifras de potencia son eléctricas y corresponden a los motores, salvo indicación expresa.

El [script de auditoría](auditar_modelo.py) reproduce las pruebas numéricas con los datos de esta revisión. Desde la raíz del proyecto, en el entorno local auditado, se ejecuta con:

```bash
venv_sus_d/bin/python auditar_modelo.py
```

Se comparan dos configuraciones con misiones distintas. La base usa 3 tramos de 280 m, velocidad respecto al aire de 8.5 m/s, viento frontal de 6 m/s y temperatura interior de 85 °C. El histórico usa 2 tramos de 330 m, 7.68 m/s respecto al aire, el mismo viento y 93.3 °C en el interior. Las columnas ajustadas de la tabla son cálculos de sensibilidad para esas mismas configuraciones. Las pruebas reproducen el comportamiento del software. Las hipótesis sobre el vehículo construido se identifican por separado.

## 1. Geometría y propagación del error

El casco une dos semielipsoides de revolución por su sección de radio máximo `R`. Para cada mitad prolada, `c` es la longitud axial desde esa sección hasta la punta. La excentricidad `ecc` es adimensional. El área curva de una mitad y el volumen de ambas son:

```text
ecc = sqrt(1 - (R/c)^2)
S_mitad = pi*R^2 + pi*R*c*asin(ecc)/ecc
S_total = S_mitad(R, cf) + S_mitad(R, cr)
V_total = (2/3)*pi*R^2*(cf + cr)
```

La rama prolada implementa únicamente el segundo sumando de `S_mitad`. La diferencia total es exactamente `2*pi*R^2`. Aunque el término omitido tiene las dimensiones y el valor del área de un disco, proviene de integrar la **superficie curva**. Una comprobación sencilla es el límite esférico: cuando `c` tiende a `R`, la expresión implementada tiende a `pi*R^2` y un hemisferio tiene área curva `2*pi*R^2`. El script integra numéricamente el perfil de revolución y el volumen por secciones. El volumen coincide en ambos diseños. SymPy y el evaluador rápido comparten la fórmula equivocada del área. [Ecuaciones simbólicas](modelo.py#L465) · [Rama estricta](evaluador.py#L452) · [Función de área de los barridos](evaluador.py#L104)

| Magnitud | Unidad | Base original | Base con área corregida | Histórico original | Histórico con área corregida |
|---|---|---:|---:|---:|---:|
| Superficie exterior S | m² | 29.5791 | 39.8641 | 34.9731 | 44.0841 |
| Pérdida térmica Qp a igual U | W | 1436.4 | 1935.8 | 1313.5 | 1655.7 |
| Masa de película mc según el conteo actual | kg | 0.7081 | 0.9543 | 1.1619 | 1.4646 |
| Masa de batería mbat | kg | 0.9719 | 1.0796 | 0.6744 | 0.7709 |
| Potencia motriz Pelec | W | 1104.6 | 1232.0 | 637.3 | 734.9 |

Para reproducir la tabla se mantienen las dimensiones, el combustible embarcado, las eficiencias y el perfil de misión. Se calcula `Qp = U*S*dT` con el área integrada. Como la masa de película es proporcional al producto de superficie y gramaje, el script multiplica el gramaje por `S_corregida/S_original` **solo dentro del ensayo numérico**. Así introduce la masa corregida en el lazo original sin cambiar el material físico. El lazo recalcula la batería que hace falta para sostener y mover la masa adicional. La base ya superaba los 640 W y, tras el ajuste, supera también el límite de batería de 1 kg.

### Piel exterior y masa de material

Las resistencias térmicas cuentan `ncap + 1` películas por sección. En cambio, la fórmula `Sc = ncap*S*(1 + 2*e/W)` de la configuración multicapa cuenta una lámina por capa celular más el material de los tabiques. El CAD representa además una piel exterior. Hay que identificar en el inventario qué pieza corresponde a cada lámina y si la piel está incluida en la masa adicional `mad`. Si queda fuera del inventario, una piel de 44.0841 m² con gramaje de 8.4 g/m² aporta unos **370 g**. Con esa hipótesis adicional, la potencia calculada del histórico sube a **921.5 W**. La tabla principal excluye esa hipótesis. Para un despiece real también conviene usar el área de cada capa interior y contabilizar uniones y refuerzos. [Masa de película](evaluador.py#L575) · [Capas representadas en CAD](generar_cad_solidworks.py#L399)

## 2. Solucionador y cálculos inversos

Se evaluaron 81 combinaciones de velocidad, temperatura interior, esbeltez y número de capas. El evaluador estricto devolvió 47 soluciones y descartó 34 puntos. En las 47 soluciones se sustituyeron los resultados en las 101 ecuaciones. El máximo de `abs(izquierda-derecha)/max(1, abs(izquierda), abs(derecha))` fue **4.7e-13**. Esto aporta evidencia de consistencia numérica en el barrido. Un descarte solo indica que esa ruta de cálculo rechazó el punto. El error compartido de superficie ilustra por qué también se necesita una referencia independiente. [Verificación global y solucionador](modelo.py#L1552)

| Intercambio de variables | Resultado reproducido |
|---|---|
| Fijar distancia total y liberar número de viajes | Para 560 m y tramos de 280 m se recuperan 2 viajes. |
| Fijar densidad caliente y liberar temperatura | Para 0.643867 kg/m³ se recuperan 90 °C con las restantes entradas del ensayo. |
| Fijar volumen y liberar masa compensada por flotación | Para 21.437896 m³ se recuperan 3.4 kg. |
| Fijar transmitancia U y liberar espesor celular e | El cálculo directo con 16.000 mm da 0.6907344 W/(m²·K). El inverso devuelve 14.081 mm. Ambos espesores reproducen el mismo U en el cálculo directo. |

En el último caso, las dos construcciones pertenecen a regímenes diferentes. A 14.081 mm el modelo da `Nuc = 1` y a 16.000 mm da aproximadamente `Nuc = 1.316`. Un residuo diminuto puede corresponder a cualquiera de las dos raíces. Hay otra simetría ilustrativa: intercambiar las longitudes de nariz y cola conserva la superficie total. En la base, las fracciones de nariz 0.35 y 0.65 dan el mismo valor de `S`. Cuando una magnitud se usa como entrada inversa, el intervalo o la rama física elegidos forman parte del resultado.

## 3. Optimización y límites de factibilidad

El estudio combina seis indicadores mediante pesos y referencias relativas a la base. Una puntuación de 50 expresa una valoración dentro de esa escala. El rendimiento físico se juzga con magnitudes como potencia, empuje, ángulo, energía y combustible. La búsqueda muestrea puntos con una secuencia de Halton y luego refina candidatos localmente. [Puntuación](diseno.py#L444) · [Restricciones de candidatos](diseno.py#L488) · [Muestreo](diseno.py#L629)

| Prueba | Resultado observado | Consecuencia |
|---|---|---|
| Ajustes predeterminados del optimizador | 53.93 puntos y 1090.7 W frente a 640 W. Se muestra una alerta. | Los límites de hardware están desactivados inicialmente. Una búsqueda exitosa puede devolver un diseño que excede el equipo instalado. |
| Mismos pesos y límites de hardware activos | 44.64 puntos. Al invertir solo el orden de las ocho variables libres, se obtuvieron 45.91 puntos. | El cambio de orden modifica la exploración. El primer candidato es mejorable bajo el mismo objetivo. |
| Histórico con cuatro motores limitados a 100 W cada uno, sin variables libres y con límites exigidos | Se devuelve `encontrado=True` junto con el aviso «637 W > 400 W». | Cuando las entradas carecen del valor derivado `Pmax`, la restricción predeterminada usa 640 W. El aviso posterior sí calcula los 400 W del equipo configurado. |
| Análisis directo con `ejecutar_optimizador=False`, temperatura de 100 °C y límite activo de 95 °C | Se devuelve `encontrado=True`, una evaluación válida, 100 °C como óptimo y la lista de avisos de restricciones vacía. | Esta ruta declara éxito sin comprobar el límite activo. |
| Histórico con 5 g de combustible a bordo | Se requieren 27.52 g. El indicador `valido` usado en las curvas sigue siendo verdadero. El optimizador descarta ese mismo candidato. | La etiqueta de validez tiene distinto alcance según dónde se consulte. |

Una comprobación común de factibilidad, calculada a partir del equipo y de las restricciones activas de cada candidato, permitiría que la ficha, las curvas y la búsqueda informen el mismo resultado para una misma misión. [Restricciones por defecto](diseno.py#L137) · [Ruta de análisis directo](app.py#L365) · [Indicador de validez](evaluador.py#L666) · [Filtro de las curvas](graficas.py#L86)

## 4. Interfaz y dominios físicos

Cuando salta una alerta de hardware, la presentación invierte el signo de varias magnitudes de sustentación. En la base, la API devuelve `F = +31.28 N` y `valor_vista = -31.28 N`. El empuje aerostático sigue apuntando hacia arriba mientras el sistema avisa de la sobrepotencia. Conservar su signo físico y expresar la infracción mediante el mensaje y el color evitaría que se interprete como fuerza descendente. [Transformación de valores visibles](formateo.py#L72)

El solucionador principal también aceptó, por separado, `N = 3.5` motores, `ncal = 1.5` (150 % de eficiencia del calefactor) y `dTc = 80 K` de enfriamiento desde 85 °C con ambiente a 15 °C. Para el último caso indicó 737 s hasta 5 °C. El mecanismo de enfriamiento pasivo modelado solo intercambia calor con ese ambiente. La validación debe considerar tipos discretos, cotas de eficiencia y temperatura final alcanzable además de la positividad. [Validaciones y enfriamiento](evaluador.py#L579)

## 5. Alcance físico de las predicciones

### Flotabilidad y volumen de las celdas

La ley del gas ideal y la expresión `F = (rho_exterior - rho_interior)*g*V` son coherentes para aire interior uniforme. El evaluador aplica la densidad del núcleo caliente a todo el volumen exterior. En el CAD, las celdas ocupan espacio hacia dentro y el modelo térmico predice una caída de temperatura a través de ellas. Si su aire está más frío a presión comparable, será más denso y la sustentación disponible será menor. El histórico tiene cuatro capas superiores de 31.84 mm, un espesor acumulado de unos 127 mm. Un balance por regiones podría usar `g*(rho_exterior*V_desplazado - suma(rho_i*V_i))` para la sustentación neta asociada al gas y contabilizar las masas sólidas en el balance de peso. Se necesitan los volúmenes útiles y temperaturas de las cámaras para cuantificar la diferencia. [Gas y flotabilidad](evaluador.py#L427) · [Geometría interior](generar_cad_solidworks.py#L38)

### Inercia y duración de la maniobra

La base contiene 13.17 kg de aire caliente y reporta 4.24 kg en `mtot`, que suma la masa material y la carga. La diferencia de densidades ya contempla el peso del aire caliente en estática. Al acelerar importa también el gas que se mueve con el casco, además de la masa añadida del aire exterior, dependiente de la dirección. El evaluador usa `mtot` para la aceleración vertical y `fap*mtot` para la horizontal, con `fap = 1.15` en la base. Usa además las aceleraciones de una maniobra de 5 s al calcular una potencia que integra durante los 336 s de misión. Para estimar la batería se requieren dos comprobaciones distintas: potencia máxima durante la maniobra y energía integrada durante las fases reales de vuelo. [Fuerzas y energía](evaluador.py#L309) · [Estudio experimental de masa añadida en dirigibles](https://www.mdpi.com/2226-4310/11/11/872)

### Trabajo útil y potencia de hélice

En avance horizontal, el trabajo útil por unidad de tiempo depende de la componente horizontal de fuerza multiplicada por la velocidad. En general es el producto escalar fuerza por velocidad. Sustituir automáticamente `FX*v` por `Ttot*v` atribuiría trabajo de avance a la componente vertical. Sostener el peso también consume potencia inducida, y el modelo ya incluye un término dependiente del empuje total. La incertidumbre proviene de combinar ese término de régimen estático con una eficiencia empírica de avance para hélices inclinadas. Para evaluar un margen original de solo 2.7 W se necesitan curvas empuje–potencia del motor, hélice y alimentación utilizados, a densidad y condiciones de avance representativas. [Potencia implementada](evaluador.py#L317) · [NASA Glenn, teoría de empuje de hélices](https://www.grc.nasa.gov/WWW/K-12/BGP/propth.html)

### Arrastre y referencia de velocidad

La correlación de Hoerner usa la esbeltez y el área de referencia volumétrica `V^(2/3)`, adecuados para una estimación preliminar del casco limpio. El factor parásito `kp = 1.45` representa accesorios y depende de la góndola, brazos y elementos expuestos. Hay además dos distancias relevantes con viento. Para la base, `ED = FD*dm` usa el recorrido sobre el suelo y da 10.18 kJ. El trabajo asociado al recorrido respecto al aire, `FD*v*tm`, da 34.61 kJ. Se debe explicitar la referencia de `ED` si se interpreta como disipación aerodinámica. La energía eléctrica de misión se calcula por separado. [Arrastre](evaluador.py#L509) · [Energía ED](evaluador.py#L596) · [Hoerner, Fluid-Dynamic Drag, ecuación 36](https://home.hvl.no/ansatte/gste/ftp/MarinLab_files/Litteratur/Hoerner_1965_Fluid-dynamic_drag.pdf)

### Transferencia térmica y tiempo de enfriamiento

En las celdas superiores de la base, el Rayleigh calculado es 1507, inferior al umbral 1708. El valor `Nuc = 1` concuerda con la correlación de Hollands implementada. En el histórico se obtiene un Rayleigh de 15072 y `Nuc = 2.65`. La correlación original se estudió en capas de aire calentadas desde abajo y depende de la inclinación. Aplicarla de forma uniforme a toda una mitad curva introduce incertidumbre en `U` y en el combustible requerido. Una medición térmica por zonas ayudaría a cuantificarla. [Cálculo de convección en celdas](evaluador.py#L198) · [Hollands y colaboradores, 1976](https://doi.org/10.1115/1.3450517)

El tiempo `tc = m*cp*dTc/Qp` mantiene constante la pérdida inicial. La potencia perdida disminuye a medida que el gas se aproxima a la temperatura ambiente. Para validar una caída de 20 K conviene integrar el balance con pérdidas dependientes de la temperatura y contrastarlo con una curva de enfriamiento medida. Los 184.3 s de la base y 210.0 s del histórico corresponden a la aproximación original. [Tiempo de enfriamiento](evaluador.py#L586)

### Carga útil y autonomía

La capacidad útil se estima con `mcarga + Fexc/g` a partir del excedente de fuerza del punto actual. El histórico informa 2.409 kg. Si se aumenta la carga, cambian el empuje de maniobra, la potencia y posiblemente la batería requerida. Para demostrar esa capacidad habría que aumentar la carga, resolver de nuevo el circuito masa–potencia–batería y verificar todos los límites. La autonomía publicada de 660 m resulta del mínimo entre alcance eléctrico y térmico, calculados por proporción a partir de una misión de referencia. Su fiabilidad depende de los consumos y de la batería del diseño revisado. [Indicadores de capacidad y autonomía](diseno.py#L272)

## 6. Documentación y siguiente validación

El README describe 167 variables, 103 ecuaciones, mamparos internos y un simulador por fases llamado `simulacion.py`. En la copia auditada la API devuelve 163 variables y 101 ecuaciones, y ese módulo está ausente. La tabla del README atribuye a la base 270.7 W y ninguna alerta, con velocidad respecto al aire de 5.5 m/s y viento de 2.5 m/s. La base ejecutada usa 8.5 y 6 m/s respectivamente y devuelve 1104.6 W. Para comparar resultados de distintas versiones deben registrarse la revisión, las entradas de misión y los límites activos junto a la ficha. [Valores documentados](README.md#L53) · [Estado publicado por la API](app.py#L123)

1. **Corregir la superficie en ambas implementaciones.** Comprobar el límite hemisférico, contrastar el área con integración independiente y regenerar las estimaciones del histórico conservando sus entradas originales como referencia.
2. **Cerrar el inventario físico.** Identificar piel, láminas, tabiques, uniones y refuerzos. Medir la masa de envolvente y delimitar el volumen del núcleo caliente y de las celdas.
3. **Unificar la factibilidad.** Derivar límites del hardware configurado, contrastar combustible embarcado con requerido y conservar signos físicos en pantalla. Documentar las ramas posibles de los cálculos inversos.
4. **Medir y volver a optimizar.** Contrastar la pérdida térmica y la curva empuje–potencia con el equipo real, además de la masa de envolvente. Separar picos de maniobra de consumo de crucero y repetir la búsqueda para una misión fija. El resultado podrá compararse mediante márgenes en vatios, newtons, gramos y metros junto a la puntuación ponderada.

## 7. Reverificación de la copia local tras las correcciones

Esta sección corresponde a los cambios locales sobre `e1415db`. Las secciones 1 a 6 conservan los resultados anteriores. Se ejecutaron el modelo, el análisis de diseño de la API, la serialización del estado, el evaluador de las gráficas y la búsqueda por defecto. Las comprobaciones son computacionales, sin mediciones de un prototipo.

| Resultado recalculado | Base actual de 840 m | Histórico de 660 m | Nuevo candidato de 840 m |
|---|---:|---:|---:|
| Potencia motriz de maniobra (W) | 1403.76 | 1808.46 | 638.01 |
| Potencia motriz de crucero (W) | 1159.51 | 935.91 | 449.10 |
| Masa de batería (kg) | 1.0515 | 1.3431 | 0.6676 |
| Empuje de maniobra (N) | 23.47 | 31.31 | 12.79 |
| Cumple los límites evaluados por defecto | No | No | Sí, con 1 kg de carga |

El histórico conserva su entrada de maniobra de 5 s. La base actual usa 18 s. Los 734.9 W de la primera auditoría aislaban solo la corrección de superficie. Los 1808.46 W actuales incorporan, entre otros cambios, piel exterior, inercia del gas y un nuevo cálculo del volumen y la batería. El nuevo candidato deja 1.99 W respecto de 640 W y 2.86 g de combustible respecto del consumo estimado. Son márgenes del cálculo.

### Correcciones verificadas

- La integral de revolución coincide con las áreas actuales de 40.6477 m² en la base y 46.4293 m² en el histórico. La masa de película incluye la piel exterior y el balance de flotación distingue núcleo y cámaras.
- El balance eléctrico emplea potencias distintas en maniobra y crucero. El trabajo de arrastre usa velocidad respecto al aire. El enfriamiento tiene solución logarítmica bajo la hipótesis de transmitancia constante.
- El solucionador rechaza 3.5 motores, eficiencia del 150 % y caída de 80 K con solo 70 K de diferencia inicial. La API mantiene el signo de la fuerza (31.28 N en ambos campos), la falta de combustible invalida el candidato y el análisis directo rechaza 100 °C ante un límite activo de 95 °C.
- En 81 combinaciones, 41 dieron solución en el evaluador estricto y 40 se descartaron. Para las 41 soluciones el mayor residuo escalado de las 107 ecuaciones fue 4.64e-13. Tres inversiones recuperaron las entradas esperadas. Fijar U aún admite espesores de 14.082 y 16.000 mm, comportamiento que ahora documenta el README.
- La búsqueda dio 47.59 puntos y los mismos parámetros al invertir el orden de las ocho variables. Esta reproducibilidad no constituye una prueba de optimalidad global.

### Problemas reproducidos en la nueva versión

1. **Restricciones de hardware desactualizadas.** Tomar las entradas del nuevo candidato, cambiar `Pmax1` de 160 a 100 W y enviar las restricciones previamente generadas para cuatro motores de 160 W. Con los límites activos y sin búsqueda, la API devuelve simultáneamente `encontrado=True`, `valido_hardware=False`, 638.01 W demandados, 400 W disponibles y cero avisos de restricciones activas. Al omitir la lista y dejar que se regenere, rechaza el punto. La interfaz reenvía la lista y el umbral efectivo solo se reajusta en circunstancias concretas si varía el número de motores. [Umbral efectivo](diseno.py#L208) · [Petición del frontend](frontend/js/components/designStudio.js#L1212)
2. **Carga útil sobreestimada.** El nuevo candidato se evalúa con 1 kg y publica 2.4194 kg de capacidad. Al introducir esa carga en las mismas entradas y redimensionar la batería, exige 1836.47 W. Una bisección entre 1 y 1.1 kg sitúa el límite local en 1.0090 kg manteniendo los demás parámetros. El indicador usa solo el excedente de fuerza y también alimenta la puntuación. [Cálculo de capacidad](diseno.py#L349)
3. **Ángulo de crucero sin verificar.** A partir del nuevo candidato, fijar `mflot=4.171488179039247` kg, `mp=0.16` kg y `ta=30` s. El ángulo de maniobra es 74.605°, pero el crucero requiere `atan2(FD, mres*g) = 75.122°` con tope de 75°. Tanto el evaluador como el estudio con variables fijas aceptan el punto. [Criterio de ángulo](evaluador.py#L704)
4. **Casco sin celdas incoherente entre rutas.** Con `ncapS=ncapI=0`, los barridos devuelven el coeficiente sin aislante, U = 4.32577 W/(m²·K). El solucionador principal rechaza la misma configuración por la ecuación de caída térmica en una celda inexistente. La rama numérica asigna cero a esa caída y la ecuación simbólica sigue exigiendo una caída positiva. [Rama numérica](evaluador.py#L603) · [Ecuación simbólica](modelo.py#L554)
5. **Precalentamiento calculado con una sola temperatura.** El modelo sitúa el aire de las cámaras a la temperatura media entre interior y ambiente para obtener su masa, pero aplica a toda la masa la subida de temperatura completa del núcleo. Con la misma aproximación de calor sensible a masas finales, sumar por regiones da 926.69 kJ en la base frente a 960.82 kJ publicados, y 1079.87 kJ en el histórico frente a 1190.90 kJ. Esto afecta a la energía y al costo iniciales. [Masa y calor sensible](modelo.py#L468)
6. **Comparación con dron en G7.** La energía del dron se obtiene aplicando potencia de maniobra a toda la misión, y su aceleración horizontal reutiliza la masa aparente del dirigible, que ahora incluye el gas. El dirigible se evalúa por fases. La misma gráfica calcula la caída de flotabilidad a 10 K usando solo la densidad del núcleo, aunque ahora la flotabilidad total depende también de las cámaras. [Sensibilidad y comparación en G7](graficas.py#L836)
7. **Histórico y pruebas anteriores.** La ficha anterior sigue mostrando 637.3 W y hardware válido al leer el histórico local. Conviene mantener su procedencia y distinguirla claramente del resultado recalculado de 1808.46 W. El script de la primera auditoría comprueba bien la geometría pero se interrumpe al acceder al campo de avisos de un óptimo que ahora, correctamente, vale `None`. Las pruebas siguientes se ejecutaron por separado. [Lectura de históricos](diseno.py#L1112) · [Supuesto de la prueba anterior](auditar_modelo.py#L84)

Para construir a partir del nuevo candidato aún hace falta contrastar la curva de empuje y potencia a la densidad de operación, la masa real de la envolvente y las pérdidas térmicas. El modelo usa un factor de inercia común a ambos ejes, una temperatura media de cámaras y correlaciones térmicas aproximadas. La aceptación numérica de un candidato con apenas 1.99 W de margen depende de esos supuestos.
