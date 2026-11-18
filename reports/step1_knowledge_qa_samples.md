# Knowledge QA Human Review Sample (50 Items Per Partition)

**Corpus**: English Wikipedia Foundational Articles (`enwiki-20261101-pages-articles1.xml-p1p41242.bz2`, SHA-256 `e3fd5a837f2a6b3a26c3596d0667600073a86c9fc29dc60ef0b2de605c754387`)  
**Corpus Size**: 6,000 lead article abstracts in `data/wikipedia_abstracts_5k.jsonl` (~5k subset per Decision D2).  
**Partitions**: 300 validation items, 300 locked-test items, 300 train items.  
**Span Verification**: Every item has an exact character span `[start, end]` where `passage[start:end] == answer`. All 900 items 100% verified.  

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

## LOCKED_TEST Partition Samples (50 items of 300)

| # | ID | Passage Title | Question | Ground Truth Answer | Answer Span | Type | Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `kqa_lock_0129` | Fred Singer | When was Fred Singer born? | **September 27, 1924** | `[23, 41]` | date | `born_date` |
| 2 | `kqa_lock_0200` | Ed Sullivan | When did Ed Sullivan die? | **October 13, 1974** | `[46, 62]` | date | `death_date` |
| 3 | `kqa_lock_0090` | Gilles Deleuze | When was Gilles Deleuze born? | **18 January 1925** | `[27, 42]` | date | `born_date` |
| 4 | `kqa_lock_0264` | Georg Henrik von Wright | What was the profession or occupation of Georg Henrik von Wright? | **philosopher** | `[70, 81]` | occupation | `profession` |
| 5 | `kqa_lock_0043` | Hezârfen Ahmed Çelebi | When was Hezârfen Ahmed Çelebi born? | **1609** | `[25, 29]` | date | `born_date` |
| 6 | `kqa_lock_0207` | Filippo Tommaso Marinetti | When did Filippo Tommaso Marinetti die? | **2 December 1944** | `[55, 70]` | date | `death_date` |
| 7 | `kqa_lock_0278` | C. S. Lewis | When did C. S. Lewis die? | **22 November 1963** | `[45, 61]` | date | `death_date` |
| 8 | `kqa_lock_0038` | Claude Debussy | When did Claude Debussy die? | **25 March 1918** | `[48, 61]` | date | `death_date` |
| 9 | `kqa_lock_0199` | Emil Theodor Kocher | When did Emil Theodor Kocher die? | **27 July 1917** | `[38, 50]` | date | `death_date` |
| 10 | `kqa_lock_0050` | C. L. Moore | When was C. L. Moore born? | **January 24, 1911** | `[25, 41]` | date | `born_date` |
| 11 | `kqa_lock_0174` | Burhanuddin Rabbani | What was the profession or occupation of Burhanuddin Rabbani? | **politician** | `[74, 84]` | occupation | `profession` |
| 12 | `kqa_lock_0145` | Bill Joy | What is the profession or occupation of Bill Joy? | **engineer** | `[67, 75]` | occupation | `profession` |
| 13 | `kqa_lock_0261` | Daniel Gabriel Fahrenheit | When did Daniel Gabriel Fahrenheit die? | **16 September 1736** | `[45, 62]` | date | `death_date` |
| 14 | `kqa_lock_0056` | Bob Knight | When was Bob Knight born? | **October 25, 1940** | `[26, 42]` | date | `born_date` |
| 15 | `kqa_lock_0243` | Berthe Morisot | When did Berthe Morisot die? | **2 March 1895** | `[58, 70]` | date | `death_date` |
| 16 | `kqa_lock_0018` | Charles Alston | When was Charles Alston born? | **November 28, 1907** | `[31, 48]` | date | `born_date` |
| 17 | `kqa_lock_0081` | Billy Crystal | What is the profession or occupation of Billy Crystal? | **actor** | `[70, 75]` | occupation | `profession` |
| 18 | `kqa_lock_0260` | Hugh Hefner | When did Hugh Hefner die? | **September 27, 2017** | `[37, 55]` | date | `death_date` |
| 19 | `kqa_lock_0219` | Charles Evans Hughes | When did Charles Evans Hughes die? | **August 27, 1948** | `[39, 54]` | date | `death_date` |
| 20 | `kqa_lock_0248` | Elizabeth Garrett Anderson | When was Elizabeth Garrett Anderson born? | **9 June 1836** | `[28, 39]` | date | `born_date` |
| 21 | `kqa_lock_0240` | Dressed to Kill (1980 film) | What award or prize did Dressed to Kill (1980 film) receive? | **Saturn Award** | `[1065, 1077]` | award | `award_won` |
| 22 | `kqa_lock_0171` | Christian Goldbach | When was Christian Goldbach born? | **18 March 1690** | `[25, 38]` | date | `born_date` |
| 23 | `kqa_lock_0101` | George Abbot (author) | What was the profession or occupation of George Abbot (author)? | **writer** | `[67, 73]` | occupation | `profession` |
| 24 | `kqa_lock_0242` | Albert Frederick, Duke of Prussia | When did Albert Frederick, Duke of Prussia die? | **27 August 1618** | `[35, 49]` | date | `death_date` |
| 25 | `kqa_lock_0053` | Languages of Europe | What was the reported population of Languages of Europe? | **744 million** | `[143, 154]` | quantity | `population` |
| 26 | `kqa_lock_0291` | E. E. Smith | What was the profession or occupation of E. E. Smith? | **engineer** | `[72, 80]` | occupation | `profession` |
| 27 | `kqa_lock_0250` | Aaliyah | When did Aaliyah die? | **August 25, 2001** | `[49, 64]` | date | `death_date` |
| 28 | `kqa_lock_0258` | Bram Stoker | What was the profession or occupation of Bram Stoker? | **writer** | `[62, 68]` | occupation | `profession` |
| 29 | `kqa_lock_0158` | Drew Barrymore | When was Drew Barrymore born? | **February 22, 1975** | `[27, 44]` | date | `born_date` |
| 30 | `kqa_lock_0157` | Diego Maradona | When was Diego Maradona born? | **30 October 1960** | `[24, 39]` | date | `born_date` |
| 31 | `kqa_lock_0028` | Brion Gysin | When did Brion Gysin die? | **13 July 1986** | `[33, 45]` | date | `death_date` |
| 32 | `kqa_lock_0102` | Bert Bell | When was Bert Bell born? | **February 25, 1895** | `[27, 44]` | date | `born_date` |
| 33 | `kqa_lock_0177` | Christine Lavin | When was Christine Lavin born? | **January 2, 1952** | `[22, 37]` | date | `born_date` |
| 34 | `kqa_lock_0293` | Huldrych Zwingli | What was the profession or occupation of Huldrych Zwingli? | **theologian** | `[100, 110]` | occupation | `profession` |
| 35 | `kqa_lock_0077` | Camilla Hall | When was Camilla Hall born? | **March 24, 1945** | `[24, 38]` | date | `born_date` |
| 36 | `kqa_lock_0224` | Antonio Vivaldi | When was Antonio Vivaldi born? | **4 March 1678** | `[23, 35]` | date | `born_date` |
| 37 | `kqa_lock_0217` | Graham Chapman | What was the profession or occupation of Graham Chapman? | **actor** | `[63, 68]` | occupation | `profession` |
| 38 | `kqa_lock_0111` | Charles Baudelaire | What was the profession or occupation of Charles Baudelaire? | **poet** | `[77, 81]` | occupation | `profession` |
| 39 | `kqa_lock_0103` | Edward Jenner | When was Edward Jenner born? | **17 May 1749** | `[15, 26]` | date | `born_date` |
| 40 | `kqa_lock_0194` | Hannibal Hamlin | What was the profession or occupation of Hannibal Hamlin? | **politician** | `[65, 75]` | occupation | `profession` |
| 41 | `kqa_lock_0292` | Hunter S. Thompson | When did Hunter S. Thompson die? | **February 20, 2005** | `[47, 64]` | date | `death_date` |
| 42 | `kqa_lock_0161` | Agostino Carracci | What was the profession or occupation of Agostino Carracci? | **painter** | `[87, 94]` | occupation | `profession` |
| 43 | `kqa_lock_0039` | Georg Henrik von Wright | When did Georg Henrik von Wright die? | **16 June 2003** | `[42, 54]` | date | `death_date` |
| 44 | `kqa_lock_0118` | Fort William, Scotland | What was the reported population of Fort William, Scotland? | **15,757** | `[162, 168]` | quantity | `population` |
| 45 | `kqa_lock_0154` | Crete | What was the reported population of Crete? | **624,408** | `[983, 990]` | quantity | `population` |
| 46 | `kqa_lock_0112` | Bobby Charlton | What was the profession or occupation of Bobby Charlton? | **footballer** | `[71, 81]` | occupation | `profession` |
| 47 | `kqa_lock_0114` | Dr. Seuss | When was Dr. Seuss born? | **March 2, 1904** | `[25, 38]` | date | `born_date` |
| 48 | `kqa_lock_0148` | Albert Camus | What was the profession or occupation of Albert Camus? | **philosopher** | `[71, 82]` | occupation | `profession` |
| 49 | `kqa_lock_0012` | William M. Tweed | When was William M. Tweed born? | **April 3, 1823** | `[29, 42]` | date | `born_date` |
| 50 | `kqa_lock_0216` | The Bronx | What was the reported population of The Bronx? | **1,472,654** | `[122, 131]` | quantity | `population` |

