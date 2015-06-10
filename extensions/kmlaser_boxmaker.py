#! /usr/bin/env python

#    This file is part of KM Laser Bundle.
#
#    KM Laser Bundle is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    KM Laser Bundle is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with KM Laser Bundle.  If not, see <http://www.gnu.org/licenses/>.

'''
Generates Inkscape SVG file containing box components needed to 
laser cut a tabbed construction box taking kerf and clearance into account

Copyright (C) 2011 elliot white   elliot@twot.eu
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
__version__ = "0.3" ### please report bugs, suggestions etc to board@knoxmakers.org ###

#debug
#set value to true to return debug information
#set value to false to turn debug information off
debug = False

import sys,inkex,simplestyle,gettext
_ = gettext.gettext

def addGroup(piece): 
  #This adds a group to the current layer
  #we want all 4 segements of a box side to be grouped
  #it'll also allow grouping of tab slots
  grp_name='Piece' + str(piece)
  grp_attribs = {inkex.addNS('label','inkscape'):grp_name}
  grp = inkex.etree.SubElement(parent, 'g', grp_attribs) #the group to put everything in
  return grp
  
def drawS(XYstring,grp):         # Draw lines from a list
  name= 'part'
  style = { 'stroke': '#000000', 'fill': 'none' }
  drw = {'style':simplestyle.formatStyle(style),inkex.addNS('label','inkscape'):name,'d':XYstring}
  inkex.etree.SubElement(grp, inkex.addNS('path','svg'), drw )
  return
  
def drawR((rx,ry),(dx,dy),grp): 
  #draw a rectange
  #place corner of rectangle at (rx,ry)
  #it will have dimensions of (dx,dy)
  #the rectangle will be placed in group grp
  style = { 'stroke': '#000000', 'fill': 'none' }
  attribs = {
    'style'    : simplestyle.formatStyle(style),
    'height'   : str(dy),
    'width'    : str(dx),
    'x'        : str(rx),
    'y'        : str(ry)
          }
  rect= inkex.etree.SubElement(grp, inkex.addNS('rect','svg'),attribs)
  
def slots((rx,ry),(sox,soy),length,side,grp):
  ##(rx,ry) are the root coordinates for each corner of the bounding box
  #(sox,soy) are -1,0, or 1.  They are factors that indicated the offset of the first point on each side
  #length is the total length of each side of the bounding box
  #side is an integer 0 to 3
  # 0 is side a
  # 1 is side b
  # 2 is side c
  # 3 is side d
    
  #Ensure there are an odd number of divisions
  divs=int(length/nomTab)  # divisions
  if not divs%2: divs-=1   # make divs odd
  divs=float(divs)
  tabs=(divs-1)/2          # tabs for side
  if debug:
    message = "Divisions per side = " + str(divs)
    inkex.debug(message)

  #Removing Proportional Tabs as an option
  #only fixed width tabs now
  gapWidth=tabWidth=length/divs
  
  # kerf correction
  shortTab=tabWidth + correction/2
  shortGap=gapWidth - correction/2
  gapWidth-=correction
  tabWidth+=correction
  
  #debug info
  if debug:
    message1 = "Gap Width = " + str(gapWidth)
    message2 = "Tab Width = " + str(tabWidth)
    message3 = "Short Gap = " + str(shortGap)
    message4 = "Short Tab = " + str(shortTab)
    inkex.debug(message1)
    inkex.debug(message2)
    inkex.debug(message3)
    inkex.debug(message4)
    
  #calculate first position
  (Vx,Vy)=(rx+sox*thickness,ry+soy*thickness)
    
    #actions depend on sides
  if side == 0:
    #this is side A
    #direction of travel is positive x
    #Every slot will start at an a Y coord of
    #  ry
    Vy = ry
    #every slot will be of height thickness
    #middle slots will be gapwidth wide
    #end slots may be modified
    if sox == 0 and soy == 0:
      #in this case, root position
      #first move +x for a Tab
      Vx+=shortTab
      #if we start with a tab, we end with a tab
      #there will be one less gap
      gapcount = (int(divs)-1)/2
      for i in range(0,gapcount):
        #create a rectangle at each of gaps
        #no special widths because tabs are on the ends
        drawR((Vx,Vy),(gapWidth,thickness),grp)
        #after every rectangle, move +x
        #move amount: gapwidth + tabwith
        Vx+=gapWidth + tabWidth
        #increment loop counter
        i+=1
      
    elif sox ==0 and soy ==1:
      #in this case, offset y and not x
      #cut a first gap
      drawR((Vx,Vy),(shortGap,thickness),grp)
      #the next gap should be after this gap, plus room for the tab
      Vx+=shortGap + tabWidth
      #start with a gap means more gaps than tabs
      #total gaps = (divs+1)/2
      #because the first and last will be modified
      #gap count should be that total, less two
      gapcount = (int(divs)+1)/2-2
      for i in range(0,gapcount):
        #create a rectangle at each gap
        #all constant width
        drawR((Vx,Vy),(gapWidth,thickness),grp)
        #after every rectangle, move +x
        #move amount: gapwidth+tabwidth
        Vx+= gapWidth + tabWidth
        #increment loop counter
        i+=1
      #draw a final gap, equal length to first
      drawR((Vx,Vy),(shortGap,thickness),grp)
    
    elif sox == 1 and soy ==1:
      #in this case, offset x and y
      #first move +x for gap
      #this gap isn't modified because it mates with a full width tab
      #we need to reset the starting point to the root position
      Vx = rx
      drawR((Vx,Vy),(shortGap,thickness),grp)
      #the next gap should be after this gap, plus tab
      Vx+=shortGap + tabWidth
      #same gap count as previous case
      gapcount = (int(divs)+1)/2-2
      for i in range(0,gapcount):
        #create rectangle at each pag
        #all constant width
        drawR((Vx,Vy),(gapWidth,thickness),grp)
        #after every rectangle, move +x
        #move amount: gapwidth+tabwidth
        Vx+= gapWidth + tabWidth
        #increment loop counter
        i+=1
      #draw a final gap, equal length to first
      drawR((Vx,Vy),(shortGap,thickness),grp)
    if debug:
      message = "Final X value is " + str(Vx)
      inkex.debug(message)
      
  elif side ==1:
    #this is side b
    #direction of travel is positive y
    #Every rectangle will start at an x position of 
    # rx - thickness
    Vx = rx - thickness
    #each will have an x width of thickness
    
    if sox == 0 and soy == 0:
      #in this case, root position
      #first move +y for a Tab
      Vy+=shortTab
      #with tabs on the ends
      #all tabs will be equal length
      gapcount = (int(divs)-1)/2
      for i in range(0,gapcount):
        drawR((Vx,Vy),(thickness,gapWidth),grp)
        #increment +y position
        Vy += gapWidth + tabWidth
        #increment counter
        i += 1
        
    elif sox ==0 and soy ==1:
      #in this case, offset y and not x
      # first move +y for a Tab
      # modified length by thickness
      shortTab-=thickness
      Vy+=shortTab
      #with tabs on ends
      #all tabs will be equal length
      gapcount = (int(divs)-1)/2
      for i in range(0,gapcount):
        drawR((Vx,Vy),(thickness,gapWidth),grp)
        #increment +y position
        Vy += gapWidth + tabWidth
        #increment counter
        i+= 1
            
    elif sox == -1 and soy ==1:
      #in this case, offset x and y
      #First draw gap
      #modified distance due to offset
      shortGap-=thickness
      drawR((Vx,Vy),(thickness,shortGap),grp)
      #move starting point for next rect
      Vy+=shortGap + tabWidth
      #more gaps than tabs
      #first and last are not included in loop
      gapcount = (int(divs)+1)/2 -2
      for i in range(0,gapcount):
        #draw rectangle of constant width
        drawR((Vx,Vy),(thickness,gapWidth),grp)
        #increment y position
        Vy += gapWidth + tabWidth
        #increment counter
        i += 1
        
      #draw final rectangle
      drawR((Vx,Vy),(thickness,shortGap),grp)
    if debug:
      message = "Final Y value is " + str(Vy)
      inkex.debug(message)
  elif side == 2:
    #this is side c
    #direction of travel is negative x
    #because negative width isn't allowed in SVG
    #we have to travel to far in the negative x direction
    #then specify the width in positive values
    #every rectangle will start at y position
    #ry - thickness
    Vy = ry - thickness

    if sox == 0 and soy == 0:
      #in this case, root position
      #first move -x for a Tab
      #then move -x for width of gap
      Vx-=shortTab + gapWidth
      #tabs on ends means fewer gaps
      #all gaps the same width
      gapcount = (int(divs)-1)/2
      for i in range(0,gapcount):
        drawR((Vx,Vy),(gapWidth,thickness),grp)
        #increment Vx
        Vx-= gapWidth + tabWidth
        #increment counter
        i += 1
        
    elif sox ==0 and soy ==-1:
      #in this case, offset y and not x
      # first move -x for a gap
      Vx-=shortGap
      #draw a first/last rectangle
      drawR((Vx,Vy),(shortGap,thickness),grp)
      #gaps on ends means more gaps
      #but first and last are special length
      gapcount = (int(divs)+1)/2 -2
      for i in range(0,gapcount):
        #increment Vx
        Vx-= gapWidth+tabWidth
        #add rectangle
        drawR((Vx,Vy),(gapWidth,thickness),grp)
        #increment counter
        i += 1
      #draw final rectangle
      #increment over short gap width
      Vx -= shortGap + tabWidth
      drawR((Vx,Vy),(shortGap,thickness),grp)
        
    elif sox == -1 and soy == -1:
      #in this case, offset x and y
      #first move -x for gap
      #in this case, this isn't offset by thickness
      #because it mates up with a full length tab
      #also, we need to reset to the root position
      Vx=rx
      #move to far side of gap
      Vx-=shortGap
      #draw first rectangle
      drawR((Vx,Vy),(shortGap,thickness),grp)
      #gaps on ends mean more gaps
      #but first and last are special length
      gapcount = (int(divs)+1)/2 -2
      for i in range(0,gapcount):
        #increment Vx
        Vx -= gapWidth + tabWidth
        #add rectangle
        drawR((Vx,Vy),(gapWidth,thickness),grp)
        #increment counter
        i+=1
      #draw final rectangle
      #increment first/last gap width
      Vx -= shortGap + tabWidth
      drawR((Vx,Vy),(gapWidth,thickness),grp)
    
    if debug:
      message = "Final X value is " + str(Vx)
      inkex.debug(message)
  elif side == 3:
    #this is side d
    #direction of travel is negative y
    #because negative height isn't allowed in SVG
    #we travel past the rectangle and specify a positive height
    #all rectangles will be located at an x position of
    #  rx
    Vx = rx
    
    if sox == 0 and soy == 0:
      #in this case, root position
      #first move -y for a Tab"
      #additionally move past the gap in the y
      Vy-=shortTab + gapWidth
      #because tabs on end, fewer gaps
      #all gaps same width
      gapcount = (int(divs)-1)/2
      for i in range(0,gapcount):
        #draw rectangles
        drawR((Vx,Vy),(thickness,gapWidth),grp)
        #increment Vy
        Vy -= tabWidth + gapWidth
        #increment counter
        i =+ 1
    elif sox ==0 and soy ==-1:
      #in this case, offset y and not x
      # first move -y for a Tab
      # modified length by thickness
      shortTab-=thickness
      Vy-=shortTab
      #move past gap in y
      Vy -= gapWidth
      #tabs on end, all gaps equal size
      gapcount = (int(divs)-1)/2
      for i in range(0,gapcount):
        #draw rectangle
        drawR((Vx,Vy),(thickness,gapWidth),grp)
        #increment Vy
        Vy -= gapWidth + tabWidth
        #increment counter
        i += 1
        
    elif sox == 1 and soy ==-1:
      #in this case, offset x and y
      #first move -y for gap
      #modified distance due to offset
      shortGap-=thickness
      Vy-=shortGap
      #draw first rectangle with first/last length
      drawR((Vx,Vy),(thickness, shortGap),grp)
      #gaps on ends mean more gaps
      #but first and last are different
      gapcount = (int(divs)+1)/2 -2
      for i in range(0,gapcount):
        #increment by tab + gap
        Vy -= gapWidth + tabWidth
        #draw rect
        drawR((Vx,Vy),(thickness,gapWidth),grp)
        #increment counter
        i+=1
      #increment last amount
      Vy -= shortGap + tabWidth
      drawR((Vx,Vy),(thickness,shortGap),grp)
      
    if debug:
      message = "Final Y value is " + str(Vy)
      inkex.debug(message)
      
   

def newSide((rx,ry),(sox,soy),length,side):
  #(rx,ry) are the root coordinates for each corner of the bounding box
  #(sox,soy) are -1,0, or 1.  They are factors that indicated the offset of the first point on each side
  #length is the total length of each side of the bounding box
  #side is an integer 0 to 3
  # 0 is side a
  # 1 is side b
  # 2 is side c
  # 3 is side d
  
  #changing around side drawing feature
  #in this version, the start of each point will be defined
  #then relative coordinates will be used to generate the rest of the path
  #this will simplify the code quite a bit
  #and hopefully make it easier to draw tabs
  
  #Ensure there are an odd number of divisions
  divs=int(length/nomTab)  # divisions
  if not divs%2: divs-=1   # make divs odd
  divs=float(divs)
  tabs=(divs-1)/2          # tabs for side
  if debug:
    message = "Divisions per side = " + str(divs)
    inkex.debug(message)
    
  #Removing Proportional Tabs as an option
  #only fixed width tabs now
  gapWidth=tabWidth=length/divs
  
  #Since this is a program for laser cutting
  #the program will ignore kerf in length of the tabs
  #This will result in the tabs being shorter than the thickness
  #by half of the kerf
  
  #When cutting out gaps, we want to cut inside the lines
  #when cutting out the tabs, we want to cut outside the lines
  #that mean the length of gaps is always smaller than the division length
  #by the amount of correction
  #the tabs are always longer by the amount of correction
  #this results in the first tab only having half a correction
  
  #There is always an odd number of divisions
  #The first and last tab/gap will have half the correction
  
  # kerf correction
  shortTab=tabWidth + correction/2
  shortGap=gapWidth - correction/2
  gapWidth-=correction
  tabWidth+=correction
  
  #calculate first position
  (Vx,Vy)=(rx+sox*thickness,ry+soy*thickness)
  if debug:
    message1 = "Start X at: " + str(Vx)
    message2 = "Start Y at: " + str(Vy)
    inkex.debug(message1)
    inkex.debug(message2)
  
  #debug info
  if debug:
    message1 = "Gap Width = " + str(gapWidth)
    message2 = "Tab Width = " + str(tabWidth)
    message3 = "Short Gap = " + str(shortGap)
    message4 = "Short Tab = " + str(shortTab)
    inkex.debug(message1)
    inkex.debug(message2)
    inkex.debug(message3)
    inkex.debug(message4)
    
  
  # Create an empty string  
  s=[] 
  
  #calculate first position
  (Vx,Vy)=(rx+sox*thickness,ry+soy*thickness)
  if debug:
    message1 = "Start X at: " + str(Vx)
    message2 = "Start Y at: " + str(Vy)
    inkex.debug(message1)
    inkex.debug(message2)
    
  #write the start position to the string    
  s='m '+str(Vx)+','+str(Vy)+' '
  
  #actions depend on sides
  if side == 0:
    #this is side A
    #direction of travel is positive x
    #first pass
    if sox == 0 and soy == 0:
      #in this case, root position
      #first move +x for a Tab
      s+= str(shortTab) + ",0 "
      Vx+=shortTab
      lastMov=shortTab
      mov = 1
    elif sox ==0 and soy ==1:
      #in this case, offset y and not x
      # first move +x for a gap
      s+= str(shortGap) + ",0 "
      Vx+=shortGap
      lastMov=shortGap
      mov = 3      
    elif sox == 1 and soy ==1:
      #in this case, offset x and y
      #first move +x for gap
      #modified distance due to offset
      shortGap-=thickness
      s+= str(shortGap) + ",0 "
      Vx+=shortGap
      lastMov=shortGap
      mov = 3
    #next iterate over the side
    #there are always 2*divs-1 number of segments
    #the first segment is handled above
    #the last segment will be different, and handled after
    #this for loop will handle all but the first and last segments
    #there should be 2*divs-3 number of segments in it
    for i in range(0,2*int(divs)-3):
      #keep cycling while not finished
      #write relative coordinates for subsequent segements
      if debug:
        message = "Current X Value is " + str(Vx)
        inkex.debug(message)
      if mov == 3:
        #in this case, move -y
        s+= "0,-" + str(thickness) + " "
        mov=0
      elif mov ==2:
        #in this case, move +x for gap
        s+= str(gapWidth) + ",0 "
        Vx+=gapWidth
        mov += 1
      elif mov == 1:
        # in this case, move +y
        s+= "0," + str(thickness) + " "
        mov+=1
      elif mov == 0:
        #in this case, move +x for tab
        s+= str(tabWidth) + ",0 "
        Vx+=tabWidth
        mov += 1
      #increment loop counter
      i+=1
    
    #the last move is always a move in the +x direction
    #a short move
    Vx+=lastMov
    s+= str(lastMov) + ",0 "
    if debug:
      message = "Final X value is " + str(Vx)
      inkex.debug(message)
      
  elif side ==1:
    #this is side b
    #direction of travel is positive y
    #first pass
    if sox == 0 and soy == 0:
      #in this case, root position
      #first move +y for a Tab
      s+= "0," + str(shortTab) + " "
      Vy+=shortTab
      lastMov=shortTab
      mov = 1
    elif sox ==0 and soy ==1:
      #in this case, offset y and not x
      # first move +y for a Tab
      # modified length by thickness
      shortTab-=thickness
      s+= "0," + str(shortTab) + " "
      Vy+=shortTab
      lastMov=shortTab
      mov = 1      
    elif sox == -1 and soy ==1:
      #in this case, offset x and y
      #first move +y for gap
      #modified distance due to offset
      shortGap-=thickness
      s+= "0," + str(shortGap) + " "
      Vy+=shortGap
      lastMov=shortGap
      mov = 3
    #next iterate over the side
    #there are always 2*divs-1 number of segments
    #the first segment is handled above
    #the last segment will be different, and handled after
    #this for loop will handle all but the first and last segments
    #there should be 2*divs-3 number of segments in it
    for i in range(0,2*int(divs)-3):
      #keep cycling while not finished
      #write relative coordinates for subsequent segements
      if debug:
        message = "Current Y Value is " + str(Vy)
        inkex.debug(message)
      if mov == 3:
        #in this case, go +x
        s+= str(thickness) + ",0 "
        mov=0
      elif mov ==2:
        #in this case, move +y for gap
        s+= "0," + str(gapWidth) + " "
        Vy+=gapWidth
        mov += 1
      elif mov == 1:
        # in this case, move -x
        s+= "-" + str(thickness) + ",0 "
        mov+=1
      elif mov == 0:
        #in this case, move +y for tab
        s+= "0," + str(tabWidth) + " "
        Vy+=tabWidth
        mov += 1
      #increment loop counter
      i+=1
    
    #the last move is always a move in the +y direction
    #a short move
    Vy+=lastMov
    s+= "0," + str(lastMov) + " "
    if debug:
      message = "Final Y value is " + str(Vy)
      inkex.debug(message)
  elif side == 2:
    #this is side c
    #direction of travel is negative x
    #first pass
    if sox == 0 and soy == 0:
      #in this case, root position
      #first move -x for a Tab
      s+= "-" + str(shortTab) + ",0 "
      Vx-=shortTab
      lastMov=shortTab
      mov = 1
    elif sox ==0 and soy ==-1:
      #in this case, offset y and not x
      # first move -x for a gap
      s+= "-" + str(shortGap) + ",0 "
      Vx-=shortGap
      lastMov=shortGap
      mov = 3      
    elif sox == -1 and soy == -1:
      #in this case, offset x and y
      #first move -x for gap
      #modified distance due to offset
      shortGap-=thickness
      s+= "-" + str(shortGap) + ",0 "
      Vx-=shortGap
      lastMov=shortGap
      mov = 3
    #next iterate over the side
    #there are always 2*divs-1 number of segments
    #the first segment is handled above
    #the last segment will be different, and handled after
    #this for loop will handle all but the first and last segments
    #there should be 2*divs-3 number of segments in it
    for i in range(0,2*int(divs)-3):
      #keep cycling while not finished
      #write relative coordinates for subsequent segements
      if debug:
        message = "Current X Value is " + str(Vx)
        inkex.debug(message)
      if mov == 3:
        #in this case, move +y
        s+= "0," + str(thickness) + " "
        mov=0
      elif mov ==2:
        #in this case, move -x for gap
        s+= "-" + str(gapWidth) + ",0 "
        Vx-=gapWidth
        mov += 1
      elif mov == 1:
        # in this case, move -y
        s+= "0,-" + str(thickness) + " "
        mov+=1
      elif mov == 0:
        #in this case, move -x for tab
        s+= "-" + str(tabWidth) + ",0 "
        Vx-=tabWidth
        mov += 1
      #increment loop counter
      i+=1
    
    #the last move is always a move in the -x direction
    #a short move
    Vx-=lastMov
    s+= "-" + str(lastMov) + ",0 "
    if debug:
      message = "Final X value is " + str(Vx)
      inkex.debug(message)
  elif side == 3:
    #this is side d
    #direction of travel is negative y
    #first pass
    if sox == 0 and soy == 0:
      #in this case, root position
      #first move -y for a Tab
      s+= "0,-" + str(shortTab) + " "
      Vy-=shortTab
      lastMov=shortTab
      mov = 1
    elif sox ==0 and soy ==-1:
      #in this case, offset y and not x
      # first move -y for a Tab
      # modified length by thickness
      shortTab-=thickness
      s+= "0,-" + str(shortTab) + " "
      Vy-=shortTab
      lastMov=shortTab
      mov = 1      
    elif sox == 1 and soy ==-1:
      #in this case, offset x and y
      #first move -y for gap
      #modified distance due to offset
      shortGap-=thickness
      s+= "0,-" + str(shortGap) + " "
      Vy-=shortGap
      lastMov=shortGap
      mov = 3
    #next iterate over the side
    #there are always 2*divs-1 number of segments
    #the first segment is handled above
    #the last segment will be different, and handled after
    #this for loop will handle all but the first and last segments
    #there should be 2*divs-3 number of segments in it
    for i in range(0,2*int(divs)-3):
      #keep cycling while not finished
      #write relative coordinates for subsequent segements
      if debug:
        message = "Current Y Value is " + str(Vy)
        inkex.debug(message)
      if mov == 3:
        #in this case, go -x
        s+= "-" + str(thickness) + ",0 "
        mov=0
      elif mov ==2:
        #in this case, move -y for gap
        s+= "0,-" + str(gapWidth) + " "
        Vy-=gapWidth
        mov += 1
      elif mov == 1:
        # in this case, move +x
        s+= str(thickness) + ",0 "
        mov+=1
      elif mov == 0:
        #in this case, move -y for tab
        s+= "0,-" + str(tabWidth) + " "
        Vy-=tabWidth
        mov += 1
      #increment loop counter
      i+=1
    
    #the last move is always a move in the -y direction
    #a short move
    Vy-=lastMov
    s+= "0,-" + str(lastMov) + " "
    if debug:
      message = "Final Y value is " + str(Vy)
      inkex.debug(message)
  
  return s
    
class BoxMaker(inkex.Effect):
  def __init__(self):
    # Support for Inkscape 0.48 and 0.91 unittouu
      if not hasattr(self, 'unittouu'):
        self.unittouu = inkex.unittouu      # Call the base class constructor.
      inkex.Effect.__init__(self)
      # Define options
      self.OptionParser.add_option('--active-tab',action='store',type='string',
        dest='activetab',default='',help='Active Tab')
      self.OptionParser.add_option('--unit',action='store',type='string',
        dest='unit',default='mm',help='Measure Units')
      self.OptionParser.add_option('--inside',action='store',type='int',
        dest='inside',default=0,help='Int/Ext Dimension')
      self.OptionParser.add_option('--length',action='store',type='float',
        dest='length',default=100,help='Length of Box')
      self.OptionParser.add_option('--width',action='store',type='float',
        dest='width',default=100,help='Width of Box')
      self.OptionParser.add_option('--depth',action='store',type='float',
        dest='height',default=100,help='Height of Box')
      self.OptionParser.add_option('--tab',action='store',type='float',
        dest='tab',default=25,help='Nominal Tab Width')
      #remove tab width option.  only equal tabs remain, no more fixed tabs
      #self.OptionParser.add_option('--equal',action='store',type='int',
      #  dest='equal',default=0,help='Equal/Prop Tabs')
      self.OptionParser.add_option('--thickness',action='store',type='float',
        dest='thickness',default=10,help='Thickness of Material')
      self.OptionParser.add_option('--kerf',action='store',type='float',
        dest='kerf',default=0.5,help='Kerf (width) of cut')
      self.OptionParser.add_option('--clearance',action='store',type='float',
        dest='clearance',default=0.01,help='Clearance of joints')
      self.OptionParser.add_option('--style',action='store',type='int',
        dest='style',default=25,help='Layout/Style')
      self.OptionParser.add_option('--spacing',action='store',type='float',
        dest='spacing',default=25,help='Part Spacing')
      self.OptionParser.add_option('--slotside',action='store',type='int',
        dest='slotside',default=0,help='Side to replace with slots')


  def effect(self):
    global parent,nomTab,thickness,correction
    
        # Get access to main SVG document element and get its dimensions.
    svg = self.document.getroot()
    
        # Get the attibutes:
    widthDoc  = self.unittouu(svg.get('width'))
    heightDoc = self.unittouu(svg.get('height'))

        # Create a new layer.
    layer = inkex.etree.SubElement(svg, 'g')
    layer.set(inkex.addNS('label', 'inkscape'), 'newlayer')
    layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
    
    parent=self.current_layer
    
        # Get script's option values.
    unit=self.options.unit
    inside=self.options.inside
    X = self.unittouu( str(self.options.length)  + unit )
    Y = self.unittouu( str(self.options.width) + unit )
    Z = self.unittouu( str(self.options.height)  + unit )
    thickness = self.unittouu( str(self.options.thickness)  + unit )
    nomTab = self.unittouu( str(self.options.tab) + unit )
    #equalTabs=self.options.equal
    kerf = self.unittouu( str(self.options.kerf)  + unit )
    clearance = self.unittouu( str(self.options.clearance)  + unit )
    layout=self.options.style
    spacing = self.unittouu( str(self.options.spacing)  + unit )
    slotside=self.options.slotside
    
    if inside: # if inside dimension selected correct values to outside dimension
      X+=thickness*2
      Y+=thickness*2
      Z+=thickness*2

    correction=kerf-clearance

    # check input values mainly to avoid python errors
    # TODO restrict values to *correct* solutions
    error=0
    
    if min(X,Y,Z)==0:
      inkex.errormsg(_('Error: Dimensions must be non zero'))
      error=1
    if max(X,Y,Z)>max(widthDoc,heightDoc)*10: # crude test
      inkex.errormsg(_('Error: Dimensions Too Large'))
      error=1
    if min(X,Y,Z)<3*nomTab:
      inkex.errormsg(_('Error: Tab size too large'))
      error=1
    if nomTab<thickness:
      inkex.errormsg(_('Error: Tab size too small'))
      error=1    
    if thickness==0:
      inkex.errormsg(_('Error: Thickness is zero'))
      error=1    
    if thickness>min(X,Y,Z)/3: # crude test
      inkex.errormsg(_('Error: Material too thick'))
      error=1    
    if correction>min(X,Y,Z)/3: # crude test
      inkex.errormsg(_('Error: Kerf/Clearence too large'))
      error=1    
    if spacing>max(X,Y,Z)*10: # crude test
      inkex.errormsg(_('Error: Spacing too large'))
      error=1    
    if spacing<kerf:
      inkex.errormsg(_('Error: Spacing too small'))
      error=1    

    if error: exit()
   
    # layout format:(rootx),(rooty),Xlength,Ylength,tabInfo
    # root= (spacing,X,Y,Z) * values in tuple
    # tabInfo= <abcd>
    # for each piece:
    #    Side "a' is the bottom in the xy-plane
    #    Side "b" is the right in the xy-plane
    #    Side "c" is the top in the xy-plane
    #    Side "d" is the left in the xy-plane
    
    #the root location of each side is the lower left corner of the circumscribed square for the part
    #  for tabinfo:
    #    0 indicates a tab at the start of the side, no offset required
    #    1 indicates a gap at the start of a side, an offset is required
    
    #Because of the layout of the sides, the presence of tabs on adjacent sides
    #will impact the modification of the starting point of a path
    
    #example: for side "a", the presence of a tab on sides a and d 
    #would mean no offset in either direction, and the root location is not modified
    #A tab on "a" but not on "d" would not change the y starting location
    #but would shift the start in the x direction to make room for a tab from another piece
    #Likewise, the ending point of a path is modified by the presence or lack on tabs.
    
    #the tab layouts have been specified to make sure that pieces will interconnect
    if   layout==1: # Diagramatic Layout
      pieces=[[(2,0,0,1),(3,0,1,1),X,Z,0b1010],[(1,0,0,0),(2,0,0,1),Z,Y,0b1111],
              [(2,0,0,1),(2,0,0,1),X,Y,0b0000],[(3,1,0,1),(2,0,0,1),Z,Y,0b1111],
              [(4,1,0,2),(2,0,0,1),X,Y,0b0000],[(2,0,0,1),(1,0,0,0),X,Z,0b1010]]
    elif layout==2: # 3 Piece Layout
      pieces=[[(2,0,0,1),(2,0,1,0),X,Z,0b1010],[(1,0,0,0),(1,0,0,0),Z,Y,0b1111],
              [(2,0,0,1),(1,0,0,0),X,Y,0b0000]]
    elif layout==3: # Inline(compact) Layout
      pieces=[[(5,2,0,2),(1,0,0,0),X,Z,0b1010],[(3,2,0,0),(1,0,0,0),Z,Y,0b1111],
              [(1,0,0,0),(1,0,0,0),X,Y,0b0000],[(4,2,0,1),(1,0,0,0),Z,Y,0b1111],
              [(2,1,0,0),(1,0,0,0),X,Y,0b0000],[(6,3,0,2),(1,0,0,0),X,Z,0b1010]]
    #Re
    #Removing alternating tabs layout.  Asymmetry is evil and should be destroyed.
    #elif layout==4: # Diagramatic Layout with Alternate Tab Arrangement
    #  pieces=[[(2,0,0,1),(3,0,1,1),X,Z,0b1001],[(1,0,0,0),(2,0,0,1),Z,Y,0b1100],
    #          [(2,0,0,1),(2,0,0,1),X,Y,0b1100],[(3,1,0,1),(2,0,0,1),Z,Y,0b0110],
    #          [(4,1,0,2),(2,0,0,1),X,Y,0b0110],[(2,0,0,1),(1,0,0,0),X,Z,0b1100]]
    #create a counter for group numbering
    #each piece becomes its own group
    groupcount= 0
    for piece in pieces: # generate and draw each piece of the box
      #increment groupcounter
      groupcount+=1
      #this section is used to space out the pieces
      #such that there is no overlap when the pieces are drawn
      (xs,xx,xy,xz)=piece[0]
      (ys,yx,yy,yz)=piece[1]
      x=xs*spacing+xx*X+xy*Y+xz*Z  # root x co-ord for piece
      y=ys*spacing+yx*X+yy*Y+yz*Z  # root y co-ord for piece
      
      #at this point, x and y are the location of the corner of the circumscribed rectangle
      
      #dx is the length traveled in the x direction
      #dy is the length traveled in the y direction
      dx=piece[2]
      dy=piece[3]
      
      #extract the tabs information
      tabs=piece[4]
      a=tabs>>3&1; b=tabs>>2&1; c=tabs>>1&1; d=tabs&1 # extract tab status for each side
      # generate and draw the sides of each piece
      #first, create a group for all 4 sides to be placed in
      grp=addGroup(groupcount)
      
      #Use slotside to determine if a slotted piece needs to be drawn
      #when slotside == groupcount, that means draw that piece with slots
      #otherwise, draw a normal side
      if slotside == groupcount:
      #in this case, draw a collection of rectangles instead of paths
        slots((x,y),(d,a),dx,0,grp) #side a
        slots((x+dx,y),(-b,a),dy,1,grp) #side b
        slots((x+dx,y+dy),(-b,-c),dx,2,grp) # side c
        slots((x,y+dy),(d,-c),dy,3,grp)      # side d
        
      else:
        #if slotside does not equal group count, draw a normal side
        drawS(newSide((x,y),(d,a),dx,0),grp) # side a
        drawS(newSide((x+dx,y),(-b,a),dy,1),grp) #side b
        drawS(newSide((x+dx,y+dy),(-b,-c),dx,2),grp) # side c
        drawS(newSide((x,y+dy),(d,-c),dy,3),grp)      # side d
      
# Create effect instance and apply it.
effect = BoxMaker()
effect.affect()
