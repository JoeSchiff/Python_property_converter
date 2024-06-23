import argparse
import distutils
import pathlib


def setup_parser():
    parser = argparse.ArgumentParser(
        description="Convert properties in Cython extension classes from the deprecated legacy syntax to the decorator syntax"
    )
    parser.add_argument(
        "--input_dir",
        "-i",
        type=str,
        nargs="?",
        default=".",
        help="Path of the folder containing the files to be modified. Default: Current working directory.",
    )
    parser.add_argument(
        "--output_dir",
        "-o",
        type=str,
        nargs="?",
        default="DEFAULT",
        help="Path of the folder to save the modified files. Default: create a subfolder called `new_syntax` where the script is located.",
    )
    parser.add_argument(
        "--class_declaration",
        "-c",
        type=str,
        choices=("cython", "pure_python"),
        default="cython",
        help="Which class declaration syntax to use. cython: `cdef class Spam:` or pure_python `@cython.cclass\\nclass Spam:`. Default: cython",
    )
    parser.add_argument(
        "--output_mod_only",
        "-m",
        dest="output_mod_only",
        type=lambda x: bool(distutils.util.strtobool(x)),
        default=False,
        help="True/False. Output all files or only modified files. Default: False (output all files)",
    )
    parser.add_argument(
        "--no_getter",
        "-n",
        type=str,
        choices=("skip", "convert"),
        default="skip",
        help="The new syntax must have a getter method before using a setter or deleter method. If a getter method does not exist for that property, you must either keep the old syntax or create an empty getter method.",
    )
    
    return parser.parse_args()


class IndentTracker:
    """All code in a property block must have its indent reduced by 1 when converting."""

    prev_indent = ""
    current_indent = ""
    one_indent = ""
    property_indent = ""
    property_name = ""
    pause_insertions = False  # Prevent newlines immediately after property decorator
    property_detect = ""  # Move docstrings only if immediately after property decorator
    get_detect = False  # Prevent setter and deleter methods if getter doesn't exist

    def update_indent(line):
        if not line.strip():
            return
        
        Docstring.update_property_detect()
        
        IndentTracker.current_indent = get_indent(line)

        # Increase detected
        if len(IndentTracker.current_indent) > len(IndentTracker.prev_indent):

            # First indent detected
            if len(IndentTracker.prev_indent) == 0:
                IndentTracker.one_indent = IndentTracker.current_indent


        # End of property block detected
        if len(IndentTracker.current_indent) <= len(IndentTracker.property_indent):
            IndentTracker.property_name = ""
            IndentTracker.pause_insertions = False
            IndentTracker.get_detect = False

        # Always set prev to current
        IndentTracker.prev_indent = IndentTracker.current_indent

    def prevent_mixed_chars(line):
        """Prevent use of mixed spaces and tabs in an indent"""
        indent = get_indent(line)        
        if " " in indent and "\t" in indent:
            print(f"ERROR mixed indent on line number {line_number}: {repr(line)}")
            print(f"\n An indent must not contain both tabs and spaces.\n")
            raise SystemExit

        if len(indent) > 0 and len(IndentTracker.property_indent) > 0:
            if indent[0] != IndentTracker.property_indent[0]:
                print()
                #print(3333333333, " ".join(str(ord(char)) for char in indent))



