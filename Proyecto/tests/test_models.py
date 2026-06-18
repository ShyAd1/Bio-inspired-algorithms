"""
Test - Pruebas unitarias del sistema
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import unittest
from models.agent import Agent, AgentState
from models.building import Building, NodeOccupancy
from models.map_model import MapModel, ElementType, Floor
from models.emergency import Emergency, EmergencyType
from algorithms.pheromone import PheromoneMatrix
from algorithms.ant import Ant
from algorithms.colony import Colony


class TestAgent(unittest.TestCase):
    """Pruebas para la clase Agent"""
    
    def test_agent_creation(self):
        """Verifica la creación correcta de un agente"""
        agent = Agent(id=1, position=(10, 20), floor=0)
        self.assertEqual(agent.id, 1)
        self.assertEqual(agent.position, (10, 20))
        self.assertEqual(agent.floor, 0)
        self.assertEqual(agent.state, AgentState.WALKING)
    
    def test_agent_state_change(self):
        """Verifica cambio de estado"""
        agent = Agent(id=1, position=(0, 0))
        agent.change_state(AgentState.WAITING)
        self.assertEqual(agent.state, AgentState.WAITING)
    
    def test_agent_evacuation(self):
        """Verifica evacuación de agente"""
        agent = Agent(id=1, position=(0, 0))
        agent.evacuate(10.5)
        self.assertEqual(agent.state, AgentState.EVACUATED)
        self.assertEqual(agent.evacuation_time, 10.5)
    
    def test_agent_route(self):
        """Verifica gestión de rutas"""
        agent = Agent(id=1, position=(0, 0))
        route = [0, 1, 2, 3]
        agent.set_route(route)
        self.assertEqual(agent.current_route, route)
        self.assertEqual(agent.get_next_node(), 0)


class TestMapModel(unittest.TestCase):
    """Pruebas para MapModel"""
    
    def test_map_creation(self):
        """Verifica creación de mapa"""
        map_model = MapModel(name="test_map", num_floors=2)
        self.assertEqual(map_model.name, "test_map")
        self.assertEqual(map_model.num_floors, 2)
        self.assertEqual(len(map_model.floors), 2)
    
    def test_add_element(self):
        """Verifica añadir elemento"""
        map_model = MapModel(name="test", num_floors=1)
        element_id = map_model.add_element_to_floor(
            0, ElementType.EXIT, (100, 100), 20, 20, capacity=10
        )
        self.assertGreaterEqual(element_id, 0)
        self.assertIn(element_id, map_model.exits)
    
    def test_map_validation(self):
        """Verifica validación de mapa"""
        map_model = MapModel(name="test", num_floors=1)
        valid, errors = map_model.validate_map()
        self.assertFalse(valid)
        self.assertTrue(any("salida" in e.lower() for e in errors))
    
    def test_map_serialization(self):
        """Verifica serialización JSON"""
        map_model = MapModel(name="test", num_floors=1)
        map_model.add_element_to_floor(0, ElementType.EXIT, (100, 100), 20, 20)
        
        data = map_model.to_dict()
        self.assertEqual(data['name'], "test")
        self.assertEqual(data['num_floors'], 1)


class TestBuilding(unittest.TestCase):
    """Pruebas para Building"""
    
    def test_building_creation(self):
        """Verifica creación de edificio"""
        map_model = MapModel(name="test", num_floors=1)
        building = Building(map_model=map_model)
        self.assertEqual(len(building.agents), 0)
    
    def test_add_agent(self):
        """Verifica añadir agente"""
        map_model = MapModel(name="test", num_floors=1)
        building = Building(map_model=map_model)
        
        agent_id = building.add_agent((50, 50), floor=0)
        self.assertEqual(len(building.agents), 1)
        self.assertEqual(building.agents[agent_id].id, agent_id)
    
    def test_node_occupancy(self):
        """Verifica ocupancia de nodos"""
        occupancy = NodeOccupancy(node_id=1, capacity=5)
        
        self.assertTrue(occupancy.add_agent(10))
        self.assertEqual(occupancy.current_occupancy, 1)
        self.assertAlmostEqual(occupancy.congestion_level, 0.2)


class TestPheromone(unittest.TestCase):
    """Pruebas para PheromoneMatrix"""
    
    def test_pheromone_initialization(self):
        """Verifica inicialización de matriz"""
        pheromone = PheromoneMatrix(5, initial_pheromone=1.0)
        self.assertEqual(pheromone.num_nodes, 5)
    
    def test_pheromone_add(self):
        """Verifica añadir feromonas"""
        pheromone = PheromoneMatrix(3, initial_pheromone=1.0)
        pheromone.add_pheromone(0, 1, 2.0)
        
        value = pheromone.get_pheromone(0, 1)
        self.assertGreater(value, 1.0)
    
    def test_pheromone_evaporation(self):
        """Verifica evaporación"""
        pheromone = PheromoneMatrix(2, initial_pheromone=10.0)
        initial_value = pheromone.get_pheromone(0, 1)
        
        pheromone.evaporate(0.5)
        after_evaporation = pheromone.get_pheromone(0, 1)
        
        self.assertLess(after_evaporation, initial_value)


class TestAnt(unittest.TestCase):
    """Pruebas para Ant"""
    
    def test_ant_creation(self):
        """Verifica creación de hormiga"""
        ant = Ant(id=1, start_node=0, end_node=5)
        self.assertEqual(ant.id, 1)
        self.assertEqual(ant.current_node, 0)
        self.assertEqual(len(ant.visited), 1)
    
    def test_ant_movement(self):
        """Verifica movimiento de hormiga"""
        ant = Ant(id=1, start_node=0, end_node=3)
        ant.move_to(1, distance=10, travel_time=5)
        
        self.assertEqual(ant.current_node, 1)
        self.assertEqual(ant.tour_distance, 10)
        self.assertIn(1, ant.visited)


class TestColony(unittest.TestCase):
    """Pruebas para Colony"""
    
    def test_colony_creation(self):
        """Verifica creación de colonia"""
        colony = Colony(num_ants=10, start_node=0, end_node=5)
        self.assertEqual(len(colony.ants), 10)
    
    def test_colony_reset(self):
        """Verifica reset de colonia"""
        colony = Colony(num_ants=5, start_node=0, end_node=5)
        colony.reset_ants()
        
        for ant in colony.ants:
            self.assertEqual(len(ant.visited), 1)
            self.assertEqual(ant.tour_distance, 0.0)


class TestEmergency(unittest.TestCase):
    """Pruebas para Emergency"""
    
    def test_emergency_creation(self):
        """Verifica creación de emergencia"""
        emergency = Emergency(emergency_type=EmergencyType.FIRE)
        self.assertEqual(emergency.emergency_type, EmergencyType.FIRE)
        self.assertFalse(emergency.is_active)
    
    def test_emergency_activation(self):
        """Verifica activación"""
        emergency = Emergency(emergency_type=EmergencyType.FIRE)
        emergency.activate()
        self.assertTrue(emergency.is_active)


def run_tests():
    """Ejecuta todas las pruebas"""
    unittest.main(verbosity=2)


if __name__ == "__main__":
    run_tests()
