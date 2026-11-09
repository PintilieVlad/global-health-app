# Lab 2 – Results

The run used here took place on 4 November 2026, 18:28–18:30 (EET), on macOS 27.0.1. The
software was Python 3.14.8, PostgreSQL 18.6 (Postgres.app), pandas 3.1.0, SQLAlchemy 2.1.6
and Alembic 1.20.1. The steps were:

1. The database was upgraded with `python -m app.create_tables`. The Lab 1 schema was
   stamped at revision `0001`, then migration `0002` added `observation.is_outlier`.
2. The raw files were downloaded by running `notebooks/lab2_exploration.ipynb` (Task 2.1).
3. The data was imported twice with the three import scripts, in the order World Bank,
   WHO, OWID (`python -m etl.import_worldbank`, `python -m etl.import_who`,
   `python -m etl.import_owid`).
4. The overview queries and the checks in
   [`db/quality_checks.sql`](../db/quality_checks.sql) were run on the database after the
   second import. The tables below are their results.

## Data availability on the day of the run

| Source | Download | Result |
| --- | --- | --- |
| World Bank | country list and 5 indicators, 2000–2024 | 6 files, HTTP 200 |
| Our World in Data | 2 charts (full CSV) | 2 files, HTTP 200 |
| WHO GHO | `SDGPM25` and `SDGAIRBODA` from 2000 | **HTTP 503 Service Unavailable** (HTTP 500 on 2 November) |

The WHO import therefore printed `SDGPM25 SKIP (missing SDGPM25_from2000.json)`, and the
same for `SDGAIRBODA`; the other indicators were imported normally. The WHO extractor and
transform could only be checked on synthetic records in the GHO format. They will run on
real data once the API is back.

The WHO data portal (data.who.int) was online. It reads from a different API
(`xmart-api-public.who.int`), whose records have another shape: M49 numeric country codes,
the sex as `TOTAL`/`MALE`/`FEMALE`, and a cause-of-death dimension. Adapting the extractor
to it is a possible improvement. For Task 2.4 the WHO value comes from `SH.STA.AIRP.P5`
instead: it is WHO's estimate, republished by the World Bank.

## Task 2.1 – Missing values per indicator

From the last cell of the notebook. "Empty values" are rows of the downloaded file without
a value. "Country-years without a value" is the share of the 5,425 combinations of the 217
World Bank countries and the 25 years 2000–2024 for which the source has no value.

| Indicator | Rows in file | Empty values | Empty values % | Countries with data | Years with data | Country-years without a value % |
| --- | --- | --- | --- | --- | --- | --- |
| EN.ATM.PM25.MC.M3 | 6650 | 698 | 10.5 | 200 | 2000–2023 | 11.5 |
| SH.STA.AIRP.P5 | 6650 | 6419 | 96.5 | 183 | 2019 | 96.6 |
| SH.PRV.SMOK | 6650 | 4733 | 71.2 | 166 | 2000–2024 | 72.5 |
| EG.CFT.ACCS.ZS | 6650 | 650 | 9.8 | 192 | 2000–2024 | 11.5 |
| NY.GDP.PCAP.CD | 6650 | 208 | 3.1 | 214 | 2000–2024 | 3.4 |
| OWID_CRD_DEATH_RATE | 4939 | 0 | 0.0 | 111 | 1950–2024 | 59.7 |
| OWID_PM25_EXPOSURE | 6912 | 0 | 0.0 | 215 | 1998–2024 | 0.9 |

The two sources report missing data in different ways:

- **The World Bank returns a full grid.** There is one record per economy and year
  (266 economies × 25 years = 6,650), with `value: null` when data is missing. The 266
  economies include 49 aggregates (World, regions, income groups), which the cleaning removes.
  The amount of missing data depends on how each indicator is produced:
  - **PM2.5:** the GBD 2023 model ends in 2023. The 17 countries without any value are mostly
    small territories (Aruba, Gibraltar, the Cayman Islands, ...), plus Liechtenstein, Hong
    Kong and Macao SAR, and Kosovo.
  - **Air pollution mortality (`SH.STA.AIRP.P5`):** estimated for 2019 only.
  - **Tobacco use:** WHO estimates exist only for 2000, 2005, 2007, 2010, 2015, 2020 and
    2022–2024.
