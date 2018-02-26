# plot_utils.py
# Common geometric plotting utilities for EiBotBoard
# https://github.com/evil-mad/plotink
# 
# Intended to provide some common interfaces that can be used by 
# EggBot, WaterColorBot, AxiDraw, and similar machines.
#
# Version 0.9.0, Dated October 15, 2017.
#
#
# The MIT License (MIT)
# 
# Copyright (c) 2017 Windell H. Oskay, Evil Mad Scientist Laboratories
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from math import sqrt
import cspsubdiv
from bezmisc import *

def version():
	return "0.9"	# Version number for this document

pxPerInch = 90.0	# 90 px per inch, as of Inkscape 0.91
					# Note that the SVG specification is for 96 px per inch; 
					# Expect a change to 96 as of Inkscape 0.92.

def checkLimits( value, lowerBound, upperBound ):
	# Limit a value to within a range.
	# Return constrained value with error boolean.
	if (value > upperBound):
		return upperBound, True
	if (value < lowerBound):
		return lowerBound, True	
	return value, False	

def checkLimitsTol( value, lowerBound, upperBound, tolerance ):
	# Limit a value to within a range.
	# Return constrained value with error boolean.
	# Allow a range of tolerance where we constrain the value without an error message.

	if (value > upperBound):
		if (value > (upperBound + tolerance)):
			return upperBound, True		# Truncate & throw error
		else:
			return upperBound, False	# Truncate with no error
	if (value < lowerBound):
		if (value < (lowerBound - tolerance)):
			return lowerBound, True		# Truncate & throw error
		else:
			return lowerBound, False	# Truncate with no error
	return value, False					# Return original value without error

def constrainLimits( value, lowerBound, upperBound ):
	# Limit a value to within a range. 
	return max( lowerBound, min(upperBound, value) ) 

def distance( x, y ):
	'''
	Pythagorean theorem!
	'''
	return sqrt( x * x + y * y )

def dotProductXY( inputVectorFirst, inputVectorSecond):
	temp = inputVectorFirst[0] * inputVectorSecond[0] + inputVectorFirst[1] * inputVectorSecond[1]
	if (temp > 1):
		return 1
	elif (temp < -1):
		return -1
	else:
		return temp 

def getLength( altself, name, default ):
	'''
	Get the <svg> attribute with name "name" and default value "default"
	Parse the attribute into a value and associated units.  Then, accept
	no units (''), units of pixels ('px'), and units of percentage ('%').
	Return value in px.
	'''
	str = altself.document.getroot().get( name )

	if str:
		v, u = parseLengthWithUnits( str )
		if not v:
			# Couldn't parse the value
			return None
		elif ( u == '' ) or ( u == 'px' ):
			return v
		elif  u == 'in' :
			return (float( v ) * pxPerInch)		
		elif u == 'mm':
			return (float( v ) * pxPerInch / 25.4)
		elif u == 'cm':
			return (float( v ) * pxPerInch / 2.54)
		elif u == 'Q':
			return (float( v ) * pxPerInch / (40.0 * 2.54))
		elif u == 'pc':
			return (float( v ) * pxPerInch / 6.0)
		elif u == 'pt':
			return (float( v ) * pxPerInch / 72.0)
		elif u == '%':
			return float( default ) * v / 100.0
		else:
			# Unsupported units
			return None
	else:
		# No width specified; assume the default value
		return float( default )

def getLengthInches( altself, name ):
	'''
	Get the <svg> attribute with name "name" and default value "default"
	Parse the attribute into a value and associated units.  Then, accept
	units of inches ('in'), millimeters ('mm'), or centimeters ('cm')
	Return value in inches.
	'''
	str = altself.document.getroot().get( name )
	if str:
		v, u = parseLengthWithUnits( str )
		if not v:
			# Couldn't parse the value
			return None
		elif  u == 'in' :
			return v
		elif u == 'mm':
			return (float( v ) / 25.4)
		elif u == 'cm':
			return (float( v ) / 2.54)
		elif u == 'Q':
			return (float( v ) / (40.0 * 2.54))
		elif u == 'pc':
			return (float( v ) / 6.0)	
		elif u == 'pt':
			return (float( v ) / 72.0)
		else:
			# Unsupported units
			return None

def parseLengthWithUnits( str ):
	'''
	Parse an SVG value which may or may not have units attached.
	There is a more general routine to consider in scour.py if more
	generality is ever needed.
	'''
	u = 'px'
	s = str.strip()
	if s[-2:] == 'px':		# pixels, at a size of pxPerInch per inch
		s = s[:-2]
	elif s[-2:] == 'in':	# inches
		s = s[:-2]
		u = 'in'		
	elif s[-2:] == 'mm':	# millimeters
		s = s[:-2]
		u = 'mm'			
	elif s[-2:] == 'cm':	# centimeters
		s = s[:-2]
		u = 'cm'	
	elif s[-2:] == 'pt':	# points	1pt = 1/72th of 1in
		s = s[:-2]
		u = 'pt'			
	elif s[-2:] == 'pc':	# picas!	1pc = 1/6th of 1in
		s = s[:-2]
		u = 'pc'	
	elif ((s[-1:] == 'Q') or (s[-1:] == 'q')):		# quarter-millimeters. 1q = 1/40th of 1cm
		s = s[:-1]
		u = 'Q'	
	elif s[-1:] == '%':
		u = '%'
		s = s[:-1]

	try:
		v = float( s )
	except:
		return None, None

	return v, u

