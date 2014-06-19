from itertools import product
from sage.structure.sage_object import SageObject
from sage.misc.package import is_package_installed
from sage.matrix.constructor import matrix
from parser import Parser
from player import _Player


class NormalFormGame(SageObject):
    r"""
    EXAMPLES:

    A basic 2-player game constructed from two matrices. ::

        sage: A = matrix([[1, 2], [3, 4]])
        sage: B = matrix([[3, 3], [1, 4]])
        sage: C = NormalFormGame([A, B])
        sage: C.obtain_Nash()
        [[[0.0, 1.0], [0.0, 1.0]]]

    """
    def __init__(self, arg1=None, arg2=None):

        self.players = []
        flag = 'n-player'
        if type(arg1) is list:
            matrices = arg1
            flag = 'two-matrix'
            if matrices[0].dimensions() != matrices[1].dimensions():
                raise ValueError("matrices must be the same size")
        # elif arg1 == 'bi-matrix':
        #     flag = arg1
        #     bimatrix = arg2
        elif arg1 == 'zero-sum':
            flag = 'two-matrix'
            matrices = [arg2]
            matrices.append(-arg2)

        if flag == 'two-matrix':
            self._two_matrix_game(matrices)
        # elif flag == 'bi-matrix':
        #     self._bimatrix_game(bimatrix)

    def _two_matrix_game(self, matrices):
        self.add_player(matrices[0].dimensions()[0])
        self.add_player(matrices[1].dimensions()[1])
        for key in self.strategy_profiles:
            self.strategy_profiles[key] = (matrices[0][key], matrices[1][key])

    # def _bimatrix_game(self, bimatrix):
    #     self.add_player(bimatrix.dimensions()[0])
    #     self.add_player(bimatrix.dimensions()[1])
    #     for key in self.strategy_profiles:
    #         self.strategy_profiles[key] = bimatrix[key]

    def add_player(self, num_strategies):
        self.players.append(_Player(num_strategies))
        self.generate_strategy_profiles()

    def generate_strategy_profiles(self):
        self.strategy_profiles = {}
        strategy_sizes = [range(p.num_strategies) for p in self.players]
        for profile in product(*strategy_sizes):
            self.strategy_profiles[profile] = False

    def add_strategy(self, player):
        self.players[player].add_strategy()
        self.generate_strategy_profiles()

    def define_utility_vector(self, strategy_profile, utility_vector):
        self.strategy_profiles[strategy_profile] = utility_vector

    def _is_complete(self):
        return all(self.strategy_profiles.values())

    def obtain_Nash(self, algorithm="LCP", maximization=True):
        if len(self.players) > 2:
            raise NotImplementedError("Nash equilibrium for games with more "
                                      "than 2 players have not been "
                                      "implemented yet. Please see the gambit "
                                      "website [LINK] that has a variety of "
                                      "available algorithms")

        if not self._is_complete():
            raise ValueError("strategy_profiles hasn't been populated")

        if algorithm == "LCP":
            return self._solve_LCP(maximization)

        if algorithm == "lrs":
            if not is_package_installed('lrs'):
                raise NotImplementedError("lrs is not installed")
            m1, m2 = self._game_two_matrix()
            if maximization is False:
                min1 = - m1
                min2 = - m2
                nasheq = self._solve_lrs(min1, min2)
            else:
                nasheq = self._solve_lrs(m1, m2)
            return nasheq

    def _game_two_matrix(self):
        m1 = matrix(self.players[0].num_strategies, self.players[1].num_strategies)
        m2 = matrix(self.players[0].num_strategies, self.players[1].num_strategies)
        for key in self.strategy_profiles:
                m1[key] = self[key][0]
                m2[key] = self[key][1]
        return m1, m2

    def _solve_LCP(self, maximization):
        if not is_package_installed('gambit'):
                raise NotImplementedError("gambit is not installed")
        from gambit import Game
        from gambit.nash import ExternalLCPSolver
        strategy_sizes = [p.num_strategies for p in self.players]
        g = Game.new_table(strategy_sizes)
        for key in self.strategy_profiles:
            for player in range(len(self.players)):
                if maximization is False:
                    g[key][player] = - int(self.strategy_profiles[key][player])
                else:
                    g[key][player] = int(self.strategy_profiles[key][player])
        output = ExternalLCPSolver().solve(g)
        nasheq = Parser(output, g).format_gambit()
        return nasheq

    def _solve_lrs(self, m1, m2):
        r"""
        EXAMPLES:

        A simple game. ::

            sage: A = matrix([[1, 2], [3, 4]])
            sage: B = matrix([[3, 3], [1, 4]])
            sage: C = NormalFormGame([A, B])
            sage: C._solve_lrs(A, B)
            [([0, 1], [0, 1])]

        2 random matrices. ::

        sage: p1 = matrix([[-1, 4, 0, 2, 0],
        ....:              [-17, 246, -5, 1, -2],
        ....:              [0, 1, 1, -4, -4],
        ....:              [1, -3, 9, 6, -1],
        ....:              [2, 53, 0, -5, 0]])
        sage: p2 = matrix([[0, 1, 1, 3, 1],
        ....:              [3, 9, 44, -1, -1],
        ....:              [1, -4, -1, -3, 1],
        ....:              [1, 0, 1, 0, 0,],
        ....:              [1, -3, 1, 21, -2]])
        sage: biggame = NormalFormGame([p1, p2])
        sage: biggame._solve_lrs(p1, p2)
        [([0, 0, 0, 20/21, 1/21], [11/12, 0, 0, 1/12, 0]), ([0, 0, 0, 1, 0], [9/10, 0, 1/10, 0, 0])]
        """
        from sage.misc.temporary_file import tmp_filename
        from subprocess import Popen, PIPE
        # so that we don't call _Hrepresentation() twice.
        in_str = self._Hrepresentation(m1, m2)
        game1_str = in_str[0]
        game2_str = in_str[1]

        g1_name = tmp_filename()
        g2_name = tmp_filename()
        g1_file = file(g1_name, 'w')
        g2_file = file(g2_name, 'w')
        g1_file.write(game1_str)
        g1_file.close()
        g2_file.write(game2_str)
        g2_file.close()

        process = Popen(['nash', g1_name, g2_name], stdout=PIPE)
        lrs_output = [row for row in process.stdout]
        nasheq = Parser(lrs_output).format_lrs()
        return nasheq

    def _solve_enumeration(self):
        # call _is_complete()
        # write algorithm at some point
        pass

    def _Hrepresentation(self, m1, m2):
        r"""
        Creates the H-representation strings required to use lrs nash.

        EXAMPLES::

            sage: A = matrix([[1, 2], [3, 4]])
            sage: B = matrix([[3, 3], [1, 4]])
            sage: C = NormalFormGame([A, B])
            sage: print C._Hrepresentation(A, B)[0]
            H-representation
            linearity 1 5
            begin
            5 4 rational
            0 1 0 0
            0 0 1 0
            0 -3 -1 1
            0 -3 -4 1
            -1 1 1 0
            end
            <BLANKLINE>
            sage: print C._Hrepresentation(A, B)[1]
            H-representation
            linearity 1 5
            begin
            5 4 rational
            0 -1 -2 1
            0 -3 -4 1
            0 1 0 0
            0 0 1 0
            -1 1 1 0
            end
            <BLANKLINE>

        """
        from sage.geometry.polyhedron.misc import _to_space_separated_string
        m = self.players[0].num_strategies
        n = self.players[1].num_strategies
        midentity = list(matrix.identity(m))
        nidentity = list(matrix.identity(n))

        s = 'H-representation\n'
        s += 'linearity 1 ' + str(m + n + 1) + '\n'
        s += 'begin\n'
        s += str(m + n + 1) + ' ' + str(m + 2) + ' rational\n'
        for f in list(midentity):
            s += '0 ' + _to_space_separated_string(f) + ' 0 \n'
        for e in list(m2.transpose()):
            s += '0 ' + _to_space_separated_string(-e) + '  1 \n'
        s += '-1 '
        for g in range(m):
            s += '1 '
        s += '0 \n'
        s += 'end\n'

        t = 'H-representation\n'
        t += 'linearity 1 ' + str(m + n + 1) + '\n'
        t += 'begin\n'
        t += str(m + n + 1) + ' ' + str(n + 2) + ' rational\n'
        for e in list(m1):
            t += '0 ' + _to_space_separated_string(-e) + '  1 \n'
        for f in list(nidentity):
            t += '0 ' + _to_space_separated_string(f) + ' 0 \n'
        t += '-1 '
        for g in range(n):
            t += '1 '
        t += '0 \n'
        t += 'end\n'
        return s, t
