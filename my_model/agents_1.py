# import mesa

# class Beneficiary(mesa.Agent):
#     """
#     A static agent representing a household or shelter with growing needs.

#     Attributes:
#         water_urgency (int): Current water need level (0-100).
#         food_urgency (int): Current food need level (0-100).
#         is_critical (bool): Flag indicating if total urgency exceeds critical threshold.
#     """
#     def __init__(self, model):
#         super().__init__(model)
#         self.water_urgency = 0  # 0 to 100
#         self.food_urgency = 0   # 0 to 100
#         self.is_critical = False

#     def step(self):
#         # 1. NEED DECAY: Needs grow over time
#         # Water urgency increases faster than food urgency (2 vs 1 per step)
#         self.water_urgency = min(self.water_urgency + 2, 100)
#         self.food_urgency = min(self.food_urgency + 1, 100)

#         # 2. STATE CHECK: Update visual state
#         total_stress = self.water_urgency + self.food_urgency
#         self.is_critical = total_stress > 100

# class Truck(mesa.Agent):
#     """
#     A mobile agent that carries resources and prioritizes the most urgent needs.

#     Attributes:
#         supplies (int): Current amount of supplies the truck is carrying.
#         range (int): The radius within which the truck can detect beneficiaries.
#     """
#     def __init__(self, model):
#         super().__init__(model)
#         self.supplies = 50
#         self.range = 5

#     def move_towards(self, target_pos):
#         """
#         Moves the agent one step closer to the target position.
        
#         Args:
#             target_pos (tuple): The (x, y) coordinates of the destination.
#         """
#         current_x, current_y = self.pos
#         target_x, target_y = target_pos

#         next_x, next_y = current_x, current_y

#         if current_x < target_x: next_x += 1
#         elif current_x > target_x: next_x -= 1
        
#         if current_y < target_y: next_y += 1
#         elif current_y > target_y: next_y -= 1

#         # Move logic
#         self.model.grid.move_agent(self, (next_x, next_y))

#     def step(self):
#         """
#         Executes one step of the truck's behavior:
#         1. Checks supplies and returns to depot if empty.
#         2. Scans for local beneficiaries.
#         3. Prioritizes the most urgent beneficiary.
#         4. Moves towards target or distributes aid if reached.
#         5. Moves randomly if no targets found.
#         """
#         # 1. LOGISTICS CHECK: If empty, return to Depot (0,0)
#         if self.supplies <= 0:
#             if self.pos == (0, 0):
#                 self.supplies = 50 # Refill
#             else:
#                 self.move_towards((0, 0))
#             return

#         # 2. SCANNING: Look for beneficiaries within range
#         neighbors = self.model.grid.get_neighbors(
#             self.pos, moore=True, include_center=True, radius=self.range
#         )
        
#         # Filter for Beneficiaries
#         victims = [a for a in neighbors if isinstance(a, Beneficiary)]

#         if victims:
#             # Sort by total urgency (The "Needs-Based" Logic)
#             # Prioritize agents with the highest combined water and food urgency
#             target = max(victims, key=lambda x: x.water_urgency + x.food_urgency)

#             if self.pos == target.pos:
#                 # Distribute Aid
#                 # Distribute Aid: Prioritize the more urgent need
#                 if target.water_urgency > target.food_urgency:
#                     target.water_urgency = 0
#                 else:
#                     target.food_urgency = 0
#                 self.supplies -= 5 # Consume supplies
#             else:
#                 self.move_towards(target.pos)
#         else:
#             # Random Movement (Exploration)
#             # Use self.random (Mesa's RNG)
#             neighborhood = self.model.grid.get_neighborhood(self.pos, moore=True)
#             self.model.grid.move_agent(self, self.random.choice(neighborhood))
import mesa

