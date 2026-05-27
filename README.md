# Planificador de rutas en una red de transporte

**Asignatura:** Estructuras de Datos y Algoritmos I  
**Entregable:** Implementación en Python puro + análisis teórico obligatorio

---

## Descripción del proyecto

Sistema de consola que modela una red de transporte como un **grafo no dirigido ponderado**. Permite cargar y guardar la red desde archivo, administrar estaciones y conexiones, calcular la **ruta más rápida** (Dijkstra), comprobar **conectividad** (BFS) y generar un **informe JSON** con la estación *hub* (bonus).

### Ejecución

```bash
python red_transporte.py
```

Archivo de ejemplo incluido: `red.txt` (formato `origen, destino, minutos`).

---

## Estructura del código

| Componente | Archivo | Rol |
|------------|---------|-----|
| Clase `RedTransporte` | `red_transporte.py` | Grafo, algoritmos y persistencia |
| Menú CLI | `main()` en el mismo archivo | Interfaz interactiva |
| Datos de prueba | `red.txt` | Red de ejemplo |
| Informe bonus | `informe_red.json` | Generado al cargar o al salir |

---

## 1. Estructuras de datos elegidas y justificación

### Diccionario (`dict`) como lista de adyacencia

```python
self._grafo: dict[str, list[tuple[str, float]]]
```

- **Clave:** nombre de la estación (vértice).
- **Valor:** lista de tuplas `(estación_destino, minutos)`.

**Justificación:** Inserción y consulta de adyacentes en tiempo amortizado $O(1)$ para acceder a un vértice conocido. El grafo es **disperso** (pocas conexiones por estación frente a $|V|^2$), por lo que la matriz de adyacencia desperdiciaría memoria. El diccionario permite nombres legibles (`"Centro"`, `"Norte"`) sin mapear a índices numéricos.

### `set` para nodos visitados / procesados

- En **Dijkstra:** `procesados` evita relajar aristas desde un nodo ya extraído con distancia mínima definitiva.
- En **BFS:** `visitados` evita encolar el mismo nodo dos veces.

**Justificación:** Pertencia y alta en $O(1)$ promedio frente a $O(n)$ en una lista.

### `heapq` (cola de prioridad / min-heap)

- Almacena tuplas `(distancia_acumulada, estacion)`.
- `heappop` devuelve siempre el nodo con **menor tiempo acumulado** pendiente.

**Justificación:** Dijkstra requiere repetidamente el vértice no procesado con menor distancia provisional. Un heap reduce el coste de esa operación frente a buscar el mínimo en una lista ($O(V)$ por extracción).

### `collections.deque` en BFS

- Cola FIFO para el recorrido en anchura.

**Justificación:** `popleft()` en $O(1)$; con una lista, `pop(0)` sería $O(V)$.

### Persistencia en texto plano

- Formato: `origen, destino, minutos` (`.txt` o `.csv`).
- Sin dependencias externas (no NetworkX ni similares).

---

## 2. Complejidad temporal

Notación: $V = |V|$ estaciones, $E = |E|$ conexiones (aristas en lista de adyacencia; en grafo no dirigido cada arista física aparece dos veces, pero $E = \Theta(\text{aristas únicas})$ para el análisis asintótico estándar).

### Añadir estación

- Crear clave en el diccionario: **$O(1)$** amortizado.

### Añadir conexión

- Comprobar existencia de estaciones: **$O(1)$** (búsqueda en `dict`).
- Detectar arista duplicada: recorrer adyacentes de un extremo → **$O(\deg(u))$**; en el peor caso acotado por **$O(V)$** si el grado es alto.
- Inserción en lista de adyacencia: **$O(1)$** amortizado.

**Conclusión:** $O(1)$ en validaciones simples; **$O(V)$** en el peor caso por la comprobación anti-duplicados.

### Algoritmo de Dijkstra — $O((V + E) \log V)$

Implementación con **min-heap** y conjunto de procesados.

| Paso | Operación | Coste |
|------|-----------|-------|
| 1 | Inicializar distancias y heap con origen | $O(V)$ para el dict de distancias + $O(\log V)$ push |
| 2 | Cada iteración: `heappop` | $O(\log V)$ |
| 3 | Por cada arista $(u,v)$ saliente de $u$ relajada | Una operación de relajación |
| 4 | Si mejora distancia: `heappush` | $O(\log V)$ |

- Cada vértice se marca **procesado** una vez → a lo sumo $V$ extracciones efectivas del heap.
- Cada arista se examina cuando se procesa su extremo origen → **$O(E)$** relajaciones.
- En el peor caso puede haber **múltiples inserciones** del mismo vértice en el heap (lazy decrease-key), acotadas por $O(E)$ pushes totales.

Total heap: $O((V + E) \log V)$.

