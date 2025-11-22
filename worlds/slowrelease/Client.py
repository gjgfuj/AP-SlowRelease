
from CommonClient import ClientCommandProcessor, CommonContext, logger, server_loop, gui_enabled, get_base_parser
from worlds.AutoWorld import World
from BaseClasses import Region
import asyncio
import random
tracker_loaded = True
from worlds.tracker import DeferredEntranceMode
from worlds.tracker.TrackerClient import TrackerGameContext, TrackerCommandProcessor

class SlowReleaseCommandProcessor(TrackerCommandProcessor):
    def _cmd_time(self, time_min=None, time_max=None):
        """If no arguments are provided, show the time per check. Else, set the time per check. Value in seconds. If two numbers are provided, then set a range to be randomly decided per check."""
        self.ctx.set_time(time_min, time_max)
    def _cmd_region_mode(self):
        """Toggle Region mode (i.e. make the slow release client act more like a player by handling one region of the world at a time.)"""
        self.ctx.region_mode = not self.ctx.region_mode
        logger.info(f"Set region mode to {self.ctx.region_mode}")

class SlowReleaseContext(TrackerGameContext):
    time_per_min = 10
    time_per_max = 10
    tags = ["SlowRelease", "Tracker"]
    game = ""
    has_game = False
    region_mode = True
    command_processor = SlowReleaseCommandProcessor
    autoplayer_task = None
    def autoplayer_log(self, message):
        logger.info(message)
    def set_time(self, time_min=None, time_max=None):
        if time_min:
            self.time_per_min = float(time_min)
            if time_max and float(time_min) < float(time_max):
                self.time_per_max = float(time_max)
            else:
                self.time_per_max = float(time_min)
            logger.info(f"Set time per check to {self.time_per_min}-{self.time_per_max}s")
        else:
            logger.info(f"Time per check is {self.time_per_min}-{self.time_per_max}s")
    async def autoplayer(self):
        print("Autoplayer")
        inbk = False
        while not self.tracker_core.player_id:
            await asyncio.sleep(1)
        world: World = self.tracker_core.multiworld.worlds[self.tracker_core.player_id]
        current_region : Region = self.tracker_core.multiworld.get_region(world.origin_region_name, self.tracker_core.player_id)
        while True:
            if len(self.tracker_core.locations_available) > 0:
                inbk = False
                goal_location = None
                visited_regions = []
                regions = [*map(lambda e: e.connected_region,self.tracker_core.multiworld.get_region(world.origin_region_name, self.tracker_core.player_id).get_exits())]
                if self.region_mode:
                    while not goal_location:
                        randolocs = self.tracker_core.locations_available.copy()
                        random.shuffle(randolocs)
                        for location in randolocs:
                            location = world.get_location(world.location_id_to_name[location])
                            if location.parent_region == current_region:
                                goal_location = location.address
                                self.autoplayer_log(f"Going for {self.location_names.lookup_in_game(goal_location)}")
                                break
                        if not goal_location:
                            current_region = random.choice(regions)
                            if current_region not in visited_regions:
                                regions += [*filter(lambda e: e not in regions and e not in visited_regions, map(lambda e: e.connected_region, current_region.get_exits()))]
                            visited_regions.append(current_region)
                            regions.remove(current_region)
                            self.autoplayer_log(f"Attempting to go to: {current_region.name}")
                            await asyncio.sleep(0.1)
                else:
                    goal_location = random.choice(self.tracker_core.locations_available)
                    self.autoplayer_log(f"Going for {self.location_names.lookup_in_game(goal_location)}")
                await asyncio.sleep(random.uniform(self.time_per_min, self.time_per_max))
                await self.check_locations([goal_location])
                await asyncio.sleep(0.1)
            else:
                if inbk:
                    await asyncio.sleep(1)
                else:
                    self.autoplayer_log("In BK.")
                    inbk = True
                    await asyncio.sleep(1)
    def make_gui(self):
        ui = super().make_gui()
        ui.base_title = "Slow Release Client"
        return ui
    def on_package(self, cmd, args):
        super().on_package(cmd, args)
        if cmd == "Connected":
            if "Tracker" in self.tags:
                self.tags.remove("Tracker")
                asyncio.create_task(self.send_msgs([{"cmd": "ConnectUpdate", "tags": self.tags}]))
            if self.autoplayer_task:
                self.autoplayer_task.cancel()
            self.autoplayer_task = asyncio.create_task(self.autoplayer())
            self.autoplayer_task.add_done_callback(self.autoplayer_done)
    def autoplayer_done(self, autoplayer_task):
        try:
            _ = autoplayer_task.result()
        except Exception as e:
            logger.error("Autoplayer Error", exc_info=True)
    def disconnect(self, *args):
        if self.autoplayer_task:
            self.autoplayer_task.cancel()
        if "Tracker" not in self.tags:
            self.tags.append("Tracker")
        return super().disconnect(*args)
def launch(*args):

    async def main(args):
        ctx = SlowReleaseContext(args.connect, args.password)
        ctx.auth = args.name
        ctx.server_task = asyncio.create_task(server_loop(ctx), name="server loop")
        ctx.set_time(args.time, args.time_max)

        if tracker_loaded:
            ctx.tracker_core.enforce_deferred_connections = DeferredEntranceMode.disabled
            ctx.run_generator()
        if gui_enabled:
            ctx.run_gui()
        ctx.run_cli()

        await ctx.exit_event.wait()
        await ctx.shutdown()

    import colorama

    parser = get_base_parser(description="Slow Release Archipelago Client, for text interfacing.")
    parser.add_argument('--name', default=None, help="Slot Name to connect as.")
    parser.add_argument('--time', type=float, default=10.0, help="Minimum time per check in seconds. If maximum is not specified, defaults to this.")
    parser.add_argument('--time_max', type=float, default=None, help="Maximum time per check.")
    parser.add_argument("url", nargs="?", help="Archipelago connection url")
    args = parser.parse_args(args)

    # handle if text client is launched using the "archipelago://name:pass@host:port" url from webhost
    if args.url:
        import urllib
        url = urllib.parse.urlparse(args.url)
        if url.scheme == "archipelago":
            args.connect = url.netloc
            if url.username:
                args.name = urllib.parse.unquote(url.username)
            if url.password:
                args.password = urllib.parse.unquote(url.password)
        else:
            parser.error(f"bad url, found {args.url}, expected url in form of archipelago://archipelago.gg:38281")

    # use colorama to display colored text highlighting on windows
    colorama.init()

    asyncio.run(main(args))
    colorama.deinit()

