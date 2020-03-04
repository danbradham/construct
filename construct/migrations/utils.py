# -*- coding: utf-8 -*-

# Local imports
from ..io import fsfs


def create_old_project(where, pmnt='3D'):
    '''Creates a Construct 0.1.x style project.'''

    def new_asset(p, col, typ, asset):
        return [
            (p / pmnt / col, 'collection'),
            (p / pmnt / col / typ, 'asset_type'),
            (p / pmnt / col / typ / asset, 'asset'),
            (p / pmnt / col / typ / asset / 'model', 'task'),
            (p / pmnt / col / typ / asset / 'model/work/maya', 'workspace'),
            (p / pmnt / col / typ / asset / 'rig', 'task'),
            (p / pmnt / col / typ / asset / 'rig/work/maya', 'workspace'),
            (p / pmnt / col / typ / asset / 'shade', 'task'),
            (p / pmnt / col / typ / asset / 'shade/work/maya', 'workspace'),
            (p / pmnt / col / typ / asset / 'light', 'task'),
            (p / pmnt / col / typ / asset / 'light/work/maya', 'workspace'),
            (p / pmnt / col / typ / asset / 'comp', 'task'),
            (p / pmnt / col / typ / asset / 'comp/work/maya', 'workspace'),
        ]

    def new_shot(p, col, seq, shot):
        return [
            (p / pmnt / col, 'collection'),
            (p / pmnt / col / seq, 'sequence'),
            (p / pmnt / col / seq / shot, 'shot'),
            (p / pmnt / col / seq / shot / 'anim', 'task'),
            (p / pmnt / col / seq / shot / 'anim/work/maya', 'workspace'),
            (p / pmnt / col / seq / shot / 'light', 'task'),
            (p / pmnt / col / seq / shot / 'light/work/maya', 'workspace'),
            (p / pmnt / col / seq / shot / 'fx', 'task'),
            (p / pmnt / col / seq / shot / 'fx/work/maya', 'workspace'),
            (p / pmnt / col / seq / shot / 'comp', 'task'),
            (p / pmnt / col / seq / shot / 'comp/work/maya', 'workspace'),
        ]

    entries = [(where, 'project')]
    entries.extend(new_asset(where, 'assets', 'prop', 'prop_01'))
    entries.extend(new_asset(where, 'assets', 'product', 'product_01'))
    entries.extend(new_asset(where, 'assets', 'character', 'char_01'))
    entries.extend(new_shot(where, 'shots', 'seq_01', 'seq_01_010'))
    entries.extend(new_shot(where, 'shots', 'seq_01', 'seq_01_020'))
    entries.extend(new_shot(where, 'shots', 'seq_01', 'seq_01_030'))
    entries.extend(new_shot(where, 'users', 'user_01', 'user_01_010'))
    entries.extend(new_shot(where, 'users', 'user_01', 'user_01_020'))
    entries.extend(new_shot(where, 'users', 'user_01', 'user_01_030'))

    for path, tag in entries:
        fsfs.tag(path, tag)
