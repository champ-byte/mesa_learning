import mesa

# class Beneficiary(mesa.Agent):
#     def __init__(self, model):
#         super().__init__(model)
#         self.water_urgency = 0
#         self.food_urgency = 0
#         self.is_critical = False
#         self.days_critical = 0
#         self.claimed_by = None 

#     def step(self):
#         # 1. Decay
#         self.water_urgency = min(self.water_urgency + 2, 100)
#         self.food_urgency = min(self.food_urgency + 1, 100)

#         # 2. Criticality
#         total = self.water_urgency + self.food_urgency
#         if total > 100:
#             self.is_critical = True
#             self.days_critical += 1
#         else:
#             self.is_critical = False
#             self.days_critical = 0 

#         # 3. Death
#         if self.days_critical > 5:
#             self.model.grid.remove_agent(self)
#             self.remove()
import mesa

class Beneficiary(mesa.Agent):
    def __init__(self, model):
        super().__init__(model)
        self.water_urgency = 0
        self.food_urgency = 0
        self.is_critical = False
        self.days_critical = 0
        self.claimed_by = None 

    def move_towards(self, target_pos):
        """
        Moves the agent one step closer to the target position.
        (Copied from Truck logic to give Beneficiaries agency)
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
        # 1. BIOLOGICAL DECAY
        self.water_urgency = min(self.water_urgency + 2, 100)
        self.food_urgency = min(self.food_urgency + 1, 100)

        # 2. STATE ASSESSMENT
        total_stress = self.water_urgency + self.food_urgency
        
        # Criticality Check
        if total_stress > 100:
            self.is_critical = True
            self.days_critical += 1
        else:
            self.is_critical = False
            self.days_critical = 0 

        # Death Check
        if self.days_critical > 5:
            self.model.grid.remove_agent(self)
            self.remove()
            return # Stop executing if dead

        # 3. BEHAVIOR SELECTION (The Needs-Based Logic)
        
        if total_stress > 50:
            # HIGH NEED STATE: Seek Help
            # Move towards the Depot (0,0) where trucks refill
            if self.pos != (0, 0):
                self.move_towards((0, 0))
        else:
            # LOW NEED STATE: Wander / Normal Life
            # Move randomly to simulate local activity
            neighborhood = self.model.grid.get_neighborhood(self.pos, moore=True)
            choice = self.random.choice(neighborhood)
            self.model.grid.move_agent(self, choice)

class Truck(mesa.Agent):
    def __init__(self, model):
        super().__init__(model)
        self.supplies = 100
        self.delivery_rate = 10
        self.target = None 

    def get_distance(self, pos):
        x1, y1 = self.pos
        x2, y2 = pos
        return abs(x1 - x2) + abs(y1 - y2)

    def get_utility(self, beneficiary):
        # Safety Check: If beneficiary is dead (pos is None), return -1 (ignore it)
        if beneficiary.pos is None:
            return -1
            
        dist = self.get_distance(beneficiary.pos)
        urgency = beneficiary.water_urgency + beneficiary.food_urgency
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
        # 1. LOGISTICS
        if self.supplies <= 0:
            if self.target and self.target.claimed_by == self:
                self.target.claimed_by = None
                self.target = None
            
            if self.pos == (0, 0):
                self.supplies = 50
            else:
                self.move_towards((0, 0))
            return

        # 2. TARGET VALIDATION (The Fix is Here)
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
                if isinstance(a, Beneficiary) and (a.claimed_by is None) and (a.pos is not None)
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
                self.target.claimed_by = None
                self.target = None
            else:
                self.move_towards(self.target.pos)