import random
from time import sleep


class Item:
    def __init__(self, name, weight, value, lb, ub):
        self.name = name
        self.weight = weight
        self.value = value
        self.lb = lb
        self.ub = ub


# Datos del problema (10 unidades max por producto)
# Nombre, peso (lb), valor (galleons), minimo requerido, maximo permitido
items = [
    Item("Decoy Detonators", 4.0, 10.0, 0, 10),
    Item("Love Potion", 2.0, 8.0, 3, 10),  # minimo 3
    Item("Extendable Ears", 5.0, 12.0, 0, 10),
    Item("Skiving Snackbox", 5.0, 6.0, 2, 10),  # minimo 2
    Item("Fever Fudge", 2.0, 3.0, 0, 10),
    Item("Puking Pastilles", 1.5, 2.0, 0, 10),
    Item("Nosebleed Nougat", 1.0, 2.0, 0, 10),
]

CAPACITY = 30.0

# Parametros ABC solicitados
SWARM_SIZE = 40
EMPLOYED_BEES = 20
ONLOOKER_BEES = 20
LIMIT = 5
MAX_ITERS = 50


def total_weight(sol):
    return sum(x * it.weight for x, it in zip(sol, items))


def total_value(sol):
    return sum(x * it.value for x, it in zip(sol, items))


def random_feasible_solution():
    # Inicializador usando la fórmula x_ij = l_j + r*(u_j - l_j) con r~U(0,1)
    # Truncamos (int) para obtener la parte entera (equivalente a floor para >=0)
    while True:
        sol = []
        for it in items:
            r = random.uniform(0, 1)
            val = it.lb + r * (it.ub - it.lb)
            q = int(val)  # truncar la parte fraccionaria
            sol.append(q)

        if total_weight(sol) <= CAPACITY:
            return sol


def generate_neighbor(x, xk):
    # Vecino ABC: v_ij = x_ij + r * (x_ij - x_kj), r en [0,1]
    v = x[:]  # copiar la solucion actual

    # Escoger aleatoriamente una dimensión j para modificar (item)
    j = random.randint(0, len(items) - 1)
    r = random.uniform(0.0, 1.0)
    v[j] = int(x[j] + r * (x[j] - xk[j]))

    # Si se sale de los límites del item, se marca como inválido
    it = items[j]
    if v[j] < it.lb:
        return v, False
    elif v[j] > it.ub:
        return v, False

    # Si excede la capacidad total, también se considera inválido
    if total_weight(v) > CAPACITY:
        return v, False

    return v, True


def fitness(sol):
    # Calcular el valor total (No necesita penalización porque el generador de soluciones ya asegura factibilidad)
    return total_value(sol)


def roulette_selection(probs):
    r = random.uniform(0.0, 1.0)
    acc = 0.0
    for i, p in enumerate(probs):
        acc += p
        if r <= acc:
            return i
    return len(probs) - 1


