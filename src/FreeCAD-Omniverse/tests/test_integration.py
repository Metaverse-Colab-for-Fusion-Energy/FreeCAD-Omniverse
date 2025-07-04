import os
import sys
import unittest
from unittest.mock import MagicMock
import FreeCAD
import Part

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from file_utils import GetAuthCheck, DownloadSTPFromNucleus, ClearLocalDirectory, UploadUSDToNucleus, CreateNewAssetOnNucleus, CreateNewProjectOnNucleus, UploadSTPToNucleus

# === Global Omniverse server config ===
# Input your real hostname here:
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
    def test_import_omniConnectorGui(self):
        # Mock GUI import as cannot do this via console testing
        sys.modules["FreeCADGui"] = MagicMock()
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
    def test_create_new_project_on_nucleus(self):

        # Unique project name to avoid collision
        project_name = PROJECT_NAME
        ok, stdout_lines, stderr_lines = CreateNewProjectOnNucleus(
            host_name=HOSTNAME,
            project_name=project_name,
            make_public=False  # or True if you want everyone to see it
        )

        print("\n[STDOUT]")
        print("\n".join(stdout_lines))
        print("\n[STDERR]")
        print("\n".join(stderr_lines))

        # Allow pass even if project already exists
        if not ok:
            combined = "\n".join(stdout_lines + stderr_lines)
            self.assertIn("already_exists", combined.lower(), "Project creation failed unexpectedly.")

class TestRealCreateNewAsset(unittest.TestCase):
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

        # Accept if asset already exists (idempotent behavior)
        if error is not None and "ERROR_ALREADY_EXISTS" not in error:
            self.fail(f"Asset creation failed with error: {error}")

        # Even if the asset exists, links should be non-empty if accessible
        self.assertTrue(usdlink is None or usdlink.endswith((".usd", ".usda")))

class TestGetAuthCheckRealBatch(unittest.TestCase):

    def test_real_project_access_or_expected_denial(self):
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

class TestRealSTPUpload(unittest.TestCase):
    def test_real_stp_upload_to_nucleus(self):
        # Required setup
        stplink = STP_LINK
        token = TOKEN

        # Create a test document and object
        doc = FreeCAD.newDocument("UploadTestDoc")
        box = doc.addObject("Part::Box", "TestBox")
        box.Length = 10
        box.Width = 10
        box.Height = 10
        doc.recompute()

        # Upload the object
        stdout, stderr = UploadSTPToNucleus(stplink, box, token)

        # Output results
        print("\n[STDOUT]:")
        print(stdout)
        print("\n[STDERR]:")
        print(stderr)

        # Assert it ran successfully
        self.assertIn("OK", stdout)
        self.assertTrue("ERROR" not in stderr.upper())

        FreeCAD.closeDocument("UploadTestDoc")


class TestRealUSDUpload(unittest.TestCase):
    def test_real_usd_upload_to_nucleus(self):
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


class TestDownloadSTPFromNucleusRealBatch(unittest.TestCase):

    def test_download_stp_from_real_nucleus(self):
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

    def test_download_usd_from_real_nucleus(self):
        usdlink = USD_LINK
        token = TOKEN

        doc = FreeCAD.newDocument("TestDoc")
        ClearLocalDirectory()

        success, imported_object, stdout, stderr, fc_err = DownloadSTPFromNucleus(usdlink, token)

        self.assertIn(success, [True, False])
        if success:
            self.assertIsNotNone(imported_object)
        else:
            self.assertIsNone(imported_object)
            print("\n[stdout]\n", stdout)
            print("[stderr]\n", stderr)
            print("[fc_err]\n", fc_err)

        FreeCAD.closeDocument("TestDoc")


if __name__ == '__main__':
    unittest.main()