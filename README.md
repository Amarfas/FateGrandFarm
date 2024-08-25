# Fate/Grand Farm

<p align="center">
  <img width="200" src="https://i.imgur.com/7efNMgy.png?1">
</p>

Fate/Grand Farm is a Python program designed to aid players in the mobile game 'Fate/Grand Order' by utilizing linear programming to create optimal farming plans for Materials.

## Introduction

With the variety of Materials in the game, some of which don't help any of the Servants you rolled, it can be difficult to optimally plan your farming route. Even if you plan the best route for farming Free Quests, Events can offer much better drop rates. With readily available open-sourced data for Events, and the Global version lagging 2 years behind the Japanese version, surely there must be a better way to reach your farming goals.

This is where Fate/Grand Farm comes to your rescue! Input your farming goals, select which Events you want to analyze, possibly change some configurations if you're into that, press that exe button, and have the next 2 years of your grinding life dictated to you by a machine!

The executable only works for Windows. If you use another Operating System (or run into other problems), look into the 'Python Environment Set Up' section below to find out what you need for the Python program.

*Note: As the linear programming algorithms can only compute averages, the actual number of runs required to reach your goal may be highly variable for a low number of Materials required.*

## How to Use
  1. Open 'GOALS.csv', and input the number of Materials you desire next to the corresponding Material. XP cards are all condensed into one entry. Save.
  2. Move/copy all Event '.csv's in the 'Events List' folder to the 'Events Farm' folder that you want to be included in the analysis.
  3. Open 'fgf_config.ini' and change any settings you want. Save.
  4. Run 'Fate_Grand_Farm.exe'

For more details on configuring the analysis or managing/upkeeping Event data, scroll down to the 'Set Up' section. This is mostly helpful for creating Event-specific Run Caps.

## How to Read the Output
After running the program, you will find 3 output files in the main directory ('FateGrandFarm'), all of which will replace those files from previous runs. These are 'Farming Plan.txt', 'Farming Plan Drops.txt', and 'Config Notes.txt'. Extra copies will be placed in the 'Former Plans' folder, using the 'Plan Name' configured in 'fgf_config.ini' if one was chosen.

### Farming Plan.txt
'Farming Plan' presents the optimized farming plan generated by the program. The 1st line should say that the results are 'optimal,' and the 2nd line will provide the Total AP for the plan. For each line in the following analysis;

 * 1st Entry: Name of the Event/Singularity/Lost Belt. The Event name is determined by the name of the corresponding '.csv' file.
 * 2nd Entry: Quest/node name.
 * 3rd Entry: Suggested number of times it should be run. Expected number of gained Boxes is also included for Lotto runs.

Run count suggestions may randomly go a small amount over the specified Run Cap. This seems to be a consequence of adding together run count floats before they are converted to integers at the end.

If the 'Monthly Ticket Per Day' configuration in 'fgf_config.ini' was greater than 0, 'Farming Plan.txt' will then include suggestions for what Materials to choose with your Monthly Exchange Ticket each month. If a month is not included, it either exists outside the chosen date range, or the choice does not matter.

### Farming Plan Drops.txt
'Farming Plan Drops' is very similar to 'Farming Plan'. However, it also lists the expected number of each Material dropped for those runs. Note that if the 'Remove Zeros' configuration is on, it will not include undesired Materials (those with no goal).

### Config Notes.txt
'Config Notes' contains all the information necessary to properly understand the context for the corresponding 'Farming Plans'. This includes all the Errors that came up, Configurations, the Monthly Exchange Ticket date range, the Events included, Lotto Drop Rate boosts, and the applied Run Caps.

