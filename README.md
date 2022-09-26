# Screw It: I'll describe the basics
# Anatomy of the repo atm

"FarmGrandOrder": this folder contains the workhorse python code, FarmGrandOrder.py.
  There are also 2 other python for potential testing/debugging, "Nodes.py" and "NodesTest.py". "NodesTest.py" is meant to run debugging programs to see if potential changes to the Nodes Class will change the output matrix or run slower. This isn't quite complete yet, and probably needs to be updated. "Nodes.py" was originally meant to house the changed Nodes Class for the comparisons that "NodesTest.py" did, but I think I just started putting those changes in "NodesTest.py," so right now it's not important.
  My cache is in there and I don't think it's supposed to be. Should probably just delete it, I don't know what kind of problems having my computer's cache in there causes when trying to run the program.

"config": this folder contains the config file which FarmGrandOrder.py reads to know what it should do. Work in progress.

"Files": this folder contains all the csv's atm which FarmGrandOrder reads to do its analysis. The weird names for most of the csv's is caused by google sheets. That's     just the names sheets gave them when I downloaded the files, and I'm keeping them as is for simplicity.
  "GOALS.csv": where you're supposed to put your mat farming goals. Currently my own goals (I think, my other sheet might have been bugged and this needs to get fixed).
  "GOALSRandom.csv": a relately arbitrary list that needs all materials. Could be used for testing whether the outputs work properly or not.
  "Efficiency_ - APD.csv": used so the main program knows the drop rate of every Singularity/Lost Belt free quest.
  "Efficiency_ - Calc.csv": used so the main program can use material names to put values in the proper spot on the matrix when reading event free quest data.
  "Efficiency_ Hunting 9 PER - Event Quest.csv": drop rates for a random event quest, currently being read if the 'config' isn't on MultEvent mode.
  
  "Events": Folder which contains the event quest drop rates for every FGO event in the next 2 years. Also has the "Multi Event Folder."
    "Multi Event Folder": when MultEvent mode is turned on in config, the program reads every single event csv in this folder and creates a big matrix.
    "Christmas 202X": These are separated because otherwise they'd take up way too much space in the main "Events" folder.
    Anatomy of Lotto Event Names: Lotto events have some extra words on the end of them, after the event name but before the "- Event Quest.csv". The number after the "D" refers to the drop bonus used in the drop rate calculations. So "D4" means that you have the CEs to get +4 lotto mats, and "D12" means you're maxed out on boosting CEs. The Christmas lottos also have a shortened material name at the end. This means that the calculations are assuming you intend to spend your lotto box tickets on that item (by placing all 3 in the Multi Event Folder, the program can work out which materials you should redeem with those tickets). Finally, the "BB" at the end means "Buyback," which means that the AP Cost for running the event quests is reduced by the average amount of apples you're expected to get back from opening boxes.
