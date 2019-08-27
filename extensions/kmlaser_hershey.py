# coding=utf-8
#
# Copyright (C) 2019 -  Windell H. Oskay, www.evilmadscientist.com
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
Hershey Text 3.0.1, 2019-07-05

Copyright 2019, Windell H. Oskay, www.evilmadscientist.com

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
import sys
import math

import inkex
import simplestyle

from simpletransform import composeTransform, parseTransform, formatTransform

from lxml import etree
from copy import deepcopy


class Hershey( inkex.Effect ):
    def __init__( self ):
        inkex.Effect.__init__( self )

        self.OptionParser.add_option( "--tab", \
            action="store", type="string", dest="mode", \
            default="render", \
            help="The active tab or mode when Apply was pressed" )

        self.OptionParser.add_option( "--fontface", \
            action="store", type="string", dest="fontface", \
            default="HersheySans1", \
            help="The selected font face when Apply was pressed" )

        self.OptionParser.add_option( "--otherfont", \
            action="store", type="string", dest="otherfont", \
            default="", \
            help="Optional other font name or path to use" )
        
        self.OptionParser.add_option( "--preserve", \
            action="store", type="inkbool", dest="preserve_text", \
            default=False, \
            help="Preserve original text")

        self.OptionParser.add_option("--action",\
            type="string", action="store", dest="util_mode",\
            default="sample",
            help="The utility option selected")

        self.OptionParser.add_option("--text",\
            type="string", action="store", dest="sample_text",\
            default="sample",
            help="Text to use for font table")

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

For a general introduction to stroke fonts, please visit:
  www.evilmadscientist.com/go/hershey

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


