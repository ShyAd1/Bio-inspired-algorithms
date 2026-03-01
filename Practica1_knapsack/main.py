import random

# Defincion de parametros
TAM_POBALACION = 10
GENERACIONES = 50
PROB_CRUZA = 0.85
PROB_MUTACION = 0.1
CAP_MOCHILA = 30  # libras
MAX_PARA_CADA_OBJETO = 10
# Definicion de objetos (peso, valor)
# Objeto 1: Decoy Detonators (4, 10)
# Objeto 2: Love Potion (2, 8)
# Objeto 3: Extendable Ears (5, 12)
# Objeto 4: Skiving Snackbox (5, 6)
# Objeto 5: Fever Fudge (2, 3)
# Objeto 6: Puking Pastilles (1.5, 2)
# Objeto 7: Nosebleed Nougat (1, 2)
OBJETOS = [(4, 10), (2, 8), (5, 12), (5, 6), (2, 3), (1.5, 2), (1, 2)]
UMBRAL_CRUZA = 0.5
PROBABILIDADES = [0] * TAM_POBALACION
PADRES_SELECCIONADOS = (
    []
)  # Tupla (padre1, padre2) para cada par de padres seleccionados
VARIABLES_ALEATORIAS = [0] * len(
    OBJETOS
)  # Lista de variables aleatorias generadas para la selección de padres

# Restricciones
# 1.- Al menos debe de haber 3 Love Potions y 2 Skiving Snackbox en la mochila
# Por lo que se generaran valores aleatorios entre 3 y 10 para el objeto 2 y entre 2 y 10 para el objeto 4 para los demas sera entre 0 y 10
# 2.- Seleccion de padres por metodo de ruleta
# 3.- Cruza por metodo de cruza uniforme
# 4.- Mutacion por metodo de mutacion uniforme
# 5.- Seleccion de sobreviviente por metodo generacional con remplazo del padre mas debil


def generar_individuo():
    # Generar un individuo aleatorio que cumpla las restricciones de al menos 3 Love Potions y
    # 2 Skiving Snackbox y que no exceda la capacidad de la mochila
    while True:
        individuo = [
            random.randint(0, MAX_PARA_CADA_OBJETO),  # Decoy Detonators
            random.randint(3, MAX_PARA_CADA_OBJETO),  # Love Potion
            random.randint(0, MAX_PARA_CADA_OBJETO),  # Extendable Ears
            random.randint(2, MAX_PARA_CADA_OBJETO),  # Skiving Snackbox
            random.randint(0, MAX_PARA_CADA_OBJETO),  # Fever Fudge
            random.randint(0, MAX_PARA_CADA_OBJETO),  # Puking Pastilles
            random.randint(0, MAX_PARA_CADA_OBJETO),  # Nosebleed Nougat
        ]
        peso_total = sum(individuo[i] * OBJETOS[i][0] for i in range(len(OBJETOS)))
        if peso_total <= CAP_MOCHILA:
            return individuo


def calcular_fitness(individuo):
    peso_total = sum(individuo[i] * OBJETOS[i][0] for i in range(len(OBJETOS)))
    valor_total = sum(individuo[i] * OBJETOS[i][1] for i in range(len(OBJETOS)))
    if peso_total > CAP_MOCHILA:
        return 0  # Penalización por exceder la capacidad
    return valor_total


def tabla_fitness(poblacion):
    print("Individuo\t\t\tPeso Total\tValor Total\tFitness")
    for individuo in poblacion:
        peso_total = sum(individuo[i] * OBJETOS[i][0] for i in range(len(OBJETOS)))
        valor_total = sum(individuo[i] * OBJETOS[i][1] for i in range(len(OBJETOS)))
        fitness = calcular_fitness(individuo)
        print(f"{individuo}\t\t{peso_total}\t\t{valor_total}\t\t{fitness}")


def tabla_ruleta(poblacion):
    fitness_total = sum(calcular_fitness(individuo) for individuo in poblacion)
    print("Individuo\t\t\tFitness\t\tProbabilidad\tProbabilidad Acumulada")
    prob_acumulada = 0
    for individuo in poblacion:
        fitness = calcular_fitness(individuo)
        probabilidad = fitness / fitness_total if fitness_total > 0 else 0
        prob_acumulada += probabilidad
        PROBABILIDADES[poblacion.index(individuo)] = prob_acumulada
        print(f"{individuo}\t\t{fitness}\t\t{probabilidad:.4f}\t\t{prob_acumulada:.4f}")


def variable_aleatoria():
    return random.uniform(0, 1)


