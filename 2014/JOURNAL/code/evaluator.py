
import os, cv2, Image, numpy
from xml.dom.minidom import parse, parseString
from xml.etree import ElementTree as et
import toolbox_svg, toolbox_topology
import class_balloon

import matplotlib.pyplot as plt
#reload(class_balloon)

class Evaluator:
    """
        Class to evaluation extractor according to ground truth files store in a SVG format
    """
    
    def __init__(self, img, groudtruthFolderPath, detectionFolderPath, objectType, nonValidRegionList=None):
        """ 
            Evaluator constructor 
        """
        self.objectsGT = self.loadFromGT(groudtruthFolderPath, objectType, boundingBoxOnly=False, nonValidRegionList=nonValidRegionList, modeGT=True)
        self.objectDetected = self.loadFromGT(detectionFolderPath, objectType, boundingBoxOnly=False, nonValidRegionList=nonValidRegionList, modeGT=False)
        self.validTextObjectList = None#validTextObjectList
        self.empty = (0, 0), (0, 0)
        self. img = img
   

    ############# SELF FUNCTIONS ##################
    

    def loadFromGT(self, svgPath, objectType, boundingBoxOnly, nonValidRegionList=None, modeGT=False):
        """ 
            Load regions from ground truth SVG (eBDtheque dataset) 
        """
        regions = []
        n = 1
       
        #Test file existence
        if not os.path.isfile(svgPath):
            print 'ERROR: file not found (',svgPath,')'
            return

        xmldoc = parse(svgPath)
        itemlist = xmldoc.getElementsByTagName('polygon') 
            
        for s in itemlist :
            
            if s.parentNode.attributes['class'].value == objectType:
                xList = []
                yList = []
                points = s.attributes['points'].value

                #If the region has been detected as invalid before then ignore it (do not load)
                if nonValidRegionList != None:
                    idRegion = s.childNodes[1].attributes['id'].value + '\n'
                    if idRegion in nonValidRegionList:
                        print '-',#idRegion,'is nonValidRegionList (not loaded)'
                        continue

                coords = points.split(' ')          

                #Compute bounding box
                for c in coords:
                    pts = c.split(',')
                    xList.append(int(pts[0]))
                    yList.append(int(pts[1]))
                #Build the region bounding box
                l = min(xList)
                t = min(yList)
                r = max(xList)
                b = max(yList)
                box = (int(l),int(t),int(r),int(b))      
        
                if modeGT:

                    if objectType == 'Balloon':

                        # Filter on closed balloons only for GT only
                        # try:
                        #     borderStyle = s.childNodes[1].attributes['borderStyle'].value
                        #     if borderStyle == 'other':
                        #         print '-',
                        #         n = n + 1
                        #         continue
                        # except:
                        #     pass

                        # Filter on speech balloons (with tail)
                        # try:
                        #     tailTip = s.childNodes[1].attributes['tailTip'].value
                        #     if tailTip == "":
                        #         print '-',
                        #         n = n + 1
                        #         continue
                        # except:
                        #     pass

                        pass

                    if objectType == 'Line':
                        
                        # #Filter on speech text for GT only
                        # r1 = (box[0], box[1]), (box[2], box[3]) # (left, top), (right, bottom) 

                        # #Load balloons
                        # balloons = self.loadFromGT(svgPath, 'Balloon', boundingBoxOnly=True, nonValidRegionList=None, modeGT=False)
                        # isContained = False
                        # for b in balloons:                           
                        #     obj = b
                        #     r2 = (obj[0], obj[1]), (obj[2], obj[3])
                        #     res = self.intersect(r1, r2)
                        #     empty = (0, 0), (0, 0)# The empty rectangle.
                        #     #If included in a balloon
                        #     if res != empty:
                        #         intersectArea = (res[1][0]-res[0][0]) * (res[1][1]-res[0][1])
                        #         if intersectArea > 50:
                        #             #print 'Line',box,'intersect balloon',b
                        #             isContained = True
                        #             break

                        # if not isContained:
                        #     print '-',
                        #     #Ignore text line
                        #     continue
                        # else:
                        #     #Ignore if this balloon has no tail
                        #     try:
                        #         tailTip = s.childNodes[1].attributes['tailTip'].value
                        #         if tailTip == "":
                        #             print '-',
                        #             n = n + 1
                        #             #Ignore text line
                        #             continue
                        #     except:
                        #         pass

                        pass

                #Add region to the list       
                if boundingBoxOnly:                    
                    regions.append(box)
                else:                    
                    regions.append(toolbox_svg.svgList2NumpyArray(coords))
                                
                n = n + 1
        
        return regions
    

    

    def evaluateAtObjectLevel(self, threshold, savePath, verbose):
        
        """ 
            Evaluate the detected regions at pixel level with the pre loaded ground truth regions 
        """

        nbTruePos = 0
        nbFalsePos = 0
        matchList = []
        #height, width, depth = drawing.shape

        #If there is nothing to detect and nothing detected then return maximal score
        if len(self.objectDetected) == 0 and len(self.objectsGT) == 0:
            if verbose:
                print '\nDEBUG: no object in the GT and no object predicted -> R=1 and P=1 for this file'
            return 1, 1, 0

        for predictedObject in self.objectDetected:
        
            #Find corresponding balloon with the biggest sharing intersection
            maxArea = 0
            overlapRatio = 0
            maxOverlapRatio = 0
            bestMatchObject = None
            bestMatchObjectBox = None
            idxB2 = 0
            predictedObjectBox = self.getBox(predictedObject)
            for gtObject in self.objectsGT:                
                gtObjectBox = self.getBox(gtObject)
                r3 = toolbox_topology.intersect(predictedObjectBox, gtObjectBox) #left, top, right, bottom
                if not is_empty(r3):
                    r3Geom = rect2geom(r3[0],r3[1]) #Converts a rectangle to geometry representation: (left, top), (width, height). 
                    area = r3Geom[1][0] * r3Geom[1][1]
                    
                    #Intersection
                    intersectionArea = area

                    #Union area
                    unionAreaWidth  = max( predictedObjectBox[1][0], gtObjectBox[1][0]) - min(predictedObjectBox[0][0], gtObjectBox[0][0]) # max right - min left
                    unionAreaHeight = max( predictedObjectBox[1][1], gtObjectBox[1][1]) - min(predictedObjectBox[0][1], gtObjectBox[0][1]) # max bottom - min top
                    unionArea = unionAreaWidth * unionAreaHeight # width * height of the bounding box of the two regions
                    overlapRatio = float(intersectionArea) / unionArea
            
                    if overlapRatio > maxOverlapRatio:
                        maxOverlapRatio = overlapRatio

                    #if maxArea < area:
                        bestMatchObject = gtObject
                        bestMatchObjectBox = gtObjectBox
                        maxArea = area

                idxB2 += 1

            #If the object has no correspondence in the GT
            if bestMatchObjectBox == None:
                nbFalsePos += 1
                if verbose:
                    print 'DEBUG: not match found in GT for prediction:',predictedObjectBox
                    cv2.drawContours(self.img,[predictedObject],0,(0,0,255),2) #BGR
                continue
                #Else if this object has already been predicted
            else:
                #pointList = bestMatchObjectBox
                if bestMatchObjectBox in matchList:            
                    if verbose:
                        print 'DEBUG GT object already discovered:',bestMatchObjectBox,''
                        cv2.drawContours(self.img,[bestMatchObject],0,(100,100,100),1) #BGR
                    cv2.drawContours(self.img,[predictedObject],0,(0,0,255),2) #BGR
                    cv2.putText(self.img, str("%.2f" % overlapRatio),(bestMatchObjectBox[0][0]+5, bestMatchObjectBox[0][1]+15), cv2.FONT_HERSHEY_PLAIN, 0.8,(0,0,255))
                    nbFalsePos += 1
                    continue

            # #Bounding Box Evaluation
            # intersectionArea = maxArea

            # #Union area
            # unionAreaWidth  = max( predictedObjectBox[1][0], bestMatchObjectBox[1][0]) - min(predictedObjectBox[0][0], bestMatchObjectBox[0][0]) # max right - min left
            # unionAreaHeight = max( predictedObjectBox[1][1], bestMatchObjectBox[1][1]) - min(predictedObjectBox[0][1], bestMatchObjectBox[0][1]) # max bottom - min top
            # unionArea = unionAreaWidth * unionAreaHeight # width * height of the bounding box of the two regions
            # overlapRatio = float(intersectionArea) / unionArea
            
            #print 'overlapRatio=',overlapRatio,'for',predictedObjectBox,'and',bestMatchObjectBox,'union and intersection =',intersectionArea,unionArea
            #print 'overlapRatio=',intersectionArea,'/',unionArea,'=',overlapRatio

            #If the object has a overlap ratio < T
            if maxOverlapRatio <= threshold:
                nbFalsePos += 1
                if verbose:
                    cv2.drawContours(self.img,[bestMatchObject],0,(100,100,100),1) #BGR
                    cv2.drawContours(self.img,[predictedObject],0,(0,0,255),2) #BGR
                    cv2.putText(self.img, str("%.2f" % overlapRatio),(bestMatchObjectBox[0][0]+5, bestMatchObjectBox[0][1]+15), cv2.FONT_HERSHEY_PLAIN, 0.8,(0,0,255))
                continue
            else:
                nbTruePos += 1

                #Store the object do not count it twice                
                matchList.append(bestMatchObjectBox)     
                if verbose:
                    print 'DEBUG: new GT object discovered:',bestMatchObjectBox,'for predicted object',predictedObjectBox       
                    cv2.drawContours(self.img,[bestMatchObject],0,(100,100,100),1) #BGR
                    cv2.drawContours(self.img,[predictedObject],0,(0,255,0),2) #BGR
                    cv2.putText(self.img, str("%.2f" % overlapRatio),(bestMatchObjectBox[0][0]+5, bestMatchObjectBox[0][1]+15), cv2.FONT_HERSHEY_PLAIN, 0.8,(0,0,255))

        ##END OF FOR LOOP

        #Count nb of missed detections (false negatives)
        nbFalseNeg = len(self.objectsGT) - nbTruePos

        #Recall
        if (nbTruePos + nbFalseNeg) == 0:
            recall = 0
        else:
            recall = float(nbTruePos)/(nbTruePos + nbFalseNeg)

        #Precision
        if (nbTruePos + nbFalsePos) == 0:
            precision = 0
        else:
            #print 'nbTruePos,nbFalseNeg,nbFalsePos=',nbTruePos,nbFalseNeg,nbFalsePos 
            precision = float(nbTruePos)/(nbTruePos + nbFalsePos)
        
        #f-score
        if (precision + recall) > 0:
            fscore = 2 * precision * recall / (precision + recall)
        else:
            fscore = 0

        if verbose:
            print '***'
            print 'Nb object to detect:',len(self.objectsGT)
            print 'Nb object predicted:',len(self.objectDetected)
            print 'Recall:',recall,'( TP=',nbTruePos,', FN=',nbFalseNeg,')'
            print 'Precision:',precision,'( FP=',nbFalsePos,')'
            print 'f-score:',fscore

            cv2.imwrite(savePath, self.img)
            print 'Saved in '+savePath
               
        return recall, precision, fscore, len(self.objectDetected)

    # Check if a rectangle is empty.
    #
    def is_empty(self, (left, top), (right, bottom)):
            return left >= right or top >= bottom


    # Compute the intersection or two or more rectangles.
    # This works with a list or tuple argument.
    #
    def intersect(self, r1 , rect):
        empty = (0, 0), (0, 0)# The empty rectangle.
        if not list: raise error, 'intersect called with empty list'
        if self.is_empty(r1[0], r1[1]): return empty
        (left, top), (right, bottom) = r1
            
         #for rect in list[1:]:
        if self.is_empty(rect[0], rect[1]):
            return empty
            
        (l, t), (r, b) = rect
        if left < l: left = l
        if top < t: top = t
        if right > r: right = r
        if bottom > b: bottom = b
            
        if self.is_empty((left, top), (right, bottom)):
            return empty
        return (left, top), (right, bottom)


    def getBox(self, array):
        """
            Returns left, top, right, bottom coordinates from a 2 dimensions array
        """
        xList = []
        yList = []
        #TO REPLACE BY NUMPY OPERATION
        for c in array:
            xList.append( c[0][0] )
            yList.append( c[0][1] )
        
        l = numpy.min(xList)
        t = numpy.min(yList)
        r = numpy.max(xList)
        b = numpy.max(yList)
        return (int(l),int(t)),(int(r),int(b))