- **Our World in Data lists only the rows that have a value**, so its files have no empty
  values. For these indicators the missing data is the absent country-years. The chronic
  respiratory diseases death rate covers only 111 of the 217 countries, the countries that
  report causes of death to the WHO Mortality Database. Its coverage also shrinks in recent
  years because of the reporting lag: 89 countries in 2019, 69 in 2022, 48 in 2023 and 17 in
  2024. The satellite-based PM2.5 exposure covers every country except the Channel Islands.

## Cleaning: rows kept and dropped per rule

From the log lines of the first import. The second import printed identical lines.

| Indicator | Raw rows | Not a known country | Missing value | Year outside 2000–2024 | Clean (loaded) | IQR outliers flagged |
| --- | --- | --- | --- | --- | --- | --- |
| EN.ATM.PM25.MC.M3 | 6650 | 1225 | 625 | 0 | 4800 | 197 |
| SH.STA.AIRP.P5 | 6650 | 1225 | 5242 | 0 | 183 | 0 |
| SH.PRV.SMOK | 6650 | 1225 | 3931 | 0 | 1494 | 11 |
| EG.CFT.ACCS.ZS | 6650 | 1225 | 625 | 0 | 4800 | 0 |
| NY.GDP.PCAP.CD | 6650 | 1225 | 183 | 0 | 5242 | 423 |
| OWID_CRD_DEATH_RATE | 4939 | 90 | 0 | 2665 | 2184 | 112 |
| OWID_PM25_EXPOSURE | 6912 | 1080 | 0 | 432 | 5400 | 227 |
| SDGPM25, SDGAIRBODA (WHO) | – | – | – | – | skipped | – |

Several rules dropped no rows: fractional years, unknown sex or residence-area codes, values
outside the plausible bounds, and duplicates. The rows that were not known countries were:

- **World Bank:** the 49 aggregates. The five income groups among them have an empty
  `countryiso3code`.
- **OWID, CRD death rate:** the French overseas departments Guadeloupe, French Guiana,
  Martinique, Mayotte and Réunion, which are not separate World Bank economies.
- **OWID, PM2.5:** the 14 OWID aggregates (`OWID_WRL`, `OWID_EUR`, ...) and 26 territories
  outside the World Bank list (e.g. Taiwan, Western Sahara, Vatican). Kosovo was kept: OWID
  codes it `OWID_KOS`, and the cleaning maps that to the World Bank code `XKX`.

The 2,665 and 432 rows outside the year window are the CRD years 1950–1999 and the PM2.5
years 1998–1999.

## Task 2.2 – IQR outlier flag

`clean_observations()` computes Q1 and Q3 of each indicator over all its countries and
years, with linear interpolation (the pandas default), and sets IQR = Q3 − Q1. A row is
flagged `is_outlier = true` when its value is below Q1 − 1.5 × IQR or above
Q3 + 1.5 × IQR. Flagged rows are stored, not dropped.

The flag needs a new column, `observation.is_outlier`. It is a BOOLEAN NOT NULL with default
`false`, added by the Alembic migration
[`alembic/versions/0002_observation_is_outlier.py`](../alembic/versions/0002_observation_is_outlier.py).
The counts below come from the query `iqr_outliers_per_indicator`. They were also
recomputed from the raw files with an independent script (Python standard library only),
which gave the same numbers.

| Indicator | Rows | Q1 | Q3 | IQR | Upper fence | Flagged | % | Flagged countries (rows) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EN.ATM.PM25.MC.M3 (µg/m³) | 4800 | 12.88 | 30.35 | 17.47 | 56.56 | 197 | 4.1 | 16: Bangladesh, Qatar, Saudi Arabia (24 each), Kuwait (23), Niger (22), Nigeria (20), Bahrain (15), Pakistan (13), UAE (8), Bolivia, Peru (6), … |
| OWID_PM25_EXPOSURE (µg/m³) | 5400 | 10.70 | 26.30 | 15.60 | 49.70 | 227 | 4.2 | 14: Bangladesh, Kuwait, Qatar (25 each), UAE (24), Nigeria (22), Saudi Arabia (20), Cameroon, Niger (19), Bahrain (16), India, Pakistan (11), … |
| SH.STA.AIRP.P5 (per 100,000) | 183 | 31.65 | 165.45 | 133.80 | 366.15 | 0 | 0.0 | – |
| OWID_CRD_DEATH_RATE (per 100,000) | 2184 | 16.22 | 29.28 | 13.06 | 48.87 | 112 | 5.1 | 12: South Africa (18), Kazakhstan (15), Argentina (14), Maldives (12), Kyrgyz Republic (11), Philippines (10), Mauritius, Brunei, Fiji, Brazil, Sri Lanka, Moldova |
| SH.PRV.SMOK (% of adults) | 1494 | 14.30 | 31.30 | 17.00 | 56.80 | 11 | 0.7 | 6: Kiribati, Myanmar (3 each), Nauru (2), Bangladesh, Comoros, Nepal (1 each) |
| EG.CFT.ACCS.ZS (% of population) | 4800 | 26.00 | 98.00 | 72.00 | 206.00 | 0 | 0.0 | – |
| NY.GDP.PCAP.CD (current US$) | 5242 | 1,576.38 | 21,289.68 | 19,713.30 | 50,859.64 | 423 | 8.1 | 32: Bermuda, Liechtenstein, Monaco (25 each), Luxembourg (23), Norway, Switzerland (21), Qatar (20), … |

