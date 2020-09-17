import unittest
import copy
import random

from plotink import plot_utils

from plotink.plot_utils_import import from_dependency_import

cspsubdiv = from_dependency_import('ink_extensions.cspsubdiv')

# python -m unittest discover in top-level package dir

class PlotUtilsTestCase(unittest.TestCase):

    def test_subdivideCubicPath_no_divisions(self):
        """ when applied to a straight line, there will be no subdivisions as the "curve"
        can be represented easily as only one/two segments """
        orig_beziers = [[(0,0), (0.5, 0.5), (1, 1)],
                        [(1.25, 1.25), (1.75, 1.75), (2, 2)]]
        processed_beziers = copy.deepcopy(orig_beziers)
        
        plot_utils.subdivideCubicPath(processed_beziers, 0)

        self.assertEqual(orig_beziers, processed_beziers)

    def test_subdivideCubicPath_divisions(self):
        orig_beziers = [[(1, 1), (2, 2), (0, 0)],
                        [(2, 2), (1, 1), (0, 0)]]
        processed_beziers = copy.deepcopy(orig_beziers)

        plot_utils.subdivideCubicPath(processed_beziers, .2)

        self.assertGreater(len(processed_beziers), len(orig_beziers))
        # but some things should not be modified
        self.assertEqual(orig_beziers[1][1:], processed_beziers[len(processed_beziers) - 1][1:])

    def test_max_dist_from_n_points_1(self):
        """ behavior for one point """
        input = [(0,0), (5,5), (10,0)]

        self.assertEqual(5, plot_utils.max_dist_from_n_points(input))

    def test_max_dist_from_n_points_2(self):
        """ check that the results are the same as the original maxdist """
        inputs = [self.get_random_points(4, i + .01) for i in range(5)]  # check a few possibilities

        for input in inputs:
            self.assertEqual(cspsubdiv.maxdist(input), plot_utils.max_dist_from_n_points(input))

    def test_max_dist_from_n_points_3(self):
        """ behavior for three points """
        input = [(0,0), (0, 3), (-4, 0), (4, -7), (10,0)]

        self.assertEqual(7, plot_utils.max_dist_from_n_points(input))

    def test_supersample_few_vertices(self):
        """ supersample returns the list of vertices unchanged if the list is too small (<= 2) """
        verticeses = [ self.get_random_points(i, i) for i in range(3) ] # inputs of size 1, 2, 3

        for orig_vertices in verticeses:
            processed_vertices = copy.deepcopy(orig_vertices)
            plot_utils.supersample(processed_vertices, 0)
            self.assertEqual(orig_vertices, processed_vertices)

    def test_supersample_no_deletions(self):
        orig_vertices = self.get_random_points(12, 1)
        tolerance = -1 # an impossibly low tolerance

        processed_vertices = copy.deepcopy(orig_vertices)
        plot_utils.supersample(processed_vertices, tolerance)
        self.assertEqual(orig_vertices, processed_vertices)

    def test_supersample_delete_one(self):
        tolerance = 1
        verticeses = [[(0, 0), (0, tolerance - .1), (2, 0)],
                      [(0, 0), (1, tolerance - .2), (2, 0), (3, tolerance + 20000), (4, 0)]]

        for orig_vertices in verticeses:
            processed_vertices = copy.deepcopy(orig_vertices)
            plot_utils.supersample(processed_vertices, tolerance)

            self.assertEqual(len(orig_vertices) - 1, len(processed_vertices), # removed one exactly
                             "Incorrect result: {}".format(processed_vertices))
            # other vertices stayed the same
            self.assertEqual(orig_vertices[0], processed_vertices[0])
            for i in range(2, len(orig_vertices)):
                self.assertEqual(orig_vertices[i], processed_vertices[i - 1])

    def test_supersample_delete_groups(self):
        tolerance = .05
        vertices = [(0, 10), (tolerance - .02, 9), (0, 8), # del 1
                         (1, 8), (2, 8 + tolerance / 2), (3, 8 + tolerance / 3), (4, 8), # del 3
                         (4, 7), (5, 7), (5, 6), # no deletions
                         (0, 0), (1, tolerance - .01), (2, 0)] # del 1 again

        expected_result = [(0, 10), (0, 8),
                           (4, 8),
                           (4, 7), (5, 7), (5, 6),
                           (0, 0), (2, 0)]

        plot_utils.supersample(vertices, tolerance)

        self.assertEqual(expected_result, vertices)


    def test_supersample_delete_all(self):
        verticeses = [self.get_random_points(i + 3, i + 1) for i in range(5)]
        tolerance = 100 # guaranteed to be higher than any of the distances

        for orig_vertices in verticeses:
            processed_vertices = copy.deepcopy(orig_vertices)
            plot_utils.supersample(processed_vertices, tolerance)

            self.assertEqual(2, len(processed_vertices), # deleted all but start and end
                             "Error for test case {}. Should be length 2, instead got {}"
                             .format(orig_vertices, processed_vertices))
            # start and end are the same
            self.assertEqual(orig_vertices[0], processed_vertices[0])
            self.assertEqual(orig_vertices[len(orig_vertices) - 1], processed_vertices[1])


    @staticmethod
    def get_random_points(num, seed=0):
        """ generate random (but deterministic) points where coords are between 0 and 1 """
        random.seed(seed)

        return [(random.random(), random.random()) for _ in range(num)]
