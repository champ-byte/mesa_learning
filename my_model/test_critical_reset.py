from refined_model import HumanitarianModel
from refined_agents import Beneficiary, Truck

def test_critical_reset_logic_real_truck():
    print("Testing Critical Days Reset Logic with Real Truck...")
    model = HumanitarianModel(num_beneficiaries=0, num_trucks=0, width=20, height=20)
    
    # Setup Beneficiary
    b = Beneficiary(model)
    model.grid.place_agent(b, (10, 10))
    
    # Setup Truck
    t = Truck(model)
    model.grid.place_agent(t, (10, 10))
    t.supplies = 100
    
    # --- Scenario 2: Delivery to Critical Agent (High Urgency) ---
    print("\n--- Scenario: Delivery occurs for Critical Agent (Urgency > 100) ---")
    b.water_urgency = 120
    b.food_urgency = 0
    b.days_critical = 3
    b.state = "seeking"
    b.is_critical = True
    
    # Manually set target to ensure delivery happens immediately
    t.target = b
    b.claimed_by = t
    
    print(f"Before Delivery: Urgency={b.water_urgency}, Days Critical={b.days_critical}")
    
    # Execute Truck Step (Should deliver and reset)
    t.step()
    
    print(f"After Truck Step: Urgency={b.water_urgency}, Days Critical={b.days_critical}")
    
    if b.days_critical == 0:
        print("RESULT: Days Critical RESET (SUCCESS).")
    else:
        print(f"RESULT: Days Critical is {b.days_critical} (FAILURE).")

    # Optional: See what happens next Beneficiary Step
    b.step()
    print(f"After Beneficiary Step (Next Tick): Urgency={b.water_urgency}, Days Critical={b.days_critical}")
    # Note: If urgency is still > 100, it might increment to 1 here. That is expected behavior (new critical day started).
    # The important part is that the previous '3' was wiped out.

if __name__ == "__main__":
    test_critical_reset_logic_real_truck()