class Beneficiary(mesa.Agent):
    """
    A static agent representing a household.
    NOW INCLUDES: Criticality thresholds and Mortality (Death).
    """
    def __init__(self, model):
        super().__init__(model)
        self.water_urgency = 0
        self.food_urgency = 0
        self.is_critical = False
        
        # FIX 1: The Death Spiral Tracker
        self.days_critical = 0 

    def step(self):
        # 1. NEED DECAY (Linear growth)
        self.water_urgency = min(self.water_urgency + 2, 100)
        self.food_urgency = min(self.food_urgency + 1, 100)

        # 2. STATE CHECK & MORTALITY
        total_stress = self.water_urgency + self.food_urgency
        
        if total_stress > 100:
            self.is_critical = True
            self.days_critical += 1
        else:
            self.is_critical = False
            self.days_critical = 0 # Reset if helped in time

        # Death Condition: If critical for > 5 steps, remove from simulation
        if self.days_critical > 5:
            # Safely remove agent from grid and model
            self.model.grid.remove_agent(self)
            self.remove() 

class Truck(mesa.Agent):
    """
    A mobile agent that carries resources.
    NOW INCLUDES: Utility functions and Partial Satisfaction.
    """
    def __init__(self, model):
        super().__init__(model)
        self.supplies = 100
        self.range = 10 # Increased range slightly to make utility interesting
        self.delivery_rate = 10 # Amount to give per interaction

    def get_distance(self, pos):
        """
        Helper: Manhattan distance between self and target.
        """
        x1, y1 = self.pos
        x2, y2 = pos
        return abs(x1 - x2) + abs(y1 - y2)

    def get_utility(self, beneficiary):
        """
        FIX 2: Utility Function
        Calculates a score based on urgency vs. cost (distance).
        Formula: Total Urgency / (Distance + 1)
        """
        # Calculate Distance
        dist = self.get_distance(beneficiary.pos)
        
        # Calculate Total Need
        urgency = beneficiary.water_urgency + beneficiary.food_urgency
        
        # Return Ratio (Higher is better)
        return urgency / (dist + 1)

    def move_towards(self, target_pos):
        current_x, current_y = self.pos
        target_x, target_y = target_pos

        next_x, next_y = current_x, current_y
        if current_x < target_x: next_x += 1
        elif current_x > target_x: next_x -= 1
        if current_y < target_y: next_y += 1
        elif current_y > target_y: next_y -= 1

        self.model.grid.move_agent(self, (next_x, next_y))

    def step(self):
        # 1. LOGISTICS CHECK: If empty, return to Depot
        if self.supplies <= 0:
            if self.pos == (0, 0):
                self.supplies = 50 # Refill
            # else:
            #     self.move_towards((0, 0))
            return

        # 2. SCANNING
        neighbors = self.model.grid.get_neighbors(
            self.pos, moore=True, include_center=True, radius=self.range
        )
        victims = [a for a in neighbors if isinstance(a, Beneficiary)]

        if victims:
            # FIX 2: Decision Complexity (Use Utility, not just Max Urgency)
            target = max(victims, key=self.get_utility)

            # Check if we are at the target's location
            if self.pos == target.pos:
                # FIX 3: Partial Satisfaction (No more Magic Wand)
                # We give at most 'delivery_rate', limited by our own supplies
                amount_to_give = min(self.supplies, self.delivery_rate)

                # Distribute to the most urgent need first
                if target.water_urgency >= target.food_urgency:
                    # Give to water (capped by actual need)
                    actual_given = min(amount_to_give, target.water_urgency)
                    target.water_urgency -= actual_given
                else:
                    # Give to food (capped by actual need)
                    actual_given = min(amount_to_give, target.food_urgency)
                    target.food_urgency -= actual_given
                
                # Deduct from truck inventory
                self.supplies -= actual_given
                
            else:
                self.move_towards(target.pos)
        else:
            # Random Movement if no targets visible
            neighborhood = self.model.grid.get_neighborhood(self.pos, moore=True)
            self.model.grid.move_agent(self, self.random.choice(neighborhood))