from collections import OrderedDict
import random

from .Handler import Handler

class RanCat(object):
    def __init__(self, seed=None, unique=False, read_size=1000):
        self.files = OrderedDict()

        from time import time
        self.seed = time() if not seed else seed
        random.seed(self.seed)

        self._conversion = self._default_conversion
        self._unique = bool(unique)
        self._total_combinations = 0
        self._seen_map = {}
        self._read_size = int(read_size)

    def __del__(self):
        for filepath in self.files:
            self.files[filepath].close()

    def __iter__(self):
        return self
    
    def __next__(self):
        return self.next()

    def next(self):
        if (len(self._seen_map.keys()) < self._total_combinations and \
            len(self._seen_map.keys()) > self._total_combinations // 2) \
            or len(self._seen_map.keys()) == 0:
            self._refresh_all(self._read_size)

        if len(self._seen_map.keys()) == self._total_combinations:
            raise StopIteration('Exhausted combinations')

        # Build the string
        seen = False
        while not seen:
            result_string = ''
            for file_tuple in self.files.values():    
                choice = random.choice(file_tuple.current_lines)
                result_string += self._conversion(choice) + '_'
            result_string = result_string[:-1]

            if not self._unique:
                return result_string

            if not self._seen_map.get(result_string, False):
                self._seen_map[result_string] = True
                seen = True

        return result_string

    def load(self, filepath):

        original_filepath = filepath
        filepath = str(filepath)
        while filepath in self.files:
            # We can multi-hash here since we don't need
            # to be able to access a file via filepath after this
            # method.
            filepath = hash(filepath) * hash(filepath)

        self.files[filepath] = Handler(original_filepath)

        return self

    def soft_reset(self):
        """
        Resets the combination tracking
        """
        self._total_combinations = 0
        self._seen_map = {}
        return self

    def hard_reset(self):
        """
        Performs a soft reset as well as clears the files structure
        """
        self.soft_reset()
        for filepath in self.files:
            self.files[filepath].close()
        self.files = OrderedDict()

    def _refresh_all(self, n):
        """
        Reads in the next n lines from the files
        """
        self._total_combinations = 0
        for filepath in self.files:
            if self.files[filepath].is_open():
                for _ in range(0, n):
                    line = self.files[filepath].read_next()
                    if not line:
                        self.files[filepath].close()
                        break
                    self.files[filepath].append(line)

            # Recalculate _total_combinations
            if self._total_combinations == 0:
                self._total_combinations = len(self.files[filepath].current_lines)
            else:
                self._total_combinations *= len(self.files[filepath].current_lines)

    def _default_conversion(self, phrase):
        """
        Removes new lines, replaces whitespace and 
        hyphens with underscores, removes apostrophies.
        """
        return phrase.rstrip().replace(' ', '_').replace(
            '-', '_').replace('\'', '')

    def set_conversion(self, conversion_callable):
        """
        Sets the conversion method for phrases
        """
        if hasattr(conversion_callable, '__call__'):
            self._conversion = conversion_callable
        else:
            raise TypeError('{} must be callable'.format(str(conversion_callable)))
        return self

    def set_unique(self, boolean):
        self._unique = bool(boolean)
        return self

    def set_read_size(self, read_size):
        self._read_size = int(read_size)
        return self
    
    def load_structure(self, *args):
        """
        Accepts a number of arguments which may be filepaths
        or lists/tuples.

        If the arg was a filepath then it is loaded, otherwise
        the list/tuple is used like a file.
        """
        for obj in args:
            self.load(obj)

        return self
