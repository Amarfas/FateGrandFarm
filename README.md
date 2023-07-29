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

## Configuring Your Own Event CSV
To generate your own '.csv' files for specific Events, use my ['FGO Efficiency'](https://docs.google.com/spreadsheets/d/1CDQYB2Oa3YT1gfD6eT3hqRR7sVshQIQMKB_BOqDzTRU/) google sheet. To obtain your '.csv' file:
 1. Go the sheet's menu bar, select 'File' -> 'Make a Copy'. You can rename it whatever.
 2. Open your own copy of the sheet.
 3. Go to the 'Event Quest' tab.
 4. Input any configurations you want.
 5. Go to the sheet's menu bar, selct 'File' -> 'Download' -> 'Comma Separated Values (.csv)'.
 6. Go to your Downloads folder. I suggest giving the file a descriptive name, as that determines what the Event is called in the 'Farming Plan'.
 7. Place it into the 'Events Farm' folder.

Note that if the file name starts with 'FGO Efficiency' or ends with ' - Free Quest', those parts will be ignored for the Event Name.

Relevant Configurations:
 * Selecting the desired Event in cell A1.
 * For Lotto Events, specifying an Event-wide Drop Rate Bonus in cell E1. If you leave this blank, Materials from Boxes will not be included in the analysis.
 * Specifying a quest-specific Drop Rate Bonus in the corresponding row of column E.
 * Determine if you want Box Apple AP 'Buyback' to affect the AP values of the quests.
 * 'Event' and 'Raid Run Caps' for this specific Event.

Worth noting that in addition to the above, Fate/Grand Farm only actually reads:
 * 'Actual Event Name' in cell C1 (hidden by default), used so that the program recognizes 'Christmas 2023 w/ Claw' and 'Christmas 2023 w/ Feather' are the same when determining Run Caps.
 * For each Event quest, its name in column A.
 * Its AP in column B.
 * Its Type in column D.
 * Its Drop Rate Bonus in column F (hidden by default, determined by above configurations).
 * Each column with a Material ID (used to prevent translation changes from affecting the program).
 * Each column with a Material Drop Rate.

Efficiency values in the sheet are not relevant for this program, so any settings in the 'Mat' tab do not affect this analysis.

Details on configuring the Run Caps:
 * Any integer to the right of the a 'Run Cap' overwrites the corresponding value in 'fgf_config.ini'.
 * For 'Lotto' Type quests, values to the right of 'Event Run Caps:' overwrite 'Lotto Cap' in 'fgf_config.ini'.
 * Multiple entries for Run Caps are relevant for quests with numbered Types (like 'Lotto 1', 'Lotto 2', etc).
 * If only 1 value is entered, that Run Cap will be applied separately to EACH of 'Lotto 1' and 'Lotto 2'.
 * If 2 or more values are entered, the 1st will be applied to 'Lotto 1' and the 2nd applied to 'Lotto 2.'
 * If there are more numbered Types than entries, the Run Caps will be cycled through for later numbers.

As an example, if only 2 values are given, 'Lotto 3' will use the 1st Run Cap. If there are 3 or more values, 'Lotto 3' will use the 3rd Run Cap. 'Raids' work the same.

## Upkeep
Similar to how the 'Event Quest' tab from the ['FGO Efficiency'](https://docs.google.com/spreadsheets/d/1CDQYB2Oa3YT1gfD6eT3hqRR7sVshQIQMKB_BOqDzTRU/) google sheet was used to produce the relevant Event '.csv's, the 'APD' and 'Calc' tabs were used to produce the relevant '.csv' files in the 'Data Files' Folder. If you want to update Fate/Grand Farm with new information, you need merely to download the relevant files and place them in the proper folders. For a more extensive explanation, read the next section.

## Making Your Own Readable CSVs

To create your own readable '.csv' files for FGF ('Fate/Grand Farm') follow these guidelines for each type of file. You can also read the Python code itself.

## 'Calc' File
 1. Create a CSV file with a name ending in '*Calc.csv' in the 'Data Files' folder. This file will be read alongside 'GOALS.csv'.
 2. Place the Material IDs in a row whose first column starts with 'ID'. Start entering the actual Material ID values on the 2nd column (assumed where 'Proof of Hero' is).
 3. Make sure to use the same order as 'GOALS.csv'.
 4. Similarly, put the Material names on the next row, starting from the 2nd column.
 5. Insert a blank entry/column between group of Materials in the following categories:
     * Bronze mats
     * Silver mats
     * Gold mats
     * Blue Gems
     * Red Gems
     * Gold Gems
     * Statues
     * Monuments
     * Blazes
     * Hellfires

Worth noting that FGF recognizes the skips by the lines starting with '!!' in 'GOALS.csv'.

## 'APD' File
 1. Create a CSV file with a name ending in '*APD.csv' in the 'Data Files' folder. This will determine the 'Free Quest' drop rates.
 2. On the 1st row, input a string with the word 'Bronze' on the column where you want to start reading drop data.
 3. Also on the 1st row, input a string with the word 'Monument' on the column that starts where Monuments are input.
 4. Input Free Quest data on each subsequent row. FGF will skip rows whose 3rd column are not integers.
 5. The 1st column is where the 'Singularity' or 'Lost Belt' Name goes.
 6. The 2nd column is where the Quest Name goes.
 7. The 3rd column is where the AP Cost goes.
 8. The 4th column is where the Type goes, if you want 'Training Grounds Half AP' and 'Bleach Cap' to work. FGF looks for the strings 'Daily' and 'Bleach' to apply these conditions, respectively.
 9. Starting from the same column where you input 'Bronze', add Drop Rate data. Make sure the Materials follow the same order used in '*Calc.csv' and 'GOALS.csv'.

Worth noting that when building the Drop Matrix, FGF will stop adding new columns 9 columns after the row with 'Monument' in it. It assumes 'Blazes' start 8 columns past that, and thus only makes a single column for XP as the final column. It will add Drop data from the next 15 columns to the final column, tripling all Drop Rates 6 columns after that final column (Hellfires should start after that).

The Singularity/Lost Belt name should follow the conventions used in 'fgf_config' if you want 'Last Area' to work. Worth noting that FGF looks for whether or not string fragments are found in the Singularity to decide if it should stop reading data (so 'Last Area' = 'Pluribus' will cause it to stop reading at 'E Pluribus Unum').

## 'Event' Files

Some details of how the 'Event' files are read is described in the 'Configuring Your Own Event CSV' section. Specifically, in the first row, it looks at the 3rd column for the 'Actual

However, after the first row, FGF does not look for specific column numbers. It instead looks for a row with columns containing a value of 'ID', and uses strings in that row to determine where it should find the data. Worth noting that the location is set by the first column it finds matching the following strings, except for 'ID' and 'Drop%'. The strings it looks for to find the corresponding data are:
 * 'Location' for the Quest Name
 * 'AP' for the AP Costs
 * 'Type' for the Quest Type.
 * 'Lotto' for the Drop Rate Bonus.
 * 'R/Box' for the average numbers of runs to get a Box.
 * 'ID' for the Material IDs. These should match the IDs used in 'Calc'.
 * 'Drop%' for the Drop Rate for the above Materials. Note that FGF assumes the 1st 'ID' it finds corresponds to the 1st 'Drop%' it finds, the 2nd 'ID' to the 2nd 'Drop%', etc.

FGF reads the 3rd cell in the first row as the 'Actual Event Name', then goes along the row until it finds a cell with 'Event Run Caps:'. After that cell, it uses every integer it reads to replace the 'Event' and 'Lotto Cap's in 'fgf_config.ini', until it finds a cell with 'Raid Run Caps:'. It then uses every integer it reads to replace the 'Raid Cap' in 'fgf_config.ini' until the row ends. It then skips rows until it finds one with a cell containing 'ID'. It notes every column/cell containing 'ID' in that row. It then goes row by row, skipping ones whose 2nd cell are not floats, or whose cells in the first column found using 'ID' are blank (''). If a row is read, it reads the 1st column as the quest name, the 2nd as the AP, and the 4th as the type of quest. and then goes to each column on the 'ID' list. It reads the value 2 cells to the right of each 'ID' as the drop rate for that ID, and if it is not empty it adds the drop rate to the index corresponding to the 'ID'.
