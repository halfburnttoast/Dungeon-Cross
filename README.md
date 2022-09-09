# Dungeon Cross
A Python + Pygame stand-alone, reimplementation of Zachtronic's Dungeons and Diagrams. I love Picross and Dungeons and Diagrams is an amazing twist on classic nonograms. I wanted to have a stand-alone version of this game to have open in the background while I do other things. Hence this project was born.

If you like this game, please checkout the other amazing puzzle games by Zachtronics. 

------------
**NOTE:** This program is still in alpha development stage, expect unusual behavior. User interface, gameplay mechanics, graphics, sound effects, music, and keybindings are all subject to change at any time without warning.

All the sprites, music, and sound effects listed in credits are, to the best of my understanding, licensed as Creative Commons.

------------

### Controls:
    LMB - Place/remove walls
    RMB - Place/remove marks
    SpaceBar - Next puzzle
    R - Reset puzzle
    M - Mute music


------------

### Running
To either run or compile Dungeon Cross, you'll need to have Python 3.7 (or newer) installed along with Pygame. If you've installed Python with the 'Add to path' option selected, you can run the following in a command prompt to install pygame:

`$ pip3 install pygame`

To run the program, you can then run this command from the main game directory:
`$ python3 dungeon_cross.py`

Alternatively, you can download the pre-compiled binaries listed under releases. 

### Building
Included with this repository is a Makefile for Linux and MacOS and a Batch file for Windows. To run either of these, you'll need to have Python 3.7 or newer installed IWITH the 'Add to path' option selected. From there, you can build the game to an binary file by doing the following:

###### Windows
Double click on `make.bat`. A command prompt window will appear. It will install the required libraries and build to the `dist/` folder.

###### MacOS or Linux
You will need to have the make utility installed. Open a command prompt in the main game folder and execute the following command:
`$ make`
It will install the required libraries and build to the `dist/` folder.



------------


### Credits:
* HalfBurntToast - All programming in this project. 
* Zachtronics                    - Original game design concepts.
* Shadowcluster                  - Raw puzzle frameworks

##### Sprites:
* DCSS                           - All sprites except for the chest sprite.
* PIPOYA                         - Chest sprite.
* Big Rigs: Over the Road Racing - Legendary win screen that I jpeg'd the heck out of.

##### Music:
* Alexander Nakarada | https://www.serpentsoundstudios.com

##### Sound Effects:
* Kenney | https://www.kenney.nl

##### Third-party libraries
Pygame | https://github.com/pygame
pygame_menu | https://github.com/ppizarror/pygame-menu

![Screenshot at 2022-09-07 11-48-30](https://user-images.githubusercontent.com/10293645/188939021-4a26c0cc-9a72-4604-8aa0-490a99ee1616.png)
