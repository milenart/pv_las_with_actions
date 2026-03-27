import unittest
from unittest.mock import patch
from .base_test import QgsPluginBaseTest, PLUGIN_NAME
from .constants import GPKG_POWIATY

class TestBdotDownload(QgsPluginBaseTest):
    required_files = [GPKG_POWIATY]
    
    def setUp(self):
        super().setUp()
        # Przygotowanie warstwy powiatu
        self.dialog.powiaty = self.loadLayer(GPKG_POWIATY, self.module_const.INPUT_LAYERS['powiaty']['layer_name'], self.module_const.INPUT_LAYERS['powiaty']['layer_name'])
        self.project.addMapLayer(self.dialog.powiaty)

    @patch(f'{PLUGIN_NAME}.modules.dane_bdot_task.LayerUtils.applyLayerStyle')
    def testPobieranieBdot(self, mock_style):
        print("\n" + "=" * 50)
        print(f"\n [TEST] Pobieranie danych BDOT10k")
        
        self.dialog.wczytajDaneBdot10k()
        task = getattr(self.dialog, 'bdot_task', None)
        self.waitForTask(task, timeout=300)

        l_drogi = self.project.mapLayersByName(self.module_const.LAYER_NAME_BDOT10K_DROGI)
        
        self.assertEqual(len(l_drogi), 1)
        cnt = l_drogi[0].featureCount()
        self.assertGreater(cnt, 0)

        print(f" [WYNIK] Dane pobrane poprawnie, niezerowa liczba obiektow \n")
        print('=' * 50)

if __name__ == "__main__":
    unittest.main()