#########################################################################################

#                                  Public methods                                       #

#########################################################################################



def evaluateTailExtraction(f, inputSVGGroundtruth, inputSVGDetection, outputFolderPNG, verbose):
    """
        Evaluate the tail detection using recall and precision
    """

    #Load balloons detections and ground truth
    balloonsFromExtractor = loadBalloonsFromSVG(f, inputSVGDetection, 'polygon', 'Balloon', verbose)
    balloonsFromGroundtruth = loadBalloonsFromSVG(f, inputSVGGroundtruth, 'polygon', 'Balloon', verbose)

    width, height = toolbox_svg.getImageSizeFromSvg(inputSVGGroundtruth+f)
    matchList = []
    precision = 0
    recall = 0
    nbWrong = 0
    found = 0
    nb = 0
    for balloonExt in balloonsFromExtractor:
        #Ckecking
        #assert balloonExt.tailDirection != '' , 'ERROR: tail direction is not set for balloon'+str(balloonExt.BdB)+' in file '+f
        if balloonExt.tailDirection != '':
            print '\nERROR: tail direction is not set for balloon'+str(balloonExt.BdB)+' in file '+f

        #Find corresponding balloon with the biggest sharing intersection
        balloonMatchGT = getMaxMatchV2(width, height, balloonExt, balloonsFromGroundtruth, outputFolderPNG, verbose)
        
        if balloonMatchGT == None:
            if verbose:
                print '\nERROR: balloon match not found (no evaluation then) for '+str(balloonExt.BdB)+' in '+f
            continue
        pointList = balloonMatchGT.getPoints()
        if pointList in matchList:            
            if verbose:
                print 'ERROR duplicate point list (no evaluation then) in',inputSVGDetection+f,'(',pointList,')'
            continue
        matchList.append(pointList)
        
        #Position (recall)
        # try:
        if balloonMatchGT.tailCoordinates == balloonExt.tailCoordinates:
            recall += 1 #if both have the same value (none OR '' OR X,Y coordinates)
        elif balloonMatchGT.tailCoordinates == '' or balloonExt.tailCoordinates == '':
            recall += 0 #if only one is empty
        else:
            try:
                if (int(balloonMatchGT.tailCoordinates[0]) - 10 < int(balloonExt.tailCoordinates[0]) < int(balloonMatchGT.tailCoordinates[0]) + 10) and (int(balloonMatchGT.tailCoordinates[1]) - 10 < int(balloonExt.tailCoordinates[1]) < int(balloonMatchGT.tailCoordinates[1]) + 10):
                    recall += 1
                elif (int(balloonMatchGT.tailCoordinates[0]) - 20 < int(balloonExt.tailCoordinates[0]) < int(balloonMatchGT.tailCoordinates[0]) + 20) and (int(balloonMatchGT.tailCoordinates[1]) - 20 < int(balloonExt.tailCoordinates[1]) < int(balloonMatchGT.tailCoordinates[1]) + 20):
                    recall += 0.5
            except:
                recall += 0
                print 'WARNING: set recall=0 for',balloonExt.tailCoordinates,'and',balloonMatchGT.tailCoordinates,'for balloon',balloonExt.BdB,'in',f
        
        #Direction (precision)
        if balloonExt.tailDirection == balloonMatchGT.tailDirection:
            precision += 1
            found = 1
        elif balloonExt.tailDirection == 'S' and (balloonMatchGT.tailDirection == 'SE' or balloonMatchGT.tailDirection == 'SW'):
            precision += 0.5
            found = 0.5
        elif balloonExt.tailDirection == 'SE' and (balloonMatchGT.tailDirection == 'S' or balloonMatchGT.tailDirection == 'E'):
            precision += 0.5
            found = 0.5
        elif balloonExt.tailDirection == 'E' and (balloonMatchGT.tailDirection == 'SE' or balloonMatchGT.tailDirection == 'NE'):
            precision += 0.5
            found = 0.5
        elif balloonExt.tailDirection == 'NE' and (balloonMatchGT.tailDirection == 'S' or balloonMatchGT.tailDirection == 'N'):
            precision += 0.5
            found = 0.5
        elif balloonExt.tailDirection == 'N' and (balloonMatchGT.tailDirection == 'NE' or balloonMatchGT.tailDirection == 'NW'):
            precision += 0.5
            found = 0.5
        elif balloonExt.tailDirection == 'NW' and (balloonMatchGT.tailDirection == 'N' or balloonMatchGT.tailDirection == 'W'):
            precision += 0.5
            found = 0.5
        elif balloonExt.tailDirection == 'W' and (balloonMatchGT.tailDirection == 'NW' or balloonMatchGT.tailDirection == 'SW'):
            precision += 0.5
            found = 0.5
        elif balloonExt.tailDirection == 'SW' and (balloonMatchGT.tailDirection == 'W' or balloonMatchGT.tailDirection == 'S'):
            precision += 0.5
            found = 0.5    
        else:
            precision += 0#nbWrong += 1
            found = 0

        if verbose:
            if found == 1:
                print 'Matching',balloonExt.tailDirection,'for',balloonExt.BdB,'and',balloonMatchGT.BdB
            elif found == 0.5:
                print 'Found 50%',balloonExt.tailDirection,'!=',balloonMatchGT.tailDirection ,'between',balloonExt.BdB,'and', balloonMatchGT.BdB,'in',f
                plt.figure()
                plt.imshow(balloonExt.thumbnail)
                plt.show()
            else:
                print 'Found 0%',balloonExt.tailDirection,'!=',balloonMatchGT.tailDirection ,'between',balloonExt.BdB,'and', balloonMatchGT.BdB,'in',f
                plt.figure()
                plt.imshow(balloonExt.thumbnail)
                plt.show()
        
            

        nb += 1

    #Get number of balloons
    nbBalloonsFromExtractor = len(balloonsFromExtractor)
    nbBalloonsFromGroundtruth = len(balloonsFromGroundtruth)

    #IF no balloon to find and no balloon found then return max score
    if nbBalloonsFromExtractor == 0 and nbBalloonsFromGroundtruth == 0:
        return 1,1,1
    else:
        #Avoid division by zero
        if nbBalloonsFromGroundtruth == 0:
            nbBalloonsFromGroundtruth = 1
        elif nbBalloonsFromExtractor == 0:
            nbBalloonsFromExtractor = 1
        return float(recall)/nbBalloonsFromGroundtruth,float(precision)/nbBalloonsFromGroundtruth, nbBalloonsFromExtractor #return recall, precision
    

