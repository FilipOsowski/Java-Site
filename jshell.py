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

            for f in [in_path, out_path, snippet_path]:
                try:
                    os.remove(f)
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
        jshell_process = subprocess.Popen(f"jshell < {in_path} | tee -a fifos/log_{self.EOF_key}", shell=True, preexec_fn=os.setsid, universal_newlines=True, stdout=subprocess.PIPE)


        # This is needed so that exit() can refer to both
        # processes without using self.{process}.
        # This way, garbage collection of this jshell
        # instances works properly.
        self.dummy_input_process = dummy_input_process
        self.jshell_process = jshell_process
        self.in_path = in_path
        self.out_path = out_path
        self.snippet_path = snippet_path

        self.jshell_process.stdout.read(89)


    def kill(self):
        os.killpg(os.getpgid(self.jshell_process.pid), signal.SIGTERM)
        os.killpg(os.getpgid(self.dummy_input_process.pid), signal.SIGTERM)

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
        return self.jshell_process.stdout.read(num_bytes)


    def flush(self):
        with open(self.in_path, 'w') as java_in:
            java_in.write("\n //" + self.EOF_key + "\n")


    def run(self, code, q=None, blocking=False):
        if not blocking and q == None:
            raise Exception("If blocking=False, a queue must be passed in.")

        num_bytes = len(code.encode('utf-8'))

        self.write(code)
        self.read(num_bytes)
        self.flush()

        output = []
        x = 0
        for i, line in enumerate(self.jshell_process.stdout):
            if self.EOF_key in line:
                break
            elif i:
                output.append(line)
                x += len(line)

        if not blocking:
            q.put(output)
        else:
            return output
