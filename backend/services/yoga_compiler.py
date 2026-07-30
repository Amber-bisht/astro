from __future__ import annotations

from typing import Any
import networkx as nx
from backend.services.ephemeris import SIGN_LORDS, SIGNS, PLANET_ORDER, PLANET_LABELS

def build_horoscope_graph(bundle: ChartBundle) -> nx.MultiDiGraph:
    """Build a Directed Multigraph representing all entities and relationships in the birth chart."""
    G = nx.MultiDiGraph()
    
    # 1. Add House Nodes
    for h in range(1, 13):
        h_str = str(h)
        sign_idx = (bundle.lagna_sign_index + h - 1) % 12
        sign_name = SIGNS[sign_idx]
        lord = SIGN_LORDS[sign_name]
        G.add_node(h_str, type="house", number=h, sign=sign_name, lord=lord)
        
    # 2. Add Sign Nodes
    for idx, sign_name in enumerate(SIGNS):
        lord = SIGN_LORDS[sign_name]
        G.add_node(sign_name, type="sign", index=idx, lord=lord)
        
    # 3. Add Planet Nodes
    for p_key in PLANET_ORDER:
        p_info = bundle.data["planets"][p_key]
        G.add_node(p_key, type="planet", sign=p_info["sign"], house=p_info["house"], degree=p_info["degree"])
        
    # 4. Add Lordship Edges
    for h in range(1, 13):
        h_str = str(h)
        lord_key = G.nodes[h_str]["lord"].lower()
        G.add_edge(h_str, lord_key, relation="lordship")
        
    for sign_name in SIGNS:
        lord_key = G.nodes[sign_name]["lord"].lower()
        G.add_edge(sign_name, lord_key, relation="lordship")
        
    # 5. Add Placement Edges
    for p_key in PLANET_ORDER:
        p_node = G.nodes[p_key]
        G.add_edge(p_key, str(p_node["house"]), relation="placed_house")
        G.add_edge(p_key, p_node["sign"], relation="placed_sign")
        
    # 6. Add Conjunction & Aspect Edges
    # Conjunctions
    for p1 in PLANET_ORDER:
        for p2 in PLANET_ORDER:
            if p1 != p2 and G.nodes[p1]["sign"] == G.nodes[p2]["sign"]:
                G.add_edge(p1, p2, relation="conjunction")
                
    # Aspects received
    aspects = bundle.data.get("aspects", {}).get("aspects_given", {})
    for p_key, aspect_list in aspects.items():
        for target_house_num in aspect_list:
            target_house = str(target_house_num)
            G.add_edge(p_key, target_house, relation="aspect")
            # Aspect to target planets in that house
            for other_p in PLANET_ORDER:
                if other_p != p_key and str(G.nodes[other_p]["house"]) == target_house:
                    G.add_edge(p_key, other_p, relation="aspect")
                    
    return G

# Standardized Yoga Rule Schema matches
def evaluate_graph_yoga(G: nx.MultiDiGraph, yoga_rule: dict[str, Any]) -> bool:
    """Evaluate a compiled yoga schema against the NetworkX graph."""
    try:
        rules = yoga_rule.get("rules", [])
        for rule in rules:
            r_type = rule.get("type")
            if r_type == "relation":
                node_a = rule["node_a"]
                node_b = rule["node_b"]
                relation = rule["relation"]
                
                # Check edges
                has_relation = False
                for u, v, data in G.edges(data=True):
                    if u == node_a and v == node_b:
                        if relation == "aspect_or_conjunction" and data["relation"] in {"aspect", "conjunction"}:
                            has_relation = True
                            break
                        if data["relation"] == relation:
                            has_relation = True
                            break
                if not has_relation:
                    return False
                    
            elif r_type == "kendra":
                node = rule["node"]
                ref = rule["ref"]
                h_val = G.nodes[node]["house"]
                
                if ref == "lagna":
                    if h_val not in {1, 4, 7, 10}:
                        return False
                elif ref == "moon":
                    moon_house = G.nodes["moon"]["house"]
                    dist = ((h_val - moon_house) % 12) + 1
                    if dist not in {1, 4, 7, 10}:
                        return False
                        
            elif r_type == "sign_dignity":
                node = rule["node"]
                dignity = rule["dignity"]
                sign_name = G.nodes[node]["sign"]
                label = PLANET_LABELS[node]
                strength = classify_planet_strength(label, sign_name)
                if strength != dignity:
                    return False
        return True
    except Exception:
        return False

# Library of classical Sanskrit yogas
YOGA_LIBRARY = [
    {
        "name": "Gajakesari Yoga",
        "description": "Jupiter in a Kendra (1, 4, 7, 10) from the Moon, aspecting or conjunct the Moon. Grants wealth, intelligence, and high status.",
        "rules": [
            { "type": "relation", "node_a": "jupiter", "node_b": "moon", "relation": "aspect_or_conjunction" },
            { "type": "kendra", "node": "jupiter", "ref": "moon" }
        ]
    },
    {
        "name": "Adhi Yoga",
        "description": "Benefics (Mercury, Venus, Jupiter) in 6th, 7th, or 8th from the Moon. Bestows fame, leadership, and protection.",
        "rules": [
            { "type": "relation", "node_a": "jupiter", "node_b": "moon", "relation": "aspect" } # simplified proxy check
        ]
    }
]

def compile_and_detect_yogas(bundle: ChartBundle) -> list[dict[str, Any]]:
    """Build the MultiDiGraph and scan for matches using the compiled Yoga patterns."""
    G = build_horoscope_graph(bundle)
    detected_yogas = []
    
    for yoga in YOGA_LIBRARY:
        if evaluate_graph_yoga(G, yoga):
            detected_yogas.append({
                "name": yoga["name"],
                "strength": "High",
                "description": yoga["description"]
            })
            
    return detected_yogas
