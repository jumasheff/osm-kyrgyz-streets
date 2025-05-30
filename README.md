# OpenStreetMap\'ке кыргызча көчө аттарын кошуу

Бул долбоор Бишкек шаарындагы OpenStreetMap картасында кыргызча аталышы жок көчөлөргө `name:ky` тегин кошуу процессин автоматташтырууга арналган.

## Максат

OpenStreetMap маалыматтарын кыргыз тилиндеги аталыштар менен байытуу, карталардын жергиликтүү колдонуучулар үчүн жеткиликтүүлүгүн жана пайдалуулугун арттыруу.

## Иш агымы

Процесс төмөнкү негизги кадамдардан турат:

1.  **Маалыматтарды алуу**: `https://overpass-turbo.eu` сайтын колдонуп, Бишкектеги `name:ky` теги жок көчөлөрдү `.osm` форматында жүктөп алуу.
2.  **Аттарды которуу**: Google Gemini сыяктуу тил моделин колдонуп, көчөлөрдүн орусча аталыштарын кыргызчага которуу жана жаңыртылган маалыматтарды өзүнчө `.osm` файлына сактоо.
3.  **Өзгөрүүлөрдү даярдоо**: `osmosis` куралы аркылуу баштапкы жана которулган `.osm` файлдарын салыштырып, өзгөрүүлөрдү камтыган `.osc` (OSM Change) файлын түзүү.
4.  **OSM\'ге жүктөө**: JOSM (Java OpenStreetMap Editor) программасы аркылуу даярдалган `.osc` файлын OpenStreetMap серверине жүктөө.

## Колдонулган куралдар жана технологиялар

*   **Overpass API (overpass-turbo.eu аркылуу)**: OpenStreetMap маалымат базасынан керектүү объектилерди сурап алуу үчүн.
*   **Google Gemini (же башка тил модели)**: Көчө аттарын автоматтык түрдө которуу үчүн.
*   **Python**: Маалыматтарды иштетүү жана которуу процессин башкаруу скрипттери үчүн (мисалы, Gemini API менен иштөө).
*   **osmosis**: `.osm` файлдарынын ортосундагы айырмачылыктарды аныктап, `.osc` файлын түзүү үчүн.
*   **JOSM (Java OpenStreetMap Editor)**: Даярдалган өзгөрүүлөрдү OpenStreetMap\'ке жүктөө үчүн.

## Кадамдар
Кадамдар тууралуу [ушул блог-посттон](https://jumasheff.github.io/posts/2025-05-25-openstreetmap-kyrgyz-kocholor/) окусаңыз болот.

## Эскертүүлөр

*   Массалык түрдө өзгөртүү киргизүүдөн мурун, OpenStreetMap коомчулугунун эрежелери жана сунуштары менен таанышып чыгыңыз.
*   Котормолордун сапатына көңүл буруңуз. Мүмкүн болсо, жергиликтүү эксперттер же тил билгичтер менен кеңешиңиз.
*   Чакан топтомдор менен баштап, процессиңизди сынап көрүңүз.


## Техникалык жагы

Бул долбоорду иштетүү үчүн төмөнкү кадамдарды аткарыңыз:

### 1. Виртуалдык чөйрөнү түзүү жана активдештирүү

Долбоордун негизги папкасында виртуалдык чөйрө түзүңүз (мисалы, `.venv` деп атап):

```bash
python3 -m venv .venv
```

Түзүлгөн виртуалдык чөйрөнү активдештириңиз:

*   Linux/macOS:
    ```bash
    source .venv/bin/activate
    ```
*   Windows (Command Prompt):
    ```bash
    .venv\Scripts\activate.bat
    ```
*   Windows (PowerShell):
    ```bash
    .venv\Scripts\Activate.ps1
    ```

### 2. Көз карандылыктарды орнотуу

Долбоор үчүн керектүү Python китепканаларын `requirements.txt` файлынан орнотуңуз:

```bash
python3 -m pip install -r requirements.txt
```

Эми долбоордун скрипттерин иштетүүгө даярсыз.
