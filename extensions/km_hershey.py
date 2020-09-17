# coding=utf-8
#
# Copyright(C) 2020 -  Windell H. Oskay, www.evilmadscientist.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

'''
Hershey Text 3.0.4, 2020-06-01

Copyright 2020, Windell H. Oskay, www.evilmadscientist.com

Major revisions in Hershey Text 3.0:

1. Migrate font format to use SVG fonts.
    - SVG fonts support unicode, meaning that we can use a full range of
        characters. We are no longer limited to the ASCII range that the
        historical Hershey font formats used.
    - Arbitrary curves are supported within glyphs; we are no longer limited to
        the straight line segments used in the historical Hershey format.
    - The set of fonts can now be expanded.

2. Add a mechanism for adding your own SVG fonts, either within the
    folder containing the default fonts, or from an external file or directory.
    This is particularly important for installations where one does not
    have access to edit the contents of the Inkscape extensions directory.

3. Support font mapping: If a given font face is used for a given block of
    text, check first to see if a matching SVG font is present. If not,
    substitute with the default (selected) stroke font from the list of
    included fonts.

4. Instead of entering text (one line at a time) in the extension,
    this script now converts text (either all text, or all selected text)
    in the document, replacing it in place. While not every possible
    method of formatting text is supported, many are.

'''

import os
import math

from copy import deepcopy

import inkex
from inkex import Transform, Style, units

from inkex import load_svg, Group, TextElement, FlowPara, SVGfont, FontFace,\
    FlowSpan, Glyph, MissingGlyph, Tspan, FlowRoot, Rectangle, Use, PathElement, Defs