The highest flagged values (query `iqr_outliers_examples`) were:

- PM2.5 (World Bank): Qatar 2003, 124.66 µg/m³
- PM2.5 (OWID): Qatar 2022, 85.7 µg/m³
- CRD death rate: Kyrgyz Republic 2003, 99.91
- Tobacco use: Kiribati 2000, 68 %
- GDP per capita: Monaco 2024, US$ 288,001.57

**Interpretation.**

- **Every flag is a high outlier.** All these indicators are right-skewed, so the lower
  fence is negative and nothing falls below it.
- **The flagged values are real, which is why they are kept.** The PM2.5 outliers are the
  countries with desert dust (Gulf states, Sahel) or heavy combustion pollution (South
  Asia). These are exactly the high-exposure countries the research question is about.
  Dropping them would cut off the upper end of the exposure range.
- **The GDP flag marks small, very rich economies.** In the regression GDP per capita will
  be log-transformed, so these values will not dominate.
- **The flag allows a sensitivity analysis.** The models can be fitted with and without the
  flagged rows.
- **Bounded indicators are not flagged.** `SH.STA.AIRP.P5` and the clean-cooking percentage
  have a very wide IQR, so no value is extreme relative to it.

## Task 2.3 – Running the imports twice

Both runs printed the same line for every indicator, for example
`EN.ATM.PM25.MC.M3 raw= 6650 clean= 4800 loaded= 4800 outliers= 197`. Both also exited with
status 0.

**Overview query after each run** (`overview_rows_per_indicator`). The output was identical
after the first and after the second run (`diff` found no difference):

| code | name | rows | first_year | last_year |
| --- | --- | --- | --- | --- |
| EG.CFT.ACCS.ZS | Access to clean fuels and technologies for cooking | 4800 | 2000 | 2024 |
| EN.ATM.PM25.MC.M3 | PM2.5 air pollution, mean annual exposure | 4800 | 2000 | 2023 |
| NY.GDP.PCAP.CD | GDP per capita | 5242 | 2000 | 2024 |
| OWID_CRD_DEATH_RATE | Chronic respiratory diseases death rate, age-standardized (WHO Mortality Database) | 2184 | 2000 | 2024 |
| OWID_PM25_EXPOSURE | Outdoor air pollution exposure, population-weighted PM2.5 (SatPM) | 5400 | 2000 | 2024 |
| SH.PRV.SMOK | Prevalence of current tobacco use | 1494 | 2000 | 2024 |
| SH.STA.AIRP.P5 | Mortality rate attributed to household and ambient air pollution, age-standardized | 183 | 2019 | 2019 |

**Query 2 (duplicates on the natural key)** returned no rows after the second run.

**`import_log`** has seven rows per run, one per imported indicator; skipped indicators
are not logged. Rows 1–7 are the first run and rows 8–14 the second:

| import_id | source_name | indicator_code | rows_loaded | imported_at |
| --- | --- | --- | --- | --- |
| 14 | Our World in Data | OWID_PM25_EXPOSURE | 5400 | 2026-11-04 18:29:55+02 |
| 13 | Our World in Data | OWID_CRD_DEATH_RATE | 2184 | 2026-11-04 18:29:55+02 |
| 12 | World Bank | NY.GDP.PCAP.CD | 5242 | 2026-11-04 18:29:54+02 |
| 11 | World Bank | EG.CFT.ACCS.ZS | 4800 | 2026-11-04 18:29:54+02 |
| 10 | World Bank | SH.PRV.SMOK | 1494 | 2026-11-04 18:29:54+02 |
| 9 | World Bank | SH.STA.AIRP.P5 | 183 | 2026-11-04 18:29:54+02 |
| 8 | World Bank | EN.ATM.PM25.MC.M3 | 4800 | 2026-11-04 18:29:53+02 |
| 7 | Our World in Data | OWID_PM25_EXPOSURE | 5400 | 2026-11-04 18:29:52+02 |
| 6 | Our World in Data | OWID_CRD_DEATH_RATE | 2184 | 2026-11-04 18:29:52+02 |
| 5 | World Bank | NY.GDP.PCAP.CD | 5242 | 2026-11-04 18:29:51+02 |
| 4 | World Bank | EG.CFT.ACCS.ZS | 4800 | 2026-11-04 18:29:51+02 |
| 3 | World Bank | SH.PRV.SMOK | 1494 | 2026-11-04 18:29:51+02 |
| 2 | World Bank | SH.STA.AIRP.P5 | 183 | 2026-11-04 18:29:51+02 |
| 1 | World Bank | EN.ATM.PM25.MC.M3 | 4800 | 2026-11-04 18:29:50+02 |

