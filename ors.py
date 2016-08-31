class UnknownGeneratorError(Exception):
    pass

def cached_property(compute):
    def getter(*a):
        if not hasattr(getter, 'computed_value'):
            getter.computed_value = compute(*a)

        return getter.computed_value
    getter.__name__ = compute.__name__
    return property(getter)

def left_factors(X):
    l_factors = set()
    for w in X:
        for i in range(len(w) + 1):
            l_factors.add(w[:i])
    return l_factors

def right_factors(X):
    r_factors = set()
    for w in X:
        for i in range(1, len(w)):
            r_factors.add(w[-i:])
    return r_factors

def left_and_right_factors(X):
    return left_factors(X).intersection(right_factors(X))

def subwords(w):
    w = tuple(w)
    yield ()
    yield w

    for sublength in range(1, len(w) - 1):
        for index in range(len(w) - sublength):
            yield w[index:index + sublength]

def factorise(Sigma, w, factors = ()):
    '''
    Attempt to factorise the word 'w' as a product of factors in the set Sigma.
    If this is not possible, return False.
    '''
    if len(w) == 0:
        return factors
    else:
        for prefix in Sigma:
            if is_prefix(prefix, w) and len(prefix) > 0:
                result = factorise(Sigma, w[len(prefix):], factors + (prefix,))
                if result:
                    return result
        return False

def is_prefix(a, b):
    'Returns True iff a is a prefix of b.'
    return b[:len(a)] == a

def is_suffix(a, b):
    'Returns True iff a is a suffix of b.'
    return b[-len(a):] == a

def format_word(w):
    return 'ε' if w == () else ''.join(map(str, w))

class Distinct:
    def __init__(self, letter):
        self.letter = letter

    def __str__(self):
        return '%s\'' % self.letter

class Monoid:
    def __init__(self, gens, relations):
        self.gens = set(gens)
        self.relations = set((tuple(a), tuple(b)) for (a, b) in relations)

        for (a, b) in self.relations:
            if not set(a).issubset(self.gens) or not set(b).issubset(self.gens):
                raise UnknownGeneratorError

    def format_rels(self):
        return ', '.join('%s → %s' % (format_word(u), format_word(v)) for (u, v) in sorted(self.relations, key = lambda a: a[0]))

    def __repr__(self):
        return 'Mon ⟨ %s | %s ⟩' % (', '.join(sorted(self.gens)), self.format_rels())

    def relations_for(self, word):
        return self.relations

    def normal_form(self, word):
        word = tuple(word)
        if not set(word).issubset(self.gens):
            raise UnknownGeneratorError
        
        previous = None
        current = word

        while previous != current:
            previous = current
            
            for (u, v) in self.relations_for(current):
                for i in range(len(current)):
                    if current[i:i + len(u)] == u:
                        current = current[:i] + v + current[i + len(u):]
                        break

        return current

class OneRelatorMonoid(Monoid):
    def __init__(self, gens, relator):
        super().__init__(gens, [(relator, ())])
        self.relator = tuple(relator)

        if not set(relator).issubset(gens):
            raise UnknownGeneratorError


    @cached_property
    def minimal_words(self):
        return self.compute_minimal_words()

    def compute_minimal_words(self, step = lambda A: None):
        '''
        Compute the set E(M) [Zhang1992a] for the monoid; optionally calling
        the function `step' for every new set C_i.
        '''
        C_prev = None
        C_next = {self.relator}

        step(C_prev)

        while C_prev != C_next:
            C_prev = C_next
            C_next = C_prev.copy()
            W = left_and_right_factors(C_prev)

            for yx in C_prev:
                for y in W:
                    if is_prefix(y, yx):
                        x = yx[len(y):]
                        C_next.add(x + y)

            for zy in C_prev:
                for y in W:
                    if is_suffix(y, zy):
                        z = zy[:-len(y)]
                        C_next.add(y + z)

            step(C_next)

        # We have stabilised, so find minimal words i.e. those with no proper
        # right factor in W(C_next).
        minimal_words = set()

        for w in W:
            is_minimal = True
            for u in right_factors([w]).difference({w, ''}):
                if u in W:
                    is_minimal = False
                    break

            if is_minimal:
                minimal_words.add(w)

        return minimal_words

    @cached_property
    def relator_in_minimal_words(self):
        return factorise(self.minimal_words, self.relator)

    @cached_property
    def group_of_units(self):
        self.minimal_alphabet = {w: Distinct(w) for w in self.minimal_words}
        gens = set(self.minimal_alphabet.values())
        relator = [self.minimal_alphabet[w] for w in self.relator_in_minimal_words]
        return OneRelatorMonoid(gens, relator)





BicyclicMonoid = OneRelatorMonoid('bc', 'bc')
M = OneRelatorMonoid('ab', 'bbab')
