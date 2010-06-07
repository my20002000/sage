r"""
Field of Arbitrary Precision Complex Intervals

AUTHORS:

- William Stein wrote complex_field.py.
    -- William Stein (2006-01-26): complete rewrite
  Then complex_field.py was copied to complex_interval_field.py and
  heavily modified:
    -- Carl Witty (2007-10-24): rewrite for intervals

    -- Niles Johnson (2010-08): Trac #3893: ``random_element()`` should pass on ``*args`` and ``**kwds``.

"""

#################################################################################
#       Copyright (C) 2006 William Stein <wstein@gmail.com>
#
#  Distributed under the terms of the GNU General Public License (GPL)
#
#                  http://www.gnu.org/licenses/
#*****************************************************************************

import complex_number
import complex_double
import field
import integer_ring
import integer
import real_mpfr
import weakref
import ring
import real_mpfi
import complex_interval
import complex_field
from sage.misc.sage_eval import sage_eval

from sage.structure.parent_gens import ParentWithGens

NumberFieldElement_quadratic = None
def late_import():
    global NumberFieldElement_quadratic
    if NumberFieldElement_quadratic is None:
        import sage.rings.number_field.number_field_element_quadratic as nfeq
        NumberFieldElement_quadratic = nfeq.NumberFieldElement_quadratic

def is_ComplexIntervalField(x):
    return isinstance(x, ComplexIntervalField_class)

cache = {}
def ComplexIntervalField(prec=53, names=None):
    """
    Return the complex field with real and imaginary parts having prec
    *bits* of precision.

    EXAMPLES:
        sage: ComplexIntervalField()
        Complex Interval Field with 53 bits of precision
        sage: ComplexIntervalField(100)
        Complex Interval Field with 100 bits of precision
        sage: ComplexIntervalField(100).base_ring()
        Real Interval Field with 100 bits of precision
        sage: i = ComplexIntervalField(200).gen()
        sage: i^2
        -1
        sage: i^i
        0.207879576350761908546955619834978770033877841631769608075136?
    """
    global cache
    if cache.has_key(prec):
        X = cache[prec]
        C = X()
        if not C is None:
            return C
    C = ComplexIntervalField_class(prec)
    cache[prec] = weakref.ref(C)
    return C


