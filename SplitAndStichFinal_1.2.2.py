###########################
###Version as of 27.4.23
###########################



#@ String (visibility=MESSAGE, value="<html>Folder below should contain ONLY ONE FILE<br/>(i.e the video you want analysed)<html>") message1

#@ File (label="File Directory", style="directory") folder
#@ Integer (label="Number of ATP frames per repeat") atpframes
#@ Integer (label="Number of Zline frames per repeat") zlineframes

#@ String (visibility=MESSAGE, value="<html>TrackMate Setup<p>Please make sure all parameters below<br/>are written to 1 decimal place<br/>except Max Frame Gap") message2
#@ Double (label="TrackMate Threshold", style="format:0.0") threshold
#@ Double (label="TrackMate Linking Distance", style="format:0.0", value = 100) link
#@ Double (label="TrackMate Gap Max Closing Distance", style="format:0.0", value = 100) gap
#@ Integer (label="TrackMate Max Frame Gap", value = 5) frame_gap

#@ String (visibility=MESSAGE, value="Additional Options") message3
#@ String (Label="Rerun Choice For TrackMate",choices={"ATP", "Zlines"}, style="radioButtonHorizontal") RerunChoice
#@ String (label="Run Drift Correction",choices={"Yes","No"}, style="radioButtonHorizontal") DriftCorChoice 

#@ String (label="Choose A Custom ROI?",choices={"Yes","No"},style="radioButtonHorizontal") CustomROI

