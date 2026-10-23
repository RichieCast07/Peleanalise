# Modelo de clasificación PeleAnálise

- Versión: `ham10000-mobilenetv2-v1`  ·  Arquitectura: MobileNetV2 (transfer learning, ImageNet)
- Datos: HAM10000 (13354 imágenes, 7470 lesiones). Partición por **lesión** 70/15/15.
- Entrada: RGB 224x224 en [0,1]  ·  Salida: probabilidades [Benigno, Sospechoso, Maligno] (temperature scaling T=1.00)

## Agrupación de diagnósticos (decisión clínica, requiere validación médica)
- Benigno: nevus melanocítico, queratosis benigna, dermatofibroma, lesión vascular
- Sospechoso: queratosis actínica (lesión precancerosa)
- Maligno: melanoma, carcinoma basocelular

## Resultados en el conjunto de prueba (1908 imágenes de 1067 lesiones no vistas)
- Accuracy: 0.838  ·  Accuracy balanceada: 0.686 (IC95% 0.627–0.746)
- Sensibilidad para Maligno: 0.608 (IC95% 0.525–0.692)
- Sensibilidad Maligno detectado como Sospechoso o Maligno: 0.656
- Especificidad para Benigno: 0.896
- AUC (uno contra resto, promedio): 0.914

Matriz de confusión (filas = real, columnas = predicho):

| | Benigno | Sospechoso | Maligno |
|---|---|---|---|
| Benigno | 1374 | 13 | 147 |
| Sospechoso | 10 | 35 | 18 |
| Maligno | 107 | 15 | 189 |

## Regla de decisión orientada a cribado (la que usa la aplicación)
Con "gana la clase más probable" se omiten malignos. La aplicación usa umbrales ajustados en validación (objetivo: que como máximo 10 % de los malignos se marquen Benigno):
- Maligno si P(Maligno) ≥ 0.23  ·  Sospechoso si P(Sospechoso)+P(Maligno) ≥ 0.59  ·  si no, Benigno.
- Sensibilidad (maligno marcado Sospechoso o Maligno): **0.900**
- Sensibilidad para Maligno exacto: 0.871  ·  Especificidad Benigno: **0.742**  ·  Accuracy balanceada: 0.638
- Costo: más benignos marcados como alerta (falsas alarmas). Es el compromiso habitual al cribar.

Matriz de confusión con esta regla (filas = real, columnas = predicho):

| | Benigno | Sospechoso | Maligno |
|---|---|---|---|
| Benigno | 1138 | 7 | 389 |
| Sospechoso | 3 | 19 | 41 |
| Maligno | 31 | 9 | 271 |

## Limitaciones (leer antes de usar)
- **No existe un modelo sin error.** Los falsos negativos (lesiones malignas clasificadas como benignas) son posibles; ver la matriz.
- HAM10000 es dermatoscopia de población mayormente de piel clara (Austria y Australia). El rendimiento en otros tonos de piel, fotos con celular o equipos distintos puede ser **peor** y no está medido.
- Es una herramienta de apoyo. No sustituye el diagnóstico del dermatólogo ni la biopsia.
- Las clases están muy desbalanceadas (≈67 % nevus), por eso se reportan sensibilidad por clase y no solo accuracy.
