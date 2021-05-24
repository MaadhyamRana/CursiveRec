# Gesture Recognizer
from tkinter import Tk, Canvas, Label, Button
from pickle import load, dump
from tkinter.simpledialog import askstring
from math import floor

defaultDir = 'CursiveRec Files/defaultGestures.pkl'
customDir = 'CursiveRec Files/customGestures.pkl'
uiFont = ("Segoe UI Light", 14)
displayFont = ("Segoe UI Light", 20)

# Recog Object Class
class Recog():

   def __init__(self):
      self.res = 10        # Resolution of recognition. Increase to improve accuracy 
      self.minWidth = 30   # Minimum allowed width of canvas stroke
      self.minHeight = 30  # Minimum allowed height of canvas stroke
      self.normSize = 200  # Normalization dimensions
      self.gestCoords = [] # Stores coordinates for active gesture
      self.count = 1       # Stores count of points in gesture
      self.rec = ''        # String of recognized gestures so far

   def draw(self, event):
      x1, y1, x2, y2 = (event.x - 0.5), (event.y - 0.5), (event.x + 0.5), (event.y + 0.5)
      canvas.create_oval(x1, y1, x2, y2)
      # Captures coordinates at every 5 function calls/points to save space and recognition time
      if self.count % 5 == 0: self.gestCoords += [[x2, y2]]
      self.count += 1

   # Gets the min/max of the x/y coordinates in gesture
   def __getMinMax(self, axis, func, gesture):
      return func([i[axis] for i in gesture])

   # Moves gesture along x and/or y axes 
   def __translateGesture(self, gesture, xOffset, yOffset):
      out = []
      for coord in gesture:
         out += [[coord[0] + xOffset, coord[1] + yOffset]]
      return out

   # Resizes gesture based on x and/or y scaling factors
   def __scaleGesture(self, gesture, xScale, yScale):
      for coord in gesture: coord[0] *= xScale ; coord[1] *= yScale;
      return gesture

   # Produces Euclidean distance between points pt1 and pt2
   def __distPts(self, pt1, pt2):
      return ((pt2[0] - pt1[0])**2 + (pt2[1] - pt1[1])**2)**0.5

   # Gets desired point indices specified in 'points' from gesture
   def __getPoints(self, gesture, points):
      out = []
      try:
         for i in points: out+=[gesture[i]]
         return out
      except:
         return []

   # Produces a non-decreasing array of length 'pcs' ranging from 0 to (n-1) with uniform spacing 
   def __spaceOut(self, n, pcs):
      l = []
      try:
        for i in range(pcs):
            if i == pcs - 1: l += [n - 1]
            else: l += [floor(i * 1/(pcs - 1) * n)]
        return l
      except:
         return []

   # Moves gesture near the origin (Top right corner of gesture's bounds will become (0, 0))
   def __moveToOrigin(self, gesture):
      return self.__translateGesture(gesture,
                                     -self.__getMinMax(0, min, gesture),
                                     -self.__getMinMax(1, min, gesture))

   # Checks if gesture is narrower/shorter than minimum width/height
   def __dimensionCheck(self, axis, gesture, minimum):
      return (self.__getMinMax(axis, max, gesture) - self.__getMinMax(axis, min, gesture)) < minimum

   # Returns scaling factor for gesture for a target size 
   def __scaleFactor(self, axis, targetSize, gesture):
      return targetSize / self.__getMinMax(axis, max, gesture)

   # Moves gesture to origin and scales it down/up so that gesture is 200x200 in dimensions
   def __normalizeGesture(self, gesture):
      movedToOriginGesture = self.__moveToOrigin(gesture)
      
      if self.__dimensionCheck(0, gesture, self.minWidth):
         return self.__scaleGesture(movedToOriginGesture, 1,
                                    self.__scaleFactor(1, self.normSize, movedToOriginGesture))

      if self.__dimensionCheck(1, gesture, self.minHeight):
         return self.__scaleGesture(movedToOriginGesture,
                                    self.__scaleFactor(1, self.normSize, movedToOriginGesture), 1)

      else:
         return self.__scaleGesture(movedToOriginGesture,
                                    self.__scaleFactor(0, self.normSize, movedToOriginGesture),
                                    self.__scaleFactor(1, self.normSize, movedToOriginGesture))

   # Calculates average distance between consecutive points in equi-length gestures 1 and 2
   def __avgDist(self, gesture1, gesture2, k):
      dist = 0
      for i in range(k): dist += self.__distPts(gesture1[i], gesture2[i]) / k
      return dist
      
   # Produces a sample of k evenly-spaced (index-wise) points from a gesture
   def __kSample(self, gesture, k):
      return self.__getPoints(gesture, self.__spaceOut(len(gesture), k))

   # Calculates average distance between 2 normalized, sampled gestures 
   def __kMatch(self, gesture1, gesture2, k):
      return self.__avgDist(self.__normalizeGesture(self.__kSample(gesture1, k)),
                            self.__normalizeGesture(self.__kSample(gesture2, k)), k)

   # Returns the name of gesture from library having lowest average distance with current gesture
   def recognize(self, library):
      if self.gestCoords == []: resultDisplay["text"] = "Canvas is empty"; return

      minMatch = library[0]
      minMatchDist = self.__kMatch(self.gestCoords, minMatch[1], self.res)
      
      for gesture in library[1:]:
         currentDist = self.__kMatch(self.gestCoords, gesture[1], self.res)
         if currentDist < minMatchDist: minMatch, minMatchDist = gesture, currentDist
         
      self.rec += minMatch[0]
      resultDisplay["text"] = "Recognized gesture(s): " + self.rec
      self.gestCoords = []

   # Resets variables, clears canvas   
   def clear(self):
      self.gestCoords = []
      canvas.delete("all")
      resultDisplay["text"] = ""
      self.count = 1
      self.rec = ''

   def deleteLast(self):
      if self.rec != '':
         self.rec = self.rec[-2::-1][-1::-1]
         resultDisplay["text"] = "Recognized gesture(s): " + self.rec

   def copy(self):
      root.clipboard_clear()
      root.clipboard_append(self.rec)

   # Helps with saving custom gestures to a separate binary file
   def saveCustom(self):
      global GestureLibrary
      gestureName = askstring('Save Gesture','Enter a name for this new gesture: ')
      if gestureName != None:
         GestureLibrary += [[gestureName, self.gestCoords]]
         CustomLibrary = load(open(customDir,'rb'))
         CustomLibrary += [[gestureName, self.gestCoords]]
         dump(CustomLibrary, open(customDir, 'wb'))
   

