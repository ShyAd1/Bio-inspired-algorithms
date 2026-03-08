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
PROBABILIDADES = [
    0
] * TAM_POBALACION  # Lista de probabilidades acumuladas para la selección por ruleta
VARIABLES_ALEATORIAS = [0] * len(
    OBJETOS
)  # Lista de variables aleatorias generadas para la selección de padres

# Seed para reproducibilidad
# random.seed(1143417438)

# Restricciones
# 1.- Al menos debe de haber 3 Love Potions y 2 Skiving Snackbox en la mochila
# por lo que se generaran valores aleatorios entre 3 y 10 para el objeto 2 y entre 2 y 10
# para el objeto 4 para los demas sera entre 0 y 10
# 2.- Seleccion de padres por metodo de ruleta
# 3.- Cruza por metodo de cruza uniforme
# 4.- Mutacion por metodo de mutacion uniforme
# 5.- Seleccion de sobreviviente por metodo generacional con remplazo del padre mas debil


def generar_individuo():
    # Generar un individuo aleatorio que cumpla las restricciones de al menos
    # 3 Love Potions y 2 Skiving Snackbox y que no exceda la capacidad de la mochila
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
        return 0, peso_total  # Penalización por exceder la capacidad
    return valor_total, peso_total


def tabla_fitness(poblacion):
    print("Individuo\t\t\tPeso Total\tFitness")
    for individuo in poblacion:
        fitness, peso_total = calcular_fitness(individuo)
        print(f"{individuo}\t\t{peso_total}\t\t{fitness}")


def tabla_ruleta(poblacion):
    fitness_total = sum(calcular_fitness(individuo)[0] for individuo in poblacion)
    print("Individuo\t\t\tFitness\t\tProbabilidad\tProbabilidad Acumulada")
    prob_acumulada = 0
    for i, individuo in enumerate(poblacion):
        fitness, _ = calcular_fitness(individuo)
        probabilidad = fitness / fitness_total if fitness_total > 0 else 0
        prob_acumulada += probabilidad
        PROBABILIDADES[i] = prob_acumulada
        print(f"{individuo}\t\t{fitness}\t\t{probabilidad:.4f}\t\t{prob_acumulada:.4f}")


def variable_aleatoria():
    return random.uniform(0, 1)


def seleccionar_indice_ruleta(probabilidades_acumuladas):
    r = variable_aleatoria()
    for i, prob in enumerate(probabilidades_acumuladas):
        if r <= prob:
            return i
    # Fallback por posibles redondeos en flotantes.
    return len(probabilidades_acumuladas) - 1


def cruza_uniforme(padre1, padre2):
    # Realizar cruza uniforme entre dos padres para generar dos hijos dentro de
    # la maxima capacidad de la mochila y cumpliendo las restricciones de al
    # menos 3 Love Potions y 2 Skiving Snackbox
    while True:
        if variable_aleatoria() > PROB_CRUZA:
            # No se realiza cruza, los hijos son iguales a los padres,
            # basicamente pasan los padres a la siguiente generacion sin cambios
            return padre1, padre2

        hijo1 = padre1.copy()
        hijo2 = padre2.copy()

        VARIABLES_ALEATORIAS = [0] * len(
            OBJETOS
        )  # Reiniciar variables aleatorias para cruza
        for i in range(0, len(OBJETOS)):
            VARIABLES_ALEATORIAS[i] = variable_aleatoria()

        # Cruza uniforme
        for i in range(len(padre1)):
            if VARIABLES_ALEATORIAS[i] <= UMBRAL_CRUZA:
                hijo1[i] = padre1[i]
                hijo2[i] = padre2[i]
            else:
                hijo1[i] = padre2[i]
                hijo2[i] = padre1[i]

        VARIABLES_ALEATORIAS = [0] * len(
            OBJETOS
        )  # Reiniciar variables aleatorias para mutacion hijo 1

        # Mutacion uniforme para el hijo 1
        for i in range(0, len(OBJETOS)):
            VARIABLES_ALEATORIAS[i] = variable_aleatoria()
        # print("\nVariables aleatorias para mutacion del hijo 1:")
        # print(VARIABLES_ALEATORIAS)

        # print(f"Hijo 1 antes de mutacion: {hijo1}")

        hijo1 = mutacion_uniforme(hijo1)

        # print(f"Hijo 1 despues de mutacion: {hijo1}")

        VARIABLES_ALEATORIAS = [0] * len(
            OBJETOS
        )  # Reiniciar variables aleatorias para mutacion del hijo 2

        # Mutacion uniforme para el hijo 2
        for i in range(0, len(OBJETOS)):
            VARIABLES_ALEATORIAS[i] = variable_aleatoria()
        # print("\nVariables aleatorias para mutacion del hijo 2:")
        # print(VARIABLES_ALEATORIAS)

        # print(f"Hijo 2 antes de mutacion: {hijo2}")

        hijo2 = mutacion_uniforme(hijo2)

        # print(f"Hijo 2 despues de mutacion: {hijo2}")

        # Verificar que los hijos cumplan con la restricción de capacidad
        peso_hijo1 = sum(hijo1[i] * OBJETOS[i][0] for i in range(len(OBJETOS)))
        peso_hijo2 = sum(hijo2[i] * OBJETOS[i][0] for i in range(len(OBJETOS)))

        if peso_hijo1 <= CAP_MOCHILA and peso_hijo2 <= CAP_MOCHILA:
            return hijo1, hijo2
        # Si no cumplen, el while True vuelve a intentar con nueva cruza y mutación


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


