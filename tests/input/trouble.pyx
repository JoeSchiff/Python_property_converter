
cdef class cheese:
    """multi line
    class docstring"""
    property dep:
        """RETURNS (uint64): ID of syntactic dependency label."""
        def __get__(self):
            return self.c.dep

        def __set__(self, label):
            self.c.dep = label


    property sent_start:
        def __get__(self):
            "Deprecated: use Token.is_sent_start instead."
            # Raising a deprecation warning here causes errors for autocomplete
            # Handle broken backwards compatibility case: doc[0].sent_start
            # was False.
            if self.i == 0:
                return False
            else:
                return self.c.sent_start

    property pound:
        # this needs to move also
        def __get__(self):
            return self.val

    property test1:
        """multi line
        docstring"""
        def __get__(self):
            return self.val

    property test2:
        """
        multi line docstring.
        not using self
        """
        def __get__(crazy_person):
            return crazy_person.val

    property split:
        "docstring for split"
        def __get__(self): return self.val
    
                
cdef class spam:
    property url_match:
        def __set__(self, url_match):
            self._url_match = url_match
            self._reload_special_cases()


