r"""
Error Functions

This module provides symbolic error functions. These functions use the
`mpmath library` for numerical evaluation and Maxima, Pynac for
symbolics.

The main objects which are exported from this module are:

 * :meth:`erf <Function_erf>` -- The error function
 * :meth:`erfc <Function_erfc>` -- The complementary error function
 * :meth:`erfi <Function_erfi>` -- The imaginary error function
 * :meth:`erfinv <Function_erfinv>` -- The inverse error function
 * :meth:`fresnel_sin <Function_Fresnel_sin>` -- The Fresnel integral `S(x)`
 * :meth:`fresnel_cos <Function_Fresnel_cos>` -- The Fresnel integral `C(x)`

AUTHORS:

 * Original authors ``erf``/``error_fcn`` (c) 2006-2014:
   Karl-Dieter Crisman, Benjamin Jones, Mike Hansen, William Stein,
   Burcin Erocal, Jeroen Demeyer, W. D. Joyner, R. Andrew Ohana
 * Reorganisation in new file, addition of ``erfi``/``erfinv``/``erfc``
   (c) 2016: Ralf Stephan
 * Fresnel integrals (c) 2017 Marcelo Forets

REFERENCES:

- [DLMF-Error]_

- [WP-Error]_
"""

# ****************************************************************************
#       Copyright (C) 2016 Ralf Stephan <gtrwst9 at gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#                  https://www.gnu.org/licenses/
# ****************************************************************************

from sage.structure.all import parent as s_parent
from sage.symbolic.function import BuiltinFunction
from sage.libs.mpmath import utils as mpmath_utils
from sage.symbolic.expression import Expression
from sage.functions.all import sqrt, exp
from sage.symbolic.constants import pi
from sage.rings.rational import Rational
from sage.rings.infinity import unsigned_infinity
from sage.symbolic.expression import I

