import unittest
import Player

class Test36KeyMode(unittest.TestCase):
    def test_missing_note_uses_nearest_available_key(self):
        custom_map = {48: 'low-c', 50: 'low-d'}
        self.assertEqual(Player.nearest_key_from_map(49, custom_map), 'low-c')
        self.assertEqual(Player.nearest_key_from_map(51, custom_map), 'low-d')

    def test_50_key_mode_maps_four_octaves_and_two_notes(self):
        self.assertEqual(len(Player.KEY_MAP_50), 50)
        self.assertEqual(Player.noteTrans(36, use_50_keys=True), 'NUMPADMULTIPLY')
        self.assertEqual(Player.noteTrans(37, use_50_keys=True), 'NUMPADDIVIDE')
        self.assertEqual(Player.noteTrans(48, use_50_keys=True), '`')
        self.assertEqual(Player.noteTrans(60, use_50_keys=True), 'z')
        self.assertEqual(Player.noteTrans(72, use_50_keys=True), 'w')
        self.assertEqual(Player.noteTrans(84, use_50_keys=True), '1')
        self.assertEqual(Player.noteTrans(85, use_50_keys=True), '2')
        self.assertEqual(Player.noteTrans(86, use_50_keys=True), 'e')

    def test_50_key_mode_maps_numpad_virtual_keys(self):
        self.assertEqual(Player.key_to_vk('NUMPADMULTIPLY'), 0x6A)
        self.assertEqual(Player.key_to_vk('NUMPADDIVIDE'), 0x6F)

    def test_21_key_mode_normalizes_and_uses_closest_note(self):
        # Same normalization and nearest-note behavior as WWM's Python mode.
        self.assertEqual(Player.noteTrans(48), 'z')
        self.assertEqual(Player.noteTrans(60), 'a')
        self.assertEqual(Player.noteTrans(61), 'a')
        self.assertEqual(Player.noteTrans(83), 'u')
        self.assertEqual(Player.noteTrans(84), 'q')
        self.assertTrue(Player.isNoteInRange(20))

    def test_note_trans_36_key_mode_supports_36_midi_notes(self):
        # WWM's chromatic layout uses the physical keys shown in the image.
        self.assertEqual(Player.noteTrans(48, use_36_keys=True), 'z')
        self.assertEqual(Player.noteTrans(49, use_36_keys=True), '3')
        self.assertEqual(Player.noteTrans(51, use_36_keys=True), '6')
        self.assertEqual(Player.noteTrans(60, use_36_keys=True), 'a')
        self.assertEqual(Player.noteTrans(72, use_36_keys=True), 'q')
        self.assertEqual(Player.noteTrans(83, use_36_keys=True), 'u')
        self.assertEqual(Player.noteTrans(84, use_36_keys=True), 'q')

    def test_key_range_for_36_key_mode(self):
        self.assertTrue(Player.isNoteInRange(36, use_36_keys=True))
        self.assertTrue(Player.isNoteInRange(83, use_36_keys=True))

    def test_key_map_has_exactly_36_entries_and_image_row_order(self):
        self.assertEqual(len(Player.KEY_MAP_36), 36)
        self.assertEqual(Player.KEY_MAP_36[48], 'z')
        self.assertEqual(Player.KEY_MAP_36[56], '=')
        self.assertEqual(Player.KEY_MAP_36[58], '/')
        self.assertEqual(Player.KEY_MAP_36[59], 'm')
        self.assertEqual(Player.KEY_MAP_36[60], 'a')
        self.assertEqual(Player.KEY_MAP_36[68], '-')
        self.assertEqual(Player.KEY_MAP_36[70], '.')
        self.assertEqual(Player.KEY_MAP_36[71], 'j')
        self.assertEqual(Player.KEY_MAP_36[72], 'q')
        self.assertEqual(Player.KEY_MAP_36[80], '0')
        self.assertEqual(Player.KEY_MAP_36[82], ',')
        self.assertEqual(Player.KEY_MAP_36[83], 'u')

    def test_find_best_key_for_36_mode_is_stable_identity_shift(self):
        # 36-key screenshot layer must not invent a transposition shift.
        self.assertEqual(Player.findBestKey('TruePianos 1.mid', use_36_keys=True), 0)
        self.assertEqual(Player.allToCMajor('TruePianos 1.mid', use_36_keys=True), [0])

    def test_key_symbol_to_windows_virtual_key_is_consistent_for_symbols(self):
        self.assertEqual(Player.key_to_vk('a'), ord('A'))
        self.assertEqual(Player.key_to_vk('['), 0xDB)
        self.assertEqual(Player.key_to_vk('/'), 0xBF)
        self.assertEqual(Player.key_to_vk(','), 0xBC)
        self.assertEqual(Player.key_to_vk('.'), 0xBE)

    def test_parse_key_keeps_physical_keys_unmodified(self):
        self.assertEqual(Player.parse_key('3'), ('3', None))
        self.assertEqual(Player.parse_key('/'), ('/', None))
        self.assertEqual(Player.parse_key('a'), ('a', None))

if __name__ == '__main__':
    unittest.main()
