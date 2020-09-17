#!/usr/bin/env python3
#
# (c) 2020 Yoichi Tanibayashi
#
import inkex
from lxml import etree
import math

class Point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def distance(self, c):
        return math.sqrt((c.x - self.x) ** 2 + (c.y - self.y) ** 2)

    def rotate(self, rad):
        new_x = math.cos(rad) * self.x - math.sin(rad) * self.y
        new_y = math.sin(rad) * self.x + math.cos(rad) * self.y
        self.x = new_x
        self.y = new_y
        return self

    def mirror(self):
        self.x = -self.x
        return self


class Vpoint(Point):
    '''
    A point with (x, y) coordinates and direction (rad)

    rad: Direction (true up: 0, right: math.pi / 2, ...)
    '''
    def __init__(self, x, y, rad=0):
        super(Vpoint, self).__init__(x, y)
        self.rad = rad

    def rotate(self, rad):
        super(Vpoint, self).rotate(rad)
        self.rad += rad
        return self

    def mirror(self):
        super(Vpoint, self).mirror()
        self.rad = -self.rad
        return self


class SvgObj(object):
    DEF_COLOR = '#00FF00'
    DEF_STROKE_WIDTH = 0.2
    DEF_STROKE_DASHARRAY = 'none'

    def __init__(self, parent):
        self.parent = parent
        self.type = None
        self.attr = {}

    def draw(self, color=DEF_COLOR,
             stroke_width=DEF_STROKE_WIDTH,
             stroke_dasharray=DEF_STROKE_DASHARRAY):

        self.attr['style'] = str(inkex.Style({
            'stroke': str(color),
            'stroke-width': str(stroke_width),
            'stroke-dasharray': str(stroke_dasharray),
            'fill': 'none'}))
        return etree.SubElement(self.parent,
                                      inkex.addNS(self.type, 'svg'),
                                      self.attr)


class SvgCircle(SvgObj):
    DEF_COLOR = '#FF0000'
    DEF_STROKE_WIDTH = 0.2
    DEF_STROKE_DASHARRAY = 'none'

    def __init__(self, parent, r):
        super(SvgCircle, self).__init__(parent)
        self.r = r
        self.type = 'circle'

    def draw(self, point,
             color=DEF_COLOR,
             stroke_width=DEF_STROKE_WIDTH,
             stroke_dasharray=DEF_STROKE_DASHARRAY):
        self.attr['cx'] = str(point.x)
        self.attr['cy'] = str(point.y)
        self.attr['r'] = str(self.r)

        return super(SvgCircle, self).draw(color,
                                           stroke_width, stroke_dasharray)


class SvgPath(SvgObj):
    DEF_COLOR = '#0000FF'
    DEF_STROKE_WIDTH = 0.2
    DEF_STROKE_DASHARRAY = 'none'

    def __init__(self, parent, points):
        super(SvgPath, self).__init__(parent)
        self.points = points
        self.type = 'path'

    def create_svg_d(self, origin_vpoint, points):
        '''
        to be override

        This is sample code.
        '''
        svg_d = ''
        for i, p in enumerate(points):
            (x1, y1) = (p.x + origin_vpoint.x, p.y + origin_vpoint.y)
            if i == 0:
                svg_d = 'M %f,%f' % (x1, y1)
            else:
                svg_d += ' L %f,%f' % (x1, y1)
        return svg_d

    def rotate(self, rad):
        for p in self.points:
            p.rotate(rad)
        return self

    def mirror(self):
        for p in self.points:
            p.mirror()
        return self

    def draw(self, origin,
             color=DEF_COLOR, stroke_width=DEF_STROKE_WIDTH,
             stroke_dasharray=DEF_STROKE_DASHARRAY):

        self.rotate(origin.rad)

        svg_d = self.create_svg_d(origin, self.points)
        # inkex.errormsg('svg_d=%s' % svg_d)
        # inkex.errormsg('svg_d=%s' % str(Path( svg_d )))

        self.attr['d'] = svg_d
        return super(SvgPath, self).draw(color, stroke_width, stroke_dasharray)


