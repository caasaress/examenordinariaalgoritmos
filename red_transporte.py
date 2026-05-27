"""
Planificador de rutas en una red de transporte.
Estructuras de Datos y Algoritmos I - Examen final.
"""

from __future__ import annotations

import csv
import heapq
import json
from collections import deque
from pathlib import Path
from typing import Final

ARCHIVO_RED_DEFECTO: Final[str] = "red.txt"
ARCHIVO_INFORME_BONUS: Final[str] = "informe_red.json"


class RedTransporte:
    """Grafo no dirigido ponderado representado como lista de adyacencia."""

    def __init__(self) -> None:
        self._grafo: dict[str, list[tuple[str, float]]] = {}

    @property
    def grafo(self) -> dict[str, list[tuple[str, float]]]:
        """Acceso de solo lectura al grafo (copia superficial de claves)."""
        return self._grafo

    def _asegurar_estacion(self, nombre: str) -> None:
        nombre_limpio = nombre.strip()
        if not nombre_limpio:
            raise ValueError("El nombre de la estación no puede estar vacío.")
        if nombre_limpio not in self._grafo:
            self._grafo[nombre_limpio] = []

    def anadir_estacion(self, nombre: str) -> None:
        """Registra una estación sin conexiones."""
        try:
            self._asegurar_estacion(nombre)
        except ValueError as exc:
            raise ValueError(f"No se pudo añadir la estación: {exc}") from exc

    def _existe_arista(self, origen: str, destino: str) -> bool:
        return any(vecino == destino for vecino, _ in self._grafo.get(origen, []))

    def anadir_conexion(
        self, origen: str, destino: str, minutos: float, bidireccional: bool = True
    ) -> None:
        """Añade una arista ponderada; por defecto es no dirigida."""
        try:
            origen_l = origen.strip()
            destino_l = destino.strip()

            if origen_l == destino_l:
                raise ValueError("Origen y destino deben ser estaciones distintas.")

            if minutos <= 0:
                raise ValueError("El tiempo en minutos debe ser un número positivo.")

            if origen_l not in self._grafo or destino_l not in self._grafo:
                raise ValueError(
                    "Ambas estaciones deben existir antes de conectarlas. "
                    "Use la opción de añadir estación."
                )

            if self._existe_arista(origen_l, destino_l):
                raise ValueError(
                    f"Ya existe una conexión entre '{origen_l}' y '{destino_l}'."
                )

            self._grafo[origen_l].append((destino_l, float(minutos)))
            if bidireccional:
                if self._existe_arista(destino_l, origen_l):
                    raise ValueError("Conexión duplicada detectada en sentido inverso.")
                self._grafo[destino_l].append((origen_l, float(minutos)))

        except (TypeError, ValueError) as exc:
            raise ValueError(f"No se pudo añadir la conexión: {exc}") from exc

    def listar_estaciones(self) -> list[str]:
        return sorted(self._grafo.keys())

    def listar_conexiones(self) -> list[tuple[str, str, float]]:
        """Devuelve aristas únicas (origen <= destino lexicográficamente)."""
        vistas: set[tuple[str, str]] = set()
        resultado: list[tuple[str, str, float]] = []

        for origen, adyacentes in self._grafo.items():
            for destino, peso in adyacentes:
                par = (origen, destino) if origen <= destino else (destino, origen)
                if par in vistas:
                    continue
                vistas.add(par)
                resultado.append((par[0], par[1], peso))

        resultado.sort(key=lambda t: (t[0], t[1]))
        return resultado

    def cargar_desde_archivo(self, ruta: str | Path) -> int:
        """
        Lee líneas con formato: origen, destino, minutos
        Soporta .txt y .csv.
        """
        path = Path(ruta)
        if not path.is_file():
            raise FileNotFoundError(f"No se encontró el archivo: {path}")

        self._grafo.clear()
        lineas_leidas = 0

        try:
            with path.open(encoding="utf-8", newline="") as archivo:
                if path.suffix.lower() == ".csv":
                    lector = csv.reader(archivo)
                    filas = lector
                else:
                    filas = (linea.split(",") for linea in archivo if linea.strip())

                for numero, partes in enumerate(filas, start=1):
                    try:
                        if not partes or all(not p.strip() for p in partes):
                            continue
                        if len(partes) < 3:
                            raise ValueError("Se requieren tres campos: origen, destino, minutos")

                        origen = partes[0].strip()
                        destino = partes[1].strip()
                        minutos = float(partes[2].strip())

                        self._asegurar_estacion(origen)
                        self._asegurar_estacion(destino)

                        if not self._existe_arista(origen, destino):
                            self.anadir_conexion(origen, destino, minutos)
                        lineas_leidas += 1

                    except (ValueError, TypeError) as exc:
                        raise ValueError(
                            f"Error en línea {numero} de '{path.name}': {exc}"
                        ) from exc

        except OSError as exc:
            raise OSError(f"No se pudo leer el archivo: {exc}") from exc

        return lineas_leidas

    def guardar_en_archivo(self, ruta: str | Path) -> int:
        """Escribe conexiones únicas en formato origen, destino, minutos."""
        path = Path(ruta)
        conexiones = self.listar_conexiones()

        try:
            with path.open("w", encoding="utf-8", newline="") as archivo:
                if path.suffix.lower() == ".csv":
                    escritor = csv.writer(archivo)
                    for origen, destino, minutos in conexiones:
                        escritor.writerow([origen, destino, minutos])
                else:
                    for origen, destino, minutos in conexiones:
                        archivo.write(f"{origen}, {destino}, {minutos}\n")
        except OSError as exc:
            raise OSError(f"No se pudo escribir el archivo: {exc}") from exc

        return len(conexiones)

    def ruta_mas_rapida(
        self, origen: str, destino: str
    ) -> tuple[float, list[str]] | None:
        """
        Dijkstra con heapq (min-heap).
        Retorna (tiempo_total, lista_de_estaciones) o None si no hay camino.
        """
        origen_l = origen.strip()
        destino_l = destino.strip()

        if origen_l not in self._grafo or destino_l not in self._grafo:
            raise ValueError("Ambas estaciones deben existir en la red.")

        if origen_l == destino_l:
            return 0.0, [origen_l]

        distancias: dict[str, float] = {nodo: float("inf") for nodo in self._grafo}
        distancias[origen_l] = 0.0
        predecesores: dict[str, str | None] = {nodo: None for nodo in self._grafo}
        procesados: set[str] = set()

        heap: list[tuple[float, str]] = [(0.0, origen_l)]

        while heap:
            dist_actual, nodo_actual = heapq.heappop(heap)

            if nodo_actual in procesados:
                continue

            procesados.add(nodo_actual)

            if nodo_actual == destino_l:
                break

            if dist_actual > distancias[nodo_actual]:
                continue

            for vecino, peso in self._grafo[nodo_actual]:
                if vecino in procesados:
                    continue

                nueva_dist = dist_actual + peso
                if nueva_dist < distancias[vecino]:
                    distancias[vecino] = nueva_dist
                    predecesores[vecino] = nodo_actual
                    heapq.heappush(heap, (nueva_dist, vecino))

        if distancias[destino_l] == float("inf"):
            return None

        camino: list[str] = []
        actual: str | None = destino_l
        while actual is not None:
            camino.append(actual)
            actual = predecesores[actual]
        camino.reverse()

        return distancias[destino_l], camino

    def estan_conectadas(self, origen: str, destino: str) -> bool:
        """BFS para comprobar conectividad en grafo no dirigido."""
        origen_l = origen.strip()
        destino_l = destino.strip()

        if origen_l not in self._grafo or destino_l not in self._grafo:
            raise ValueError("Ambas estaciones deben existir en la red.")

        if origen_l == destino_l:
            return True

        visitados: set[str] = set()
        cola: deque[str] = deque([origen_l])
        visitados.add(origen_l)

        while cola:
            actual = cola.popleft()
            if actual == destino_l:
                return True

            for vecino, _ in self._grafo[actual]:
                if vecino not in visitados:
                    visitados.add(vecino)
                    cola.append(vecino)

        return False

    def grado_estacion(self, estacion: str) -> int:
        """Número de conexiones incidentes (grado en grafo no dirigido)."""
        estacion_l = estacion.strip()
        if estacion_l not in self._grafo:
            raise ValueError(f"La estación '{estacion_l}' no existe.")
        return len(self._grafo[estacion_l])

    def detectar_hub(self) -> tuple[str, int]:
        """Estación con mayor grado; en empate, la primera alfabéticamente."""
        if not self._grafo:
            raise ValueError("La red no tiene estaciones.")

        mejor_estacion = ""
        mejor_grado = -1

        for estacion in self.listar_estaciones():
            grado = self.grado_estacion(estacion)
            if grado > mejor_grado:
                mejor_grado = grado
                mejor_estacion = estacion

        return mejor_estacion, mejor_grado

    def exportar_informe_json(self, ruta: str | Path = ARCHIVO_INFORME_BONUS) -> Path:
        """Bonus: informe JSON con estadísticas y estación hub."""
        path = Path(ruta)
        estaciones = self.listar_estaciones()
        conexiones = self.listar_conexiones()
        hub, grado_hub = self.detectar_hub()

        conexiones_hub = [
            {"destino": dest, "minutos": peso}
            for orig, dest, peso in conexiones
            if orig == hub or dest == hub
        ]

        informe: dict[str, object] = {
            "numero_total_estaciones": len(estaciones),
            "numero_total_conexiones": len(conexiones),
            "estacion_hub": {
                "nombre": hub,
                "grado": grado_hub,
                "conexiones": conexiones_hub,
            },
            "estaciones": estaciones,
        }

        try:
            with path.open("w", encoding="utf-8") as archivo:
                json.dump(informe, archivo, ensure_ascii=False, indent=2)
        except OSError as exc:
            raise OSError(f"No se pudo exportar el informe JSON: {exc}") from exc

        return path


