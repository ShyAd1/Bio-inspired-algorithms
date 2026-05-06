import random
import numpy as np
from time import sleep

# import matplotlib.pyplot as plt

"""Variables globales"""
rho = 0.2  # Tasa de evaporación
Q = 1  # Cantidad de feromona depositada por cada hormiga
alpha = 1.5  # Importancia de la feromona
beta = 2.0  # Importancia de la heurística
num_iteraciones = 50  # Número de iteraciones del algoritmo

# Matriz de distancias entre las ciudades
distancias = np.array(
    [  # 1  2   3   4   5   6
        [0, 6, 9, 17, 13, 21],  # 1
        [6, 0, 19, 21, 12, 18],  # 2
        [9, 19, 0, 20, 23, 11],  # 3
        [17, 21, 20, 0, 15, 10],  # 4
        [13, 12, 23, 15, 0, 21],  # 5
        [21, 18, 11, 10, 21, 0],  # 6
    ]
)

# Número de ciudades
num_ciudades = distancias.shape[0]

# Numero de hormigas (Una por ciudad)
num_hormigas = num_ciudades

# Inicializar la matriz de feromonas con un valor pequeño
feromonas = np.ones((num_ciudades, num_ciudades)) * 0.1

"""Funciones del algoritmo de hormigas"""


# Funcion para calcular las probabilidades
def calcular_probabilidades(probabilidades, ciudades_no_visitadas, ciudad_actual):
    for ciudad in ciudades_no_visitadas:
        tau = feromonas[ciudad_actual][ciudad] ** alpha
        eta = (1 / distancias[ciudad_actual][ciudad]) ** beta
        probabilidades.append(tau * eta)

    probabilidades = np.array(probabilidades)
    probabilidades /= probabilidades.sum()  # Normalizar
    return probabilidades


# Funcion para mostrar tabla de probabilidades, probabilidades acumuladas, ciudades no visitadas, ciudad actual
def mostrar_tabla_probabilidades(
    probabilidades, acumulado_probabilidades, ciudades_no_visitadas, ciudad_actual
):
    print(f"Ciudad actual: {ciudad_actual + 1}")
    print("Ciudades no visitadas y sus probabilidades:")
    for i, ciudad in enumerate(ciudades_no_visitadas):
        print(
            f"Ciudad {ciudad + 1}: Probabilidad = {probabilidades[i]:.4f}, Acumulada = {acumulado_probabilidades[i]:.4f}"
        )
    print("\n")


# Funcion para escoger la siguiente ciudad usando ruleta
def escoger_siguiente_ciudad(acumulado_probabilidades, ciudades_no_visitadas):
    variable_aleatoria = random.uniform(0, 1)
    print(f"Variable aleatoria para selección: {variable_aleatoria:.4f}")
    siguiente_ciudad = ciudades_no_visitadas[
        np.argmax(acumulado_probabilidades >= variable_aleatoria)
    ]
    return siguiente_ciudad


# Funcion para mostrar las feromonas en cada iteracion sin repeticion
# de ciudades y sin mostrar la diagonal principal junto al costo de
# las conexiones entre ciudades
def mostrar_feromonas(iteracion):
    print(f"Feromonas después de la iteración {iteracion + 1}:")
    for i in range(num_ciudades):
        for j in range(i + 1, num_ciudades):
            print(
                f"Conexión Ciudad {i + 1} - Ciudad {j + 1}: Feromona = {feromonas[i][j]:.4f}, Distancia = {distancias[i][j]}"
            )
    print("\n")


"""Funcion main"""
if __name__ == "__main__":
    mejor_ruta = None
    mejor_distancia = float("inf")

    for iteracion in range(num_iteraciones):
        rutas = []
        distancias_rutas = []

        for hormiga in range(num_hormigas):
            ruta = [hormiga]  # Comenzar en una ciudad diferente para cada hormiga
            while len(ruta) < num_ciudades:
                ciudad_actual = ruta[-1]
                ciudades_no_visitadas = [
                    i for i in range(num_ciudades) if i not in ruta
                ]
                print(f"Hormiga {hormiga + 1}, Ciudad actual: {ciudad_actual + 1}")
                print(
                    f"Ciudades no visitadas: {[c + 1 for c in ciudades_no_visitadas]}"
                )

                # Calcular la probabilidad de elegir cada ciudad no visitada
                probabilidades = []
                probabilidades = calcular_probabilidades(
                    probabilidades, ciudades_no_visitadas, ciudad_actual
                )

                acumulado_probabilidades = np.cumsum(probabilidades)

                mostrar_tabla_probabilidades(
                    probabilidades,
                    acumulado_probabilidades,
                    ciudades_no_visitadas,
                    ciudad_actual,
                )

                # Escoger la siguiente ciudad usando ruleta
                siguiente_ciudad = escoger_siguiente_ciudad(
                    acumulado_probabilidades, ciudades_no_visitadas
                )
                ruta.append(siguiente_ciudad)

                print(
                    f"Hormiga {hormiga + 1} eligió la ciudad {siguiente_ciudad + 1}\n"
                )

            # Ruta de la forma [0, 2, 4, 1, 3, 5, 0] (índices de las ciudades)
            ruta.append(ruta[0])  # Volver al punto de inicio para completar el ciclo

            # Calcular la distancia total de la ruta
            distancia_total = sum(
                distancias[ruta[i]][ruta[i + 1]] for i in range(len(ruta) - 1)
            )

            print(
                f"Hormiga {hormiga + 1} completó la ruta: {[c + 1 for c in ruta]} con distancia total: {distancia_total}\n"
            )

            # Guardar la ruta construida para poder actualizar feromonas después
            rutas.append(ruta)

            distancias_rutas.append(distancia_total)

            # Actualizar la mejor ruta encontrada
            if distancia_total < mejor_distancia:
                mejor_distancia = distancia_total
                mejor_ruta = ruta

        print(
            f"Iteración {iteracion + 1} - Mejor ruta: {[c + 1 for c in mejor_ruta]} con distancia: {mejor_distancia}\n"
        )

        # Evaporar feromonas
        feromonas *= 1 - rho

        # Depositar nuevas feromonas basadas en las rutas encontradas
        for i in range(num_hormigas):
            for j in range(len(rutas[i]) - 1):
                ciudad_a = rutas[i][j]
                ciudad_b = rutas[i][j + 1]
                feromonas[ciudad_a][ciudad_b] += Q / distancias_rutas[i]
                feromonas[ciudad_b][ciudad_a] += Q / distancias_rutas[i]

        # Mostrar feromonas después de la iteración
        mostrar_feromonas(iteracion)

        print(f"{'-'*40}\n")
        sleep(5)  # Pausa para facilitar la lectura de la salida

    print(
        f"Mejor ruta encontrada: {[c + 1 for c in mejor_ruta]} con distancia total: {mejor_distancia}"
    )