# Importing default + custom gestures libraries
GestureLibrary = load(open(defaultDir,'rb')) + load(open(customDir,'rb'))

# Main windows and canvas 
root = Tk()
root.resizable(height = False, width = False)
root.title("CursiveRec")
canvas = Canvas(root, width=700, height=400, bd=3, relief='ridge')
canvas.grid(row = 0, column = 0, columnspan = 7)

# Setting up recognizer object
recog = Recog()

# Labels
canvas.bind("<B1-Motion>", recog.draw) # Binding left-mouse button movement to draw function
Label(root, text = 'Click and drag mouse to draw, and then click "Recognize" when done',
      font = uiFont,).grid(row = 1, column = 0, columnspan = 7, pady = 4, padx = 4)
Label(root, text = 'Click "Save Custom Gesture" to save current gesture',
      font = uiFont,).grid(row = 2, column = 0, columnspan = 7, pady = 4, padx = 4)
Label(root, text = 'You can draw more gestures. Click "Delete last" to remove last character',
      font = uiFont,).grid(row = 3, column = 0, columnspan = 7, pady = 4, padx = 4)
Label(root, text = 'Click "Copy" to copy recognized text to clipboard',
      font = uiFont,).grid(row = 4, column = 0, columnspan = 7, pady = 4, padx = 4)

# Buttons
recogButton = Button(root, text = "Recognize", font = uiFont, command = lambda gl = GestureLibrary: recog.recognize(gl))
recogButton.grid(row = 5, column = 0, padx = 8, pady = 8)
clearButton = Button(root, text = "Clear Canvas", font = uiFont, command = recog.clear)
clearButton.grid(row = 5, column = 1, padx = 8, pady = 8)
saveButton = Button(root, text = "Save Custom Gesture", font = uiFont, command = recog.saveCustom)
saveButton.grid(row = 5, column = 2, padx = 8, pady = 8)
delCharButton = Button(root, text = "Delete Last", font = uiFont, command = recog.deleteLast)
delCharButton.grid(row = 5, column = 3, padx = 8, pady = 8)
delCharButton = Button(root, text = "Copy", font = uiFont, command = recog.copy)
delCharButton.grid(row = 5, column = 4, padx = 8, pady = 8)
exitButton = Button(root, text = "Exit", font = uiFont, command = root.destroy)
exitButton.grid(row = 5, column = 5, padx = 8, pady = 8)

# Display
resultDisplay = Label(root, text = "", font = displayFont)
resultDisplay.grid(row = 6, column = 0, columnspan = 7, padx = 10, pady = 10)
root.mainloop()