def _leer_linea(mensaje: str) -> str:
    return input(mensaje).strip()


def _leer_float_positivo(mensaje: str) -> float:
    texto = _leer_linea(mensaje)
    try:
        valor = float(texto)
        if valor <= 0:
            raise ValueError
        return valor
    except ValueError as exc:
        raise ValueError("Debe ingresar un número positivo válido.") from exc


def _mostrar_red(red: RedTransporte) -> None:
    estaciones = red.listar_estaciones()
    if not estaciones:
        print("\nLa red no tiene estaciones registradas.\n")
        return

    print("\n--- Estaciones ---")
    for estacion in estaciones:
        print(f"  • {estacion} (grado: {red.grado_estacion(estacion)})")

    print("\n--- Conexiones ---")
    conexiones = red.listar_conexiones()
    if not conexiones:
        print("  (sin conexiones)")
    else:
        for origen, destino, minutos in conexiones:
            print(f"  {origen} <-> {destino} : {minutos} min")

    try:
        hub, grado = red.detectar_hub()
        print(f"\nEstación hub: {hub} (grado {grado})")
    except ValueError:
        pass
    print()


def main() -> None:
    red = RedTransporte()
    archivo_actual = ARCHIVO_RED_DEFECTO

    while True:
        print("\n=== Planificador de rutas en red de transporte ===")
        print("1. Cargar red desde archivo")
        print("2. Anadir estacion")
        print("3. Anadir conexion")
        print("4. Ver estaciones y conexiones")
        print("5. Ruta mas rapida entre dos estaciones")
        print("6. Estan conectadas dos estaciones?")
        print("7. Guardar y salir")

        opcion = _leer_linea("\nSeleccione una opción (1-7): ")

        try:
            if opcion == "1":
                ruta = _leer_linea(
                    f"Ruta del archivo [{archivo_actual}] (Enter para defecto): "
                )
                if not ruta:
                    ruta = archivo_actual
                n = red.cargar_desde_archivo(ruta)
                archivo_actual = ruta
                print(f"\nRed cargada: {n} conexión(es) desde '{ruta}'.")
                informe = red.exportar_informe_json()
                print(f"Informe bonus exportado a '{informe}'.")

            elif opcion == "2":
                nombre = _leer_linea("Nombre de la estación: ")
                red.anadir_estacion(nombre)
                print(f"\nEstación '{nombre.strip()}' añadida correctamente.")

            elif opcion == "3":
                origen = _leer_linea("Estación origen: ")
                destino = _leer_linea("Estación destino: ")
                minutos = _leer_float_positivo("Tiempo en minutos: ")
                red.anadir_conexion(origen, destino, minutos)
                print(
                    f"\nConexión {origen.strip()} <-> {destino.strip()} "
                    f"({minutos} min) registrada."
                )

            elif opcion == "4":
                _mostrar_red(red)

            elif opcion == "5":
                origen = _leer_linea("Estación origen: ")
                destino = _leer_linea("Estación destino: ")
                resultado = red.ruta_mas_rapida(origen, destino)
                if resultado is None:
                    print(
                        f"\nNo existe ruta entre '{origen.strip()}' y '{destino.strip()}'."
                    )
                else:
                    tiempo, camino = resultado
                    print(f"\nTiempo mínimo: {tiempo} minutos")
                    print("Ruta: " + " -> ".join(camino))

            elif opcion == "6":
                origen = _leer_linea("Estación origen: ")
                destino = _leer_linea("Estación destino: ")
                conectadas = red.estan_conectadas(origen, destino)
                if conectadas:
                    print(
                        f"\nSí, '{origen.strip()}' y '{destino.strip()}' "
                        "están conectadas."
                    )
                else:
                    print(
                        f"\nNo, '{origen.strip()}' y '{destino.strip()}' "
                        "no están conectadas."
                    )

            elif opcion == "7":
                if red.listar_estaciones():
                    ruta = _leer_linea(
                        f"Archivo de salida [{archivo_actual}] (Enter para defecto): "
                    )
                    if ruta:
                        archivo_actual = ruta
                    n = red.guardar_en_archivo(archivo_actual)
                    informe = red.exportar_informe_json()
                    print(
                        f"\nRed guardada ({n} conexión(es)) en '{archivo_actual}'."
                    )
                    print(f"Informe bonus guardado en '{informe}'.")
                print("\n¡Hasta luego!")
                break

            else:
                print("\nOpción no válida. Elija un número del 1 al 7.")

        except (ValueError, FileNotFoundError, OSError) as exc:
            print(f"\nError: {exc}")


if __name__ == "__main__":
    main()
