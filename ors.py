#!/usr/bin/env python3
# * encoding: utf-8 *
import argparse, json, os, pprint, string, tabulate, threading, time

class UnknownGeneratorError(Exception):
    pass

def cached_property(compute):
    def getter(self, *a):
        attr = '__computed_%s' % compute.__name__
        if not hasattr(self, attr):
            setattr(self, attr, compute(self, *a))
            getter.computed_value = compute(self, *a)

        return getattr(self, attr)
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
        for i in range(0, len(w)):
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
        Compute the set E(M) [Zha92a] for the monoid; optionally calling
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
    def is_group(self):
        return {(g,) for g in self.gens}.issubset(self.minimal_words)

    @cached_property
    def has_trivial_units(self):
        return len(self.minimal_words) == 1

    @cached_property
    def relator_in_minimal_words(self):
        return factorise(self.minimal_words, self.relator)

    @cached_property
    def group_of_units(self):
        self.minimal_alphabet = {w: Distinct(w) for w in self.minimal_words}
        gens = set(self.minimal_alphabet.values())
        relator = [self.minimal_alphabet[w] for w in self.relator_in_minimal_words]
        return OneRelatorMonoid(gens, relator)


def all_strings(num_letters, length):
    '''
    Iterate over all strings of length `length' over {a, b, ...}, stopping at
    the `num_letters'th letter of the alphabet.
    '''
    assert num_letters <= 26
    if length == 1:
        yield from [string.ascii_lowercase[i] for i in range(num_letters)]
    elif length > 1:
        yield from [string.ascii_lowercase[i] + s for i in range(num_letters) for s in all_strings(num_letters, length - 1)]

# We want to investigate what percentage of one-relator monoids are definitely
# groups or definitely trivial-unit scaling on number of generators and length
# of relation.
class Experiment:
    def __init__(self, filename):
        self.results = {}
        self.filename = filename

        if os.path.exists(filename):
            self.load()

    def check(self, num_gens, length, verbose = False):
        if length == 1:
            return {
                'total': num_gens,
                'group': 0,
                'trivial_units': num_gens,
                'time': 0
            }

        result = {
            'total': 0,
            'group': 0,
            'trivial_units': 0,
            'time': 0
        }
        gens = string.ascii_lowercase[:num_gens]
        start_time = time.time()

        for relation in all_strings(num_gens, length):
            M = OneRelatorMonoid(gens, relation)
            result['total'] += 1
            if M.is_group:
                result['group'] += 1
                #groups[num_gens, length] = groups.get((num_gens, length), [])
                #groups[num_gens, length].append(M)
            if M.has_trivial_units:
                result['trivial_units'] += 1

            if verbose:
                group = 'group ' if M.is_group else ''
                trivial = 'trivial ' if M.has_trivial_units else ''
                neither = 'neither' if not M.is_group and not M.has_trivial_units else ''
                print('< %s | %s >: %s%s%s' % (gens, relation, group, trivial, neither))

        result['time'] = time.time() - start_time
        self.results[num_gens, length] = result
        return result
    
    def load(self):
        with open(self.filename) as handle:
            self.results = {eval(k): v for k, v in json.load(handle).items()}

    def save(self):
        with open(self.filename, 'w') as handle:
            json.dump({str(k): v for k, v in self.results.items()}, handle)

    def run(self, gens_range, length_range, thread_count = 4, verbose = False):
        gens_min, gens_max = gens_range
        split = int((gens_max - gens_min) / thread_count)
        length_min, length_max = length_range
        threads = []

        for i in range(thread_count):
             this_min, this_max = split * i, max(split * (i + 1), gens_max)
             def runner():
                 for num_gens in range(this_min + 1, this_max + 1):
                     for length in range(length_min + 1, length_max + 1):
                         if (num_gens, length) in self.results:
                             print('Skipping |A|=%d |w|=%d.' % (num_gens, length))
                             continue

                         print('Starting to check |A|=%d |w|=%d.' % (num_gens, length))
                         result = self.check(num_gens, length, verbose)
                         print('Finished checking |A|=%d |w|=%d in %.3fs.' % (num_gens, length, result['time']))
                         self.save()

             thread = threading.Thread(target = runner)
             threads.append(thread)
             thread.start()

        try:
            for thread in threads:
                thread.join()
        except KeyboardInterrupt:
            print('Saving...')
            self.save()
    
    def report(self, format = 'fancy_grid'):
        headers = ['$|A|$', '$|w|$', '# groups', '% groups', '# trivial units', '% trivial units', 'total', 'time (s)']
        table = [(gens,
                  length,
                  v['group'],
                  '%.02f' % (v['group'] / v['total'] * 100),
                  v['trivial_units'],
                  '%.02f' % (v['trivial_units'] / v['total'] * 100),
                  v['total'],
                  '%.4f' % v['time']) for ((gens, length), v) in self.results.items()]
        table.sort(key = lambda t: (t[0], t[1]))
        print(tabulate.tabulate(table, headers = headers, tablefmt = format))


