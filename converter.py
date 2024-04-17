import argparse
import distutils
import pathlib


class IndentTracker:
    """All code in a property block must have its indent reduced by 1 when converting."""

    prev_indent = ""
    current_indent = ""
    one_indent = ""
    property_indent = ""
    property_name = ""
    disallow_space = False  # Prevent newlines after decorator

    def update_indent(line):
        if not line.strip():
            return

        line = IndentTracker.prevent_mixed_chars(line)
        IndentTracker.current_indent = get_indent(line)

        # Increase
        if len(IndentTracker.current_indent) > len(IndentTracker.prev_indent):

            # First indent
            if len(IndentTracker.prev_indent) == 0:
                IndentTracker.one_indent = IndentTracker.current_indent

        # End of property block
        if len(IndentTracker.current_indent) <= len(IndentTracker.property_indent):
            IndentTracker.property_name = ""
            IndentTracker.disallow_space = False

        # Always set prev to current
        IndentTracker.prev_indent = IndentTracker.current_indent

    def prevent_mixed_chars(line):
        """Prevent use of mixed spaces and tabs in an indent"""
        indent = get_indent(line)
        if " " in indent and "\t" in indent:
            print(f"ERROR mixed indent on line number {line_number}: {repr(line)}")
            print(f"\n An indent must not contain both tabs and spaces.\n")
            raise SystemExit

        return line


class Docstring:
    """A docstring for a property must be saved and moved to after a def statement"""

    COLON_PREFIXES = (
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
    )
    DEMLIM_CHARS = ("'''", '"""', "'", '"')

    text = ""
    descriptor = ""
    delim_char = None

    def new_docstring_detected(line):
        Docstring.text = line

        ## change to line.strip()[:3]?
        # Set triple quote style
        for delim_char in Docstring.DEMLIM_CHARS:
            if line.strip().startswith(delim_char):
                Docstring.delim_char = delim_char
                break
        else:
            print("ERROR docstring", line)

        ## change to line.strip().endswith(Docstring.delim_char)?
        # One line docstring
        if line.count(Docstring.delim_char) > 1:
            Docstring.descriptor = "INSERT"
        # Begin multi line docstring
        else:
            Docstring.descriptor = "MULTI_LINE_IN_PROGRESS"

    def build_multi_line(line):  ## make this 2 methods?
        if Docstring.descriptor == "MULTI_LINE_IN_PROGRESS":
            Docstring.text = "\n".join((Docstring.text, line))
            if line.strip().endswith(Docstring.delim_char):
                Docstring.descriptor = "INSERT"
            return True

    def insert_docstring(line):
        if Docstring.descriptor != "INSERT":
            return line

        if Docstring.check_inline(line):
            modified_line = Docstring.split_inline(line)
        else:
            modified_line = "\n".join((line, Docstring.text))

        Docstring.text = ""
        Docstring.descriptor = ""

        return modified_line

    def check_inline(line):
        """Must split combined one line statements when trying to insert a doctstring.
        Example: def __get__(self): return self.ptr.index

        Only split the line when all true:
        inside a property,
        there is a docstring,
        docstring is ready to be inserted,
        the next line is a one-linner
        """

        if (
            line.count(":") != 1
            or not IndentTracker.property_name
            or not Docstring.text
        ):
            return

        if not any(
            line.strip().startswith(colon_prefix)
            for colon_prefix in Docstring.COLON_PREFIXES
        ):
            return

        line_one, line_two = line.split(":")

        for each_line in (line_one, line_two):
            if not each_line.strip():
                return

        return True

    def split_inline(line):
        line_one, line_two = line.split(":")

        line_one += ":"
        line_two = (
            get_indent(line) + IndentTracker.one_indent + line_two.strip()
        )  ## how does this work without adding one indent? same for docstring? +

        return "\n".join((line_one, Docstring.text, line_two))


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
        "--class_dec",
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

    return parser.parse_args()


def remove_one_indent(line):
    return line.replace(IndentTracker.one_indent, "", 1)


def get_indent(line):
    indent_pos = len(line) - len(line.lstrip())
    return line[:indent_pos]


def one_line_convert(line, orig_name):
    """For `__get__` and the second line of `__set__` and `__del__`"""
    modified_line = line.replace(orig_name, IndentTracker.property_name)
    return remove_one_indent(modified_line)


def two_line_convert(line, orig_name, new_name):
    """For `__set__` and `__del__`"""
    first_line = remove_one_indent(line)
    first_line = f"{get_indent(first_line)}@{IndentTracker.property_name}.{new_name}"
    second_line = one_line_convert(line, orig_name)
    return "\n".join((first_line, second_line))


def convert_line(line):
    """Return empty when you want to exclude the line from the output file.
    Such as when moving docstrings.
    """

    if Docstring.build_multi_line(line):
        return

    if not line.strip():
        if (
            Docstring.descriptor == "INSERT" or IndentTracker.disallow_space
        ):  # Remove extra newline
            return
        return line

    IndentTracker.disallow_space = False

    modified_line = line

    match line.strip():

        # Class name
        case string if string.startswith("cdef class "):
            if args.class_dec == "pure_python":
                modified_line = modified_line.replace("cdef ", "@cython.cclass\n")

        # Init prop
        case string if string.startswith("property "):
            IndentTracker.property_indent = get_indent(line)
            IndentTracker.property_name = line.split("property ")[1].split(":")[0]
            IndentTracker.disallow_space = True
            modified_line = f"{get_indent(line)}@property"

        # Prop get
        case string if string.startswith("def __get__(self"):
            if IndentTracker.property_name:
                modified_line = one_line_convert(line, "__get__")

        # Prop set
        case string if string.startswith("def __set__(self"):
            if IndentTracker.property_name:
                modified_line = two_line_convert(line, "__set__", "setter")

        # Prop del
        case string if string.startswith("def __del__(self"):
            if IndentTracker.property_name:
                modified_line = two_line_convert(line, "__del__", "deleter")

        # Docstring
        case string if string.startswith("'") or string.startswith('"'):
            if IndentTracker.property_name:
                Docstring.new_docstring_detected(line)
                return

        # No match
        case _:
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


modified_files = []
for file_path in pathlib.Path(input_path).glob("**/*"):
    if file_path.suffix not in (".pyx", ".pxi"):
        continue
    print(f"Begin: {file_path}")

    file_modified = False
    modified_file_contents = ""

    with open(file_path) as file:
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
