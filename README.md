# Fate/Grand Farm

<p align="center">
  <img width="200" src="https://i.imgur.com/7efNMgy.png?1">
</p>

Fate/Grand Farm is a Python program designed to aid players in the mobile game 'Fate/Grand Order' by utilizing linear programming to create optimal farming plans for Materials.

## Introduction

With the variety of Materials in the game, some of which don't help any of the Servants you rolled, it can be difficult to optimally plan your farming route. Even if you plan the best route for farming Free Quests, Events can offer much better drop rates. With readily available open-sourced data for Events, and the global version lagging 2 years behind the Japanese version, there has to be a better way to reach your farming goals? This is where Fate/Grand Farm comes to your rescue! Input your farming goals, select which Events you want to analyze, possibly change some configurations if you're into that, press that exe button, and have the next 2 years of your grinding life dictated to you by a machine!

The executable only works for Windows. If you use another Operating System (or run into other problems), look into the 'Troubleshooting' section below to find out what you need for the Python program.

*Note: As the linear programming algorithms can only compute averages, the actual number of runs required to reach your goal may be highly variable for a low number of Materials required.*

## How to Use
  1. Open 'GOALS.csv', and input the number of Materials you desire next to the corresponding Material. XP cards are all condensed into one entry. Save.
  2. Move/copy all Event '.csv's in the 'Events List' folder to the 'Events Farm' folder that you want to be included in the analysis.
  3. Open 'fgf_config.ini' and change any settings you want. Save.
  4. Run 'Fate_Grand_Farm.exe'

For more details on how configuring the analysis or managing/upkeeping Event data, scroll down to the 'Set Up' section. This is mostly helpful for creating Event specific Run Caps.

## How to Read the Output
After running the program, you will find 3 output files in the main directory ('FateGrandFarm'), all of which will replace previous files. These are 'Farming Plan.txt', 'Farming Plan Drops'.txt, and 'Debug.txt'. Extra copies will be placed in the 'Former Plans' folder, using the 'Plan Name' configured in 'fgf_config.ini', if any.

'Farming Plan.txt' presents the optimized farming plan generated by the program. The 1st line should say that the results are 'optimal,' and the 2nd line will provide the Total AP for the plan. For each line in the following analysis;

> 1st Entry: Name of the Event/Singularity/Lost Belt. The Event name is determined by the name of the corresponding '.csv' file.
>
> 2nd entry: Quest/node name.
>
> 3rd entry: Suggested number of times it should be run. Expected number of gained Boxes is also included for Lotto runs.

'Farming Plan Drops.txt' is very similar to 'Farming Plan'. However, it also lists the expected number of each Material dropped for those runs. Note that if the 'Remove Zeros' configuration is on, it will not include Materials who have no goal.

'Debug' contains all the information necessary to properly understand the context for the corresponding 'Farming Plan.' This includes all the Errors that came up, Configurations, the Events included, and Lotto Drop Rate boosts.

