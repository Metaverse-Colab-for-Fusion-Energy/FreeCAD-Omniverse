import unittest
from file_utils import GetAuthCheck

class TestGetAuthCheckRealBatch(unittest.TestCase):

    def test_valid_project_returns_ok_access(self):
        usdlink = "omniverse://mcfe-nucleus.soe.manchester.ac.uk/Projects/FreeCAD/sampleProject/"
        stdout, stderr, permission = GetAuthCheck(usdlink)

        self.assertEqual(permission, 'OK_ACCESS')
        self.assertTrue(any('Connected username' in line for line in stdout))
        # Do not assume stderr is empty — it may contain log info

    def test_invalid_project_returns_no_access(self):
        usdlink = "omniverse://mcfe-nucleus.soe.manchester.ac.uk/Projects/aaaaa"
        stdout, stderr, permission = GetAuthCheck(usdlink)

        self.assertEqual(permission, 'NO_ACCESS')
        self.assertTrue(any('NOT_FOUND' in line for line in stdout))
        self.assertTrue(any('Cannot be found!' in line for line in stdout))

if __name__ == '__main__':
    unittest.main()