def seleccionar_sobreviviente(padre1, padre2, hijo1, hijo2):
    fitness_padre1, _ = calcular_fitness(padre1)
    fitness_padre2, _ = calcular_fitness(padre2)
    fitness_hijo1, _ = calcular_fitness(hijo1)
    fitness_hijo2, _ = calcular_fitness(hijo2)

    # Ordenar de mayor a menor y seleccionar a los dos mejores individuos para
    # la siguiente generación
    individuos = [padre1, padre2, hijo1, hijo2]
    fitnesses = [fitness_padre1, fitness_padre2, fitness_hijo1, fitness_hijo2]

    # Ordenar los individuos por fitness de mayor a menor
    individuos_ordenados = [
        x
        for _, x in sorted(
            zip(fitnesses, individuos), key=lambda pair: pair[0], reverse=True
        )
    ]

    return (
        individuos_ordenados[0],
        individuos_ordenados[1],
    )  # Retornar los dos mejores individuos


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

        nueva_poblacion = []

        while (
            len(nueva_poblacion) < TAM_POBALACION
        ):  # Generar hijos hasta tener la pobalacion completa
            # Seleccionar 2 padres por ruleta forzando índices distintos.
            indice_padre1 = seleccionar_indice_ruleta(PROBABILIDADES)
            indice_padre2 = seleccionar_indice_ruleta(PROBABILIDADES)
            while indice_padre2 == indice_padre1:
                indice_padre2 = seleccionar_indice_ruleta(PROBABILIDADES)

            padre1 = poblacion[indice_padre1]
            padre2 = poblacion[indice_padre2]

            # Cruza uniforme para generar dos hijos
            hijo1, hijo2 = cruza_uniforme(padre1, padre2)

            # Selección de sobrevivientes por método generacional con remplazo del
            # padre más débil pero si la cruza da que no se realiza, entonces los
            # hijos son iguales a los padres y causaria algo erroneo en la seleccion
            # de sobrevivientes, por lo que se verifica que los hijos sean diferentes
            # a los padres
            if (
                hijo1 != padre1
                and hijo1 != padre2
                and hijo2 != padre1
                and hijo2 != padre2
            ):
                sobreviviente1, sobreviviente2 = seleccionar_sobreviviente(
                    padre1, padre2, hijo1, hijo2
                )
                nueva_poblacion.append(sobreviviente1)
                nueva_poblacion.append(sobreviviente2)
            else:
                nueva_poblacion.append(padre1)
                nueva_poblacion.append(padre2)

        poblacion = nueva_poblacion[
            :TAM_POBALACION
        ]  # Mantener solo el tamaño de población definido

        print(
            "\nPoblación después de cruza uniforme mutada y seleccion de sobrevivientes:"
        )
        tabla_fitness(poblacion)

        # Resetear variables para la siguiente generación
        PROBABILIDADES = [0] * TAM_POBALACION
        PADRES_SELECCIONADOS = []
        VARIABLES_ALEATORIAS = [0] * len(OBJETOS)
