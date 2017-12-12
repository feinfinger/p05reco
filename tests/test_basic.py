import unittest
from context import p05reco

class initReconTest(unittest.TestCase):

    def testInit(self):
        test_config = './reco_config_dlr_005d.ini'
        p05obj = p05reco.recoObject(test_config)
        print(p05obj.config)


if __name__ == "__main__":
    unittest.main()
