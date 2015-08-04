#!/usr/bin/env python

import enum
import asyncio
import random

import transitions


class Role(enum.Enum):
    villager = (True, False)
    wolf = (False, False)
    seer = (True, True)

    def __init__(self, good, special):
        self.good = good
        self.special = special

    def __repr__(self):
        return "Role(good={0.good}, special={0.special})  # {0.name}".format(self)


class Remote:

    @asyncio.coroutine
    def get(self):
        raise NotImplementedError

    @asyncio.coroutine
    def post(self, payload):
        raise NotImplementedError


class RemoteStub:

    @asyncio.coroutine
    def get(self):
        vote = random.choice(self.can_vote)
        return vote

    @asyncio.coroutine
    def post(self, payload):
        self.can_vote = payload

    
class Player:

    def __init__(self, uuid, role, remote):
        # remote player can get and post
        self.uuid = uuid
        self.role = role
        self.remote = remote
        self.alive = True

    @asyncio.coroutine
    def vote(self, can_vote):
        yield from self.remote.post(can_vote)
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
            initial="initializing",
        )
        self.machine.add_transition(
            trigger="start",
            source="initializing",
            dest="day"
        )
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
        self.loop.call_soon(self.start)
        self.loop.call_soon(self.day)
        self.loop.create_task(self.day_vote())
        self.loop.run_forever()
        self.loop.close()

    @asyncio.coroutine
    def day_vote(self):
        votes = yield from asyncio.gather(
            *[player.vote(
                [other_player.uuid
                 for other_player in self.alive_players
                 if other_player is not player])
                for player in self.alive_players
            ]
        )
        voted = max(votes, key=votes.count)
        self.players[voted].alive = False
        if self.end(): return
        self.night()
        self.loop.create_task(self.night_vote())

    @asyncio.coroutine
    def night_vote(self):
        votes = yield from asyncio.gather(
            *[player.vote(
                [other_player.uuid
                 for other_player in self.good_players
                 if other_player is not player])
                for player in self.alive_players
            ]
        )
        voted = max(votes, key=votes.count)
        self.players[voted].alive = False
        if self.end(): return
        self.day()
        self.loop.create_task(self.day_vote())

    def is_game_over(self):
        game_over = (
            len(self.alive_players) <= 1
            or len(self.good_players) <= len(self.evil_players)
            or len(self.evil_players) < 1
        )
        return game_over

    def on_enter_end(self):
        self.loop.stop()

    @property
    def alive_players(self):
        return [player
                for player in self.players
                if player.alive]

    @property
    def good_players(self):
        return [player
                for player in self.players
                if player.alive and player.role.good]

    @property
    def evil_players(self):
        return [player
                for player in self.players
                if player.alive and not player.role.good]
