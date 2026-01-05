import mesa
from resource_patch import ResourcePatch


class MVTForager(mesa.Agent):
    """
    Smart Agent with Needs:
    - Balances Hunger and Fatigue.
    - Rests PROACTIVELY before collapsing.
    - Uses MVT to optimize foraging when healthy i.e It compares the 'Marginal Gain' (next bite) vs 'Long Term Average' (memory).
    """

    def __init__(self, model):
        super().__init__(model)
        self.energy = 0
        self.state = "WANDERING"

        # Moving average window for better MVT decisions
        # Instead of lifetime average, use recent history
        self.food_history = []  # List of (food_gained, steps_taken) tuples
        self.history_window = 50  # Consider last 50 steps
        
        # Initialize with reasonable starting estimate
        # This prevents early overestimation from first big harvests
        self.initial_average = 5.0

        # INTERNAL STATE
        self.hunger = 0
        self.fatigue = 0
        self.alive_steps = 0
        
        # Proactive rest threshold (rest BEFORE collapse)
        self.fatigue_rest_threshold = 70

    def step(self):
        self.hunger += 2
        self.alive_steps += 1

        # DEATH CHECK
        if self.hunger >= 100:
            self.remove()
            return

        # PROACTIVE REST: Rest before exhaustion, not after
        # This is smarter than waiting to collapse
        if self.fatigue >= self.fatigue_rest_threshold and self.state != "RESTING":
            # Only rest if not starving
            if self.hunger < 60:
                self.state = "RESTING"
        
        # FORCED REST: Collapse if fatigue hits 100
        if self.fatigue >= 100: 
            self.state = "RESTING"

        # Execute Behavior
        if self.state == "RESTING":
            self.rest_behavior()
        elif self.state == "HARVESTING":
            self.harvest_behavior()
        else:
            self.wander_behavior()

    def rest_behavior(self):
        self.fatigue -= 5
        if self.fatigue <= 0:
            self.fatigue = 0
            self.state = "WANDERING"

    def harvest_behavior(self):
        self.fatigue += 1  # extracting resources takes effort
        cell_contents = self.model.grid.get_cell_list_contents([self.pos])
        patch = next(
            (obj for obj in cell_contents if isinstance(obj, ResourcePatch)), None
        )

        if not patch:
            self.state = "WANDERING"
            return

        # DECISION LOGIC (The MVT Calculation with Moving Average)
        # Calculate average rate using recent history instead of lifetime
        average_rate = self.get_moving_average()

        # Check what I would get if I stay (current yield, not future)
        marginal_gain = patch.predict_harvest()

        # EMERGENCY OVERRIDE: If starving, ignore MVT and keep eating
        if self.hunger > 80:
            should_leave = False
        else:
            # THE SMART CHOICE:
            # If the current yield is less than my recent average, consider leaving
            # Add a small buffer (0.9x) to avoid leaving too eagerly
            should_leave = marginal_gain < (average_rate * 0.9)

        if should_leave:
            self.state = "WANDERING"
        else:
            # Stay and eat
            food = patch.harvest()
            self.energy += food
            self.hunger = max(0, self.hunger - food)
            
            # Track this harvest in history for moving average
            self.food_history.append(food)
            # Keep only recent history
            if len(self.food_history) > self.history_window:
                self.food_history.pop(0)
            
            # If patch runs dry, leave
            if patch.current_food <= 0:
                self.state = "WANDERING"

    def wander_behavior(self):
        self.fatigue += 2
        
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
    
    def get_moving_average(self):
        """
        Calculate moving average of food gains from recent history.
        Uses initial_average as fallback when history is sparse.
        This prevents MVT from being thrown off by early lucky harvests.
        """
        if len(self.food_history) < 5:
            # Not enough data yet, use conservative initial estimate
            return self.initial_average
        
        # Calculate average from recent harvests
        return sum(self.food_history) / len(self.food_history)