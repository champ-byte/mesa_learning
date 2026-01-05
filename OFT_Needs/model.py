import mesa
from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from resource_patch import ResourcePatch
from rigid_agent import RigidForager
from mvt_agent import MVTForager


# # Helper functions for data collection
# def count_rigid_survivors(model):
#     """Count how many Rigid agents are still alive"""
#     return len([a for a in model.agents if isinstance(a, RigidForager)])

# def count_smart_survivors(model):
#     """Count how many Smart agents are still alive"""
#     return len([a for a in model.agents if isinstance(a, MVTForager)])
def get_avg_rigid_age(model):
    """Calculate average age of living Rigid agents"""
    agents = [a.alive_steps for a in model.agents if isinstance(a, RigidForager)]
    # Avoid division by zero if all are dead
    return sum(agents) / len(agents) if agents else 0

def get_avg_smart_age(model):
    """Calculate average age of living Smart agents"""
    agents = [a.alive_steps for a in model.agents if isinstance(a, MVTForager)]
    return sum(agents) / len(agents) if agents else 0

# class ForagingModel(Model):
#     """
#     A model to simulate optimal foraging theory.
#     """

#     def __init__(self, width=20, height=20, num_patches=10, num_agents=10, seed=None):
#         super().__init__(seed=seed)

#         self.grid = MultiGrid(width, height, torus=True)
#         self.running = True

#         # Create Resource Patches
#         for _ in range(num_patches):
#             patch = ResourcePatch(self, max_food=500, decay_rate=0.1)

#             # Find a random empty spot
#             x = self.random.randrange(self.grid.width)
#             y = self.random.randrange(self.grid.height)
#             self.grid.place_agent(patch, (x, y))

#         # Create AGENTS (Half Rigid, Half Smart)
#         # We split num_agents in half
#         num_rigid = num_agents // 2
#         num_smart = num_agents - num_rigid

#         # A. Create Rigid Agents with DIFFERENT strategies
#         # We want to see which 'patience' value wins
#         strategies = [3, 5, 17, 21, 40]
#         for i in range(num_rigid):
#             # Assign a strategy from the list (cycling through if more agents than strategies)
#             patience_value = strategies[i % len(strategies)]

#             agent = RigidForager(self, patience=patience_value)

#             # Place agent at random location
#             self.place_agent_randomly(agent)

#         # B. Smart Agents that use MVT
#         for i in range(num_smart):
#             agent = MVTForager(self)
#             self.place_agent_randomly(agent)

#         # # Data Collection
#         # self.datacollector = DataCollector(
#         #     model_reporters={
#         #         "Rigid_Survivors": count_rigid_survivors,
#         #         "Smart_Survivors": count_smart_survivors,
#         #     }
#         # )
#         self.datacollector = DataCollector(
#             model_reporters={
#                 "Avg_Rigid_Age": get_avg_rigid_age,
#                 "Avg_Smart_Age": get_avg_smart_age,
#             }
#         )


#     def place_agent_randomly(self, agent):
#         x = self.random.randrange(self.grid.width)
#         y = self.random.randrange(self.grid.height)
#         self.grid.place_agent(agent, (x, y))

#     def step(self):
#         self.agents.shuffle_do("step")

#         # Collect data
#         self.datacollector.collect(self)
class ForagingModel(Model):
    def __init__(self, width=20, height=20, num_patches=10, num_agents=10, seed=None):
        super().__init__(seed=seed)
        
        self.grid = MultiGrid(width, height, torus=True)
        self.running = True

        # 1. Place Resource Patches (Keep these Random!)
        for _ in range(num_patches):
            patch = ResourcePatch(self, max_food=500, decay_rate=0.1)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(patch, (x, y))

        # 2. Create Agents
        num_rigid = num_agents // 2
        num_smart = num_agents - num_rigid
        strategies = [3, 8, 15, 25, 40]

        # Rigid Agents
        for i in range(num_rigid):
            patience = strategies[i % len(strategies)]
            agent = RigidForager(self, patience=patience)
            
            # CHANGE: Place at Nest instead of Randomly
            self.place_agent_at_nest(agent)

        # Smart Agents
        for i in range(num_smart):
            agent = MVTForager(self)
            
            # CHANGE: Place at Nest
            self.place_agent_at_nest(agent)

        # Data Collection
        self.datacollector = DataCollector(
            model_reporters={
                "Avg_Rigid_Age": get_avg_rigid_age,   # Ensure these match your helpers
                "Avg_Smart_Age": get_avg_smart_age,
            }
        )

    def place_agent_at_nest(self, agent):
        """
        Spawns agent near the center of the grid (The Hive/Nest).
        """
        center_x = self.grid.width // 2
        center_y = self.grid.height // 2
        
        # Add a random offset so they aren't stacked on the exact same pixel
        # Offset between -2 and +2
        x = center_x + self.random.randint(-2, 2)
        y = center_y + self.random.randint(-2, 2)
        
        # Ensure we stay within grid bounds (handling wrap-around automatically if torus=True)
        # But good practice to clamp just in case
        x = x % self.grid.width
        y = y % self.grid.height
        
        self.grid.place_agent(agent, (x, y))

    def step(self):
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)