def loadBalloonsFromSVG(filename, foldername, tagName, attributeClass, verbose):
    polygons = []
    contours = []
    #w, h = imgSize
    nbContour = 0
    #nbMatch = 0
    #nbSmooth = 0
    #nbWavy = 0
    #nbZigzag = 0
    #nbNoTMatch = 0
    sumMeanHeight = 0
    #s = filepath.split(os.sep)
    #filepath = s[len(s) - 1]

    if verbose:
        img = cv2.imread('/media/Donnees/DATA/DATASET/eBDtheque_100/'+filename.split('.')[0]+'.jpg')
    
    if not filename.endswith('svg'):
        print 'ERROR in loadBalloonsFromSVG: not an SVG file (',filename,')'
        return

    w, h = toolbox_svg.getImageSizeFromSvg(foldername+filename)
    xmldoc = parse(foldername+filename)
    itemlist = xmldoc.getElementsByTagName(tagName) # find all polygon elements
    
    #contoursSVGImg = numpy.zeros([h, w], numpy.uint8)
    #defectsImg = numpy.zeros([h, w], numpy.uint8)
    itemListIterator = 0
    for item in itemlist :
        # process only polygon that are in a svg tag with class=Balloon
        if item.parentNode.attributes['class'].value == attributeClass:                
            
            points = item.attributes['points'].value
            coords = points.split(' ')

            balloonType = 'unknown'
            #if loadTypeFromText:
            #    balloonType = getTypeFromTextFile(filepath.split('.')[0]+'.txt', itemListIterator)
            #    itemListIterator += 1
            #else:
            #    for child in item.childNodes:
            #        if child.nodeType == 1:
            #            balloonType = child.attributes['shape'].value
                        
            #if balloonType == 'unknown' or balloonType == '':
            #    print 'WARNING: unknwon or empty balloon type in',filepath,
            
            
            #Convert point list into an array
            contour = toolbox_svg.svgList2NumpyArray(coords)            
                                                                          
            #Barycenter
            M = cv2.moments(contour)
            try:
                c_x = int(M['m10']/M['m00'])
                c_y = int(M['m01']/M['m00'])
            except:
                print 'ERROR: division by zero in barycenter of contour',contour,'in file',filename,'(coords=',coords,')'
                c_x = 0
                c_y = 0
            
            #Spacial position of the balloon  
            t, b, l, r = coord2box(coords, w, h)#xList, yList, w, h )   
            #coef = 100 / max((b-t),(r-l))# / 100.0
            #contourDiv = rint(contour/coef).astype(int) #divide the contour by a scalar and keep the closest integer value. Then convert as integer
            #print 'coef=',coef,'contour=',contour,'contourDiv=',contourDiv
                
            
            #Draw contour to equalize the number of points 
            newDrawing = numpy.zeros([h, w], numpy.uint8)
            cv2.drawContours(newDrawing,[contour],0,(100,50,255),0)
                    
            #Normalize and detect again contour (spatial lost)
            newContours, hierachy = cv2.findContours(newDrawing.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)              
            newContour = newContours[0]

            #Get tail direction and position fro metadata tag
            tailDirection = item.childNodes[1].attributes['tailDirection'].value
            tailTip = item.childNodes[1].attributes['tailTip'].value
            
            #if verbose:
            #    cv2.circle(img,(c_x, c_y),1,[255,0,0],2) #plot barycenter for thumbnail
            #    cv2.circle(img,tuple(newContour[0][0]),1,[0,255,0],2) #plot starting point for thumbnail
                
            if verbose:
                #Draw contour
                cv2.drawContours(img,[newContour],0,(255,0,0),1) #RGB
                #Draw position line
                if tailTip != '':
                    x1, y1 = tailTip.split(',')
                    cv2.circle(img, (int(x1), int(y1)), 5, (0,255,0), 2)

                thumbnail = img[t:b, l:r]
            else:
                thumbnail = None

            #New MyBalloon object
            myBalloon = class_balloon.MyBalloon(points, [c_x, c_y], newContour, balloonType, [t, b, l, r], thumbnail, [c_x, c_y], tailTip, tailDirection )

            #Add new contour to the contour list
            contours.append(myBalloon)          
    
            del contour
    
            #if verbose:
                #Draw contour for later use
                #cv2.drawContours(img,[newContour],0,(255,0,0),1) #RGB
       
            nbContour += 1     
            
    return contours


