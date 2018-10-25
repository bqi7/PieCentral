import random

codes = []
solutions = []
code_solution = {}
code_effect = {}
effect_list = list(Utils.EFFECT())

def assign_code_solution():
    '''
    Generate 16 codes and create a code_solution dictionary
    '''
    list_of_code = []
    for i in range(16):
        new_code = generate_code(list_of_code)
        list_of_code.append(newcode)
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
        code_effect[codes[i]] = effect_list[random.randint(0,len(effect_list))]
    return code_effect