def cruza_uniforme(padre1, padre2):
    hijo1 = padre1.copy()
    hijo2 = padre2.copy()
    for i in range(len(padre1)):
        if VARIABLES_ALEATORIAS[i] <= UMBRAL_CRUZA:
            hijo1[i] = padre1[i]
        else:
            hijo1[i] = padre2[i]

    for i in range(len(padre2)):
        if VARIABLES_ALEATORIAS[i] <= UMBRAL_CRUZA:
            hijo2[i] = padre2[i]
        else:
            hijo2[i] = padre1[i]
    return hijo1, hijo2


def mutacion_uniforme(individuo):
    for i in range(len(individuo)):
        if VARIABLES_ALEATORIAS[i] <= PROB_MUTACION:
            if i == 1:  # Love Potion
                individuo[i] = random.randint(3, MAX_PARA_CADA_OBJETO)
            elif i == 3:  # Skiving Snackbox
                individuo[i] = random.randint(2, MAX_PARA_CADA_OBJETO)
            else:
                individuo[i] = random.randint(0, MAX_PARA_CADA_OBJETO)
    return individuo


if __name__ == "__main__":
    # Generar población inicial
    poblacion = [generar_individuo() for _ in range(TAM_POBALACION)]

    print("Población inicial:")
    for individuo in poblacion:
        print(individuo)

    for generacion in range(GENERACIONES):
        print(f"\nGeneración {generacion + 1}")

        # Evaluar fitness de la población inicial
        print("\nTabla de fitness de la población inicial:")
        tabla_fitness(poblacion)

        # Selección de padres por método de ruleta
        print("\nTabla de selección por ruleta:")
        tabla_ruleta(poblacion)

        # Selección de padres por random.uniform entre 0 y 1 y comparando con las probabilidades acumuladas
        # en forma tupla (padre1, padre2) para cada par de padres seleccionados
        for i in range(TAM_POBALACION):
            r = random.uniform(0, 1)
            print(f"Random: {r:.4f}")
            for j in range(TAM_POBALACION):
                if r <= PROBABILIDADES[j]:
                    PADRES_SELECCIONADOS.append(poblacion[j])
                    break

        print("\nPadres seleccionados:")
        for i in range(0, len(PADRES_SELECCIONADOS), 2):
            print(
                f"Padre 1: {PADRES_SELECCIONADOS[i]}, Padre 2: {PADRES_SELECCIONADOS[i+1]}"
            )

        for i in range(0, len(OBJETOS)):
            VARIABLES_ALEATORIAS[i] = variable_aleatoria()
        print("\nVariables aleatorias para cruza:")
        print(VARIABLES_ALEATORIAS)

        # Cruza por método de cruza uniforme y mutacion uniforme
        poblacion = []
        for i in range(0, len(PADRES_SELECCIONADOS), 2):
            padre1 = PADRES_SELECCIONADOS[i]
            padre2 = PADRES_SELECCIONADOS[i + 1]
            hijo1, hijo2 = cruza_uniforme(padre1, padre2)

            for i in range(0, len(OBJETOS)):
                VARIABLES_ALEATORIAS[i] = variable_aleatoria()
            print("\nVariables aleatorias para mutacion del hijo 1:")
            print(VARIABLES_ALEATORIAS)

            print(f"Hijo 1 antes de mutacion: {hijo1}")

            hijo1 = mutacion_uniforme(hijo1)

            for i in range(0, len(OBJETOS)):
                VARIABLES_ALEATORIAS[i] = variable_aleatoria()
            print("\nVariables aleatorias para mutacion del hijo 2:")
            print(VARIABLES_ALEATORIAS)

            print(f"Hijo 2 antes de mutacion: {hijo2}")

            hijo2 = mutacion_uniforme(hijo2)

            poblacion.append(hijo1)
            poblacion.append(hijo2)

        print("\nPoblación después de cruza uniforme:")
        for individuo in poblacion:
            print(individuo)

        # Evaluar fitness de la nueva población
        print("\nTabla de fitness de la nueva población:")
        tabla_fitness(poblacion)

        # Selección de sobreviviente por método generacional con remplazo del padre más débil

        # Ordenar los padres por fitness de menor a mayor
        padres_ordenados = sorted(
            PADRES_SELECCIONADOS, key=lambda ind: calcular_fitness(ind)
        )

        # Eliminar los hijos que superan la capacidad de la mochila y remplazar por el padre más débil
        nueva_poblacion = []
        for hijo in poblacion:
            if calcular_fitness(hijo) > 0:  # Solo agregar hijos válidos
                nueva_poblacion.append(hijo)
            else:
                nueva_poblacion.append(
                    padres_ordenados[0]
                )  # Reemplazar por el padre más débil

        print("\nNueva población después de selección de sobrevivientes:")
        for individuo in nueva_poblacion:
            print(individuo)

        poblacion = nueva_poblacion

        # Resetear variables para la siguiente generación
        PROBABILIDADES = [0] * TAM_POBALACION
        PADRES_SELECCIONADOS = []
        VARIABLES_ALEATORIAS = [0] * len(OBJETOS)