def SplitAndStich(directory,atpframes,zlineframes,DriftCorChoice,correction="ATP",threshold=2.0,link=100.,gap=100.,frame_gap=20):

    import sys
    import os
    import csv
    import pdb
    
    from ij import IJ
    from ij import WindowManager
    from ij.plugin import FolderOpener
    from java.io import File
    from fiji.plugin.trackmate import Model
    from fiji.plugin.trackmate import Logger
    
    from ij.plugin import Concatenator
    
    
    ##########################
    ###Custom Functions Begin###
    ##########################
    
    ###TrackMateAutomated
    def TrackMateAut(inp,outp,threshold,link=100.,gap=100.,frame_gap=20):
        '''Open an image, run Trackmate and save the output in a CSV file
        From:https://imagej.net/plugins/trackmate/scripting/scripting
       :param outp: path to the output folder 
        :param inp: path to the input image
        :param threshold: changes threshold for the TrackMat LogDetector. Any number should be followed by a "."
        '''
        import sys
        import os
        import csv
        
        from ij import IJ
        from ij import WindowManager
    
        from fiji.plugin.trackmate import TrackMate
        from fiji.plugin.trackmate import Model
        from fiji.plugin.trackmate import SelectionModel
        from fiji.plugin.trackmate import Settings
        from fiji.plugin.trackmate import Logger
        from fiji.plugin.trackmate.detection import LogDetectorFactory
        from fiji.plugin.trackmate.tracking.jaqaman import LAPUtils
        from fiji.plugin.trackmate.tracking.jaqaman import SimpleSparseLAPTrackerFactory
        from fiji.plugin.trackmate.gui.displaysettings import DisplaySettingsIO
        from fiji.plugin.trackmate.visualization.hyperstack import HyperStackDisplayer
        
        from fiji.plugin.trackmate.visualization.table import AllSpotsTableView
        from fiji.plugin.trackmate.visualization.table import TrackTableView
        from fiji.plugin.trackmate.action import ExportAllSpotsStatsAction
        from fiji.plugin.trackmate.action import ExportStatsTablesAction
        from fiji.plugin.trackmate.visualization.table import TablePanel
        from java.io import File
        from ij.gui import Roi, PolygonRoi
        from ij.gui import WaitForUserDialog
         
    

    
        # We have to do the following to avoid errors with UTF8 chars generated in 
        # TrackMate that will mess with our Fiji Jython.
        reload(sys)
        sys.setdefaultencoding('utf-8')
        
        
        if os.path.isfile(str(outp) + ".csv"):
            imp = WindowManager.getImage(str(inp))
        else:
            imp = IJ.openImage(inp)
            if imp is None:
                imp = WindowManager.getCurrentImage()
            else:
                imp.show()
        
        #Set Roi 10 pixels away from the edge to illimitate possible unspesific detection 
        w = imp.getWidth()
        h = imp.getHeight()


        #### WIP ####
        ### Making adjustable ROI for trackmate ####
        
        if CustomROI == "Yes":
            
            # Activate freehand tool
            IJ.setTool("freehand")
            
            # Show dialog box with message and "OK" button
            dialog = WaitForUserDialog("Draw the ROI. Click OK when ready.")
            dialog.show()
            
        else:
        	#Set a standard ROI
       		imp.setRoi(5,5,w-10,h-10) 

        #-------------------------
        # Instantiate model object
        #-------------------------
    
        model = Model()
    
        # Set logger
        model.setLogger(Logger.IJ_LOGGER)
    
        #------------------------
        # Prepare settings object
        #------------------------
    
        settings = Settings(imp)
    
        # Configure detector 
        settings.detectorFactory = LogDetectorFactory()
        settings.detectorSettings = {
            'DO_SUBPIXEL_LOCALIZATION' : True,
            'RADIUS' : 195.,
            'TARGET_CHANNEL' : 1,
            'THRESHOLD' : threshold,
            'DO_MEDIAN_FILTERING' : False,
        }
    
        # Configure tracker
        settings.trackerFactory = SimpleSparseLAPTrackerFactory()
        settings.trackerSettings = LAPUtils.getDefaultSegmentSettingsMap()
        settings.trackerSettings['LINKING_MAX_DISTANCE'] = link
        settings.trackerSettings['GAP_CLOSING_MAX_DISTANCE'] = gap
        settings.trackerSettings['MAX_FRAME_GAP'] = frame_gap
    
        # Add the analyzers for some spot features.
        # Here we decide brutally to add all of them. 
        settings.addAllAnalyzers()
    
        # We configure the initial filtering to discard spots 
        # with a quality lower than 1.
        settings.initialSpotFilterValue = 1.
    
        print(str(settings))
    
        #----------------------
        # Instantiate trackmate
        #----------------------
    
        trackmate = TrackMate(model, settings)
    
        #------------
        # Execute all
        #------------
    
    
        ok = trackmate.checkInput()
        if not ok:
            sys.exit(str(trackmate.getErrorMessage()))
    
        ok = trackmate.process()
        if not ok:
            sys.exit(str(trackmate.getErrorMessage()))
    
    
    
        #----------------
        # Display results
        #----------------
    
        model.getLogger().log('Found ' + str(model.getTrackModel().nTracks(True)) + ' tracks.')
    
        # A selection.
        sm = SelectionModel( model )
    
        # Read the default display settings.
        ds = DisplaySettingsIO.readUserDefault()
    
        # The viewer.
        displayer =  HyperStackDisplayer( model, sm, imp, ds ) 
        displayer.render()
    
        # The feature model, that stores edge and track features.
        fm = model.getFeatureModel()
    
    
        # Iterate over all the tracks that are visible.
        for id in model.getTrackModel().trackIDs(True):
    
            # Fetch the track feature from the feature model.
            v = fm.getTrackFeature(id, 'TRACK_MEAN_SPEED')
            model.getLogger().log('')
            model.getLogger().log('Track ' + str(id) + ': mean velocity = ' + str(v) + ' ' + model.getSpaceUnits() + '/' + model.getTimeUnits())
    
            # Get all the spots of the current track.
            track = model.getTrackModel().trackSpots(id)
            for spot in track:
                sid = spot.ID()
                # Fetch spot features directly from spot.
                # Note that for spots the feature values are not stored in the FeatureModel
                # object, but in the Spot object directly. This is an exception; for tracks
                # and edges, you have to query the feature model.
                x=spot.getFeature('POSITION_X')
                y=spot.getFeature('POSITION_Y')
                t=spot.getFeature('FRAME')
                q=spot.getFeature('QUALITY')
                snr=spot.getFeature('SNR_CH1')
                mean=spot.getFeature('MEAN_INTENSITY_CH1')
                model.getLogger().log('\tspot ID = ' + str(sid) + ': x='+str(x)+', y='+str(y)+', t='+str(t)+', q='+str(q) + ', snr='+str(snr) + ', mean = ' + str(mean))
    
    
    
        ##Export TrackMate analysis to the .csv
        Export = TrackTableView(trackmate.getModel(), sm, ds)
        Table = Export.getTrackTable()
        ## put adress of the directory you want to work in 
        os.chdir(outp) 
        ##adress plus file name 
        file = File (str(outp) + ".csv") 
        Table.exportToCsv(file)
        return imp
    
    ## Function to return a list of images in file format from a "path" folder
    def batch_open_images(path, file_type=None, name_filter=None, recursive=False):
        ''' 
        NOT MINE https://imagej.net/imagej-wiki-static/Jython_Scripting
        Open all files in the given folder.
        :param path: The path from were to open the images. String and java.io.File are allowed.
        :param file_type: Only accept files with the given extension (default: None).
        :param name_filter: Only accept files that contain the given string (default: None).
        :param recursive: Process directories recursively (default: False).
        '''
        # Converting a File object to a string.
        if isinstance(path, File):
            path = path.getAbsolutePath()
    
        def check_type(string):
            '''This function is used to check the file type.
            It is possible to use a single string or a list/tuple of strings as filter.
            This function can access the variables of the surrounding function.
            :param string: The filename to perform the check on.
            '''
            if file_type:
                # The first branch is used if file_type is a list or a tuple.
                if isinstance(file_type, (list, tuple)):
                    for file_type_ in file_type:
                        if string.endswith(file_type_):
                            # Exit the function with True.
                            return True
                        else:
                            # Next iteration of the for loop.
                            continue
                # The second branch is used if file_type is a string.
                elif isinstance(file_type, string):
                    if string.endswith(file_type):
                        return True
                    else:
                        return False
                return False
            # Accept all files if file_type is None.
            else:
                return True
    
        def check_filter(string):
            '''This function is used to check for a given filter.
            It is possible to use a single string or a list/tuple of strings as filter.
            This function can access the variables of the surrounding function.
            :param string: The filename to perform the filtering on.
            '''
            if name_filter:
                # The first branch is used if name_filter is a list or a tuple.
                if isinstance(name_filter, (list, tuple)):
                    for name_filter_ in name_filter:
                        if name_filter_ in string:
                            # Exit the function with True.
                            return True
                        else:
                            # Next iteration of the for loop.
                            continue
                # The second branch is used if name_filter is a string.
                elif isinstance(name_filter, string):
                    if name_filter in string:
                        return True
                    else:
                        return False
                return False
            else:
            # Accept all files if name_filter is None.
                return True
    
        # We collect all files to open in a list.
        path_to_images = []
        # Replacing some abbreviations (e.g. $HOME on Linux).
        path = os.path.expanduser(path)
        path = os.path.expandvars(path)
        # If we don't want a recursive search, we can use os.listdir().
        if not recursive:
            for file_name in os.listdir(path):
                full_path = os.path.join(path, file_name)
                if os.path.isfile(full_path):
                    if check_type(file_name):
                        if check_filter(file_name):
                            path_to_images.append(full_path)
        # For a recursive search os.walk() is used.
        else:
            # os.walk() is iterable.
            # Each iteration of the for loop processes a different directory.
            # the first return value represents the current directory.
            # The second return value is a list of included directories.
            # The third return value is a list of included files.
            for directory, dir_names, file_names in os.walk(path):
                # We are only interested in files.
                for file_name in file_names:
                    # The list contains only the file names.
                    # The full path needs to be reconstructed.
                    full_path = os.path.join(directory, file_name)
                    # Both checks are performed to filter the files.
                    if check_type(file_name):
                        if check_filter(file_name):
                            # Add the file to the list of images to open.
                            path_to_images.append(full_path)
        # Create the list that will be returned by this function.
        images = []
        for img_path in path_to_images:
            # IJ.openImage() returns an ImagePlus object or None.
            imp = IJ.openImage(img_path)
            # An object equals True and None equals False.
            if imp:
                images.append(imp)
        return images
    
    ## Loads a difined "i" file form a folder and changes it's dimentions to OAF settings
    #Set to load only the first file by default
    def load(path, i=0 ):
        image = batch_open_images(path)
        imp = image [i]
        # Change dimesntions
        imp.getCalibration().setXUnit("nm")
        imp.getCalibration().setYUnit("nm")
        imp.getCalibration().setZUnit("nm")
    
        dims = imp.getDimensions()
        if (dims [4] == 1):
            IJ.run(imp, "Properties...", "channels=1 slices=" + str(dims[4]) + " frames=" + str(dims[3]) + " pixel_width=63 pixel_height=63 voxel_depth=63 frame=[2 sec]")
        return imp
    
    
    ## Function to split into ATP and Z-line slices and save in a folder
    def split(atpframes,zlineframes,path,imp):
            
        #check if ATP and Zlines have already beed made, if not, create
        
        if not os.path.isdir(str(path) + "\ATP"):
        
            os.makedirs(str(path) + "\ATP")
            os.makedirs(str(path) + "\Zlines")
        
        #set up the loger 
        model = Model()
        model.setLogger(Logger.IJ_LOGGER)
        
        n = 1
        i = 0
        b = 0.
         
        
        #make sure the number of stacks is correct through the logger
        dims = imp.getDimensions()
        num = long(dims[4])/(atpframes+zlineframes) - 5
        model.getLogger().log("Stack Number: " + str(dims[4]))
        model.getLogger().log("Repeat Number: " + str(num))
        
        #split and save
        while b < num:

            a = imp.crop(str(n) + "-" + str(n+atpframes-1))
            IJ.saveAs(a, "Tiff", str(path) + "\ATP" + "\ATP" + str(b) )

            z = imp.crop(str(n+atpframes+zlineframes-1) + "-" + str(n+atpframes+zlineframes-1))
            IJ.saveAs(z, "Tiff", str(path) + "\Zlines" + "\Zlines" + str(b))
    
            n+= atpframes+zlineframes
            b+=1

            #save Z-line copies
            c = 0
            while c < (atpframes-1):
            
                IJ.saveAs(z, "Tiff", str(path) + "\Zlines" + "\Zlines" + str(b-1) + "_" + str(c+1) )
                
                c+=1
    
    
    ##Function to return concatenatored vidios from a set folder 
    def stich(path):
        conc = FolderOpener.open(str(path)+"\\", "");
        return conc
    
    
    ##Function to remove all files form a folder     
    def remove_files(path):
        for file_name in os.listdir(path):
                full_path = os.path.join(path, file_name)
                os.remove(str(full_path))
    
    
    
    ##Function to run put ATP and Z-line stacks together, apply drift correction and save sepparatly 
    #NOTE: when using interactive drift correction plugin, one should make sure to choose only a handfull of points which are assured to stay throughout the most(ideally all) of the stack
    def driftcor (drATP,drZline):
    
        #open both stacks
        ATP = IJ.openImage(drATP + "\ATP.tif")
        Zlines = IJ.openImage(drZline + "\Zlines.tif")
        ATP.show()
        Zlines.show()
    
        #Merge stacks using merge channels 
        IJ.run(ATP, "Merge Channels...", "c5=Zlines.tif c6=ATP.tif create")
    
        #Run Drift corrector plugin
        IJ.run("Descriptor-based series registration (2d/3d + t)", "series_of_images=Merged brightness_of=[Interactive ...] approximate_size=[Interactive ...] type_of_detections=[Interactive ...] subpixel_localization=[3-dimensional quadratic fit] transformation_model=[Translation (2d)] images_are_roughly_aligned number_of_neighbors=3 redundancy=1 significance=3 allowed_error_for_ransac=5 global_optimization=[All-to-all matching with range ('reasonable' global optimization)] range=5 choose_registration_channel=1 image=[Fuse and display] interpolation=[Linear Interpolation]")
        Merged = WindowManager.getImage("Merged")
        Merged.close()
    
        #Split channels 
        IJ.run("Split Channels")
    
        #Save ATP Results
        ATP = WindowManager.getImage("C2-registered Merged")
        #ATP.setDisplayRange(89, 250)
        ATP.getCalibration().setXUnit("nm")
        ATP.getCalibration().setYUnit("nm")
        ATP.getCalibration().setZUnit("nm")
        IJ.run(ATP, "Properties...", " pixel_width=63 pixel_height=63 voxel_depth=63 frame=[2 sec]")
        IJ.run(ATP, "Grays","")
        IJ.saveAs(ATP, "Tiff", drATP + "\ATP")
        ATP.close()
    
        #Save Zlines Results
        zlines = WindowManager.getImage("C1-registered Merged")
        #zlines.setDisplayRange(89, 250)
        zlines.getCalibration().setXUnit("nm")
        zlines.getCalibration().setYUnit("nm")
        zlines.getCalibration().setZUnit("nm")
        IJ.run(zlines, "Properties...", " pixel_width=63 pixel_height=63 voxel_depth=63 frame=[2 sec]")
        IJ.run(zlines, "Grays","")
        IJ.saveAs(zlines, "Tiff", drZlines + "\Zlines")
        zlines.close()
    
    ##Function to open the Corrected Zline file, cut out the repeat stacks and save over the CorrectedZline.tif 
    #EZR = Excess Zline Removal 
    ##Takes three parameter: zlinedir - path to the directory with CorrectedZlines.tif file 
    def EZR (zlinedir,atpframes,zlineframes):
        
        from fiji.plugin.trackmate import Model
        from fiji.plugin.trackmate import Logger
        
        drZlines = zlinedir
        Temp = (drZlines +"\Temp")

        
        os.makedirs(Temp)

        imp = IJ.openImage(drZlines + "\Zlines.tif")
        imp.show()
        zlines = WindowManager.getImage("Zlines.tif")
    
        model = Model()
        model.setLogger(Logger.IJ_LOGGER)
        
        dims = zlines.getDimensions()
        b = 0
        n = 1
        limits = long(dims[4])/(atpframes-1+zlineframes)
        
        while b < (limits-5):
            
            z = zlines.crop(str(n) + "-" + str(n))
            IJ.saveAs(z, "Tiff", str(Temp) + "\Zlines" + str(n))
            model.getLogger().log("Zlines " + str(n) + " Saved")
            n+=(atpframes-1+zlineframes)
            b+=1
            
        model.getLogger().log("Repeats " + str(limits))
        imp.close()
        imp = stich(Temp)
        remove_files(Temp)
        os.rmdir(Temp)
        
        dims = imp.getDimensions()
        if (dims [4] == 1):
            IJ.run(imp, "Properties...", "channels=1 slices=" + str(dims[4]) + " frames=" + str(dims[3]) + " pixel_width=63 pixel_height=63 voxel_depth=63 frame=[2 sec]")
        
        IJ.saveAs(imp,"Tiff",str(drZlines) + "\Zlines")  
    
    
    ##########################
    ####Custom Functions END####
    ##########################
        
    
    #####
    ###Put all this code to work
    #####
    
    #Set working folder
    folder = directory
    
    #Set analysis folder
    analysis = (str(folder) + "\Analysis")
    
    #Define ATP and Z-lines folders
    drATP = (str(analysis) + "\ATP")
    drZlines = (str(analysis) + "\Zlines")
    
    ##If analysis folder is not set up yet (i.e first analysis , loaded the image, split the image and TrackMate )
    if not os.path.isdir(analysis):
        imp = load(folder)
        split(atpframes,zlineframes,analysis,imp)
        
        #ATP
        atp = stich(drATP)
        remove_files(drATP)
        
        dims = atp.getDimensions()
        if (dims [4] == 1):
            IJ.run(atp, "Properties...", "channels=1 slices=" + str(dims[4]) + " frames=" + str(dims[3]) + " pixel_width=63 pixel_height=63 voxel_depth=63 frame=[2 sec]")
        
        IJ.saveAs(atp,"Tiff",str(drATP) + "\ATP")
        
        #Zlines
        zlines = stich(drZlines)
        remove_files(drZlines)
        
        dims = zlines.getDimensions()
        if (dims [4] == 1):
            IJ.run(zlines, "Properties...", "channels=1 slices=" + str(dims[4]) + " frames=" + str(dims[3]) + " pixel_width=63 pixel_height=63 voxel_depth=63 frame=[2 sec]")
        
        IJ.saveAs(zlines,"Tiff",str(drZlines) + "\Zlines")
        
        #Run Drift Corrector if requested 
        if DriftCorChoice == "Yes":
            #Run drift correction on both 
            driftcor(drATP,drZlines)
    
        #Run EZR on the corrected Zline stack
        EZR (drZlines,atpframes,zlineframes)
    
        #Run TrackMate on both
        TrackMateAut(str(drATP) + "\ATP.tif",analysis+"\ATP",threshold,link,gap,frame_gap)
        TrackMateAut(str(drZlines) + "\Zlines.tif",analysis+"\Zlines",threshold,link,gap,frame_gap)     
    else:
        ##Run TrackMateAutomated on both Zlinesa and ATP to adjust the threshold
        #All objects after and including Threshold have to be followed by "." eg 5. or 4. , except for frame_gap
        if correction == "ATP":
            TrackMateAut("ATP.tif",analysis+"\ATP",threshold,link,gap,frame_gap)
        if correction == "Zlines":
            TrackMateAut("Zlines.tif",analysis+"\Zlines",threshold,link,gap,frame_gap)
            
#d = os.listdir('C:\\Users\\Labuser\\Desktop\\Analysis MP')
#length = len (d)
SplitAndStich(folder,atpframes,zlineframes,DriftCorChoice,RerunChoice,threshold,link,gap,frame_gap)