class Function_erf(BuiltinFunction):
    r"""
    The error function.

    The error function is defined for real values as

    .. MATH::

        \operatorname{erf}(x) = \frac{2}{\sqrt{\pi}} \int_0^x e^{-t^2} dt.

    This function is also defined for complex values, via analytic
    continuation.

    EXAMPLES:

    We can evaluate numerically::

        sage: erf(2)
        erf(2)
        sage: erf(2).n()
        0.995322265018953
        sage: erf(2).n(100)
        0.99532226501895273416206925637
        sage: erf(ComplexField(100)(2+3j))
        -20.829461427614568389103088452 + 8.6873182714701631444280787545*I

    Basic symbolic properties are handled by Sage and Maxima::

        sage: x = var("x")
        sage: diff(erf(x),x)
        2*e^(-x^2)/sqrt(pi)
        sage: integrate(erf(x),x)
        x*erf(x) + e^(-x^2)/sqrt(pi)

    ALGORITHM:

    Sage implements numerical evaluation of the error function via the
    ``erf()`` function from mpmath. Symbolics are handled by Sage and Maxima.

    REFERENCES:

    - :wikipedia:`Error_function`
    - http://mpmath.googlecode.com/svn/trunk/doc/build/functions/expintegrals.html#error-functions

    TESTS:

    Check limits::

        sage: limit(erf(x),x=0)
        0
        sage: limit(erf(x),x=infinity)
        1

     Check that it's odd::

         sage: erf(1.0)
         0.842700792949715
         sage: erf(-1.0)
         -0.842700792949715

    Check against other implementations and against the definition::

        sage: erf(3).n()
        0.999977909503001
        sage: maxima.erf(3).n()
        0.999977909503001
        sage: (1-pari(3).erfc())
        0.999977909503001
        sage: RR(3).erf()
        0.999977909503001
        sage: (integrate(exp(-x**2),(x,0,3))*2/sqrt(pi)).n()
        0.999977909503001

    :trac:`9044`::

        sage: N(erf(sqrt(2)),200)
        0.95449973610364158559943472566693312505644755259664313203267

    :trac:`11626`::

        sage: n(erf(2),100)
        0.99532226501895273416206925637
        sage: erf(2).n(100)
        0.99532226501895273416206925637

    Test (indirectly) :trac:`11885`::

        sage: erf(float(0.5))
        0.5204998778130465
        sage: erf(complex(0.5))
        (0.5204998778130465+0j)

    Ensure conversion from maxima elements works::

        sage: merf = maxima(erf(x)).sage().operator()
        sage: merf.parent() == erf.parent()
        True

    Make sure we can dump and load it::

        sage: loads(dumps(erf(2)))
        erf(2)

    Special-case 0 for immediate evaluation::

        sage: erf(0)
        0
        sage: solve(erf(x)==0,x)
        [x == 0]

    Make sure that we can hold::

        sage: erf(0,hold=True)
        erf(0)
        sage: simplify(erf(0,hold=True))
        0

    Check that high-precision ComplexField inputs work::

        sage: CC(erf(ComplexField(1000)(2+3j)))
        -20.8294614276146 + 8.68731827147016*I
    """

    def __init__(self):
        r"""
        See docstring for :meth:`Function_erf`.

        EXAMPLES::

            sage: maxima(erf(2))
            erf(2)
            sage: erf(2)._sympy_()
            erf(2)
        """
        BuiltinFunction.__init__(self, "erf", latex_name=r"\operatorname{erf}",
                                 conversions=dict(maxima='erf',
                                                  sympy='erf',
                                                  fricas='erf',
                                                  giac='erf'))

    def _eval_(self, x):
        """
        EXAMPLES:

        Input is not an expression but is exact::

            sage: erf(0)
            0
            sage: erf(1)
            erf(1)
            sage: erf(oo)
            1
            sage: erf(SR(-oo))
            -1
            sage: erf(unsigned_infinity)
            Infinity

        Input is not an expression and is not exact::

            sage: erf(0.0)
            0.000000000000000

        Input is an expression but not a trivial zero::

            sage: erf(x)
            erf(x)

        Input is an expression which is trivially zero::

            sage: erf(SR(0))
            0
        """
        if isinstance(x, Expression):
            if x.is_trivial_zero():
                return x
            elif x.is_infinity():
                if x.is_positive_infinity():
                    return 1
                elif x.is_negative_infinity():
                    return -1
                else:
                    return unsigned_infinity
        elif not x:
            return x

    def _evalf_(self, x, parent=None, algorithm=None):
        """
        EXAMPLES::

            sage: erf(2).n()
            0.995322265018953
            sage: erf(2).n(200)
            0.99532226501895273416206925636725292861089179704006007673835
            sage: erf(pi - 1/2*I).n(100)
            1.0000111669099367825726058952 + 1.6332655417638522934072124547e-6*I

        TESTS:

        Check that PARI/GP through the GP interface gives the same answer::

            sage: gp.set_real_precision(59)  # random
            38
            sage: print(gp.eval("1 - erfc(1)")); print(erf(1).n(200))
            0.84270079294971486934122063508260925929606699796630290845994
            0.84270079294971486934122063508260925929606699796630290845994

        Check that for an imaginary input, the output is also imaginary, see
        :trac:`13193`::

            sage: erf(3.0*I)
            1629.99462260157*I
            sage: erf(33.0*I)
            1.51286977510409e471*I

        Check that real ball evaluation is fixed :trac:`28061`::

            sage: RealBallField(128)(erf(5))
            [0.99999999999846254020557196514981165651 +/- 7.33e-39]
        """
        R = parent or s_parent(x)
        import mpmath
        y = mpmath_utils.call(mpmath.erf, x, parent=R)
        return y

    def _derivative_(self, x, diff_param=None):
        """
        Derivative of erf function.

        EXAMPLES::

            sage: erf(x).diff(x)
            2*e^(-x^2)/sqrt(pi)

        TESTS:

        Check if :trac:`8568` is fixed::

            sage: var('c,x')
            (c, x)
            sage: derivative(erf(c*x),x)
            2*c*e^(-c^2*x^2)/sqrt(pi)
            sage: erf(c*x).diff(x)._maxima_init_()
            '((%pi)^(-1/2))*(_SAGE_VAR_c)*(exp(((_SAGE_VAR_c)^(2))*((_SAGE_VAR_x)^(2))*(-1)))*(2)'
        """
        return 2*exp(-x**2)/sqrt(pi)

erf = Function_erf()


