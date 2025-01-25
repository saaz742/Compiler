from anytree import RenderTree
from scanner import Scanner
from parser2 import Parser

def main():
    input_path = "input.txt"
    scanner = Scanner(input_path)
    parser = Parser(scanner)
    parse_tree, errors = parser.parse()
    parser.code_generator.to_code_string('output.txt')
    parser.code_generator.semanticErrorMessage.to_semantic_errors('semantic_errors.txt')
    # with open("parse_tree.txt", "w") as f:
    #     f.write(RenderTree(parse_tree.to_anytree()).by_attr())
    # with open("syntax_errors.txt", "w") as f:
    #     if len(errors) == 0:
    #         f.write(f"There is no syntax error.")
    #     else:
    #         for error in errors:
    #             f.write(f"{error}\n")

if __name__ == "__main__":
    main()