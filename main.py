import sys
import pathlib
import json
import yaml

def load_spec(file_path):
    ext = pathlib.Path(file_path).suffix
    if ext not in [".json", ".yaml", ".yml"]:
        print("ERROR: File of wrong format")
        exit(1)

    f = open(file_path)
    if ext == ".json":
        return json.load(f)
    else:
        return yaml.safe_load(f) 
    f.close()

def get_decorator(spec, path):
    methods = spec["paths"][path].keys()
    method_str = ", ".join([f"\"{m.upper()}\"" for m in methods])
    return f"@app.route(\"{path}\", methods=[{method_str}])"
     
def get_function_head(spec, path):
    components = ["root"]
    arguments = list()

    for c in path.split("/"):
        if len(c) == 0: continue

        if c[0] == "{" and c[-1] == "}":
            components.append(c[1:-1])
            arguments.append(c[1:-1])
        else:
            components.append(c)

    function_name = "_".join(components)
    argument_str = ", ".join(arguments)
    return f"def {function_name}({argument_str}):"

def get_function_body(spec, path):
    methods = [r.upper() for r in spec["paths"][path].keys()] 
    lines = list()
    for i, m in enumerate(methods):
        else_opt  = "" if i == 0 else "el"
        lines.append(f"\t{else_opt}if request.method == \"{m}\":\n")
        lines.append("\t\tpass\n")

    return lines

if __name__ == "__main__":
    argv = sys.argv
    argc = len(argv)

    if argc != 2:
        print("ERROR: Please supply one file")
        exit(1)

    api_spec = load_spec(argv[1])

    filename =  api_spec["info"]["title"].lower().replace(" ", "_") + ".py"

    with open(filename, "w") as f:
        f.write("from flask import Flask\n")
        f.write("\n")
        f.write("app = Flask(__name__)\n")
        f.write("\n")

        for path in api_spec["paths"]:
            decorator = get_decorator(api_spec, path)
            function_head = get_function_head(api_spec, path)
            function_body = get_function_body(api_spec, path)

            f.write(decorator + "\n")
            f.write(function_head + "\n")
            f.writelines(function_body)
            f.write("\n")