def getMaxMatchV2(width, height, balloonDetected, balloonsFromGT, outputFolderPNG, verbose):
    """
        Find the corresponding balloons by comparing the overlapping
    """
    maxPrecision = 0
    bestMatchBalloonGT = None

    #Mask for detected balloon
    maskDetection = numpy.zeros((height,width), dtype=numpy.uint8)
    cv2.drawContours(maskDetection,[balloonDetected.shape],0,255,-1) #<0 = fills the area
    nbPixelMaskDetection = (maskDetection == 255).sum()

    #if verbose:
    #    cv2.imwrite(outputFolderPNG+'maskDetection.png',maskDetection)

    #For each balloon in the GT
    for balloonGT in balloonsFromGT:
        #Create mask of the GT balloon
        maskGroundtruth = numpy.zeros((height,width), dtype=numpy.uint8)
        cv2.drawContours(maskGroundtruth,[balloonGT.shape],0,255,-1) #<0 = fills the area
        
        #Binary operation to count the number of shared pixels

        #Count also the number of pixel outside the detected balloon for the GT balloon
        # to measure the matching precision to help the decision in case of several matchings
        intersection  = maskDetection & maskGroundtruth
        nbPixelIntersect = (intersection == 255).sum()
        
        #Skip if no intersection found
        if nbPixelIntersect == 0:
            continue

        #Compare precision (nb pixels outside)
        currentPrecision = float(nbPixelIntersect) / nbPixelMaskDetection
        if maxPrecision < currentPrecision:
            bestMatchBalloonGT = balloonGT #the GT balloon that matched with the highest precision
            maxPrecision = currentPrecision
            #if verbose:
            #    cv2.imwrite(outputFolderPNG+'balloonMatch_'+str(currentPrecision)+'.png',maskGroundtruth)

    if bestMatchBalloonGT == None:
        print 'WARNING: no match found for ',balloonDetected.BdB
    return bestMatchBalloonGT


