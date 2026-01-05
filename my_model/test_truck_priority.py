from refined_model import HumanitarianModel
from refined_agents import Beneficiary, Truck

def test_truck_priorities():
    print("Testing Truck Priority Logic...")
    model = HumanitarianModel(num_beneficiaries=0, num_trucks=0, width=20, height=20)
    
    truck = Truck(model)
    model.grid.place_agent(truck, (10, 10))
    
    # 1. Place a "Green" Agent (Low Urgency) VERY CLOSE
    green_agent = Beneficiary(model)
    green_agent.water_urgency = 10 
    green_agent.food_urgency = 10 # Total = 20 (<= 50)
    model.grid.place_agent(green_agent, (10, 11)) # Distance 1
    
    # 2. Place a "Red" Agent (High Urgency) FAR AWAY
    red_agent = Beneficiary(model)
    red_agent.water_urgency = 80
    red_agent.food_urgency = 0 # Total = 80 (> 50)
    model.grid.place_agent(red_agent, (10, 15)) # Distance 5
    
    print(f"Truck at {truck.pos}")
    print(f"Green Agent at {green_agent.pos} (Urgency 20)")
    print(f"Red Agent at {red_agent.pos} (Urgency 80)")
    
    # 3. Step Truck
    truck.step()
    
    # 4. Check Target
    if truck.target == red_agent:
        print("SUCCESS: Truck chose the Red agent (Critical) despite Green agent being closer.")
    elif truck.target == green_agent:
        print("FAILURE: Truck chose the Green agent (Low Urgency). Logic needs fixing.")
    else:
        print(f"FAILURE: Truck chose {truck.target}")

if __name__ == "__main__":
    test_truck_priorities()