def abc_knapsack(seed=42):
    random.seed(seed)

    # Fuentes de alimento = numero de obreras
    food_sources = [random_feasible_solution() for _ in range(EMPLOYED_BEES)]
    trials = [0] * EMPLOYED_BEES

    best = max(food_sources, key=fitness)
    best_fit = fitness(best)

    # Mostrar soluciones iniciales y el mejor
    print("=== Soluciones iniciales (ABC) ===")
    for i, fs in enumerate(food_sources):
        print(
            f"Fuente {i + 1:2d}: {fs} - Valor: {fitness(fs):.2f} - Peso: {total_weight(fs):.2f}"
        )
    print(
        f"\nMejor inicial: {best} - Valor: {best_fit:.2f} - Peso: {total_weight(best):.2f}\n"
    )

    for iter in range(MAX_ITERS):
        # 1) Fase obreras
        for i in range(EMPLOYED_BEES):
            # Escoger aleatoriamente otra fuente de alimento (distinta a i)
            k = random.randint(0, EMPLOYED_BEES - 1)
            while k == i:
                k = random.randint(0, EMPLOYED_BEES - 1)

            candidate, valid = generate_neighbor(food_sources[i], food_sources[k])

            if not valid:
                trials[i] += 1
                continue

            if fitness(candidate) > fitness(food_sources[i]):
                food_sources[i] = candidate
                trials[i] = 0
            else:
                trials[i] += 1

        # Mostrar soluciones después de fase obreras y sus intentos
        print("=== Soluciones después de fase obreras (ABC) ===")
        for i, fs in enumerate(food_sources):
            print(
                f"Fuente {i + 1:2d}: {fs} - Valor: {fitness(fs):.2f} - Peso: {total_weight(fs):.2f} - Trials: {trials[i]}"
            )
        print("\n")

        sleep(0.5)  # Pausa para mejor visualización

        # 2) Fase observadoras, estamos maximizando el valor, así que la probabilidad es proporcional al fitness de cada fuente de alimento
        fits = [fitness(fs) for fs in food_sources]
        fit_sum = sum(fits)
        probs = [f / fit_sum for f in fits]

        for _ in range(ONLOOKER_BEES):
            i = roulette_selection(probs)

            k = random.randint(0, EMPLOYED_BEES - 1)
            while k == i:
                k = random.randint(0, EMPLOYED_BEES - 1)

            candidate, valid = generate_neighbor(food_sources[i], food_sources[k])

            if not valid:
                trials[i] += 1
                continue

            if fitness(candidate) > fitness(food_sources[i]):
                food_sources[i] = candidate
                trials[i] = 0
            else:
                trials[i] += 1

        # Mostrar soluciones después de fase observadoras y sus intentos
        print("=== Soluciones después de fase observadoras (ABC) ===")
        for i, fs in enumerate(food_sources):
            print(
                f"Fuente {i + 1:2d}: {fs} - Valor: {fitness(fs):.2f} - Peso: {total_weight(fs):.2f} - Trials: {trials[i]}"
            )
        print("\n")

        sleep(0.5)  # Pausa para mejor visualización

        # 3) Fase scout (exploracion)
        for i in range(EMPLOYED_BEES):
            if trials[i] >= LIMIT:
                food_sources[i] = random_feasible_solution()
                trials[i] = 0

        # Mostrar soluciones después de fase de exploración y sus intentos
        print("=== Soluciones después de fase scout (ABC) ===")
        for i, fs in enumerate(food_sources):
            print(
                f"Fuente {i + 1:2d}: {fs} - Valor: {fitness(fs):.2f} - Peso: {total_weight(fs):.2f} - Trials: {trials[i]}"
            )
        print("\n")

        sleep(0.5)  # Pausa para mejor visualización

        # Mostrar el mejor encontrado en esta iteracion
        current_best = max(food_sources, key=fitness)
        current_fit = fitness(current_best)
        print(
            f"Mejor en esta iteracion: {current_best} - Valor: {current_fit:.2f} - Peso: {total_weight(current_best):.2f}"
        )

        # Actualizar mejor global
        if current_fit > best_fit:
            best = current_best[:]
            best_fit = current_fit

        # Mostrar el mejor encontrado hasta ahora
        print(
            f"Mejor hasta ahora: {best} - Valor: {best_fit:.2f} - Peso: {total_weight(best):.2f}\n"
        )
        sleep(1)  # Pausa para mejor visualización
        print(f"==== Iteracion {iter} completa ====\n")

    return best, total_value(best), total_weight(best)


if __name__ == "__main__":
    best_sol, best_value, best_weight = abc_knapsack(seed=42)

    print("=== Mejor solucion encontrada (ABC) ===")
    for it, q in zip(items, best_sol):
        print(f"{it.name:20s}: {q}")

    print(f"\nValor total (galleons): {best_value:.2f}")
    print(f"Peso total (lb):        {best_weight:.2f}")
    print(f"Capacidad maxima:       {CAPACITY:.2f}")
    print(
        f"\nMejor solucion: {best_sol} - Valor: {best_value:.2f} - Peso: {best_weight:.2f}\n"
    )
