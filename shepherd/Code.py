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
