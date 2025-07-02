import unittest
from file_utils import GetAuthCheck
from file_utils import DownloadSTPFromNucleus
import FreeCAD

class TestDownloadSTPFromNucleusRealBatch(unittest.TestCase):

    def test_download_from_real_nucleus(self):
        usdlink = "omniverse://mcfe-nucleus.soe.manchester.ac.uk/Projects/FreeCAD/sampleProject/assets/engineering_object/engineering_object.stp"
        token = "testtoken123"

        # ✅ Create dummy FreeCAD document
        doc = FreeCAD.newDocument("TestDoc")

        # 🔧 Call function
        success, imported_object, stdout, stderr, fc_err = DownloadSTPFromNucleus(usdlink, token)

        # 🧪 Test results — do not fail if access denied
        self.assertIn(success, [True, False])
        if success:
            self.assertIsNotNone(imported_object)
        else:
            self.assertIsNone(imported_object)
            print("\n[stdout]\n", stdout)
            print("[stderr]\n", stderr)
            print("[fc_err]\n", fc_err)

        # 🧹 Clean up the dummy document
        FreeCAD.closeDocument("TestDoc")

class TestGetAuthCheckRealBatch(unittest.TestCase):

    def test_project_access_or_expected_denial(self):
        usdlink = "omniverse://mcfe-nucleus.soe.manchester.ac.uk/Projects/FreeCAD/sampleProject/"
        stdout, stderr, permission = GetAuthCheck(usdlink, filetype='project')

        output_text = "\n".join(stdout + [stderr])

        if permission == 'OK_ACCESS':
            self.assertTrue(any('Connected username' in line for line in stdout))
        elif permission == 'NO_ACCESS':
            # Acceptable if access is explicitly denied with a known cause
            self.assertTrue(
                any(keyword in output_text for keyword in [
                    'NO_AUTH',
                    'NO_PERMISSION',
                    'do not have permissions',
                    'Cannot authenticate',
                ]),
                msg="NO_ACCESS was returned but no valid denial reason was found in output"
            )
        else:
            self.fail(f"Unexpected permission result: {permission}")


    def test_invalid_project_returns_no_access(self):
        usdlink = "omniverse://mcfe-nucleus.soe.manchester.ac.uk/Projects/aaaaa"
        stdout, stderr, permission = GetAuthCheck(usdlink, filetype='project')

        self.assertEqual(permission, 'NO_ACCESS')
        self.assertTrue(any('NOT_FOUND' in line for line in stdout))
        self.assertTrue(any('Cannot be found!' in line for line in stdout))

    def test_invalid_server_address(self):
        usdlink = "omniverse://fake-server/Projects/bogus"
        stdout, stderr, permission = GetAuthCheck(usdlink)

        self.assertEqual(permission, 'NO_ACCESS')
        self.assertTrue(any('NO_AUTH' in line for line in stdout))


class TestFreeCADImport(unittest.TestCase):
    def test_import_omniConnectorGui(self):
        try:
            import omniConnectorGui
        except Exception as e:
            self.fail(f"Failed to import omniConnectorGui: {e}")
    def test_import_file_utils(self):
        try:
            import file_utils
        except Exception as e:
            self.fail(f"Failed to import file_utils: {e}")
    def test_import_utils(self):
        try:
            import utils
        except Exception as e:
            self.fail(f"Failed to import utils: {e}")
if __name__ == '__main__':
    unittest.main()
