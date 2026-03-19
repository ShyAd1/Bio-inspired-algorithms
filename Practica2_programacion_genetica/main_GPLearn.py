import graphviz
import numpy as np
import matplotlib.pyplot as plt
import shutil
from pathlib import Path
from sklearn.dummy import check_random_state
from gplearn.genetic import SymbolicRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.tree import DecisionTreeRegressor
from graphviz.backend.execute import ExecutableNotFound


# import random


def data_sintetico():
    x0 = np.arange(-1, 1, 1 / 10.0)
    x1 = np.arange(-1, 1, 1 / 10.0)
    x0, x1 = np.meshgrid(x0, x1)
    y_truth = x0**2 - x1**2 + x1 - 1

    ax = plt.figure().add_subplot(projection="3d")
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    surf = ax.plot_surface(
        x0, x1, y_truth, rstride=1, cstride=1, color="green", alpha=0.5
    )
    plt.show()

    return x0, x1, y_truth


def datos_aleatorios_de_prueba_y_entrenamiento():
    rng = check_random_state(0)
    # Training samples
    X_train = rng.uniform(-1, 1, 100).reshape(50, 2)
    y_train = X_train[:, 0] ** 2 - X_train[:, 1] ** 2 + X_train[:, 1] - 1

    # Testing samples
    X_test = rng.uniform(-1, 1, 100).reshape(50, 2)
    y_test = X_test[:, 0] ** 2 - X_test[:, 1] ** 2 + X_test[:, 1] - 1

    return X_train, y_train, X_test, y_test


def regresion_simbolica(X_train, y_train, X1, X0):
    est_gp = SymbolicRegressor(
        population_size=5000,
        generations=20,
        stopping_criteria=0.01,
        p_crossover=0.7,
        p_subtree_mutation=0.1,
        p_hoist_mutation=0.05,
        p_point_mutation=0.1,
        max_samples=0.9,
        verbose=1,
        parsimony_coefficient=0.01,
        random_state=0,
    )
    est_gp.fit(X_train, y_train)

    print(f"\n\n{est_gp._program}\n\n")

    return est_gp


def comparar_con_modelos(X_train, y_train, X_test, y_test):
    est_tree = DecisionTreeRegressor()
    est_tree.fit(X_train, y_train)
    est_rf = RandomForestRegressor()
    est_rf.fit(X_train, y_train)

    return est_tree, est_rf


def mostrar_superficies_de_decision(
    est_gp, est_tree, est_rf, x0, x1, y_truth, X_train, y_train, X_test, y_test
):
    y_gp = est_gp.predict(np.c_[x0.ravel(), x1.ravel()]).reshape(x0.shape)
    score_gp = est_gp.score(X_test, y_test)
    y_tree = est_tree.predict(np.c_[x0.ravel(), x1.ravel()]).reshape(x0.shape)
    score_tree = est_tree.score(X_test, y_test)
    y_rf = est_rf.predict(np.c_[x0.ravel(), x1.ravel()]).reshape(x0.shape)
    score_rf = est_rf.score(X_test, y_test)

    fig = plt.figure(figsize=(12, 10))

    for i, (y, score, title) in enumerate(
        [
            (y_truth, None, "Ground Truth"),
            (y_gp, score_gp, "SymbolicRegressor"),
            (y_tree, score_tree, "DecisionTreeRegressor"),
            (y_rf, score_rf, "RandomForestRegressor"),
        ]
    ):

        ax = fig.add_subplot(2, 2, i + 1, projection="3d")
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        surf = ax.plot_surface(
            x0, x1, y, rstride=1, cstride=1, color="green", alpha=0.5
        )
        points = ax.scatter(X_train[:, 0], X_train[:, 1], y_train)
        if score is not None:
            score = ax.text(-0.7, 1, 0.2, r"$R^2 = %.6f$" % score, "x", fontsize=14)
        plt.title(title)
    plt.show()


def renderizar_grafo_con_respaldo(dot_data, nombre_salida):
    graph = graphviz.Source(dot_data)
    if shutil.which("dot") is None:
        ruta_dot = Path(f"{nombre_salida}.dot")
        ruta_dot.write_text(dot_data, encoding="utf-8")
        print(
            "Graphviz (dot) no esta disponible en PATH. "
            f"Se guardo el archivo DOT en: {ruta_dot.resolve()}"
        )
        return

    try:
        ruta_render = graph.render(nombre_salida)
        # print(f"Arbol renderizado en: {Path(ruta_render).resolve()}")
    except ExecutableNotFound:
        ruta_dot = Path(f"{nombre_salida}.dot")
        ruta_dot.write_text(dot_data, encoding="utf-8")
        print(
            "No se pudo ejecutar 'dot'. "
            f"Se guardo el archivo DOT en: {ruta_dot.resolve()}"
        )


def inspeccionar_programa(est_gp):
    dot_data = est_gp._program.export_graphviz()
    renderizar_grafo_con_respaldo(dot_data, "program_tree")
    print(f"{est_gp._program.parents}\n\n")


def mostrar_padres(est_gp):
    idx = est_gp._program.parents["donor_idx"]
    fade_nodes = est_gp._program.parents["donor_nodes"]
    dot_data = est_gp._programs[-2][idx].export_graphviz(fade_nodes=fade_nodes)
    renderizar_grafo_con_respaldo(dot_data, "program_tree_parents")


if __name__ == "__main__":
    x0, x1, y_truth = data_sintetico()
    X_train, y_train, X_test, y_test = datos_aleatorios_de_prueba_y_entrenamiento()
    est_gp = regresion_simbolica(X_train, y_train, x0, x1)
    est_tree, est_rf = comparar_con_modelos(X_train, y_train, X_test, y_test)
    mostrar_superficies_de_decision(
        est_gp,
        est_tree,
        est_rf,
        x0,
        x1,
        y_truth,
        X_train,
        y_train,
        X_test,
        y_test,
    )
    inspeccionar_programa(est_gp)
    mostrar_padres(est_gp)
