from jshell import JShell
import sys
import importlib.util
import json
import jinja2

problem_URL = "/home/filip/image/2004/1/a/"
num_test_cases = 100
arg_generator = []
jshell = JShell()
setup_ended_key = "//``SETUP ENDED``" 

def load_template(template_URL):
    templateLoader = jinja2.FileSystemLoader(searchpath="/")
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template(template_URL)
    return template


def get_arg_generators(arg_generator_directory_URL):
    from inspect import getmembers, isfunction

    # Need to add new path to locate & import arg_generators
    sys.path.append(arg_generator_directory_URL)
    import arg_generators

    # functions are sorted by alphabetical order, meaning
    # functions _2, _3, _1 will be automatically sorted to
    # _1, _2, _3.
    functions_list = [o[1] for o in getmembers(arg_generators) if isfunction(o[1])]

    return functions_list


def create_test_cases(problem_URL):
    test_cases = []
    solution = None
    with open(problem_URL + "solution.java") as s:
        solution = s.read()

    jshell.run(solution, blocking=True)

    test_case_template = load_template(problem_URL + "test_case_template.java")
    test_case_args = []
    arg_generators = get_arg_generators(problem_URL)

    for _ in range(num_test_cases):
        template_args = {}
        for i, arg_generator in enumerate(arg_generators):
            template_args[str(i)] = arg_generator()

        input_ = test_case_template.render(template_args)

        output = []
        setup_ended = False

        for line in input_:
            if setup_ended_key in line:
                setup_ended = True

            if setup_ended:
                output.append(o)

        test_cases.append({"input": input_, "output": output})

    with open(problem_URL + "test_cases.json", "w") as test_case_file:
        json.dump(test_cases, test_case_file)

create_test_cases(problem_URL)
