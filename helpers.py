import random
import string
import jinja2
import os

def load_template(template_URL):
    templateLoader = jinja2.FileSystemLoader(searchpath="/")
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template(template_URL)
    return template

def random_string(n):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))

def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        pass