## Troubleshooting
Fate/Grand Farm was programmed in Python 3.9, and the necessary libraries are: [NumPy](https://numpy.org/), [SciPy](https://scipy.org/), and [CVXPY](https://www.cvxpy.org/).

It is recommended to download and install [Anaconda.](https://www.anaconda.com/) If you encounter any issues finding CVXPY, you may need to add the 'conda-forge' channel.

After setting up the required Python environment and libraries, navigate to the 'Code' folder and execute 'Fate_Grand_Farm.py' by running the following command in your terminal or command prompt:
```
python Fate_Grand_Farm.py
```

## Set Up
## 'Events List' Folder
Contains the drop rate data for various Events in '.csv' format. Lotto Events have their own folders to help organize the data. 

Lotto Events have their own additional naming convention:
 * '-D#' describes the Drop Rate Bonus used in the analysis, as the Materials obtained from Boxes are added to each quest's drop rate table.
 * '-D-' means that boxes are not included in the analysis.
 * Any truncated Material name after '-D#-' represents the Material to be obtained using the ticket from the Lotto Box.

For example, 'Christmas 2023 -D12-Claw' signifies the drop rate table of all 'Christmas 2023' quests, assuming that you have a +12 Drop Rate Bonus from Event CEs, and that you are choosing Claws of Chaos with any tickets you get from Boxes from those runs. To improve the 'Farming Plan' it is suggested to include a '.csv' for each ticket Material in the 'Events Farm' folder. Extra data won't confuse the analysis and will instead help you in choosing Materials from the tickets.

### Configuring Your Own Event CSV
To generate your own '.csv's, you can go to my ['FGO Efficiency' google sheet](https://docs.google.com/spreadsheets/d/1CDQYB2Oa3YT1gfD6eT3hqRR7sVshQIQMKB_BOqDzTRU/), go to the menu bar, and select 'File' -> 'Make a Copy'. Once you have your own copy, you can go to the 'Event Quest' tab, input any configurations you wants, then go to the sheet's menu bar, and select 'File' -> 'Download' -> 'Comma Separated Values (.csv)'. You can then give the '.csv' file a descriptive name (assuming you did not already rename the google sheet), and put the file into the 'Events Farm' folder. Note that if the file name starts with 'FGO Efficiency' or ends with ' - Free Quest', those parts will be ignored when the Event is named in the output 'Farming Plan.'

What configurations on the 'Event Quest' tab are relevant for 'Fate/Grand Farm'? Obviously you must select the Event you want analyzed in A1. Then for lotto Events, you can specify an Event wide Drop Rate Bonus in E1 or any quest specific values in the same column. You can also determine if you want box apple AP 'Buyback' to affect the AP values of the quests, and also input 'Event' and 'Raid Run Caps' for this specific Event.

Worth noting that this program only actually reads the (hidden in C1) 'Actual Event Name,' whether or not there's 'Buyback,' the 'Event' and 'Raid Run Caps,' and for each Event Quest its, its AP, its type, the Drop Rate Bonus (read value is hidden in F column by default but included if the Event wide value is input into E1), and the (hidden) ID and drop rate for each Material dropped. Material IDs are used so translation changes don't affect the program. None of the values for Efficiency in the document are relevant for this program, so any other settings in the 'Mat' do not affect the analysis. The 'Actual Event Name' is a constant for multiple entries of the same event, so that the program recognizes that 'Christmas 2023 w/ Claw' and 'Christmas 2023 w/ Feather' are actually the same for determining Run Caps.

On configuring the Run Caps, any readable entry to the right of the corresponding Run Cap type overwrites the value in 'FGF_config' for that specific Event. For Run Cap values read in the Event '.csv,' 'Event' and 'Lotto' Type quests both treated as 'Event' quests. The multiple entries for Run Caps are relevant for quests with numbered Types (like 'Lotto 1', 'Lotto 2', etc). If there is only one readable value given, that Run Cap will be applied separately to EACH of 'Lotto 1' and 'Lotto 2'. If two or more readable values are given, the 1st will be applied to 'Lotto 1' and the 2nd applied to 'Lotto 2.' If there are more numbered Types than entries, the Run Caps will be cycled through for later numbers. So if only two values are given, 'Lotto 3' will use the 1st Run Cap. If there are three or more values, 'Lotto 3' will use the 3rd Run Cap. 'Raids' work the same.

## Upkeep and Making Your Own CSVs
Similar to how the 'Event Quest' tab from my ['FGO Efficiency' google sheet](https://docs.google.com/spreadsheets/d/1CDQYB2Oa3YT1gfD6eT3hqRR7sVshQIQMKB_BOqDzTRU/) was used to produce the relevant Event '.csv's, the 'APD' and 'Calc' '.csv' files in the 'Data Files' Folder

What follows is a lengthy description of how the 'APD', 'Calc', and 'Event' '.csv's are read by FGF ('Fate/Grand Farm') in case you wanted to make your own from scratch rather than downloading the corresponding file from the google sheet, you could also just read the Python code.

The 'Calc' file is found by locating a file ending in 'Calc.csv'. It is read alongside 'GOALS.csv'. FGF looks at the 3rd row for the ID of each Material and the 4th row for their name. It starts on the 2nd column of those lines (it assumes that's where 'Proof of Hero' is) and reads alongside 'GOALs', matching each Material goal to its corresponding Material ID and name. Order matters. There is a blank entry between each of Bronze mats, Silver mats, Gold mats, Blue Gems, Red Gems, Gold Gems, Statues, Monuments, Blazes, and Hellfires. These are all relevant to make sure the GOALS and Free Quest data all line up. It recognizes skips by the lines starting with '!!' in 'GOALS.csv'. All the Blazes and Hellfires entries are read and pointed to the final index in the drop data.

The 'APD' file is found by locating a file ending 'APD.csv', and is used to gather 'Free Quest' drop rates. FGF recognizes where the data starts by skipping rows until it finds a cell with a string that has the word 'Bronze' in it.  It designates that column as the starting point of the Bronze Materials, and searches for a cell with a string that has the word 'Monument' in it. It assumes the start of the XP cards ('Blazes') are 8 columns past that. FGF then reads row by row, skipping all rows where the 3rd column are either blank ('') or 'AP', and finally stops when either rows run out or a cell with a string containing the value set by 'Last Area' in 'FGF_config.ini' is found. If 'Last Area' is blank, it looks for 'ZZZZZ' in vain. On each read row, the 1st column is read as the singularity name, the 2nd as the quest name, the 3rd as the AP value, and the 4th as the type of quest. It then starts reading starting from the column determined by 'Bronze', adding the Material drop rate to the corresponding index by taking the AP (in the 3rd column) and diving by the APD value. Having the same order as 'Calc' and "GOALS' matters. Once 9 columns past 'Monument' is reached, it adds every cell past that to the last index, tripling the drop rate once it is 15 entries past 'Monument' (as Hellfires are 3x as good as Blazes).

Some details of how the 'Event' files are read described in the 'Configuring Your Own Event CSV' section. FGF reads the 3rd cell in the first row as the 'Actual Event Name', then goes along the row until it finds a cell with 'Event Run Caps:'. After that cell, it uses every integer it reads to replace the 'Event' and 'Lotto Cap's in 'fgf_config.ini', until it finds a cell with 'Raid Run Caps:'. It then uses every integer it reads to replace the 'Raid Cap' in 'fgf_config.ini' until the row ends. It then skips rows until it finds one with a cell containing 'ID'. It notes every column/cell containing 'ID' in that row. It then goes row by row, skipping ones whose 2nd cell are not floats, or whose cells in the first column found using 'ID' are blank (''). If a row is read, it reads the 1st column as the quest name, the 2nd as the AP, and the 4th as the type of quest. and then goes to each column on the 'ID' list. It reads the value 2 cells to the right of each 'ID' as the drop rate for that ID, and if it is not empty it adds the drop rate to the index corresponding to the 'ID'.
