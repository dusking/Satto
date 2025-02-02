from typing import Union, Tuple

def sum_numbers(*numbers: Union[int, float]) -> Union[int, float]:
    """
    Calculate the sum of the given numbers.
    
    Args:
        *numbers: Variable number of integers or floating point numbers
        
    Returns:
        The sum of all provided numbers
        
    Raises:
        TypeError: If any of the provided arguments is not a number
    """
    if not numbers:
        return 0
        
    for num in numbers:
        if not isinstance(num, (int, float)):
            raise TypeError(f"Expected a number, got {type(num).__name__}")
            
    return sum(numbers)
