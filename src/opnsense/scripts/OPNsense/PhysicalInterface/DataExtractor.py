from __future__ import print_function
import re

class DataExtractor:
    def __init__(self, haystack):
        self.haystack = haystack
        self._processed_ranges = []

    def extract(self, pattern):
        self.matches = m = re.search(pattern, self.haystack)
        if m:
            self._processed_ranges += [(m.start(), m.end())]
            return True
        else:
            return False

    def _is_processed(self, i):
        ret = any(start <= i < end for start, end in self._processed_ranges)
        return ret

    def unprocessed(self):
        h = self.haystack
        return ''.join(h[i] for i in xrange(len(h)) if not self._is_processed(i))

    def unprocessed_stripped(self):
        return re.sub(r'(\s)\s+', r'\1', self.unprocessed().strip())

    def illustrate(self):
        print(self.haystack.rstrip())
        for i in xrange(len(self.haystack)):
            if self._is_processed(i):
                c = ' '
            else:
                c = '^'
            if self.haystack[i] == '\t':
                c = 8*c
            print(c, end='')
        print()

    def extractfail(self):
        self._processed_ranges.pop()

if __name__ == '__main__':
    s = 'apples 50 bearname Winnie brainsize small'
    de = DataExtractor(s)
    if de.extract(r'\bbearname (\w+)\b'):
        print('Bear is called', de.matches.group(1))
    m = de.extract(r'\bbrainsize (\w+)\b')
    if m:
        print('Brain size is', de.matches.group(1))
    print('Unprocessed data: %r' % de.unprocessed())
    de.illustrate()