## Python Environment Set Up
Fate/Grand Farm was programmed in Python 3.9, and the necessary libraries are: [NumPy](https://numpy.org/), [SciPy](https://scipy.org/), and [CVXPY](https://www.cvxpy.org/).

It is recommended to download and install [Anaconda.](https://www.anaconda.com/) If you encounter any issues finding CVXPY, you may need to add the 'conda-forge' channel.

After setting up the required Python environment and libraries, navigate to the 'Code' folder and execute 'Fate_Grand_Farm.py' by running the following command in your terminal or command prompt:
```
python Fate_Grand_Farm.py
```

# Set Up
## 'fgf_config.ini' Extra Notes

For any y/n (yes/no) question in the configurations, it will also read the following as yes or no (not case sensitive):
 * 1 = yes , 0 = no
 * true = yes , false = no
 * t = yes , f = no
 * yes = yes , no = no
 * y = yes , n = no
 * on = yes , off = no

For another note on 'remove_zeros', sometimes there are non-trivial different solutions which fulfill the same goals for the same AP Cost. Consequently, sometimes an entirely different run path will be spit out when 'remove_zeros' is toggled, as the technically different matrix causes the solver to reach its solution on a different path.

For the Monthly Exchange Ticket analysis, the 'Monthly Ticket Per Day' configuration caps at 4. The 'Monthly Ticket End Date' can either be a specific date or a time lapse relative to the starting date. If the starting date was 10/23/2024 and '2 months' was entered, the end date will be 12/23/2024. The program will accept relative time frames in 'days', 'months', or 'years'. Does not have to be plural ('day' will also be accepted).

## 'Events List' Folder
Contains the drop rate data for various Events in '.csv' format. Lotto Events have their own folders to help organize the data. 

Lotto Events have their own additional naming convention:
 * '-D#' describes the Drop Rate Bonus used in the analysis, as the Materials obtained from Boxes are added to each Quest's drop rate table.
 * '-D-' means that boxes are not included in the analysis.
 * Any truncated Material name after '-D#-' represents the Material to be obtained using the ticket from the Lotto Box.

For example, 'Christmas 2023 -D12-Claw' signifies the drop rate table for all 'Christmas 2023' Quests, assuming that you have a +12 Drop Rate Bonus from Event CEs, and that you are choosing Claws of Chaos with any tickets you get from Boxes with those runs.

To improve the 'Farming Plan', it is suggested to add a '.csv' for each Material that can be gotten from Lotto tickets to the 'Events Farm' folder. Extra data won't confuse the analysis, and will instead help you in choosing Materials from those tickets.

As a further note, all Lotto Event '.csv's that come pre-installed with Fate/Grand Farm have 'Apple AP Buyback' turned on. This means that Apples gained from Boxes are assumed to go back into farming the Quest in question. This effectively lowers their AP Cost for each Quest. Even if this is not how you actually farm the Event, it does represent how efficient the drop rate is per AP spent.

## Configuring Your Own Event CSV
To generate your own '.csv' files for specific Events, use my ['FGO Efficiency'](https://docs.google.com/spreadsheets/d/1CDQYB2Oa3YT1gfD6eT3hqRR7sVshQIQMKB_BOqDzTRU/) google sheet. To obtain your '.csv' file:
 1. Go the sheet's menu bar, select 'File' -> 'Make a Copy'. You can rename it whatever.
 2. Open your own copy of the sheet.
 3. Go to the 'Event Quest' tab.
 4. Input any configurations you want.
 5. Go to the sheet's menu bar, select 'File' -> 'Download' -> 'Comma Separated Values (.csv)'.
 6. Go to your Downloads folder. I suggest giving the file a descriptive name, as that determines what the Event is called in the 'Farming Plan'.
 7. Place it in the 'Events Farm' folder.

Note that if the file name starts with 'FGO Efficiency' or ends with ' - Event Quest', those parts will be ignored for the Event Name.

Relevant Configurations:
 * Selecting the desired Event in cell A1.
 * For Lotto Events, specifying an Event-wide Drop Rate Bonus in cell G1. If you leave this blank, Materials from Boxes will not be included in the analysis.
 * Specifying a Quest-specific Drop Rate Bonus in the corresponding row of column G.
 * Determine if you want Box Apple AP 'Buyback' to affect the AP Costs of the Quests.
 * 'Event' and 'Raid Run Caps' for that specific Event.

Worth noting that in addition to the above, Fate/Grand Farm only actually reads:
 * 'Actual Event Name' in cell C1 (hidden by default), used so that the program recognizes 'Christmas 2023 w/ Claw' and 'Christmas 2023 w/ Feather' as the same Event when determining Run Caps.
 * Whether 'Apple AP Buyback' is active or not from cell M1.
 * The cells after 'Event Run Caps' and 'Raid Run Caps' in the 1st row. 
 * For each Event Quest in the following rows:
   - Its name in column A.
   - Its AP Cost in column B.
   - Its Type in column E.
   - Its Drop Rate Bonus in column F (hidden by default, determined by above configurations).
   - Each column with a Material ID (hidden by default, used to prevent translation changes from affecting the program).
   - Each column with a Material Drop Rate.

Efficiency values from the sheet are not relevant for this program, so any settings from the 'Mat'/'Inputs tab do not affect this analysis.

Details on configuring the Run Caps:
 * Any integer to the right of the a 'Run Cap' overwrites the corresponding value in 'fgf_config.ini'.
 * For 'Lotto' Type Quests, values to the right of 'Event Run Caps:' overwrite 'Lotto Cap' in 'fgf_config.ini'.
 * Multiple entries for Run Caps are relevant for Quests with numbered Types (like 'Lotto 1', 'Lotto 2', etc).
 * If only 1 value is entered, that Run Cap will be applied separately to EACH of 'Lotto 1' and 'Lotto 2'.
 * If 2 or more values are entered, the 1st will be applied to 'Lotto 1' and the 2nd applied to 'Lotto 2.'
 * If there are more numbered Types than entries, the Run Caps will be cycled through for later numbers.

As an example, if only 2 values are given, 'Lotto 3' will use the 1st Run Cap. If there are 3 or more values, 'Lotto 3' will use the 3rd Run Cap. 'Raids' work the same.

## Upkeep
Similar to how the 'Event Quest' tab from the ['FGO Efficiency'](https://docs.google.com/spreadsheets/d/1CDQYB2Oa3YT1gfD6eT3hqRR7sVshQIQMKB_BOqDzTRU/) google sheet was used to produce the relevant Event '.csv's, the 'APD', 'Calc', and 'Monthly Ticket' tabs were used to produce the relevant '.csv' files in the 'Data Files' Folder. If you want to update Fate/Grand Farm with new information, for 'APD' and 'Calc" you merely need to download the relevant files and place them in the 'Datw Files' folder. For a more extensive explanation, read section 'Making Your Own Readable CSVs'.

Adding new 'Monthly Ticket' '.csv's takes slightly more work. Before downloading the data from the 'Monthly Ticket' tab as a '.csv' file, you have to input the corresponding month in cell B1 and year in cell D1, both as integers. Then the Material IDs corresponding to the choices available must be input into column C. It is recommended that you instead input each Material's name into the next cell in column D, causing the sheet to automatically find and input the Material's ID.

# Troubleshooting
 * Before anything else, check the 'Config Notes' file and see if it notes anything wrong at the top.

If nothing is stated explicitly, and it doesn't list all (or any) of the Events meant to be included in the analysis, the program probably halted before reaching that point. That means it either had a hard time reading the '.csv's in the 'Data Files' folder, the 'GOALS', or an Event '.csv'.

 * First, remove all files from the 'Events Farm' folder, and see if 'Fate/Grand Farm' outputs a 'Farming Plan'.
 * If it does, then one of the Event '.csv's is at fault. It reads through the files alphabetically, so try removing either the last recorded Event file or the one just after.
 * If the problem was with an Event file, you can try creating a new file from the ['FGO Efficiency'](https://docs.google.com/spreadsheets/d/1CDQYB2Oa3YT1gfD6eT3hqRR7sVshQIQMKB_BOqDzTRU/) google sheet.
 * If the problem is not in the 'Events Farm' folder, it might be in 'GOALS.csv'. Make sure your formatting follows what has been described, as demonstrated in the 'Sample_GOALS.csv' file.

If the above does not fix the issue, it is suggested you return to the Fate/Grand Farm github page and see if there are any newer versions. The newest version should have up to date files in the 'Data Files' folder.

 * If you're running the program through the 'Fate_Grand_Farm.py' file and want to debug it yourself, make sure the 'Debug on Fail' option in 'fgf_config.ini' is set to 'n'.

# Making Your Own Readable CSVs

To create your own readable '.csv' files for FGF ('Fate/Grand Farm') follow these guidelines for each type of file. You can also read the Python code itself.

## 'Calc' File
 1. Create a CSV file with a name ending in 'Calc.csv' in the 'Data Files' folder. This file will be read alongside 'GOALS.csv'.
 2. Input the Material IDs in a row whose first column starts with 'ID'. Start entering the actual Material ID values from the 2nd column (assumed to be where 'Proof of Hero' is).
 3. Make sure to use the same order as 'GOALS.csv'.
 4. Similarly, put the Material names on the next row, starting from the 2nd column.
 5. Insert a blank entry/column between groups of Materials in the following categories:
     * Bronze Mats
     * Silver Mats
     * Gold Mats
     * Blue Gems
     * Red Gems
     * Gold Gems
     * Statues
     * Monuments
     * Blazes
     * Hellfires

Note that FGF recognizes the skips by the lines starting with '!!' in 'GOALS.csv'.

## 'APD' File
 1. Create a CSV file with a name ending in 'APD.csv' in the 'Data Files' folder. This will determine the 'Free Quest' drop rates.
 2. On the 1st row, input a string with the word 'Bronze' on the column where you want to start reading drop data.
 3. Also on the 1st row, input a string with the word 'Monument' on the column where Monument drop data starts being inputted.
 4. Input Free Quest data on each subsequent row. FGF will skip rows whose 3rd columns are not integers.
 5. The 1st column is where the 'Singularity' or 'Lost Belt' Name goes.
 6. The 2nd column is where the Quest Name goes.
 7. The 3rd column is where the AP Cost goes.
 8. The 4th column is where the Type goes, if you want 'Training Grounds Half AP' and 'Bleach Cap' to work. FGF looks for the strings 'Daily' and 'Bleach' to apply these conditions, respectively.
 9. Starting from the same column where you input 'Bronze', add Drop Rate data. Make sure the Materials follow the same order used in the '*Calc.csv' and 'GOALS.csv'.

Worth noting that when building the Drop Matrix, FGF will stop adding new types of Materials 9 columns after the column with 'Monument' in the 1st row. It assumes 'Blazes' start 8 columns past that, and thus only makes a single final column for XP. It will add Drop data from the next 15 columns to that final column, tripling all Drop Rates 6 columns after that final column (Hellfires should start after that).

The Singularity/Lost Belt name should follow the conventions used in 'fgf_config' if you want 'Last Area' to work. Note that FGF looks for whether or not string fragments are found in the Singularity to decide if it should stop reading data (so 'Last Area' = 'Pluribus' will cause it to stop reading at 'E Pluribus Unum'). It looks like, somehow, 'Id' does not cause a problem here.

## 'Event' Files

Some details on how the 'Event' files are read is described in the 'Configuring Your Own Event CSV' section. 

Specifically, in the 1st row:
 * FGF looks at the 3rd column for the 'Actual Event Name'.
 * FGF looks for the string 'Buyback?:' and considers the Lotto Event to have it if the next column is not empty.
 * FGF looks for the string 'Event Run Caps:' and adds every integer in subsequent columns to the 'Event Run Cap' matrix until it finds...
 * FGF looks for the string 'Raid Run Caps:' and adds every integer in subsequent columns to the 'Raid Run Cap' matrix.

However, after the 1st row, FGF does not look for specific column numbers. It instead looks for a row with columns containing a value of 'ID', and uses strings in that row to determine where it should find the data. Note that the column number is set by the first column it finds matching the following strings, except for 'ID' and 'Drop%'; FGF records the numbers for all columns with 'ID' and 'Drop%'. The strings it looks for in order to find the corresponding data are:
 * 'Location' for the Quest Name.
 * 'AP' for the AP Costs.
 * 'Type' for the Quest Type.
 * 'Lotto' for the Drop Rate Bonus.
 * 'R/Box' for the average numbers of runs to get a Box.
 * 'ID' for the Material IDs. These should match the IDs used in 'Calc'.
 * 'Drop%' for the Drop Rate for the above Materials. Note that FGF assumes the 1st 'ID' it finds corresponds to the 1st 'Drop%' it finds, the 2nd 'ID' to the 2nd 'Drop%', etc.

FGF skips all lines whose AP Cost is not a float. It also skips all lines whose first 'Drop%' entry is empty.

There are a few special Material IDs that FGF interprets as multiple different Materials at once. These are:
 * '-1' = Blue Gems
 * '-2' = Red Gems
 * '-3' = Gold Gems
 * '-4' = Statues
 * '-5' = Monuments
 * '-6' = XP Cards

## 'Monthly Ticket' Files
 1. Create a CSV file with any name whatsoever in the 'Monthly Exchange Ticket Choices' folder, found in the 'Data Files' folder.
 2. On the 1st row, input the month in the 2nd column and the year in the 4th column, as integers.
 3. Below the 1st row, input the value/string 'ID' into any cell.
 4. Input the Material IDs that correspond to the Monthly Exchange Ticket choices on subsequent rows in the same column as 'ID'. These should match the IDs used in 'Calc'.

# Acknowledgements

 * [pyinstaller](https://github.com/pyinstaller/pyinstaller) for making it easy to create an executable.

 * [CVXPY](https://www.cvxpy.org/) for making a library that can crunch these numbers, and my friend for pointing them out to me.

Other credit goes to the various communities that have worked hard to compile data and analyze this game. Specifically:

 * [Atlas Academy](https://atlasacademy.io/) for more recent data.

 * JP Data is sourced from the [following community collaboration.](https://docs.google.com/spreadsheets/d/1TrfSDteVZnjUPz68rKzuZWZdZZBLqw03FlvEToOvqH0/)

 * [Domus Aurea](https://sites.google.com/view/fgo-domus-aurea) was usually the JP source I pulled data from/cross-referenced with.

 * [Guruguru FGO](https://sites.google.com/site/gurugurufgo/) was another JP source I pulled data from/cross-referenced with.
