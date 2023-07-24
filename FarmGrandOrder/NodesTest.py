import csv
import glob
import numpy as np
import cvxpy as cp

class Nodes:
    def __init__( self, goals, materialListCSV, removeZeros = False ):
        self.matCount = 0
        self.matTotal = 0
        self.skipDataIndex = {}
        self.removeZeros = removeZeros

        self.goals = []
        self.IDtoIndex = {-1: [], -2: [], -3: [], -4: [], -5: [], -6: 'T'}
        self.indexToName = {}
        self.interpretCSVs( goals, materialListCSV )

        self.nodeNames = []
        self.APCost = []
        self.runCap = []
        self.dropMatrix = np.array([])
        self.hellfireRange = [9700000,500]
    
    # Interpret the Materials by groups between their gaps.
    def interpretGroup( self, reader, matID, matName, count, index, gaps, error ):
        row = next(reader)
        if row[0] != error[0]:
            debug.errorWarning( 'Does not seem to be the start of '+ error[1] +'. GOALS and/or Material List CSVs may need to be updated.' )
        
        while row[0][0:2] != '!!':
            try:
                matGoal = int(row[1])
            except:
                matGoal = 0
            
            # Flag whether or not to remove this material from the Drop Matrix.
            skip = self.removeZeros and (matGoal == 0)
            self.skipDataIndex[count] = skip

            count += 1
            row = next(reader)
            
            if skip:
                self.IDtoIndex.setdefault( int(matID[count]), 'T' )
            else:
                self.goals.append( [matGoal] )
                self.IDtoIndex.setdefault( int(matID[count]), index )
                self.indexToName.setdefault( index, matName[count] )
                index += 1

                if gaps > 2:
                    self.IDtoIndex[2-gaps].append( int(matID[count]) )

        self.skipDataIndex[count] = self.removeZeros
        count += 1
        if not self.removeZeros:
            self.goals.append([0])
            self.indexToName.setdefault( index, '' )
            index += 1

        # Notes that negative Mat IDs should be skipped if the entry is empty.
        if gaps > 2:
            if self.IDtoIndex[2-gaps] == []:
                self.IDtoIndex[2-gaps] = 'T'
        
        return reader, count, index

    # Creates three dictionaries, 'IDtoIndex' maps a Material's ID to placement in Drop Matrix, or notes that it should be skipped with a 'T' value.
    # 'indexToName' maps placement in Drop Matrix to the corresponding Material's name.
    # 'skipDataIndex' maps whether or not an entry in the Free Drop Matrix should be skipped.
    # Also transforms the data in the GOALS csv into a computable column matrix.
    # count is generally incremented before 'matID' and 'matName' because the 0th index is not the start of the relevant values.
    def interpretCSVs( self, goals, materialListCSV ):
        with open( materialListCSV, newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)
            matID = next(reader)
            while( matID[0][0:2] != 'ID' ):
                matID = next(reader)
            matName = next(reader)
            f.close()
        
        with open( goals, newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)
            row = next(reader)

            count = 0
            index = 0

            # Warn if the gaps between Material groups do not line up.
            errors = [['Proof of Hero', 'Bronze Mats'],['Seed of Yggdrasil','Silver Mats'],['Claw of Chaos','Gold Mats'], 
                         ['Gem of Saber','Blue Gems'], ['Magic Gem of Saber','Red Gems'], ['Secret Gem of Saber','Gold Gems'],
                         ['Saber Piece','Statues'], ['Saber Monument', 'Monuments']]

            for gaps in range(8):
                reader, count, index = self.interpretGroup( reader, matID, matName, count, index, gaps, errors[gaps] )

            row = next(reader)
            if row[0] != 'Saber Blaze':
                debug.errorWarning( 'Does not seem to be the start of XP. GOALS and/or Material List CSVs may need to be updated.' )
            
            try:
                matGoal = int(row[1])
            except:
                matGoal = 0
            f.close()
        
        # 'Saber Blaze' index will be used in place of all XP drops.
        self.matCount = index
        skip = self.removeZeros and (matGoal == 0)
        if skip:
            index = 'T'
        else:
            self.goals.append( [matGoal] )
            self.IDtoIndex[-6] = [ int(matID[count+1]) ]
            self.indexToName.setdefault( index, 'Class Blaze' )
            self.matCount += 1

        for i in range(16):
            self.skipDataIndex[count] = skip
            count += 1
            self.IDtoIndex.setdefault( int(matID[count]), index )
        
        self.matTotal = count
        self.goals = np.array(self.goals)

    # TODO: There are some issues with this method of assembling matrices.
    # The basic issue is that cvxpy analysis requires data in the form of numpy matrices, but the best way to form numpy matrices is to initialize its size.
    # This is because vstacking numpy matrices line by line is slow, because it rewrites the entire matrix every time.
    # ^^^ NOT CONFIRMED, maybe that's what I should do.
    # Unfortunately, in order to initialize the size, we have to know how many lines the csv is. This apparently requires reading through the entire csv once.
    # Since the csv's have to be read and added to the data line by line, this would be inelegant/slow.
    # For the above reasons, I have instead opted to put the data from the csv into an array first, and then turn those arrays into a numpy matrix before stacking.
    # This seems to have caused an issue with making a 'Run Cap' constraint, as the column matrixes are size '(X,)' rather than '(X,1)'
    # This doesn't make sense and tells me there needs to be some changes.

    # FIXED SIZE PROBLEM: rest should still be looked into.
    def assembleMatrix( self, addAPCost, addRunCap, addDropMatrix ):
            if np.size( self.dropMatrix ) == 0:
                self.APCost = np.array( addAPCost )
                self.runCap = np.array( addRunCap )
                self.dropMatrix = np.array( addDropMatrix )
            else:
                self.APCost = np.vstack(( self.APCost, addAPCost ))
                self.runCap = np.vstack(( self.runCap, addRunCap ))
                self.dropMatrix = np.vstack(( self.dropMatrix, addDropMatrix ))
    
    def addEventDrop( self, eventDropCSV, debug, multEvent, eventCap = '' ):
        start = eventDropCSV.rindex('Efficiency ')+len('Efficiency ')
        eventName = eventDropCSV[(start):eventDropCSV.rindex(' - Event',start)]

        if not multEvent:
            debug.fileName = eventName
        debug.makeNote( eventName + '\n' )

        with open( eventDropCSV, newline = '', encoding = 'latin1' ) as f:
            reader = csv.reader(f)
        
            # Finds where the lotto material drops start in the csv, as the formatting changes for these.
            materialLoc = []
            while materialLoc == []:
                try:
                    eventDrop = next(reader)
                except:
                    debug.errorWarning( 'Sheet does not have columns labeled "ID".' )
                count = 0
                for i in eventDrop:
                    if i == 'ID': 
                        materialLoc.append(count)
                    count += 1

            eventAPCost = []
            eventDropMatrix = []
            eventRunCap = []

            # Interpretation of how this is supposed to read the Event Quest csv:
            # If there is no material assigned in the first slot, skip this line.
            # If there is an AP assigned, assume the drops are part of a new node and start a new line of the Drop Matrix.
            # Add drops to the last made line in the Drop Matrix.
            for eventNode in reader:
                if materialLoc[0] == '': 
                    continue

                if eventNode[1] != '':
                    self.nodeNames.append( eventName + ', ' + eventNode[0] )
                    eventAPCost.append( [float(eventNode[1])] )
                    eventRunCap.append( [eventCap] )
                    eventDropMatrix.append( np.zeros( self.matCount ) )

                for i in materialLoc:
                    if eventNode[i+2] != '':
                        matID = int(eventNode[i])
                        if self.IDtoIndex[matID] == 'T':
                            continue

                        dropRate = float(eventNode[i+2]) / 100
                        if matID >= self.hellfireRange[0] and matID % self.hellfireRange[1] == 0:
                            dropRate *= 3

                        if matID < 0:
                            matID = self.IDtoIndex[matID]
                        else:
                            matID = [matID]
                        for j in matID:
                            eventDropMatrix[-1][ self.IDtoIndex[j] ] += dropRate
            f.close()
            
            self.assembleMatrix( eventAPCost, eventRunCap, eventDropMatrix )
    
    def addFreeDrop( self, freeDropCSV, lastArea ):
        with open( freeDropCSV, newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)

            # Find the starting index of the Materials and where the XP starts.
            matStart = 0
            matEnd = 0
            while matEnd == 0:
                try:
                    freeDrop = next(reader)
                except:
                    debug.errorWarning( 'Sheet does not have a column labeled as referencing "Monument" mats.' )
                for i in range(len(freeDrop)):
                    if freeDrop[i].find('Bronze') >= 0:
                        matStart = i
                    if freeDrop[i].find('Monument') >= 0:
                        matEnd = i+9
                        break
            if matStart == 0:
                debug.errorWarning( 'Sheet does not have a column labeled as referencing "Bronze" mats.' )
            
            freeAPCost = []
            freeRunCap = []
            freeDropMatrix = []

            # Interpretation of how this is supposed to read the APD csv:
            # If the Singularity is further than the user wants to farm as defined in the config file, stop.
            # If the line is filler because the original google sheet copies the Japanese document formatting, skip it.
            # Else, start a new line of drop rate data.
            for freeDrop in reader:
                if freeDrop[0].find( lastArea ) >= 0: 
                    break

                if freeDrop[2] == '' or freeDrop[2] == 'AP': 
                    continue

                nodeAP = int(freeDrop[2])
                self.nodeNames.append( freeDrop[0] + ', ' + freeDrop[1] )
                freeAPCost.append( [nodeAP] )
                freeRunCap.append( [100000] )
                dropMatrixAdd = []

                for i in range(matStart,matEnd):
                    if not self.skipDataIndex[i-matStart]:
                        try: 
                            dropMatrixAdd.append( nodeAP / float(freeDrop[i]) )
                        except:
                            dropMatrixAdd.append(0)
                
                if not self.skipDataIndex[i-matStart]:
                    XPMult = 1
                    for i in range(matEnd,matEnd+14):
                        if i == matEnd + 6:
                            XPMult = 3
                        try:
                            dropMatrixAdd[-1] += XPMult * nodeAP / float(freeDrop[i])
                        except:
                            dropMatrixAdd[-1] += 0

                freeDropMatrix.append( dropMatrixAdd )
            f.close()
            
            self.assembleMatrix( freeAPCost, freeRunCap, freeDropMatrix )
    
    def multiEvent( self, path, debug, eventFind, multEvent, eventCap = '' ):
        if multEvent:
            debug.fileName = 'Multi'
            debug.makeNote( 'The Events included in this analysis are:\n' )
            eventFolder = glob.glob( path + 'Events\\Multi Event Folder\\*' )
        else:
            debug.make( 'The Event included in this analysis is: ')
            eventFolder = glob.glob( path + '*' + eventFind + '* - Event Quest.csv' )

        for event in eventFolder:
            self.addEventDrop( event , debug , multEvent, eventCap )
        
        debug.makeNote('\n')