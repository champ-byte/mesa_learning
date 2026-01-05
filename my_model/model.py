import mesa
from agents import Beneficiary, Truck


class HumanitarianModel(mesa.Model):
    """
    A model with some number of Beneficiaries and Trucks.

    Attributes:
        num_beneficiaries (int): Number of beneficiary agents.
        num_trucks (int): Number of truck agents.
        grid (mesa.space.MultiGrid): The grid space where agents move.
    """

    def __init__(self, num_beneficiaries=30, num_trucks=3, width=20, height=20, seed=None):
        """
        Create a new Humanitarian model with the given parameters.

        Args:
            num_beneficiaries (int): Number of beneficiaries to create.
            num_trucks (int): Number of trucks to create.
            width (int): Width of the grid.
            height (int): Height of the grid.
            seed (int, optional): Random seed for reproducibility.
        """
        super().__init__(seed=seed)
        
        self.num_beneficiaries = num_beneficiaries
        self.num_trucks = num_trucks
        self.grid = mesa.space.MultiGrid(width, height, torus=False)
        
        # 1. Create and Place Beneficiaries
        for _ in range(self.num_beneficiaries):
            a = Beneficiary(self)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))

        # 2. Create and Place Trucks
        for _ in range(self.num_trucks):
            a = Truck(self)
            self.grid.place_agent(a, (0, 0))

        # 3. Setup Data Collection
        self.datacollector = mesa.DataCollector(
            model_reporters={"Average Urgency": self.get_average_urgency}
        )
        self.running = True

    def step(self):
        """
        Advance the model by one step.
        """
        self.datacollector.collect(self)
        self.agents.shuffle().do("step")

    @staticmethod
    def get_average_urgency(model):
        """
        Helper for data collection: Calculates the average urgency of all beneficiaries.
        
        Args:
            model (HumanitarianModel): The model instance.
            
        Returns:
            float: The average urgency (water + food) or 0 if no beneficiaries.
        """
        beneficiaries = [a for a in model.agents if isinstance(a, Beneficiary)]
        if not beneficiaries: return 0
        total = sum(a.water_urgency + a.food_urgency for a in beneficiaries)
        return total / len(beneficiaries)