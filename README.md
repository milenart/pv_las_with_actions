# Fotowoltaika LP

## PL

Wtyczka pozwala na wyznaczanie miejsc lokalizacji dla farm fotowoltaicznych na gruntach w zarządzie Lasów Państwowych. 

### Wymagania:
Warunkiem koniecznym do prawidłowego działania wtyczki jest posiadanie wersji QGIS 3.28.0 lub wyższej.

#### Warstwy pochodne niezbędne do działania wtyczki:
- pow_pol.shp
- wydz_pol.shp
- kom_lin.shp
- oddz_pol.shp
- ow_pkt.shp
- nadl_pol.shp

Przykładowy zestaw warstw pochodnych do pobrania jest dostępny [tutaj](https://downloads.envirosolutions.pl/dane/test_layers.zip).

W przypadku chęci przeanalizowania własnych danych należy pobrać warstwy pochodne dla danego nadleśnictwa z Systemu Informatycznego Lasów Państwowych. Struktura danych, która jest konieczna do poprawnego działania wtyczki jest następująca:
- wydz_pol.shp (wydzielenia - poligon):
    - id_adres (Int64) - klucz unikalny łączący geometrię wydzielenia z jego opisem z warstwy ow_pkt. Np. "1215014353"
    - adr_les (String) - pełny adres wydzielenia leśnego. Atrybut jest przypisywany do warstwy wynikowej i wyświetlany w raporcie jako identyfikator obszaru. Np. "12-15-1-01-39    -d   -00"
- ow_pkt.shp (lokalizacja opisów wydzieleń - punkt):
    - id_adres (Int64) - klucz unikalny łączący geometrię punktu z jego opisem z warstwy wydz_pol. Np. "1215014353"
    - g_l (String) - określa typ/klasę gleby. Wtyczka filtruje wydzielenia leśne na podstawie tego atrybutu. Wtyczka szuka w ciągu znaków wartości "RV" lub "RVI". Np. "j RIVA"
- kom_lin.shp (drogi - linia):
    - kod_ob (String) - kod, rodzaj ciągu komunikacyjnego. Wtyczka szuka obiektów, gdzie wartość pola równa się "DROGI L". Np. "DROGI L"
- pow_pol.shp (powiaty - poligon):
    - woj (String) - kod województwa. Np. "02"
    - pow (String) - kod powiatu. Np. "15"
    Na podstawie tych danych wtyczka wyznacza, jakie dane pobrać z BDOT10K.
- nadl_pol.shp (nadleśnictwo - poligon):
    - nzw_nadl (String) - nazwa nadleśnictwa. Wtyczka wykorzystuje ten atrybut do nadawania nazwy na wydruku i w raporcie. Np. "RYTEL"
- oddz_pol.shp (oddziały - poligon):
    - geom (Geometria) - Wykorzystywany do analizy przestrzennej. Na podstawie tej geometrii definiuje się, czy wybrana droga z BDOT jest leśna.

### Instrukcja pobrania:
1. Wtyczkę należy zainstalować w QGIS jako ZIP bądź wgrać pliki wtyczki do lokalizacji `C:\Users\User\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins`.
2. Aby uruchomić wtyczkę, należy kliknąć na ikonę żółtego drzewka ze słońcem.
3. Jeżeli ikona wtyczki nie jest widoczna w panelu warstw, spróbuj zrestartować QGIS.
4. Jeżeli wtyczka nadal nie jest widoczna, należy przejść w QGIS Desktop do Wtyczki -> Zarządzanie wtyczkami -> Zainstalowane -> Fotowoltaika LP -> Odinstalować wtyczkę i zainstalować ponownie.

### Instrukcja użytkowania:
1. W oknie wtyczki, w sekcji Wczytywanie danych, kliknij przycisk "Wczytaj warstwy pochodne". Otworzy się okno wyboru folderu zip z warstwami pochodnymi dla danego nadleśnictwa, pobranym z Systemu Informatycznego Lasów Państwowych.
2. Po wybraniu folderu zip z warstwami pochodnymi do projektu zostaną załadowane warstwy z drogami leśnymi i wydzieleniami leśnymi danego nadleśnictwa, a także mapa bazowa – Rastrowa Mapa Topograficzna Polski.
3. W oknie wtyczki, w sekcji Wczytywanie danych, kliknij przycisk "Pobierz i wyświetl dane BDOT10K".
4. Do projektu zostanie załadowana warstwa linii energetycznych i dróg z BDOT10k dla powiatów, w obrębie których znajdują się wydzielenia leśne danego nadleśnictwa. Ładowanie danych może potrwać kilka minut.
5. Po załadowaniu ww. warstw można przystąpić do wykonania analizy na potrzeby farm fotowoltaicznych. Należy kliknąć przycisk "Wykonaj analizę na potrzeby fotowoltaiki w LP". Analiza może potrwać kilka minut.
6. Do projektu zostaną załadowane warstwy z wyznaczonymi obszarami, a także warstwy z najbliższymi liniami energetycznymi i najbliższymi drogami.
7. Możliwości wtyczki:
    - Wtyczka pozwala na zapisanie warstw z wyznaczonymi obszarami, najbliższymi liniami energetycznymi i najbliższymi drogami do pliku Shapefile po kliknięciu przycisku "Zapisz warstwy" i wybraniu lokalizacji zapisu w oknie dialogowym.
    - Wtyczka umożliwia również wygenerowanie dokumentu w formacie PDF lub obrazu rastrowego po kliknięciu przycisku "Generuj wydruk" i zapisaniu go w lokalizacji wybranej w oknie dialogowym. Wydruk będzie zawierał mapę z wyznaczonymi obszarami, najbliższymi liniami energetycznymi i najbliższymi drogami.
    - Możliwe jest również wygenerowanie raportu (plik XLSX) z tabelarycznym wykazem wyznaczonych obszarów oraz podanymi odległościami od najbliższych dróg i linii energetycznych wraz z ich rodzajem. W tym celu należy kliknąć przycisk "Generuj raport".
8. Na każdym etapie można wyczyścić dane za pomocą przycisku "Wyczyść". Czyści z pamięci wtyczki poprzednie dane i pozwala na ponowne wykonanie po kolei wszystkich kroków. Nie usuwa już uprzednio dodanych warstw. 

### Uwagi
- Ikona ze znakiem zapytania w oknie wtyczki pozwala na pobranie instrukcji obsługi wtyczki w formacie PDF.
- Do prawidłowego działania wtyczki niezbędne jest połączenie z Internetem oraz zainstalowany program do obsługi arkuszy kalkulacyjnych.
- Rekomendowane wersje QGIS: 3.34.4.

#### Wyznaczone obszary muszą spełnić następujące warunki:
- być w zarządzie PGL LP,
- mieć powierzchnię powyżej 1.5 ha (pojedyncze wydzielenia leśne lub grupa sąsiadujących wydzieleń),
- być gruntami rolnymi,
- zaliczać się do IV lub poniżej klasy bonitacji gleby.

#### Przykład użycia

![przyklad_uzycia](docs/przyklad_uzycia.gif)

## EN

The plugin allows for the identification of suitable locations for photovoltaic power stations on land managed by the State Forests (PGL LP).

### Requirements:
To use the plugin, you need QGIS version 3.28.0 or higher.

#### Necessary layers for the plugin:
- pow_pol.shp
- wydz_pol.shp
- kom_lin.shp
- oddz_pol.shp
- ow_pkt.shp
- nadl_pol.shp

A sample set of derived layers is available for download [here](https://downloads.envirosolutions.pl/dane/test_layers.zip).

If you wish to analyze your own data, you must download the derived layers for a specific Forest District from the State Forests Information System (SILP). The data structure required for the plugin is as follows:

- wydz_pol.shp (compartments - polygon):
    - id_adres (Int64) - unique key linking the compartment geometry to its description from the ow_pkt layer. E.g., "1215014353"
    - adr_les (String) - full address of the forest compartment. This attribute is assigned to the result layer and displayed in the report as the area identifier. E.g., "12-15-1-01-39    -d   -00"
- ow_pkt.shp (location of compartment descriptions - point):
    - id_adres (Int64) - unique key linking the point geometry to its description from the wydz_pol layer. E.g., "1215014353"
    - g_l (String) - indicates the soil type/class. The plugin filters forest compartments based on this attribute. The plugin searches for the values "RV" or "RVI" in the string. E.g., "j RIVA"
- kom_lin.shp (roads - line):
    - kod_ob (String) - code, type of communication route. The plugin searches for objects where the field value equals "DROGI L". E.g., "DROGI L"
- pow_pol.shp (counties - polygon):
    - woj (String) - voivodeship code. E.g., "02"
    - pow (String) - county code. E.g., "15"
    Based on this data, the plugin determines which data to download from BDOT10K.
- nadl_pol.shp (forest district - polygon):
    - nzw_nadl (String) - name of the forest district. The plugin uses this attribute to assign a name in the printout and report. E.g., "RYTEL"
- oddz_pol.shp (compartments - polygon):
    - geom (Geometry) - used for spatial analysis. Based on this geometry, it is determined whether a selected road from BDOT is a forest road.

### Installation instructions:
1. Install the plugin in QGIS as a ZIP file or upload the plugin files to the location `C:\Users\User\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins`.
2. To activate the plugin, click on the icon with a sun and solar panel.
3. If the plugin icon is not visible in the layer panel, try restarting QGIS.
4. If the plugin is still not visible, go to QGIS Desktop -> Plugins -> Manage and Install Plugins -> Installed -> Fotowoltaika LP -> Uninstall the plugin and reinstall it.

### Usage instructions:
1. In the plugin window, under the Data Loading (Wczytywanie danych) section, click "Load derived layers" (Wczytaj warstwy pochodne). Select the ZIP folder containing the layers for the Forest District.
2. After selection, the forest roads and sub-compartments will be loaded into the project, along with a base map (Raster Topographic Map of Poland)
3. Click the button "Download and display BDOT10K data" (Pobierz i wyświetl dane BDOT10K).
4. Power line and road layers from the BDOT10K database will be loaded for the relevant counties. This may take several minutes
5. Once loaded, click "Perform PV analysis for State Forests" (Wykonaj analizę na potrzeby fotowoltaiki w LP). The analysis may take few minutes.
6. The project will now display the identified areas, the nearest power lines, and the nearest roads.
7. Plugin Features:
   - Save Layers: Save identified areas and nearby infrastructure to Shapefiles by clicking "Save layers" (Zapisz warstwy).
   - Generate Printout: Create a PDF or raster image by clicking "Generate printout" (Generuj wydruk). The layout will include the map with identified areas and infrastructure.
   - Generate Report: Export an XLSX file with a tabular list of identified areas, including distances to the nearest roads and power lines. Click "Generate report" (Generuj raport).
8. You can use the "Clear" (Wyczyść) button at any stage. This clears the plugin's memory and allows you to restart the process. Note: This does not remove layers already added to the QGIS layers panel.

### Notes
- The question mark icon in the plugin window allows you to download the user guide in PDF format.
- For the plugin to work correctly, an internet connection and spreadsheet editing software must be installed.
- Recommended version of QGIS: 3.34.4.

#### Designated areas must meet the following criteria:
- Managed by PGL LP,
- Have an area greater than 1.5 hectares (individual forest compartments or neighboring groups),
- Be agricultural land,
- Fall into IV or lower soil bonitation classes.

#### Usage Example

![example_usage](docs/przyklad_uzycia.gif)
