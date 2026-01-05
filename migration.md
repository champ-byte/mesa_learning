Let me get the actual migration guide from Mesa directly: # Mesa Migration Guide - Complete Summary

Based on the Mesa migration documentation, here's a comprehensive summary of all migration changes across versions:

## Mesa 3.4.0

### `batch_run` - Random Seed Control
**Change:** New explicit control over random seeds for running multiple replications. 

**Old approach:**
```python
results = mesa.batch_run(
    MoneyModel,
    parameters=params,
    iterations=5,  # Deprecated
    max_steps=100,
)
```

**New approach:**
```python
import numpy as np
import sys

rng = np.random.default_rng(42)
rng_values = rng.integers(0, sys.maxsize, size=(5,))

results = mesa.batch_run(
    MoneyModel,
    parameters=params,
    rng=rng_values. tolist(),  # Pass explicit seed values
    max_steps=100,
    number_processes=1,
    data_collection_period=1,
    display_progress=True,
)
```

---

## Mesa 3.3.0

Mesa 3.3.0 introduced visualization upgrades with new and improved API, full support for both `altair` and `matplotlib` backends.

### Portrayal Components - Dictionary to Class Instance

**Old approach:**
```python
def agent_portrayal(agent):
    return {
        "color": "white" if agent.state == 0 else "black",
        "marker": "s",
        "size": "30"
    }

propertylayer_portrayal = {
    "sugar": {
        "colormap": "pastel1",
        "alpha": 0.75,
        "colorbar": True,
        "vmin": 0,
        "vmax": 10,
    }
}
```

**New approach:**
```python
from mesa.visualization import AgentPortrayalStyle, PropertyLayerStyle

def agent_portrayal(agent):
    return AgentPortrayalStyle(
        color="white" if agent.state == 0 else "black",
        marker="s",
        size=30,
    )

def propertylayer_portrayal(layer):
    if layer.name == "sugar":
        return PropertyLayerStyle(
            color="pastel1", alpha=0.75, colorbar=True, vmin=0, vmax=10
        )
```

### Space Visualization - SpaceRenderer Introduction

**Old approach:**
```python
from mesa.visualization import SolaraViz, make_space_component

SolaraViz(model, components=[make_space_component(agent_portrayal)])
```

**New approach:**
```python
from mesa.visualization import SolaraViz, SpaceRenderer

renderer = SpaceRenderer(model, backend="matplotlib").render(
    agent_portrayal=agent_portrayal,
)

SolaraViz(
    model,
    renderer,
    components=[],
)
```

### Page Tab View
Support for defining multiple pages for different plot components: 

```python
from mesa.visualization import SolaraViz, make_plot_component

SolaraViz(
    model,
    components=[
        make_plot_component("foo", page=1),
        make_plot_component("bar", "baz", page=2),
    ],
)
```

---

## Mesa 3.0 - Major Breaking Changes

### 1. Reserved and Private Variables

