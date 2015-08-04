import asyncio
import pytest
import pytest_asyncio.plugin

import lupusintabulabot.engine as lupus


@pytest.mark.asyncio
def test_player_vote(unused_tcp_port, event_loop):
    def vote(reader, writer):
        player = lupus.Player(
            1, lupus.Role.villager, reader, writer)
        writer.write(2)
        voted = yield from player.vote()
        return voted

    server = asyncio.start_server(
        vote,
        'localhost',
        port=unused_tcp_port,
        loop=event_loop
    )
    assert voted == 2
