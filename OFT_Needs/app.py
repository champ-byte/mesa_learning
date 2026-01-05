import solara
from mesa.visualization import SolaraViz, make_space_component, make_plot_component
from model import ForagingModel
from resource_patch import ResourcePatch
from rigid_agent import RigidForager
from mvt_agent import MVTForager


def agent_portrayal(agent):
    """
    Determines how agents look in the browser.
    """
    # VISUALIZING THE RESOURCE PATCHES (FOOD)
    if isinstance(agent, ResourcePatch):
        # Calculate opacity: If 0 food, it becomes invisible
        if agent.current_food <= 0:
            return {"color": "white", "alpha": 0.0, "size": 0}

        opacity = max(0.2, agent.current_food / agent.max_food)

        return {
            "color": "green",
            "marker": "s",  # 's' = square
            "size": 35,  # Fill most of the grid cell
            "alpha": opacity,  # Fade out as it gets eaten
            "zorder": 0,  # LAYER 0: Draw at the bottom
        }

    # VISUALIZING FORAGERS
    elif isinstance(agent, RigidForager) or isinstance(agent, MVTForager):
        portrayal = {"size": 25, "zorder": 1, "marker": "o"}

        # --- STATE VISUALS ---
        # If resting (Sleeping)
        if agent.state == "RESTING":
            portrayal["color"] = "blue"
            portrayal["marker"] = "p" # p = Pentagon (House/Tent)
            return portrayal

        # If starving (Critical Warning)
        if agent.hunger > 80:
            portrayal["color"] = "red"
            return portrayal
        
        # --- NORMAL IDENTIFICATION ---
        if isinstance(agent, RigidForager):
            strategy_colors = {3: "black", 8: "black", 15: "black", 25: "black", 40: "black"}
            portrayal["color"] = strategy_colors.get(agent.patience, "gray")
        
        elif isinstance(agent, MVTForager):
            portrayal["color"] = "gold"
            portrayal["marker"] = "*"
            portrayal["size"] = 40
            
        return portrayal

    return {}


# Define Model Parameters
model_params = {
    "num_agents": {
        "type": "SliderInt",
        "value": 10,
        "label": "Total Agents",
        "min": 2,
        "max": 20,
    },
    "num_patches": {
        "type": "SliderInt",
        "value": 15,
        "label": "Food Patches",
        "min": 5,
        "max": 30,
    },
}

initial_model = ForagingModel(num_agents=10, num_patches=15, width=20, height=20)

#  Create the Visualization Page
page = SolaraViz(
    initial_model,
    model_params=model_params,
    components=[
        make_space_component(agent_portrayal, post_process=None, draw_grid=True),
        # Plot Survivors over time
        # make_plot_component(["Smart_Survivors", "Rigid_Survivors"]),
        make_plot_component(["Avg_Smart_Age", "Avg_Rigid_Age"]),
    ],
    name="Needs-Based Foraging: Survival of the Smartest",
)

# Run with: solara run app.py
