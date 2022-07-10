#!/usr/bin/env python3
"""6.009 Lab 8: Snek Interpreter"""

import doctest

# NO ADDITIONAL IMPORTS!


###########################
# Snek-related Exceptions #
###########################


class SnekError(Exception):
    """
    A type of exception to be raised if there is an error with a Snek
    program.  Should never be raised directly; rather, subclasses should be
    raised.
    """
    pass


class SnekSyntaxError(SnekError):
    """
    Exception to be raised when trying to evaluate a malformed expression.
    """
    pass


class SnekNameError(SnekError):
    """
    Exception to be raised when looking up a name that has not been defined.
    """
    pass


class SnekEvaluationError(SnekError):
    """
    Exception to be raised if there is an error during evaluation other than a
    SnekNameError.
    """
    pass


#####################
# Environment Class #
#####################
class Environment:
    def __init__(self, parent=None):
        '''
        Initializes the parent pointer environment and the associated
        variables in the environment
        '''
        self.parent = parent
        self.variables = {}
    
    def set_var(self, var, val):
        '''
        Maps {var: val} in environment's variable dict
        '''
        self.variables[var] = val
    
    def get_var(self, var):
        '''
        Continues searching for var in the current environment. If not found,
        searches in the environment's parent environment. If parent is None 
        (ie. reached the global frame) and var still not found, raise SnekNameError
        '''
        while self is not None:
            if var in self.variables:
                return self.variables[var]
            self = self.parent
        raise SnekNameError
    

##################
# Function Class #
##################
class Func:
    def __init__(self, parameters, body, environment):
        '''
        Initializes Function's parameter, body, and environment
        '''
        self.parameters = parameters
        self.body = body
        self.environment = environment
    
    def __str__(self):
        return "Function Object\nParameters: " + str(self.parameters) +  " body: " + str(self.body)


############################
# Tokenization and Parsing #
############################


def number_or_symbol(x):
    """
    Helper function: given a string, convert it to an integer or a float if
    possible; otherwise, return the string itself

    >>> number_or_symbol('8')
    8
    >>> number_or_symbol('-5.32')
    -5.32
    >>> number_or_symbol('1.2.3.4')
    '1.2.3.4'
    >>> number_or_symbol('x')
    'x'
    """
    try:
        return int(x)
    except ValueError:
        try:
            return float(x)
        except ValueError:
            return x


def tokenize(source):
    """
    Splits an input string into meaningful tokens (left parens, right parens,
    other whitespace-separated values).  Returns a list of strings.

    Arguments:
        source (str): a string containing the source code of a Snek
                      expression

    >>> print(tokenize("(cat (dog (tomato)))"))
    ['(', 'cat', '(', 'dog', '(', 'tomato', ')', ')', ')']
    
    """
    
    # split based on new lines
    split = []
    for elt in source.split("\n"):
               
        # ignore comments (;)
        if ";" in elt:
            if elt[0] == ";":
                pass
            else:
                i = elt.find(";")
                elt_copy = elt[:i]  # grab everything before the comment
                
                # remove white space before and after and append it
                elt_copy = elt_copy.lstrip().rstrip()
                split.append(elt_copy)
        
        # no comments in code
        else:
            split.append(elt)
    
    split_copy = []
    # checks the case of one-line code
    if "\n" not in source:
        source_copy = source[:]
        
        # ignore comments (;)
        if ";" in source:
            if source[0] == ";":
                pass
            else:
                i = source.find(";")
                # grab everything before the comment and remove white space before and after
                source_copy = source[:i].lstrip().rstrip()
        
        # split the one-line code based on spacing
        split_copy = source_copy.split(" ")
    
    # split multi-line code based on spaces in between atomic expressions
    else:
        for elt in split:
            new_split = elt.split(" ")
            split_copy.extend(new_split)
        
        
    # split those with parentheses and variables/number that are adjacent
    # Ex. '(cat'
    tokens = []
    for elt in split_copy:
        temp = ""
        for char in elt:
            if char in ["(", ")"]:
                if temp != "":              # if the ) comes after the num/str   Ex. 'cat)'
                    tokens.append(temp)     # append everything before the )
                    temp = ""               # reset the temp
                tokens.append(char)         # else: just append the ( or )
            else:
                temp += char                # add the char to temp if there's no ( or )
        if temp != "":                      # append temp to tokens if it's not empty
            tokens.append(temp)
    
    return tokens



