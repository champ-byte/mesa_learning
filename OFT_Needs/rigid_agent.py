import mesa
from resource_patch import ResourcePatch


class RigidForager(mesa.Agent):
    """
    Rigid Agent:
    - Stay in a food patch for exactly P steps(patience), then leave.
    - Ignores fatigue until it collapses (Fatigue >= 100).
    - Ignores hunger until it dies (Hunger >= 100).
    """

    def __init__(self, model, patience=3):
        super().__init__(model)
        self.patience = patience  # The fixed rule (e.g., stay 3 steps)
        self.energy = 0  # Total food collected (Score)
        self.steps_in_patch = 0  # Counter for current patch

        # INTERNAL STATE
        self.hunger = 0  # 0 to 100 (Die at 100)
        self.fatigue = 0  # 0 to 100 (Pass out at 100)
        self.alive_steps = 0  # Survival metric

        self.state = "WANDERING"  # WANDERING, HARVESTING, RESTING

    def step(self):
        # METABOLISM
        self.hunger += 2
        self.alive_steps += 1

        # CHECK FOR DEATH
        if self.hunger >= 100:
            self.remove()
            return  # Agent is dead

        # CHECK FOR EXHAUSTION (Forced Rest)
        if self.fatigue >= 100:
            self.state = "RESTING"

        # EXECUTE STATE BEHAVIOR
        if self.state == "RESTING":
            self.rest_behavior()
        elif self.state == "HARVESTING":
            self.harvest_behavior()
        else:
            self.wander_behavior()

    def rest_behavior(self):
        """
        Recover fatigue. Rigid agents only do this when forced.
        """
        self.fatigue -= 5
        if self.fatigue <= 0:
            self.fatigue = 0
            self.state = "WANDERING"  # Wake up

    def harvest_behavior(self):
        """
        Behavior executed while the agent is exploiting a resource patch.

        Key limitation:
        ----------------
        The agent does NOT evaluate whether staying is still profitable.
        It only counts time.
        """
        self.fatigue += 1 #extracting resources takes effort

        # Identify the patch we are standing on
        cell_contents = self.model.grid.get_cell_list_contents([self.pos])

        # Find the ResourcePatch object in this cell
        patch = next(
            (obj for obj in cell_contents if isinstance(obj, ResourcePatch)), None
        )

        # Harvest if possible
        if patch:
            # Patch decides how much food is obtained (diminishing returns)
            food = patch.harvest()
            self.energy += food
            self.steps_in_patch += 1
            self.hunger = max(0, self.hunger - food)  # Eating reduces hunger

        # The RIGID RULE: "Have I stayed long enough?"
        # It leaves exactly when the counter hits 'patience', even if food is still good.
        if self.steps_in_patch >= self.patience:
            self.leave_patch()

        # Edge case: If patch is totally empty, forced to leave
        elif patch and patch.current_food <= 0:
            self.leave_patch()

    def wander_behavior(self):
        """
        Behavior when looking for food.
        """
        self.fatigue += 2  # Wandering increases fatigue
        
        # Move randomly (Moore neighborhood = 8 surrounding cells)
        neighbors = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        new_position = self.random.choice(neighbors)
        self.model.grid.move_agent(self, new_position)

        # Check if we landed on food
        cell_contents = self.model.grid.get_cell_list_contents([self.pos])
        patch = next(
            (obj for obj in cell_contents if isinstance(obj, ResourcePatch)), None
        )

        # If found a patch with food, start harvesting
        if patch and patch.current_food > 1.0:  # Ignore crumbs
            self.state = "HARVESTING"
            self.steps_in_patch = 0
            
    def leave_patch(self):
        """Transition from Harvesting to Wandering."""
        self.state = "WANDERING"
        self.steps_in_patch = 0
