class CommentedFile:
    def __init__(self, f, commentstring="#"):
        self.f = f
        self.commentstring = commentstring

    def _skip(self, line):
        skip = line.startswith(self.commentstring) or line.isspace()
        return skip
        
    def _detrail(self, line):
        return line.split(self.commentstring)[0]

    def __next__(self):
        line = next(self.f)
        while self._skip(line):
            line = next(self.f)
        return self._detrail(line)

    def readlines(self):
        lines = [ self._detrail(l) for l in self.f.readlines() if not self._skip(l)]
        return lines
        

    def __iter__(self):
        return self