**Reserved variables** (can read, but don't modify):
- **Model:** `agents`, `current_id`, `random`, `running`, `steps`, `time`
- **Agent:** `unique_id`, `model`

**Private variables:** Any variable starting with `_` is for Mesa's internal use.

### 2. Removal of `mesa.flat` Namespace
Use full namespace for imports. 

### 3. Mandatory Model Initialization with `super().__init__()`

**Old approach:**
```python
class MyModel(mesa.Model):
    def __init__(self, some_arg):
        # No super() call
        pass
```

**New approach:**
```python
class MyModel(mesa.Model):
    def __init__(self, some_arg_I_need, seed=None, some_kwarg_I_need=True):
        super().__init__(seed=seed)  # Now mandatory
        # Your initialization code here
```

### 4. Automatic Assignment of `unique_id` to Agents

**Old approach:**
```python
# Manual unique_id assignment
class MyAgent(Agent):
    def __init__(self, unique_id, model, ... ):
        super().__init__(unique_id, model)

# Creating agents
agent = MyAgent(unique_id=1, model=self, ...)
agent = MyAgent(self. next_id(), self, ...)
```

**New approach:**
```python
# unique_id is automatic
class MyAgent(Agent):
    def __init__(self, model, ... ):
        super().__init__(model)  # No unique_id parameter

# Creating agents
agent = MyAgent(model=self, ...)
agent = MyAgent(self, ...)
```

**Key notes:**
- `unique_id` automatically starts from 1
- `Model. next_id()` is removed
- Store custom ID values in a separate attribute if needed

### 5. AgentSet and `Model.agents`

The Model class now uses internal structures: 
- `self._agents`: Dictionary of all agents by `unique_id`
- `self._agents_by_type`: Dictionary of AgentSets by type
- `self._all_agents`: AgentSet of all agents

**Important:** `model.agents` is read-only and reserved. 

If you need custom agent storage: 
```python
# Old (now raises AttributeError)
model.agents = my_custom_agents

# New
model.custom_agents = my_custom_agents
```

### 6. Time and Schedulers - Complete Removal

#### Automatic `steps` Counter
The `steps` counter increments automatically with each `Model.step()` call. No manual tracking needed.

#### Removal of Old Time Variables
- `Model._time` → removed (define your own time variable if needed)
- `Model._steps` → renamed to `Model.steps`
- `Model._advance_time()` → removed (happens automatically)

#### Scheduler Replacement with AgentSet

**The entire Time module is deprecated and will be removed in Mesa 3.1.**

##### BaseScheduler
```python
# Old
self.schedule = BaseScheduler(self)
self.schedule.step()

# New
self.agents. do("step")
```

##### RandomActivation
```python
# Old
self.schedule = RandomActivation(self)
self.schedule.step()

# New
self.agents.shuffle_do("step")
```

##### SimultaneousActivation
```python
# Old
self.schedule = SimultaneousActivation(self)
self.schedule.step()

# New
self.agents.do("step")
self.agents.do("advance")
```

##### StagedActivation
```python
# Old
self.schedule = StagedActivation(self, ["stage1", "stage2", "stage3"])
self.schedule.step()

# New
for stage in ["stage1", "stage2", "stage3"]: 
    self.agents.do(stage)

# With shuffle options
stages = ["stage1", "stage2", "stage3"]
if shuffle:
    self.random.shuffle(stages)
for stage in stages:
    if shuffle_between_stages:
        self.agents.shuffle_do(stage)
    else:
        self.agents.do(stage)
```

##### RandomActivationByType
```python
# Old
self.schedule = RandomActivationByType(self)
self.schedule.step()

# New
for agent_class in self.agent_types:
    self.agents_by_type[agent_class]. shuffle_do("step")

# Replacing step_type
# Old
self.schedule. step_type(AgentType)

# New
self.agents_by_type[AgentType].shuffle_do("step")
```

##### General Scheduler Replacement Notes
1. `Model.steps` is automatically incremented (no manual increment needed)
2. `self.schedule.agents` → `self.agents`
3. `self.schedule.get_agent_count()` → `len(self.agents)`
4. `self.schedule.agents_by_type` → `self.agents_by_type`
5. Agents are automatically added/removed from `model.agents` when created/deleted: 
   - Replace `self.schedule.remove(agent)` with `agent.remove()`
   - Replace `self.model.schedule.remove(self)` with `self.remove()`

**Benefit:** No longer bound to 5 distinct schedulers; mix and match AgentSet methods (`do`, `shuffle_do`, `select`, etc.) freely.

### 7. Visualization Changes

#### Model Initialization in SolaraViz

**Old approach:**
```python
from mesa.experimental import SolaraViz

SolaraViz(model_cls, model_params, agent_portrayal=agent_portrayal)
```

**New approach:**
```python
from mesa.visualization import SolaraViz, make_space_component

SolaraViz(model, components=[make_space_component(agent_portrayal)])
```

#### Model Initialization with Keyword Arguments

All model inputs must now be keyword arguments:

```python
class MyModel(mesa.Model):
    def __init__(self, n_agents=10, seed=None):
        super().__init__(seed=seed)
        # Initialize with N agents
```

#### Default Space Visualization

**Old approach:**
```python
from mesa.experimental import SolaraViz

SolaraViz(model_cls, model_params, agent_portrayal=agent_portrayal)
```

**New approach:**
```python
from mesa.visualization import SolaraViz, make_space_component

SolaraViz(model, components=[make_space_component(agent_portrayal)])
```

#### Plotting Measures

**Old approach:**
```python
def make_plot(model):
    ...

SolaraViz(model_cls, model_params, measures=[make_plot, "foo", ["bar", "baz"]])
```

**New approach:**
```python
from mesa.visualization import SolaraViz, make_plot_component

SolaraViz(model, components=[make_plot, make_plot_component("foo"), make_plot_component("bar", "baz")])
```

#### Plotting Text

**Old approach:**
```python
from mesa.experimental import SolaraViz, make_text

def show_steps(model):
    return f"Steps: {model.steps}"

SolaraViz(model_cls, model_params, measures=make_text(show_steps))
```

**New approach:**
```python
from mesa.visualization import SolaraViz

def show_steps(model):
    return f"Steps: {model.steps}"

SolaraViz(model, components=[show_steps])
```

### 8. Removal of `Model.initialize_data_collector`

**Old approach:**
```python
self.initialize_data_collector(...)
```

**New approach:**
```python
self.datacollector = DataCollector(...)
```

---

## Recommended Upgrade Strategy

1. Update to latest Mesa 2.x release (`mesa<3`)
2. Resolve all errors and warnings
3. Update to latest Mesa 3.0. x release (`mesa<3.1`)
4. Resolve all errors and warnings
5. Update to latest Mesa 3.x release (`mesa<4`)

This phased approach ensures smooth migration with each step. 