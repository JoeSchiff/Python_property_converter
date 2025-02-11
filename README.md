<h1 align="center">Cython Property Converter</h1>

## Convert properties in Cython extension classes from the deprecated legacy syntax to the decorator syntax. ##


<br><br>
### Is this what you're trying to do? ###
![](assets/screenshot.png)
https://cython.readthedocs.io/en/stable/src/userguide/extension_types.html#properties


<br><br>
### Table of Contents
* [Summary](#Summary)
* [Basic Usage](#Basic-Usage)
* [Optional Arguments](#Optional-Arguments)
* [Doc strings](#Doc-strings)
* [Requirements](#Requirements)


<br/><br/>
### Summary
Convert from this:
```
    property cheese:
        "A doc string can go here."
        def __get__(self):
            ...
        def __set__(self, value):
            ...
        def __del__(self):
            ...
```
to this:
```
    @property
    def cheese(self):
        "A doc string can go here."
        ...
    @cheese.setter
    def cheese(self, value):
        ...
    @cheese.deleter
    def cheese(self):
        ...
```



<br><br>
### Basic Usage ###
Give it a folder with the files to convert and a folder to put the new files:<br>
`python converter.py -i /path/to/files/ -o /path/to/output/`



<br><br>
### Optional Arguments ###
```
  -h, --help            show this help message and exit
  --input_dir [INPUT_DIR], -i [INPUT_DIR]
                        Path of the folder containing the files to be modified. Default: Current working directory.
  --output_dir [OUTPUT_DIR], -o [OUTPUT_DIR]
                        Path of the folder to save the modified files. Default: create a subfolder called `new_syntax` where the script is located.
  --class_declaration {cython,pure_python}, -c {cython,pure_python}
                        Which class declaration syntax to use. cython: `cdef class Spam:` or pure_python: `@cython.cclass class Spam:`. Default: cython
  --output_mod_only OUTPUT_MOD_ONLY, -m OUTPUT_MOD_ONLY
                        True/False. Output all files or only modified files. Default: False (output all files)
  --no_getter {skip,convert}, -n {skip,convert}
                        The new syntax must have a getter method before using a setter or deleter method. If a getter method does not exist for that property, you must either keep the old
                        syntax (`skip`) or create an empty getter method (`convert`). Default: skip

```

<br/><br/>
### Class declaration syntax ###

Choose either Pure Python:<br>
`python converter.py --class_declaration pure_python`
```
@cython.cclass
class Spam:
    @property
    def cheese(self):
        ...
```
or Cython:<br>
`python converter.py --class_declaration cython`
```
cdef class Spam:
    @property
    def cheese(self):
        ...
```

<br><br>
### Missing getter method ###
Consider this example of a valid setter method without a getter method using the old syntax:
```
cdef class spam:
    property url_match:
        def __set__(self, url_match):
            self._url_match = url_match
            self._reload_special_cases()
```
However, the new syntax does not allow using a setter or deleter method without a getter method. Use the `--no_getter` argument to decide how to handle this.<br><br>
You can either skip this property and keep the old syntax unchanged:<br>
`python converter.py --no_getter skip`
<br><br>
or create an empty getter method and continue with the conversion:<br>
`python converter.py --no_getter convert`
```
cdef class spam:
    @property
    def url_match(self):
        pass
    @url_match.setter
    def url_match(self, url_match):
        self._url_match = url_match
        self._reload_special_cases()
```


<br><br>
### Doc strings ###
Since there cannot be a docstring between the decorator and the def statement, the docstrings will be moved from here:
```
    property cheese:
        "A doc string can go here."
        def __get__(self):
            ...
```
to here:
```
    @property
    def cheese(self):
        "A doc string can go here."
        ...
```
<br><br>
Aditionally, one-line statements with a doctstring will be split from this:
```    
    property split:
        "docstring for split"
        def __get__(self): return self.val
```        
to this:
```
    @property
    def split(self):
        "docstring for split"
        return self.val
```

<br><br>
### Requirements ###
Compatible with indents that use spaces or tabs. However, an indent must not contain both tabs and spaces.
<br><br>

Required Python versions >= 3.8  
Required packages: cython


<br><br>
