import logging

from ..pathfinder import PathFinder
from ..modemanager import ModeManager

__title__ = 'EntSw General Library Mode Unit Tests'
__author__ = ['bborel']
__version__ = '2.0.0'

log = logging.getLogger(__name__)


class TestMach(object):
    uut_prompt_map = [
        ('BTLDR', 'switch: '),
        ('IOS', '[sS]witch> '),
        ('IOSE', '[sS]witch# '),
        ('DIAG', 'Diag> '),
        ('TRAF', 'Traf> '),
        ('SYMSH', '-> '),
        ('LINUX', r'(?:~ # )|(?:/[a-zA-Z][\S]* # )'),
        ('STARDUST', r'(?:Stardust> )|(?:[A-Z][\S]*> )'),
    ]
    uut_state_machine = {
        'BTLDR': [('LINUX', 1), ('IOS', 1)],
        'LINUX': [('BTLDR', 1), ('STARDUST', 1)],
        'IOS': [('IOSE', 1)],
        'IOSE': [('BTLDR', 1), ('IOS', 1)],
        'STARDUST': [('LINUX', 1), ('TRAF', 1), ('DIAG', 1), ('SYMSH', 1)],
        'TRAF': [('STARDUST', 1), ('SYMSH', 1)],
        'DIAG': [('STARDUST', 1), ('SYMSH', 1)],
        ('SYMSH', 1): [('STARDUST', 1), ('DIAG', 1), ('TRAF', 1)],
    }
    uut_state_machine2 = {
        'BTLDR': [('LINUX', 5), ('IOS', 10)],
        'LINUX': [('BTLDR', 7), ('STARDUST', 3)],
        'IOS': [('IOSE', 2)],
        'IOSE': [('BTLDR', 10), ('IOS', 2), ('IOSCFG', 3)],
        'IOSCFG': [('IOSE', 2)],
        'STARDUST': [('LINUX', 4), ('TRAF', 3), ('DIAG', 2), ('SYMSH', 2)],
        'TRAF': [('STARDUST', 1), ('SYMSH', 2)],
        'DIAG': [('STARDUST', 1), ('SYMSH', 2)],
        ('SYMSH', 1): [('STARDUST', 2), ('DIAG', 2), ('TRAF', 2)],
    }

    #
    # modemanager
    # ----------------------------------------------------------------------------------------------------------------------------------------------------------
    def test_modemanager(self):
        mmd = {'mode_module_fullname': 'apollo.scripts.entsw.libs.mode.tests.dummy_mode',
               'uut_conn': None,
               'current_mode': '',
               'verbose': True,
               'statemachine': TestMach.uut_state_machine,
               'uut_prompt_map': TestMach.uut_prompt_map}
        mm = ModeManager(True, **mmd)
        mm.current_mode = 'BTLDR'
        mm.print_uut_prompt_map()
        file_template = mm.build_product_mode_skeleton()
        print(file_template)
        assert "def create_mode_manager(uut_state_machine, uut_prompt_map, uut_conn, **kwargs):" in file_template
        assert "def btldr_to_ios(mm, **kwargs):" in file_template
        assert "def diag_to_symsh(mm, **kwargs):" in file_template
        # Need a sophisticated simulator to perform actual mode goto's.
        # assert mm.goto_mode('BTLDR')
        # assert mm.goto_mode('STARDUST')

    #
    # pathfinder
    # ----------------------------------------------------------------------------------------------------------------------------------------------------------
    def test_pathfinder1(self, capsys):
        sm = PathFinder()
        sm.add_node('s1', [('s11', 2), ('s2', 1), ('s3', 6), ('s4', 10)])
        sm.add_node('s2', [('s1', 2), ('s3', 5), ('s6', 1)])
        sm.add_node('s3', [('s1', 3), ('s4', 4), ('s6', 1)])
        sm.add_node('s4', [('s5', 1), ('s3', 8)])
        sm.add_node('s5', [('s4', 5), ('s7', 1)])
        sm.add_node('s6', [('s5', 2), ('s7', 3)])
        sm.add_node('s7', [('s6', 1), ('s5', 1)], stateful=True)
        sm.print_state_machine()
        out, err = capsys.readouterr()
        print('\n{0}'.format(out))
        print('\n{0}'.format(err))
        assert [('s1', 0), ('s2', 1), ('s6', 1), ('s5', 2)] == sm.get_path('s1', 's5', withcost=True)
        assert ['s1', 's2', 's6', 's5'] == sm.get_path('s1', 's5')
        assert ['s1', 's4', 's3', 's6', 's7', 's5'] == sm.get_path('s1', 's5', followpath=['s2', 's6', 's9'])
        assert ['s2', 's6', 's5'] == sm.get_path('s2', 's5')
        assert ['s3', 's1', 's4', 's5'] == sm.get_path('s3', 's5', 'MAXCOST')
        assert ['s7', 's5', 's4', 's3', 's1'] == sm.get_path('s7', 's1', 'MINHOP')
        assert ['s7', 's5', 's4', 's3', 's1'] == sm.get_path('s7', 's1')
        assert [] == sm.get_path('s1', 's1')

    def test_pathfinder2(self, capsys):
        mmd = {'statemachine': TestMach.uut_state_machine}
        sm = PathFinder(**mmd)
        sm.print_state_machine()
        out, err = capsys.readouterr()
        print('\n{0}'.format(out))
        print('\n{0}'.format(err))
        assert ['BTLDR', 'LINUX', 'STARDUST', 'TRAF'] == sm.get_path('BTLDR', 'TRAF')
        assert ['SYMSH', 'TRAF'] == sm.get_path('SYMSH', 'TRAF')
        assert ['STARDUST', 'SYMSH'] == sm.get_path('STARDUST', 'SYMSH')
        assert ['SYMSH', 'STARDUST', 'LINUX', 'BTLDR', 'IOS', 'IOSE'] == sm.get_path('SYMSH', 'IOSE')