class Docstring:
    """A docstring for a property must be saved and moved to after a def statement"""

    ONELINER_PREFIXES = (
        "if ",
        "elif ",
        "else",
        "for ",
        "while ",
        "def ",
        "cdef ",
        "cpdef ",
        "class ",
        "try",
        "except",
        "finally",
    )  # all one-liners must start with one of these
    DELIM_CHARS = ("'''", '"""', "'", '"', "#")

    text = ""
    descriptor = ""
    delim_char = None

    def new_docstring_detected(line):
        Docstring.text = line

        ## change to line.strip()[:3]?
        # Set quote style
        for delim_char in Docstring.DELIM_CHARS:
            if line.strip().startswith(delim_char):
                Docstring.delim_char = delim_char
                break
        else:
            print("ERROR docstring", line)

        ## change to line.strip().endswith(Docstring.delim_char)?
        # One line docstring
        if line.count(Docstring.delim_char) > 1 or delim_char == "#":
            Docstring.descriptor = "INSERT"
        # Begin multi line docstring
        else:
            Docstring.descriptor = "MULTI_LINE_IN_PROGRESS"

    def insert_docstring(line):
        if Docstring.descriptor != "INSERT":
            return line

        modified_line = "\n".join((line, Docstring.text))

        Docstring.text = ""
        Docstring.descriptor = ""
        return modified_line

    def build_multi_line(line):
        """Combine all docstring lines. Return True while collecting multiline docstring"""
        if Docstring.descriptor == "MULTI_LINE_IN_PROGRESS":
            Docstring.text = "\n".join((Docstring.text, line))
            if line.strip().endswith(Docstring.delim_char):
                Docstring.descriptor = "INSERT"
            return True

    def update_property_detect():
        "Detect the line after the property keyword"
        if IndentTracker.property_detect == "CURRENT_LINE":
            IndentTracker.property_detect = "LINE_AFTER"
        else:
            IndentTracker.property_detect = ""
            
    def split_inline(line):
        """Must split combined one line statements when trying to insert a doctstring.
        Example: `def __get__(self): return self.index`

        Only split the line when all true:
        inside a property,
        there is a docstring to be inserted,
        the next line is a one-linner
        """

        if (
            line.count(":") < 1
            or not IndentTracker.property_name
            or not Docstring.text
        ):
            return line

        if not any(
            line.strip().startswith(colon_prefix)
            for colon_prefix in Docstring.ONELINER_PREFIXES
        ):
            return line

        if line.count(":") > 1:
            print("ERROR: can not split oneliner", line)
            raise SystemExit

        line_one, line_two = line.split(":")

        for each_line in (line_one, line_two):
            if not each_line.strip():
                return line

        line_one += ":"
        line_two = (
            get_indent(line) + IndentTracker.one_indent + line_two.strip()
        )

        return "\n".join((line_one, line_two))



def remove_one_indent(line):
    return line.replace(IndentTracker.one_indent, "", 1)


def get_indent(line):
    indent_pos = len(line) - len(line.lstrip())
    return line[:indent_pos]


def convert_method_name(line, old_dunder_name):
    """For `__get__` and the second line of `__set__` and `__del__`"""
    modified_line = line.replace(old_dunder_name, IndentTracker.property_name)
    modified_line = remove_one_indent(modified_line)
    return modified_line

def create_decorator(line, old_dunder_name, new_name):
    """For `__set__` and `__del__`"""
    first_line = remove_one_indent(line)
    first_line = f"{get_indent(first_line)}@{IndentTracker.property_name}.{new_name}"
    second_line = convert_method_name(line, old_dunder_name)
        
    return "\n".join((first_line, second_line))



def first_pass(file_path):
    modified_file_contents = ""
    with open(file_path) as file:
        for line_number, line in enumerate(file.read().splitlines(), 1):
            IndentTracker.update_indent(line)
            
            match_property(line)
            match_docstring(line)
            
            IndentTracker.prevent_mixed_chars(line)
            modified_line = Docstring.split_inline(line)
            modified_line = no_getter(modified_line, line_number)
            
            if isinstance(modified_line, str):
                modified_file_contents = "\n".join(
                    (modified_file_contents, modified_line)
                )

    write_file(get_output_path(file_path), modified_file_contents)

no_getter_skip_prop = []
def no_getter(line, line_number):
    """Setter and deleter methods must have a getter method"""
    
    if line.strip().startswith("def __get__("):
        IndentTracker.get_detect = True
                    
    if ( line.strip().startswith("def __set__(") or line.strip().startswith("def __del__(") ) and not IndentTracker.get_detect:
        print("ERROR: `get` not detected", line, IndentTracker.property_name)
        print(line_number)
        # Create an empty getter
        if args.no_getter == "convert":
            line_one = f"{IndentTracker.property_indent}{IndentTracker.one_indent}def __get__(self):"
            line_two = f"{IndentTracker.property_indent}{IndentTracker.one_indent}{IndentTracker.one_indent}pass"
            return "\n".join((line_one, line_two, line))
        else:
            #raise SystemExit
            no_getter_skip_prop.append(IndentTracker.property_name)
    return line
        

def match_class_name(line):
    if line.strip().startswith("cdef class "):
        if args.class_declaration == "pure_python":
            return line.replace("cdef ", "@cython.cclass\n")
    return line