class Function_erfi(BuiltinFunction):
    r"""
    The imaginary error function.

    The imaginary error function is defined by

    .. MATH::

        \operatorname{erfi}(x) = -i \operatorname{erf}(ix).
    """
    def __init__(self):
        r"""
        Initialize ``self``.

        EXAMPLES::

            sage: maxima(erfi(2))
            erfi(2)
            sage: erfi(2)._sympy_()
            erfi(2)
        """
        BuiltinFunction.__init__(self, "erfi",
                                 latex_name=r"\operatorname{erfi}",
                                 conversions=dict(maxima='erfi',
                                                  sympy='erfi',
                                                  fricas='erfi'))

    def _eval_(self, x):
        """
        EXAMPLES::

            sage: erfi(0)
            0
            sage: erfi(SR(0))
            0
            sage: erfi(oo)
            Infinity
            sage: erfi(SR(-oo))
            Infinity
        """
        if isinstance(x, Expression):
            if x.is_trivial_zero():
                return x
            elif x.is_infinity():
                return unsigned_infinity
        elif not x:
            return x

    def _evalf_(self, x, parent=None, algorithm=None):
        """
        EXAMPLES::

            sage: erfi(2.)
            18.5648024145756
            sage: erfi(2).n(100)
            18.564802414575552598704291913
            sage: erfi(-2*I).n(100)
            -0.99532226501895273416206925637*I
        """
        R = parent or s_parent(x)
        import mpmath
        return mpmath_utils.call(mpmath.erfi, x, parent=R)

    def _derivative_(self, x, diff_param=None):
        """
        Derivative of erfi function.

        EXAMPLES::

            sage: erfi(x).diff(x)
            2*e^(x^2)/sqrt(pi)

        """
        return 2*exp(x**2)/sqrt(pi)

erfi = Function_erfi()

class Function_erfc(BuiltinFunction):
    r"""
    The complementary error function.

    The complementary error function is defined by

    .. MATH::

        \frac{2}{\sqrt{\pi}} \int_t^\infty e^{-x^2} dx.

    EXAMPLES::

        sage: erfc(6)
        erfc(6)
        sage: erfc(6).n()
        2.15197367124989e-17
        sage: erfc(RealField(100)(1/2))
        0.47950012218695346231725334611

        sage: 1 - erfc(0.5)
        0.520499877813047
        sage: erf(0.5)
        0.520499877813047

    TESTS:

    Check that :trac:`25991` is fixed::

            sage: erfc(x)._fricas_()                                            # optional - fricas
            - erf(x) + 1

    """
    def __init__(self):
        r"""
        EXAMPLES::

            sage: maxima(erfc(2))
            erfc(2)
            sage: erfc(2)._sympy_()
            erfc(2)
        """
        BuiltinFunction.__init__(self, "erfc",
                                 latex_name=r"\operatorname{erfc}",
                                 conversions=dict(maxima='erfc',
                                                  sympy='erfc',
                                                  fricas='(x+->1-erf(x))',
                                                  giac='erfc'))

    def _eval_(self, x):
        """
        EXAMPLES::

            sage: erfc(0)
            1
            sage: erfc(SR(0))
            1
            sage: erfc(oo)
            0
            sage: erfc(SR(-oo))
            2
        """
        if isinstance(x, Expression):
            if x.is_trivial_zero():
                return 1
            elif x.is_infinity():
                if x.is_positive_infinity():
                    return 0
                elif x.is_negative_infinity():
                    return 2
                else:
                    return unsigned_infinity
        elif not x:
            return 1

    def _evalf_(self, x, parent=None, algorithm=None):
        """
        EXAMPLES::

            sage: erfc(4).n()
            1.54172579002800e-8
            sage: erfc(4).n(100)
            1.5417257900280018852159673487e-8
            sage: erfc(4*I).n(100)
            1.0000000000000000000000000000 - 1.2969597307176392315279409506e6*I
        """
        R = parent or s_parent(x)
        import mpmath
        return mpmath_utils.call(mpmath.erfc, x, parent=R)

    def _derivative_(self, x, diff_param=None):
        """
        Derivative of erfc function.

        EXAMPLES::

            sage: erfc(x).diff(x)
            -2*e^(-x^2)/sqrt(pi)
        """
        return -2*exp(-x**2)/sqrt(pi)

