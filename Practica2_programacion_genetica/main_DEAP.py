import operator
import math
import random
from pathlib import Path

import numpy
import matplotlib.pyplot as plt
import sympy as sp

from functools import partial

from deap import algorithms
from deap import base
from deap import creator
from deap import tools
from deap import gp


# Define new functions
def protectedDiv(left, right):
    try:
        return left / right
    except ZeroDivisionError:
        return 1


pset = gp.PrimitiveSet("MAIN", 2)
pset.addPrimitive(operator.add, 2)
pset.addPrimitive(operator.sub, 2)
pset.addPrimitive(operator.mul, 2)
# Se quitaron las funciones trigonométricas
pset.addPrimitive(protectedDiv, 2)
pset.addPrimitive(operator.neg, 1)
pset.addEphemeralConstant(
    "rand101", partial(random.randint, -5, 5)
)  # Se amplió el rango de constantes aleatorias a [-5, 5]
pset.renameArguments(ARG0="x")
pset.renameArguments(ARG1="y")

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMin)

toolbox = base.Toolbox()
toolbox.register(
    "expr", gp.genHalfAndHalf, pset=pset, min_=1, max_=6
)  # Se aumentó la profundidad máxima de los árboles a 6 para permitir soluciones más complejas
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("compile", gp.compile, pset=pset)


def target_function(x, y):
    return 5 * x**3 * y**2 + 0.5 * x


def simplify_best_individual(individual, pset):
    """Convierte el árbol DEAP a una expresión SymPy y la simplifica."""
    x_sym, y_sym = sp.symbols("x y")

    def tree_to_sympy(tree, idx=0):
        """Recorre el árbol DEAP recursivamente y construye expresión SymPy."""
        if idx >= len(tree):
            return None, idx

        node = tree[idx]

        # Si es un terminal (arity = 0)
        if node.arity == 0:
            if node.name == "x" or node.name == "ARG0":
                return x_sym, idx + 1
            elif node.name == "y" or node.name == "ARG1":
                return y_sym, idx + 1
            else:
                # Es una constante numérica
                try:
                    return sp.Integer(int(node.value)), idx + 1
                except:
                    return sp.symbols(node.name), idx + 1

        # Es una función, procesar argumentos
        args = []
        next_idx = idx + 1
        for _ in range(node.arity):
            arg, next_idx = tree_to_sympy(tree, next_idx)
            if arg is not None:
                args.append(arg)

        # Aplicar operación según el tipo
        if node.name == "add":
            result = args[0] + args[1]
        elif node.name == "sub":
            result = args[0] - args[1]
        elif node.name == "mul":
            result = args[0] * args[1]
        elif node.name == "protectedDiv" or node.name == "div":
            result = args[0] / args[1]
        elif node.name == "neg":
            result = -args[0]
        else:
            result = args[0] if args else None

        return result, next_idx

    try:
        expr, _ = tree_to_sympy(individual)
        if expr is None:
            print(f"Error: No se pudo convertir el árbol a expresión SymPy")
            return None

        # Simplificar y expandir
        simplified = sp.simplify(expr)
        expanded = sp.expand(simplified)

        # Retornar la forma más simple
        if str(expanded) != str(simplified):
            return expanded
        return simplified
    except Exception as e:
        print(f"Error al simplificar: {e}")
        return None


def evalSymbReg(individual, points):
    # Transform the tree expression in a callable function
    func = toolbox.compile(expr=individual)
    # Evaluate the mean squared error between the expression
    # and the real function: 5*x**3*y**2 + x/2
    penalty = 1e20
    sqerrors = []

    for x, y in points:
        try:
            error = func(x, y) - target_function(x, y)
            sq_error = error * error
        except (OverflowError, ZeroDivisionError, ValueError, FloatingPointError):
            return (penalty,)

        if not math.isfinite(sq_error):
            return (penalty,)

        sqerrors.append(sq_error)

    return (math.fsum(sqerrors) / len(points),)


