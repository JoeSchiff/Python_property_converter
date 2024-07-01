cdef class cheese:
    """multi line
    class docstring"""
    @property
    def dep(self):
        """RETURNS (uint64): ID of syntactic dependency label."""
        return self.c.dep

    @dep.setter
    def dep(self, label):
        self.c.dep = label


    @property
    def sent_start(self):
        "Deprecated: use Token.is_sent_start instead."
        # Raising a deprecation warning here causes errors for autocomplete
        # Handle broken backwards compatibility case: doc[0].sent_start
        # was False.
        if self.i == 0:
            return False
        else:
            return self.c.sent_start

    @property
    def pound(self):
        # this needs to move also
        return self.val

    @property
    def test1(self):
        """multi line
        docstring"""
        return self.val

    @property
    def test2(crazy_person):
        """
        multi line docstring.
        not using self
        """
        return crazy_person.val

    @property
    def split(self):
        "docstring for split"
        return self.val
    
                
cdef class spam:
    property url_match:
        def __set__(self, url_match):
            self._url_match = url_match
            self._reload_special_cases()