---

## TRAIN Partition Samples (50 items of 300)

| # | ID | Passage Title | Question | Ground Truth Answer | Answer Span | Type | Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `kqa_train_0209` | Alexis Carrel | When was Alexis Carrel born? | **28 June 1873** | `[17, 29]` | date | `born_date` |
| 2 | `kqa_train_0202` | Bob Costas | When was Bob Costas born? | **March 22, 1952** | `[28, 42]` | date | `born_date` |
| 3 | `kqa_train_0245` | Austin, Texas | What was the reported population of Austin, Texas? | **961,855** | `[80, 87]` | quantity | `population` |
| 4 | `kqa_train_0134` | Hatfield, Hertfordshire | What was the reported population of Hatfield, Hertfordshire? | **29,616** | `[121, 127]` | quantity | `population` |
| 5 | `kqa_train_0218` | Charles Lyell | What was the profession or occupation of Charles Lyell? | **geologist** | `[89, 98]` | occupation | `profession` |
| 6 | `kqa_train_0018` | E. T. A. Hoffmann | What was the profession or occupation of E. T. A. Hoffmann? | **composer** | `[170, 178]` | occupation | `profession` |
| 7 | `kqa_train_0195` | Emperor Sukō | When did Emperor Sukō die? | **31 January 1398** | `[15, 30]` | date | `death_date` |
| 8 | `kqa_train_0294` | Dartmouth, Devon | What was the reported population of Dartmouth, Devon? | **5,512** | `[341, 346]` | quantity | `population` |
| 9 | `kqa_train_0008` | Cornish Nationalist Party | In what year was Cornish Nationalist Party founded or established? | **1975** | `[71, 75]` | year | `founded_year` |
| 10 | `kqa_train_0149` | Andrew Jackson | When was Andrew Jackson born? | **March 15, 1767** | `[16, 30]` | date | `born_date` |
| 11 | `kqa_train_0022` | Harrison Schmitt | When was Harrison Schmitt born? | **July 3, 1935** | `[36, 48]` | date | `born_date` |
| 12 | `kqa_train_0085` | Gustave de Molinari | What was the profession or occupation of Gustave de Molinari? | **economist** | `[79, 88]` | occupation | `profession` |
| 13 | `kqa_train_0013` | Andy Warhol | When was Andy Warhol born? | **August 6, 1928** | `[40, 54]` | date | `born_date` |
| 14 | `kqa_train_0159` | Carl Rogers | When did Carl Rogers die? | **February 4, 1987** | `[38, 54]` | date | `death_date` |
| 15 | `kqa_train_0181` | Andrew Jackson | When did Andrew Jackson die? | **June 8, 1845** | `[33, 45]` | date | `death_date` |
| 16 | `kqa_train_0240` | Gilles Deleuze | What was the profession or occupation of Gilles Deleuze? | **philosopher** | `[80, 91]` | occupation | `profession` |
| 17 | `kqa_train_0295` | Frédéric Bastiat | What was the profession or occupation of Frédéric Bastiat? | **economist** | `[75, 84]` | occupation | `profession` |
| 18 | `kqa_train_0067` | George Orwell | When did George Orwell die? | **21 January 1950** | `[34, 49]` | date | `death_date` |
| 19 | `kqa_train_0028` | Gerard Manley Hopkins | When did Gerard Manley Hopkins die? | **8 June 1889** | `[38, 49]` | date | `death_date` |
| 20 | `kqa_train_0135` | Britney Spears | When was Britney Spears born? | **December 2, 1981** | `[26, 42]` | date | `born_date` |
| 21 | `kqa_train_0139` | Frederick I of Brandenburg-Ansbach | When did Frederick I of Brandenburg-Ansbach die? | **4 April 1536** | `[82, 94]` | date | `death_date` |
| 22 | `kqa_train_0114` | Dylan Thomas | When was Dylan Thomas born? | **27 October 1914** | `[22, 37]` | date | `born_date` |
| 23 | `kqa_train_0014` | Baku | What territory or country is Baku the capital of? | **Azerbaijan** | `[47, 57]` | location | `capital_city` |
| 24 | `kqa_train_0221` | Interior Alaska | What was the reported population of Interior Alaska? | **113,154** | `[613, 620]` | quantity | `population` |
| 25 | `kqa_train_0035` | Bernie Federko | When was Bernie Federko born? | **May 12, 1956** | `[28, 40]` | date | `born_date` |
| 26 | `kqa_train_0125` | Hartmann Schedel | When did Hartmann Schedel die? | **28 November 1514** | `[80, 96]` | date | `death_date` |
| 27 | `kqa_train_0273` | Eindhoven | What was the reported population of Eindhoven? | **249,054** | `[216, 223]` | quantity | `population` |
| 28 | `kqa_train_0138` | Fay Wray | When did Fay Wray die? | **August 8, 2004** | `[36, 50]` | date | `death_date` |
| 29 | `kqa_train_0183` | Gerard Manley Hopkins | What was the profession or occupation of Gerard Manley Hopkins? | **poet** | `[66, 70]` | occupation | `profession` |
| 30 | `kqa_train_0160` | Hermann Hesse | When was Hermann Hesse born? | **2 July 1877** | `[22, 33]` | date | `born_date` |
| 31 | `kqa_train_0003` | Jean Siméon Chardin | What was the profession or occupation of Jean Siméon Chardin? | **painter** | `[92, 99]` | occupation | `profession` |
| 32 | `kqa_train_0296` | Anton Drexler | When did Anton Drexler die? | **24 February 1942** | `[30, 46]` | date | `death_date` |
| 33 | `kqa_train_0102` | Buckminster Fuller | What award or prize did Buckminster Fuller receive? | **Gold Medal** | `[1339, 1349]` | award | `award_won` |
| 34 | `kqa_train_0036` | Edmund Stoiber | When was Edmund Stoiber born? | **28 September 1941** | `[29, 46]` | date | `born_date` |
| 35 | `kqa_train_0100` | Alfred Russel Wallace | When did Alfred Russel Wallace die? | **7 November 1913** | `[40, 55]` | date | `death_date` |
| 36 | `kqa_train_0048` | Harold Kushner | When did Harold Kushner die? | **April 28, 2023** | `[39, 53]` | date | `death_date` |
| 37 | `kqa_train_0045` | Florence | What was the reported population of Florence? | **361,625** | `[122, 129]` | quantity | `population` |
| 38 | `kqa_train_0021` | Gary North (economist) | When did Gary North (economist) die? | **February 24, 2022** | `[40, 57]` | date | `death_date` |
| 39 | `kqa_train_0019` | Aberdare | What was the reported population of Aberdare? | **39,550** | `[159, 165]` | quantity | `population` |
| 40 | `kqa_train_0197` | A. E. Housman | When was A. E. Housman born? | **26 March 1859** | `[25, 38]` | date | `born_date` |
| 41 | `kqa_train_0089` | Catherine Coleman | What is the profession or occupation of Catherine Coleman? | **chemist** | `[71, 78]` | occupation | `profession` |
| 42 | `kqa_train_0269` | François Truffaut | When was François Truffaut born? | **6 February 1932** | `[33, 48]` | date | `born_date` |
| 43 | `kqa_train_0121` | Elie Wiesel | What was the profession or occupation of Elie Wiesel? | **writer** | `[87, 93]` | occupation | `profession` |
| 44 | `kqa_train_0174` | Gustav Radbruch | What was the profession or occupation of Gustav Radbruch? | **politician** | `[87, 97]` | occupation | `profession` |
| 45 | `kqa_train_0175` | Dalton Trumbo | When was Dalton Trumbo born? | **December 9, 1905** | `[21, 37]` | date | `born_date` |
| 46 | `kqa_train_0145` | Harry Secombe | What was the profession or occupation of Harry Secombe? | **actor** | `[74, 79]` | occupation | `profession` |
| 47 | `kqa_train_0299` | Ernst Haeckel | When was Ernst Haeckel born? | **16 February 1834** | `[43, 59]` | date | `born_date` |
| 48 | `kqa_train_0099` | Bob Hawke | When did Bob Hawke die? | **16 May 2019** | `[47, 58]` | date | `death_date` |
| 49 | `kqa_train_0046` | Engelbert Dollfuss | What was the profession or occupation of Engelbert Dollfuss? | **politician** | `[90, 100]` | occupation | `profession` |
| 50 | `kqa_train_0051` | Antonio Canova | When did Antonio Canova die? | **13 October 1822** | `[36, 51]` | date | `death_date` |

---