class ComplexIntervalField_class(field.Field):
    """
    The field of complex numbers.

    EXAMPLES:
        sage: C = ComplexIntervalField(); C
        Complex Interval Field with 53 bits of precision
        sage: Q = RationalField()
        sage: C(1/3)
        0.3333333333333334?
        sage: C(1/3, 2)
        0.3333333333333334? + 2*I

    We can also coerce rational numbers and integers into C, but
    coercing a polynomial will raise an exception.

        sage: Q = RationalField()
        sage: C(1/3)
        0.3333333333333334?
        sage: S = PolynomialRing(Q, 'x')
        sage: C(S.gen())
        Traceback (most recent call last):
        ...
        TypeError: unable to coerce to a ComplexIntervalFieldElement

    This illustrates precision.
        sage: CIF = ComplexIntervalField(10); CIF(1/3, 2/3)
        0.334? + 0.667?*I
        sage: CIF
        Complex Interval Field with 10 bits of precision
        sage: CIF = ComplexIntervalField(100); CIF
        Complex Interval Field with 100 bits of precision
        sage: z = CIF(1/3, 2/3); z
        0.333333333333333333333333333334? + 0.666666666666666666666666666667?*I

    We can load and save complex numbers and the complex field.
        sage: cmp(loads(z.dumps()), z)
        0
        sage: loads(CIF.dumps()) == CIF
        True
        sage: k = ComplexIntervalField(100)
        sage: loads(dumps(k)) == k
        True

    This illustrates basic properties of a complex field.
        sage: CIF = ComplexIntervalField(200)
        sage: CIF.is_field()
        True
        sage: CIF.characteristic()
        0
        sage: CIF.precision()
        200
        sage: CIF.variable_name()
        'I'
        sage: CIF == ComplexIntervalField(200)
        True
        sage: CIF == ComplexIntervalField(53)
        False
        sage: CIF == 1.1
        False
        sage: CIF = ComplexIntervalField(53)

        sage: CIF.category()
        Category of fields
        sage: TestSuite(CIF).run()
    """
    def __init__(self, prec=53):
        self._prec = int(prec)
        from sage.categories.fields import Fields
        ParentWithGens.__init__(self, self._real_field(), ('I',), False, category = Fields())

    def __reduce__(self):
        """
        Used for pickling.

        TESTS::
            loads(dumps(CIF)) == CIF
        """
        return ComplexIntervalField, (self._prec, )

    def is_exact(self):
        """
        The complex interval field is not exact.

        EXAMPLES::

            sage: CIF.is_exact()
            False
        """
        return False

    def prec(self):
        """
        Returns the precision of self (in bits).

        EXAMPLES::

            sage: CIF.prec()
            53
            sage: ComplexIntervalField(200).prec()
            200
        """
        return self._prec

    def to_prec(self, prec):
        """
        Returns a complex interval field with the given precision.

        EXAMPLES::

            sage: CIF.to_prec(150)
            Complex Interval Field with 150 bits of precision
            sage: CIF.to_prec(15)
            Complex Interval Field with 15 bits of precision
            sage: CIF.to_prec(53) is CIF
            True
        """
        return ComplexIntervalField(prec)

    def _magma_init_(self, magma):
        r"""
        Return a string representation of self in the Magma language.

        EXAMPLES:
            sage: magma(ComplexIntervalField(100)) # optional - magma
            Complex field of precision 30
            sage: floor(RR(log(2**100, 10)))
            30
        """
        return "ComplexField(%s : Bits := true)" % self.prec()

    def _sage_input_(self, sib, coerce):
        r"""
        Produce an expression which will reproduce this value when evaluated.

        EXAMPLES:
            sage: sage_input(CIF, verify=True)
            # Verified
            CIF
            sage: sage_input(ComplexIntervalField(25), verify=True)
            # Verified
            ComplexIntervalField(25)
            sage: k = (CIF, ComplexIntervalField(37), ComplexIntervalField(1024))
            sage: sage_input(k, verify=True)
            # Verified
            (CIF, ComplexIntervalField(37), ComplexIntervalField(1024))
            sage: sage_input((k, k), verify=True)
            # Verified
            CIF37 = ComplexIntervalField(37)
            CIF1024 = ComplexIntervalField(1024)
            ((CIF, CIF37, CIF1024), (CIF, CIF37, CIF1024))
            sage: from sage.misc.sage_input import SageInputBuilder
            sage: ComplexIntervalField(2)._sage_input_(SageInputBuilder(), False)
            {call: {atomic:ComplexIntervalField}({atomic:2})}
        """
        if self.prec() == 53:
            return sib.name('CIF')

        v = sib.name('ComplexIntervalField')(sib.int(self.prec()))
        name = 'CIF%d' % self.prec()
        sib.cache(self, v, name)
        return v

    precision = prec


    # very useful to cache this.
    def _real_field(self):
        try:
            return self.__real_field
        except AttributeError:
            self.__real_field = real_mpfi.RealIntervalField(self._prec)
            return self.__real_field

    def _middle_field(self):
        try:
            return self.__middle_field
        except AttributeError:
            self.__middle_field = complex_field.ComplexField(self._prec)
            return self.__middle_field

    def __cmp__(self, other):
        if not isinstance(other, ComplexIntervalField_class):
            return cmp(type(self), type(other))
        return cmp(self._prec, other._prec)

    def __call__(self, x, im=None):
        """
        EXAMPLES:
            sage: CIF(2)
            2
            sage: CIF(CIF.0)
            1*I
            sage: CIF('1+I')
            1 + 1*I
            sage: CIF(2,3)
            2 + 3*I
            sage: CIF(pi, e)
            3.141592653589794? + 2.718281828459046?*I
        """
        if im is None:
            if isinstance(x, complex_interval.ComplexIntervalFieldElement) and x.parent() is self:
                return x
            elif isinstance(x, complex_double.ComplexDoubleElement):
                return complex_interval.ComplexIntervalFieldElement(self, x.real(), x.imag())
            elif isinstance(x, str):
                # TODO: this is probably not the best and most
                # efficient way to do this.  -- Martin Albrecht
                return complex_interval.ComplexIntervalFieldElement(self,
                            sage_eval(x.replace(' ',''), locals={"I":self.gen(),"i":self.gen()}))

            late_import()
            if isinstance(x, NumberFieldElement_quadratic) and list(x.parent().polynomial()) == [1, 0, 1]:
                (re, im) = list(x)
                return complex_interval.ComplexIntervalFieldElement(self, re, im)

            try:
                return x._complex_mpfi_( self )
            except AttributeError:
                pass
            try:
                return x._complex_mpfr_field_( self )
            except AttributeError:
                pass
        return complex_interval.ComplexIntervalFieldElement(self, x, im)

    def _coerce_impl(self, x):
        """
        Return the canonical coerce of x into this complex field, if it is defined,
        otherwise raise a TypeError.

        The rings that canonically coerce to the MPFI complex field are:
           * this MPFI complex field, or any other of higher precision
           * anything that canonically coerces to the mpfi real field with this prec
        """
        try:
            K = x.parent()
            if is_ComplexIntervalField(K) and K._prec >= self._prec:
                return self(x)
