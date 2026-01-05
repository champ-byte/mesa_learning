import mesa
from mesa import Agent


class ResourcePatch(Agent):
    """
    ResourcePatch represents a foraging patch (e.g., berry bush, grassland).

    Ecological interpretation:
    - Patches contain a finite amount of food.
    - Food becomes harder to extract the longer a forager stays.
    - This creates diminishing returns, a core assumption of
      Optimal Foraging Theory (OFT) and Marginal Value Theorem (MVT).
    """

    def __init__(self, model, max_food=100, decay_rate=0.1):
        """
        Parameters:
         max_food :
            Maximum food capacity of the patch (patch quality).
         decay_rate :
            Rate at which harvesting efficiency declines with time spent.
            Higher values mean faster depletion (steeper diminishing returns).
        """
        super().__init__(model)
        self.max_food = max_food
        self.current_food = max_food
        self.decay_rate = decay_rate

        # Tracks how long the patch has been continuously exploited
        # Used as a proxy for "time spent in patch" in MVT
        self.steps_harvested = 0

    def harvest(self):
        """
        Returns food amount based on diminishing returns.
        Formula: Gain = Base * e^(-decay * time_spent)
        """

        # If the patch is empty, nothing can be harvested
        if self.current_food <= 0:
            return 0

        # Maximum possible intake when the patch is fresh
        # Represents high food density and low search/handling time
        base_yield = 10

        # Exponential decay models diminishing returns:
        # Easy-to-access food is taken first, leaving harder-to-find resources
        amount = base_yield * (2.718 ** (-self.decay_rate * self.steps_harvested))

        # Ensure the agent cannot harvest more food than remains in the patch
        amount = min(amount, self.current_food)

        self.current_food -= amount

        # Increase exploitation time, making future harvesting less efficient
        self.steps_harvested += 1
        return amount

    def predict_harvest(self):
        """
        specific method to calculate yield WITHOUT changing state.
        Allows the Smart Agent to 'plan'.
        """
        if self.current_food <= 0:
            return 0

        base_yield = 10
        amount = base_yield * (2.718 ** (-self.decay_rate * self.steps_harvested))
        amount = min(amount, self.current_food)
        return amount

    def regenerate(self):
        """
        Slowly regrow food if abandoned.
        """
        if self.steps_harvested > 0:
            # Gradually reduce the exploitation history
            # Making the patch easier to harvest again
            self.steps_harvested = max(0, self.steps_harvested - 1)
            # Slowly restore food up to the maximum capacity
            self.current_food = min(self.max_food, self.current_food + 1)