(c) 2019 Windell H. Oskay
Evil Mad Scientist Laboratories
'''

    
    def getLengthInches(self, name):
        """
        Get the <svg> attribute with name "name", and parse it as a length,
        into a value and associated units. Return value in inches.
    
        This may cause scaling issues in some circumstances. Note, for
        example, that Adobe Illustrator uses 72 px per inch, and Inkscape
        used 90 px per inch prior to version 0.92.
        """
        string_to_parse = self.document.getroot().get(name)
        if string_to_parse:
            v, u = self.parseLengthWithUnits(string_to_parse)
            if v is None:
                return None
            elif u == 'in':
                return float(v)
            elif u == 'mm':
                return float(v) / 25.4
            elif u == 'cm':
                return float(v) / 2.54
            elif u == 'Q' or u == 'q':
                return float(v) / (40.0 * 2.54)
            elif u == 'pc':
                return float(v) / 6.0
            elif u == 'pt':
                return float(v) / 72.0
            elif u == '' or u == 'px':
                return float(v) / self.PX_PER_INCH
            else: # Unsupported units, including '%'
                return None

    def parseLengthWithUnits(self, string_to_parse):
        """
        Parse an SVG value which may or may not have units attached.
        """
        u = 'px'
        s = string_to_parse.strip()
        if s[-2:] == 'px':  # pixels, at a size of PX_PER_INCH per inch
            s = s[:-2]
        elif s[-2:] == 'in':  # inches
            s = s[:-2]
            u = 'in'
        elif s[-2:] == 'mm':  # millimeters
            s = s[:-2]
            u = 'mm'
        elif s[-2:] == 'cm':  # centimeters
            s = s[:-2]
            u = 'cm'
        elif s[-2:] == 'pt':  # points; 1pt = 1/72th of 1in
            s = s[:-2]
            u = 'pt'
        elif s[-2:] == 'pc':  # picas; 1pc = 1/6th of 1in
            s = s[:-2]
            u = 'pc'
        elif s[-1:] == 'Q' or s[-1:] == 'q':  # quarter-millimeters. 1q = 1/40th of 1cm
            s = s[:-1]
            u = 'Q'
        elif s[-1:] == '%':
            u = '%'
            s = s[:-1]
        try:
            v = float(s)
        except:
            return None, None
        return v, u
    
    
    
    def unitsToUserUnits(self, input_string):
        """
        Custom replacement for the unittouu routine in inkex.py
    
        Parse the attribute into a value and associated units.
        Return value in user units (typically "px"). 
        Importantly, also return None for malformed inputs.
        """
    
        v, u = self.parseLengthWithUnits(input_string)
        if v is None:
            return None
        elif u == '' or u == 'px':
            return float(v)
        elif u == 'in':
            return float(v) * PX_PER_INCH
        elif u == 'mm':
            return float(v) * PX_PER_INCH / 25.4
        elif u == 'cm':
            return float(v) * PX_PER_INCH / 2.54
        elif u == 'Q' or u == 'q':
            return float(v) * PX_PER_INCH / (40.0 * 2.54)
        elif u == 'pc':
            return float(v) * PX_PER_INCH / 6.0
        elif u == 'pt':
            return float(v) * PX_PER_INCH / 72.0
        elif u == '%':
            return float(v) / 100.0
        else:
            # Unsupported units
            return None

    
    def vb_scale(self, vb, p_a_r, doc_width, doc_height):
        """"
        Parse SVG viewbox and generate scaling parameters.
        Reference documentation: https://www.w3.org/TR/SVG11/coords.html
        
        Inputs:
            vb:         Contents of SVG viewbox attribute
            p_a_r:      Contents of SVG preserveAspectRatio attribute
            doc_width:  Width of SVG document
            doc_height: Height of SVG document
            
        Output: sx, sy, ox, oy
            Scale parameters (sx,sy) and offset parameters (ox,oy)
        
        """
        if vb is None:
            return 1,1,0,0 # No viewbox; return default transform
        else:
            vb_array = vb.strip().replace(',', ' ').split()
            
            if len(vb_array) < 4:
                return 1,1,0,0 # invalid viewbox; return default transform
        
            min_x =  float(vb_array[0]) # Viewbox offset: x
            min_y =  float(vb_array[1]) # Viewbox offset: y
            width =  float(vb_array[2]) # Viewbox width
            height = float(vb_array[3]) # Viewbox height
    
            if width <= 0 or height <= 0:
                return 1,1,0,0 # invalid viewbox; return default transform
            
            d_width = float(doc_width)
            d_height = float(doc_height)
    
            if d_width <= 0 or d_height <= 0:
                return 1,1,0,0 # invalid document size; return default transform
    
            ar_doc = d_height / d_width # Document aspect ratio
            ar_vb = height / width      # Viewbox aspect ratio
            
            # Default values of the two preserveAspectRatio parameters:
            par_align = "xmidymid" # "align" parameter (lowercased)
            par_mos = "meet"       # "meetOrSlice" parameter
            
            if p_a_r is not None:
                par_array = p_a_r.strip().replace(',', ' ').lower().split()
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
    
                sx = d_width/ width
                sy = d_height / height
                ox = -min_x
                oy = -min_y
                return sx,sy,ox,oy
                
            """
            Other than "none", all situations fall into two classes:
            
            1)   (ar_doc >= ar_vb AND par_mos == "meet")
                   or  (ar_doc < ar_vb AND par_mos == "slice")
                -> In these cases, scale document up until VB fills doc in X.
            
            2)   All other cases, i.e.,
                (ar_doc < ar_vb AND par_mos == "meet")
                   or  (ar_doc >= ar_vb AND par_mos == "slice")
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
    
            if (((ar_doc >= ar_vb) and (par_mos == "meet"))
                or ((ar_doc < ar_vb) and (par_mos == "slice"))):
                # Case 1: Scale document up until VB fills doc in X.
    
                sx = d_width / width
                sy = sx # Uniform aspect ratio
                ox = -min_x
                
                scaled_vb_height = ar_doc * width
                excess_height = scaled_vb_height - height
    
                if par_align in {"xminymin", "xmidymin", "xmaxymin"}:
                    # Case: Y-Min: Align viewbox to minimum Y of the viewport.
                    oy = -min_y
                    # OK: tested with Tall-Meet, Wide-Slice
    
                elif par_align in {"xminymax", "xmidymax", "xmaxymax"}:
                    # Case: Y-Max: Align viewbox to maximum Y of the viewport.
                    oy = -min_y + excess_height
                    #  OK: tested with Tall-Meet, Wide-Slice
    
                else: # par_align in {"xminymid", "xmidymid", "xmaxymid"}:
                    # Default case: Y-Mid: Center viewbox on page in Y
                    oy = -min_y + excess_height / 2
                    # OK: Tested with Tall-Meet, Wide-Slice
                    
                return sx,sy,ox,oy
            else:
                # Case 2: Scale document up until VB fills doc in Y.
                
                sy = d_height / height
                sx = sy # Uniform aspect ratio
                oy = -min_y
    
                scaled_vb_width = height / ar_doc
                excess_width = scaled_vb_width - width
    
                if par_align in {"xminymin", "xminymid", "xminymax"}:
                    # Case: X-Min: Align viewbox to minimum X of the viewport.
                    ox = -min_x 
                    # OK: Tested with Tall-Slice, Wide-Meet
    
                elif par_align in {"xmaxymin", "xmaxymid", "xmaxymax"}:
                    # Case: X-Max: Align viewbox to maximum X of the viewport.
                    ox = -min_x + excess_width
                    # Need test: Tall-Slice, Wide-Meet
    
                else: # par_align in {"xmidymin", "xmidymid", "xmidymax"}:
                    # Default case: X-Mid: Center viewbox on page in X
                    ox = -min_x + excess_width / 2
                    # OK: Tested with Tall-Slice, Wide-Meet
                    
                return sx,sy,ox,oy
        return 1,1,0,0 # Catch-all: return default transform


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
        
    def parse_svg_font( self, node_list ):
        '''
        Parse an input svg etree, searching for an SVG font. If an
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
            if node.tag == inkex.addNS('defs', 'svg') or node.tag == 'defs':
                return self.parse_svg_font(node) # Recursive call

            if node.tag == inkex.addNS( 'font', 'svg' ) or node.tag == 'font':
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
                            glyph_name (string)
                            horiz_adv_x (numeric)
                            d (string)
                
                    missing_glyph
                        A dictionary for a single code point, with keys:
                            horiz_adv_x (numeric)
                            d (string)
                        
                    geometry
                        A dictionary containing geometric data
                        Keys will include: 
                            horiz_adv_x (numeric) -- Default value
                            units_per_em (numeric)
                            ascent (numeric)
                            descent (numeric)
                            x_height (numeric)
                            cap_height (numeric)
                            bbox  (string)
                            underline_position (numeric)
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

                glyph_tag = inkex.addNS( 'glyph', 'svg' )
                ff_tag = inkex.addNS( 'font-face', 'svg' )
                mg_tag = inkex.addNS( 'missing-glyph', 'svg' )

                for element in node:

                    if element.tag == 'glyph' or element.tag == glyph_tag:
                        # First, because it is the most common element
                        try:
                            uni_text = element.get('unicode')
                        except:
                            # Can't use this point if no unicode mapping.
                            continue

                        if uni_text is None:
                            continue
                        
                        uni_text2 = uni_text
                        if uni_text in glyphs:
                            # Skip if that unicode point is already in the
                            # list of glyphs. (There is not currently support
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

                    elif element.tag == 'font-face' or element.tag == ff_tag:
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

                    elif element.tag == 'missing-glyph' or element.tag == mg_tag:
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


    def load_font( self, fontname ):
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
    
            f = open(the_path)
            p = etree.XMLParser(huge_tree=True)
            font_svg = etree.parse(f, parser=p)
            f.close()
    #             return self.parse_svg_font( font_svg.getroot() )
            self.font_dict[fontname] = self.parse_svg_font( font_svg.getroot() )
            
        except IOError as e:
            self.font_dict[fontname] = None
            pass
        except:
            inkex.errormsg('Error parsing SVG font at ' + str(the_path))
            self.font_dict[fontname] = None
            

    def font_table (self):
        # Generate display table of all available SVG fonts
        
        self.options.preserve_text = False
        
        # Embed text in group to make manipulation easier:
        g = inkex.etree.SubElement(self.current_layer, 'g')  # type: lxml.etree.ElementTree

        for fontname in self.font_file_list:
            self.load_font(fontname)

        font_size = 0.2 # in inches -- will be scaled by viewbox factor.
        font_size_text = str( font_size / self.vb_scale_factor) + 'px' 
        labeltext_style = simplestyle.formatStyle({ 'stroke' : 'none', \
         'font-size':font_size_text, 'fill' : 'black', \
                'font-family' : 'sans-serif', 'text-anchor': 'end'})

        x_offset = font_size / self.vb_scale_factor
        y_offset = 1.5 * x_offset
        y = y_offset
        
        for fontname in sorted(self.font_dict):
            text_attribs = {'x':'0','y': str(y),'hershey-ignore':'true'}
            textline = inkex.etree.SubElement(g,inkex.addNS('text','svg'),text_attribs )
            textline.text = fontname

            textline.set( 'style',labeltext_style)    
    
            text_attribs = {'x':str(x_offset) ,'y': str(y) }

            sampletext_style = { 'stroke' : 'none', 'font-size':font_size_text, 'fill' : 'black', \
                'font-family' : fontname, 'text-anchor': 'start'}

            sampleline = inkex.etree.SubElement(g,inkex.addNS('text','svg'),text_attribs )

            try: # python 2
                sampleline.text = self.options.sample_text.decode('utf-8')
            except AttributeError: # python 3
                sampleline.text = self.options.sample_text

            sampleline.set( 'style',simplestyle.formatStyle(sampletext_style))
    
            y += y_offset
        self.recursively_traverse_svg( g, self.docTransform )


    def glyph_table (self):
       # Generate display table of glyphs within the current SVG font.
       # Sorted display of all printable characters in the font _except_
       # missing glyph.
        
        self.options.preserve_text = False
        
        fontname = self.font_load_wrapper('not_a_font_name') # force load of default
        
        if self.font_load_fail:
            inkex.errormsg('Font not found; Unable to generate glyph table.')
            return
        
        # Embed in group to make manipulation easier:
        g = inkex.etree.SubElement(self.current_layer, 'g')  

        missing_glyph = self.font_dict[fontname]['missing_glyph']

        glyph_count = 0
        for glyph in self.font_dict[fontname]['glyphs']:
            if self.font_dict[fontname]['glyphs'][glyph]['d'] is not None:
                glyph_count += 1

        columns = int(math.floor(math.sqrt(glyph_count)))

        font_size = 0.4 # in inches -- will be scaled by viewbox factor.
        font_size_text = str( font_size / self.vb_scale_factor) + 'px' 
        glyph_style = simplestyle.formatStyle({ 'stroke' : 'none', \
        'font-size':font_size_text, 'fill' : 'black', \
                'font-family' : fontname, 'text-anchor': 'start'})

        x_offset = 1.5 * font_size / self.vb_scale_factor
        y_offset = x_offset
        x = x_offset
        y = y_offset

        draw_position = 0

        for glyph in sorted(self.font_dict[fontname]['glyphs']):

            if self.font_dict[fontname]['glyphs'][glyph]['d'] is None:
                continue
            y_pos,x_pos =  divmod(draw_position,columns)
            x = x_offset * ( x_pos + 1) 
            y = y_offset * ( y_pos + 1) 
            text_attribs = {'x':str(x),'y': str(y)}
            sampleline = inkex.etree.SubElement(g,inkex.addNS('text','svg'),text_attribs )
            sampleline.text = glyph
            sampleline.set( 'style',glyph_style)    
            draw_position = draw_position + 1

        self.recursively_traverse_svg( g, self.docTransform )


    def find_font_files (self):
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
        appear to be SVG (SVG font) files. It does not parse the files.
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
                file_path = os.path.join(font_dir,dir_item)
                if os.path.isfile(file_path): # i.e., if not a directory
                    root, ext = os.path.splitext(dir_item)
                    self.font_file_list[root] = file_path

        # split off file extension (e.g., ".svg")
        root, ext = os.path.splitext(self.options.otherfont)

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
            # was located for other SVG files (which may be fonts)

            for dir_item in os.listdir(directory):
                if dir_item.endswith((".svg", ".SVG")):
                    file_path = os.path.join(directory,dir_item)
                    if os.path.isfile(file_path): # i.e., if not a directory
                        root, _ext =  os.path.splitext(dir_item)
                        self.font_file_list[root] = file_path
            return
        
        # Check for case "(C)": A directory name
        if os.path.isdir(test_path):
            for dir_item in os.listdir(test_path):
                if dir_item.endswith((".svg", ".SVG")):
                    file_path = os.path.join(test_path,dir_item)
                    if os.path.isfile(file_path): # i.e., if not a directory
                        root, _ext =  os.path.splitext(dir_item)
                        self.font_file_list[root] = file_path






    def font_load_wrapper( self, fontname ):
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
        else:
            return fontname


    def get_font_char( self, fontname, char ):
        '''
        Given a font face name and a character (unicode point),
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
            else:
                x_adv = self.font_dict[fontname]['glyphs'][char]['horiz_adv_x']

                return self.font_dict[fontname]['glyphs'][char]['d'], \
                    x_adv, scale_factor
        except:
            return None


    def handle_viewBox( self ):

        self.svg_height = self.getLengthInches( 'height' )
        self.svg_width = self.getLengthInches( 'width' )

        self.svg = self.document.getroot()
        vb = self.svg.get('viewBox')
        if vb:
            p_a_r = self.svg.get('preserveAspectRatio')
            sx,sy,ox,oy = self.vb_scale(vb, p_a_r, self.svg_width, self.svg_height)
        else: 
            sx = 1.0 / float(self.PX_PER_INCH) # Handle case of no viewbox
            sy = sx
            ox = 0.0
            oy = 0.0
        
        # Initial transform of document is based on viewbox, if present:
        self.docTransform = parseTransform(
            'scale({0:.6E},{1:.6E}) translate({2:.6E},{3:.6E})'.format(
            sx, sy, ox, oy))
        
        self.vb_scale_factor = (sx + sy) / 2.0
        # In case of non-square aspect ratio, use average value. 
        

    def draw_svg_text(self, chardata, parent):
        char = chardata['char']
        font_family = chardata['font_family']
        offset = chardata['offset']
        vertoffset = chardata['vertoffset']
        font_height = chardata['font_height']
        scale = 1.0
        
        # Stroke scale factor, including external transformations:
        stroke_scale = chardata['stroke_scale'] * self.vb_scale_factor

        try:
            path_string, adv_x, scale_factor = self.get_font_char( font_family, char )
        except:
            adv_x = 0
            path_string = None
            scale_factor = 1.0

        if self.font_load_fail:
            return 0

        scale *= scale_factor * font_height

        hOffset = 0
        vOffset = 0
        trans=""
        
        # SVG fonts use inverted Y axis; mirror vertically
        scale_text = 'scale('+format(scale,'.6f')+', -'+format(scale,'.6f')+')'

        # Combine scales of external transformations with the scaling
        # applied by this function:
        stroke_width = self.render_width / (scale * stroke_scale)
        
        # Stroke-width is a css style element; cannot use scientific notation.
        # Thus, use variable width for encoding the stroke width factor:
        
        log_ten = math.log10(stroke_width)
        if log_ten > 0:  # For stroke_width > 1
            width_string = "{0:.3f}in".format(stroke_width)
        else:
            prec = int(math.ceil(-log_ten) + 3)
            width_string = "{0:.{1}f}in".format(stroke_width, prec)
        
        p_style = {'stroke-width': width_string}

        xOffset = offset + hOffset
        yOffset = vertoffset + vOffset 
    
        trans += 'translate('+format(xOffset,'.6f')+','+format(yOffset,'.6f')+')'
        trans += scale_text
        text_attribs = {'d':path_string, 'transform':trans, 'style': simplestyle.formatStyle(p_style)}
        
        if path_string is not None:
            inkex.etree.SubElement(parent, inkex.addNS('path','svg'), text_attribs)
            self.OutputGenerated = True    

        return offset + float(adv_x) * scale  # new horizontal offset value        


    def recursivelyGetEnclosingTransform( self, node ):

        '''
        Determine the cumulative transform which node inherits from
        its chain of ancestors.
        '''
        node = node.getparent()
        if node is not None:
            parent_transform = self.recursivelyGetEnclosingTransform( node )
            node_transform = node.get( 'transform', None )
            if node_transform is None:
                return parent_transform
            else:
                tr = parseTransform( node_transform )
                if parent_transform is None:
                    return tr
                else:
                    return composeTransform( parent_transform, tr )
        else:
            return self.docTransform

    def recursivelyParseFlowRoot( self, NodeList, parent_info):
        
        font_height_local = parent_info['font_height'] # By default, inherit these values from parent.
        font_family_local = parent_info['font_family']
        line_spacing_local = parent_info['line_spacing']
        text_align_local = parent_info['align']
        
        for node in NodeList:
            try:
                node_style = simplestyle.parseStyle(node.get('style'))
            except:
                pass 
        
            try:
                font_height = node_style['font-size']
                font_height_local = self.unitsToUserUnits(font_height)
            except:
                pass 
                
            try:
                font_family_local = self.strip_quotes(node_style['font-family'])
            except:
                pass 

            try:
                line_spacing = node_style['line-height']
                if "%" in line_spacing: # Handle percentage line spacing (e.g., 125%)
                    line_spacing_local = float(line_spacing.rstrip("%")) / 100.0
                else:
                    line_spacing_local = float(line_spacing) # (e.g., line-height:1.25)
            except:
                pass 

            try:
                text_align_local = node_style['text-align'] # Use text-anchor in text nodes
            except:
                pass 
        
            if node.text is not None:
                self.text_string += node.text
                
                for char in node.text:
                    self.text_families.append(font_family_local)
                    self.text_heights.append(font_height_local)
                    self.text_spacings.append(line_spacing_local)
                    self.text_aligns.append(text_align_local)
                            
            if ((node.tag == inkex.addNS("flowPara", "svg")) or (node.tag == inkex.addNS("flowSpan", "svg"))
                or (node.tag == 'flowPara') or (node.tag == 'flowSpan')):
                
                the_style = dict()
                the_style['font_height'] = font_height_local
                the_style['font_family'] = font_family_local
                the_style['line_spacing'] = line_spacing_local
                the_style['align'] = text_align_local
                
                self.recursivelyParseFlowRoot( node, the_style )
            
            if node.tail is not None:
                font_height_local = parent_info['font_height']    # By default, inherit these values from parent.
                font_family_local = parent_info['font_family']
                line_spacing_local = parent_info['line_spacing']
                
                text_align_local = parent_info['align']
                self.text_string += node.tail
                for char in node.tail:
                    self.text_families.append(font_family_local)
                    self.text_heights.append(font_height_local)
                    self.text_spacings.append(line_spacing_local)
                    self.text_aligns.append(text_align_local)
            
            if node.tag == inkex.addNS("flowPara", "svg"):
                self.text_string += "\n"    # Conclude every flowpara with a return
                self.text_families.append(font_family_local)
                self.text_heights.append(font_height_local)
                self.text_spacings.append(line_spacing_local)    
                self.text_aligns.append(text_align_local)

    def recursivelyParseTextNode( self, node, parent_info):

        font_height_local = parent_info['font_height'] # By default, inherit these values from parent.
        font_family_local = parent_info['font_family']
        anchor_local = parent_info['anchor']
        x_local = parent_info['x_pos']
        y_local = parent_info['y_pos']
        parent_line_spacing = parent_info['line_spacing']

        try:
            node_style = simplestyle.parseStyle(node.get('style'))
        except:
            pass 

        try:
            font_height = node_style["font-size"]
            font_height_local = self.unitsToUserUnits(font_height)
        except:
            pass 

        try:
            font_family_local = self.strip_quotes(node_style['font-family'])
        except:
            pass 

        try:
            anchor_local = node_style['text-anchor'] # Use text-anchor in text nodes
        except:
            pass 

        try:
            xTemp = node.get('x')
            if xTemp is not None:
                x_local = xTemp
        except:
            pass 

        try:
            yTemp = node.get('y')
            if yTemp is not None:
                y_local = yTemp
            else:
                # Special case, to handle multi-line text given by tspan
                # elements that do not have y values
                y_local = float(y_local) + self.line_number * parent_line_spacing * font_height_local
        except:
            pass 

        if node.text is not None:
            self.text_string += node.text

            for char in node.text:
                self.text_families.append(font_family_local)
                self.text_heights.append(font_height_local)
                self.text_aligns.append(anchor_local)
                self.text_x.append(x_local)
                self.text_y.append(y_local)

        for subNode in node:
            # If text is located within a subnode of this node, process that subnode, with this very routine.
            
            if ((subNode.tag == inkex.addNS( 'tspan', 'svg' )) or (subNode.tag == 'tspan')):
                # Note: There may be additional types of text tags that we should recursively search as well.
                
                node_info = dict()
                node_info['font_height'] = font_height_local
                node_info['font_family'] = font_family_local
                node_info['anchor'] = anchor_local
                node_info['x_pos'] = x_local
                node_info['y_pos'] = y_local
                node_info['line_spacing'] = parent_line_spacing

                adv_line = False
                role = subNode.get('sodipodi:role')
                if role == "line":
                    adv_line = True

                self.recursivelyParseTextNode( subNode, node_info)

                # Increment line after tspan if it is labeled as a line
                if adv_line:
                    self.line_number = self.line_number + 1 

        if node.tail is not None:
            _stripped_tail = node.tail.strip()
            if _stripped_tail is not None:    
                font_height_local = parent_info['font_height']    # By default, inherit these values from parent.
                font_family_local = parent_info['font_family']
                text_align_local = parent_info['anchor']
                x_local = parent_info['x_pos']
                y_local = parent_info['y_pos']
                self.text_string += _stripped_tail
                for char in _stripped_tail:
                    self.text_heights.append(font_height_local)
                    self.text_families.append(font_family_local)
                    self.text_aligns.append(text_align_local)
                    self.text_x.append(x_local)
                    self.text_y.append(y_local)


    def recursively_traverse_svg( self, aNodeList,
        matCurrent=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        parent_visibility='visible' ):

        for node in aNodeList:

            # Ignore invisible nodes
            v = node.get( 'visibility', parent_visibility )
            if v == 'inherit':
                v = parent_visibility
            if v == 'hidden' or v == 'collapse':
                continue

            # First apply the current matrix transform to this node's tranform
            
            matNew = composeTransform( matCurrent, parseTransform( node.get( "transform" ) ) )

            if node.tag == inkex.addNS( 'g', 'svg' ) or node.tag == 'g':

                recurseGroup = True
                ink_label = node.get( inkex.addNS( 'label', 'inkscape' ) )

                if not ink_label:
                    pass
                else:
                    if (ink_label == 'Hershey Text'):
                        recurseGroup = False    # Do not traverse groups of rendered text.
                if recurseGroup:
                    self.recursively_traverse_svg( node, matNew, v )


            elif node.tag == inkex.addNS( 'use', 'svg' ) or node.tag == 'use':

                # A <use> element refers to another SVG element via an xlink:href="#blah"
                # attribute.  We will handle the element by doing an XPath search through
                # the document, looking for the element with the matching id="blah"
                # attribute.  We then recursively process that element after applying
                # any necessary (x,y) translation.
                #
                # Notes:
                #  1. We ignore the height and width attributes as they do not apply to
                #     path-like elements, and
                #  2. Even if the use element has visibility="hidden", SVG still calls
                #     for processing the referenced element.  The referenced element is
                #     hidden only if its visibility is "inherit" or "hidden".

                refid = node.get( inkex.addNS( 'href', 'xlink' ) )
                if not refid:
                    continue # missing reference

                # [1:] to ignore leading '#' in reference
                path = '//*[@id="%s"]' % refid[1:]
                refnode = node.xpath( path )

                if refnode:
                    local_transform = parseTransform( node.get( "transform" ) )
                    x = float( node.get( 'x', '0' ) )
                    y = float( node.get( 'y', '0' ) )
                    # Note: the transform has already been applied
                    if ( x != 0 ) or (y != 0 ):
                        matNew2 = composeTransform(local_transform, parseTransform('translate({0:.6E},{1:.6E})'.format(x, y)))
                    else:
                       matNew2 = local_transform

                    try:
                        ref_group = inkex.etree.SubElement(aNodeList, 'g') # Add a subgroup
                    except TypeError:
                        inkex.errormsg('Unable to process selected nodes. Consider unlinking cloned text.') 
                        continue

                    try:
                        id = ref_group.get( 'id' )
                    except AttributeError:
                        id = self.uniqueId(None,True)
                        ref_group.set( 'id', id)
                    
                    ref_group.set( 'transform',formatTransform(local_transform))

                    id_list = []

                    for subnode in refnode:
                        try:
                            id = subnode.get( 'id' )
                        except AttributeError:
                            id = self.uniqueId(None,True)
                            subnode.set( 'id', id)
    
                        if id not in id_list:
                            ref_group.append( deepcopy(subnode) ) # add a node to the end of our current nodelist
                            id_list.append(id)

                    for subnode in ref_group:
                        # The copied text elements should be removed at the end,
                        # or they will persist if original elements are preserved.
                        self.nodes_to_delete.append(subnode)

                    #Preserve original element?
                    if not self.options.preserve_text:
                        self.nodes_to_delete.append(node)


            elif (node.tag == inkex.addNS('text','svg')) or (node.tag == 'text') or (node.tag == inkex.addNS("flowRoot", "svg")):

                # Variables are initially zeroed for each text object.
                self.baseline_offset = 0.0    # Baseline Shift
                self.indent_offset = 0.0
                self.kern_offset = 0.0
                self.fontSize_offset = 0.0    # Deviation of font size away from nominal
                self.newLine = True    # Flag for when we start a new line of text, for use with indents.

                startX = 0  # Defaults; Fail gracefully in case xy position is not given.
                startY = 0

                # Default line spacing and font height: 125%, 16 px
                line_spacing = "1.25"                                # Default
                font_height = self.unitsToUserUnits("16px")    # Default
                
                startX = node.get('x')    # XY Position of element
                startY = node.get('y')   
                
                bounding_rect = False
                rect_height = 100        #default size of bounding rectangle for flowroot object
                rect_width = 100         #default size of bounding rectangle for flowroot object
                transform = ""          #transform (scale, translate, matrix, etc.)
                text_align = "start"

                try:
                    hershey_ignore = node.get('hershey-ignore')
                    if hershey_ignore is not None:
                        continue # If the attribute is present, skip this node.
                except:
                    pass 

                try:
                    node_style = simplestyle.parseStyle(node.get('style'))
                except:
                    pass 

                font_height = 0
                try:
                    font_height_temp = node_style['font-size']
                    font_height = self.unitsToUserUnits(font_height_temp)
                except:
                    pass 

                try:
                    font_family = self.strip_quotes(node_style['font-family'])
                except:
                    pass 

                try:
                    line_spacing_temp = node_style['line-height']
                    if "%" in line_spacing_temp: # Handle percentage line spacing (e.g., 125%)
                        line_spacing = float(line_spacing_temp.rstrip("%")) / 100.0
                    else:
                        line_spacing = float(line_spacing_temp) # (e.g., line-height:1.25)
                except:
                    pass 

                try:
                    transform = node.get('transform')
                except:
                    pass 

                if (transform is not None):
                    transform2 = parseTransform( transform )

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

                id = node.get('id')

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
                g_attribs = {inkex.addNS('label','inkscape'):'Hershey Text' }
                parent = node.getparent()    
                g = inkex.etree.SubElement(parent, 'g', g_attribs)
                style = { 'stroke' : '#000000', 'fill' : 'none', \
                    'stroke-linecap' : 'round', 'stroke-linejoin' : 'round' }
                    
                # Apply rounding to ends to improve final engraved text appearance.
                g.set( 'style',simplestyle.formatStyle(style))    

                # Some common variables used in both cases A and B:
                strPos = 0      # Position through the full string that we are rendering
                i = 0           # Dummy (index) variable for looping over letters in string
                w = 0           # Initial spacing offset        
                wTemp = 0       # Temporary variable for horizontal spacing offset
                widthThisLine = 0 # Estimated width of characters to be stored on this line

                '''
                CASE A: Handle flowed text nodes
                '''
                
                if node.tag == inkex.addNS("flowRoot", "svg"):

                    try:
                        text_align = node_style['text-align']        # Use text-align, not text-anchor, in flowroot
                    except:
                        pass 

                    #selects the flowRegion's child (svg:rect) to get @X and @Y
                    flowref = self.xpathSingle('/svg:svg//*[@id="%s"]/svg:flowRegion[1]' % id)[0]
                    
                    if flowref.tag == inkex.addNS("rect", "svg"):
                        startX = flowref.get('x', '0')
                        startY = flowref.get('y', '0')
                        rect_height = flowref.get('height')
                        rect_width = float(flowref.get('width'))
                        bounding_rect = True

                    elif flowref.tag == inkex.addNS( 'use', 'svg' ) or flowref.tag == 'use':
                        pass
                        
                        # A <use> element refers to another SVG element via an xlink:href="#blah"
                        # attribute.  We will handle the element by doing an XPath search through
                        # the document, looking for the element with the matching id="blah"
                        # attribute.  We then recursively process that element after applying
                        # any necessary (x,y) translation.
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
                        # refid = flowref.get( inkex.addNS( 'href', 'xlink' ) )
                        # if refid is not None:
                        #     # [1:] to ignore leading '#' in reference
                        #     path = '//*[@id="%s"]' % refid[1:]
                        #     refnode = flowref.xpath( path )
                        #     if refnode is not None:
                        #         refnode = refnode[0]
                        #         if refnode.tag == inkex.addNS("rect", "svg"):
                        #             startX = refnode.get('x")
                        #             startY = refnode.get('y")
                        #             rect_height = refnode.get('height")
                        #             rect_width = refnode.get('width")
                        #             bounding_rect = True
                                    
                    if not bounding_rect:
                        self.warnUnflow = True
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
                    
                    self.recursivelyParseFlowRoot( node, the_style )

                    if (self.text_string == ""):
                        continue # No convertable text in this SVG element.
                        
                    if (self.text_string.isspace()):
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
                    strPos_eol = 0 # strPos after end of previous text_line.

                    nbsp = u'\xa0' # Unicode non-breaking space character

                    for line_number, text_line in enumerate(text_lines):

                        line_length = len(text_line)
                        extd_line_length = len(extd_text_lines[line_number])

                        i = 0   # Position within this text_line.
                        
                        # A given text_line may take more than one strip
                        # to render, if it overflows our box width.
                        
                        line_start = 0 # Value of i when the current strip started.
                        
                        if line_length == 0:
                            strPos_temp = strPos_eol
                            char_height = float(self.text_heights[strPos_temp])
                            charline_spacing = float(self.text_spacings[strPos_temp])
                            charVSpacing = charline_spacing * char_height
                            v = v + charVSpacing
                        else:
                            while (i < line_length):
                            
                                word_start = i # Value of i at beginning of the current word.
                                
                                while (i < line_length): # Step through the line
                                    # until we reach the end of the line or word.
                                    # (i.e., until we reach whitespace)
                                    character = text_line[i] # character is unicode (not byte string)
                                    strPos_temp = strPos_eol + i
    
                                    char_height = self.text_heights[strPos_temp] 
                                    char_family = self.text_families[strPos_temp] 
                               
                                    try:
                                        _a, x_adv, scale_factor = self.get_font_char( char_family, character )
                                    except:
                                        x_adv = 0
                                        scale_factor = 1
                                        
                                    wTemp += x_adv * scale_factor * char_height
                                    
                                    i += 1
                                    if character.isspace() and not character == nbsp:
                                        break # Break at space, except non-breaking
    
                                render_line = False
                                if wTemp > rect_width: # If the word will overflow the box
                                    if word_start == line_start: 
                                        # This is the first word in the strip, so this
                                        # word (alone) is wider than the box. Render it.
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
                                    lineGroup = inkex.etree.SubElement(g, 'g')
                                    
                                    wTemp = 0
                                    w = 0
                                    
                                    self.newLine = True
                                    widthThisLine = 0   
                                    lineMaxVSpacing = 0
    
                                    j = line_start
    
                                    while ( j < i ): # Calculate max height for the strip:
                                        strPos_temp = strPos_eol + j
                                        char_height = float(self.text_heights[strPos_temp])
                                        charline_spacing = float(self.text_spacings[strPos_temp])
                                        charVSpacing = charline_spacing * char_height
                                        if (charVSpacing > lineMaxVSpacing):
                                            lineMaxVSpacing = charVSpacing
                                        j = j + 1
    
                                    v = v + lineMaxVSpacing
    
                                    char_data = dict()
                                    char_data['vertoffset']= v
                                    char_data['stroke_scale'] = scale_r
                                    
                                    j = line_start
                                    while ( j < i ): # Render the strip on the page
                                        strPos = strPos_eol + j
    
                                        char_height = self.text_heights[strPos] 
                                        char_family = self.text_families[strPos] 
                                        text_align = self.text_aligns[strPos]
        
                                        char_data['char'] = text_line[j]
                                        char_data['font_height'] = char_height
                                        char_data['font_family'] = char_family
                                        char_data['offset'] = w
    
                                        w = self.draw_svg_text(char_data, lineGroup)
        
                                        widthThisLine = w    
                                        firstWordOfLine = False    
        
                                        j = j + 1
                                        strPos = strPos + 1
    
                                    line_start = i
    
                                    # Alignment for the strip:
    
                                    t = "" # Empty string for translation  
                                    if (text_align == "center"):    # when using text-align
                                        t = 'translate(' + str((float(rect_width) - widthThisLine)/2) +  ')'
                                    elif (text_align == "end"):
                                        t = 'translate(' + str(float(rect_width) - widthThisLine) +  ')'
                                    if (t != ""):
                                        lineGroup.set( 'transform',t)
                                        
                                    if first_line:  
                                        y_offs_overall = lineMaxVSpacing / 3  # Heuristic
                                        first_line = False

                        strPos_eol = strPos_eol + extd_line_length
                        strPos = strPos_eol

                    t = 'translate(' + str(startX) + ',' + str(float(startY) - y_offs_overall) + ')'

                else:    # If this is a text object, rather than a flowroot object:
                    '''
                    CASE B: Handle regular (non-flowroot) text nodes
                    '''

                    try:
                        # Use text-anchor, not text-align, in text (not flowroot) elements
                        text_align = node_style["text-anchor"]     
                    except:
                        pass 

                    '''
                    Recursively loop through content of the text object,
                    looping through text, tspan, and other things as necessary. 
                    (A recursive search since style elements may be nested.)
                    
                    Create multiple lists: One of text content, others of the
                    style that should be applied to that content.
                    
                    For each line, want to record the plain text, font size
                    per character, text alignment, and x,y start values 
                    for that line)
                    
                    (We may need to eventually handle additional text types and
                    tags, as when importing from other SVG sources. We should
                    try to eventually support additional formulations 
                    of x, y, dx, dy, etc. 
                    https://www.w3.org/TR/SVG/text.html#TSpanElement )
                    
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
                    node_info['x_pos'] = startX
                    node_info['y_pos'] = startY
                    node_info['line_spacing'] = line_spacing

                    # Keep track of line number. Used in cases where daughter
                    # tspan elements do not have Y positions given.
                    # Reset to zero on each text element.
                    self.line_number = 0 
                    
                    self.recursivelyParseTextNode( node, node_info)
                    # self.recursivelyParseTextNode( node, font_height, text_align, startX, startY )

                    if (self.text_string == ""):
                        continue # No convertable text in this SVG element.
                    if (self.text_string.isspace()):
                        continue # No convertable text in this SVG element.

                    letter_vals = [q for q in self.text_string] 
                    strLen = len(letter_vals)

                    lineGroup = inkex.etree.SubElement(g, 'g') # Use a group for each line. This starts the first.
                    i = 0
                    while (i < strLen):    # Loop through the entire text of the string.
    
                        xStartLine = float(self.text_x[i]) # We are starting a new line here.
                        yStartLine = float(self.text_y[i])
                        
                        while (i < strLen): # Inner while loop, that we will break out of, back to the outer while loop.
                            
                            q = letter_vals[i]
                            charfont_height = self.text_heights[i]

                            char_data = dict()
                            char_data['char'] = q
                            char_data['font_family'] = self.text_families[i]

                            char_data['font_height'] = charfont_height
                            char_data['offset'] = w
                            char_data['vertoffset']= 0
                            char_data['stroke_scale'] = scale_r

                            w = self.draw_svg_text(char_data, lineGroup)
                            widthThisLine = w    
                            wTemp = w
                        
                            # Set the alignment if (A) this is the last character in the string
                            # or if the next piece of the string is at a different position

                            setAlignment = False
                            iNext = i + 1
                            if (iNext >= strLen):    # End of the string; this is the last character.
                                setAlignment = True
                            elif ((float(self.text_x[iNext]) != xStartLine) or (float(self.text_y[iNext]) != yStartLine) ):
                                setAlignment = True
                                
                            if setAlignment:
                                text_align = self.text_aligns[i]
                                # Not currently supporting text alignment that changes in the span;
                                # Use the text alignment as of the last character.

                                # Left (or "start") alignment is default. 
                                # if (text_align == "middle"): Center alignment
                                # if (text_align == "end"): Right alignment
                                # 
                                # Strategy: Align every row (left, center, or right) as it is created.

                                xShift = 0
                                if (text_align == "middle"): # when using text-anchor
                                    xShift = xStartLine - (widthThisLine / 2)
                                elif (text_align == "end"):
                                    xShift = xStartLine - widthThisLine
                                else:
                                    xShift = xStartLine
                                
                                yShift = yStartLine
                                
                                t = 'translate('+format(xShift,'.7f')+','+format(yShift,'.7f')+')'
                                lineGroup.set( 'transform',t)

                                lineGroup = inkex.etree.SubElement(g, 'g')  #Create new group for this line
                                self.newLine = True # Used for managing indent defects
                                w = 0    
                                i += 1
                                break
                            i += 1    # Only executed when setAlignment is false.
                    t = ""

                if len(lineGroup) == 0:
                    parent = lineGroup.getparent()
                    parent.remove(lineGroup)

                #End cases A & B. Apply transform to text/flowroot object:

#                 if transform is not None:
#                     t3 = transform + t
#                 else:
#                     t3 = t
#                 g.set( 'transform',str(t3))    
#
#                 This above five lines are a simplistic approach to applying transformations :
#                 simply concatenating the transforms. It can end up with applied tranformations of the form:
#                 "translate(-32.477009,-204.40135)translate(58.688175,293.76318)scale(0.775862068966)"
# 
#                 A more "correct" approach is to instead compose the transformation, using the following
#                which results in a more compact file, at the cost of slightly more processing time:

                if (transform is not None):
#                     transform2 = parseTransform( transform )
                    t2 = parseTransform( t )                
                    result = composeTransform( transform2, t2 )
                    t4 = formatTransform(result)
                else:
                    t4 = t
                g.set( 'transform',str(t4))
                
                if not self.OutputGenerated:
                    parent.remove(g)    #remove empty group

                #Preserve original element?
                if not self.options.preserve_text and self.OutputGenerated:
                    self.nodes_to_delete.append(node)

    def effect( self ):

        # Input sanitization:
        self.options.mode = self.options.mode.strip("\"")
        self.options.fontface = self.options.fontface.strip("\"")
        self.options.otherfont = self.options.otherfont.strip("\"")
        self.options.util_mode = self.options.util_mode.strip("\"")
        self.options.sample_text = self.options.sample_text.strip("\"")

        self.docTransform = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
        
        self.font_load_fail = False

        self.find_font_files()
        
        # Font dictionary - Dictionary of loaded fonts
        self.font_dict = dict()

        self.OutputGenerated = False
        
        self.warnUnflow = False
        self.warnTextPath = False    # For future use: Give warning about text attached to path.

        self.nodes_to_delete = [] # List of font elements to remove
        # Must save a list and add back at the end, so that any use elements
        # still have the original nodes to reference.

        
        self.handle_viewBox()
        
        # Calculate "ideal" effective width of rendered strokes:
        #   Default: 1/800 of page width or height, whichever is smaller
        
        _rendered_stroke_scale = 1 / (self.PX_PER_INCH * 800.0)

        self.render_width = 1
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
                for id in self.options.ids:
                    transform = self.recursivelyGetEnclosingTransform( self.selected[id] )
                    self.recursively_traverse_svg( [self.selected[id]], transform)
            else: # Traverse entire document
                self.recursively_traverse_svg( self.document.getroot(), self.docTransform )

        for element_to_remove in self.nodes_to_delete: 
            if element_to_remove is not None:
                parent = element_to_remove.getparent()
                if parent is not None:
                    parent.remove(element_to_remove)

        if self.font_load_fail:
            inkex.errormsg(  'Warning: unable to load SVG stroke fonts.')

        if self.warnUnflow:
            inkex.errormsg(  'Warning: unable to convert text flowed into a frame.\n'
                + 'Please use Text > Unflow to convert it prior to use.\n'
                + 'If you are unable to identify the object in question, '
                + 'please contact technical support for help.'
                )

if __name__ == '__main__':
    e = Hershey()
    e.affect()