def match_property(line):
    if line.strip().startswith("property "):
        IndentTracker.property_indent = get_indent(line)
        IndentTracker.property_name = line.split("property ")[1].split(":")[0]
        IndentTracker.pause_insertions = True
        IndentTracker.property_detect = "CURRENT_LINE"
        if IndentTracker.property_name in no_getter_skip_prop:
            IndentTracker.property_name = ""
        else:
            return f"{get_indent(line)}@property"
    return line

def match_get(line):
    if line.strip().startswith("def __get__("):
        if IndentTracker.property_name:
            #IndentTracker.get_detect = True
            return convert_method_name(line, "__get__")
    return line
    
def match_set(line):
    if line.strip().startswith("def __set__("):
        if IndentTracker.property_name:
            return create_decorator(line, "__set__", "setter")
    return line
    
def match_del(line):
    if line.strip().startswith("def __del__("):
        if IndentTracker.property_name:
            return create_decorator(line, "__del__", "deleter")
    return line

def match_docstring(line):
    if (line.strip().startswith("'") or line.strip().startswith('"') or line.strip().startswith('#')
    ) and IndentTracker.property_detect == "LINE_AFTER":

        if IndentTracker.property_name:

            Docstring.new_docstring_detected(line)
            return True


def convert_line(line):
    """Return empty when you want to exclude the line from the output file.
    Such as when moving docstrings.
    """

    if Docstring.build_multi_line(line):
        return

    if not line.strip():
        if (
            Docstring.descriptor == "INSERT" or IndentTracker.pause_insertions
        ):  # Remove extra newline
            return
        return line

    if match_docstring(line):
        return

    IndentTracker.pause_insertions = False

    modified_line = line

    modified_line = match_class_name(modified_line)

    modified_line = match_property(modified_line)

    modified_line = match_get(modified_line)
    
    modified_line = match_set(modified_line)
    
    modified_line = match_del(modified_line)

    # No matches
    if modified_line == line:
        if IndentTracker.property_name:
            modified_line = remove_one_indent(line)

    modified_line = Docstring.insert_docstring(modified_line)

    return modified_line


def write_file(path, content):
    path.parent.mkdir(
        exist_ok=True, parents=True
    )  # used only when output_mod_only = True
    content = content[1:]  # prevent extra newline at beginning
    content = "\n".join((content, ""))  # replace missing newline at end
    with open(path, "w") as f:
        f.write(content)


def get_output_path(file_path):
    project_name_ind = file_path.parts.index(PROJECT_NAME)
    rel_path_parts = file_path.parts[project_name_ind:]
    return pathlib.Path(output_path).joinpath(*rel_path_parts)


def copy_orig_dir():
    if args.output_mod_only:
        return
    new_output_path = output_path.joinpath(PROJECT_NAME)
    distutils.dir_util.copy_tree(str(input_path), str(new_output_path))


args = setup_parser()
input_path = pathlib.Path(args.input_dir).resolve()
PROJECT_NAME = pathlib.Path(input_path).parts[-1]

if args.output_dir == "DEFAULT":
    output_path = pathlib.Path(__file__).parent.joinpath("new_syntax")
else:
    output_path = pathlib.Path(args.output_dir)

copy_orig_dir()


for file_path in pathlib.Path(input_path).glob("**/*"):
    if file_path.suffix not in (".pyx", ".pxi"):
        continue
    print(f"Begin1: {file_path}")

    with open(file_path) as file:
        first_pass(file_path)




modified_files = []
for file_path in pathlib.Path(output_path).glob("**/*"):
    if file_path.suffix not in (".pyx", ".pxi"):
        continue
    print(f"Begin2: {file_path}")

    file_modified = False
    modified_file_contents = ""

    with open(file_path) as file:
        Docstring.text = ""
        Docstring.descriptor = ""
        for line_number, line in enumerate(file.read().splitlines(), 1):
            IndentTracker.update_indent(line)
            modified_line = convert_line(line)

            if isinstance(modified_line, str):
                modified_file_contents = "\n".join(
                    (modified_file_contents, modified_line)
                )

            if line != modified_line:
                file_modified = True

    if file_modified:
        modified_files.append(file_path)
        write_file(get_output_path(file_path), modified_file_contents)



print("\n Modified files:")
for filename in modified_files:
    print(filename)

print(f"\n Number of modified files: {len(modified_files)}")

print(f"\n Output directory: \n{output_path.resolve()}")


