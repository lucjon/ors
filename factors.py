r'''
\addbibresource{ors.bib}
In \cite{Zhang92a}, $W(C_i)$ is defined to be `the set of all elements that are
both left and right factors of elements of $C_i$'. This seems like it could be
any of:
\begin{enumerate}
    \item \label{allLR} $L(C_i) \cap R(C_i)$
    \item \label{eachLR} $\bigcup \{L(\{c\}) \cap R(\{c\}) \mid c \in C_i\}$
    \item \label{unionLR} $L(C_i) \cup R(C_i)$
\end{enumerate}

The paper asserts that a few things follow from the definition of $W(C_i)$. For
each $i$, every element of $C_i$ should have the same length as $w$, where $w$
is the single defining relator of the monoid. Furthermore, if $E(M)$ denotes
the set of elements in $W(C_k)$ (where $C_k$ is the maximal set over all $C_i$)
which have no proper right factors in $W(C_k)$ --- that is,
    \[ E(M) = \{ w \in W(C_k) \mid R(w) \intersect W(C_k) \subseteq \{w, \epsilon\} \} --- \]
then the relator $w$ is expressible as a product of factors in $E(M)$.

For experimentation purposes, we provide functions to calculate the $C_i$s and
$E(M)$ based on each possible definition of $W$.
'''
import random, pprint, string, sys


def L(A):
    'Yields all the left factors of words in A.'
    for w in A:
        for i in range(len(w) + 1):
            yield w[:i]

def R(A):
    'Yields all the right factors of words in A.'
    for w in A:
        for i in range(len(w)):
            yield w[-i:]
 
def W1(Ci):
    'W, according to definition \\ref{allLR}.'
    return set(L(Ci)).intersection(set(R(Ci)))

def W2(Ci):
    'W, according to definition \\ref{eachLR}.'
    S = set()
    for s in (set(L([c])).intersection(set(R([c]))) for c in Ci):
        for w in s:
            S.add(w)
    return S

def W3(Ci):
    'W, according to definition \\ref{unionLR}.'
    return set(L(Ci)).union(set(R(Ci)))


all_Ws = (W1, W2, W3)


def Cnext(Ci, W):
    'Given $C_i$ and a choice of $W$, compute $C_{i+1}$.'
    result = set(Ci)

    for x in W(Ci):
        for u in Ci:
            if u.endswith(x):
                y = u[:-len(x)]
                result.add(x + y)
            if u.startswith(x):
                z = u[len(x):]
                result.add(z + x)

    return result

def Ck(w, W):
    'Given the relator $w$ and a choice of $W$, compute the maximal $C_k$.'
    result = None
    new = set((w,))

    while result != new:
        result = new
        new = Cnext(result, W)

    return result

def E(Ck, W):
    'Given the maximal $C_k$ and the $W$ used to compute it, find $E(M)$.'
    WCk = W(Ck)
    result = set()

    for w in WCk:
        candidate = True
        for u in set(R((w,))).difference({w, ''}):
            if u in WCk:
                candidate = False
                break

        if candidate:
            result.add(w)

    return result

def decompose(Sigma, w, factors = ()):
    '''
    Attempt to express the word 'w' as a product of factors in the set Sigma.
    If this is not possible, return False.
    '''
    if len(w) == 0:
        return factors
    else:
        for prefix in Sigma:
            if w.startswith(prefix) and len(prefix) > 0:
                result = decompose(Sigma, w[len(prefix):], factors + (prefix,))
                if result:
                    return result
        return False

def trial(w, *Ws):
    result = {}

    for W in Ws:
        ck = Ck(w, W)
        e = E(Ck(w, W), W)
        length_correct = len(set(len(x) for x in ck)) == 1 and len(next(iter(ck))) == len(w)
        result[W] = (e, length_correct, decompose(e, w))
        
    return result


def random_relator(n, k):
    return ''.join(random.choice(string.ascii_lowercase[:n]) for i in range(random.randint(1, k)))

def random_trial(n, k):
    relator = random_relator(n, k)
    return relator, trial(relator, *all_Ws)
    
def random_trials(n, k, m):
    works = {w: True for w in all_Ws}

    for i in range(m):
        r, result = random_trial(n, k)
        for w, (_, length, factors) in result.items():
            old = works[w]
            works[w] = old and bool(length and factors)

            if old and not works[w]:
                pprint.pprint((w, r))

    return works


# The following:
#    >>> random_trials(6, 25, 1000) 
#    (<function W3 at 0x7fcb0f5f3048>, 'ecedcacc')
#    (<function W2 at 0x7fcb0f5f1f28>, 'dfbfbffdd')
#    {<function W1 at 0x7fcb0f5f1ea0>: True, <function W3 at 0x7fcb0f5f3048>: False, <function W2 at 0x7fcb0f5f1f28>: False}
# suggests W1 is correct.


def give_us_some_Es(n, k, m = 20):
    for i in range(m):
        r = random_relator(n, k)
        ck = Ck(r, W1)
        pprint.pprint((r, E(ck, W1)))

def steps(w):
    result = None
    new = [w]
    i = 1

    while result != new:
        sys.stdout.write('%d & \\{%s\\} & \\{%s\\}' % (i, ', '.join(new), ', '.join(W1(new))))
        result = new
        new = Cnext(result, W1)
        i += 1
        if result != new:
            print(' \\\\')
        else:
            print('')



