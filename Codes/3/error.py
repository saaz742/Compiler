import enum

class SemanticErrorMessage(enum.Enum):
    NOT_GENERATED = "The code has not been generated."
    SCOPING = "#{}: Semantic Error! '{}' is not defined."
    VOID_TYPE = "#{}: Semantic Error! Illegal type of void for '{}'."
    BREAK_STATEMENT = "#{}: Semantic Error! No 'for' found for 'break'."
    TYPE_MISMATCH = (
        "#{}: Semantic Error! Type mismatch in operands, Got {} instead of {}."
    )
    NO_ERROR = "The input program is semantically correct."
    PARAMS_NUM = (
        "#{}: Semantic Error! Mismatch in numbers of arguments of '{}'."
    )
    PARAM_TYPE = "#{}: Semantic Error! Mismatch in type of argument {} of '{}'. Expected '{}' but got '{}' instead."


class SemanticError:
    def __init__(self, parser, scanner):
        self.parser = parser
        self.scanner = scanner

        self.semantic_errors = list()
        

    def type_mismatch(self, type_right, type_left):
        if type_right != type_left:
            self.semantic_errors.append(
                SemanticErrorMessage.TYPE_MISMATCH.value.format(
                    self.scanner.lineno, type_right, type_left
                )
            ) 
            return True
        else: 
            return False
    
    def scoping(self, id):
        self.semantic_errors.append(
            SemanticErrorMessage.SCOPING.value.format(self.scanner.lineno, id)
        )

    def void_type(self, id):
        self.semantic_errors.append(
            SemanticErrorMessage.VOID_TYPE.value.format(
                self.scanner.lineno, id)
        )

    def break_statement(self):
        self.semantic_errors.append(
            SemanticErrorMessage.BREAK_STATEMENT.value.format(
                self.scanner.lineno)
        )

    def param_num_check(self, current_func):
        self.semantic_errors.append(
            SemanticErrorMessage.PARAMS_NUM.value.format(
                self.scanner.lineno, current_func)
        )
     


    def param_type_check(self, current_func, index, expected_type, type_right):
        # type_right = self.get_type(address)
        if type_right != expected_type:
            self.semantic_errors.append(
                SemanticErrorMessage.PARAM_TYPE.value.format(
                    self.scanner.lineno, index, current_func, expected_type, type_right)
            )
            return True
        else:
            return False
                
    def no_code(self, path):
        if len(self.semantic_errors) > 0:
            with open(path, "w") as f:
                f.write(f"{SemanticErrorMessage.NOT_GENERATED.value.format(self.scanner.lineno)}")
            return True
        else:
            return False

    def to_semantic_errors(self, path):
            if len(self.semantic_errors) == 0:
                with open(path, "w") as f:
                     f.write(f"{SemanticErrorMessage.NO_ERROR.value.format(self.scanner.lineno)}")
            else:
                x = []
                x.append(self.semantic_errors[0])
                for i in range (len(self.semantic_errors)-1):
                    x.append(self.semantic_errors[i+1])
                    if self.semantic_errors[i] == self.semantic_errors[i+1]:
                        x.pop()
                with open(path, "w") as f:
                    f.write("\n".join(x) + "\n")