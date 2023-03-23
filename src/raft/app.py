class Application:
    def __init__(self):
        self.dict = {}

    def execute(self, command):
        command = command.split()
        print(command)
        type = command[0]
        key = command[1]
        value = command[2]
        if type == "add":
            print("add item")
            if key not in self.dict:
                self.dict[key] = {value}
            else:
                self.dict[key].add(value)
        elif type == "delete":
            print("delete item")
            if key in self.dict:
                if len(self.dict[key]) == 1:
                    self.dict.pop(key)
                else:
                    self.dict[key].remove(value)
        