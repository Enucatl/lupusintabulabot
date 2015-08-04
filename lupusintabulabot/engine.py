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


class Player:

    def __init__(self, uuid, role, reader, writer):
        # reader and writer are asyncio.StreamReader and
        # asyncio.StreamWriter
        self.uuid = uuid
        self.role = role
        self.reader = reader
        self.writer = writer
        self.alive = True

    @asyncio.coroutine
    def vote(self):
        voted = yield from self.reader.read().decode()
        return voted

    def __repr__(self):
        return "Player(uuid={}, role={}, reader={}, writer={}".format(
            self.uuid,
            repr(self.role),
            repr(self.reader),
            repr(self.writer)
        )


class Game:

    def __init__(self):
        self.machine = transitions.Machine(
            model=self,
            states=["initializing", "day", "night", "end"],
            initial="initializing"
        )
        self.machine.add_transition(
            trigger="set_players",
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

    def set_players(self, players):
        self.players = players
        self.day()

    def day(self):
        votes = asyncio.gather(
            [player.vote() for player in self.alive_players()]
        )
        print(votes)
        self.end()
        self.night()

    def night(self):
        votes = asyncio.gather(
            [player.vote()
             for player in self.alive_players()]
        )
        print(votes)
        self.end()
        self.day()

    def is_game_over(self):
        return len(self.alive_players())

    def alive_players(self):
        return (player
                for player in self.players
                if player.alive)
