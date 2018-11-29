import random
from Utils import *

codes = []
solutions = []
code_solution = {}
code_effect = {}
effect_list = []
effect_list = list(EFFECTS.ALL_EFFECTS)

def generate_code(code_list):
    ##: TODO
    pass

def decode(code):
    ##: TODO
    pass

def assign_code_solution():
    '''
    Generate 16 codes and create a code_solution dictionary
    '''
    global codes
    global solutions
    global code_solution
    global code_effect
    global effect_list
    list_of_code = []
    for i in range(16):
        # pylint: disable=assignment-from-no-return
        new_code = generate_code(list_of_code)
        list_of_code.append(new_code)
    codes = list_of_code
    solutions = [decode(code) for code in codes]
    for i in range(16):
        code_solution[codes[i]] = solutions[i]
    return code_solution

def assign_code_effect():
    '''
    Assign each code to a random effect
    '''
    for i in range(16):
        code_effect[codes[i]] = effect_list[random.randint(0, len(effect_list))]
    return code_effect
