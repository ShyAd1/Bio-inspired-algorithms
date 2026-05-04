# Importar librerias necesarias
import random
import matplotlib.pyplot as plt
import numpy as np

# Variables globales
NUM_PARTICULAS = 20
MAX_ITERACIONES = 50
A = 0.4  # Inercia
B_1 = 0.7  # Aprendizaje local
B_2 = 1.2  # Aprendizaje global
RANGO_POSICION = (-5, 5)  # Rango de posiciones para las partículas en X e Y
TIPO_VELOCIDAD = "Aleatoria"  # "Aleatoria" o "Cero"
PAUSA_VISUALIZACION = 1  # Segundos entre actualizaciones de la gráfica


# Funciones necesarias para el algoritmo PSO
def funcion_objetivo(x, y):
    return x**2 + y**2 + 25 * (np.sin(x) + np.sin(y))


def actualizacion_velocidad_global(
    velocidad, posicion, mejor_posicion_particula, mejor_posicion_global
):
    nueva_velocidad = []
    r1 = random.uniform(0, 1)
    r2 = random.uniform(0, 1)
    for i in range(len(velocidad)):
        v_i = (
            A * velocidad[i]
            + B_1 * r1 * (mejor_posicion_particula[i] - posicion[i])
            + B_2 * r2 * (mejor_posicion_global[i] - posicion[i])
        )
        nueva_velocidad.append(v_i)
    return nueva_velocidad


def actualizacion_posicion(posicion, velocidad):
    # La posición es un vector [x, y], así que actualizamos ambos componentes.
    nueva_posicion = [posicion[i] + velocidad[i] for i in range(len(posicion))]

    # Mantener cada coordenada dentro del rango permitido.
    for i in range(len(nueva_posicion)):
        if nueva_posicion[i] < RANGO_POSICION[0]:
            nueva_posicion[i] = RANGO_POSICION[0]
        elif nueva_posicion[i] > RANGO_POSICION[1]:
            nueva_posicion[i] = RANGO_POSICION[1]

    return nueva_posicion


def calcular_mejor_posicion_global(particulas):
    mejor_posicion_global = None
    mejor_valor_global = float("inf")

    for particula in particulas:
        valor_actual = funcion_objetivo(*particula["Posicion"])
        if valor_actual < mejor_valor_global:
            mejor_valor_global = valor_actual
            mejor_posicion_global = particula["Posicion"]
    print(
        f"\nMejor posición global: {mejor_posicion_global}, Valor: {mejor_valor_global}"
    )
    return mejor_posicion_global, mejor_valor_global


def generar_primeras_particulas(num_particulas, tipo_velocidad):
    particulas = []
    for i in range(num_particulas):
        posicion = [
            random.uniform(RANGO_POSICION[0], RANGO_POSICION[1]),
            random.uniform(RANGO_POSICION[0], RANGO_POSICION[1]),
        ]
        if tipo_velocidad == "Aleatoria":
            velocidad = [
                random.uniform(-1, 1),
                random.uniform(-1, 1),
            ]
        elif tipo_velocidad == "Cero":
            velocidad = [0, 0]
        valor_inicial = funcion_objetivo(*posicion)
        particulas.append(
            {
                "Particula": i,
                "Posicion": posicion,
                "Velocidad": velocidad,
                "pBest_posicion": posicion.copy(),
                "pBest_valor": valor_inicial,
            }
        )
    print("Partículas iniciales:")
    for particula in particulas:
        print(
            f"Particula {particula['Particula']}, Posición: {particula['Posicion']}, Velocidad: {particula['Velocidad']}"
        )
    return particulas


def graficar_particulas_y_funcion_objetivo_3D(
    ax, particulas, mejor_posicion_global, iteracion, mejor_valor_global
):
    ax.cla()

    # Graficar la función objetivo
    x = y = np.linspace(RANGO_POSICION[0], RANGO_POSICION[1], 100)
    X, Y = np.meshgrid(x, y)
    Z = funcion_objetivo(X, Y)
    ax.plot_surface(X, Y, Z, cmap="viridis", alpha=0.6)
    # Graficar las partículas
    for particula in particulas:
        ax.scatter(
            particula["Posicion"][0],
            particula["Posicion"][1],
            funcion_objetivo(*particula["Posicion"]),
            color="red",
        )
    # Graficar la mejor posición global
    ax.scatter(
        mejor_posicion_global[0],
        mejor_posicion_global[1],
        funcion_objetivo(*mejor_posicion_global),
        color="blue",
        s=100,
    )

    ax.set_title(
        f"PSO - Iteración {iteracion + 1}/{MAX_ITERACIONES} | Mejor valor: {mejor_valor_global:.4f}"
    )
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")

    plt.draw()
    plt.pause(PAUSA_VISUALIZACION)


def main():
    plt.ion()
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")

    # Generar las partículas iniciales
    print(f"{'-'*20}Iteración 0{'-'*20}")
    particulas = generar_primeras_particulas(NUM_PARTICULAS, TIPO_VELOCIDAD)

    # Calcular la mejor posición global inicial
    mejor_posicion_global, mejor_valor_global = calcular_mejor_posicion_global(
        particulas
    )

    # Iterar para actualizar las posiciones y velocidades de las partículas
    for iteracion in range(MAX_ITERACIONES):
        print(f"\n\n{'-'*20}Iteración {iteracion + 1}{'-'*20}")

        graficar_particulas_y_funcion_objetivo_3D(
            ax,
            particulas,
            mejor_posicion_global,
            iteracion,
            mejor_valor_global,
        )

        for particula in particulas:
            # Actualizar velocidad
            particula["Velocidad"] = actualizacion_velocidad_global(
                particula["Velocidad"],
                particula["Posicion"],
                particula["pBest_posicion"],  # Mejor posición local es la actual
                mejor_posicion_global,
            )

            # Actualizar posición
            particula["Posicion"] = actualizacion_posicion(
                particula["Posicion"], particula["Velocidad"]
            )

            # Actualizar mejor posición local (pBest)
            valor_actual = funcion_objetivo(*particula["Posicion"])
            if valor_actual < particula["pBest_valor"]:
                particula["pBest_valor"] = valor_actual
                particula["pBest_posicion"] = particula["Posicion"].copy()

            print(
                f"Particula {particula['Particula']}, Posición: {particula['Posicion']}, Velocidad: {particula['Velocidad']}"
            )

        # Calcular la mejor posición global después de actualizar todas las partículas
        mejor_posicion_global, mejor_valor_global = calcular_mejor_posicion_global(
            particulas
        )

    # Mostrar el estado final y dejar la última gráfica fija.
    graficar_particulas_y_funcion_objetivo_3D(
        ax,
        particulas,
        mejor_posicion_global,
        MAX_ITERACIONES - 1,
        mejor_valor_global,
    )
    plt.ioff()
    plt.show()


if __name__ == "__main__":
    main()
