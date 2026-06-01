#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
PtolChain Node — canonical Flask node
Merged from JackCoin (save=True sync) + JackCoin5001 (serialization fix).
Port from PTOLEMY_CHAIN_PORT env / Config.DEFAULT_PORT — no hardcodes.
Callimachus audit trail: blocks carry face_id and record_type fields.
"""
import os
import sys
import json

from flask import Flask, request, jsonify

# Relative imports (package mode)
try:
    from .Block   import Block
    from .Chain   import Chain
    from .Sync    import Sync, sync_local
    from .Config  import DEFAULT_PORT, PEERS, NUM_ZEROS, CHAINDATA_DIR
except ImportError:
    from Block    import Block
    from Chain    import Chain
    from Sync     import Sync, sync_local
    from Config   import DEFAULT_PORT, PEERS, NUM_ZEROS, CHAINDATA_DIR

node = Flask(__name__)

# Sync and save the overall "best" blockchain from peers on startup
node_blocks = Sync(save=True)


@node.route('/blockchain.json', methods=['GET'])
def get_blockchain():
    """Return full blockchain as JSON."""
    local_chain = sync_local()
    python_blocks = []
    for block in local_chain:
        python_blocks.append({
            'index':     block.index,
            'timestamp': block.timestamp,
            'data':      block.data,
            'hash':      block.hash,
            'prev_hash': block.prev_hash,
        })
    return json.dumps(python_blocks)


@node.route('/audit', methods=['POST'])
def audit_record():
    """
    Callimachus audit trail endpoint.
    POST JSON: { face_id, record_type, payload }
    Mines a new block with the record as data.
    Used by LuthSpell halt records and Aule forge events.
    """
    try:
        rec  = request.get_json(force=True)
        data = json.dumps(rec)
        from Mine import mine_block
        block = mine_block(data)
        return jsonify({'status': 'ok', 'index': block.index,
                        'hash': block.hash}), 201
    except Exception as e:
        return jsonify({'status': 'error', 'detail': str(e)}), 500


@node.route('/status', methods=['GET'])
def status():
    local_chain = sync_local()
    return jsonify({'length': len(local_chain), 'port': _port})


if __name__ == '__main__':
    _port = int(sys.argv[1]) if len(sys.argv) >= 2 else DEFAULT_PORT
    node.run(host='127.0.0.1', port=_port)
