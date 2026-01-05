import mesa
from resource_patch import ResourcePatch


class RigidForager(mesa.Agent):
    """
    A Rigid Agent that follows a fixed rule:
    'Stay in a food patch for exactly P steps, then leave.'

    This represents the 'Needs Problem': it cannot adapt its patience
    based on hunger or environmental quality.
    """

    def __init__(self, model, patience=3):
        super().__init__(model)
        self.patience = patience  # The fixed rule (e.g., stay 3 steps)
        self.energy = 0  # Total food collected (Score)
        self.steps_in_patch = 0  # Counter for current patch

        # Internal behavioral state
        # WANDERING: searching for patches
        # HARVESTING: extracting food from a patch
        self.state = "WANDERING"

    def step(self):
        if self.state == "HARVESTING":
            self.harvest_behavior()
        else:
            self.wander_behavior()

    def harvest_behavior(self):
        """
        Behavior executed while the agent is exploiting a resource patch.

        Key limitation:
        ----------------
        The agent does NOT evaluate whether staying is still profitable.
        It only counts time.
        """
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
