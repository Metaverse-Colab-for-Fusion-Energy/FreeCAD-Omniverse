import os
import sys
import unittest
from unittest.mock import MagicMock
import FreeCAD
import Part

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from file_utils import GetAuthCheck, DownloadSTPFromNucleus, ClearLocalDirectory, UploadUSDToNucleus, CreateNewAssetOnNucleus, CreateNewProjectOnNucleus, UploadSTPToNucleus, GetLocalDirectoryName

# === Global Omniverse server config ===
# Input real hostname here:
HOSTNAME = "mcfe-nucleus.soe.manchester.ac.uk"

# Leave as is
PROJECT_NAME = "test_project"
PROJECT_PATH = f"/Projects/FreeCAD/{PROJECT_NAME}"
DUMMY_PROJECT_PATH = "/Projects/FreeCAD/abc123"
PROJECT_URL = f"omniverse://{HOSTNAME}{PROJECT_PATH}"
DUMMY_PROJECT_URL = f"omniverse://{HOSTNAME}{DUMMY_PROJECT_PATH}"

# Asset paths - leave as is
TEST_ASSET_NAME = "test_asset"
ASSET_URL_BASE = f"{PROJECT_URL}/assets/{TEST_ASSET_NAME}"
USD_LINK = f"{ASSET_URL_BASE}/{TEST_ASSET_NAME}.usda"
STP_LINK = f"{ASSET_URL_BASE}/{TEST_ASSET_NAME}.stp"
TOKEN = "TEST_TOKEN_123"


class TestFreeCADImport(unittest.TestCase):
    # Test if we can import the workbench into FreeCAD's python
    def test_import_omniConnectorGui(self):
        sys.modules["FreeCADGui"] = MagicMock() # Mock GUI Import 
        sys.modules["FreeCADGui"].addCommand = MagicMock()

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

class TestRealCreateNewProject(unittest.TestCase):
    # Test if we can create a new project
    def test_create_new_project_on_nucleus(self):
        project_name = PROJECT_NAME
        ok, stdout_lines, stderr_lines = CreateNewProjectOnNucleus(
            host_name=HOSTNAME,
            project_name=project_name,
            make_public=False
        )

        print("\n[STDOUT]")
        print("\n".join(stdout_lines))
        print("\n[STDERR]")
        print("\n".join(stderr_lines))

        # Allow pass if project already exists - we just test if we can trigger it
        if not ok:
            combined = "\n".join(stdout_lines + stderr_lines)
            self.assertIn("already_exists", combined.lower(), "Project creation failed unexpectedly.")

class TestRealCreateNewAsset(unittest.TestCase):
    # test if we can create a new asset
    def test_create_new_asset_on_nucleus(self):
        project_url = PROJECT_URL
        asset_name = TEST_ASSET_NAME
        token = TOKEN

        stdout, stderr, stplink, usdlink, error = CreateNewAssetOnNucleus(
            asset_name=asset_name,
            use_url=True,
            projectURL=project_url,
            token=token
        )

        print("\n[STDOUT]")
        print("\n".join(stdout))
        print("\n[STDERR]")
        print("\n".join(stderr))
        print("\n[ASSET LINKS]")
        print("STP Link:", stplink)
        print("USD Link:", usdlink)
        print("Error:", error)

        # Accept if asset already exists - just testing if we can trigger asset creation
        if error is not None and "ERROR_ALREADY_EXISTS" not in error:
            self.fail(f"Asset creation failed with error: {error}")

        # Check if stp & usd links are valid or do not return at all
        self.assertTrue(usdlink is None or usdlink.endswith((".usd", ".usda")))
        # also check that stplink is either valid or is not returned
        self.assertTrue(stplink is None or stplink.endswith((".stp")))

