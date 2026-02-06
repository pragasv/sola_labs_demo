# %% [markdown]
# #### Libraries

# %%
from pydantic import BaseModel
from typing import List, Dict
import json
import os

# %% [markdown]
# #### Class Memory

# %%
class Memory(BaseModel):
    """A class to manage conversation history in a memory-like structure."""
    conversation_history: List[Dict[str, str]] = []
 
    def add_message(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content})

    def get_recent_messages(self, num: int = 5):
        return self.conversation_history[-num:]    

    

# %% [markdown]
# #### General functions for managing memory

# %%
def save_memory_to_file(file_name_memory, memory):
    """Saves the memory to a file in JSON format."""
    with open(file_name_memory, "w") as file:
        json.dump(memory.dict(), file)

def load_memory_from_file(file_name_memory):
    """Loads the memory from a file in JSON format."""
    try:
        with open(file_name_memory, "r") as file:
            data = json.load(file)
            memory = Memory(**data)
    except FileNotFoundError:
        memory = Memory()
    return memory

def clear_memory_file(file_name_memory):
    """Clears the memory file if it exists."""
    if os.path.exists(file_name_memory):
        os.remove(file_name_memory)