class SvgLine(SvgPath):
    # exactly same as SvgPath
    pass


class SvgPolygon(SvgPath):
    def create_svg_d(self, origin, points):
        svg_d = super(SvgPolygon, self).create_svg_d(origin, points)
        svg_d += ' Z'
        return svg_d


class SvgPart1Outline(SvgPolygon):
    def __init__(self, parent, points, bw_bf):
        super(SvgPart1Outline, self).__init__(parent, points)
        self.bw_bf = bw_bf

    def create_svg_d(self, origin, points, bw_bf=1):
        for i, p in enumerate(points):
            (x1, y1) = (p.x + origin.x, p.y + origin.y)
            if i == 0:
                d = 'M %f,%f' % (x1, y1)
            elif i == 7:
                d += ' L %f,%f' % (x1, y1)
                x2 = x1
                y2 = y1 + self.bw_bf
            elif i == 8:
                d += ' C %f,%f %f,%f %f,%f' % (x2, y2, x1, y2, x1, y1)
            else:
                d += ' L %f,%f' % (x1, y1)

        d += ' Z'
        return d


class SvgNeedleHole(SvgPolygon):
    def __init__(self, parent, w, h, tf):
        '''
        w: width
        h: height
        tf: tilt factor
        '''
        self.w = w
        self.h = h
        self.tf = tf

        self.gen_points(self.w, self.h, self.tf)
        super(SvgNeedleHole, self).__init__(parent, self.points)

    def gen_points(self, w, h, tf):
        self.points = []
        self.points.append(Point(-w / 2,  h * tf))
        self.points.append(Point( w / 2,  h * (1 - tf)))
        self.points.append(Point( w / 2, -h * tf))
        self.points.append(Point(-w / 2, -h * (1 - tf)))


