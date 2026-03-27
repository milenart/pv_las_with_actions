# -*- coding: utf-8 -*-

from qgis.core import (
    QgsTask, QgsMessageLog, Qgis, QgsProject, QgsVectorLayer,
    QgsField, QgsGeometry, QgsPointXY, QgsPoint, QgsFeature,
    QgsPalLayerSettings, QgsTextFormat, QgsTextBufferSettings,
    QgsVectorLayerSimpleLabeling, QgsMapSettings, QgsRectangle
)
from qgis.PyQt.QtCore import QVariant, QMetaType
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtWidgets import QMessageBox
from ..constants import (
    LAYER_NAME_BDOT10K_DROGI, LAYER_NAME_BDOT10K_LINIE,
    VOLTAGE_TYPES, ROAD_TYPE_FOREST,
    SOIL_ROLES, LABEL_SETTINGS,
    LAYER_NAME_DROGI_LESNE_FILTER, AREA_HA_THRESHOLD,
    PROVIDERS, URI_TEMPLATE_POLYGON, URI_TEMPLATE_LINE,
    OUTPUT_ATTRS, RESULT_KEYS, INPUT_ATTRS,
    NAME_LAYER_OBSZARY, NAME_LAYER_LINIE, NAME_LAYER_DROGI, QGS_VER_INT_MIN
)
# Warstwa kompatybilności dla Qt5/Qt6 oraz unikanie DeprecationWarning w QGIS >= 3.30
if Qgis.QGIS_VERSION_INT >= QGS_VER_INT_MIN:
    # Składnia dla nowszych wersji
    TYPE_INT = QMetaType.Type.Int
    TYPE_DOUBLE = QMetaType.Type.Double
    TYPE_STRING = QMetaType.Type.QString
else:
    # Składnia dla starszych wersji
    TYPE_INT = QVariant.Int
    TYPE_DOUBLE = QVariant.Double
    TYPE_STRING = QVariant.String

from typing import List, Dict, Any, Optional, Tuple


from ..utils import LayerUtils, MessageUtils

