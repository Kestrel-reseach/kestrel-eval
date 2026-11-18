# Knowledge QA Human Review Sample (50 Validation Items)

**Corpus**: English Wikipedia Foundational Articles (`enwiki-20261101-pages-articles1.xml-p1p41242.bz2`, SHA-256 `e3fd5a837f2a6b3a26c3596d0667600073a86c9fc29dc60ef0b2de605c754387`)  
**Corpus Size**: 6,000 lead article abstracts in `data/wikipedia_abstracts_5k.jsonl` (~5k subset per Decision D2).  
**Partition**: VALIDATION partition only (50 of 300 items).  
**Span Verification**: Every item has an exact character span `[start, end]` where `passage[start:end] == answer`. All items 100% verified.  

---

## VALIDATION Partition Samples (50 items of 300)

| # | ID | Passage Title | Question | Ground Truth Answer | Answer Span | Type | Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `kqa_val_0023` | Clyde Tombaugh | When was Clyde Tombaugh born? | **February 4, 1906** | `[26, 42]` | date | `born_date` |
| 2 | `kqa_val_0006` | Donald Dewar | What was the profession or occupation of Donald Dewar? | **statesman** | `[72, 81]` | occupation | `profession` |
| 3 | `kqa_val_0153` | Greg Egan | What is the profession or occupation of Greg Egan? | **writer** | `[65, 71]` | occupation | `profession` |
| 4 | `kqa_val_0004` | Guangzhou | What territory or country is Guangzhou the capital of? | **Guangdong in southern China** | `[68, 95]` | location | `capital_city` |
| 5 | `kqa_val_0054` | Henry Bordeaux | When was Henry Bordeaux born? | **25 January 1870** | `[18, 33]` | date | `born_date` |
| 6 | `kqa_val_0026` | Ballarat | What was the reported population of Ballarat? | **111,973** | `[118, 125]` | quantity | `population` |
| 7 | `kqa_val_0197` | Gustave de Molinari | When did Gustave de Molinari die? | **28 January 1912** | `[38, 53]` | date | `death_date` |
| 8 | `kqa_val_0012` | Béla Bartók | When did Béla Bartók die? | **26 September 1945** | `[46, 63]` | date | `death_date` |
| 9 | `kqa_val_0091` | Blythe Danner | When was Blythe Danner born? | **February 3, 1943** | `[30, 46]` | date | `born_date` |
| 10 | `kqa_val_0263` | A Fire Upon the Deep | What award or prize did A Fire Upon the Deep receive? | **Hugo Award** | `[284, 294]` | award | `award_won` |
| 11 | `kqa_val_0063` | Ann Arbor, Michigan | What was the reported population of Ann Arbor, Michigan? | **123,851** | `[106, 113]` | quantity | `population` |
| 12 | `kqa_val_0019` | Catalonia | What was the reported population of Catalonia? | **8,124,126** | `[371, 380]` | quantity | `population` |
| 13 | `kqa_val_0136` | Henry Moseley | What award or prize did Henry Moseley receive? | **Nobel Prize** | `[1279, 1290]` | award | `award_won` |
| 14 | `kqa_val_0143` | Gerolamo Cardano | When did Gerolamo Cardano die? | **21 September 1576** | `[70, 87]` | date | `death_date` |
| 15 | `kqa_val_0264` | Arthur Jensen | When was Arthur Jensen born? | **August 24, 1923** | `[22, 37]` | date | `born_date` |
| 16 | `kqa_val_0071` | David Janssen | What was the profession or occupation of David Janssen? | **actor** | `[112, 117]` | occupation | `profession` |
| 17 | `kqa_val_0190` | Bamberg | In which region or country is Bamberg located? | **Upper Franconia** | `[55, 70]` | location | `city_location` |
| 18 | `kqa_val_0172` | G. K. Chesterton | When was G. K. Chesterton born? | **29 May 1874** | `[26, 37]` | date | `born_date` |
| 19 | `kqa_val_0114` | Alfred Russel Wallace | When was Alfred Russel Wallace born? | **8 January 1823** | `[23, 37]` | date | `born_date` |
| 20 | `kqa_val_0138` | Gary Lineker | What is the profession or occupation of Gary Lineker? | **footballer** | `[116, 126]` | occupation | `profession` |
| 21 | `kqa_val_0181` | Elizabeth Barrett Browning | When was Elizabeth Barrett Browning born? | **6 March 1806** | `[49, 61]` | date | `born_date` |
| 22 | `kqa_val_0276` | Charles Lyell | When was Charles Lyell born? | **14 November 1797** | `[32, 48]` | date | `born_date` |
| 23 | `kqa_val_0170` | Edmund Stoiber | What is the profession or occupation of Edmund Stoiber? | **politician** | `[60, 70]` | occupation | `profession` |
| 24 | `kqa_val_0008` | Amos Bronson Alcott | When did Amos Bronson Alcott die? | **March 4, 1888** | `[48, 61]` | date | `death_date` |
| 25 | `kqa_val_0080` | Charles Alston | When did Charles Alston die? | **April 27, 1977** | `[51, 65]` | date | `death_date` |
| 26 | `kqa_val_0032` | Abner Doubleday | When did Abner Doubleday die? | **January 26, 1893** | `[38, 54]` | date | `death_date` |
| 27 | `kqa_val_0099` | Agostino Carracci | When did Agostino Carracci die? | **22 March 1602** | `[57, 70]` | date | `death_date` |
| 28 | `kqa_val_0095` | Ernst Kaltenbrunner | What was the profession or occupation of Ernst Kaltenbrunner? | **lawyer** | `[71, 77]` | occupation | `profession` |
| 29 | `kqa_val_0192` | Alexis Carrel | What award or prize did Alexis Carrel receive? | **Nobel Prize** | `[165, 176]` | award | `award_won` |
| 30 | `kqa_val_0167` | Hannibal Hamlin | When did Hannibal Hamlin die? | **July 4, 1891** | `[35, 47]` | date | `death_date` |
| 31 | `kqa_val_0281` | Archduke Charles, Duke of Teschen | When was Archduke Charles, Duke of Teschen born? | **5 September 1771** | `[75, 91]` | date | `born_date` |
| 32 | `kqa_val_0175` | Robert Bellarmine | When did Robert Bellarmine die? | **17 September 1621** | `[40, 57]` | date | `death_date` |
| 33 | `kqa_val_0171` | Brussels | What territory or country is Brussels the capital of? | **Belgium** | `[159, 166]` | location | `capital_city` |
| 34 | `kqa_val_0223` | Aberdour | What was the reported population of Aberdour? | **1,633** | `[294, 299]` | quantity | `population` |
| 35 | `kqa_val_0296` | City of London | What was the reported population of City of London? | **8,583** | `[806, 811]` | quantity | `population` |
| 36 | `kqa_val_0029` | François d'Aguilon | When did François d'Aguilon die? | **20 March 1617** | `[91, 104]` | date | `death_date` |
| 37 | `kqa_val_0234` | Carl Barks | When did Carl Barks die? | **August 25, 2000** | `[29, 44]` | date | `death_date` |
| 38 | `kqa_val_0203` | İsmet İnönü | When did İsmet İnönü die? | **25 December 1973** | `[41, 57]` | date | `death_date` |
| 39 | `kqa_val_0221` | David Cronenberg | What is the profession or occupation of David Cronenberg? | **director** | `[63, 71]` | occupation | `profession` |
| 40 | `kqa_val_0009` | Berthe Morisot | When was Berthe Morisot born? | **14 January 1841** | `[35, 50]` | date | `born_date` |
| 41 | `kqa_val_0297` | Dardanelles | What was the reported population of Dardanelles? | **110,000** | `[1120, 1127]` | quantity | `population` |
| 42 | `kqa_val_0210` | Cairo | What territory or country is Cairo the capital of? | **Egypt** | `[41, 46]` | location | `capital_city` |
| 43 | `kqa_val_0253` | Bill Haley | When did Bill Haley die? | **February 9, 1981** | `[45, 61]` | date | `death_date` |
| 44 | `kqa_val_0086` | Frank Capra | When was Frank Capra born? | **May 18, 1897** | `[51, 63]` | date | `born_date` |
| 45 | `kqa_val_0067` | Galeazzo Alessi | When was Galeazzo Alessi born? | **1512** | `[17, 21]` | date | `born_date` |
| 46 | `kqa_val_0017` | J. Craig Venter | When did J. Craig Venter die? | **April 29, 2026** | `[38, 52]` | date | `death_date` |
| 47 | `kqa_val_0104` | Cedar Falls, Iowa | In which region or country is Cedar Falls, Iowa located? | **Black Hawk County** | `[25, 42]` | location | `city_location` |
| 48 | `kqa_val_0069` | Émile Baudot | What was the profession or occupation of Émile Baudot? | **engineer** | `[87, 95]` | occupation | `profession` |
| 49 | `kqa_val_0045` | Hannibal Hamlin | When was Hannibal Hamlin born? | **August 27, 1809** | `[17, 32]` | date | `born_date` |
| 50 | `kqa_val_0109` | Borneo | What was the reported population of Borneo? | **23,053,723** | `[88, 98]` | quantity | `population` |

---
