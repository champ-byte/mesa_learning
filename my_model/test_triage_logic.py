import sys
import os

# Add needs_based directory to sys.path so that 'import need_agents' inside need_model works
sys.path.append(os.path.join(os.path.dirname(__file__), 'needs_based'))

# Now we can import directly as if we were inside the folder
from need_model import HumanitarianModel
from need_agents import Beneficiary, Truck

def test_hybrid_triage():
    print("Testing Hybrid Triage Logic...")
    model = HumanitarianModel(num_beneficiaries=0, num_trucks=0, width=20, height=20)
    
    truck = Truck(model)
    model.grid.place_agent(truck, (0, 0))
    
    # --- SCENARIO 1: Critical (Survival) vs Non-Critical (Efficiency) ---
    print("\n--- Scenario 1: Critical vs Non-Critical ---")
    
    # Critical Agent (Desperate): High Urgency, Far Away
    critical_agent = Beneficiary(model)
    critical_agent.name = "Critical Agent" # Add name
    critical_agent.water_urgency = 95
    critical_agent.food_urgency = 95
    critical_agent.state = "desperate" # Force state
    critical_agent.is_critical = True
    model.grid.place_agent(critical_agent, (0, 10)) # Distance 10
    
    # Non-Critical Agent (Seeking): Moderate Urgency, Very Close
    close_agent = Beneficiary(model)
    close_agent.name = "Close Agent" # Add name
    close_agent.water_urgency = 65
    close_agent.food_urgency = 65 # Total 130
    close_agent.state = "seeking" # Force state
    model.grid.place_agent(close_agent, (0, 1)) # Distance 1
    
    # Current Logic (Utility = Urgency^2 / Dist) might pick Close Agent if dist difference is huge?
    # Or might pick Critical if urgency difference is huge.
    # New Logic MUST pick Critical Agent because they are dying.
    
    truck.step()
    
    target_name = getattr(truck.target, "name", "None")
    print(f"Truck chose: {target_name}")
    
    if truck.target == critical_agent:
        print("SCENARIO 1 RESULT: PASS (Picked Critical Agent)")
    elif truck.target == close_agent:
        print("SCENARIO 1 RESULT: FAIL (Picked Close Agent)")
    else:
        print(f"SCENARIO 1 RESULT: FAIL (Picked {target_name})")

    # --- SCENARIO 2: Logistics (Efficiency) ---
    print("\n--- Scenario 2: Logistics Efficiency (Non-Criticals) ---")
    
    # Use a fresh model for Scenario 2 to avoid any lingering state/grid issues
    model = HumanitarianModel(num_beneficiaries=0, num_trucks=0, width=20, height=20)
    truck = Truck(model)
    model.grid.place_agent(truck, (0, 0))
    
    # Agent A: High Total Urgency, Far Distance
    # Urgency 80, Dist 10 -> Ratio 8
    agent_a = Beneficiary(model)
    agent_a.water_urgency = 40
    agent_a.food_urgency = 40
    agent_a.state = "opportunistic"
    model.grid.place_agent(agent_a, (0, 10))
    
    # Agent B: Moderate Total Urgency, Close Distance
    # Urgency 60, Dist 2 -> Ratio 30 (Better Value)
    agent_b = Beneficiary(model)
    agent_b.water_urgency = 30
    agent_b.food_urgency = 30
    agent_b.state = "opportunistic"
    model.grid.place_agent(agent_b, (0, 2))
    
    truck.step()
    
    print(f"Truck chose: {truck.target}")
    if truck.target == agent_b:
        print("RESULT: Truck chose Agent B (Higher Value/Mile - Correct for Tier 2)")
    elif truck.target == agent_a:
        print("RESULT: Truck chose Agent A (Lower Value/Mile)")
    else:
        print("RESULT: Truck picked nothing")

if __name__ == "__main__":
    test_hybrid_triage()
