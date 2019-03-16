import random
from Utils import *

codes = []
solutions = []
code_solution = {}
code_effect = {}

def generate_code(code_list):
    ##: TODO
    return 1234

def decode(code):
    ##: TODO
    return 1234

def assign_code_solution():
    '''
    Generate 16 codes and create a code_solution dictionary
    '''
    codes.clear()
    solutions.clear()
    for i in range(16):
        # pylint: disable=assignment-from-no-return
        new_code = generate_code(codes)
        codes.append(new_code)
    for code in codes:
        solutions.append(decode(code))
    for i in range(16):
        code_solution[codes[i]] = solutions[i]
    return code_solution

def assign_code_effect():
    '''
    Assign each code to a random effect
    '''
    for i in range(16):
        code_effect[codes[i]] = (EFFECTS.TWIST if random.random() <
                                 CONSTANTS.TWIST_CHANCE else
                                 EFFECTS.SPOILED_CANDY)
    return code_effect

def rotate(numbers):
    copy = numbers
    max_num = 0
    while copy:
        num = copy % 10
        copy = copy // 10
        size = math.log(numbers)//math.log(10)
        max_num = num if num > max_num else max_num
    for i in range(max_num):
        lsd = numbers % 10
        numbers = numbers // 10
        msd = (lsd) * 10**(size)
        numbers = numbers + msd
    return int(numbers)

def tennis_ball(num):
    index = 5
    while index > 0:
        if num % 3 == 0:
            num = num // 3
        elif num % 2 == 1:
            num = num * 4 + 2
        else:
            num += 1
        index -= 1
    return num

def most_common(num):
    pass
