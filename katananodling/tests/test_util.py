import logging
import unittest

from katananodling.util import Version

logger = logging.getLogger(__name__)


class VersionTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def _log(self, *args):
        msg = "[{}] ".format(self.id().split(".", 1)[-1])
        args = map(str, args)
        msg += " ".join(args)
        logger.info(msg)
        return

    def test_init_error(self):

        with self.assertRaises(AssertionError):
            version = Version("5.2")

        with self.assertRaises(ValueError):
            version = Version("5-2-1")

        with self.assertRaises(TypeError):
            version = Version(None)

        with self.assertRaises(TypeError):
            version = Version(5)

        version = Version("5.2.3")
        version = Version([5, 2, 3])
        version = Version((5, 2, 3))

    def test_init(self):

        version = Version("2.0.3")
        self.assertEqual(version.version, (2, 0, 3))
        self.assertEqual(str(version), "2.0.3")
        self.assertEqual(version.major, 2)
        self.assertEqual(version.minor, 0)
        self.assertEqual(version.patch, 3)

        version = Version((2, 0, 3))
        self.assertEqual(version.version, (2, 0, 3))
        self.assertEqual(str(version), "2.0.3")
        self.assertEqual(version.major, 2)
        self.assertEqual(version.minor, 0)
        self.assertEqual(version.patch, 3)

    def test_operator(self):

        versionA = Version("2.0.3")
        versionB = Version("2.0.3")
        versionC = Version("2.0.0")

        self.assertEqual(versionA, versionB)
        self.assertNotEqual(versionA, versionC)


if __name__ == "__main__":
    unittest.main()
