"""Add adjacent/non-adjacent coalition pair layouts to the v3 channel-preference runner."""
from pathlib import Path

s = ''


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)


p = Path(r'C:\Users\dipan\colosseum\experiments\collusion\run_channel_study.py')
s = p.read_text(encoding='utf-8')
rep("""        pair_index = int(cfg['experiment']['channel_study'].get('pair_index', 0))
        ring_pairs = sorted(tuple(sorted(g)) for g in communication_network.channel_groups() if len(g) == 2)
        if not 0 <= pair_index < len(ring_pairs):
            raise ValueError('pair_index outside fixed ring edges')
        colluders = list(ring_pairs[pair_index])""",
"""        pair_index = int(cfg['experiment']['channel_study'].get('pair_index', 0))
        pair_layout = cfg['experiment']['channel_study'].get('pair_layout', 'adjacent')
        ring_edges = [tuple(sorted(str(m) for m in g)) for g in communication_network.channel_groups() if len(g) == 2]
        if pair_layout == 'adjacent':
            ring_pairs = sorted(ring_edges)
        elif pair_layout == 'nonadjacent':
            # Opposite ring positions: no shared neighbor board, so any private route needs two relays.
            ring = ring_order(ring_edges)
            ring_pairs = sorted(tuple(sorted((ring[i], ring[i + 3]))) for i in range(3))
        else:
            raise ValueError('pair_layout must be adjacent or nonadjacent')
        if not 0 <= pair_index < len(ring_pairs):
            raise ValueError('pair_index outside the ring pairs for this layout')
        colluders = list(ring_pairs[pair_index])""")
rep("""        selected = frozenset(str(member) for member in colluders)
        if selected not in edges:""", """        selected = frozenset(str(member) for member in colluders)
        nonadjacent = v3 and cfg['experiment']['channel_study'].get('pair_layout', 'adjacent') == 'nonadjacent'
        if nonadjacent and selected in edges:
            raise ValueError(f"Non-adjacent coalition {sorted(selected)} shares a ring edge")
        if not nonadjacent and selected not in edges:""")
rep("""        assert len(partner_boards) == 1, (""", """        expected_peer_boards = 0 if nonadjacent else 1
        assert len(partner_boards) == expected_peer_boards, (""")
rep("""            partner_boards[0],
        )""", """            partner_boards[0] if partner_boards else None,
        )""")
rep("""            'incentive': cfg['experiment']['channel_study']['incentive'],
            'agent_order'""", """            'incentive': cfg['experiment']['channel_study']['incentive'],
            'pair_layout': cfg['experiment']['channel_study'].get('pair_layout', 'adjacent'),
            'agent_order'""")
rep("""        VERSION, validate_config, PreferenceProtocol, PreferenceTools, save_channel_metrics,
    )""", """        VERSION, validate_config, PreferenceProtocol, PreferenceTools, save_channel_metrics, ring_order,
    )""")
p.write_text(s, encoding='utf-8')

p = Path(r'C:\Users\dipan\colosseum\experiments\collusion\choice\channel_preference_v3.py')
s = p.read_text(encoding='utf-8')
rep("""    if study.get('stage') not in ('engineering', 'research'):""", """    if study.get('pair_layout', 'adjacent') not in ('adjacent', 'nonadjacent'):
        raise ValueError('pair_layout must be adjacent or nonadjacent')
    if study.get('stage') not in ('engineering', 'research'):""")
rep("""def channel_metrics(audit,""", """def ring_order(edges):
    \"\"\"Walk the fixed six-agent ring from its alphabetically first member.\"\"\"
    adjacent = {}
    for a, b in edges:
        adjacent.setdefault(a, set()).add(b)
        adjacent.setdefault(b, set()).add(a)
    if len(adjacent) != 6 or any(len(v) != 2 for v in adjacent.values()):
        raise ValueError('Expected a six-agent ring')
    ring = [min(adjacent)]
    previous = None
    while len(ring) < 6:
        step = min(adjacent[ring[-1]] - {previous})
        previous = ring[-1]
        ring.append(step)
    if ring[0] not in adjacent[ring[-1]]:
        raise ValueError('Expected a single six-agent cycle')
    return ring


def channel_metrics(audit,""")
p.write_text(s, encoding='utf-8')
print('patched')
