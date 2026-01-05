import mesa

class Beneficiary(mesa.Agent):
    """
    Simulates a person with dynamic needs (water and food).
    
    The agent follows a Needs-Based Architecture:
    1. Biological drives (hunger/thirst) increase over time.
    2. Behavior emerges from these drives:
       - Low needs: Random wandering.
       - High needs: Seeking help (Trucks or Depot).
    """
    def __init__(self, model, water_decay=2, food_decay=1, critical_days_threshold=5):
        """
        Create a new Beneficiary agent.

        Args:
            model: The Mesa model instance.
            water_decay (float): Amount water urgency increases per step.
            food_decay (float): Amount food urgency increases per step.
            critical_days_threshold (int): Days before death when critical.
        """
        super().__init__(model)
        self.water_urgency = 0
        self.food_urgency = 0
        self.water_decay = water_decay
        self.food_decay = food_decay
        self.critical_days_threshold = critical_days_threshold
        self.is_critical = False
        self.days_critical = 0
        self.claimed_by = None 
        self.state = "wandering" # Initial state

    def move_towards(self, target_pos):
        """
        Moves the agent one step closer to the target position.
        """
        current_x, current_y = self.pos
        target_x, target_y = target_pos

        next_x, next_y = current_x, current_y
        
        # Simple Logic: Move 1 step along the axis with the biggest difference
        if current_x < target_x: next_x += 1
        elif current_x > target_x: next_x -= 1
        
        if current_y < target_y: next_y += 1
        elif current_y > target_y: next_y -= 1
        
        # Verify the spot is valid (Mesa grids handle this, but good practice)
        self.model.grid.move_agent(self, (next_x, next_y))

    def step(self):
        """
        Advance the agent by one step.
        
        Lifecycle:
        1. Biological Decay: Needs increase naturally.
        2. State Assessment: Determine if agent is critical or dead.
        3. Behavior Selection: Choose action based on stress level.
        """
        # 1. BIOLOGICAL DECAY
        # Urgency increases linearly over time, capped at 100
        self.water_urgency = min(self.water_urgency + self.water_decay, 100)
        self.food_urgency = min(self.food_urgency + self.food_decay, 100)

        # 2. STATE ASSESSMENT
        total_stress = self.water_urgency + self.food_urgency
        
        # State Transitions
        if self.days_critical > self.critical_days_threshold:
            self.state = "dead"
        elif total_stress > 100:
            self.is_critical = True
            self.days_critical += 1
            self.state = "seeking"
        elif total_stress > 50:
            self.is_critical = False # Not critical yet but stressed
            self.days_critical = 0
            self.state = "seeking"
        else:
            self.is_critical = False
            self.days_critical = 0
            self.state = "wandering"

        # Death Check
        if self.state == "dead":
            self.model.grid.remove_agent(self)
            self.remove()
            return # Stop executing if dead

        # 3. BEHAVIOR SELECTION (The Needs-Based Logic)
        
        if self.state == "seeking":
            # HIGH NEED STATE: Seek Help
            
            # IMPROVEMENT: Seek nearest Truck first
            found_truck = self.find_nearest_truck()
            
            if found_truck:
                self.move_towards(found_truck.pos)
            elif self.pos != (0, 0):
                 # Fallback: Move towards the Depot (0,0)
                self.move_towards((0, 0))
        elif self.state == "wandering":
            # LOW NEED STATE: Wander / Normal Life
            # Move randomly to simulate local activity
            neighborhood = self.model.grid.get_neighborhood(self.pos, moore=True)
            choice = self.random.choice(neighborhood)
            self.model.grid.move_agent(self, choice)

    def find_nearest_truck(self):
        """
        Scans the neighborhood for a Truck agent.
        Returns the nearest Truck agent or None.
        """
        trucks = [a for a in self.model.agents if isinstance(a, Truck) and a.pos is not None]
        if not trucks:
            return None
            
        def get_distance(t):
            return abs(self.pos[0] - t.pos[0]) + abs(self.pos[1] - t.pos[1])
            
        nearest_truck = min(trucks, key=get_distance)
        
        # Visibility limit? Let's say they can only see trucks within distance 10.
        if get_distance(nearest_truck) <= 10:
            return nearest_truck
        return None


