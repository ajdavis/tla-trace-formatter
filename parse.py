from lark import Lark, Transformer, v_args
import jinja2
import html
import sys
import argparse

LINE_SEP = "<br />"

class State:
    def __init__(self, name, variables):
        self.name = name
        self.variables = variables

    def __str__(self):
        return "{0}\n{1}".format(
            self.name,
            " ".join("{0} = {1}".format(k, v) for k, v in self.variables.items()))

    def __repr__(self):
        return self.__str__()

class TreeToStates(Transformer):
    def __init__(self, text):
        self.text = text

    @v_args(meta=True)
    def show_text(self, children, meta):
        text = self.text[meta.start_pos:meta.end_pos] if not meta.empty else ""
        return html.escape(text).replace("\n", LINE_SEP)

    def value(self, children):
        return children[0]

    function_kv_print = show_text
    function = show_text
    word = show_text
    sequence = show_text
    state_name = show_text
    set = show_text
    # behavior is a list of states.
    behavior = list

    def function_print(self, children):
        return LINE_SEP.join(children)

    def state(self, children):
        name = children[0]
        variables = {v.children[0]: v.children[1] for v in children[1:]}
        return State(name, variables)

def parse_output(text):
    with open("output-grammar.lark", "r") as grammar:
        parser = Lark(grammar, start='behavior', propagate_positions=True)
        tree = parser.parse(text)
        # print(tree.pretty())
        result = TreeToStates(text).transform(tree)
        # print(result)
        return result

def generate_html(states, kept_variables):
    kept_variables = kept_variables or states[0].variables.keys()

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(searchpath="./"),
        # autoescape=jinja2.select_autoescape(['html', 'xml'])
    )
    template = env.get_template("template.html")
    generated = template.render(states=states,
        header=[k for k in states[0].variables.keys() if k in kept_variables])
    print(generated)


def test_html():
    state = State("State 1", {"log": "<here is log>", "term": "terms"})
    generate_html([state, state])

def parse_and_generate_html(tla_output_file_name, kept_variables):
    with open(tla_output_file_name, "r") as tla_output:
        text = tla_output.read()
        behavior = parse_output(text)
        generate_html(behavior, kept_variables)

if __name__ == "__main__":
    tla_output_file_name = "tla.out"
    parser = argparse.ArgumentParser(description='Parse TLC output')
    parser.add_argument('file_name', nargs='?', help='TLC output file name', 
                        default=tla_output_file_name)
    parser.add_argument('--keep', nargs='+', help='State variables kept in HTML')

    args = parser.parse_args()
    parse_and_generate_html(args.file_name, args.keep)

