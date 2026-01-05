import mesa
from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from resource_patch import ResourcePatch
from rigid_agent import RigidForager
from mvt_agent import MVTForager


# Helper functions for data collection
def get_avg_energy_rigid(model):
    """Calculate average energy of all Rigid agents"""
    agents = [a for a in model.agents if isinstance(a, RigidForager)]
    if not agents:
        return 0
    return sum(a.energy for a in agents) / len(agents)


def get_avg_energy_smart(model):
    """Calculate average energy of all Smart (MVT) agents"""
    agents = [a for a in model.agents if isinstance(a, MVTForager)]
    if not agents:
        return 0
    return sum(a.energy for a in agents) / len(agents)


class ForagingModel(Model):
    """
    A model to simulate optimal foraging theory.
    """

    def __init__(self, width=20, height=20, num_patches=10, num_agents=10, seed=None):
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

        # Create AGENTS (Half Rigid, Half Smart)
        # We split num_agents in half
        num_rigid = num_agents // 2
        num_smart = num_agents - num_rigid

        # A. Create Rigid Agents with DIFFERENT strategies
        # We want to see which 'patience' value wins
        strategies = [3, 8, 15, 25, 40]
        for i in range(num_rigid):
            # Assign a strategy from the list (cycling through if more agents than strategies)
            patience_value = strategies[i % len(strategies)]

            agent = RigidForager(self, patience=patience_value)

            # Place agent at random location
            self.place_agent_randomly(agent)

        # B. Smart Agents that use MVT
        for i in range(num_smart):
            agent = MVTForager(self)
            self.place_agent_randomly(agent)

        # Data Collection
        # self.datacollector = DataCollector(
        #     model_reporters={
        #         "Total_Food_Remaining": lambda m: sum([a.current_food for a in m.agents if isinstance(a, ResourcePatch)])
        #     },
        #     agent_reporters={
        #         "Type": lambda a: "Smart" if isinstance(a, MVTForager) else "Rigid",
        #         "Strategy": lambda a: getattr(a, "patience", "Adaptive"),
        #         "Total_Energy": lambda a: getattr(a, "energy", 0)
        #     }
        # )
        self.datacollector = DataCollector(
            model_reporters={
                # We track who has the energy
                "Avg_Rigid_Energy": get_avg_energy_rigid,
                "Avg_Smart_Energy": get_avg_energy_smart,
            }
        )

    def place_agent_randomly(self, agent):
        x = self.random.randrange(self.grid.width)
        y = self.random.randrange(self.grid.height)
        self.grid.place_agent(agent, (x, y))

    def step(self):
        self.agents.shuffle_do("step")

        # Collect data
        self.datacollector.collect(self)
