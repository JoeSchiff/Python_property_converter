<h1 align="center">Cython Property Converter</h1>
<h2 align="center">Convert properties in Cython extension classes from the deprecated legacy syntax to the decorator syntax.</h2>

<br><br>
## ===  Under construction  === ##
<br><br>

### Is this what you're trying to do? ###
![](assets/screenshot.png)
https://cython.readthedocs.io/en/stable/src/userguide/extension_types.html#properties
<br><br>


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
### Docstrings ###
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
### Class declaration syntax ###

Choose either Pure Python:
```
@cython.cclass
class Spam:
    @property
    def cheese(self):
        ...
```
or Cython:
```
cdef class Spam:
    @property
    def cheese(self):
        ...
```


<br><br>
Compatible with indents that use spaces or tabs. However, an indent must not contain both tabs and spaces.

<br>
Requires Python >= 3.10.


<br><br>
