import os
import json


class TemplateMap:
    __allow_initialize = False
    __instance = None
    __template_map = {
        "html_template": {
        },
        "javascript": {
        },
        "style": {
        },
        "all_path": []
    }

    def __init__(self):
        if self.__allow_initialize:
            pass
        else:
            assert False

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__allow_initialize = True
            main_path = "ui/"
            style_path = main_path + "style"
            javascript_path = main_path + "javascript"
            style_files = [f for f in os.listdir(style_path) if os.path.isfile(os.path.join(style_path, f))]
            js_files = [f for f in os.listdir(javascript_path) if os.path.isfile(os.path.join(javascript_path, f))]
            for file in style_files:
                with open(os.path.join(style_path, file), "r") as f:
                    cls.__template_map["style"][file] = f.read()
            for file in js_files:
                with open(os.path.join(javascript_path, file), "r") as f:
                    cls.__template_map["javascript"][file] = f.read()
            cls.__template_map["all_path"] = style_files + js_files
            cls.__instance = TemplateMap()
            cls.__allow_initialize = False
        return cls.__instance

    def get_template(self, file_type, template_path):
        return self.__template_map[file_type][template_path]
        
    def list_dir(self):
        return json.dumps(self.__template_map[all_path])


if __name__ == "__main__":
    # t = TemplateMap() # it should fail
    t = TemplateMap.get_instance()
    template_data = t.get_template("js", "javascript/login.js")
    print(template_data)