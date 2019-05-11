from time import sleep
from base64 import b64encode
from helpers import random_string, mkdir
import os
import string
import random
import subprocess
import atexit
import signal

# Move load_snippet
class JShell:
    in_path = None
    out_path = None
    EOF_key = None
    snippet_key = None
    fifo_key = None
    dummy_input_process = None
    jshell_process = None

    def __init__(self):
        def exit():
            os.killpg(os.getpgid(jshell_process.pid), signal.SIGTERM)
            os.killpg(os.getpgid(dummy_input_process.pid), signal.SIGTERM)

            print("removing fifos in exit")
            for f in [in_path, out_path, snippet_path]:
                try:
                    # os.remove(f)
                    pass
                except FileNotFoundError:
                    pass

        atexit.register(exit)

        mkdir("snippets")
        mkdir("fifos")

        self.EOF_key = random_string(32)
        self.snippet_key = random_string(32)
        self.fifo_key = random_string(32)
        snippet_path = "snippets/" + self.snippet_key
        in_path = "fifos/in_" + self.fifo_key
        out_path = "fifos/out_" + self.fifo_key

        for path in [in_path, out_path]:
            try:
                os.mkfifo(path)
            except FileExistsError:
                pass

        dummy_input_process = subprocess.Popen(f"(while true; do sleep 86400; done) > {in_path}", shell=True, preexec_fn=os.setsid)
        jshell_process = subprocess.Popen(f"jshell < {in_path} | tee -a fifos/log_{self.EOF_key}", shell=True, preexec_fn=os.setsid, stdout=subprocess.PIPE)


        # This is needed so that exit() can refer to both
        # processes without using self.{process}.
        # This way, garbage collection of this jshell
        # instances works properly.
        self.dummy_input_process = dummy_input_process
        self.jshell_process = jshell_process
        self.in_path = in_path
        self.out_path = out_path
        self.snippet_path = snippet_path

        with open(self.out_path) as java_out:
            java_out.read(89)

        # This breaks the JShell class
        # sleep(0.4)

        # Either one of these break the JShell class
        # self.run('/set feedback concise', blocking=True)
        # self.run('System.out.println("something");', blocking=True)

        # This causes the JShell class to work
        # sleep(1)

        # Without anything here, the JShell class
        # sometimes hangs on "ONE"


    def kill(self):
        os.killpg(os.getpgid(self.jshell_process.pid), signal.SIGTERM)
        os.killpg(os.getpgid(self.dummy_input_process.pid), signal.SIGTERM)

        print("removing fifos in kill")
        for f in [self.in_path, self.out_path, self.snippet_path]:
            try:
                os.remove(f)
            except FileNotFoundError:
                pass


    def reset():
        self.run("/reset")


    def write(self, string_):
        with open(self.in_path, 'w') as java_in:
            java_in.write(string_)


    def read(self, num_bytes):
        r = None
        print("opening...")
        with open(self.out_path) as java_out:
            print("opened!")
            r = java_out.read(num_bytes)
        return r


    def flush(self):
        with open(self.in_path, 'w') as java_in:
            java_in.write("\n //" + self.EOF_key + "\n")


    def run(self, code, q=None, blocking=False):
        if not blocking and q == None:
            raise Exception("If blocking=False, a queue must be passed in.")

        num_bytes = len(code.encode('utf-8'))


        
        self.write(code)
        print("ONE")
        print("RESULT IS", self.read(num_bytes))
        print("TWO")
        self.flush()

        output = []
        x = 0
        with open(self.out_path) as java_out:
            for i, line in enumerate(java_out):
                if self.EOF_key in line:
                    break
                elif i:
                    output.append(line)
                    x += len(line)

        if not blocking:
            # q.put(output)
            pass
        else:
            return output