PRESENT_FORMATS = {
    'latex': '%d & $\{ %s \}$ & $\{ %s \}$ \\\\',
    'plain': 'i = %d:\n\tC_i:\t{%s}\n\tW(C_i):\t{%s}'
}
def present(gens, relator, fmt = 'plain'):
    def step(C_i):
        if C_i is None:
            return

        C_i = [''.join(x) for x in C_i]
        W = [''.join(x) for x in left_and_right_factors(C_i)]
        print(PRESENT_FORMATS[fmt] % (step.i, ', '.join(C_i), ', '.join(W)))
        step.i += 1
    step.i = 1

    M = OneRelatorMonoid(gens[0], relator[0])
    M.compute_minimal_words(step = step)

BicyclicMonoid = OneRelatorMonoid('bc', 'bc')
M = OneRelatorMonoid('ab', 'bbab')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Perform various computations with one-relation special monoids.')
    parser.add_argument('-f', '--filename', default = 'experiment.dat', help = 'Path to file to store working results in. (default: experiment.dat)')

    sp = parser.add_subparsers(dest = 'mode')
    sp.required = True

    run_args = sp.add_parser('count', description = 'Count one-relation special monoids by property.')
    run_args.add_argument('max_gens', type = int, nargs = 1, help = 'Maximum number of generators in generated presentations.')
    run_args.add_argument('max_length',  type = int, nargs = 1, help = 'Maximum length of relators in generated presentations.')
    run_args.add_argument('--min-gens', dest = 'min_gens', type = int, default = 1, help = 'Minimum number of generators.')
    run_args.add_argument('--min-length', dest = 'min_length', type = int, default = 1, help = 'Minimum length of relators.')
    run_args.add_argument('-t', '--threads', type = int, default = 4, help = 'The number of threads to use checking presentations. (default: 4)')
    run_args.add_argument('-v', '--verbose', action = 'store_true', dest = 'verbose', default = False, help = 'Print detailed information about the calculations in progress.')

    report_args = sp.add_parser('report', description = 'Display results from a previous count.')
    report_args.add_argument('--format', dest = 'format', choices = ('plain', 'simple', 'fancy_grid', 'latex', 'latex_booktabs'), default = 'fancy_grid', help = 'The format of the output grid.')

    present_args = sp.add_parser('present', help = 'Show the derivation of the new presentation given a defining special presentation.')
    present_args.add_argument('-f', '--format', dest = 'format', choices = list(PRESENT_FORMATS.keys()), default = 'plain', help = 'The output format for the steps of computation.')
    present_args.add_argument('generators', nargs = 1, help = 'A string whose letters are the generators.')
    present_args.add_argument('relator', nargs = 1, help = 'The string w, where the resulting presentation is < A | w = ε >.')

    args = parser.parse_args()
    experiment = Experiment(args.filename)

    if args.mode == 'report':
        experiment.report(args.format)
    elif args.mode == 'present':
        present(args.generators, args.relator)
    elif args.mode == 'count':
        experiment.run((args.min_gens, args.max_gens[0]), (args.min_length, args.max_length[0]), args.threads, args.verbose)
    else:
        parser.usage()

