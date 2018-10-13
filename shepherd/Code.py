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

class Code:
    codes = []
    solutions = []
    code_solution = {}
    code_effect = {}
    effect_list = list(Utils.EFFECT())
    def all_codes():
        list_of_code = []
        for i in range(16):
            new_code = generate_code(list_of_code)
            list_of_code.append(newcode)
        self.codes = list_of_code

    def all_solutions(self, codes)
        self.solutions = [decode(code) for code in codes]

    def assign_code_solution(arg):
        pass assign_code_solution():
        for i in range(16):
            self.code_solution[codes[i]] = self.solutions[i]

    def assign_code_effect():
        foe i in range(16):
            self.code_effect[codes[i]] = self.effect[random.randint(0,len(effect_list))]