def check_errors(parsed):
    '''
    Check for SnekSyntaxError specific to define and lambda special forms
    '''
    
    # check define SnekSyntaxError
    if 'define' in parsed:
        # check that there are three elements in parsed
        # (define keyword, variable, and value)
        if len(parsed) != 3:
            raise SnekSyntaxError("There is no variable assignment")
        
        # Check that the second element of parsed (the variable) is a valid variable type:
        # not a int or float
        if type(parsed[1]) in [int, float]:
            raise SnekSyntaxError("Variable name is not allowed")
        
        # Check that the second element of parsed (the variable) is not empty
        if parsed[1] == []:
            raise SnekSyntaxError("Variable name is not allowed")
        
        # Check when second element of parsed is a valid list type (must not have numbers inside)
        if type(parsed[1]) == list:
            for elt in list(parsed[1]):
                # variable name cannot contain an int/float
                if type(elt) in [int, float]:
                    raise SnekSyntaxError("Variable name is not allowed")
    
    # check lambda SnekSyntaxError
    if 'lambda' in parsed:
        # check that lambda only has 3 elements
        # (lambda keyword, list of parameters, body)
        if len(parsed) != 3:
            raise SnekSyntaxError("lambda must contain the keyword, list of parameters, and function body")
        
        # check that the second element is a list of parameters
        # (0 or more strings representing parameter names)
        if type(parsed[1]) != list:
            raise SnekSyntaxError("parameters must be a list")
        
        # check that the parameters are strings
        for param in parsed[1]:
            if type(param) != str:
                raise SnekSyntaxError("Parameters must be strings")



def parse(tokens):
    """
    Parses a list of tokens, constructing a representation where:
        * symbols are represented as Python strings
        * numbers are represented as Python ints or floats
        * S-expressions are represented as Python lists

    Arguments:
        tokens (list): a list of strings representing tokens
    
    >>> print(parse(['(', 'cat', '(', 'dog', '(', 'tomato', ')', ')',  ')']))
    ['cat', ['dog', ['tomato']]]
    
    >>> print(parse(['2']))
    2
    
    >>> print(parse(['x']))
    x
    
    >>> print(parse(['(', '+', '2', '(', '-', '5', '3', ')', '7', '8', ')']))
    ['+', 2, ['-', 5, 3], 7, 8]
    """
    
    # Check that all parentheses are matched
    if tokens.count("(") != tokens.count(")"):
        raise SnekSyntaxError
    
    # Check that tokens that have more than one element have parentheses
    if len(tokens) > 1 and (")" not in tokens or "(" not in tokens):
        raise SnekSyntaxError
    
    
    def parse_expression(index):
        '''
        Take the index and return the parsed expression that started at index
        '''       
        token = number_or_symbol(tokens[index])
               
        parsed = []
        if token == "(":
            index += 1      # do not add the opening parentheses -> skip to next index
            token = number_or_symbol(tokens[index])
            
            # while the closing ) is not hit, continue parsing through the current
            # expression
            # if not ), return the token and next_index, and append the token to parsed
            while token != ")":
                parsed_expression, index = parse_expression(index)
                
                parsed.append(parsed_expression)
                token = number_or_symbol(tokens[index])
            
            
            # Check for Snek Exceptions
            check_errors(parsed)
            
            # return the parsed token and the next index if no Exceptions occur
            return parsed, index + 1
        
        
        elif token == ")":
            # Raise SnekSyntaxError if ) comes before (
            raise SnekSyntaxError("Incorrect parentheses placement")
        
        
        # Base case: return int or float or keyword
        else:
            return token, index + 1
    
    parsed_expression, next_index = parse_expression(0)
    return parsed_expression


######################
# Built-in Functions #
######################

def multiply(args):
    product = 1
    for num in args:
        product *= num
    return product

def divide(args):
    quotient = args[0]
    for num in args[1:]:
        quotient /= num
    return quotient

snek_builtins = {
    "+": sum,
    "-": lambda args: -args[0] if len(args) == 1 else (args[0] - sum(args[1:])),
    "*": multiply,
    "/": divide,
}
    


##############
# Evaluation #
##############

'''
Initiate the builtin global environment
Everything else inherits from the builtins environment
'''
builtins = Environment()
builtins.variables = snek_builtins