class Part1(object):
    def __init__(self, parent,
                 w1, w2, h1, h2, bw, bl, bf, dia1, d1, d2,
                 needle_w, needle_h, needle_tf, needle_corner_rotation):
        self.parent = parent
        self.w1 = w1
        self.w2 = w2
        self.h1 = h1
        self.h2 = h2
        self.bw = bw
        self.bl = bl
        self.bf = bf
        self.dia1 = dia1
        self.d1 = d1
        self.d2 = d2
        self.needle_w = needle_w
        self.needle_h = needle_h
        self.needle_tf = needle_tf
        self.needle_corner_rotation = needle_corner_rotation

        # Group Creation
        attr = {inkex.addNS('label', 'inkscape'): 'Part1'}
        self.g = etree.SubElement(self.parent, 'g', attr)

        # drawing
        self.points_outline = self.create_points_outline()
        self.svg_outline = SvgPart1Outline(self.g, self.points_outline,
                                           (self.bw * self.bf))
        self.svg_hole = SvgCircle(self.g, self.dia1 / 2)

        self.vpoints_needle = self.create_needle_vpoints()
        self.svgs_needle_hole = []
        for v in self.vpoints_needle:
            svg_nh = SvgNeedleHole(self.g,
                                   self.needle_w,
                                   self.needle_h,
                                   self.needle_tf)
            self.svgs_needle_hole.append((svg_nh, v))

    def create_points_outline(self):
        #Generate the coordinates of the outer frame

        points = []
        (x0, y0) = (-(self.w2 / 2), 0)

        (x, y) = (x0, y0 + self.h1 + self.h2)
        points.append(Point(x, y))

        y = y0 + self.h1
        points.append(Point(x, y))

        x = -(self.w1 / 2)
        y = y0
        points.append(Point(x, y))

        x = self.w1 / 2
        points.append(Point(x, y))

        x = self.w2 / 2
        y += self.h1
        points.append(Point(x, y))

        y += self.h2
        points.append(Point(x, y))

        x = self.bw / 2
        points.append(Point(x, y))

        y += self.bl - self.bw / 2
        points.append(Point(x, y))

        x = -(self.bw / 2)
        points.append(Point(x, y))

        y = y0 + self.h1 + self.h2
        points.append(Point(x, y))

        return points

    def create_needle_vpoints(self):
        '''
        針穴の点と方向を生成
        '''
        rad1 = math.atan((self.w2 - self.w1) / (2 * self.h1))
        rad1a = (math.pi - rad1) / 2
        a1 = self.d1 / math.tan(rad1a)

        rad2 = (math.pi / 2) - rad1
        rad2a = (math.pi - rad2) / 2
        a2 = self.d1 / math.tan(rad2a)

        #
        # summit
        #
        vpoints1 = []
        for i, p in enumerate(self.points_outline):
            (nx, ny) = (p.x, p.y)
            if i == 0:
                nx += self.d1
                ny -= self.d1 * 1.5
                vpoints1.append(Vpoint(nx, ny, 0))
            if i == 1:
                nx += self.d1
                ny += a1
                vpoints1.append(Vpoint(nx, ny, rad1))
            if i == 2:
                nx += a2
                ny += self.d1
                vpoints1.append(Vpoint(nx, ny, math.pi / 2))
            if i == 3:
                nx -= a2
                ny += self.d1
                vpoints1.append(Vpoint(nx, ny, (math.pi / 2) + rad2))
            if i == 4:
                nx -= self.d1
                ny += a1
                vpoints1.append(Vpoint(nx, ny, math.pi))
            if i == 5:
                nx -= self.d1
                ny -= self.d1 * 1.5
                vpoints1.append(Vpoint(nx, ny, math.pi))
            if i > 5:
                break

        # Generate a point that completes a vertex
        vpoints2 = []
        for i in range(len(vpoints1)-1):
            d = vpoints1[i].distance(vpoints1[i+1])
            n = int(abs(round(d / self.d2)))
            for p in self.split_vpoints(vpoints1[i], vpoints1[i+1], n):
                vpoints2.append(p)

        vpoints2.insert(0, vpoints1[0])
        return vpoints2

    def split_vpoints(self, v1, v2, n):
        #v1, v2 Generate a list by dividing the space between the two into n pieces

        if n == 0:
            return [v1]
        (dx, dy) = ((v2.x - v1.x) / n, (v2.y - v1.y) / n)

        v = []
        for i in range(n):
            v.append(Vpoint(v1.x + dx * (i + 1),
                            v1.y + dy * (i + 1),
                            v1.rad))
        if self.needle_corner_rotation:
            v[-1].rad = (v1.rad + v2.rad) / 2
        return v

    def draw(self, origin):
        origin_base = Vpoint(origin.x + self.w2 / 2,
                             origin.y,
                             origin.rad)
        self.svg_outline.draw(origin_base, color='#0000FF')

        x = origin.x + self.w2 / 2
        y = origin.y + self.h1 + self.h2 + self.bl - self.bw / 2
        origin_hole = Point(x, y)
        self.svg_hole.draw(origin_hole, color='#FF0000')

        for (svg_nh, p) in self.svgs_needle_hole:
            origin_nh = Vpoint(origin.x + p.x + self.w2 / 2,
                               origin.y + p.y,
                               p.rad)
            svg_nh.draw(origin_nh, color='#FF0000')


