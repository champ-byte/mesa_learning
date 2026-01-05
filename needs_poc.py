import mesa
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

# ==========================================
# 1. CORE FRAMEWORK (The "API")
# ==========================================

class Need:
    """Represents a single need (e.g., Hunger, Energy)."""
    def __init__(self, name: str, initial_level: float = 0.0, 
                 min_level: float = 0.0, max_level: float = 1.0,
                 decay_rate: float = 0.0, critical_threshold: float = 0.8):
        self.name = name
        self.level = initial_level
        self.min_level = min_level
        self.max_level = max_level
        self.decay_rate = decay_rate
        self.critical_threshold = critical_threshold
        self._history = []

    def update(self, delta: float, step_count: int) -> None:
        """Update need level by delta, respecting bounds."""
        old_level = self.level
        # Clamp value between min and max
        self.level = max(self.min_level, min(self.max_level, self.level + delta))
        self._history.append((step_count, old_level, self.level))

    def decay(self, step_count: int) -> None:
        """Apply natural decay (e.g., getting hungrier)."""
        self.update(self.decay_rate, step_count)

    @property
    def is_critical(self) -> bool:
        return self.level >= self.critical_threshold

    @property
    def urgency(self) -> float:
        """Returns normalized urgency (0.0 to 1.0) if critical."""
        if self.level >= self.critical_threshold:
            return (self.level - self.critical_threshold) / (self.max_level - self.critical_threshold)
        return 0.0


class NeedsDrivenAgent:
    """Mixin to add needs logic to any Mesa Agent."""
    def __init__(self):
        self.needs: Dict[str, Need] = {}
        
    def add_need(self, need: Need) -> None:
        self.needs[need.name] = need

    def get_most_urgent_need(self) -> Optional[Need]:
        """Finds the need with the highest urgency score."""
        critical_needs = [n for n in self.needs.values() if n.is_critical]
        if critical_needs:
            return max(critical_needs, key=lambda n: n.urgency)
        return None

    def update_needs(self, current_step: int) -> None:
        """Decay all needs."""
        for need in self.needs.values():
            need.decay(current_step)


class Action:
    """Base class for actions."""
    def __init__(self, name: str, duration: int = 1, need_effects: Dict[str, float] = None):
        self.name = name
        self.duration = duration
        self.need_effects = need_effects or {}
        self._remaining_duration = duration

    def can_execute(self, agent) -> bool:
        """Override this for logic (e.g., is food nearby?)."""
        return True 

    def execute(self, agent) -> bool:
        """
        Runs one step of the action. 
        Returns True if the action is finished.
        """
        if self._remaining_duration > 0:
            self._remaining_duration -= 1
            if self._remaining_duration == 0:
                self.on_complete(agent)
                return True
        return False

    def on_complete(self, agent) -> None:
        """Apply effects to the agent's needs."""
        print(f"   --> Finished Action: {self.name}")
        for need_name, delta in self.need_effects.items():
            if need_name in agent.needs:
                # Note: We pass the current step for history tracking
                agent.needs[need_name].update(delta, agent.model.steps)
    
    def reset(self) -> None:
        self._remaining_duration = self.duration


# ==========================================
# 2. DECISION SYSTEM ( The "Brain")
# ==========================================

class DecisionStrategy(ABC):
    @abstractmethod
    def select_action(self, agent, available_actions: List[Action]) -> Optional[Action]:
        pass

class GreedyNeedStrategy(DecisionStrategy):
    """Simple Logic: Find most urgent need -> Do action that fixes it."""
    def select_action(self, agent, available_actions: List[Action]) -> Optional[Action]:
        urgent_need = agent.get_most_urgent_need()
        
        # If no urgent needs, maybe do nothing or a default action?
        if not urgent_need:
            return None
        
        print(f"   [!] Critical Need: {urgent_need.name} ({urgent_need.level:.2f})")

        # Filter actions that actually fix this need
        valid_actions = [
            a for a in available_actions 
            if a.can_execute(agent) and a.need_effects.get(urgent_need.name, 0) < 0
        ]
        
        if not valid_actions:
            print("   [?] No actions available to satisfy need.")
            return None
            
        # Pick the one that reduces the need the most
        best_action = min(valid_actions, key=lambda a: a.need_effects.get(urgent_need.name, 0))
        return best_action


class BehaviorManager:
    """Orchestrates the loop: Update Needs -> Decide -> Act."""
    def __init__(self, agent, strategy: DecisionStrategy = None):
        self.agent = agent
        self.strategy = strategy or GreedyNeedStrategy()
        self.available_actions: List[Action] = []
        self.current_action: Optional[Action] = None

    def register_action(self, action: Action) -> None:
        self.available_actions.append(action)

    def step(self) -> None:
        current_step = self.agent.model.steps
        
        # 1. Update Biology (Decay)
        self.agent.update_needs(current_step)

        # 2. Continue current action if busy
        if self.current_action:
            print(f"   ... Continuing {self.current_action.name} (Left: {self.current_action._remaining_duration})")
            is_done = self.current_action.execute(self.agent)
            if is_done:
                self.current_action.reset()
                self.current_action = None
            return

        # 3. Decide new action
        new_action = self.strategy.select_action(self.agent, self.available_actions)
        
        if new_action:
            print(f"   >>> Started Action: {new_action.name}")
            self.current_action = new_action
            # Execute first tick immediately
            is_done = self.current_action.execute(self.agent)
            if is_done:
                self.current_action.reset()
                self.current_action = None
        else:
            print("   ... Idling (No critical needs)")


# ==========================================
# 3. EXAMPLE IMPLEMENTATION (The "Wolf")
# ==========================================

class Wolf(mesa.Agent, NeedsDrivenAgent):
    def __init__(self, model):
        super().__init__(model)
        NeedsDrivenAgent.__init__(self) # Initialize the Mixin
        
        # 1. Define Needs
        # Hunger: Starts at 0, grows by 0.1 per step, critical at 0.6
        self.add_need(Need("Hunger", initial_level=0.0, decay_rate=0.1, critical_threshold=0.6))
        # Energy: Starts at 0 (rested), grows by 0.05 (tired), critical at 0.8
        self.add_need(Need("Fatigue", initial_level=0.0, decay_rate=0.05, critical_threshold=0.8))

        # 2. Setup Brain
        self.behavior = BehaviorManager(self)

        # 3. Register Actions
        # Eat: Takes 1 step, reduces Hunger by 0.5
        self.behavior.register_action(Action("Eat", duration=1, need_effects={"Hunger": -0.5}))
        # Sleep: Takes 3 steps, reduces Fatigue by 1.0
        self.behavior.register_action(Action("Sleep", duration=3, need_effects={"Fatigue": -1.0}))

    def step(self):
        print(f"Wolf {self.unique_id}:")
        self.behavior.step()


class WolfModel(mesa.Model):
    def __init__(self):
        super().__init__()
        self.wolf = Wolf(self)

    def step(self):
        self.agents.shuffle_do("step")

# ==========================================
# 4. RUN SIMULATION
# ==========================================

model = WolfModel()
print("STARTING SIMULATION\n")

for i in range(15):
    print(f"--- Step {i} ---")
    model.step()
    # Print status for debugging
    h = model.wolf.needs['Hunger'].level
    f = model.wolf.needs['Fatigue'].level
    print(f"   [Status] Hunger: {h:.2f}, Fatigue: {f:.2f}\n")