def evaluate(tree, environment=None):
    """
    Evaluate the given syntax tree according to the rules of the Snek
    language.

    Arguments:
        tree (type varies): a fully parsed expression, as the output from the
                            parse function
        environment (Environment instance): default is None
    
    >>> print(evaluate('+'))
    <built-in function sum>
    
    >>> print(evaluate(3.14))
    3.14
    
    >>> evaluate(['+', 3, 7, 2])
    12
    
    >>> evaluate(['+', 3, ['-', 7, 5]])
    5
    """
    
    # Create the new global frame that inherits from builtins if environment is default None
    if environment is None:
        environment = Environment(builtins)
    
    # If the expression is a number or Func instance, it should return that value.
    if type(tree) in [int, float] or isinstance(tree, Func):
        return tree
    
    # If the expression is a symbol representing a name in snek_builtins or
    # variable bindings, it should return the associated object.
    elif type(tree) == str:        
        try:
            # try to find the variable in the current and parent environments
            return environment.get_var(tree)
        
        # if not found:
        except SnekNameError:
            
            # check first if it's a keyword
            if tree in ["lambda", "define"]:
                return tree
            
            # else:
            raise SnekNameError
    
    # List types 
    else:
        first = evaluate(tree[0], environment)
        rest = tree[1:]
        
        # If first is a built-in function
        if first in builtins.variables.values():
            operator = first
            parameters = []
            
            for elt in rest:
                parameters.append(evaluate(elt, environment))
            
            return operator(parameters)
        
        # If user is defining a variable with the define keyword
        elif first == "define":
            var = rest[0]           # EX. ['five']
            val = rest[1]           # EX. ['+', 2, 3]
            
            # If user is defining a function
            # EX. [['square', 'x'], ['*', 'x', 'x']]
            if type(var) == list:
                parameters = var[1:]        # EX. ['x']
                f_name = var[0]             # EX. ['square']
                body = val                  # EX. ['*', 'x', 'x']
                
                val = ['lambda', parameters, body]
                result = evaluate(val, environment)
                environment.set_var(f_name, result)
                return environment.get_var(f_name)
            
            # If user is defining a regular variable (ie. not a function)
            result = evaluate(val, environment)
            environment.set_var(var, result)
            return environment.get_var(var)
        
        # If user is defining a function using the lambda keyword
        # EX. ((lambda (x) (- x 8))), first = 'lambda'
        elif first == "lambda":
            parameters = rest[0]    # EX. [x]
            body = rest[1]          # EX. ['-', x, 8]]
            
            return Func(parameters, body, environment)
        
        # If user is calling a Func
        # EX. (square 2)
        elif isinstance(first, Func):
            func = first    # EX. Func associated with 'square'
            args = rest     # EX. [2]
            
            
            # check that the function has the correct number of args passed in
            if len(args) != len(func.parameters):
                raise SnekEvaluationError("Incorrect number of args passed in")
                
            
            # make a new environment whose parent is the function's enclosing environment
            new_frame = Environment(func.environment)
            
            new_args = []
            for arg in args:
                new_args.append(evaluate(arg, environment))
            
            # in that new environment, bind the function's parameters to the arguments that are passed to it.
            for i in range(len(new_args)):
                param = func.parameters[i]
                arg = new_args[i]
                
                # bind parameters with each arg in new_frame
                evaluate(["define", param, arg], new_frame)
            
            return evaluate(func.body, new_frame)
        
        else:
            raise SnekEvaluationError


def result_and_env(tree, environment=None):
    '''
    Args: tree and environment (default=None)
    Returns a tuple of two elements (result of evaluation, environment where expression is evaluated)
    '''
    # Create the new global frame if environment is default None
    if environment is None:
        environment = Environment(builtins)
    
    return evaluate(tree, environment), environment


##############
#### REPL ####
##############
def repl():
    # initiate a "global" environment that has the built-ins as its parent
    global_env = Environment(builtins)
    
    user_input = input("in> ")
    while user_input != "QUIT":
        try:
            result = evaluate(parse(tokenize(user_input)), global_env)
            print("  out>", result)
            user_input = input("in> ")
        
        # Handling Exceptions
        except SnekSyntaxError as e:
            print("SnekSyntaxError:", e)
            user_input = input("in> ")
        except SnekNameError as e:
            print("SnekNameError:", e)
            user_input = input("in> ")
        except SnekEvaluationError as e:
            print("SnekEvaluationError:", e)
            user_input = input("in> ")


if __name__ == "__main__":
    # code in this block will only be executed if lab.py is the main file being
    # run (not when this module is imported)
    
    # uncommenting the following line will run doctests from above
    #doctest.testmod()
    repl()
    
    # # Test environment variable binding
    # E1 = Environment()
    # E1.variables = {'x':3, 'y':4, 'z':5}
    # E2 = Environment(E1)
    # E2.variables = {'x':2, 'y':3}
    # E3 = Environment(E1)
    # E3.variables = {'x':7}
    # E4 = Environment(E3)
    # E4.variables = {'a':1}
    # print("E1 x=", E1.get_var('x'))
    # print("E2 x=", E2.get_var('x'))
    # print("E3 x=", E3.get_var('x'))
    # print("E4 x=", E4.get_var('x'))
    # print("E1 y=", E1.get_var('y'))
    # print("E2 y=", E2.get_var('y'))
    # print("E3 y=", E3.get_var('y'))
    
    # evaluate(parse(tokenize('(define y 8)')), E4)
    # print("E4 y=", E4.get_var('y'))
    