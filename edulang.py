from enum import Enum

#Error types
class Error(Enum):
    SYNTAX = "syntax"
    TYPE = "type"
    CATASTROPHIC = "catastrophic"

def get_commands(file):
    #read raw from file
    with open(file,"r") as f:
        commands = f.read().splitlines()

    #generate line numbers
    line_numbers = list(range(len(commands)))

    #adjust line numbers so they start with 1 and not 0
    line_numbers.append(line_numbers[-1]+1) 
    line_numbers.pop(0)

    #Load line numbers and commands into a dict
    command_list = {i:j for i,j in zip(line_numbers,commands) if len(j) != 0 and len(list(set(j))) != 1 and j.strip()[0] != "#"}

    #return the dict
    return command_list

class Env:
    def __init__(self,memory_size = "inf"):
        self.memory_size = memory_size #size of memory
        self.memory = [] #"ram"
        self.variables = {} #dict of names to addresses
        self.var_types = {}
        self.halt = False
        self.keywords = ["var","int","char","list","if","=","==","!=",">","<",">=","<=","for","while","return","import","def","class"] #keywords
        self.math_keywords = ["=","==","!=",">","<",">=","<=","*","/","+","-",",","~","^","!"] #math keywords

    def throw(self,error_type,line,command):
        print("### ERROR ###")
        print("LINE",str(line) + " ->",str(error_type) + ": " + command)
        self.halt = True

    def resolve(self,address):
        #takes in any address, and resolves it.
        try:
            address = int(address)
        except:
            pass
        if isinstance(address,int):
            return address
        try:
            return float(address)
        except:
            pass
        if "[" in address:
            addr = address.split("[")[0]
            offset = address.split(addr)[1][1:-1]
            return self.variables[addr] + self.resolve(offset)
        else:
            return self.memory[self.variables[address]]
    
    def resolve_value(self,value):
        #get keywords in order:
        keywords = []
        for letter in value:
            if letter in self.math_keywords:
                keywords.append(letter)
        keywords.append("")

        #split the value into the different elements
        for keyword in self.math_keywords:
            value = value.replace(keyword,",")
        value_split = value.split(",")

        #for each of these elements, figure out they're actual value
        for idx in range(len(value_split)):
            if "[" in value_split[idx]:
                value_split[idx] = self.memory[self.resolve(value_split[idx])]
            else:
                value_split[idx] = self.resolve(value_split[idx])
        
        out_val = "__out__="
        for i,j in zip(value_split,keywords):
            out_val += (str(i) + str(j))
        local_vars = {}
        exec(out_val,{},local_vars)
        return local_vars["__out__"]
    
    def execute(self,commands):
        #set halt to False
        self.halt = False
        for line in commands.keys():

            #if error thrown, then return False
            if self.halt:
                return False

            #get command from line number
            command = commands[line]

            #do different things
            if command.startswith("#"):
                pass
            elif command.startswith("var"):
                self.alloc_var(line,command)
            elif command.startswith("list"):
                self.alloc_list(line,command)
            else:
                command_split = command.split(" ")
                if command_split[1] == "=":
                    self.assign(line,command)
        
        #return true if executed successfully
        return True
    
    def assign(self,line,command):
        command_split = command.split(" ")
        if not command_split[1] == "=":
            self.throw(Error.CATASTROPHIC,line,command)
        
    
    def alloc_list(self,line,command):
        #check that we actually are allocing a var
        if not command.startswith("list"):
            self.throw(Error.CATASTROPHIC,line,command)
        
        #split the command up into its separate parts (We need a space both sides of the equals)
        command_split = command.split(" ")[1:]

        #check the command is either just int [varname] or int [varname] = [value]
        if not (len(command_split) == 2 or len(command_split) > 3):
            self.throw(Error.SYNTAX,line,command)
        
        #if command has assignment (i.e. longer than int a = , then check if middle is equals)
        if len(command_split) > 3:
            if not command_split[2] == "=":
                self.throw(Error.SYNTAX,line,command)
        
        #check the type has a length
        var_type = command_split[0]
        if not ("[" in var_type and var_type[-1] == "]"):
            self.throw(Error.SYNTAX,line,command)

        #resolve the type and length
        temp = var_type.split("[")[0]
        var_length = "".join(var_type.split(temp)[1])[1:-1]
        if "[" in var_length:
            var_length = self.memory(self.resolve(var_length))
        else:
            var_length = self.resolve(var_length)
        var_type = temp

        #sanitize type
        if not var_type in ["int","float","char"]:
            self.throw(Error.SYNTAX,line,command)
        
        var_name = command_split[1]
        if var_name in self.keywords:
            self.throw(Error.SYNTAX,line,command)
        
        #get values
        var_value = [0] * var_length
        if len(command_split) > 3:
            var_value = "".join(command_split[3:])
        if (var_value[0] == '"' and var_value[-1] == '"') or (var_value[0] == "'" and var_value[-1] == "'"):
            var_value = [ord(i) for i in var_value[1:-1]]
        elif var_value[0] == "[" and var_value[-1] == "]":
            var_value = var_value[1:-1].split(",")
            for idx in range(len(var_value)):
                if (var_value[idx][0] == "'" and var_value[idx][-1] == "'") or (var_value[idx][0] == '"' and var_value[idx][-1] == '"'):
                    var_value[idx] = ord(var_value[idx][1:-1])
                else:
                    if "[" in var_value[idx]:
                        var_value[idx] = self.memory[self.resolve(var_value[idx])]
                    else:
                        var_value[idx] = self.resolve(var_value[idx])
        else:
            self.throw(Error.SYNTAX,line,command)
        
        if len(var_value) != var_length:
            self.throw(Error.SYNTAX,line,command)
        
        #add to memory and save address
        var_addr = len(self.memory)
        self.var_types[var_name] = var_type
        self.memory += var_value
        self.variables[var_name] = var_addr

    def alloc_var(self,line,command):
        #check that we actually are allocing a var
        if not command.startswith("var"):
            self.throw(Error.CATASTROPHIC,line,command)

        #split the command up into its separate parts (We need a space both sides of the equals)
        command_split = command.split(" ")[1:]

        #check the command is either just int [varname] or int [varname] = [value]
        if not (len(command_split) == 2 or len(command_split) > 3):
            self.throw(Error.SYNTAX,line,command)
        
        #if command has assignment (i.e. longer than int a = , then check if middle is equals)
        if len(command_split) > 3:
            if not command_split[2] == "=":
                self.throw(Error.SYNTAX,line,command)
        
        #separate the split commands into type, name and value
        var_type = command_split[0]
        var_name = command_split[1]
        var_value = 0
        if len(command_split) > 3:
            var_value = "".join(command_split[3:])
        var_value = self.resolve_value(var_value)

        #check that the type and name are all valid
        if not var_type in ["int","char","float"]:
            self.throw(Error.SYNTAX,line,command)
        if var_name in self.keywords:
            self.throw(Error.SYNTAX,line,command)
        
        var_addr = len(self.memory)
        if var_type == "int":
            self.memory.append(int(var_value))
        elif var_type == "float":
            self.memory.append(float(var_value))
        elif var_type == "char":
            var_value = int(var_value)
            if var_value <= 255:
                self.memory.append(var_value)
            else:
                self.memory.append(0)
        self.variables[var_name] = var_addr
        self.var_types[var_name] = var_type
        

env = Env()
commands = get_commands("example.elpl")
env.execute(commands)
print(env.memory)