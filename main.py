import sys
import json
import yaml

def load_spec(file_path):
    extension = file_path[-5:]
    if extension not in [".json", ".yaml", ".yml"]:
        print("ERROR: File of wrong format")
        exit(1)

    f = open(file_path)

    if extension == ".json":
        return json.load(f)
    else:
        return yaml.safe_load(f) 

    f.close()

def generate_route(spec, path):
    decorator = generate_decorator(spec, path)
    requests = spec["paths"][path].keys()
    print(path, requests)
    return f"@app.route(\"{path}\")"
    return 

def get_decorator(spec, path):
    methods = ", ".join([r.upper() for r in spec["paths"][path].keys()])
    return f"@app.route(\"{path}\", methods=[{methods}])"
     
def get_function_head(spec, path):
    return "head"

def get_function_body(spec, path):
    return "body"

def get_route(spec, path):
    decorator = get_decorator(spec, path)
    func_head = get_function_head(spec, path)
    func_body = get_function_body(spec, path)
    return [decorator, func_head, func_body]

if __name__ == "__main__":
    argv = sys.argv
    argc = len(argv)

    if argc != 2:
        print("ERROR: Please supply one file")
        exit(1)

    api_spec = load_spec(argv[1])

    filename =  api_spec["info"]["title"].lower().replace(" ", "_") + ".py"

    with open(filename, "w") as f:
        f.writelines([
            "from flask import Flask\n", 
            "app = Flask(__name__)\n"
            ])

        for path in api_spec["paths"]:
            f.writelines(get_route(api_spec, path))