The `url` column holds the request URL that each raw file was downloaded from, for example
`https://api.worldbank.org/v2/country/all/indicator/EN.ATM.PM25.MC.M3?date=2000%3A2024&per_page=10000&format=json`.
It is read from the file's `.source.json`, not a local path.

The second run updated the 24,103 existing rows instead of adding new ones, for two
reasons:

- `upsert_observations()` uses `INSERT ... ON CONFLICT ON CONSTRAINT uq_observation DO UPDATE`.
  The constraint is on (country, indicator, year, sex, residence area), so a row that
  already exists is updated in place.
- The cleaning removes duplicates within a download first, so one statement never touches
  the same key twice.

## Task 2.4 – Data quality checks

The queries of the lab handout are adapted to this project in two ways. They use this
project's indicators instead of life expectancy and health spending. Queries 2 and 4 also
take `residence_area` into account, because it is part of the natural key: WHO splits PM2.5
into urban, rural and total. Three queries were added: 1b, 4b and 7b.

**1. Countries.**

| countries | regions |
| --- | --- |
| 217 | 7 |

The World Bank country list has 296 entries, and the 79 whose region is "Aggregates"
were removed by `transform_worldbank_country_records()`. The 217 remaining are the economies the
World Bank classifies. They include territories such as Aruba, Bermuda and the Channel
Islands. The 7 values are the World Bank's geographic regions. *1b* searches for typical
aggregate codes (WLD, EAS, ECS, LMC, HIC, EUU, AFE) and the region "Aggregates" and finds
none. **As expected.**

**2. No duplicates on the natural key.** No rows, even after two imports. **As expected.**

**3. Values inside the plausible bounds.**

| code | unit | min_value | max_value | avg_value |
| --- | --- | --- | --- | --- |
| EG.CFT.ACCS.ZS | % of population | 0.0000 | 100.0000 | 64.13 |
| EN.ATM.PM25.MC.M3 | µg/m³ | 1.3869 | 124.6574 | 23.37 |
| NY.GDP.PCAP.CD | current US$ | 109.5938 | 288001.5749 | 16314.53 |
| OWID_CRD_DEATH_RATE | deaths per 100,000 people | 5.1584 | 99.9113 | 24.43 |
| OWID_PM25_EXPOSURE | µg/m³ | 1.1000 | 85.7000 | 19.92 |
| SH.PRV.SMOK | % of adults | 3.1000 | 68.0000 | 23.60 |
| SH.STA.AIRP.P5 | per 100,000 population | 7.4000 | 305.1000 | 100.77 |

Every minimum and maximum lies inside its bound in `etl/clean.py`:

- PM2.5: (0, 500]
- death rates: [0, 1000]
- percentages: [0, 100]
- GDP per capita: (0, 500,000]

No row was dropped by the range check either, since no import logged "value outside
plausible bounds". So the sources contained no impossible values. The maxima are the
outliers discussed in Task 2.2. Clean-cooking access spans the full range, from 0 % to
100 % of the population. The two PM2.5 estimates have means of 23.4 µg/m³ (World Bank,
GBD 2023 model) and 19.9 µg/m³ (OWID, SatPM satellite model). They come from different
models over slightly different countries and years, and the Romanian series below shows
the same gap. **As expected.**

**4. Sex codes.**

| sex | count |
| --- | --- |
| BTSX | 24103 |

Only known codes appear. All stored indicators are totals for both sexes. `MLE` and `FMLE`
would come from WHO's `SDGAIRBODA`, which is split by sex but could not be downloaded.
*4b* returns only `TOTL` for the residence area, for the same reason: the urban and rural
split comes from WHO's `SDGPM25`. **As expected.**