class Truck(mesa.Agent):
    """
    A delivery agent that distributes supplies to Beneficiaries.
    
    Behavior:
    - Scans for beneficiaries with high needs.
    - Prioritizes targets based on 'utility' (urgency vs distance).
    - Delivers water/food based on which need is more pressing.
    - Refills at the Depot (0,0) when empty.
    """
    def __init__(self, model):
        super().__init__(model)
        self.supplies = 100        # Current amount of resources carried
        self.delivery_rate = 10    # Max resources delivered per step
        self.target = None         # Current Beneficiary agent being targeted 

    def move_towards(self, target_pos):
        """
        Moves the agent one step closer to the target position.
        """
        current_x, current_y = self.pos
        target_x, target_y = target_pos
        
        next_x, next_y = current_x, current_y
        if current_x < target_x: next_x += 1
        elif current_x > target_x: next_x -= 1
        if current_y < target_y: next_y += 1
        elif current_y > target_y: next_y -= 1
        
        self.model.grid.move_agent(self, (next_x, next_y))

    def get_distance(self, pos):
        x1, y1 = self.pos
        x2, y2 = pos
        return abs(x1 - x2) + abs(y1 - y2)

    def get_utility(self, beneficiary):
        """
        Calculates the utility of serving a specific beneficiary.
        
        Formula: Total Urgency / (Distance + 1)
        High urgency and close proximity yield high utility.
        """
        # Safety Check: If beneficiary is dead (pos is None), return -1 (ignore it)
        if beneficiary.pos is None:
            return -1
            
        dist = self.get_distance(beneficiary.pos)
        urgency = beneficiary.water_urgency + beneficiary.food_urgency
        # Add 1 to distance to avoid division by zero
        return urgency / (dist + 1)

    def step(self):
        """
        Advance the truck by one step.
        
        Lifecycle:
        1. Logistics: Refill if empty.
        2. Target Validation: Ensure current target is still valid.
        3. Target Selection: Find a new target if needed.
        4. Action: Move or delivering supplies.
        """
        # 1. LOGISTICS
        # If out of supplies, return to base to refill
        if self.supplies <= 0:
            if self.target and self.target.claimed_by == self:
                self.target.claimed_by = None
                self.target = None
            
            if self.pos == (0, 0):
                self.supplies = 50
            else:
                self.move_towards((0, 0))
            return

        # 2. TARGET VALIDATION
        if self.target:
            # Check if target is removed from model OR has no position (Dead)
            if (not self.target.model) or (self.target.pos is None):
                self.target = None
            elif self.target.claimed_by != self:
                self.target = None
        
        # 3. TARGET SELECTION
        if not self.target:
            all_agents = self.model.agents 
            possible_victims = [
                a for a in all_agents 
                # Check pos is not None to ensure we don't pick dead agents
                if isinstance(a, Beneficiary) 
                and (a.claimed_by is None) 
                and (a.pos is not None)
                # PRIORITY FIX: Ignore agents that are not stressed enough (Green agents)
                and (a.water_urgency + a.food_urgency > 50)
            ]

            if possible_victims:
                best_target = max(possible_victims, key=self.get_utility)
                self.target = best_target
                self.target.claimed_by = self
            else:
                neighborhood = self.model.grid.get_neighborhood(self.pos, moore=True)
                self.model.grid.move_agent(self, self.random.choice(neighborhood))
                return

        # 4. ACTION
        if self.target:
            # DOUBLE CHECK: Ensure target didn't die between validation and action
            if self.target.pos is None:
                self.target = None
                return

            if self.pos == self.target.pos:
                amount_to_give = min(self.supplies, self.delivery_rate)
                
                if self.target.water_urgency >= self.target.food_urgency:
                    actual_given = min(amount_to_give, self.target.water_urgency)
                    self.target.water_urgency -= actual_given
                else:
                    actual_given = min(amount_to_give, self.target.food_urgency)
                    self.target.food_urgency -= actual_given
                
                self.supplies -= actual_given
                self.target.days_critical = 0 # Reset critical clock on any help received
                self.target.claimed_by = None
                self.target = None
            else:
                self.move_towards(self.target.pos)
