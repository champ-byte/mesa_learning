from mesa.visualization import SolaraViz, make_space_component, make_plot_component
from refined_model import HumanitarianModel
from refined_agents import Beneficiary, Truck


def agent_portrayal(agent):
    """
    Defines how agents look in the browser visualization.
    
    Color Coding for Beneficiaries (Needs-Based status):
    - RED (Critical): Total Urgency > 100. Near death.
    - ORANGE (Stressed): Total Urgency > 50. actively seeking help.
    - GREEN (Safe): Low urgency. Wandering randomly.
    
    Trucks:
    - BLUE Squares: Delivery agents.
    
    Args:
        agent: The agent to portray.
        
    Returns:
        dict: A dictionary of style properties (color, size, marker) for the agent.
    """
    if agent is None: return
    
    # Base style
    style = {"size": 50, "marker": "o"} 

    if isinstance(agent, Beneficiary):
        if agent.state == "seeking":
             # Orange (Stressed/Seeking)
             style["color"] = "orange"
             if agent.is_critical:
                 # Red (Critical)
                 style["color"] = "red"
                 style["size"] = 80
        else:
             # Green (Wandering)
             style["color"] = "green"

    elif isinstance(agent, Truck):
        style["color"] = "blue"
        style["marker"] = "s" # Square
        style["size"] = 70
        style["z_order"] = 1  # Draw on top

    return style

# 1. Define Model Parameters (Sliders)
# These parameters will be displayed as sliders in the web interface
model_params = {
    "num_beneficiaries": {
        "type": "SliderInt",
        "value": 30,
        "label": "Number of Beneficiaries",
        "min": 10,
        "max": 100,
        "step": 5,
    },
    "num_trucks": {
        "type": "SliderInt",
        "value": 3,
        "label": "Number of Trucks",
        "min": 1,
        "max": 10,
        "step": 1,
    },
    "critical_days_threshold": {
        "type": "SliderInt",
        "value": 5,
        "label": "Critical Days Threshold",
        "min": 1,
        "max": 20,
        "step": 1,
    },
    "width": 20,
    "height": 20,
}

# 2. Create the Initial Model Instance
initial_model = HumanitarianModel(num_beneficiaries=30, num_trucks=3, width=20, height=20)

# 3. Create the Visualization Page
# SolaraViz creates the interactive dashboard
page = SolaraViz(
    model=initial_model,  # Pass the initial instance to start with
    components=[
        make_space_component(agent_portrayal),
        make_plot_component("Avg Urgency"),
        make_plot_component("Deaths"),
        make_plot_component("Critical Count")
    ],
    model_params=model_params,
    name="Refined Humanitarian Needs Model"
)

# In Solara, this 'page' object is what gets rendered.
# Run this file with: solara run refined_server.py