class AnalizaTask(QgsTask):
   
    def __init__(self, description, wydzielenia_opisy, wydzielenia, oddzialy, drogi_lesne, mapa_bazowa, iface, raportBtn, wydrukBtn, analizaBtn, zapisBtn, resetujBtn, parent):
        super().__init__(description, QgsTask.CanCancel)

        self.parent = parent
        self.project = parent.project
        
        self.iface = iface
        self.raportBtn = raportBtn
        self.wydrukBtn = wydrukBtn
        self.zapisBtn = zapisBtn
        self.resetujBtn = resetujBtn
        self.analizaBtn = analizaBtn
        
        self.mapa_bazowa = mapa_bazowa
        
        self.exception = None
        self.result_data = None
        self.rodzaj_napiecia = VOLTAGE_TYPES

        # Wczytywanie danych
        MessageUtils.pushLogInfo("AnalizaTask: Wczytywanie obiektów...")

        # Wydzielnie i oddziały
        self._loadSourceLayers(wydzielenia_opisy, wydzielenia, oddzialy)
        
        # Drogi Leśne
        self._loadForestRoads(drogi_lesne)
        
        # Warstwy BDOT
        self._loadBDOTLayers()


    def run(self):
        """
        Przetwarzanie w tle. Używa załadowanych list obiektów.
        """
        MessageUtils.pushLogInfo('Rozpoczęto wykonywanie AnalizaTask')
        
        if self.drogi_publiczne_feats is None:
            MessageUtils.pushLogInfo("Ostrzeżenie: drogi_publiczne_feats jest None")
        if self.linie_feats is None:
            MessageUtils.pushLogInfo("Ostrzeżenie: linie_feats jest None")
            

        # Filtracja wydzielni (Poligon) po klasie bonitacji
        if self.isCanceled(): return False
        relevant_features = self._getPolygonsBySoil()
        if not relevant_features:
            MessageUtils.pushLogInfo("Nie znaleziono poprawnych obszarów")
            return False
        MessageUtils.pushLogInfo(f"Znaleziono {len(relevant_features)} poprawnych obszarów")

        # Operacje geometryczne
        if self.isCanceled(): return False
        single_parts = self._processGeometry(relevant_features)
        if not single_parts:
            MessageUtils.pushLogInfo("Nie znaleziono odpowiednich obiektów dla poprawnych ID")
            return False
        MessageUtils.pushLogInfo(f"Operacje geometryczne: {len(single_parts)} obszarów")

        # Filtracja obszarów po powierzchni 
        if self.isCanceled(): return False
        obszary_valid = self._filterValidAreaByArea(single_parts)
        if not obszary_valid:
            MessageUtils.pushLogInfo("Nie znaleziono odpowiednich obszarów > {AREA_HA_THRESHOLD}ha")
            return False
        MessageUtils.pushLogInfo(f"Znaleziono {len(obszary_valid)} poprawnych obszarów > {AREA_HA_THRESHOLD}ha")

        # Przypisanie adresów leśnych (adr_les) do obszarów
        if self.isCanceled(): return False
        obszary_valid = self._assignForestAdresses(obszary_valid, relevant_features)
        if not obszary_valid:
            MessageUtils.pushLogInfo("Nie udało się określić adresów")
            return False
        MessageUtils.pushLogInfo(f"Określenie adresów: {len(obszary_valid)} obszarów")


        # Analiza najbliższych linii i drog
        final_lines = []
        final_roads = []
        
        for obszar in obszary_valid:
            if self.isCanceled(): return False
            
            line_data, road_data = self._processProximityForArea(obszar)
            
            if line_data: final_lines.append(line_data)
            if road_data: final_roads.append(road_data)

        self.result_data = {
            'obszary': obszary_valid,
            'lines': final_lines,
            'roads': final_roads
        }
        MessageUtils.pushLogInfo(f"Analiza zakończona. Linie: {len(final_lines)}, Drogi: {len(final_roads)}")
        return True

    def finished(self, result):
        if self.isCanceled(): 
            MessageUtils.pushMessage(self.iface, "Analiza anulowana")
            self._toggleButtons(False)
            return
        
        if result and self.result_data:
            # Przygotowanie warstw
            self.obszary_layer = self._prepareLayer(NAME_LAYER_OBSZARY, URI_TEMPLATE_POLYGON, self.result_data['obszary'])
            self.linie_layer = self._prepareLayer(NAME_LAYER_LINIE, URI_TEMPLATE_LINE, self.result_data['lines'])
            self.drogi_layer = self._prepareLayer(NAME_LAYER_DROGI, URI_TEMPLATE_LINE, self.result_data['roads'])

            # Ustawienie etykietowania tylko dla obszarów
            self._applyObszaryLabeling(self.obszary_layer)

            # Dodanie do projektu i widoczność
            self.project.addMapLayers([self.obszary_layer, self.linie_layer, self.drogi_layer])
            self._setupLayerVisibility()
            self._zoomToResults()

            MessageUtils.pushMessage(self.iface, "Analiza zakończona sukcesem")
            self._toggleButtons(True)
        else:
            self._handleFailure()

    def cancel(self):
        MessageUtils.pushLogInfo('AnalizaTask anulowane')
        super().cancel()


    # FUNKCJE POMOCNICZE

    # -- Funkcje pomocnicze do init --
    
    def _loadSourceLayers(self, wydzielenia_opisy: QgsVectorLayer, wydzielenia: QgsVectorLayer, oddzialy: QgsVectorLayer) -> None:

        self.wydzielenia_opisy_feats = [f for f in wydzielenia_opisy.getFeatures()]
        MessageUtils.pushLogInfo(f"AnalizaTask: Wczytano {len(self.wydzielenia_opisy_feats)} wydzielenia_opisy")
        
        self.wydzielenia_feats = [f for f in wydzielenia.getFeatures()]
        MessageUtils.pushLogInfo(f"AnalizaTask: Wczytano {len(self.wydzielenia_feats)} wydzielenia")
    
        self.oddzialy_feats = [f for f in oddzialy.getFeatures() if f.hasGeometry()]
        MessageUtils.pushLogInfo(f"AnalizaTask: Wczytano {len(self.oddzialy_feats)} oddzialy")

    def _loadForestRoads(self, drogi_lesne: QgsVectorLayer) -> None:

        # Drogi Leśne
        self.drogi_lesne_feats = []
        try:
            fields = drogi_lesne.fields()
            idx = fields.indexOf(INPUT_ATTRS['kod'])
            if idx == -1: idx = 1 # Rezerwowy indeks (1)
            
            count_total = 0
            for f in drogi_lesne.getFeatures():
                count_total += 1

                if not f.hasGeometry():
                    continue

                if str(f[idx]) != LAYER_NAME_DROGI_LESNE_FILTER:
                    continue
                
                self.drogi_lesne_feats.append(f)
            
            MessageUtils.pushLogInfo(f"AnalizaTask: Wczytano {len(self.drogi_lesne_feats)} drogi_lesne (z {count_total}) z filtrem {LAYER_NAME_DROGI_LESNE_FILTER}")
        except KeyError as e:
            MessageUtils.pushLogInfo(f"AnalizaTask: Błąd konfiguracji atrybutów (brak klucza): {e}")
        except AttributeError as e:
            MessageUtils.pushLogInfo(f"AnalizaTask: Błąd dostępu do obiektu warstwy: {e}")
        except Exception as e:
            MessageUtils.pushLogInfo(f"AnalizaTask: Nieoczekiwany błąd: {e}")

    def _loadBDOTLayers(self) -> None:
        drogi_layer = LayerUtils.getLayerByName(LAYER_NAME_BDOT10K_DROGI, self.project)
        if drogi_layer:
            self.drogi_publiczne_feats = [f for f in drogi_layer.getFeatures() if f.hasGeometry()]
            MessageUtils.pushLogInfo(f"AnalizaTask: Wczytano {len(self.drogi_publiczne_feats)} drogi_publiczne")
        else:
            self.drogi_publiczne_feats = None
            MessageUtils.pushLogInfo("AnalizaTask: Warstwa BDOT Drogi NIE znaleziona")

        linie_layer = LayerUtils.getLayerByName(LAYER_NAME_BDOT10K_LINIE, self.project)
        if linie_layer:
            # Filtrowanie linii według rodzaju napięcia
            self.linie_feats = [f for f in linie_layer.getFeatures() 
                                if f.hasGeometry() and f[INPUT_ATTRS['rodzaj']] in self.rodzaj_napiecia]
            MessageUtils.pushLogInfo(f"AnalizaTask: Wczytano {len(self.linie_feats)} linie")
        else:
            self.linie_feats = None
            MessageUtils.pushLogInfo("AnalizaTask: Warstwa BDOT Linie NIE znaleziona")

    # -- Funkcje pomocnicze do run --

    def _getPolygonsBySoil(self) -> List[QgsFeature]:
        # Znajdź ID adresów, które spełniają warunek gleby (z opisów)
        valid_ids = {
            f[INPUT_ATTRS['id_adres']] 
            for f in self.wydzielenia_opisy_feats 
            if any(role in str(f[INPUT_ATTRS['gl']]) for role in SOIL_ROLES)
        }

        if not valid_ids:
            return []

        # Zwróć POLIGONY (z wydzielenia_feats), które mają te ID
        return [f for f in self.wydzielenia_feats if f[INPUT_ATTRS['id_adres']] in valid_ids]

    def _filterValidAreaByArea(self, geometries: List[QgsGeometry]) -> List[Dict[str, Any]]:
        # Filtracja obszarów po powierzchni
        obszary_valid = []
        for i, geom in enumerate(geometries):
            area_ha = geom.area() / 10000.0
            if area_ha > AREA_HA_THRESHOLD:
                obszary_valid.append({
                    RESULT_KEYS['geometry']: geom,
                    RESULT_KEYS['area_ha']: round(area_ha, 2),
                    RESULT_KEYS['id']: i+1
                })        
        return obszary_valid

    def _processGeometry(self, features: List[QgsFeature]) -> List[QgsGeometry]:
        # Zwraca geometry
        geometries = [f.geometry() for f in features if f.hasGeometry()]
        if not geometries: return []
        
        combined_geom = QgsGeometry.unaryUnion(geometries)
        
        if combined_geom.isMultipart():
            return combined_geom.asGeometryCollection()
            
        return [combined_geom]
        
    def _assignForestAdresses(self, obszary_valid: List[Dict[str, Any]], source_polygons: List[QgsFeature]) -> List[Dict[str, Any]]:
        for obszar in obszary_valid:
            if self.isCanceled(): return []
            
            contained_adresses = []
            geom_obszar = obszar[RESULT_KEYS['geometry']]
            
            for f in source_polygons:
                # Szybki test bounding boxa przed drogim intersects/contains
                if geom_obszar.boundingBox().intersects(f.geometry().boundingBox()):
                    if geom_obszar.contains(f.geometry()):
                        try:
                            adr = f[INPUT_ATTRS['adr_les']]
                        except KeyError:
                            adr = f.attributes()[2] # Rezerwowe pobranie atrybutu
                        contained_adresses.append(str(adr))
            
            obszar[OUTPUT_ATTRS['adres_lesny']] = '\n'.join(list(set(contained_adresses))) # set usuwa duplikaty
        
        return obszary_valid

    def _getNearestFeature(self, point_xy: QgsPointXY, features: List[QgsFeature]) -> Tuple[float, Optional[QgsFeature]]:
        """Zwraca (minimalna_odległość_kwadratowa, najbliższy_obiekt) lub (inf, None)."""
        if not features:
            return float('inf'), None
        
        min_dist_sqr = float('inf')
        nearest_feat = None
        
        for f in features:
            dist_sqr, _, _, _ = f.geometry().closestSegmentWithContext(point_xy)
            if dist_sqr < min_dist_sqr:
                min_dist_sqr = dist_sqr
                nearest_feat = f
                
        return min_dist_sqr, nearest_feat

    def _processProximityForArea(self, obszar: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Przeprowadza analizę linii i dróg dla pojedynczego obszaru."""
        centroid = obszar[RESULT_KEYS['geometry']].centroid()
        point_xy = QgsPointXY(centroid.asPoint())
        nr_ob = obszar[RESULT_KEYS['id']]

        line_result = self._analyzeNearestLine(nr_ob, point_xy)
        road_result = self._analyzeNearestRoad(nr_ob, point_xy)

        return line_result, road_result

    def _analyzeNearestLine(self, nr_ob: int, point_xy: QgsPointXY) -> Optional[Dict[str, Any]]:
        dist_sqr, feat = self._getNearestFeature(point_xy, self.linie_feats)
        if not feat:
            return None
            
        return {
            RESULT_KEYS['nr_ob']: nr_ob,
            RESULT_KEYS['dist']: dist_sqr ** 0.5,
            RESULT_KEYS['rodzaj']: self.rodzaj_napiecia.get(feat[INPUT_ATTRS['rodzaj']], 'unknown'),
            RESULT_KEYS['geometry']: feat.geometry()
        }

    def _analyzeNearestRoad(self, nr_ob: int, point_xy: QgsPointXY) -> Optional[Dict[str, Any]]:
        # Szukamy obu rodzajów dróg
        d_pub_sqr, f_pub = self._getNearestFeature(point_xy, self.drogi_publiczne_feats)
        d_for_sqr, f_for = self._getNearestFeature(point_xy, self.drogi_lesne_feats)

        # Logika wyboru drogi
        chosen_dist_sqr, chosen_feat, chosen_type = float('inf'), None, ''

        if d_pub_sqr <= d_for_sqr and f_pub:
            chosen_dist_sqr, chosen_feat = d_pub_sqr, f_pub
            try:
                chosen_type = f_pub[INPUT_ATTRS['rodzaj']]
            except KeyError:
                chosen_type = str(f_pub.attributes()[0])
                
            # Specyficzny warunek: droga publiczna w lesie (przecinająca oddziały)
            if self.oddzialy_feats:
                for oddz in self.oddzialy_feats:
                    if f_pub.geometry().intersects(oddz.geometry()):
                        chosen_type = ROAD_TYPE_FOREST
                        break
        elif f_for:
            chosen_dist_sqr, chosen_feat = d_for_sqr, f_for
            chosen_type = ROAD_TYPE_FOREST

        if not chosen_feat:
            return None

        return {
            RESULT_KEYS['nr_ob']: nr_ob,
            RESULT_KEYS['dist']: chosen_dist_sqr ** 0.5,
            RESULT_KEYS['rodzaj']: chosen_type,
            RESULT_KEYS['geometry']: chosen_feat.geometry()
        }

    # -- Funkcje pomocnicze do finished --

    def _prepareLayer(self, layer_name: str, uri: str, data_list: List[Dict[str, Any]]) -> QgsVectorLayer:
        """Mapowanie danych do warstwy"""
        layer = QgsVectorLayer(uri, layer_name, PROVIDERS['MEMORY'])
        pr = layer.dataProvider()
        layer.startEditing()

        # Definiujemy kolumny (pola) w zależności od nazwy warstwy
        if layer_name == NAME_LAYER_OBSZARY:
            pr.addAttributes([
                QgsField(OUTPUT_ATTRS['nr_ob'], int(TYPE_INT)),
                QgsField(OUTPUT_ATTRS['adres_lesny'], TYPE_STRING),
                QgsField(OUTPUT_ATTRS['powierzchnia'], TYPE_DOUBLE, len=10, prec=2)
            ])
        elif layer_name == NAME_LAYER_LINIE or layer_name == NAME_LAYER_DROGI:
            # Dla linii i dróg kolumny są takie same
            pr.addAttributes([
                QgsField(OUTPUT_ATTRS['nr_ob'], int(TYPE_INT)),
                QgsField(OUTPUT_ATTRS['odleglosc'], TYPE_DOUBLE, len=10, prec=2),
                QgsField(OUTPUT_ATTRS['rodzaj'], TYPE_STRING)
            ])
        
        layer.updateFields()

        # Dodajemy obiekty
        for item in data_list:
            f = QgsFeature()
            f.setGeometry(item[RESULT_KEYS['geometry']])
            
            # Przypisujemy wartości do kolumn w zależności od typu warstwy
            if layer_name == NAME_LAYER_OBSZARY:
                f.setAttributes([
                    item[RESULT_KEYS['id']], 
                    item[OUTPUT_ATTRS['adres_lesny']], 
                    item[RESULT_KEYS['area_ha']]
                ])
            elif layer_name == NAME_LAYER_LINIE or layer_name == NAME_LAYER_DROGI:
                f.setAttributes([
                    item[RESULT_KEYS['nr_ob']], 
                    item[RESULT_KEYS['dist']], 
                    item[RESULT_KEYS['rodzaj']]
                ])
            
            pr.addFeatures([f])

        layer.commitChanges()
        LayerUtils.applyLayerStyle(layer, layer_name)
        return layer

    def _applyObszaryLabeling(self, layer: QgsVectorLayer) -> None:
        """Ustawia styl etykietowania obszarów."""
        ls = QgsPalLayerSettings()
        tf = QgsTextFormat()

        tf.setFont(QFont(LABEL_SETTINGS['font_family'], LABEL_SETTINGS['font_size']))
        color_parts = [int(x.strip()) for x in LABEL_SETTINGS['color_rgb'].split(',')]
        tf.setColor(QColor(*color_parts))
        bs = QgsTextBufferSettings()
        bs.setEnabled(True)
        bs.setSize(LABEL_SETTINGS['buffer_size'])
        tf.setBuffer(bs)

        ls.setFormat(tf)
        ls.fieldName = OUTPUT_ATTRS['nr_ob']
        ls.xOffset = LABEL_SETTINGS['x_offset']
        ls.yOffset = LABEL_SETTINGS['y_offset']
        ls.placement = QgsPalLayerSettings.AroundPoint 
        
        ls.enabled = True

        layer.setLabeling(QgsVectorLayerSimpleLabeling(ls))
        layer.setLabelsEnabled(True)

    def _setupLayerVisibility(self) -> None:
        """Pokazuje tylko wyniki i mapę bazową."""
        layers_to_show = [self.obszary_layer.id(), self.linie_layer.id(), self.drogi_layer.id(), self.mapa_bazowa.id()]
        for child in self.project.layerTreeRoot().children():
            child.setItemVisibilityChecked(child.layerId() in layers_to_show)

    def _zoomToResults(self) -> None:
        """Przybliża do wyników."""
        extent = self.obszary_layer.extent()
        if not extent.isEmpty():
            self.iface.mapCanvas().setExtent(extent.buffered(extent.width() * 0.1))
            self.iface.mapCanvas().refresh()

    def _toggleButtons(self, success: bool) -> None:
        """Włącza/wyłącza przyciski."""
        self.resetujBtn.setEnabled(True)
        self.raportBtn.setEnabled(success)
        self.wydrukBtn.setEnabled(success)
        self.zapisBtn.setEnabled(success)
        self.analizaBtn.setEnabled(not success)

    def _handleFailure(self) -> None:
        MessageUtils.pushWarning(self.iface, "Analiza nie powiodła się lub została przerwana.")
        self._toggleButtons(False)
