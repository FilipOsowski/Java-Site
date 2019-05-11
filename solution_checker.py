from jshell import JShell
from helpers import load_template, random_string
from queue import Empty
from threading import Thread
from error import Error
import multiprocessing
import json

# HERE: Check class by writing the solution to the test cases in 2004/1/a and use check_solution to see if it works correctly
class LoadingFailure(Exception):
    def __init__(self, message, errors):
        super().__init__(message)

class SolutionChecker:
    jshell = None
    snippet_key = None
    setup_ended_key = "//``SETUP ENDED``"
    busy = True

    def __init__(self):
        self.snippet_key = random_string(32)
        self.restart()


    def restart(self):
        self.busy = True
        self.jshell = JShell()
        self.busy = False


    # Check to see if `code` is a correct solution
    # for the problem located at `q_URL`. Return "correct"
    # if the solution is correct, else return an error.
    def check_solution(self, q_URL, code):
        working_dir = "/home/filip/image" + q_URL
        solution_template = load_template(working_dir + "solutio_template.java")
        user_solution = template.render(code=code)

        # JShell's /open either fails silently or omits
        # important errors. The class_name is needed to
        # further test the user's code for errors.
        class_name = user_solution.split()[2]
        
        snippet_URL = "snippets/" + self.snippet_key
        with open(snippet_URL, "w") as user_solution_file:
            user_solution_file.write(user_solution)

        error = None
        try:
            load_snippet(snippet_URL, class_name)
            error = run_test_cases(working_dir + "test_cases.json")
        except LoadingFailure:
            error = get_compiler_error(snippet_URL)

        jshell.reset()

        if error:
            return error.json()
        else:
            return "correct"

    # Load snippet into JShell environment. Raises a
    # LoadingFailure error if the snippet was unable
    # to be loaded.
    def load_snippet(self, snippet_URL, class_name):
        loaded_snippets_before = self.jshell.run("/list")
        errors = jshell.run("/load " + snippet_URL)
        loaded_snippets_after = self.jshell.run("/list")

        # Because /open ignores some errors, the loaded
        # snippet must be initialized to check for
        # any additional errors.
        errors = jshell.run("new " + class_name + "()")

        if loaded_snippets_before == loaded_snippets_after or not errors:
            raise LoadingFailure(f"Failed to load {snippet_URL}")

    # Returns the first error produced by javac when 
    # compiling the snippet located by `snippet_URL`.
    # This method is only called after a snippet is unable
    # to be loaded into the JShell env and therefore
    # must contain an error.
    def get_compile_error(self, snippet_URL):
        p = subprocess(["javac", snippet_URL], stdout=subprocess.PIPE)
        error_text = p.stdout.read()
        error = Error()

        start = False
        for line in error_text:
            if snippet_key in line:
                if start:
                    break
                else:
                    start = True
            else:
                error.text.append(line)

        return error

    # Runs the test_case["input"] part of test_cases.json 
    # and checks to see if the resulting output matches 
    # that expected by test_case["output"].
    # Returns the first error found while running test cases
    # (an actual error thrown by the code or a failed test
    # case), else returns None.
    def run_test_cases(self, test_cases_URL):
        test_cases = None
        with open(test_cases_URL) as test_cases_json:
            test_cases = json.load(test_cases_json)

        for test_case in test_cases:
            error = Error()
            setup_ended = False

            for line in test_case["input"]:
                q = multiprocessing.Queue()
                run_line = multiprocessing.Process(target=self.jshell.run, args=((line), (q)))
                run_line.start()

                try:
                    o = q.get(timeout=100)
                    error.history.append(line)

                    if self.setup_ended_key in line:
                        setup_ended = True

                    # get_first_error will return None
                    # if there is no error in the output,
                    # else, it will return the error.
                    error_text = self.get_first_error(o)

                    # If there is already an error thrown
                    # by the user's code, there is not point
                    # in checking if the code's output
                    # is correct.
                    if setup_ended and not error_text:
                        correct_output = test_case["output"].pop(0)

                        if correct_output != o:
                            error.correct_output = correct_output
                        else:
                            error.history.append(o)
                    
                    if error.text or error.correct_output:
                        return error

                except Empty:
                    error = Error()
                    error.text = "Timeout error"
                    self.nonblocking_restart()
                    return error
        return None

    # Create a new JShell instance without blocking the
    # calling thread. This is necessary to not block the
    # server should a JShell instance get stuck on some code.
    def nonblocking_restart(self):
        self.jshell.kill()
        restart_thread = Thread(target=self.restart)
        restart_thread.start()

    # Returns the first error found in output, else [].
    def get_first_error(self, output):
        error_text = []
        error_start = False
        for line in output:
            if "|  Error:" in line:
                error_start = not error_start

            if error_start:
                error_text.append(line)

        return error_text

SolutionChecker().run_test_cases('/home/filip/image/2004/1/a/test_cases.json')
