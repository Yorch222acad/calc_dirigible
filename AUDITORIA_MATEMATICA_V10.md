# Auditoría matemática y funcional V10 del dirigible híbrido

Revisión del 27 de noviembre de 2026 sobre el modelo v2. Los dos hallazgos de V9 pasaron sus regresiones. La revisión adicional detectó dos problemas en el optimizador. El primero permite publicar como óptimo un número fraccionario de viajes. El segundo afecta al diagnóstico de misiones con velocidad de avance igual o inferior a 0,35 m/s.

## 1. El optimizador admite un número fraccionario de viajes

**Reproducción**

1. Obtener el candidato predeterminado con el límite de temperatura de 130 °C y usar sus entradas como base.
2. Fijar el valor inicial de `nv` en 1,5 y dejar únicamente `nv` libre. Asignar todo el peso al consumo energético.
3. Mantener las restricciones del equipo y añadir dos cotas de energía total, `Etot >= 903.78` kJ y `Etot <= 905.78` kJ.
4. Ejecutar la optimización y leer `encontrado` y `entradas_optimo.nv`.

**Resultado observado.** El optimizador devuelve `encontrado=True` y `nv=1.5`. La energía es de 904,78 kJ, dentro de la banda solicitada. El resultado incumple el requisito de viajes enteros declarado en el catálogo.

**Causa.** El muestreo redondea las variables declaradas enteras. El candidato inicial llega a la clasificación por otra ruta, que solo comprueba si el valor cae dentro del intervalo numérico. Así puede ganar la búsqueda un valor que el propio muestreo nunca generaría. [Definición de nv](diseno.py#L94) · [Admisión del candidato inicial](diseno.py#L951) · [Redondeo en el muestreo](diseno.py#L974)

**Corrección propuesta.** Comprobar el dominio de cada variable libre antes de admitir cualquier candidato, incluido el inicial. Conservar el valor inicial en la ficha de referencia. Si se ensaya un entero vecino, recalcular su energía, puntuación y restricciones con ese entero.

**Prueba de aceptación.** Repetir la reproducción y exigir que toda solución publicada tenga `nv` entero y cumpla ambas cotas de energía al reevaluarla. Si ningún entero cumple, el resultado debe indicar que la búsqueda quedó sin solución. Como control positivo, usar una base de dos viajes y una banda que incluya su energía; el candidato inicial entero debe poder participar.

## 2. El rechazo por velocidad mínima de búsqueda se atribuye a las restricciones activas

**Reproducción.** Tomar las entradas del candidato predeterminado y fijar `mcarga=1.5` kg, `nv=1`, `d1=0.5` m y `vv=0` m/s. Ejecutar primero un análisis directo y después una optimización con solo `dTc` libre. Repetir cambiando únicamente la velocidad del aire. Sin viento, esa velocidad coincide con la de avance `vg`.

| Velocidad | Análisis directo | Optimización con solo la caída de temperatura libre |
|---:|---|---|
| 0,350 m/s | Acepta la misión sin avisos | Cero candidatos válidos. El mensaje atribuye el rechazo a las restricciones activas. |
| 0,351 m/s | Acepta la misión sin avisos | Encuentra solución. |

**Causa.** El análisis directo exige avance positivo. Al liberar una variable, la búsqueda exige `vg > 0.35` m/s. Cambiar `dTc` no puede modificar `vg`, por lo que todos los candidatos del primer caso quedan descartados por el mismo motivo. El mensaje omite la condición que permitiría al usuario entender el rechazo. [Elección del umbral](diseno.py#L946) · [Comprobación en la búsqueda](diseno.py#L401) · [Comprobación en el refinamiento](diseno.py#L801)

**Corrección propuesta.** Definir si 0,35 m/s es un margen operativo deliberado o si basta una velocidad positiva. Si se conserva el margen para la optimización, mostrar la condición estricta `vg > 0.35` junto con la velocidad evaluada. Usar el mismo criterio en todas las etapas de búsqueda.

**Prueba de aceptación.** Con el margen vigente, el caso de 0,350 m/s debe identificar el umbral que impide optimizar y el de 0,351 m/s debe seguir encontrando solución. Si se adopta el dominio de avance positivo para ambos modos, los dos casos deben admitir el candidato de referencia. Mantener como control el rechazo de una misión con velocidad neta negativa.

## Regresiones confirmadas

- Con 1 kg de carga, el análisis nominal y el evaluador de batería instalada obtuvieron 13,90 N de excedente de sustentación. Ambos admitieron la carga con un tope de empuje de 13 N y la rechazaron con 12 N.
- Para 0,5 m sin viento, el cálculo dio 5 s a 0,1 m/s y 2,5 s a 0,2 m/s. Con velocidad del aire de 0,1 m/s y viento en contra de 0,12 m/s, la API respondió con estado 400.
- Pasaron la suite matemática hasta V9 y las cinco pruebas de Chromium. Los dos casos de aceptación de V10 quedan pendientes de incorporar a la suite.
