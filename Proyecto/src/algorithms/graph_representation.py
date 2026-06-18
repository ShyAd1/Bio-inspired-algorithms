"""
Fase 4: Representación mediante Grafos
Sistema completo de representación de grafos con visualización
"""
import networkx as nx
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
import json
from .graph_generator import Node, Edge, GraphGenerator
from ..models.map_model import MapModel


class GraphRepresentation:
    """Representación completa de grafos con múltiples algoritmos de análisis"""
    
    def __init__(self, graph_generator: GraphGenerator):
        self.generator = graph_generator
        self.networkx_graph: Optional[nx.Graph] = None
        self.metrics: Dict = {}
        self.centrality_measures: Dict = {}
        self.communities: List[Set[str]] = []
    
    def build_networkx_graph(self) -> bool:
        """Construye grafo NetworkX a partir del generador"""
        try:
            self.networkx_graph = nx.Graph()
            
            # Añadir nodos
            for node_id, node in self.generator.nodes.items():
                self.networkx_graph.add_node(
                    node_id,
                    pos_x=float(node.position[0]),
                    pos_y=float(node.position[1]),
                    element_type=str(node.element_type.value),
                    capacity=node.capacity,
                    floor=node.floor
                )
            
            # Añadir aristas
            for edge in self.generator.edges:
                self.networkx_graph.add_edge(
                    edge.from_node,
                    edge.to_node,
                    weight=edge.weight,
                    distance=edge.distance,
                    connection_type=edge.connection_type
                )
            
            return True
        except Exception as e:
            print(f"Error construyendo grafo NetworkX: {e}")
            return False
    
    def calculate_metrics(self) -> Dict:
        """Calcula métricas importantes del grafo"""
        if not self.networkx_graph:
            return {}
        
        metrics = {
            'number_of_nodes': self.networkx_graph.number_of_nodes(),
            'number_of_edges': self.networkx_graph.number_of_edges(),
            'density': nx.density(self.networkx_graph),
            'average_degree': sum(dict(self.networkx_graph.degree()).values()) / 
                            self.networkx_graph.number_of_nodes() if self.networkx_graph.number_of_nodes() > 0 else 0,
            'is_connected': nx.is_connected(self.networkx_graph),
            'number_of_components': nx.number_connected_components(self.networkx_graph),
        }
        
        # Calcular diámetro si está conectado
        if metrics['is_connected']:
            metrics['diameter'] = nx.diameter(self.networkx_graph)
            metrics['average_shortest_path'] = nx.average_shortest_path_length(self.networkx_graph)
        
        self.metrics = metrics
        return metrics
    
    def calculate_centrality_measures(self) -> Dict:
        """Calcula medidas de centralidad de los nodos"""
        if not self.networkx_graph:
            return {}
        
        measures = {
            'degree_centrality': nx.degree_centrality(self.networkx_graph),
            'betweenness_centrality': nx.betweenness_centrality(self.networkx_graph),
            'closeness_centrality': nx.closeness_centrality(self.networkx_graph),
            'eigenvector_centrality': self._safe_eigenvector_centrality(),
        }
        
        self.centrality_measures = measures
        return measures
    
    def _safe_eigenvector_centrality(self) -> Dict:
        """Calcula eigenvector centrality de forma segura"""
        try:
            if self.networkx_graph:
                return nx.eigenvector_centrality(self.networkx_graph, max_iter=100)
        except:
            pass
        # Retornar centralidad de grado como fallback
        if self.networkx_graph:
            return nx.degree_centrality(self.networkx_graph)
        return {}
    
    def detect_communities(self) -> List[Set[str]]:
        """Detecta comunidades en el grafo"""
        if not self.networkx_graph:
            return []
        
        try:
            # Usar algoritmo de Louvain
            communities = list(nx.community.greedy_modularity_communities(self.networkx_graph))
            self.communities = [set(c) for c in communities]  # type: ignore
            return self.communities
        except:
            # Fallback: componentes conexas
            components = list(nx.connected_components(self.networkx_graph))
            self.communities = [set(c) for c in components]  # type: ignore
            return self.communities
    
    def find_critical_nodes(self, top_n: int = 5) -> List[Tuple[str, float]]:
        """Identifica nodos críticos para la evacuación"""
        if not self.centrality_measures:
            self.calculate_centrality_measures()
        
        if not self.networkx_graph:
            return []
        
        # Combinar varias medidas
        criticality: Dict[str, float] = {}
        for node_id in self.networkx_graph.nodes():
            score = 0.0
            
            # Considerar múltiples medidas
            if 'betweenness_centrality' in self.centrality_measures:
                score += self.centrality_measures['betweenness_centrality'].get(node_id, 0) * 0.4
            if 'closeness_centrality' in self.centrality_measures:
                score += self.centrality_measures['closeness_centrality'].get(node_id, 0) * 0.3
            if 'degree_centrality' in self.centrality_measures:
                score += self.centrality_measures['degree_centrality'].get(node_id, 0) * 0.3
            
            criticality[node_id] = score
        
        # Ordenar y retornar top N
        sorted_nodes = sorted(criticality.items(), key=lambda x: x[1], reverse=True)
        return sorted_nodes[:top_n]
    
    def get_bottlenecks(self) -> List[str]:
        """Identifica cuellos de botella en la red"""
        # Nodos con alta centralidad de intermediación que pueden ser cuellos de botella
        critical = self.find_critical_nodes(10)
        
        bottlenecks = []
        for node_id, _ in critical:
            node = self.generator.nodes.get(node_id)
            if node and len(node.adjacent_nodes) < 4:  # Pocos caminos alternativos
                bottlenecks.append(node_id)
        
        return bottlenecks
    
    def calculate_redundancy(self) -> Dict:
        """Calcula redundancia de la red"""
        if not self.networkx_graph:
            return {}
        
        # Número de caminos alternativos
        redundancy = {}
        for node in self.networkx_graph.nodes():
            paths_count = 0
            neighbors = list(self.networkx_graph.neighbors(node))
            
            if len(neighbors) < 2:
                redundancy[node] = 0
            else:
                # Contar caminos alternativos
                for i, neighbor1 in enumerate(neighbors):
                    for neighbor2 in neighbors[i+1:]:
                        try:
                            paths = list(nx.all_simple_paths(
                                self.networkx_graph, neighbor1, neighbor2, cutoff=3
                            ))
                            paths_count += len(paths)
                        except:
                            pass
                
                redundancy[node] = min(paths_count / max(len(neighbors) - 1, 1), 10)
        
        return redundancy
    
    def export_to_gexf(self, filepath: str) -> bool:
        """Exporta grafo a formato GEXF para visualización"""
        try:
            if self.networkx_graph:
                nx.write_gexf(self.networkx_graph, filepath)
                return True
        except Exception as e:
            print(f"Error exportando a GEXF: {e}")
        return False
    
    def export_to_graphml(self, filepath: str) -> bool:
        """Exporta grafo a formato GraphML"""
        try:
            if self.networkx_graph:
                nx.write_graphml(self.networkx_graph, filepath)
                return True
        except Exception as e:
            print(f"Error exportando a GraphML: {e}")
        return False
    
    def get_graph_summary(self) -> Dict:
        """Obtiene resumen completo del grafo"""
        if not self.metrics:
            self.calculate_metrics()
        if not self.centrality_measures:
            self.calculate_centrality_measures()
        
        critical_nodes = self.find_critical_nodes(3)
        bottlenecks = self.get_bottlenecks()
        
        return {
            'metrics': self.metrics,
            'critical_nodes': critical_nodes,
            'bottlenecks': bottlenecks,
            'number_of_communities': len(self.communities) if self.communities else 0,
            'graph_visualization_formats': ['gexf', 'graphml', 'json']
        }
    
    def to_dict(self) -> Dict:
        """Convierte representación a diccionario"""
        return {
            'generator_data': self.generator.export_to_dict(),
            'metrics': self.metrics,
            'centrality_measures': {
                k: {nid: float(v) for nid, v in measures.items()}
                for k, measures in self.centrality_measures.items()
            } if self.centrality_measures else {},
            'communities': [list(c) for c in self.communities],
        }
    
    def save_to_file(self, filepath: str) -> bool:
        """Guarda representación a archivo JSON"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error guardando grafo: {e}")
        return False
