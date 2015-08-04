import asyncio
import pytest
import pytest_asyncio.plugin

import lupusintabulabot.engine as lupus


@pytest.mark.asyncio
def test_player_vote():
    player = lupus.Player(
        1,
        lupus.Role.villager,
        lupus.RemoteStub())
    voted = yield from player.vote([2])
    assert voted == 2


def test_game_machine_init(event_loop):
    players = [
        lupus.Player(
            i, role, lupus.RemoteStub())
        for i, role in enumerate(lupus.Role)]
    game = lupus.Game(players, event_loop)
    assert game.state == "initializing"
    game.run()
    assert game.state == "end"
    assert len(game.players) == 3