erfc = Function_erfc()


class Function_erfinv(BuiltinFunction):
    r"""
    The inverse error function.

    The inverse error function is defined by:

    .. MATH::

        \operatorname{erfinv}(x) = \operatorname{erf}^{-1}(x).
    """
    def __init__(self):
        r"""
        Initialize ``self``.

        EXAMPLES::

            sage: erfinv(2)._sympy_()
            erfinv(2)
            sage: maxima(erfinv(2))
            inverse_erf(2)

        TESTS:

        Check that :trac:`11349` is fixed::

            sage: _ = var('z,t')
            sage: PDF = exp(-x^2 /2)/sqrt(2*pi)
            sage: integralExpr = integrate(PDF,x,z,oo).subs(z==log(t))
            sage: y = solve(integralExpr==z,t)[0].rhs().subs(z==1/4)
            sage: y
            e^(sqrt(2)*erfinv(1/2))
            sage: y.n()
            1.96303108415826
        """
        BuiltinFunction.__init__(self, "erfinv",
                                 latex_name=r"\operatorname{erfinv}",
                                 conversions=dict(sympy='erfinv',
                                                  maxima='inverse_erf'))

    def _eval_(self, x):
        """
        EXAMPLES::

            sage: erfinv(0)
            0
            sage: erfinv(SR(0))
            0
            sage: erfinv(1)
            Infinity
        """
        if isinstance(x, Expression):
            if x.is_trivial_zero():
                return x
            elif (x-1).is_trivial_zero():
                return unsigned_infinity
        elif not x:
            return x
        elif x == 1:
            return unsigned_infinity

    def _evalf_(self, x, parent=None, algorithm=None):
        """
        EXAMPLES::

            sage: erfinv(0.2)
            0.179143454621292
            sage: erfinv(1/5).n(100)
            0.17914345462129167649274901663
        """
        R = parent or s_parent(x)
        import mpmath
        return mpmath_utils.call(mpmath.erfinv, x, parent=R)

    def _derivative_(self, x, diff_param=None):
        """
        Derivative of inverse erf function.

        EXAMPLES::

            sage: erfinv(x).diff(x)
            1/2*sqrt(pi)*e^(erfinv(x)^2)
        """
        return sqrt(pi)*exp(erfinv(x)**2)/2

erfinv = Function_erfinv()

from sage.misc.persist import register_unpickle_override
register_unpickle_override('sage.functions.other', 'Function_erf', Function_erf)

############################
# Fresnel integrals        #
############################
class Function_Fresnel_sin(BuiltinFunction):
    def __init__(self):
        r"""
        The sine Fresnel integral.

        It is defined by the integral

        .. MATH ::

            \operatorname{S}(x) = \int_0^x \sin\left(\frac{\pi t^2}{2}\right)\, dt

        for real `x`. Using power series expansions, it can be extended to the
        domain of complex numbers. See the :wikipedia:`Fresnel_integral`.

        INPUT:

        - ``x`` -- the argument of the function

        EXAMPLES::

            sage: fresnel_sin(0)
            0
            sage: fresnel_sin(x).subs(x==0)
            0
            sage: x = var('x')
            sage: fresnel_sin(1).n(100)
            0.43825914739035476607675669662
            sage: fresnel_sin(x)._sympy_()
            fresnels(x)
        """
        BuiltinFunction.__init__(self, "fresnel_sin", nargs=1,
                                 latex_name=r"\operatorname{S}",
                                 conversions=dict(maxima='fresnel_s',
                                                  sympy='fresnels',
                                                  mathematica='FresnelS',
                                                  maple='FresnelS',
                                                  fricas='fresnelS'))

    def _eval_(self, x):
        r"""
        EXAMPLES::

            sage: fresnel_sin(pi)
            fresnel_sin(pi)
            sage: fresnel_sin(oo)
            1/2
            sage: fresnel_sin(-oo)
            -1/2
            sage: fresnel_sin(I*oo)
            -1/2*I
            sage: fresnel_sin(-I*oo)
            1/2*I
        """
        if isinstance(x, Expression):
            if x.is_negative():
                return -fresnel_sin(-x)
            if x.is_trivial_zero():
                return x
            if x.is_infinity():
                if x.is_positive_infinity():
                    return Rational((1,2))
                elif x.imag_part().is_positive_infinity():
                    return -I*Rational((1,2))
                elif x.imag_part().is_negative_infinity():
                    return I*Rational((1,2))
        elif x < 0:
            return -fresnel_sin(-x)
        elif not x:
            return x

    def _evalf_(self, x, parent=None, algorithm=None):
        r"""
        EXAMPLES::

            sage: fresnel_sin(pi)
            fresnel_sin(pi)
            sage: fresnel_sin(pi).n(100)
            0.59824907809026766482843860921
            sage: fresnel_sin(1.0+2*I)
            36.7254648839914 + 15.5877511044046*I
        """
        import mpmath
        from sage.libs.mpmath import utils as mpmath_utils
        return mpmath_utils.call(mpmath.fresnels, x, parent=parent)

    def _derivative_(self, x, diff_param=None):
        """
        EXAMPLES::

            sage: x = var('x')
            sage: fresnel_sin(x).diff(x)
            sin(1/2*pi*x^2)
        """
        from sage.functions.trig import sin
        return sin(pi*x**2/2)