class Hershey(inkex.Effect):

    '''
    An extension for use with Inkscape 1.0
    '''

    def __init__(self):
        super(Hershey, self).__init__()

        self.arg_parser.add_argument("--tab", \
            dest="mode", \
            default="render", help="The active tab or mode when Apply was pressed")

        self.arg_parser.add_argument("--fontface", \
            dest="fontface", \
            default="HersheySans1", help="The selected font face when Apply was pressed")

        self.arg_parser.add_argument("--otherfont", \
            dest="otherfont", \
            default="", help="Optional other font name or path to use")

        self.arg_parser.add_argument("--preserve", \
            type=inkex.Boolean, dest="preserve_text", \
            default=False, help="Preserve original text")

        self.arg_parser.add_argument("--action", \
            dest="util_mode", \
            default="sample", help="The utility option selected")

        self.arg_parser.add_argument("--text", \
            dest="sample_text", \
            default="sample", help="Text to use for font table")

        self.font_file_list = dict()
        self.font_load_fail = False

        self.svg_height = None
        self.svg_width = None

        self.output_generated = False

        self.warn_unflow = False
        self.warn_textpath = False    # For future use: Give warning about text attached to path.
        self.font_dict = dict() # Font dictionary - Dictionary of loaded fonts

        self.nodes_to_delete = [] # List of font elements to remove

        self.vb_scale_factor = 0.0104166666

        self.text_string = ""
        self.text_families = [] # List of font family for characters in the string
        self.text_heights = []  # List of font heights
        self.text_spacings = [] # List of vertical line heights
        self.text_aligns = []   # List of horizontal alignment values
        self.text_x = []    #List; x-coordinate of text line start
        self.text_y = []    #List; y-coordinate of text line start
        self.line_number = 0
        self.new_line = True
        self.render_width = 1

    PX_PER_INCH = 96.0

    help_text = '''====== Hershey Text Help ======

The Hershey Text extension is designed to replace text in your document (either
selected text or all text) with specialized "stroke" or "engraving" fonts
designed for plotters.

Whereas regular "outline" fonts (e.g., TrueType) work by filling in the region
inside an invisible outline, stroke fonts are composed only of individual lines
or strokes with finite width; much like human handwriting when using a physical
pen.

Stroke fonts are most often used for creating text-like paths that computer
controlled drawing and cutting machines (from pen plotters to CNC routers) can
efficiently follow.

A full user guide for Hershey Text is available to download from
    http://wiki.evilmadscientist.com/hershey


   ==== Basic operation ====

To use Hershey Text, start with a document that contains text objects. Select
the "Render" tab of Hershey Text, and choose a font face from the pop-up menu.

When you click Apply, it will render all text elements on your page with the
selected stroke-based typeface. If you would like to convert only certain text
elements, click Apply with just those elements selected.

If the "Preserve original text" box is checked, then the original text elements
on the page will be preserved even when you click Apply. If it is unchecked,
then the original font elements will be removed once rendered.

You can generate a list of available SVG fonts or a list of all glyphs available
in a given font by using the tools available on the "Utilities" tab.


   ==== How Hershey Text works ====

Hershey Text works by performing font substitution, starting with the text in
your document and replacing it with paths generated from the characters in the
selected SVG font.

Hershey Text uses fonts in the SVG font format. While SVG fonts are one of the
few types that support stroke-based characters, it is important to note that
converting an outline font to SVG format does not convert it to a stroke based
font. Indeed, most SVG fonts are actually outline fonts.

This extension *does not* convert outline fonts into stroke fonts, nor does it
convert other fonts into SVG format. Its sole function is to replace the text
in your document with paths from the selected SVG font.


   ==== Using an external SVG font ====

To use an external SVG font -- one not included with the distribution -- select
"Other" for the name of the font in the pop-up menu on the "Render" tab. Then,
do one of the following:

(1) Add your SVG font file (perhaps "example.svg") to the "svg_fonts" directory
within your Inkscape extensions directory, and enter the name of the font
("example") in the "Other SVG font name or path" box on the "Render" tab.

or

(2) Place your SVG font file anywhere on your computer, and enter the full path
to the file  in the "Other SVG font name or path" box on the "Render" tab.
A full path might, for example, look like:
    /Users/Robin/Documents/AxiDraw/fonts/path_handwriting.svg


   ==== Using SVG fonts: Advanced methods ====

In addition to using a single SVG font for substitution, you can also use
font name mapping to automatically use particular stroke fonts in place of
specific font faces, to support various automated workflows and to support
the rapid use of multiple stroke font faces within the same document.

Several SVG fonts are included with this distribution, including both
single-stroke and multi-stroke fonts. These fonts are included within the
"svg_fonts" directory within your Inkscape extensions directory.

You can select the font that you would like to use from the pop-up menu on the
"Render" Tab. You can also make use of your own SVG fonts.

Order of preference for SVG fonts:

(1) If there is an SVG font with name matching that of the font for a given
piece of text, that font will be used. For example, if the original text is in
font "FancyScript" and there is a file in svg_fonts with name FancyScript.svg,
then FancyScript.svg will be used to render the text.

(2) Otherwise (if there is no SVG font available matching the name of the font
for a given block of text), the face selected from the "Font face" pop-up menu
will be used as the default font when rendering text with Hershey Text.

(3) You can also enter text in the "Name/Path" box, which can represent one of
the following: (i) a font name (for a font located in the svg_fonts directory),
(ii) the path to a font file elsewhere on your computer, or (iii) the path to a
directory containing (one or more) font files.

(3a) Using a font name:
If you move a custom SVG font file into your svg_fonts directory, then you can
enter the name of the SVG font in the "Name/Path" text box and select "Other"
from the pop-up menu. Then, the named font will be used as the default.

(3b) Using a file path:
If you enter the path to an SVG font file in the "Name/Path" text box and
select "Other" from the pop-up menu. Then, that font will be used as the
default. All SVG fonts located in the same directory as that font file will
also be available for name-based font substitution. If there are multiple
font-name matches, files in an external directory take precedence over ones in
the svg_fonts directory.

(3c) Using a directory path:
If you enter the path to a directory containing SVG font files in the
"Name/Path" text box, then all SVG font files files in that directory will be
available for name-based font substitution. If there are multiple font-name
matches, files in an external directory take precedence over ones in the
svg_fonts directory.



Tips about using these methods with your own custom fonts:

(A) These methods can be used to render different text elements with different
SVG font faces. You can even rename a font -- either your own custom one or one
of the bundled ones -- to match the name of a font that you're using. For
example, if you rename a script font you name a font to "Helvetica.svg",
then all text in Helvetica will be replaced with that SVG font.

(B) Using a directory path (3c) is a particularly helpful method if you do
not have access to modify the svg_fonts directory.



   ==== Limitations ====

This extension renders text into non-editable paths, generated from the
character geometry of SVG fonts. Once you have rendered the text, the resulting
paths can be edited with path editing tools, but not text editing tools.

Since this extension works by a process of font substitution, text spanning a
single line will generally stay that way, whereas text flowed in a box (that
may span multiple lines) will be re-flowed from scratch. Style information such
as text size and line spacing can be lost in some cases.

We recommend that you use the live preview option to achieve best results with
this extension.


(c) 2020 Windell H. Oskay
Evil Mad Scientist Laboratories
'''

    def getlength_inch(self, name):
        """
        Get the <svg> attribute with name "name", and parse it as a length,
        into a value and associated units. Return value in inches.

        This may cause scaling issues in some circumstances. Note, for
        example, that Adobe Illustrator uses 72 px per inch, and Inkscape
        used 90 px per inch prior to version 0.92.
        """
        string_to_parse = self.document.getroot().get(name)
        if string_to_parse:
            value, unit = units.parse_unit(string_to_parse)
            if value is None:
                return None
            bad_units = {'%', 'ex', 'em'} # Unsupported units
            if unit in bad_units:
                return None

            return units.convert_unit(string_to_parse, 'in')
        return None


    def units_to_userunits(self, input_string):
        """
        Custom replacement for the old "unittouu" routine

        Parse the attribute into a value and associated units.
        Return value in user units (typically "px").
        Importantly, return None for malformed inputs.
        """

        value, _ = units.parse_unit(input_string)
        if value is None:
            return None

        return units.convert_unit(input_string, '')


    def vb_scale(self, viewbox, p_a_r, doc_width, doc_height):
        """"
        Parse SVG viewbox and generate scaling parameters.
        Reference documentation: https://www.w3.org/TR/SVG11/coords.html

        Inputs:
            viewbox:         Contents of SVG viewbox attribute
            p_a_r:      Contents of SVG preserveAspectRatio attribute
            doc_width:  Width of SVG document
            doc_height: Height of SVG document

        Output: s_x, s_y, o_x, o_y
            Scale parameters (s_x, s_y) and offset parameters (o_x, o_y)

        """
        if viewbox is None:
            return 1, 1, 0, 0 # No viewbox; return default transform
        vb_array = viewbox.strip().replace(', ', ' ').split()

        if len(vb_array) < 4:
            return 1, 1, 0, 0 # invalid viewbox; return default transform

        min_x = float(vb_array[0]) # Viewbox offset: x
        min_y = float(vb_array[1]) # Viewbox offset: y
        width = float(vb_array[2]) # Viewbox width
        height = float(vb_array[3]) # Viewbox height

        if width <= 0 or height <= 0:
            return 1, 1, 0, 0 # invalid viewbox; return default transform

        d_width = float(doc_width)
        d_height = float(doc_height)

        if d_width <= 0 or d_height <= 0:
            return 1, 1, 0, 0 # invalid document size; return default transform

        ar_doc = d_height / d_width # Document aspect ratio
        ar_vb = height / width      # Viewbox aspect ratio

        # Default values of the two preserveAspectRatio parameters:
        par_align = "xmidymid" # "align" parameter(lowercased)
        par_mos = "meet"       # "meetOrSlice" parameter

        if p_a_r is not None:
            par_array = p_a_r.strip().replace(', ', ' ').lower().split()
            if len(par_array) > 0:
                par0 = par_array[0]
                if par0 == "defer":
                    if len(par_array) > 1:
                        par_align = par_array[1]
                        if len(par_array) > 2:
                            par_mos = par_array[2]
                else:
                    par_align = par0
                    if len(par_array) > 1:
                        par_mos = par_array[1]

        if par_align == "none":
            # Scale document to fill page. Do not preserve aspect ratio.
            # This is not default behavior, nor what happens if par_align
            # is not given; the "none" value must be _explicitly_ specified.

            s_x = d_width/ width
            s_y = d_height / height
            o_x = -min_x
            o_y = -min_y
            return s_x, s_y, o_x, o_y

        """
        Other than "none", all situations fall into two classes:

        1)  (ar_doc >= ar_vb AND par_mos == "meet")
               or (ar_doc < ar_vb AND par_mos == "slice")
            -> In these cases, scale document up until VB fills doc in X.

        2)   All other cases, i.e.,
           (ar_doc < ar_vb AND par_mos == "meet")
               or (ar_doc >= ar_vb AND par_mos == "slice")
            -> In these cases, scale document up until VB fills doc in Y.

        Note in cases where the scaled viewbox exceeds the document
        (page) boundaries (all "slice" cases and many "meet" cases where
        an offset value is given) that this routine does not perform
        any clipping, but subsequent clipping to the page boundary
        is appropriate.

        Besides "none", there are 9 possible values of par_align:
            xminymin xmidymin xmaxymin
            xminymid xmidymid xmaxymid
            xminymax xmidymax xmaxymax
        """

        if(((ar_doc >= ar_vb) and(par_mos == "meet"))
           or((ar_doc < ar_vb) and(par_mos == "slice"))):
            # Case 1: Scale document up until VB fills doc in X.

            s_x = d_width / width
            s_y = s_x # Uniform aspect ratio
            o_x = -min_x

            scaled_vb_height = ar_doc * width
            excess_height = scaled_vb_height - height

            if par_align in {"xminymin", "xmidymin", "xmaxymin"}:
                # Case: Y-Min: Align viewbox to minimum Y of the viewport.
                o_y = -min_y
                # OK: tested with Tall-Meet, Wide-Slice

            elif par_align in {"xminymax", "xmidymax", "xmaxymax"}:
                # Case: Y-Max: Align viewbox to maximum Y of the viewport.
                o_y = -min_y + excess_height
                #  OK: tested with Tall-Meet, Wide-Slice

            else: # par_align in {"xminymid", "xmidymid", "xmaxymid"}:
                # Default case: Y-Mid: Center viewbox on page in Y
                o_y = -min_y + excess_height / 2
                # OK: Tested with Tall-Meet, Wide-Slice

            return s_x, s_y, o_x, o_y

        # Case 2: Scale document up until VB fills doc in Y.

        s_y = d_height / height
        s_x = s_y # Uniform aspect ratio
        o_y = -min_y

        scaled_vb_width = height / ar_doc
        excess_width = scaled_vb_width - width

        if par_align in {"xminymin", "xminymid", "xminymax"}:
            # Case: X-Min: Align viewbox to minimum X of the viewport.
            o_x = -min_x
            # OK: Tested with Tall-Slice, Wide-Meet

        elif par_align in {"xmaxymin", "xmaxymid", "xmaxymax"}:
            # Case: X-Max: Align viewbox to maximum X of the viewport.
            o_x = -min_x + excess_width
            # Need test: Tall-Slice, Wide-Meet

        else: # par_align in {"xmidymin", "xmidymid", "xmidymax"}:
            # Default case: X-Mid: Center viewbox on page in X
            o_x = -min_x + excess_width / 2
            # OK: Tested with Tall-Slice, Wide-Meet

        return s_x, s_y, o_x, o_y


    def strip_quotes(self, fontname):
        '''
        A multi-word font name may have a leading and trailing
        single or double quotes, depending on the source.
        If so, remove those quotes.
        '''

        if fontname.startswith("'") and fontname.endswith("'"):
            return fontname[1:-1]
        if fontname.startswith('"') and fontname.endswith('"'):
            return fontname[1:-1]
        return fontname

    def parse_svg_font(self, node_list):
        '''
        Parse an input svg, searching for an SVG font. If an
        SVG font is found, parse it and return a "digest" containing
        structured information from the font. See below for more
        about the digest format.

        If the font is not found cannot be parsed, return none.

        Notable limitations:

       (1) This function only parses the first font face found within the
        tree. We may, in the future, support discovering multiple fonts
        within an SVG file.

       (2) We are only processing left-to-right and horizontal text,
        not vertical text nor RTL.

       (3) This function currently performs only certain recursive searches,
        within the <defs> element. It will not discover fonts nested within
        groups or other elements. So far as we know, that is not a limitation
        in practice. (If you have a counterexample please contact Evil Mad
        Scientist tech support and let us know!)

       (4) Kerning details are not implemented yet.
        '''

        digest = None

        if node_list is None:
            return None

        for node in node_list:
            if isinstance(node, Defs):
                return self.parse_svg_font(node) # Recursive call

            if isinstance(node, SVGfont):
                '''
                === Internal structure for storing font information ===

                We parse the SVG font file and create a keyed "digest"
                from it that we can use while rendering text on the page.

                This "digest" will be added to a dictionary that maps
                each font family name to a single digest.

                The digest itself is a dictionary with the following
                keys, some of which may have empty values. This format
                will allow us to add additional keys at a later date,
                to support additional SVG font features.

                    font_id (a string)

                    font_family (a string)

                    glyphs
                        A dictionary mapping unicode points to a specific
                        dictionary for each point.  See below for more about
                        the key format.
                        The dictionary for a given point will include keys:
                            glyph_name(string)
                            horiz_adv_x(numeric)
                            d(string)

                    missing_glyph
                        A dictionary for a single code point, with keys:
                            horiz_adv_x(numeric)
                            d(string)

                    geometry
                        A dictionary containing geometric data
                        Keys will include:
                            horiz_adv_x(numeric) -- Default value
                            units_per_em(numeric)
                            ascent(numeric)
                            descent(numeric)
                            x_height(numeric)
                            cap_height(numeric)
                            bbox (string)
                            underline_position(numeric)
                    scale
                        A numeric scaling factor computed from the
                        units_per_em value, which gives the overall scale
                '''

                digest = dict()
                geometry = dict()
                glyphs = dict()
                missing_glyph = dict()

                digest['font_id'] = node.get('id')

                horiz_adv_x = node.get('horiz-adv-x')

                if horiz_adv_x is not None:
                    geometry['horiz_adv_x'] = float(horiz_adv_x)
                # Note: case of no horiz_adv_x value is not handled.

                for element in node:

                    if isinstance(element, Glyph):
                        # First, because it is the most common element
                        try:
                            uni_text = element.get('unicode')
                        except:
                            # Can't use this point if no unicode mapping.
                            continue

                        if uni_text is None:
                            continue

                        if uni_text in glyphs:
                            # Skip if that unicode point is already in the
                            # list of glyphs.(There is not currently support
                            # for alternate glyphs in the font.)
                            continue

                        glyph_dict = dict()
                        glyph_dict['glyph_name'] = element.get('glyph-name')

                        horiz_adv_x = element.get('horiz-adv-x')

                        if horiz_adv_x is not None:
                            glyph_dict['horiz_adv_x'] = float(horiz_adv_x)
                        else:
                            glyph_dict['horiz_adv_x'] = geometry['horiz_adv_x']

                        glyph_dict['d'] = element.get('d') # SVG path data
                        glyphs[uni_text] = glyph_dict

                    elif isinstance(element, FontFace):
                        digest['font_family'] = element.get('font-family')
                        units_per_em = element.get('units-per-em')

                        if units_per_em is None:
                            # Default: 1000, per SVG specification.
                            geometry['units_per_em'] = 1000.0
                        else:
                            geometry['units_per_em'] = float(units_per_em)

                        ascent = element.get('ascent')
                        if ascent is not None:
                            geometry['ascent'] = float(ascent)

                        descent = element.get('descent')
                        if descent is not None:
                            geometry['descent'] = float(descent)

                        '''
                        # Skip these attributes that we are not currently using
                        geometry['x_height'] = element.get('x-height')
                        geometry['cap_height'] = element.get('cap-height')
                        geometry['bbox'] = element.get('bbox')
                        geometry['underline_position'] = element.get('underline-position')
                        '''

                    elif isinstance(element, MissingGlyph):
                        horiz_adv_x = element.get('horiz-adv-x')

                        if horiz_adv_x is not None:
                            missing_glyph['horiz_adv_x'] = float(horiz_adv_x)
                        else:
                            missing_glyph['horiz_adv_x'] = geometry['horiz_adv_x']

                        missing_glyph['d'] = element.get('d') # SVG path data
                        digest['missing_glyph'] = missing_glyph


                # Main scaling factor
                digest['scale'] = 1.0 /  geometry['units_per_em']

                digest['glyphs'] = glyphs
                digest['geometry'] = geometry

                return digest
        return None

    def load_font(self, fontname):
        '''
        Attempt to load an SVG font from a file in our list
        of (likely) SVG font files.
        If we can, add the contents to the font library.
        Otherwise, add a "None" entry to the font library.
        '''

        if fontname is None:
            return

        if fontname in self.font_dict:
            return # Awesome: The font is already loaded.

        if fontname in self.font_file_list:
            the_path = self.font_file_list[fontname]
        else:
            self.font_dict[fontname] = None
            return # Font not located.
        try:
            '''
            Check to see if there is an SVG font file for us to read.

            At present, only one font file will be read per font family;
            the name of the file must be FONT_NAME.svg, where FONT_NAME
            is the name of the font family.

            Only the first font found in the font file will be read.
            Multiple weights and styles within a font family are not
            presently supported.
            '''
            font_svg = load_svg(the_path)
            self.font_dict[fontname] = self.parse_svg_font(font_svg.getroot())

        except IOError:
            self.font_dict[fontname] = None
        except:
            inkex.errormsg('Error parsing SVG font at ' + str(the_path))
            self.font_dict[fontname] = None


    def font_table(self):
        '''
        Generate display table of all available SVG fonts
        '''

        self.options.preserve_text = False

        # Embed text in group to make manipulation easier:
        group = self.svg.get_current_layer().add(Group())
        for fontname in self.font_file_list:
            self.load_font(fontname)

        font_size = 0.2 # in inches -- will be scaled by viewbox factor.
        font_size_text = str(font_size / self.vb_scale_factor) + 'px'

        labeltext_style = str(Style({'stroke' : 'none', \
            'font-size':font_size_text, 'fill' : 'black', \
            'font-family' : 'sans-serif', 'text-anchor': 'end'}))

        x_offset = font_size / self.vb_scale_factor
        y_offset = 1.5 * x_offset
        y = y_offset

        for fontname in sorted(self.font_dict):
            if self.font_dict[fontname] is None:
                continue # If the SVG file did NOT contain a font, skip it.

            text_attribs = {'x':'0', 'y': str(y), 'hershey-ignore':'true'}
            textline = group.add(TextElement(**text_attribs))
            textline.text = fontname
            textline.style = labeltext_style
            text_attribs = {'x':str(x_offset), 'y': str(y)}

            sampletext_style = {'stroke' : 'none', \
                'font-size':font_size_text, \
                'fill' : 'black', 'font-family' : fontname, \
                'text-anchor': 'start'}
            sampleline = group.add(TextElement(**text_attribs))

            try: # python 2
                sampleline.text = self.options.sample_text.decode('utf-8')
            except AttributeError: # python 3
                sampleline.text = self.options.sample_text

            sampleline.style = sampletext_style
            y += y_offset
        self.recursively_traverse_svg(group, self.doc_transform)


    def glyph_table(self):
        '''
        Generate display table of glyphs within the current SVG font. Sorted display of
        all printable characters in the font _except_ missing glyph.
        '''

        self.options.preserve_text = False

        fontname = self.font_load_wrapper('not_a_font_name') # force load of default

        if self.font_load_fail:
            inkex.errormsg('Font not found; Unable to generate glyph table.')
            return

        # Embed in group to make manipulation easier:
        group = self.svg.get_current_layer().add(Group())

        # missing_glyph = self.font_dict[fontname]['missing_glyph']

        glyph_count = 0
        for glyph in self.font_dict[fontname]['glyphs']:
            if self.font_dict[fontname]['glyphs'][glyph]['d'] is not None:
                glyph_count += 1

        columns = int(math.floor(math.sqrt(glyph_count)))

        font_size = 0.4 # in inches -- will be scaled by viewbox factor.
        font_size_text = str(font_size / self.vb_scale_factor) + 'px'

        glyph_style = str(Style({'stroke' : 'none', \
            'font-size':font_size_text, 'fill' : 'black', \
            'font-family' : fontname, 'text-anchor': 'start'}))

        x_offset = 1.5 * font_size / self.vb_scale_factor
        y_offset = x_offset
        x = x_offset
        y = y_offset

        draw_position = 0

        for glyph in sorted(self.font_dict[fontname]['glyphs']):
            if self.font_dict[fontname]['glyphs'][glyph]['d'] is None:
                continue
            y_pos, x_pos = divmod(draw_position, columns)
            x = x_offset *(x_pos + 1)
            y = y_offset *(y_pos + 1)
            text_attribs = {'x':str(x), 'y': str(y)}
            sampleline = group.add(TextElement(**text_attribs))
            sampleline.text = glyph
            sampleline.style = glyph_style
            draw_position = draw_position + 1

        self.recursively_traverse_svg(group, self.doc_transform)


    def find_font_files(self):
        '''
        Create list of "plausible" SVG font files

        List items in primary svg_fonts directory, typically located in the
        directory where this script is being executed from.

        If there is text given in the "Other name/path" input, that text may
        represent one of the following:

       (A) The name of a font file, located in the svg_fonts directory.
            - This may be given with or without the .svg suffix.
            - If it is a font file, and the font face selected is "other",
                then use this as the default font face.

       (B) The path to a font file, located elsewhere.
            - If it is a font file, and the font face selected is "other",
                then use this as the default font face.
            - ALSO: Search the directory where that file is located for
                any other SVG fonts.

       (C) The path to a directory
            - It may or may not have a trailing separator
            - Search that directory for SVG fonts.

        This function will create a list of available files that
        appear to be SVG(SVG font) files. It does not parse the files.
        We will format it as a dictionary, that maps each file name
        (without extension) to a path.
        '''

        self.font_file_list = dict()

        # List contents of primary font directory:
        font_directory_name = 'svg_fonts'

        font_dir = os.path.realpath(
            os.path.join(os.getcwd(), font_directory_name))
        for dir_item in os.listdir(font_dir):
            if dir_item.endswith((".svg", ".SVG")):
                file_path = os.path.join(font_dir, dir_item)
                if os.path.isfile(file_path): # i.e., if not a directory
                    root, _ = os.path.splitext(dir_item)
                    self.font_file_list[root] = file_path

        # split off file extension(e.g., ".svg")
        root, _ = os.path.splitext(self.options.otherfont)

        # Check for case "(A)": Input text is the name
        # of an item in the primary font directory.
        if root in self.font_file_list:
            # If we already have that name in our font_file_list,
            # and "other" is selected, this is now
            # our default font face.
            if self.options.fontface == "other":
                self.options.fontface = root
            return

        test_path = os.path.realpath(self.options.otherfont)

        # Check for case "(B)": A file, not in primary font directory
        if os.path.isfile(test_path):
            directory, file_name = os.path.split(test_path)
            root, ext = os.path.splitext(file_name)
            self.font_file_list[root] = test_path

            if self.options.fontface == "other":
                self.options.fontface = root

            # Also search the directory where that file
            # was located for other SVG files(which may be fonts)

            for dir_item in os.listdir(directory):
                if dir_item.endswith((".svg", ".SVG")):
                    file_path = os.path.join(directory, dir_item)
                    if os.path.isfile(file_path): # i.e., if not a directory
                        root, _ = os.path.splitext(dir_item)
                        self.font_file_list[root] = file_path
            return

        # Check for case "(C)": A directory name
        if os.path.isdir(test_path):
            for dir_item in os.listdir(test_path):
                if dir_item.endswith((".svg", ".SVG")):
                    file_path = os.path.join(test_path, dir_item)
                    if os.path.isfile(file_path): # i.e., if not a directory
                        root, _ = os.path.splitext(dir_item)
                        self.font_file_list[root] = file_path


    def font_load_wrapper(self, fontname):
        '''

        This implements the following logic:

        * Check to see if the font name is in our lookup table of fonts,
            self.font_dict

        * If the font is not listed in font_dict[]:
            * Check to see if there is a corresponding SVG font file that
            can be opened and parsed.

            * If the font can be opened and parsed:
                * Add that font to font_dict.
            * Otherwise
                * Add the font name to font_dict as None.

        * If the font has value None in font_dict:
            * Try to load fallback font.

        * Fallback font:
            * If an SVG font matching that in the SVG is not available,
            check to see if the default font is available. That font
            is given by self.options.fontface

        * If a font is loaded and available, return the font name.
            Otherwise, return none.

        '''

        self.load_font(fontname) # Load the font if available

        '''
        It *may* be worth building one stroke font (e.g., Hershey Sans 1-stroke) as a
            variable defined in this file so that it can be used even if no external
            SVG font files are available.
        '''

        if self.font_dict[fontname] is None:

            # If we were not able to load the requested font::
            fontname = self.options.fontface    # Fallback
            if fontname not in self.font_dict:
                self.load_font(fontname)
            else:
                pass

        if self.font_dict[fontname] is None:
            self.font_load_fail = True # Set a flag so that we only generate one copy of this error.
            return None
        return fontname


    def get_font_char(self, fontname, char):
        '''
        Given a font face name and a character(unicode point),
            return an SVG path, horizontal advance value,
            and scaling factor.

        If the font is not available by name, use the default font.
        '''

        fontname = self.font_load_wrapper(fontname) # Load the font if available

        if fontname is None:
            return None

        try:
            scale_factor = self.font_dict[fontname]['scale']
        except:
            scale_factor = 0.001  # Default: 1/1000

        try:
            if char not in self.font_dict[fontname]['glyphs']:
                x_adv = self.font_dict[fontname]['missing_glyph']['horiz_adv_x']

                return self.font_dict[fontname]['missing_glyph']['d'], \
                    x_adv, scale_factor
            x_adv = self.font_dict[fontname]['glyphs'][char]['horiz_adv_x']

            return self.font_dict[fontname]['glyphs'][char]['d'], \
                x_adv, scale_factor
        except:
            return None


    def handle_viewbox(self):
        '''
        Wrapper function for processing viewbox information
        '''

        self.svg_height = self.getlength_inch('height')
        self.svg_width = self.getlength_inch('width')

        self.svg = self.document.getroot()
        viewbox = self.svg.get('viewBox')
        if viewbox:
            p_a_r = self.svg.get('preserveAspectRatio')
            s_x, s_y, o_x, o_y = self.vb_scale(viewbox, p_a_r, self.svg_width, self.svg_height)
        else:
            s_x = 1.0 / float(self.PX_PER_INCH) # Handle case of no viewbox
            s_y = s_x
            o_x = 0.0
            o_y = 0.0

        # Initial transform of document is based on viewbox, if present:
        self.doc_transform = Transform(scale=(s_x, s_y), translate=(o_x, o_y))

        self.vb_scale_factor = (s_x + s_y) / 2.0
        # In case of non-square aspect ratio, use average value.


    def draw_svg_text(self, chardata, parent):
        '''
        Render an individual svg glyph
        '''
        char = chardata['char']
        font_family = chardata['font_family']
        offset = chardata['offset']
        vertoffset = chardata['vertoffset']
        font_height = chardata['font_height']
        font_scale = 1.0

        # Stroke scale factor, including external transformations:
        stroke_scale = chardata['stroke_scale'] * self.vb_scale_factor

        try:
            path_string, adv_x, scale_factor = self.get_font_char(font_family, char)
        except:
            adv_x = 0
            path_string = None
            scale_factor = 1.0

        if self.font_load_fail:
            return 0

        font_scale *= scale_factor * font_height

        h_offset = 0
        v_offset = 0

        # SVG fonts use inverted Y axis; mirror vertically
        scale_transform = Transform(scale=(font_scale, -font_scale))

        # Combine scales of external transformations with the scaling
        # applied by this function:
        _scale = font_scale * stroke_scale
        if _scale == 0:
            _scale = 1
        stroke_width = self.render_width / _scale

        # Stroke-width is a css style element; cannot use scientific notation.
        # Thus, use variable width for encoding the stroke width factor:

        log_ten = math.log10(stroke_width)
        if log_ten > 0:  # For stroke_width > 1
            width_string = "{0:.3f}in".format(stroke_width)
        else:
            prec = int(math.ceil(-log_ten) + 3)
            width_string = "{0:.{1}f}in".format(stroke_width, prec)

        p_style = {'stroke-width': width_string}

        the_transform = Transform(translate=(offset + h_offset, vertoffset + v_offset))
        the_transform *= scale_transform

        if path_string is not None:
            path_element = parent.add(PathElement())
            path_element.set_path(path_string)
            path_element.style = p_style
            path_element.transform = the_transform
            self.output_generated = True

        return offset + float(adv_x) * font_scale  # new horizontal offset value


    def recursive_get_encl_transform(self, node):

        '''
        Determine the cumulative transform which node inherits from
        its chain of ancestors.
        '''
        node = node.getparent()
        if node is not None:
            parent_transform = self.recursive_get_encl_transform(node)
            node_transform = node.get('transform', None)
            if node_transform is None:
                return parent_transform
            trans = Transform(node_transform).matrix

            if parent_transform is None:
                return trans
            return Transform(parent_transform) * Transform(trans)
        return self.doc_transform


    def recursively_parse_flowroot(self, node_list, parent_info):
        '''
        Parse a flowroot node and its children
        '''

        # By default, inherit these values from parent:
        font_height_local = parent_info['font_height']
        font_family_local = parent_info['font_family']
        line_spacing_local = parent_info['line_spacing']
        text_align_local = parent_info['align']

        for node in node_list:
            try:
                node_style = node.style
            except ValueError:
                pass

            try:
                font_height = node_style['font-size']
                font_height_local = self.units_to_userunits(font_height)
            except KeyError:
                pass

            try:
                font_family_local = self.strip_quotes(node_style['font-family'])
            except:
                pass

            try:
                line_spacing = node_style['line-height']
                if "%" in line_spacing: # Handle percentage line spacing(e.g., 125%)
                    line_spacing_local = float(line_spacing.rstrip("%")) / 100.0
                else:
                    line_spacing_local = self.units_to_userunits(line_spacing)
            except KeyError:
                pass

            try:
                text_align_local = node_style['text-align'] # Use text-anchor in text nodes
            except KeyError:
                pass

            if node.text is not None:
                self.text_string += node.text

                for _ in node.text:
                    self.text_families.append(font_family_local)
                    self.text_heights.append(font_height_local)
                    self.text_spacings.append(line_spacing_local)
                    self.text_aligns.append(text_align_local)

            if isinstance(node, (FlowPara, FlowSpan)):
                the_style = dict()
                the_style['font_height'] = font_height_local
                the_style['font_family'] = font_family_local
                the_style['line_spacing'] = line_spacing_local
                the_style['align'] = text_align_local

                self.recursively_parse_flowroot(node, the_style)

            if node.tail is not None:
                # By default, inherit these values from parent:
                font_height_local = parent_info['font_height']
                font_family_local = parent_info['font_family']
                line_spacing_local = parent_info['line_spacing']

                text_align_local = parent_info['align']
                self.text_string += node.tail
                for _ in node.tail:
                    self.text_families.append(font_family_local)
                    self.text_heights.append(font_height_local)
                    self.text_spacings.append(line_spacing_local)
                    self.text_aligns.append(text_align_local)

            if isinstance(node, FlowPara):
                self.text_string += "\n"    # Conclude every flowpara with a return
                self.text_families.append(font_family_local)
                self.text_heights.append(font_height_local)
                self.text_spacings.append(line_spacing_local)
                self.text_aligns.append(text_align_local)

    def recursively_parse_text(self, node, parent_info):
        '''
        parse a text node and its children
        '''

        # By default, inherit these values from parent:
        font_height_local = parent_info['font_height']
        font_family_local = parent_info['font_family']
        anchor_local = parent_info['anchor']
        x_local = parent_info['x_pos']
        y_local = parent_info['y_pos']
        parent_line_spacing = parent_info['line_spacing']

        try:
            node_style = node.style
        except:
            pass

        try:
            font_height = node_style['font-size']
            font_height_local = self.units_to_userunits(font_height)
        except KeyError:
            pass

        try:
            font_family_local = self.strip_quotes(node_style['font-family'])
        except KeyError:
            pass

        try:
            anchor_local = node_style['text-anchor'] # Use text-anchor in text nodes
        except KeyError:
            pass

        try:
            x_temp = node.get('x')
            if x_temp is not None:
                x_local = x_temp
        except ValueError:
            pass

        try:
            y_temp = node.get('y')
            if y_temp is not None:
                y_local = y_temp
            else:
                # Special case, to handle multi-line text given by tspan
                # elements that do not have y values
                if y_local is None:
                    y_local = 0
                y_local = float(y_local) + \
                   self.line_number * parent_line_spacing * font_height_local
        except ValueError:
            pass

        if node.text is not None:
            self.text_string += node.text

            for _ in node.text:
                self.text_families.append(font_family_local)
                self.text_heights.append(font_height_local)
                self.text_aligns.append(anchor_local)
                self.text_x.append(x_local)
                self.text_y.append(y_local)


        for sub_node in node:
            # If text is located within a sub_node of this node,
            #   process that sub_node, with this very routine.

            if isinstance(sub_node, Tspan):
                # Note: There may be additional types of text tags that
                #   we should recursively search as well.
                node_info = dict()
                node_info['font_height'] = font_height_local
                node_info['font_family'] = font_family_local
                node_info['anchor'] = anchor_local
                node_info['x_pos'] = x_local
                node_info['y_pos'] = y_local
                node_info['line_spacing'] = parent_line_spacing

                adv_line = False
                role = sub_node.get('sodipodi:role')
                if role == "line":
                    adv_line = True

                self.recursively_parse_text(sub_node, node_info)

                # Increment line after tspan if it is labeled as a line
                if adv_line:
                    self.line_number = self.line_number + 1

        if node.tail is not None:
            _stripped_tail = node.tail.strip()
            if _stripped_tail is not None:
                # By default, inherit these values from parent:
                font_height_local = parent_info['font_height']
                font_family_local = parent_info['font_family']
                text_align_local = parent_info['anchor']
                x_local = parent_info['x_pos']
                y_local = parent_info['y_pos']
                self.text_string += _stripped_tail
                for _ in _stripped_tail:
                    self.text_heights.append(font_height_local)
                    self.text_families.append(font_family_local)
                    self.text_aligns.append(text_align_local)
                    self.text_x.append(x_local)
                    self.text_y.append(y_local)

    def recursively_traverse_svg(self, anode_list,
                                 mat_current=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
                                 parent_visibility='visible'):
        '''
        recursively parse the full document and its children,
        looking for nodes that may contain text
        '''

        for node in anode_list:

            # Ignore invisible nodes
            vis = node.get('visibility', parent_visibility)
            if vis == 'inherit':
                vis = parent_visibility
            if vis in ('hidden', 'collapse'):
                continue

            # First apply the current matrix transform to this node's tranform
            _matrix = node.transform
            mat_new = Transform(mat_current) * Transform(_matrix)

            if isinstance(node, Group):

                recurse_group = True
                ink_label = node.get('inkscape:label')

                if not ink_label:
                    pass
                else:
                    if(ink_label == 'Hershey Text'):
                        recurse_group = False    # Do not traverse groups of rendered text.
                if recurse_group:
                    self.recursively_traverse_svg(node, mat_new, vis)

            elif isinstance(node, Use):
                # A <use> element refers to another SVG element via an xlink:href="#blah"
                # attribute.  We will handle the element by doing an XPath search through
                # the document, looking for the element with the matching id="blah"
                # attribute.  We then recursively process that element after applying
                # any necessary(x, y) translation.
                #
                # Notes:
                #  1. We ignore the height and width attributes as they do not apply to
                #     path-like elements, and
                #  2. Even if the use element has visibility="hidden", SVG still calls
                #     for processing the referenced element.  The referenced element is
                #     hidden only if its visibility is "inherit" or "hidden".

                refnode = node.href
                if refnode is None:
                    continue # missing reference

                local_transform = Transform(_matrix)
                x = float(node.get('x', '0'))
                y = float(node.get('y', '0'))
                # Note: the transform has already been applied
                if(x != 0) or(y != 0):
                    _trans_string = 'translate({0:.6E}, {1:.6E})'.format(x, y)
                    ref_transform = Transform(_matrix) * Transform(_trans_string)
                else:
                    ref_transform = local_transform

                try:
                    ref_group = anode_list.add(Group())# Add a subgroup
                except AttributeError:
                    inkex.errormsg('Unable to process text. Consider unlinking cloned text.')
                    continue

                # Tests are not using the preset seed for this atm
                #if 'id' not in ref_group.attrib:
                #    ref_group.set_random_id('')

                ref_group.set('transform', ref_transform)

                ref_group.append(deepcopy(refnode))

                for sub_node in ref_group:
                    # The copied text elements should be removed at the end,
                    # or they will persist if original elements are preserved.
                    self.nodes_to_delete.append(sub_node)

                #Preserve original element?
                if not self.options.preserve_text:
                    self.nodes_to_delete.append(node)


            elif isinstance(node, (TextElement, FlowRoot)):

                # Flag for when we start a new line of text, for use with indents:
                self.new_line = True

                start_x = 0  # Defaults; Fail gracefully in case xy position is not given.
                start_y = 0

                # Default line spacing and font height: 125%, 16 px
                line_spacing = self.units_to_userunits("1.25")
                font_height = self.units_to_userunits("16px")

                start_x = node.get('x')    # XY Position of element
                start_y = node.get('y')

                bounding_rect = False
                #rect_height = 100        #default size of bounding rectangle for flowroot object
                rect_width = 100         #default size of bounding rectangle for flowroot object
                transform = ""          #transform(scale, translate, matrix, etc.)
                text_align = "start"

                try:
                    hershey_ignore = node.get('hershey-ignore')
                    if hershey_ignore is not None:
                        continue # If the attribute is present, skip this node.
                except ValueError:
                    pass

                try:
                    node_style = node.style
                except ValueError:
                    pass

                font_height = 16
                try:
                    font_height_temp = node_style['font-size']
                    font_height = self.units_to_userunits(font_height_temp)
                except KeyError:
                    pass

                font_family = 'sans-serif'
                try:
                    font_family = self.strip_quotes(node_style['font-family'])
                except KeyError:
                    pass

                try:
                    line_spacing_temp = node_style['line-height']
                    if "%" in line_spacing_temp: # Handle percentage line spacing(e.g., 125%)
                        line_spacing = float(line_spacing_temp.rstrip("%")) / 100.0
                    else:
                        line_spacing = self.units_to_userunits(line_spacing_temp)
                except KeyError:
                    pass

                try:
                    transform = node.transform
                except ValueError:
                    pass

                if(transform is not None):
                    transform2 = Transform(transform).matrix

                    '''
                    Compute estimate of transformation scale applied to
                    this element, for purposes of calculating the
                    stroke width to apply. When all transforms are applied
                    and our elements are displayed on the page, we want the
                    final visible stroke width to be reasonable.
                    Transformation matrix is [[a c e][b d f]]
                    scale_x = sqrt(a * a + b * b),
                    scale_y = sqrt(c * c + d * d)
                    Take estimated scale as the mean of the two.
                    '''

                    scale_x = math.sqrt(transform2[0][0] * transform2[0][0] +
                                        transform2[1][0] * transform2[1][0])
                    scale_y = math.sqrt(transform2[0][1] * transform2[0][1] +
                                        transform2[1][1] * transform2[1][1])

                    scale_r = (scale_x + scale_y) / 2.0 # Average. ¯\_(ツ)_/¯
                else:
                    scale_r = 1.0

                the_id = node.get('id')

                #Initialize text attribute lists for each top-level text object:
                self.text_string = ""
                self.text_families = [] # Lis of font family for characters in the string
                self.text_heights = []  # List of font heights
                self.text_spacings = [] # List of vertical line heights
                self.text_aligns = []   # List of horizontal alignment values
                self.text_x = []    #List; x-coordinate of text line start
                self.text_y = []    #List; y-coordinate of text line start

                # Group generated paths together, to make the rendered letters
                # easier to manipulate in Inkscape once generated:
                parent = node.getparent()

                group = parent.add(Group())
                group.label = 'Hershey Text'

                style = {'stroke' : '#000000', 'fill' : 'none', \
                    'stroke-linecap' : 'round', 'stroke-linejoin' : 'round'}

                # Apply rounding to ends to improve final engraved text appearance.
                group.style = style
                # Some common variables used in both cases A and B:
                str_pos = 0      # Position through the full string that we are rendering
                i = 0           # Dummy(index) variable for looping over letters in string
                w = 0           # Initial spacing offset
                w_temp = 0       # Temporary variable for horizontal spacing offset
                width_this_line = 0 # Estimated width of characters to be stored on this line

                '''
                CASE A: Handle flowed text nodes
                '''

                if isinstance(node, FlowRoot):

                    try:
                        text_align = node_style['text-align']
                        # Use text-align, not text-anchor, in flowroot
                    except KeyError:
                        pass

                    #selects the flowRegion's child(svg:rect) to get @X and @Y
                    flowref = \
                      self.svg.getElement('/svg:svg//*[@id="%s"]/svg:flowRegion[1]' % the_id)[0]

                    if isinstance(flowref, Rectangle):
                        start_x = flowref.left
                        start_y = flowref.top
                        rect_height = flowref.height
                        rect_width = flowref.width
                        bounding_rect = True

                    elif isinstance(flowref, Use):
                        pass

                        # A <use> element refers to another SVG element via an xlink:href="#blah"
                        # attribute.  We will handle the element by doing an XPath search through
                        # the document, looking for the element with the matching id="blah"
                        # attribute.  We then recursively process that element after applying
                        # any necessary(x, y) translation.
                        #
                        # Notes:
                        #  1. We ignore the height and width attributes as they do not apply to
                        #     path-like elements, and
                        #  2. Even if the use element has visibility="hidden", SVG still calls
                        #     for processing the referenced element.  The referenced element is
                        #     hidden only if its visibility is "inherit" or "hidden".
                        #  3. We may be able to unlink clones using the code in pathmodifier.py

                        # The following code can render text flowed into a rectangle object.
                        # HOWEVER, it does not handle the various transformations that could occur
                        # be present on those objects, and does not handle more general cases, such
                        # as a rotated rectangle -- for which text *should* flow in a diamond shape.
                        # For the time being, we skip these and issue a warning.
                        #
                        # refid = flowref.get('xlink:href')
                        # if refid is not None:
                        #     # [1:] to ignore leading '#' in reference
                        #     path = '//*[@id="%s"]' % refid[1:]
                        #     refnode = flowref.xpath(path)
                        #     if refnode is not None:
                        #         refnode = refnode[0]
                        #         if isinstance(refnode, Rectangle):
                        #             start_x = refnode.get('x")
                        #             start_y = refnode.get('y")
                        #             rect_height = refnode.get('height")
                        #             rect_width = refnode.get('width")
                        #             bounding_rect = True

                    if not bounding_rect:
                        self.warn_unflow = True
                        continue

                    '''
                    Recursively loop through content of the flowroot object,
                    looping through text, flowpara, and other things.

                    Create multiple lists: One of text content,
                    others of style that should be applied to that content.

                    then, loop through those lists, one line at a time,
                    finding how many words fit on a line, etc.
                    '''

                    the_style = dict()
                    the_style['font_height'] = font_height
                    the_style['font_family'] = font_family
                    the_style['line_spacing'] = line_spacing
                    the_style['align'] = text_align

                    self.recursively_parse_flowroot(node, the_style)

                    if(self.text_string == ""):
                        continue # No convertable text in this SVG element.

                    if(self.text_string.isspace()):
                        continue # No convertable text in this SVG element.

                    # Initial vertical offset for the flowed text block:
                    v = 0

                    # Record that we are on the first line of the paragraph
                    # for setting the v position of the first line.
                    first_line = True

                    # Keep track of text height on first line, for moving entire text box:
                    y_offs_overall = 0

                    # Split text by lines AND make a list of how long each
                    # line is, including the newline characters.
                    # We need to keep track of this to match up styling
                    # information to the printable characters.

                    text_lines = self.text_string.splitlines()
                    extd_text_lines = self.text_string.splitlines(True)
                    str_pos_eol = 0 # str_pos after end of previous text_line.

                    nbsp = u'\xa0' # Unicode non-breaking space character

                    for line_number, text_line in enumerate(text_lines):

                        line_length = len(text_line)
                        extd_line_length = len(extd_text_lines[line_number])

                        i = 0   # Position within this text_line.

                        # A given text_line may take more than one strip
                        # to render, if it overflows our box width.

                        line_start = 0 # Value of i when the current strip started.

                        if line_length == 0:
                            str_pos_temp = str_pos_eol
                            char_height = float(self.text_heights[str_pos_temp])
                            charline_spacing = float(self.text_spacings[str_pos_temp])
                            char_v_spacing = charline_spacing * char_height
                            v = v + char_v_spacing
                        else:
                            while(i < line_length):

                                word_start = i # Value of i at beginning of the current word.

                                while(i < line_length): # Step through the line
                                    # until we reach the end of the line or word.
                                    #(i.e., until we reach whitespace)
                                    character = text_line[i] # character is unicode(not byte string)
                                    str_pos_temp = str_pos_eol + i

                                    char_height = self.text_heights[str_pos_temp]
                                    char_family = self.text_families[str_pos_temp]

                                    try:
                                        _, x_adv, scale_factor = \
                                                    self.get_font_char(char_family, character)
                                    except:
                                        x_adv = 0
                                        scale_factor = 1

                                    w_temp += x_adv * scale_factor * char_height

                                    i += 1
                                    if character.isspace() and not character == nbsp:
                                        break # Break at space, except non-breaking

                                render_line = False
                                if w_temp > rect_width: # If the word will overflow the box
                                    if word_start == line_start:
                                        # This is the first word in the strip, so this
                                        # word(alone) is wider than the box. Render it.
                                        render_line = True
                                    else:  # Not the first word in the strip.
                                        # Render the line up UNTIL this word.
                                        render_line = True
                                        i = word_start
                                elif i >= line_length:
                                    # Render at end of text_line, if not overflowing.
                                    render_line = True

                                if render_line:
                                    # Create group for rendering a strip of text:
                                    line_group = group.add(Group())

                                    w_temp = 0
                                    w = 0

                                    self.new_line = True
                                    width_this_line = 0
                                    line_max_v_spacing = 0

                                    j = line_start

                                    while(j < i): # Calculate max height for the strip:
                                        str_pos_temp = str_pos_eol + j
                                        char_height = float(self.text_heights[str_pos_temp])
                                        charline_spacing = float(self.text_spacings[str_pos_temp])
                                        char_v_spacing = charline_spacing * char_height
                                        if(char_v_spacing > line_max_v_spacing):
                                            line_max_v_spacing = char_v_spacing
                                        j = j + 1

                                    v = v + line_max_v_spacing

                                    char_data = dict()
                                    char_data['vertoffset'] = v
                                    char_data['stroke_scale'] = scale_r

                                    j = line_start
                                    while(j < i): # Render the strip on the page
                                        str_pos = str_pos_eol + j

                                        char_height = self.text_heights[str_pos]
                                        char_family = self.text_families[str_pos]
                                        text_align = self.text_aligns[str_pos]

                                        char_data['char'] = text_line[j]
                                        char_data['font_height'] = char_height
                                        char_data['font_family'] = char_family
                                        char_data['offset'] = w

                                        w = self.draw_svg_text(char_data, line_group)

                                        width_this_line = w

                                        j = j + 1
                                        str_pos = str_pos + 1

                                    line_start = i

                                    # Alignment for the strip:

                                    the_transform = None
                                    if(text_align == "center"):    # when using text-align
                                        the_transform = Transform(translate=\
                                                    ((float(rect_width) - width_this_line)/2))
                                    elif(text_align == "end"):
                                        the_transform = Transform(translate=\
                                                    (float(rect_width) - width_this_line))
                                    if the_transform is not None:
                                        line_group.transform = the_transform

                                    if first_line:
                                        y_offs_overall = line_max_v_spacing / 3  # Heuristic
                                        first_line = False

                        str_pos_eol = str_pos_eol + extd_line_length
                        str_pos = str_pos_eol

                    the_transform = Transform(translate=(start_x, float(start_y) - y_offs_overall))

                else:    # If this is a text object, rather than a flowroot object:
                    '''
                    CASE B: Handle regular(non-flowroot) text nodes
                    '''

                    try:
                        # Use text-anchor, not text-align, in text(not flowroot) elements
                        text_align = node_style["text-anchor"]
                    except KeyError:
                        pass

                    '''
                    Recursively loop through content of the text object,
                    looping through text, tspan, and other things as necessary.
                    (A recursive search since style elements may be nested.)

                    Create multiple lists: One of text content, others of the
                    style that should be applied to that content.

                    For each line, want to record the plain text, font size
                    per character, text alignment, and x, y start values
                    for that line)

                    (We may need to eventually handle additional text types and
                    tags, as when importing from other SVG sources. We should
                    try to eventually support additional formulations
                    of x, y, dx, dy, etc.
                    https://www.w3.org/TR/SVG/text.html#TSpanElement)

                    then, loop through those lists, one line at a time,
                    rendering text onto lines. If the x or y values changed,
                    assume we've started a new line.

                    Note: A text element creates a single line
                    of text; it does not create multiline text by including
                    line returns within the text itself. Multiple lines of text
                    are created with multiple text or tspan elements.
                    '''

                    node_info = dict()
                    node_info['font_height'] = font_height
                    node_info['font_family'] = font_family
                    node_info['anchor'] = text_align
                    node_info['x_pos'] = start_x
                    node_info['y_pos'] = start_y
                    node_info['line_spacing'] = line_spacing

                    # Keep track of line number. Used in cases where daughter
                    # tspan elements do not have Y positions given.
                    # Reset to zero on each text element.
                    self.line_number = 0

                    self.recursively_parse_text(node, node_info)
                    # self.recursively_parse_text(node, font_height, text_align, start_x, start_y)

                    if(self.text_string == ""):
                        continue # No convertable text in this SVG element.
                    if(self.text_string.isspace()):
                        continue # No convertable text in this SVG element.

                    letter_vals = [q for q in self.text_string]
                    str_len = len(letter_vals)

                    # Use a group for each line. This starts the first:
                    line_group = group.add(Group())

                    i = 0
                    while(i < str_len):    # Loop through the entire text of the string.

                        x_start_line = float(self.text_x[i]) # We are starting a new line here.
                        y_start_line = float(self.text_y[i])

                        while(i < str_len):
                            # Inner while loop, that we will break out of,
                            # back to the outer while loop.

                            q_val = letter_vals[i]
                            charfont_height = self.text_heights[i]

                            char_data = dict()
                            char_data['char'] = q_val
                            char_data['font_family'] = self.text_families[i]

                            char_data['font_height'] = charfont_height
                            char_data['offset'] = w
                            char_data['vertoffset'] = 0
                            char_data['stroke_scale'] = scale_r

                            w = self.draw_svg_text(char_data, line_group)
                            width_this_line = w
                            w_temp = w

                            # Set the alignment if(A) this is the last character in the string
                            # or if the next piece of the string is at a different position

                            set_alignment = False
                            i_next = i + 1
                            if(i_next >= str_len):  # End of the string; last character.
                                set_alignment = True
                            elif((float(self.text_x[i_next]) != x_start_line) or \
                                 (float(self.text_y[i_next]) != y_start_line)):
                                set_alignment = True

                            if set_alignment:
                                text_align = self.text_aligns[i]
                                # Not currently supporting text alignment that changes in the span;
                                # Use the text alignment as of the last character.

                                # Left(or "start") alignment is default.
                                # if(text_align == "middle"): Center alignment
                                # if(text_align == "end"): Right alignment
                                #
                                # Strategy: Align every row (left, center, or right)
                                # as it is created.

                                x_shift = 0
                                if(text_align == "middle"): # when using text-anchor
                                    x_shift = x_start_line -(width_this_line / 2)
                                elif(text_align == "end"):
                                    x_shift = x_start_line - width_this_line
                                else:
                                    x_shift = x_start_line

                                y_shift = y_start_line

                                the_transform = Transform(translate=(x_shift, y_shift))

                                line_group.transform = the_transform

                                line_group = group.add(Group()) # Create new group for this line

                                self.new_line = True # Used for managing indent defects
                                w = 0
                                i += 1
                                break
                            i += 1    # Only executed when set_alignment is false.

                    the_transform = Transform()

                if len(line_group) == 0:
                    parent = line_group.getparent()
                    parent.remove(line_group)

                #End cases A & B. Apply transform to text/flowroot object:

                if(transform is not None):
                    result = Transform(transform) * the_transform
                else:
                    result = the_transform

                group.transform = result

                if not self.output_generated:
                    parent = group.getparent()
                    parent.remove(group)    #remove empty group

                #Preserve original element?
                if not self.options.preserve_text and self.output_generated:
                    self.nodes_to_delete.append(node)


    def effect(self):
        '''
        Main entry point; Execute the extension's function.
        '''

        # Input sanitization:
        self.options.mode = self.options.mode.strip("\"")
        self.options.fontface = self.options.fontface.strip("\"")
        self.options.otherfont = self.options.otherfont.strip("\"")
        self.options.util_mode = self.options.util_mode.strip("\"")
        self.options.sample_text = self.options.sample_text.strip("\"")

        self.doc_transform = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]

        self.find_font_files()

        self.handle_viewbox()

        # Calculate "ideal" effective width of rendered strokes:
        #   Default: 1/800 of page width or height, whichever is smaller

        _rendered_stroke_scale = 1 /(self.PX_PER_INCH * 800.0)

        if self.svg_width is not None:
            if self.svg_width < self.svg_height:
                self.render_width = self.svg_width * _rendered_stroke_scale
            else:
                self.render_width = self.svg_height * _rendered_stroke_scale

        if self.options.mode == "help":
            inkex.errormsg(self.help_text)
        elif self.options.mode == "utilities":

            if self.options.util_mode == "sample":
                self.font_table()
            else:
                self.glyph_table()
        else:
            if self.options.ids:
                # Traverse selected objects
                for id_ref in self.options.ids:
                    transform = self.recursive_get_encl_transform(self.svg.selected[id_ref])
                    self.recursively_traverse_svg([self.svg.selected[id_ref]], transform)
            else: # Traverse entire document
                self.recursively_traverse_svg(self.document.getroot(), self.doc_transform)

        for element_to_remove in self.nodes_to_delete:
            if element_to_remove is not None:
                parent = element_to_remove.getparent()
                if parent is not None:
                    parent.remove(element_to_remove)

        if self.font_load_fail:
            inkex.errormsg('Warning: unable to load SVG stroke fonts.')

        if self.warn_unflow:
            inkex.errormsg('Warning: unable to convert text flowed into a frame.\n'
                           + 'Please use Text > Unflow to convert it prior to use.\n'
                           + 'If you are unable to identify the object in question, '
                           + 'please contact technical support for help.')

if __name__ == '__main__':
    Hershey().run()