**5. Missing values and the year window.**

| null_values | nan_values | out_of_window |
| --- | --- | --- |
| 0 | 0 | 0 |

The cleaning drops rows without a value instead of storing them as 0. `load.py` turns
pandas `NaN` into SQL `NULL` (an uncertainty interval that is missing is stored as `NULL`,
never as the special NUMERIC value `'NaN'`). The extra column `nan_values` confirms that no
`'NaN'` was stored. **As expected.**

**6. Rows stored compared with the last import.**

| indicator_code | rows_loaded | rows_stored |
| --- | --- | --- |
| EG.CFT.ACCS.ZS | 4800 | 4800 |
| EN.ATM.PM25.MC.M3 | 4800 | 4800 |
| NY.GDP.PCAP.CD | 5242 | 5242 |
| OWID_CRD_DEATH_RATE | 2184 | 2184 |
| OWID_PM25_EXPOSURE | 5400 | 5400 |
| SH.PRV.SMOK | 1494 | 1494 |
| SH.STA.AIRP.P5 | 183 | 183 |

The counts are equal for every indicator: both imports used the same raw files, and no
older rows exist. The counts would differ after a source revision that removes rows, since
the upsert updates rows but never deletes them. **As expected.**

**7. Coverage gaps: countries without a chronic respiratory diseases death rate.**
**106 of the 217 countries** have no value for `OWID_CRD_DEATH_RATE` in any year
(the full list follows the table). *7b* counts them per region:

| region | countries | without_crd |
| --- | --- | --- |
| East Asia & Pacific | 37 | 25 |
| Europe & Central Asia | 58 | 10 |
| Latin America & Caribbean | 42 | 13 |
| Middle East, North Africa, Afghanistan & Pakistan | 23 | 9 |
| North America | 3 | 1 |
| South Asia | 6 | 4 |
| Sub-Saharan Africa | 48 | 44 |

This is the most important limitation found by the checks.

- **The gaps follow the quality of death registration.** The WHO Mortality Database only
  contains countries with usable cause-of-death registration, so 44 of the 48 Sub-Saharan
  countries are missing.
- **The missing countries include the most populous ones:** China, India, Indonesia,
  Pakistan, Bangladesh, Nigeria and Ethiopia. Several of them (Bangladesh, India, Nigeria,
  Pakistan) are among the PM2.5 outliers of Task 2.2.
- **Consequences for the analysis:**
  - A regression of the CRD death rate on PM2.5 covers about 110 mostly high- and
    middle-income countries. It can say little about the countries with the highest
    exposure.
  - `SH.STA.AIRP.P5` (183 countries, 2019) is the complement for those countries. It is a
    modelled estimate, not a registered count.
  - The WHO mortality data (`SDGAIRBODA`) should be added when the GHO API is available
    again.

<details>
<summary>The 106 countries without any CRD death rate</summary>

