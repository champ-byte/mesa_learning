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

    #  VISUALIZING THE FORAGERS (AGENTS)
    elif isinstance(agent, RigidForager):
        strategy_colors = {3: "red", 8: "orange", 15: "blue", 25: "purple", 40: "black"}

        color = strategy_colors.get(agent.patience, "gray")

        return {
            "color": color,
            "marker": "o",  # 'o' = circle
            "size": 25,  # Slightly smaller than the patch
            "zorder": 1,  # LAYER 1: Draw ON TOP of layer 0
        }

    # VISUALIZING THE SMART FORAGERS (MVT AGENTS)
    elif isinstance(agent, MVTForager):
        # Smart Agents are GOLD STARS
        return {
            "color": "gold",
            "marker": "*",  # Star shape
            "size": 40,  # Bigger
            "zorder": 2,  # Draw on top of everything
        }

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
        make_space_component(
            agent_portrayal,
            post_process=None,
            draw_grid=True,
        ),
        make_plot_component(["Avg_Smart_Energy", "Avg_Rigid_Energy"]),
    ],
    name="Rigid vs Smart: The MVT Solution",
)

# Run with: solara run app.py
