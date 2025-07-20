"""Example Python module with functions and classes."""

import os
import sys
from pathlib import Path

def simple_function():
    """A simple function."""
    return "Hello, World!"

def function_with_params(name: str, age: int) -> str:
    """Function with parameters."""
    return f"Name: {name}, Age: {age}"

class ExampleClass:
    """An example class."""
    
    def __init__(self, value: int):
        """Initialize the class."""
        self.value = value
    
    def get_value(self) -> int:
        """Get the value."""
        return self.value
    
    def set_value(self, new_value: int) -> None:
        """Set a new value."""
        self.value = new_value

async def async_function(items: list) -> bool:
    """An async function."""
    for item in items:
        print(item)
    return True