def unitsToUserUnits( inputString ):
	'''
	Custom replacement for the unittouu routine in inkex.py
	
	Parse the attribute into a value and associated units. 
	Return value in user units (typically "px").
	'''

	v, u = parseLengthWithUnits( inputString )
	if not v:
		# Couldn't parse the value
		return None
	elif ( u == '' ) or ( u == 'px' ):
		return v
	elif  u == 'in' :
		return (float( v ) * pxPerInch)		
	elif u == 'mm':
		return (float( v ) * pxPerInch / 25.4)
	elif u == 'cm':
		return (float( v ) * pxPerInch / 2.54)
	elif u == 'Q':
		return (float( v ) * pxPerInch / (40.0 * 2.54))
	elif u == 'pc':
		return (float( v ) * pxPerInch / 6.0)
	elif u == 'pt':
		return (float( v ) * pxPerInch / 72.0)
	elif u == '%':
		return (float( v ) / 100.0)
	else:
		# Unsupported units
		return None

def subdivideCubicPath( sp, flat, i=1 ):
	"""
	Break up a bezier curve into smaller curves, each of which
	is approximately a straight line within a given tolerance
	(the "smoothness" defined by [flat]).

	This is a modified version of cspsubdiv.cspsubdiv(). I rewrote the recursive
	call because it caused recursion-depth errors on complicated line segments.
	"""

	while True:
		while True:
			if i >= len( sp ):
				return
			p0 = sp[i - 1][1]
			p1 = sp[i - 1][2]
			p2 = sp[i][0]
			p3 = sp[i][1]

			b = ( p0, p1, p2, p3 )

			if cspsubdiv.maxdist( b ) > flat:
				break
			i += 1

		one, two = beziersplitatt( b, 0.5 )
		sp[i - 1][2] = one[1]
		sp[i][0] = two[2]
		p = [one[2], one[3], two[1]]
		sp[i:1] = [p]

def userUnitToUnits(distanceUU, unitString ):
	'''
	Custom replacement for the uutounit routine in inkex.py
	
	Parse the attribute into a value and associated units. 
	Return value in user units (typically "px").
	'''

	if not distanceUU: # Couldn't parse the value
		return None
	elif ( unitString == '' ) or ( unitString == 'px' ):
		return distanceUU
	elif  unitString == 'in' :
		return (float( distanceUU ) / (pxPerInch))		
	elif unitString == 'mm':
		return (float( distanceUU ) / (pxPerInch / 25.4))
	elif unitString == 'cm':
		return (float( distanceUU ) / (pxPerInch / 2.54))
	elif unitString == 'Q':
		return (float( distanceUU ) / (pxPerInch / (40.0 * 2.54)))
	elif unitString == 'pc':
		return (float( distanceUU ) / (pxPerInch / 6.0))
	elif unitString == 'pt':
		return (float( distanceUU ) / (pxPerInch / 72.0))
	elif unitString == '%':
		return (float( distanceUU ) * 100.0)
	else:
		# Unsupported units
		return None
		
def vInitial_VF_A_Dx(VFinal,Acceleration,DeltaX):
	'''
	Kinematic calculation: Maximum allowed initial velocity to arrive at distance X
	with specified final velocity, and given maximum linear acceleration. 
	
	Calculate and return the (real) initial velocity, given an final velocity, 
		acceleration rate, and distance interval.

	Uses the kinematic equation Vi^2 = Vf^2 - 2 a D_x , where 
			Vf is the final velocity, 
			a is the acceleration rate, 
			D_x (delta x) is the distance interval, and
			Vi is the initial velocity.	
			
	We are looking at the positive root only-- if the argument of the sqrt
		is less than zero, return -1, to indicate a failure.	
	'''		
	IntialVSquared = ( VFinal * VFinal )  - ( 2 * Acceleration * DeltaX )
	if (IntialVSquared > 0):
		return sqrt(IntialVSquared)	
	else:
		return -1

def vFinal_Vi_A_Dx(Vinitial,Acceleration,DeltaX):
	'''
	Kinematic calculation: Final velocity with constant linear acceleration. 
	
	Calculate and return the (real) final velocity, given an initial velocity, 
		acceleration rate, and distance interval.

	Uses the kinematic equation Vf^2 = 2 a D_x + Vi^2, where 
			Vf is the final velocity, 
			a is the acceleration rate, 
			D_x (delta x) is the distance interval, and
			Vi is the initial velocity.	
			
	We are looking at the positive root only-- if the argument of the sqrt
		is less than zero, return -1, to indicate a failure.		
	'''		
	FinalVSquared = ( 2 * Acceleration * DeltaX ) +	( Vinitial * Vinitial )
	if (FinalVSquared > 0):
		return sqrt(FinalVSquared)	
	else:
		return -1