#            elif complex_field.is_ComplexField(K) and K.prec() >= self._prec:
#                return self(x)
        except AttributeError:
            pass
        if hasattr(x, '_complex_mpfr_field_') or hasattr(x, '_complex_mpfi_'):
            return self(x)
        return self._coerce_try(x, self._real_field())

    def _repr_(self):
        return "Complex Interval Field with %s bits of precision"%self._prec

    def _latex_(self):
        return "\\Bold{C}"

    def characteristic(self):
        return integer.Integer(0)

    def gen(self, n=0):
        if n != 0:
            raise IndexError, "n must be 0"
        return complex_interval.ComplexIntervalFieldElement(self, 0, 1)

    def random_element(self, *args, **kwds):
        """
        Create a random element of self. Simply chooses the real and
        imaginary part randomly, passing arguments and keywords to the
        underlying real interval field.

        EXAMPLES::

            sage: CIF.random_element()
            -0.30607732607725314? - 0.075929193054320221?*I
            sage: CIF.random_element(10, 20)
            10.809593725498833? + 13.964968616713041?*I

        Passes extra positional or keyword arguments through::

            sage: CIF.random_element(max=0, min=-5)
            -4.3945698326594416? - 3.8270855512644575?*I
        """
        return self._real_field().random_element(*args, **kwds) \
            + self.gen() * self._real_field().random_element(*args, **kwds)

    def is_field(self, proof = True):
        """
        Return True, since the complex numbers are a field.

        EXAMPLES:
            sage: CIF.is_field()
            True
        """
        return True

    def is_finite(self):
        """
        Return False, since the complex numbers are infinite.

        EXAMPLES:
            sage: CIF.is_finite()
            False
        """
        return False

    def pi(self):
        return self(self._real_field().pi())

    def ngens(self):
        return 1

    def zeta(self, n=2):
        """
        Return a primitive $n$-th root of unity.

        INPUT:
            n -- an integer (default: 2)

        OUTPUT:
            a complex n-th root of unity.
        """
        from integer import Integer
        n = Integer(n)
        if n == 1:
            x = self(1)
        elif n == 2:
            x = self(-1)
        elif n >= 3:
            # Use De Moivre
            # e^(2*pi*i/n) = cos(2pi/n) + i *sin(2pi/n)
            RR = self._real_field()
            pi = RR.pi()
            z = 2*pi/n
            x = complex_interval.ComplexIntervalFieldElement(self, z.cos(), z.sin())
        x._set_multiplicative_order( n )
        return x

    def scientific_notation(self, status=None):
        return self._real_field().scientific_notation(status)


