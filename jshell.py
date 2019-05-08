from time import sleep
from base64 import b64encode
import os
import subprocess
import atexit
import signal

def cleanup():
    jshell.kill()

atexit.register(cleanup)

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
        def random_string(n):
            bytes_ = os.urandom(n)
            string = b64encode(bytes_).decode('utf-8')
            return string

        self.EOF_key = random_string(32)
        self.snippet_key = random_string(32)
        self.fifo_key = random_string(32)
        self.snippet_path = "./snippets/" + self.snippet_key
        self.in_path = "./fifos/" + self.fifo_key + "_in"
        self.out_path = "./fifos/" + self.fifo_key + "_out"

        for path in [self.in_path, self.out_path]:
            try:
                os.mkfifo(path)
            except FileExistsError:
                pass

        self.dummy_input_process = subprocess.Popen("(while true; do sleep 86400; done) > in", shell=True, preexec_fn=os.setsid)
        self.jshell_process = subprocess.Popen("jshell < in > out", shell=True, cwd=".", preexec_fn=os.setsid)

        with open(self.out_path) as java_out:
            java_out.read(89)

        self.run("/set feedback concise")

    
    def kill(self):
        os.killpg(os.getpgid(jshell.jshell_process.pid), signal.SIGTERM)
        os.killpg(os.getpgid(jshell.dummy_input_process.pid), signal.SIGTERM)

        for f in [self.in_path, self.out_path, self.snippet_path]:
            try:
                os.remove(f)
            except FileNotFoundError:
                pass


    def write(self, string):
        with open(self.in_path, 'w') as java_in:
            java_in.write(string)


    def read(self, num_bytes):
        r = None
        with open(self.out_path) as java_out:
            r = java_out.read(num_bytes)

        return r


    def flush(self):
        with open(self.in_path, 'w') as java_in:
            java_in.write("\n //" + self.EOF_key + "\n")


    def run(self, code, q):
        num_bytes = len(code.encode('utf-8'))
        self.write(code)
        self.read(num_bytes)
        self.flush()

        output = []
        with open(self.out_path) as java_out:
            for i, line in enumerate(java_out):
                # print("LINE", repr(line))
                if self.EOF_key in line:
                    break
                elif i:
                    output.append(line)


        q.put(output)