Afghanistan, Algeria, American Samoa, Andorra, Angola, Aruba, Bangladesh, Benin, Bermuda,
Bhutan, Bolivia, Botswana, British Virgin Islands, Burkina Faso, Burundi, Cambodia, Cameroon,
Cayman Islands, Central African Republic, Chad, Channel Islands, China, Comoros,
Congo (Dem. Rep.), Congo (Rep.), Côte d'Ivoire, Curaçao, Djibouti, Dominica,
Equatorial Guinea, Eritrea, Eswatini, Ethiopia, Faroe Islands, French Polynesia, Gabon,
The Gambia, Ghana, Gibraltar, Greenland, Guam, Guinea, Guinea-Bissau, Haiti, Honduras, India,
Indonesia, Isle of Man, Kenya, Kiribati, Korea (Dem. People's Rep.), Kosovo, Lao PDR,
Lesotho, Liberia, Libya, Liechtenstein, Macao SAR, Madagascar, Malawi, Mali,
Marshall Islands, Mauritania, Micronesia (Fed. Sts.), Monaco, Morocco, Mozambique, Myanmar,
Namibia, Nauru, Nepal, New Caledonia, Niger, Nigeria, Northern Mariana Islands, Pakistan,
Palau, Papua New Guinea, Rwanda, Samoa, San Marino, São Tomé and Príncipe, Senegal,
Sierra Leone, Sint Maarten, Solomon Islands, Somalia, South Sudan, St. Kitts and Nevis,
St. Martin (French part), Sudan, Tanzania, Timor-Leste, Togo, Tonga, Tunisia,
Turks and Caicos Islands, Tuvalu, Uganda, Vanuatu, Viet Nam, Virgin Islands (U.S.),
West Bank and Gaza, Yemen, Zambia, Zimbabwe.

</details>

### One country over time

This is the overview query `overview_one_country`, adapted to the topic: two PM2.5
estimates and the CRD death rate for Romania.

| year | pm25_worldbank | pm25_owid | crd_death_rate |
| --- | --- | --- | --- |
| 2000 | 23.7731 | 20.1000 | 24.8547 |
| 2005 | 24.9079 | 20.5000 | 22.8984 |
| 2010 | 18.8450 | 18.2000 | 20.0803 |
| 2015 | 18.0989 | 17.7000 | 20.3042 |
| 2019 | 16.4167 | 16.3000 | 21.1304 |
| 2020 | 16.0420 | 15.2000 | 23.4943 |
| 2021 | 16.1004 | 14.9000 | NULL |
| 2022 | 16.4101 | 15.1000 | 21.2192 |
| 2023 | 16.0077 | 14.9000 | NULL |
| 2024 | NULL | 14.3000 | NULL |

The table above is an excerpt; the query returns all 25 years.

- **Exposure:** in Romania it fell between 2000 and 2019, from 23.8 to 16.4 µg/m³ in the
  World Bank series (−31 %) and from 20.1 to 16.3 µg/m³ in the OWID series (−19 %).
- **The two estimates converge:** they differ by 3.7 µg/m³ in 2000 and only 0.1 µg/m³ in
  2019.
- **Gaps:** the CRD series has no value for 2021, 2023 or 2024 (reporting gaps of the WHO
  Mortality Database). The World Bank PM2.5 series ends in 2023.

### Comparison with the source websites (Romania, 2019)

The values on the websites were read on 4 November 2026 in a web browser:

- **World Bank:** the chart tooltip on data.worldbank.org.
- **Our World in Data:** the "Table" tab of each chart, year 2019.
- **WHO:** the Romania page of data.who.int.

| Source | Indicator | Value in the raw file | Stored value | Value on the website | Agreement |
| --- | --- | --- | --- | --- | --- |
| World Bank | `NY.GDP.PCAP.CD` GDP per capita (current US$) | 12909.6104013244 | 12909.6104 | 12,909.6 ([data.worldbank.org](https://data.worldbank.org/indicator/NY.GDP.PCAP.CD?locations=RO)) | yes |
| Our World in Data | `OWID_CRD_DEATH_RATE` deaths per 100,000 | 21.130419 | 21.1304 | 21.1 ([ourworldindata.org](https://ourworldindata.org/grapher/chronic-respiratory-diseases-death-rate-who-mdb?tab=table&time=2019)) | yes |
| WHO (republished by the World Bank) | `SH.STA.AIRP.P5` air pollution deaths per 100,000, age-standardized | 67.8 | 67.8000 | World Bank: 67.8 ([data.worldbank.org](https://data.worldbank.org/indicator/SH.STA.AIRP.P5?locations=RO)); WHO: **46.8 [33.6–59.6]** ([data.who.int](https://data.who.int/countries/642)) | yes with the World Bank, **no with WHO** |

Two more checks were made:

- **`OWID_PM25_EXPOSURE`:** stored 16.3000, website 16.30 µg/m³. They agree.
- **`EN.ATM.PM25.MC.M3`:** the API returned 16.4166768529099, stored as 16.4167 (`NUMERIC(18,4)`
  rounds to four decimals). The World Bank page for Romania and this indicator returned
  HTTP 500 ("Sorry, something went wrong") on 4 November, although the world-level page
  worked. This value could therefore not be checked on the website.

**Explanation.**

- **The pipeline stores the source values unchanged.** The stored values match the raw
  files up to the four decimals of `NUMERIC(18,4)`. They also match what each publisher
  shows on its own website, which rounds to one decimal.
- **The WHO value differs, and the difference is between publishers, not a pipeline error.**
  The World Bank cites the WHO Global Health Observatory for `SH.STA.AIRP.P5` but publishes
  a single 2019 estimate, 67.8. WHO's own portal now shows 46.8, from a revised series for
  2010–2019 (the portal reports "−17.3 since 2010"). The World Bank most likely republishes
  an earlier release of the WHO estimates; the new value is 31 % lower.
- **This is why provenance is recorded.** For each value we keep the source and the download
  time (`import_log` and the `.source.json` files). It is also a reason to prefer the
  original publisher, here the WHO API, once it is reachable again.
