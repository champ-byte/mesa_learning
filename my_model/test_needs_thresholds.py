import unittest
import sys
import os

# Add needs_based to path so imports within need_model work
sys.path.append(os.path.join(os.getcwd(), 'needs_based'))

from needs_based.need_agents import Beneficiary, Truck
from needs_based.need_model import HumanitarianModel

class TestNeedsThresholds(unittest.TestCase):
    def setUp(self):
        self.model = HumanitarianModel(num_beneficiaries=1, num_trucks=1, width=20, height=20)
        # Find agents by class name to avoid module path mismatch (needs_based.need_agents vs need_agents)
        self.agent = [a for a in self.model.agents if a.__class__.__name__ == "Beneficiary"][0]
        self.truck = [a for a in self.model.agents if a.__class__.__name__ == "Truck"][0]

    def test_thresholds_transitions(self):
        # Initial state (0 needs) -> Wandering
        self.agent.water_urgency = 0
        self.agent.food_urgency = 0
        self.agent.step()
        self.assertEqual(self.agent.state, "wandering")
        print(f"Low needs: State is {self.agent.state}")

        # Comfort (40) < x < Survival (60) -> e.g. 50 -> Opportunistic
        self.agent.water_urgency = 50
        self.agent.step()
        self.assertEqual(self.agent.state, "opportunistic")
        print(f"Mid needs: State is {self.agent.state}")

        # Survival (60) < x < Critical (90) -> e.g. 80 -> Seeking
        self.agent.water_urgency = 80
        self.agent.step()
        self.assertEqual(self.agent.state, "seeking")
        print(f"High needs: State is {self.agent.state}")

        # Critical (90+) -> Desperate
        self.agent.water_urgency = 95
        self.agent.step()
        self.assertEqual(self.agent.state, "desperate")
        self.assertTrue(self.agent.is_critical)
        print(f"Extreme needs: State is {self.agent.state}")

    def test_partial_satisfaction(self):
        # Set high needs
        self.agent.water_urgency = 80
        self.agent.food_urgency = 20
        total_need_before = 100
        
        # Truck distributes aid
        self.truck.distribute_aid(self.agent, amount=10)
        
        # Check if water received more aid (80% vs 20%)
        # Water share: 80/100 * 10 = 8. New water: 72
        # Food share: 20/100 * 10 = 2. New food: 18
        
        print(f"Water: {self.agent.water_urgency}, Food: {self.agent.food_urgency}")
        self.assertAlmostEqual(self.agent.water_urgency, 72, delta=0.5)
        self.assertAlmostEqual(self.agent.food_urgency, 18, delta=0.5)

if __name__ == '__main__':
    unittest.main()
