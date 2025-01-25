from error import SemanticError

class CodeGenerator:
    def __init__(self, parser, scanner):
        self.parser = parser
        self.scanner = scanner
        self.semanticErrorMessage = SemanticError(parser, scanner)
        
        self.codes_generated = {
            0: ("ASSIGN", "#4", 0, None),
        }  
        self.semantic_stack = list()
        self.scope_stack = [
            {
                "global": {
                    "addr": 0,
                    "type": "void",
                    "params": [],
                }
            }
        ]
        self.break_stack = list()
        self.address_scope_stack = []
        self.stack_pointer = 0
        self.break_scope = list()

        self.temp_pointer = 500
        self.program_line = len(self.codes_generated)
        self.return_address = 104

        self.state_saved = []
        self.waiting_function_jumps = {}
        self.address_type_mapping = {}
        self.calls = []
        
        self.jumped_to_main = False
        self.in_loop = False
        self.skip_line = None
        self.jpf_line = 0
        self.is_output = False
        self.is_arg = False
        self.start_param = False
        self.is_arithmetic = False
        self.arg_changed = False
        self.is_compare = False
        self.add_check = False
    
        self.current_function_name = None
        self.current_function_type = None
        self.check_function_params = [[]]
        self.last_id = None
        self.last_num = None
        self.last_type = None

        self.func_param_size = 0

    def add_code_line(self, code):
        self.codes_generated[int(self.program_line)] = code
        self.program_line += 1

    def store_code_line(self, code, line):
        if isinstance(line, str):
            if line.startswith("#") or line.startswith("@"):
                line = line[1:]
        self.codes_generated[int(line)] = code 

    def is_func(self, id):
        for func in self.scope_stack:
            for key in func.keys():
                if key == id:
                    return True
        return False

    def get_var_scope(self, var, func, func_num) -> int:
        i = 0
        for scope in self.scope_stack[func_num][func]["params"]:
            if var == scope["id"]:
                return i, scope["addr"], scope["line"]
            i += 1
        return -1, None, None

    def get_var_type(self, var, func, func_num) -> int:
        i = 0
        for scope in self.scope_stack[func_num][func]["params"]:
            if var == scope["id"]:
                return scope["type"]
            i += 1
        return None
    
    def get_func_scope(self, var) -> int:
        for i, scope in reversed(list(enumerate(self.scope_stack))):
            if var in scope:
                return i, scope[var]["addr"], scope[var].get("line", None)
        return -1, None, None

    def get_temp(self, len=1, size=4):
        address = int(self.temp_pointer)
        if len == 1:
            self.temp_pointer += len * size
            self.address_type_mapping[address] = "int"
            self.address_scope_stack[-1].append(address)
        else:
            self.temp_pointer += (len) * size
            self.address_type_mapping[address] = "array"
            self.address_scope_stack[-1].append(address)
            for i in range(1, len):
                self.address_scope_stack[-1].append(address + i * size)
                self.address_type_mapping[address + i * size] = "int"
        return address

    def p_id(self, id):
        if self.last_type is not None:
                self.semantic_stack.append(id)
                return
        if self.current_function_name is not None:
            if not self.is_func(id):
                fn, _, _ = self.get_func_scope(self.current_function_name)
                scope, address, line = self.get_var_scope(id, self.current_function_name, fn)
                if scope == -1:
                    scope, address, line = self.get_var_scope(id, "global", 0)
            else:
                scope, address, line = self.get_func_scope(id)
                self.calls.append(id)
            if self.is_arg:
                    self.check_function_params[-1].append(id)
            if scope == -1:
                if id != "output":
                        self.semantic_stack.append("error")
                        self.semanticErrorMessage.scoping(id)
                        return
                else:
                    self.calls.append(id)
            if id != "output":
                    self.semantic_stack.append(str(address))
                    
    def p_num(self, num):
        self.semantic_stack.append("#" + str(num))
        if self.is_arg:  
            if len(self.calls) > 0:   
                if self.calls[-1] != "output":
                    self.check_function_params[-1].append("#" + str(num))

    def add(self):
        self.semantic_stack.append("ADD")

    def sub(self):
        self.semantic_stack.append("SUB")

    def mult(self):
        self.semantic_stack.append("MULT")

    def eq(self):
        self.semantic_stack.append("EQ")
        self.is_compare = True

    def lt(self):
        self.semantic_stack.append("LT")
        self.is_compare = True
    

    def arithmetic(self):
        if not self.is_compare:
            print(self.semantic_stack)
            right = self.semantic_stack.pop()
            op = self.semantic_stack.pop()
            left = self.semantic_stack.pop()
            result = self.get_temp()
               
            # right_type = self.get_type(right)
            # left_type = self.get_type(left)
            # print("type", left, right, left_type, right_type)
            # if left_type != "error" and right_type != "error" and left_type != "func" and right_type != "func":
            #     if self.semanticErrorMessage.type_mismatch(left_type, right_type):
            #         return
                
            if self.is_arg:
                self.arg_changed = True
                
                if self.add_check:
                    print("hiiii")
                    # self.check_function_params.append([right])
                    self.add_check = False
                    self.check_function_params.pop()
                    self.check_function_params.append([result])
                    self.check_function_params[-1].append(left)
                    print(self.check_function_params)
                else:
                    self.check_function_params.pop()
                    self.check_function_params.append([result])
                    print(self.check_function_params)
                # print(result)
                
                
            if op =="MULT":
                self.add_code_line((op, right,left,  result ))
            else:
                self.add_code_line((op, left, right, result ))
            self.semantic_stack.append(result)
        self.is_compare = False
    
    def compare(self):
        right = self.semantic_stack.pop()
        op = self.semantic_stack.pop()
        left = self.semantic_stack.pop()
        result = self.get_temp()
        self.add_code_line((op, left, right, result ))
        # self.is_compare = True
        self.semantic_stack.append(result)

    def get_type(self, address):
        address = str(address)
        if address.startswith("@"):
            address = address[1:]
        if address.startswith("#"):
            return "int"
        elif address == "error":
            return "error"
        elif self.get_func_name(address) is not None:
            return "func"
        else:
            return self.address_type_mapping[int(address)]
                # return self.get_var_type(address, self.current_function_name, self.get_func_scope(self.current_function_name)[0])
    
    def get_func_name(self, address):
        for func in self.scope_stack:
            for key in func.keys():
                if int(func[key]["addr"]) == int(address):
                    return address
        return None
    
    def arg(self):
        self.add_check = True

    def assign(self):
        right = self.semantic_stack.pop()
        left = self.semantic_stack.pop()
        right_type = self.get_type(right)
        left_type = self.get_type(left)
        print("type s", left, right, left_type, right_type)
        if left_type != "error" and right_type != "error" and left_type != "func" and right_type != "func":
            if self.semanticErrorMessage.type_mismatch(left_type, right_type):
                return
        self.add_code_line(("ASSIGN", right, left, None))
        self.semantic_stack.append(left)

    def label(self):
        self.semantic_stack.append(self.program_line)
        self.break_scope.append(len(self.scope_stack))

    def save(self):
        self.label()
        self.program_line += 1

    def jp(self):
        print(self.semantic_stack)
        code_line = self.semantic_stack.pop()
        if isinstance(code_line, str):
            if code_line.startswith("#") or code_line.startswith("@"):
                code_line = code_line[1:]
        if code_line == "error" or int(code_line) > 500 :
            code_line = self.semantic_stack.pop()
        self.store_code_line(("JP", self.program_line , None, None), code_line)
    
    def jp_break(self):
        if len(self.break_stack)> 0:
            for i, (scope, line) in enumerate(reversed(self.break_stack)):
                if scope == self.break_scope[-1]:
                    self.codes_generated[line] = (
                        "JP", 
                        f"{self.program_line+1}", 
                        None, 
                        None)
                    self.break_stack.pop(len(self.break_stack) - 1 - i)
            self.break_scope.pop()     
    
    def jpf(self):
        condition = self.semantic_stack.pop()
        self.jpf_line = self.program_line
        self.add_code_line(("JPF", condition, 0, None))

    def jpf_save(self):
        print(self.semantic_stack)
        code_line = self.semantic_stack.pop()
        condition = self.semantic_stack.pop()
        if isinstance(condition, str):
            if condition.startswith("#") or condition.startswith("@"):
                condition = condition[1:]
        if code_line == "error" or int(condition) < 500  :
            code_line = condition
            condition = self.semantic_stack.pop()
        self.store_code_line(("JPF", condition, self.program_line+1, None), code_line)
        self.save()
        
    def save_break(self):
        if not self.in_loop:
            self.semanticErrorMessage.break_statement()
            return
        self.break_stack.append((self.break_scope[-1], self.program_line))
        self.program_line += 1

    def call(self):
        first_out = True
        i = 0
        is_fe = True
        for call in reversed(self.calls):
            id =  call
            if id != "output":
                if self.is_func(id):
                        temp = self.get_temp()

                        num_func, _, line_func  = self.get_func_scope(id)
                        func_params = self.scope_stack[num_func][id]["params"]
                        print("param num", len(self.check_function_params[-1]) , self.scope_stack[num_func][id]["param_size"], self.check_function_params[-1])
                        if len(self.check_function_params[-1]) != self.scope_stack[num_func][id]["param_size"]:
                                if is_fe:
                                    self.semanticErrorMessage.param_num_check(id)
                                    is_fe = False
                                    return
                        if self.scope_stack[num_func][id]["param_size"] >0:
                            for i in (0,self.scope_stack[num_func][id]["param_size"]-1):
                                var = func_params[i]["id"]
                                var_type = func_params[i]["type"]
                                address = func_params[i]["addr"]

                                if var_type == None:
                                    var_type = "int"
                                inp = self.check_function_params[-1][i]
                                var2_type = "int"
                                if isinstance(inp, str):
                                    if inp.startswith("#") or inp.startswith("@"):
                                            inp = inp[1:]
                                            var2_type = "int"
                                    else:
                                        var2_type  = self.get_var_type(inp, self.current_function_name , self.get_func_scope( self.current_function_name)[0])
                                
                                if var2_type == None:
                                    var2_type = "int"
                            
                                self.arg_changed = False
                                print("tyy", var2_type, var_type)
                                if self.semanticErrorMessage.param_type_check( id, i+1, var_type, var2_type):
                                    return
                                i += 1
                            pop = self.semantic_stack.pop()
                            self.add_code_line(("ASSIGN", pop, address, None))
                                
                            pop2 = self.semantic_stack.pop()  
                            if isinstance(pop2, str):
                                if pop2.startswith("#") or pop2.startswith("@"):
                                            pop2 = pop2[1:]
                                            var2_type = "int"  
                            self.check_function_params.pop()
                            self.calls.pop()
                            self.semantic_stack.append(temp)
                            self.add_code_line(("ASSIGN", f"#{self.program_line + 2}", pop2, None))
                            self.add_code_line(("JP", line_func, None, None))
                            self.add_code_line(("ASSIGN", int(pop2)+4, temp, None))                   
            else:
                if first_out:
                    self.output()
                    self.check_function_params.pop()
                    self.calls.pop()
                    first_out = False
 
    def exp_end(self):
        # self.semantic_stack.pop()
        self.last_num = None
        self.last_id = None
        self.last_type = None
        self.is_output = False
        self.calls = []

    def scope_enter(self):
        if not self.jumped_to_main:
            self.waiting_function_jumps[self.program_line] = "main"
            self.program_line += 1
            self.jumped_to_main = True
        self.last_num = None
        self.last_id = None
        self.last_type = None
        self.address_scope_stack.append([])

    def scope_exit(self):
        self.last_num = None
        self.last_id = None
        self.last_type = None
        # if len(self.semantic_stack) > 1:
        #     self.semantic_stack.pop()
        self.address_scope_stack.pop()
        self.is_output = False
    
    def loop_end(self):
        self.in_loop = False
        self.break_stack = []
        for i in range (len(self.scope_stack[-1][self.current_function_name]["loop"])):
            var = self.scope_stack[-1][self.current_function_name]["loop"].pop()
            for i in range (0, var):
                self.scope_stack[-1][self.current_function_name]["params"].pop()

    def loop_start(self):
        self.in_loop = True 
        self.break_stack = []
        self.scope_stack[-1][self.current_function_name]["loop"].append(0)

    
    def start_arg(self):
        self.is_arg = True
        self.check_function_params.append([])


    def end_arg(self):
        self.is_arg = False
        if len(self.check_function_params[-1]) == 0:
            self.check_function_params.pop()
            return


    def declare_var(self):
        if self.last_type == "void":
            self.semantic_stack.pop()
            self.semanticErrorMessage.void_type(self.last_id)
            self.last_type = None
            return
        id = self.semantic_stack.pop()
        address = self.add_var_to_scope(id, self.current_function_name, "int", 1)
        self.add_code_line(("ASSIGN", "#0", address, None))
        self.last_type = None

    def declare_array(self):
        length = int(self.semantic_stack.pop()[1:])
        id = self.semantic_stack.pop()
        address = self.add_var_to_scope(id, self.current_function_name, "array", length)
        self.add_code_line(("ASSIGN", "#0", address, None))
        self.last_type = None

    def add_var_to_scope(self, var, scope_indicator, type, length=1):
        if scope_indicator is not None:
            x = self.get_func_scope(scope_indicator)[0]
            func = scope_indicator
        else:
            x = 0
            func = "global"
            if len(self.address_scope_stack) == 0:
                self.address_scope_stack.append([])
        address = self.get_temp(length, 4)
        if self.in_loop:
            self.scope_stack[x][func]["loop"][-1] += 1
        self.scope_stack[x][func]["params"].append(
        {
            "id": var,
            "addr": address,
            "type": type,
            "line": self.program_line,
        }
        )
        if self.start_param:
            if func != "main":
                self.scope_stack[x][func]["param_size"] += 1
        self.start_param = False                    
        return address
    
    def declare_array_param(self):
        self.start_param = True
        id = self.semantic_stack.pop()
        self.add_var_to_scope(id, self.current_function_name, "array")

    def declare_int_param(self):
        self.start_param = True
        id = self.semantic_stack.pop()
        self.add_var_to_scope(id, self.current_function_name, "int")

    def array_index(self):
        index = self.semantic_stack.pop()
        array = self.semantic_stack.pop()
        result = self.get_temp()
        self.add_code_line(("MULT",  index, "#4", result ))
        self.add_code_line(("ADD", f"{array}", result, result ))
        self.semantic_stack.append("@" + str(result))

    def declaring_function(self):
        self.start_param = True
        self.current_function_type = self.last_type
        self.current_function_name = self.semantic_stack.pop()
        self.scope_stack.append({})
        if len( self.address_scope_stack) == 0:
            self.address_scope_stack.append([])
        address = self.get_temp()
        self.scope_stack[-1][self.current_function_name] = {
            "line": self.program_line+1,
            "addr": address,
            "type": self.current_function_type,
            "ret": self.get_temp(),
            "param_size": 0,
            "loop": [],
            "params": []
        }

    def signature_declared(self):
        for line, function_name in self.waiting_function_jumps.items():
            if function_name == self.current_function_name:
                self.store_code_line(("JP", self.program_line, None, None), line)
    
    def function_declared(self):
        self.current_function_name = None
        self.start_param = False
        self.address_scope_stack.pop()

    def push_state(self):
        if self.current_function_name != "main":
            if len(self.calls) > 0:
                if self.calls[0] != "output":
                    self.state_saved = []
                    for address_scope in self.address_scope_stack:
                        for addr in address_scope[:1]:
                            self.add_code_line(("ASSIGN", addr, f"@{self.stack_pointer}", None))
                            self.add_code_line(("ADD", "#4", self.stack_pointer, self.stack_pointer ))
                            self.state_saved.append(addr)

    def pop_state(self):
        if self.current_function_name != "main" :
            if not self.is_output:
                for addr in reversed(self.state_saved):
                    self.add_code_line(("SUB", self.stack_pointer, "#4", self.stack_pointer ))
                    self.add_code_line(("ASSIGN", f"@{self.stack_pointer}", addr, None))
        self.state_saved = []

    def return_void(self):
        self.add_code_line(("JP", f"@{self.return_address}", None, None))

    def return_int(self):
        addr = self.semantic_stack.pop()
        # self.semantic_stack.pop()
        fn, fa, fl = self.get_func_scope(self.current_function_name)
        self.add_code_line(("ASSIGN", addr, fa+4, None))
        self.add_code_line(("JP", f"@{fa}", None, None))

    def default_return(self):
        if self.current_function_name != "main":
            fn, fa, fl = self.get_func_scope(self.current_function_name)
            self.add_code_line(("JP", f"@{fa}", None, None))
    
    def output(self):
        value = self.semantic_stack.pop()
        self.add_code_line(("PRINT", value, None, None))
        self.semantic_stack.append(value)

    def to_code_string(self, path):
        if not self.semanticErrorMessage.no_code(path):
            self.codes_generated = dict(sorted(self.codes_generated.items()))
            with open(path, "w") as f:
                for i, code_line in self.codes_generated.items():
                    output = f"{i}\t("
                    for code in code_line:
                        if code is not None:
                            output += f"{code}, "
                        else:
                            output += ", "
                    output = output[:-2] + ")\n"
                    f.write(output)
    
    def code_gen(self, action):
        print(action)
        if action[0] == "#":
            action = action[1:]
        actions = {
            "comp": self.compare,
            "get_temp": self.get_temp,
            "p_id": lambda: self.p_id(self.last_id),
            "p_num": lambda: self.p_num(self.last_num),

            "add": self.add,
            "sub": self.sub,
            "mult": self.mult,
            "eq": self.eq,
            "lt": self.lt,
            "arithmetic": self.arithmetic,
            
            "assign": self.assign,
                      
            "label": self.label,
            "save": self.save,
            "break": self.save_break,
            
            "jp": self.jp,
            "jpf": self.jpf,
            "jpf_save": self.jpf_save,
            "jp_break": self.jp_break,
            
            "declare_var": self.declare_var,
            "declare_array": self.declare_array,
            "array_index": self.array_index,
            "declare_array_param": self.declare_array_param,
            "declare_int_param": self.declare_int_param,
            "declaring_function": self.declaring_function,
            "function_declared": self.function_declared,

            "start_arg": self.start_arg,
            "end_arg": self.end_arg,
        
            "exp_end": self.exp_end,

            "scope_enter": self.scope_enter,
            "scope_exit": self.scope_exit,

            "loop_start": self.loop_start,
            "loop_end": self.loop_end,

            "call": self.call,
            "signature_declared": self.signature_declared,

            "push_state": self.push_state,
            "pop_state": self.pop_state,

            "return_void": self.return_void,
            "return_int": self.return_int,
            "default_return": self.default_return,
            "arg": self.arg,

           

            "output": self.output,
 
        }
        if action in actions:
            actions[action]()
        else:
            raise Exception("Invalid action")