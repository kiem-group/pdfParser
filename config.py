class Config:
    def __init__(self):
        self._indent = 150      # Maximal horizontal offset to consider the next line a continuation of the previous
        self._noise = 3         # Minimal threshold on lines with certain indentation. Helps to exclude non-references
        self._min_length = 30   # Minimal length of the reference or index term, to exclude page numbers, titles, etc.
        self._max_length = 300  # Maximal length of the reference or index term, to exclude article content
        self._min_words = 3     # Not used
        self._max_words = 100   # Not used

    @property
    def indent(self):
        return self._indent

    @indent.setter
    def indent(self, value):
        self._indent = value

    @indent.deleter
    def indent(self):
        del self._indent

    @property
    def noise(self):
        return self._noise

    @noise.setter
    def noise(self, value):
        self._noise = value

    @noise.deleter
    def noise(self):
        del self._noise

    @property
    def min_length(self):
        return self._min_length

    @min_length.setter
    def min_length(self, value):
        self._min_length = value

    @min_length.deleter
    def min_length(self):
        del self._min_length

    @property
    def max_length(self):
        return self._max_length

    @max_length.setter
    def max_length(self, value):
        self._max_length = value

    @max_length.deleter
    def max_length(self):
        del self._max_length

    @property
    def min_words(self):
        return self._min_words

    @min_words.setter
    def min_words(self, value):
        self._min_words = value

    @min_words.deleter
    def min_words(self):
        del self._min_words

