# Setup Guide for Slow Release Client

## Required steps

- Download both [Universal Tracker](https://github.com/FarisTheAncient/Archipelago/releases/latest) and [Slow Release Client](https://github.com/gjgfuj/AP-SlowRelease/releases) apworlds.
- Double click the apworlds to install them, or move them manually in your `Archipelago/custom_worlds` folder.

### IMPORTANT

To slow release a particular slot, you need to make sure the game and the settings used for this slot work with Universal Tracker (UT), because Slow Release uses UT to know what is in logic and thus what to release. 

Some games need to have the slot's yaml in your `Archipelago/Players` folder, some don't, some games' entrance rando and random settings break UT, some don't, and some games don't even work at all with UT.

Learn to use UT, learn what quirks your game might have with it, and use the corresponding UT setup for the game you want to slow release. More info on UT can be found here: https://discord.com/channels/731205301247803413/1367270230635839539

## Using the Slow Release Client

Open Archipelago Launcher, and open `Slow Release Client`. Two commands are relevant here, `/time` and `/region_mode`.

- The `/time` command takes a value, in seconds. This value will be the delay between released checks.
- The `/region_mode` command makes the slow release client act more like a player by handling one region of the world at a time. It's a toggle, so the value changes everytime you run the command.

Those commands and what they do are also listed at the bottom of the command list displayed every time you launch the Slow Release Client.

From there you just need to connect to the slot, and it will start slow releasing.