> Con **Fibonacci heap** teórico sería $O(E + V \log V)$; con `heapq` de la biblioteca estándar, $O((V + E) \log V)$ es la cota habitual y correcta para esta implementación.

### Comprobación de conectividad (BFS) — $O(V + E)$

- Cada estación entra en `visitados` como máximo una vez → **$O(V)$**.
- Cada lista de adyacencia se recorre cuando se visita su vértice → suma de grados **$O(E)$** en grafo no dirigido representado con listas.

**Total BFS:** $O(V + E)$.

### Detectar hub (bonus)

- Recorrer todos los vértices y sumar grados: **$O(V + E)$** (equivalente a contar aristas incidentes).

### Cargar / guardar archivo

- Proporcional al número de líneas (conexiones): **$O(E)$** por lectura/escritura, más validaciones por arista.

---

## 3. Complejidad espacial

| Estructura | Espacio |
|------------|---------|
| Lista de adyacencia | $O(V + E)$ — cada arista no dirigida almacenada dos veces en listas |
| Dijkstra: `distancias`, `predecesores`, `procesados`, heap | $O(V)$ + heap $O(V)$ en el peor caso → **$O(V)$** auxiliar |
| BFS: `visitados`, `deque` | **$O(V)$** |
| Informe JSON | $O(V + E)$ para serializar la red |

**Espacio total dominante:** $O(V + E)$ para el grafo más estructuras auxiliares lineales en $V$ durante las consultas.

---

## 4. Mejoras futuras

1. **Índice de aristas:** `set` o `dict` de pares `(u, v)` para comprobar duplicados en $O(1)$ en lugar de $O(\deg(u))$.
2. **Decrease-key explícito:** estructura con posición en heap o cola de prioridad indexada para reducir inserciones redundantes en Dijkstra.
3. **Versionado del grafo:** invalidar cachés de rutas si la red cambia entre consultas frecuentes.
4. **A* o contracción de jerarquías:** si se dispone de coordenadas geográficas o metadatos heurísticos.
5. **Componentes conexas precalculadas (Union-Find):** responder conectividad en casi $O(1)$ amortizado tras preproceso, útil si hay muchas consultas y pocas modificaciones.
6. **API REST o interfaz gráfica:** separar lógica (`RedTransporte`) de la capa de presentación (ya modularizada en clase + `main`).
7. **Tests unitarios automatizados** con `pytest` para regresiones en validaciones y casos borde (aristas negativas, estaciones inexistentes, grafos desconectados).

---

## Menú interactivo (especificación del examen)

```
1. Cargar red desde archivo
2. Anadir estacion
3. Anadir conexion
4. Ver estaciones y conexiones
5. Ruta mas rapida entre dos estaciones
6. Estan conectadas dos estaciones?
7. Guardar y salir
```

---

## Bonus: estación hub e informe JSON

La función `detectar_hub()` selecciona la estación con **mayor grado** (número de conexiones incidentes). `exportar_informe_json()` genera `informe_red.json` con:

- `numero_total_estaciones`
- `numero_total_conexiones`
- `estacion_hub` (nombre, grado, listado de conexiones)
- listado de todas las estaciones

Se exporta automáticamente al **cargar** la red y al **guardar y salir**.

---
## Bonus: estación hub e informe JSON

La función `detectar_hub()` selecciona la estación con **mayor grado** (número de conexiones incidentes). `exportar_informe_json()` genera `informe_red.json` con:

- `numero_total_estaciones`
- `numero_total_conexiones`
- `estacion_hub` (nombre, grado, listado de conexiones)
- listado de todas las estaciones

Se exporta automáticamente al **cargar** la red y al **guardar y salir**.

**Justificación técnica de la mejora:**
Se ha optado por implementar la detección del *hub* porque permite aplicar el concepto teórico de **centralidad de grado** en grafos. Desde el punto de vista algorítmico, esta operación es altamente eficiente, ya que se resuelve en tiempo lineal $O(V + E)$ iterando sobre las listas de adyacencia, sin penalizar el rendimiento global del sistema. Además, la exportación automática estructurada mediante la librería nativa `json` mejora la interoperabilidad y persistencia de los datos, demostrando un uso avanzado de archivos más allá del simple texto plano.

## Validaciones implementadas

- Tiempo en minutos **estrictamente positivo**.
- Estaciones deben **existir** antes de crear una conexión.
- **No se permiten aristas duplicadas** entre el mismo par.
- Origen y destino **distintos** en una conexión.
- Manejo de errores de archivo y líneas mal formadas con `try/except` y mensajes claros al usuario.

---

## Autoría

Proyecto académico — Estructuras de Datos y Algoritmos I. Implementación con biblioteca estándar de Python 3.10+ (`heapq`, `collections`, `json`, `csv`, `pathlib`).
