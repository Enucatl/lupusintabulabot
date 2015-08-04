#!/usr/bin/env python

import enum
import asyncio

import transitions


class Role(enum.Enum):
    villager = (True, False)
    wolf = (False, False)
    seer = (True, True)

    def __init__(self, good, special):
        self.good = good
        self.special = special

    def __repr__(self):
        return "Role(good={0.good}, special={0.special})".format(self)


class Remote:
    def get(self):
        raise NotImplementedError

    def post(self, payload):
        raise NotImplementedError


class RemoteStub:

    @asyncio.coroutine
    def get(self):
        return 2

    
class Player:

    def __init__(self, uuid, role, remote):
        # remote player can get and post
        self.uuid = uuid
        self.role = role
        self.remote = remote
        self.alive = True

    @asyncio.coroutine
    def vote(self):
        voted = yield from self.remote.get()
        return voted

    def __repr__(self):
        return "Player(uuid={}, role={}, remote={})".format(
            self.uuid,
            repr(self.role),
            repr(self.remote)
        )


class Game:

    def __init__(self, players, loop):
        self.players = players
        self.loop = loop
        self.machine = transitions.Machine(
            model=self,
            states=["initializing", "day", "night", "end"],
            initial="initializing"
        )
        self.machine.add_transition(
            trigger="start",
            source="initializing",
            dest="day")
        self.machine.add_transition(
            trigger="day",
            source="day",
            dest="night"
        )
        self.machine.add_transition(
            trigger="night",
            source="night",
            dest="day"
        )
        self.machine.add_transition(
            trigger="end",
            source=["day", "night"],
            dest="end",
            conditions="is_game_over"
        )

    def run(self):
        self.start()
        self.loop.run_forever()

    @asyncio.coroutine
    def on_enter_day(self):
        print("VOTING")
        #votes = yield from asyncio.gather(player.vote() for player in self.alive_players())
        #print(votes)
        #self.end()
        #self.night()

    def on_enter_night(self):
        print("VOTING")
        votes = yield from asyncio.gather(player.vote() for player in self.alive_players())
        print(votes)
        self.end()
        self.day()

    def is_game_over(self):
        return len(list(self.alive_players()))

    def alive_players(self):
        return (player
                for player in self.players
                if player.alive)

    def on_enter_end(self):
        self.loop.stop()
        self.loop.close()