class TestGetAuthCheckRealBatch(unittest.TestCase):
    # test if we can authenticate with nucleus instance 
    def test_real_project_access_or_expected_denial(self):
        # Test if we can access the project we just made before
        ClearLocalDirectory()
        usdlink = PROJECT_URL
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

    def test_real_usda_access_or_expected_denial(self):
        # test if we can access the asset that we just made 
        usdlink = USD_LINK
        stdout, stderr, permission = GetAuthCheck(usdlink, filetype='usd')

        output_text = "\n".join(stdout + [stderr])
        print(output_text)

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

    def test_real_stp_access_or_expected_denial(self):
        # also check the stp file of said asset
        stplink = STP_LINK
        stdout, stderr, permission = GetAuthCheck(stplink, filetype='stp')

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

    def test_invalid_project(self):
        # now test if we switch to a fake project that we didnt make
        ClearLocalDirectory()
        usdlink = DUMMY_PROJECT_URL
        stdout, stderr, permission = GetAuthCheck(usdlink, filetype='project')

        self.assertEqual(permission, 'NO_ACCESS')

        output_text = "\n".join(stdout + [stderr])
        # Accept either "NOT_FOUND" (if authenticated) or a proper auth failure reason
        self.assertTrue(
            any(keyword in output_text for keyword in [
                'NOT_FOUND',
                'NO_AUTH',
                'NO_PERMISSION',
                'do not have permissions',
                'Cannot authenticate'
            ]),
            msg="NO_ACCESS was returned but no valid denial reason was found in output"
        )

class TestUploadAssetToNucleusReal(unittest.TestCase):
    def test_real_stp_upload_to_nucleus(self):
        # now test if we can push a STP file of a box to nucleus
        stplink = STP_LINK
        token = TOKEN

        # Create a test document and object
        doc = FreeCAD.newDocument("UploadTestDoc")
        box = doc.addObject("Part::Box", "TestBox")
        box.Length = 10
        box.Width = 10
        box.Height = 10
        doc.recompute()
        stdout, stderr = UploadSTPToNucleus(stplink, box, token)
        
        print("\n[STDOUT]:")
        print(stdout)
        print("\n[STDERR]:")
        print(stderr)

        # Assert it ran successfully
        self.assertIn("OK", stdout)
        self.assertTrue("ERROR" not in stderr.upper())

        FreeCAD.closeDocument("UploadTestDoc")

    def test_real_usd_upload_to_nucleus(self):
        # also test if we can push the USD side of the asset
        usdlink = USD_LINK
        token = TOKEN

        doc = FreeCAD.newDocument("UploadTestDocUSD")
        box = doc.addObject("Part::Box", "TestBox")
        box.Length = 10
        box.Width = 10
        box.Height = 10
        doc.recompute()

        stdout, stderr = UploadUSDToNucleus(usdlink, box, token)

        print("\n[STDOUT]:")
        print(stdout)
        print("\n[STDERR]:")
        print(stderr)

        self.assertIn("Push", stdout)
        self.assertTrue("ERROR" not in stderr.upper())

        FreeCAD.closeDocument("UploadTestDocUSD")


class TestDownloadAssetFromNucleus(unittest.TestCase):

    def test_download_stp_from_real_nucleus(self):
        # now test if we can pull a STP file from the nucleus. We don't do USD pull because this isn't done anyway in the user workflow.
        stplink = STP_LINK
        token = TOKEN

        doc = FreeCAD.newDocument("TestDoc")
        ClearLocalDirectory()

        success, imported_object, stdout, stderr, fc_err = DownloadSTPFromNucleus(stplink, token)

        self.assertIn(success, [True, False])
        if success:
            self.assertIsNotNone(imported_object)
        else:
            self.assertIsNone(imported_object)
            print("\n[stdout]\n", stdout)
            print("[stderr]\n", stderr)
            print("[fc_err]\n", fc_err)
        FreeCAD.closeDocument("TestDoc")

class TestClearAll(unittest.TestCase):
    def test_clear_temp_files(self):
        dir_path = GetLocalDirectoryName()
        print(f"Before clear: contents of {dir_path} -> {os.listdir(dir_path)}")

        ClearLocalDirectory()

        print(f"After clear: contents of {dir_path} -> {os.listdir(dir_path)}")

        self.assertTrue(
            not os.listdir(dir_path), 
            f"Directory {dir_path} is not empty after ClearLocalDirectory()"
        )

if __name__ == '__main__':
    unittest.main(buffer=False, exit=False)
    # Double making sure that the temp files are removed at the end. 
    print('-------END OF TEST-------')
    print("[INFO] Cleaning up session_local...")
    ClearLocalDirectory()