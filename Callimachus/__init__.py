# from Callimachus.Database import Database
# from Callimachus.DBControlPanel import DBControlPanel
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Callimachus v09 live wire shim.
Routes new code to HyperDatabase while keeping old Database import working.

Usage (new code):
    from Callimachus import get_db
    db = get_db()           # returns HyperDatabase singleton
    db.put(record, lsh)
    db.get(label)

Legacy code (Ptolemy3.py, DBControlPanel.py) continues using:
    from Callimachus.Database import Database
    db = Database(parent=self)   # unchanged — still works
"""
import os

_PTOL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HW_DB_PATH = os.path.join(_PTOL_ROOT, 'Callimachus', 'hyperwebster.db')

_hw_db_instance = None

def get_db(path: str = None):
    """Return the HyperDatabase singleton. Creates on first call."""
    global _hw_db_instance
    if _hw_db_instance is None:
        try:
            from Callimachus.v09.database.hyperdatabase import HyperDatabase
            _hw_db_instance = HyperDatabase(path or _HW_DB_PATH)
        except Exception as e:
            print(f"[Callimachus] HyperDatabase init failed: {e}")
            _hw_db_instance = None
    return _hw_db_instance

def close_db():
    global _hw_db_instance
    if _hw_db_instance is not None:
        try:
            _hw_db_instance.close()
        except Exception:
            pass
        _hw_db_instance = None
