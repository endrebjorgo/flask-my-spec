import sys
import pathlib
import json
import yaml

REQS = ["get", "head", "post", "put", "delete", 
        "connect", "options", "trace", "patch"]

def load_spec(file_path):
    ext = pathlib.Path(file_path).suffix
    if ext not in [".json", ".yaml", ".yml"]:
        print("ERROR: File of wrong format", file=sys.stderr)
        exit(1)

    with open(file_path) as f:
        if ext == ".json":
            return json.load(f)
        else:
            return yaml.safe_load(f) 

def expand_spec_refs(spec, *args):
    ref_found = True

    while ref_found: # Gotta check if this is necessary
        ref_found = False
        curr = spec
        for arg in args:
            curr = curr[arg]

        if isinstance(curr, dict):
            keys = curr.keys()
        else:
            keys = range(len(curr))

        for key in keys:
            if key == "$ref":
                ref_found = True
                new_ref = get_value_at_ref(spec, curr.copy()["$ref"])
                set_ref(spec, new_ref, *args)
                continue
            elif not isinstance(curr[key], (dict, list)):
                continue

            expand_spec_refs(spec, *args, key)

def set_ref(spec, new_val, *args):
    curr = spec 

    for arg in args[:-1]:
        curr = curr[arg]

    curr[args[-1]] = new_val

def get_value_at_ref(spec, ref):
    path = ref.split("/")[1:]
    curr = spec
    for key in path:
        curr = curr[key]
    return curr

def generate_filename(api_spec):
    title = api_spec["info"]["title"]
    return title.lower().replace(" ", "_") + ".py"

def write_header():
    f.write("from flask import Flask, Response, request\n")
    f.write("\n")
    f.write("app = Flask(__name__)\n")
    f.write("\n")

def write_body(f, spec):
    for path in spec["paths"]:
        write_decorator(f, spec, path)
        write_func_def(f, spec, path)
        write_func_body(f, spec, path)

def write_decorator(f, spec, path):
    path_children = spec["paths"][path].keys()
    http_methods = [r for r in path_children if r in REQS]
    method_str = ", ".join([f'"{m.upper()}"' for m in http_methods])
    new_path = path.replace("{", "<").replace("}", ">")
    f.write(f"@app.route(\"{new_path}\", methods=[{method_str}])\n")

def write_func_def(f, spec, path):
    strs = ["root"]
    param_list = list()

    for s in path.split("/"):
        if len(s) == 0: continue

        if s[0] == "{" and s[-1] == "}":
            strs.append(s[1:-1])
            param_list.append(s[1:-1])
        else:
            strs.append(s)

    function_name = "_".join(strs)
    param_list_str = ", ".join(param_list)
    f.write(f"def {function_name}({param_list_str}):\n")

def write_func_body(f, spec, path):
    path_children = spec["paths"][path].keys()
    http_methods = [r.upper() for r in path_children if r in REQS]
    for i, m in enumerate(http_methods):
        else_opt  = "" if i == 0 else "el"
        f.write(f'\t{else_opt}if request.method == "{m}":\n')
        response = generate_response(spec, path, m)
        f.write(f"\t\treturn {response}\n")
    f.write(f"\telse:\n")
    f.write("\t\tpass\n\n")

def generate_response(spec, path, http_method):
    http_method = http_method.lower()
    responses = spec["paths"][path][http_method]["responses"]

    schema = responses["200"]["content"]["application/json"]["schema"]
    return schema

    return 'Response(response={"foo": "bar"}, status=200)'

if __name__ == "__main__":
    argv = sys.argv
    argc = len(argv)

    if argc != 2:
        print("ERROR: Please supply one file", file=sys.stderr)
        exit(1)

    api_spec = load_spec(argv[1])
    expand_spec_refs(api_spec)

    filename = generate_filename(api_spec) 
    
    f = open(filename, "w")

    write_header()
    write_body(f, api_spec) 
    
    f.close()