fresnel_sin = Function_Fresnel_sin()

class Function_Fresnel_cos(BuiltinFunction):
    def __init__(self):
        r"""
        The cosine Fresnel integral.

        It is defined by the integral

        .. MATH ::

            \operatorname{C}(x) = \int_0^x \cos\left(\frac{\pi t^2}{2}\right)\, dt

        for real `x`. Using power series expansions, it can be extended to the
        domain of complex numbers. See the :wikipedia:`Fresnel_integral`.

        INPUT:

        - ``x`` -- the argument of the function

        EXAMPLES::

            sage: fresnel_cos(0)
            0
            sage: fresnel_cos(x).subs(x==0)
            0
            sage: x = var('x')
            sage: fresnel_cos(1).n(100)
            0.77989340037682282947420641365
            sage: fresnel_cos(x)._sympy_()
            fresnelc(x)
        """
        BuiltinFunction.__init__(self, "fresnel_cos", nargs=1,
                                 latex_name=r"\operatorname{C}",
                                 conversions=dict(maxima='fresnel_c',
                                                  sympy='fresnelc',
                                                  mathematica='FresnelC',
                                                  maple='FresnelC',
                                                  fricas='fresnelC'))

    def _eval_(self, x):
        r"""
        EXAMPLES::

            sage: fresnel_cos(pi)
            fresnel_cos(pi)
            sage: fresnel_cos(oo)
            1/2
            sage: fresnel_cos(-oo)
            -1/2
            sage: fresnel_cos(I*oo)
            1/2*I
            sage: fresnel_cos(-I*oo)
            -1/2*I
        """
        if isinstance(x, Expression):
            if x.is_negative():
                return -fresnel_cos(-x)
            if x.is_trivial_zero():
                return x
            if x.is_infinity():
                if x.is_positive_infinity():
                    return Rational((1,2))
                elif x.imag_part().is_positive_infinity():
                    return I*Rational((1,2))
                elif x.imag_part().is_negative_infinity():
                    return -I*Rational((1,2))
        elif x < 0:
            return -fresnel_cos(-x)
        elif not x:
            return x

    def _evalf_(self, x, parent=None, algorithm=None):
        r"""
        EXAMPLES::

            sage: fresnel_cos(pi)
            fresnel_cos(pi)
            sage: fresnel_cos(pi).n(100)
            0.52369854372622864215767570284
            sage: fresnel_cos(1.0+2*I)
            16.0878713741255 - 36.2256879928817*I
        """
        import mpmath
        from sage.libs.mpmath import utils as mpmath_utils
        return mpmath_utils.call(mpmath.fresnelc, x, parent=parent)

    def _derivative_(self, x, diff_param=None):
        """
        EXAMPLES::

            sage: x = var('x')
            sage: fresnel_cos(x).diff(x)
            cos(1/2*pi*x^2)
        """
        from sage.functions.trig import cos
        return cos(pi*x**2/2)

fresnel_cos = Function_Fresnel_cos()