toolbox.register(
    "evaluate",
    evalSymbReg,
    points=[(x / 10.0, y / 10.0) for x in range(-10, 10) for y in range(-10, 10)],
)
toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("mate", gp.cxOnePoint)
toolbox.register("expr_mut", gp.genFull, min_=0, max_=2)
toolbox.register("mutate", gp.mutUniform, expr=toolbox.expr_mut, pset=pset)

toolbox.decorate(
    "mate", gp.staticLimit(key=operator.attrgetter("height"), max_value=17)
)
toolbox.decorate(
    "mutate", gp.staticLimit(key=operator.attrgetter("height"), max_value=17)
)


def show_plots(log, hof):
    # Gráfica de convergencia (mínimo MSE por generación)
    generations = log.select("gen")
    min_fitness = log.chapters["fitness"].select("min")

    plt.figure(figsize=(8, 4))
    plt.plot(generations, min_fitness, marker="o", markersize=3)
    plt.title("Convergencia de la regresión simbólica")
    plt.xlabel("Generación")
    plt.ylabel("MSE mínimo")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    output_dir = Path(__file__).resolve().parent
    convergence_path = output_dir / "convergencia_deap.png"
    plt.savefig(convergence_path, dpi=150)

    # Superficies 3D: función real vs aproximada
    best_individual = hof[0]
    best_func = toolbox.compile(expr=best_individual)

    x = numpy.linspace(-1, 1, 40)
    y = numpy.linspace(-1, 1, 40)
    X, Y = numpy.meshgrid(x, y)

    Z_real = target_function(X, Y)
    Z_pred = numpy.array(
        [
            [best_func(xi, yi) for xi, yi in zip(row_x, row_y)]
            for row_x, row_y in zip(X, Y)
        ]
    )

    fig = plt.figure(figsize=(12, 5))
    ax1 = fig.add_subplot(1, 2, 1, projection="3d")
    ax2 = fig.add_subplot(1, 2, 2, projection="3d")

    ax1.plot_surface(X, Y, Z_real, cmap="viridis", edgecolor="none")
    ax1.set_title("Función objetivo")
    ax1.set_xlabel("x")
    ax1.set_ylabel("y")
    ax1.set_zlabel("f(x, y)")

    ax2.plot_surface(X, Y, Z_pred, cmap="plasma", edgecolor="none")
    ax2.set_title("Mejor aproximación DEAP")
    ax2.set_xlabel("x")
    ax2.set_ylabel("y")
    ax2.set_zlabel("f̂(x, y)")

    plt.tight_layout()
    surfaces_path = output_dir / "superficies_deap.png"
    plt.savefig(surfaces_path, dpi=150)
    print(f"Gráfica guardada: {convergence_path}")
    print(f"Gráfica guardada: {surfaces_path}")
    plt.show()


def main():
    random.seed(318)  # Semilla fija para reproducibilidad

    pop = toolbox.population(
        n=300
    )  # Tamaño de población en 300 para equilibrar exploración y tiempo de ejecución
    hof = tools.HallOfFame(1)

    stats_fit = tools.Statistics(lambda ind: ind.fitness.values)
    stats_size = tools.Statistics(len)
    mstats = tools.MultiStatistics(fitness=stats_fit, size=stats_size)
    mstats.register("avg", numpy.mean)
    mstats.register("std", numpy.std)
    mstats.register("min", numpy.min)
    mstats.register("max", numpy.max)

    pop, log = algorithms.eaSimple(
        pop,
        toolbox,
        0.80,  # Se aumento la probabilidad de cruza de 0.5 a 0.8 para fomentar la exploración de nuevas combinaciones
        0.1,
        50,
        stats=mstats,
        halloffame=hof,
        verbose=True,
    )
    # print log
    return pop, log, hof


if __name__ == "__main__":
    pop, log, hof = main()
    print("Mejor individuo (árbol):", hof[0])
    simplified_expr = simplify_best_individual(hof[0], pset)
    if simplified_expr is not None:
        print(f"Expresión simplificada: {simplified_expr}")
    print("=" * 30)
    show_plots(log, hof)
