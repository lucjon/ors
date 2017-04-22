# vim: ft=gap
### Utility functions for calculating factors of a word.
# Calculate the left factors of a set of strings S, including the strings
# themselves and $\epsilon$.
LeftFactors := function(S)
	local L, s, i;
	L := [""];
	for s in S do
		for i in [1..Length(s)] do
			AddSet(L, s{[1..i]});
		od;
	od;
	return L;
end;

# Calculate the right factors of a set of strings S.
RightFactors := function(S)
	local L, s, i, n;
	L := [""];
	for s in S do
		n := Length(s);
		for i in [0..n-1] do
			AddSet(L, s{[(n-i)..n]});
		od;
	od;
	return L;
end;

# Compute only the proper right factors, i.e. not whole words or $\epsilon$
ProperRightFactors := S -> Difference(RightFactors(S), Concatenation(S, [""]));

# Compute words which are left and right factors of S.
LeftAndRightFactors := S -> Intersection(LeftFactors(S), RightFactors(S));

# Split off a prefix from a string .
CutPrefix := function(string, prefix)
	if Length(string) <= Length(prefix) then
		return "";
	else
		return string{[Length(prefix) + 1 .. Length(string)]};
	fi;
end;

# Split off a suffix from a string.
CutSuffix := function(string, suffix)
	if Length(string) <= Length(suffix) then
		return "";
	else
		return string{[1 .. Length(string) - Length(suffix)]};
	fi;
end;

# Factorise a given string over an `alphabet' $\Sigma$, returning false if this is
# not possible: e.g.
#	Factorise(["ab", "c"], "cababc") = ["c", "ab", "ab", "c"]
# but
#	Factorise(["c", "d"], "cde") = false.
Factorise := function(Sigma, w, arg...)
	local factors, prefix, result;
	if Length(arg) = 0 then
		factors := [];
	else
		factors := arg[1];
	fi;

	if Length(w) = 0 then
		return factors;
	else
		for prefix in Sigma do
			if StartsWith(w, prefix) and Length(prefix) > 0 then
				result := Factorise(Sigma, CutPrefix(w, prefix), Concatenation(factors, [prefix]));
				# (note, result generally not a boolean)
				if result <> false then
					return result;
				fi;
			fi;
		od;

		return false;
	fi;
end;

### The algorithm for computing the generating set.
# Compute the set $C_k$ as described in [Zha92a] for the monoid $\langle A \mid w = \epsilon \rangle$.
# Returns a list [$C_k$, $W(C_k)$], as both are computed simultaneously.
ComputeCk := function(w)
	local C_prev, C_next, W, yx, y, x, zy, z;
	C_prev := false;
	C_next := [w];

	while C_prev <> C_next do
		C_prev := C_next;
		C_next := ShallowCopy(C_prev);
		W := LeftAndRightFactors(C_prev);

		for yx in C_prev do
			for y in W do
				if StartsWith(yx, y) then
					x := CutPrefix(yx, y);
					AddSet(C_next, Concatenation(x, y));
				fi;
			od;
		od;

		for zy in C_prev do
			for y in W do
				if EndsWith(zy, y) then
					z := CutSuffix(zy, y);
					AddSet(C_next, Concatenation(y, z));
				fi;
			od;
		od;
	od;

	return [C_next, W];
end;

# The main function. Computes the set $E(M)$ of minimal words of the monoid
# $\langle A \mid w = \epsilon\rangle$, where $A$ is the set of letters in $w$.
MinimalWords := function(w)
	local W, is_minimal;
	W := ComputeCk(w)[2];
	is_minimal := w -> IsEmpty(Intersection(ProperRightFactors([w]), W));
	return Filtered(W, w -> w <> "" and is_minimal(w));
end;


