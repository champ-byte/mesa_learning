import mesa
from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector

from resource_patch import ResourcePatch 
from rigid_agent import RigidForager


class ForagingModel(Model):
    """
    A model to simulate optimal foraging theory.
    """
    def __init__(self, width=20, height=20, num_patches=10, num_agents=5, seed=None):
        super().__init__(seed=seed)
        
        self.grid = MultiGrid(width, height, torus=True)
        self.running = True

        # Create Resource Patches
        for _ in range(num_patches):
            
            patch = ResourcePatch(self, max_food=500, decay_rate=0.1)
            
            # Find a random empty spot
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(patch, (x, y))
        
        # Create Rigid Agents with DIFFERENT strategies
        # We want to see which 'patience' value wins
        strategies = [3, 8, 15, 25, 40]
        for i in range(num_agents):
            # Assign a strategy from the list (cycling through if more agents than strategies)
            patience_value = strategies[i % len(strategies)]
            
            agent = RigidForager(self, patience=patience_value)
            
            # Place agent at random location
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(agent, (x, y))
            

        # Data Collection
        self.datacollector = DataCollector(
            model_reporters={
                "Total_Food_Remaining": lambda m: sum(
                    [a.current_food for a in m.agents if isinstance(a, ResourcePatch)]
                )
            },
            agent_reporters={
                "Strategy_Patience": lambda a: getattr(a, "patience", None),
                "Total_Energy": lambda a: getattr(a, "energy", 0)
            }
        )

    def step(self):
        self.agents.shuffle_do("step")
        
        # Collect data
        self.datacollector.collect(self)