import unittest
from unittest.mock import patch, MagicMock
from omniConnectorGui import GetAuthCheck

class TestGetAuthCheck(unittest.TestCase):
    @patch('omniConnectorGui.subprocess.Popen')
    @patch('omniConnectorGui.GetFetcherScriptsDirectory')
    @patch('omniConnectorGui.GetBatchFileName')
    def test_GetAuthCheck_ok_access(self, mock_batch, mock_script_dir, mock_popen):
        # Setup
        mock_script_dir.return_value = "C:/Scripts"
        mock_batch.return_value = "check_auth.bat"

        process_mock = MagicMock()
        attrs = {
            'communicate.return_value': (
                b'Connection successful\r\nPermissions granted\r\n', 
                b''
            )
        }
        process_mock.configure_mock(**attrs)
        mock_popen.return_value = process_mock

        stdout, stderr, permission = GetAuthCheck("omniverse://host/project")

        # Test output
        self.assertEqual(permission, 'OK_ACCESS')
        self.assertIn('Connection successful', stdout[0])
        self.assertEqual(stderr, '')

    @patch('omniConnectorGui.subprocess.Popen')
    @patch('omniConnectorGui.GetFetcherScriptsDirectory')
    @patch('omniConnectorGui.GetBatchFileName')
    def test_GetAuthCheck_no_access(self, mock_batch, mock_script_dir, mock_popen):
        # Setup
        mock_script_dir.return_value = "C:/Scripts"
        mock_batch.return_value = "check_auth.bat"

        process_mock = MagicMock()
        attrs = {
            'communicate.return_value': (
                b'ERROR: NO_AUTH\r\n', 
                b'Some error occurred'
            )
        }
        process_mock.configure_mock(**attrs)
        mock_popen.return_value = process_mock

        stdout, stderr, permission = GetAuthCheck("omniverse://host/project")

        # Test output
        self.assertEqual(permission, 'NO_ACCESS')
        self.assertIn('NO_AUTH', stdout[0])
        self.assertIn('Some error occurred', stderr)

if __name__ == '__main__':
    unittest.main()
