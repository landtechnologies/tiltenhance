import yaml
import urllib.request
import textwrap
import os
import subprocess
import os.path
import json

### Tilt Shims
def local(cmd):
  result = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True, check=True)
  return result.stdout.decode('UTF-8')

def decode_yaml_stream(yaml_str):
  ret = [obj for obj in yaml.safe_load_all(yaml_str)]
  return ret

def encode_yaml_stream(objs):
  return yaml.dump_all(objs)

def k8s_yaml(*args, **kwargs):
  pass

def k8s_resource(*args, **kwargs):
  pass

def fail(reason):
  print("Real fail")
  raise Exception(f"Tiltfile failed: {reason}")

def read_json(path, default=None):
  if os.path.isfile(path):
    with open(path, "r") as f:
      return json.loads(f.read())
  else:
    if default is not None:
      return default
    else:
      return IOError(f"File at {path} doesn't exist")

def encode_json(obj):
  return json.dumps(obj)

def encode_yaml(obj):
  return yaml.dump(obj)

def load(tiltfile_path, *functions):
  old_tiltfile_dir = globals().get('current_tiltfile_dir')
  tiltfile_contents = ""
  resolved_path = "./"
  if "ext://" in tiltfile_path:
    package_name = tiltfile_path.replace("ext://", "")
    url = f"https://raw.githubusercontent.com/tilt-dev/tilt-extensions/master/{package_name}/Tiltfile"
    with urllib.request.urlopen(url) as f:
      tiltfile_contents = f.read().decode('utf-8')
  else:
    resolved_path = os.path.join(old_tiltfile_dir, tiltfile_path)
    with open(resolved_path, "r") as f:
      tiltfile_contents = f.read()

  globals_str = '\n'.join([f"global {function}" for function in functions])
  globals()['current_tiltfile_dir'] = os.path.dirname(resolved_path)
  exec(f"""
def runner():
{textwrap.indent(globals_str, "  ")}
{textwrap.indent(tiltfile_contents, "  ")}
runner()
""")

  globals()['current_tiltfile_dir'] = old_tiltfile_dir

### Tilt Shims End

class TiltConfig(object):
  def __init__(self, tilt_subcommand='up', args={}):
    self.tilt_subcommand = tilt_subcommand
    self.args = args
  
  def define_bool(self, arg):
    pass 

  def parse(self):
    return self.args


def run_tiltfile_func(tiltfile_path, function_name, mocks={}, **func_args):
  with open(tiltfile_path, "r") as f:
    globals_before = dict(globals())
    
    merged_mocks = {
      'config': TiltConfig(),
      **mocks
    }
    for mock_name,mock_val in merged_mocks.items():
      globals()[mock_name] = mock_val

    globals()['current_tiltfile_dir'] = os.path.dirname(tiltfile_path)

    code = f"""
def runner(**args):
{textwrap.indent(f.read(), "  ")}

  return {function_name}(**args)
global __return_value
__return_value = runner(**func_args)"""

    exec(code)

    return_val = globals().get('__return_value')

    extra_global_keys = set(globals().keys()) - set(globals_before.keys())

    for key in extra_global_keys:
      del globals()[key]

    for key,val in globals_before.items():
      globals()[key] = val

    return return_val