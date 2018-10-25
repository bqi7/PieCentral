import random
class Code:
    def __init__(self, code, solution, perk):
        self.code = code
        self.solution = solution
        self.perk = perk

    @staticmethod
    def look_up_by_solution(codes, solution):
        for c in codes:
            if c.solution == solution:
                return c
        return 'No matching Code object by solution'
    @staticmethod
    def look_up_by_code(codes, code):
        for c in codes:
            if c.code == code:
                return c
        return 'No matching Code object by code'


codes = []
solutions = []
code_solution = {}
code_effect = {}
effect_list = list(Utils.EFFECT())

def assign_code_solution():
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
    for i in range(16):
        code_effect[codes[i]] = effect[random.randint(0,len(effect_list))]
    return code_effect
