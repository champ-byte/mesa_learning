from refined_model import HumanitarianModel
from refined_agents import Beneficiary, Truck

def test_beneficiary_seeks_truck():
    print("Testing Beneficiary seeking behavior...")
    
    # 1. Setup Model
    # 0 agents initially, we will place them manually to control the test
    model = HumanitarianModel(num_beneficiaries=0, num_trucks=0, width=20, height=20)
    
    # 2. Place Agents
    truck = Truck(model)
    model.grid.place_agent(truck, (10, 10))
    
    # Place beneficiary 5 steps away
    beneficiary = Beneficiary(model)
    model.grid.place_agent(beneficiary, (10, 15))
    
    # 3. Induce High Stress
    beneficiary.water_urgency = 60 # > 50 threshold
    
    # Explicitly call step to update state
    # We need to run step logic to update state to 'seeking' before behavior triggers
    # Note: step() does update state AND moves.
    
    print(f"Initial positions: Truck@{truck.pos}, Beneficiary@{beneficiary.pos}")
    print(f"Beneficiary Urgency: {beneficiary.water_urgency} (High)")
    
    # 4. Step
    beneficiary.step()
    
    print(f"New position: Beneficiary@{beneficiary.pos}")
    print(f"Beneficiary State: {beneficiary.state}")
    
    # 5. Check Logic
    # Should move towards (10, 10). moving along Y axis from 15 to 10 means newly y should be 14
    expected_pos = (10, 14)
    
    if beneficiary.state == "seeking":
         print("SUCCESS: State transitions to 'seeking' correctly.")
    else:
         print(f"FAILURE: State is {beneficiary.state}, expected 'seeking'")

    if beneficiary.pos == expected_pos:
        print("SUCCESS: Beneficiary moved towards the Truck!")
    else:
        print(f"FAILURE: Beneficiary moved to {beneficiary.pos}, expected {expected_pos}")

def test_beneficiary_state_transitions():
    print("\nTesting Beneficiary State Transitions...")
    model = HumanitarianModel(num_beneficiaries=0, num_trucks=0, width=20, height=20)
    b = Beneficiary(model)
    
    # 1. Initial State
    if b.state == "wandering":
        print("SUCCESS: Initial state is 'wandering'.")
    else:
        print(f"FAILURE: Initial state is '{b.state}'")
        
    # 2. Transition to Seeking
    b.water_urgency = 55
    b.step() # Trigger update
    if b.state == "seeking":
        print("SUCCESS: Transitioned to 'seeking' when urgency > 50.")
    else:
        print(f"FAILURE: State is '{b.state}' after urgency > 50.")
        
    # 3. Transition to Critical
    b.water_urgency = 101
    b.step()
    if b.state == "seeking" and b.is_critical:
        print("SUCCESS: Remains 'seeking' but is_critical=True when urgency > 100.")
    else:
        print(f"FAILURE: State/Critical mismatch. State: {b.state}, Critical: {b.is_critical}")

    # 4. Transition to Dead
    b.days_critical = 6 # Force death condition
    b.step()
    if b.state == "dead":
        print("SUCCESS: Transitioned to 'dead' after extended critical time.")
    else:
        print(f"FAILURE: State is '{b.state}' after prolonged criticality.")

if __name__ == "__main__":
    test_beneficiary_seeks_truck()
    test_beneficiary_state_transitions()