class Part2(object):
    def __init__(self, parent, part1, dia2):
        self.parent = parent
        self.part1 = part1
        self.dia2 = dia2

        # Group Creation
        attr = {inkex.addNS('label', 'inkscape'): 'Part2'}
        self.g = etree.SubElement(self.parent, 'g', attr)

        # outer frame > Mirroring the points_outline in Part1, and use the first six points.
        self.points_outline = []
        for i in range(6):
            self.points_outline.append(self.part1.points_outline[i].mirror())

        self.svg_outline = SvgPolygon(self.g, self.points_outline)

        # clasp
        self.svg_hole = SvgCircle(self.g, self.dia2 / 2)

        # pinhole -> Mirroring the vpoints_needle in Part1
        self.svgs_needle_hole = []
        for v in self.part1.vpoints_needle:
            v.mirror()
            # Mirror also SvgNeedleHole
            svg_nh = SvgNeedleHole(self.g,
                                   self.part1.needle_w,
                                   self.part1.needle_h,
                                   self.part1.needle_tf)
            svg_nh.mirror()
            self.svgs_needle_hole.append((svg_nh, v))

    def draw(self, origin):
        origin_base = Vpoint(origin.x + self.part1.w2 / 2,
                             origin.y, origin.rad)
        self.svg_outline.draw(origin_base, color='#0000FF')

        x = origin.x + self.part1.w2 / 2
        y = origin.y + self.part1.h1 + self.part1.h2
        y -= (self.svg_hole.r + self.part1.d1)
        origin_hole = Vpoint(x, y, origin.rad)
        self.svg_hole.draw(origin_hole, color='#FF0000')

        for (svg_nh, p) in self.svgs_needle_hole:
            origin_nh = Vpoint(origin.x + p.x + self.part1.w2 / 2,
                               origin.y + p.y,
                               p.rad)
            svg_nh.draw(origin_nh, color='#FF0000')


class PliersCover(inkex.Effect):
    DEF_OFFSET_X = 20
    DEF_OFFSET_Y = 20

    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument("--tabs")
        self.arg_parser.add_argument("--w1", type=float)
        self.arg_parser.add_argument("--w2", type=float)
        self.arg_parser.add_argument("--h1", type=float)
        self.arg_parser.add_argument("--h2", type=float)
        self.arg_parser.add_argument("--bw", type=float)
        self.arg_parser.add_argument("--bl", type=float)
        self.arg_parser.add_argument("--bf", type=float)
        self.arg_parser.add_argument("--dia1", type=float)
        self.arg_parser.add_argument("--dia2", type=float)
        self.arg_parser.add_argument("--d1", type=float)
        self.arg_parser.add_argument("--d2", type=float)
        self.arg_parser.add_argument("--needle_w", type=float)
        self.arg_parser.add_argument("--needle_h", type=float)
        self.arg_parser.add_argument("--needle_tf", type=float)
        self.arg_parser.add_argument("--needle_corner_rotation", type=inkex.Boolean, default=True)

    def effect(self):
        # inkex.errormsg('view_center=%s' % str(self.view_center))
        # inkex.errormsg('selected=%s' % str(self.selected))

        # parameters
        opt = self.options

        #
        # error check
        #
        if opt.w1 >= opt.w2:
            msg = "Error: w1(%d) > w2(%d) !" % (opt.w1, opt.w2)
            inkex.errormsg(msg)
            return

        if opt.dia1 >= opt.bw:
            msg = "Error: dia1(%d) >= bw(%d) !" % (opt.dia1, opt.bw)
            inkex.errormsg(msg)
            return

        #
        # draw
        #
        origin_vpoint = Vpoint(self.DEF_OFFSET_X, self.DEF_OFFSET_Y)

        # Group Creation
        attr = {inkex.addNS('label', 'inkscape'): 'PliersCover'}
        self.g = etree.SubElement(self.svg.get_current_layer(), 'g', attr)

        part1 = Part1(self.g,
                      opt.w1, opt.w2, opt.h1, opt.h2,
                      opt.bw, opt.bl, opt.bf, opt.dia1,
                      opt.d1, opt.d2,
                      opt.needle_w, opt.needle_h, opt.needle_tf,
                      opt.needle_corner_rotation)
        part1.draw(origin_vpoint)

        origin_vpoint.x += opt.w2 + 10

        part2 = Part2(self.g, part1, opt.dia2)
        part2.draw(origin_vpoint)

if __name__ == '__main__':
    PliersCover().run()