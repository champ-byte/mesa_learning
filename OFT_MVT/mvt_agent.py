import mesa
from resource_patch import ResourcePatch


class MVTForager(mesa.Agent):
    """
    A Smart Agent that follows the Marginal Value Theorem (MVT).
    It compares the 'Marginal Gain' (next bite) vs 'Long Term Average' (memory).
    """

    def __init__(self, model):
        super().__init__(model)
        self.energy = 0
        self.state = "WANDERING"

        # Memory to calculate Long-Term Average Rate
        self.lifetime_food = 0
        self.lifetime_steps = 0

    def step(self):
        self.lifetime_steps += 1

        if self.state == "HARVESTING":
            self.harvest_behavior()
        else:
            self.wander_behavior()

    def harvest_behavior(self):
        # Get the Patch
        cell_contents = self.model.grid.get_cell_list_contents([self.pos])
        patch = next(
            (obj for obj in cell_contents if isinstance(obj, ResourcePatch)), None
        )

        if not patch:
            self.state = "WANDERING"
            return

        # DECISION LOGIC (The MVT Calculation)
        # Calculate my global average rate of return (Food per Step)
        # Avoid division by zero at the very start
        global_average_rate = 0
        if self.lifetime_steps > 0:
            global_average_rate = self.lifetime_food / self.lifetime_steps

        # Check what I would get if I stay
        marginal_gain = patch.predict_harvest()

        # THE SMART CHOICE:
        # If the next bite gives less than my average life, I should leave.
        # (We add a small buffer of 0.5 to prevent leaving too early when average is low)
        if marginal_gain < global_average_rate:
            self.state = "WANDERING"
        else:
            # Stay and eat
            food = patch.harvest()
            self.energy += food
            self.lifetime_food += food

            # If patch runs dry, leave
            if patch.current_food <= 0:
                self.state = "WANDERING"

    def wander_behavior(self):
        # Random Movement
        neighbors = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        new_position = self.random.choice(neighbors)
        self.model.grid.move_agent(self, new_position)

        # Check for food
        cell_contents = self.model.grid.get_cell_list_contents([self.pos])
        patch = next(
            (obj for obj in cell_contents if isinstance(obj, ResourcePatch)), None
        )

        if patch and patch.current_food > 1.0:
            self.state = "HARVESTING"