def coord2box(pointList, w, h):# w, h):
    #w, h = imgSize
    xList = []
    yList = []
    for c in pointList:
        pts = c.split(',')                    
        xList.append(int(pts[0]))
        yList.append(int(pts[1]))

    l = min(xList)
    if(l > 0):
        l = l - 1#enlarge a bit
    t = min(yList)
    if(t > 0):
        t = t - 1#enlarge a bit
    r = max(xList)
    if(r < w):
        r = r + 1#enlarge a bit
    b = max(yList)
    if(b < h - 1):
        b = b + 1#enlarge a bit     
    return t, b, l, r

# Check if a rectangle is empty.
#
def is_empty(r):
    (left, top), (right, bottom) = r
    return left >= right or top >= bottom

# Conversions between rectangles and 'geometry tuples',
# given as origin (h, v) and dimensions (width, height).
#
def rect2geom((left, top), (right, bottom)):
    return (left, top), (right-left, bottom-top)
    
alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYabcdefghijklmnopqrstuvwxyz'

def edits1(word):
   splits     = [(word[:i], word[i:]) for i in range(len(word) + 1)]
   deletes    = [a + b[1:] for a, b in splits if b]
   transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b)>1]
   replaces   = [a + c + b[1:] for a, b in splits for c in alphabet if b]
   inserts    = [a + c + b     for a, b in splits for c in alphabet]
   return set(deletes + transposes + replaces + inserts)

def edits2(word):
    return set(e2 for e1 in edits1(word) for e2 in edits1(e1))

