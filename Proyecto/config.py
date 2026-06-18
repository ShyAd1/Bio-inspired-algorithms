"""
Archivo de configuración centralizada del sistema
"""

# Configuración de pantalla
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900
FPS = 60

# Configuración de colores
COLOR_BACKGROUND = (255, 255, 255)
COLOR_WALL = (50, 50, 50)
COLOR_DOOR = (150, 75, 0)
COLOR_STAIR = (100, 100, 255)
COLOR_EXIT = (0, 200, 0)
COLOR_OBSTACLE = (200, 200, 200)
COLOR_AGENT = (255, 0, 0)
COLOR_AGENT_EVACUATED = (0, 150, 0)
COLOR_AGENT_BLOCKED = (255, 165, 0)
COLOR_PHEROMONE = (255, 255, 0)

# Configuración de agentes
AGENT_RADIUS = 4
AGENT_SPEED = 2.0

# Configuración de capacidades
CORRIDOR_CAPACITY = 20
DOOR_CAPACITY = 5
STAIR_CAPACITY = 8
STAIR_WIDE_CAPACITY = 20
EXIT_CAPACITY = 10

# Configuración de ACO
ACO_ALPHA = 1.0          # Importancia de las feromonas
ACO_BETA = 2.0           # Importancia de la visibilidad/distancia
ACO_GAMMA = 1.5          # Importancia del factor de congestión
ACO_EVAPORATION = 0.1    # Tasa de evaporación de feromonas
ACO_NUM_ANTS = 30        # Número de hormigas para exploración
ACO_MAX_ITERATIONS = 100 # Iteraciones máximas de ACO

# Configuración de simulación
SIMULATION_SPEED = 1.0
SIMULATION_UPDATE_INTERVAL = 5  # Frames entre actualizaciones de ruta

# Configuración de rutas
ROUTE_RECALCULATION_INTERVAL = 10  # Frames entre recálculos de ruta
CONGESTION_THRESHOLD = 0.7         # Umbral de congestión (ocupación/capacidad)

# Tipos de emergencias
EMERGENCY_TYPES = {
    'FIRE': 'Incendio',
    'EARTHQUAKE': 'Terremoto',
    'PREVENTIVE': 'Evacuación Preventiva'
}

# Configuración de reportes
REPORT_FORMAT = 'png'  # Formato de gráficas generadas
REPORT_DPI = 150
