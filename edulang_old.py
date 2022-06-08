from enum import Enum

#Error types
class Error(Enum):
    SYNTAX = "syntax"

#Reads commands from a file into a dictionary of line numbers and commands (to throw errors)
def get_commands(file):
    with open(file,"r") as f:
        commands = f.read().splitlines()
    line_numbers = list(range(len(commands)))
    line_numbers.append(line_numbers[-1]+1)
    line_numbers.pop(0)

    command_list = {i:j for i,j in zip(line_numbers,commands) if len(j) != 0 and len(list(set(j))) != 1 and j.strip()[0] != "#"}
    return command_list

class Interpreter:
    def __init__(self):
        self.memory = [] #"ram" of the program

        self.variables = {} #dict of vars and mem addressess
        self.alloc_var = 0 #where to alloc
        self.functions = {} #dict of functions and code

        self.keywords = ["var","int","char","list","if","=","==","!=",">","<",">=","<=","for","while","return","import","def","class"]
        self.math_keywords = ["=","==","!=",">","<",">=","<=","*","/","+","-",",","~","^","!"]
    
    #throw error
    def throw(self,error_type,line,command):
        print("### ERROR ###")
        print("LINE",str(line) + " ->",str(error_type) + ": " + command)
    
    #resolves list_index to memory location
    def resolve(self,list_index):
        if "[" in list_index:
            temp = list_index.split("[")
            start = temp[0]
            offset = list_index.split(start)[1][1:-1]
            start = self.variables[start]["addr"]
            addr = start + self.resolve(offset)
            set_type = int
            if type(start) is str:
                set_type = float
                if self.variables[start]["type"] in ["int","char"]:
                    set_type = int
            if addr >= len(self.memory):
                return set_type(0)
            return set_type(self.memory[addr])
        else:
            if list_index.isnumeric():
                return int(list_index)
            else:
                return self.variables[list_index]["addr"]
    
    #Execute a dict of commands, with local vars
    def execute(self,commands,local_vars=[]):
        for nline in commands:
            command = commands[nline]
            if command.startswith("var"):
                splitted = command.split()
                if len(splitted) < 3 or len(splitted) == 4:
                    self.throw(Error.SYNTAX,nline,command);break
                if splitted[1] in ["int","float","char"]:
                    var_type = splitted[1]
                else:
                    self.throw(Error.SYNTAX,nline,command);break
                var_name = splitted[2]
                if var_name in self.keywords:
                    self.throw(Error.SYNTAX,nline,command);break
                var_val = 0
                if len(splitted) > 3:
                    if splitted[3] != "=":
                        self.throw(Error.SYNTAX,nline,command);break
                    val = "".join(splitted[4:])
                    temp_val = val[:]
                    for keyword in self.math_keywords:
                        temp_val = temp_val.replace(keyword," ")
                    vars_needed = [i.strip("()") for i in temp_val.split() if not i.isnumeric()]
                    val = "__out__=" + val
                    do_break = False
                    local_vars = {}
                    temp_name = 0
                    for i in vars_needed:
                        if i in self.keywords:
                            self.throw(Error.SYNTAX,nline,command);do_break=True
                        elif i in self.variables:
                            local_vars[i] = self.memory[self.variables[i]["addr"]]
                        elif "[" in i:
                            new_name = "__temp" + str(temp_name) + "__"
                            val = val.replace(i,new_name)
                            try:
                                local_vars[new_name] = self.resolve(i)
                            except:
                                self.throw(Error.SYNTAX,nline,command);do_break=True
                        else:
                            self.throw(Error.SYNTAX,nline,command);do_break=True
                    if do_break:
                        break
                    exec(val,{},local_vars)
                    var_val = local_vars["__out__"]
                var_addr = len(self.memory)
                if var_type == "int":
                    self.memory.append(int(var_val))
                elif var_type == "float":
                    self.memory.append(float(var_val))
                elif var_type == "char":
                    var_val = int(var_val)
                    if var_val > 255:
                        self.throw(Error.SYNTAX,nline,command);break
                    self.memory.append(var_val)
                self.variables[var_name] = {"type":var_type,"addr":var_addr}

            elif command.startswith("list"):
                splitted = command.split()
                if len(splitted) < 3 or len(splitted) == 4:
                    self.throw(Error.SYNTAX,nline,command);break
                if "[" not in splitted[1]:
                    self.throw(Error.SYNTAX,nline,command);break
                var_name = splitted[2]
                if var_name in self.keywords:
                    self.throw(Error.SYNTAX,nline,command);break
                var_type = splitted[1].split("[")[0]
                len_list = splitted[1].split(var_type)[1][1:-1]
                if not var_type in ["int","float","char"]:
                    self.throw(Error.SYNTAX,nline,command);break
                if len_list.isnumeric():
                    len_list = int(len_list)
                else:
                    if "[" in len_list:
                        len_list = self.resolve(len_list)
                    else:
                        if len_list in self.variables:
                            len_list = self.memory[self.variables[len_list]["addr"]]
                vals = [0] * len_list
                if len(splitted) > 3:
                    if splitted[3] != "=":
                        self.throw(Error.SYNTAX,nline,command);break
                    vals = command.split(" = ")[1][1:-1]
                    vals = [i.strip() for i in vals.split(",")]
                    if '"' in vals[0] or "'" in vals[0]:
                        if var_type == "char":
                            vals = [ord(i[1:-1]) for i in vals]
                        else:
                            self.throw(Error.SYNTAX,nline,command);break
                    if var_type == "int" or var_type == "char":
                        vals = [int(i) for i in vals]
                    if var_type == "float":
                        vals = [float(i) for i in vals]
                if len(vals) != len_list:
                    self.throw(Error.SYNTAX,nline,command);break
                var_addr = len(self.memory)
                self.memory.append(var_addr+1)
                for i in range(len_list):
                    self.memory.append(vals[i])
                self.variables[var_name] = {"type":var_type,"addr":var_addr}

            elif command.split()[1] == "=":
                pass

commands = get_commands("example.elpl")
inter = Interpreter()
inter.execute(commands)
print(inter.memory)
print(inter.variables)
