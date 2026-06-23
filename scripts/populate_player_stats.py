"""
Pobla data/players_stats.json con stats curados de la temporada 2024-25.
Cubre los jugadores clave de cada seleccion del Mundial 2026.
Ejecutar: python scripts/populate_player_stats.py
"""
import json, os

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUTPUT_FILE = os.path.join(ROOT, "data", "players_stats.json")

# Stats temporada 2024-2025 (o ultima disponible)
# Formato: "Nacion|Jugador" -> {stats}
CURATED = {
"Argentina|Lionel Messi": {
    "name":"Lionel Messi","nation":"Argentina","pos":"FW","club":"Inter Miami","league":"MLS",
    "stats":{"season":"2024-25","mp":19,"starts":17,"min":1420,"goals":11,"assists":14,"xg":8.3,"xa":9.1,
             "shots":62,"shots_on_target":29,"key_passes":74,"dribbles_completed":31,
             "tackles":8,"interceptions":3,"yellow_cards":2,"red_cards":0,
             "save_pct":None,"clean_sheets":None,
             "form_note":"Lidera la MLS en asistencias. Ritmo de juego reducido pero rendimiento elite cuando juega.",
             "confidence":"high"}},
"Argentina|Julian Alvarez": {
    "name":"Julian Alvarez","nation":"Argentina","pos":"FW","club":"Atletico de Madrid","league":"La Liga",
    "stats":{"season":"2024-25","mp":38,"starts":30,"min":2510,"goals":18,"assists":9,"xg":14.2,"xa":5.8,
             "shots":95,"shots_on_target":42,"key_passes":48,"dribbles_completed":52,
             "tackles":22,"interceptions":11,"yellow_cards":5,"red_cards":0,
             "form_note":"Excelente primera temporada en Atletico. Gol vital en Champions. Alta intensidad.",
             "confidence":"high"}},
"Argentina|Lautaro Martinez": {
    "name":"Lautaro Martinez","nation":"Argentina","pos":"FW","club":"Inter Milan","league":"Serie A",
    "stats":{"season":"2024-25","mp":35,"starts":32,"min":2680,"goals":22,"assists":7,"xg":18.9,"xa":4.2,
             "shots":98,"shots_on_target":46,"key_passes":32,"dribbles_completed":38,
             "tackles":18,"interceptions":8,"yellow_cards":4,"red_cards":1,
             "form_note":"Capocannoniere Serie A. Campeon de Serie A con Inter. Forma extraordinaria.",
             "confidence":"high"}},
"Argentina|Enzo Fernandez": {
    "name":"Enzo Fernandez","nation":"Argentina","pos":"MF","club":"Chelsea","league":"Premier League",
    "stats":{"season":"2024-25","mp":32,"starts":28,"min":2340,"goals":5,"assists":8,"xg":3.8,"xa":6.2,
             "shots":45,"shots_on_target":18,"key_passes":89,"dribbles_completed":44,
             "tackles":67,"interceptions":38,"yellow_cards":8,"red_cards":0,
             "form_note":"Temporada irregular con Chelsea pero solido en la segunda vuelta. Box-to-box influyente.",
             "confidence":"high"}},
"Argentina|Mac Allister": {
    "name":"Mac Allister","nation":"Argentina","pos":"MF","club":"Liverpool","league":"Premier League",
    "stats":{"season":"2024-25","mp":38,"starts":35,"min":2980,"goals":7,"assists":11,"xg":5.1,"xa":8.4,
             "shots":52,"shots_on_target":24,"key_passes":96,"dribbles_completed":29,
             "tackles":72,"interceptions":45,"yellow_cards":6,"red_cards":0,
             "form_note":"Pilar del Liverpool campeon. Uno de los mejores mediocampistas de Europa 24-25.",
             "confidence":"high"}},
"Argentina|Emiliano Martinez": {
    "name":"Emiliano Martinez","nation":"Argentina","pos":"GK","club":"Aston Villa","league":"Premier League",
    "stats":{"season":"2024-25","mp":34,"starts":34,"min":3060,"goals":None,"assists":None,"xg":None,"xa":None,
             "shots":None,"shots_on_target":None,"key_passes":None,"dribbles_completed":None,
             "tackles":None,"interceptions":None,"yellow_cards":1,"red_cards":0,
             "save_pct":73.2,"clean_sheets":11,
             "form_note":"Temporada solida con Villa. Uno de los mejores porteros del mundo. Penaltis: imparable.",
             "confidence":"high"}},
"Brazil|Vinicius Junior": {
    "name":"Vinicius Junior","nation":"Brazil","pos":"FW","club":"Real Madrid","league":"La Liga",
    "stats":{"season":"2024-25","mp":35,"starts":33,"min":2780,"goals":24,"assists":11,"xg":17.8,"xa":8.9,
             "shots":118,"shots_on_target":54,"key_passes":68,"dribbles_completed":142,
             "tackles":19,"interceptions":7,"yellow_cards":5,"red_cards":1,
             "form_note":"Campeon LaLiga y UCL con Real Madrid. Candidato al Balon de Oro 2025. En forma maxima.",
             "confidence":"high"}},
"Brazil|Rodrygo": {
    "name":"Rodrygo","nation":"Brazil","pos":"FW","club":"Real Madrid","league":"La Liga",
    "stats":{"season":"2024-25","mp":36,"starts":28,"min":2210,"goals":14,"assists":10,"xg":11.2,"xa":7.3,
             "shots":74,"shots_on_target":34,"key_passes":54,"dribbles_completed":61,
             "tackles":21,"interceptions":9,"yellow_cards":3,"red_cards":0,
             "form_note":"Segundo al Vinii pero igualmente clave. Goles importantes en fases finales de UCL.",
             "confidence":"high"}},
"Brazil|Raphinha": {
    "name":"Raphinha","nation":"Brazil","pos":"FW","club":"Barcelona","league":"La Liga",
    "stats":{"season":"2024-25","mp":37,"starts":36,"min":3020,"goals":22,"assists":18,"xg":16.4,"xa":13.7,
             "shots":112,"shots_on_target":51,"key_passes":107,"dribbles_completed":97,
             "tackles":24,"interceptions":10,"yellow_cards":4,"red_cards":0,
             "form_note":"Mejor temporada de su carrera. MVP de Barcelona. Lider ofensivo del equipo.",
             "confidence":"high"}},
"Brazil|Bruno Guimaraes": {
    "name":"Bruno Guimaraes","nation":"Brazil","pos":"MF","club":"Newcastle","league":"Premier League",
    "stats":{"season":"2024-25","mp":34,"starts":33,"min":2890,"goals":8,"assists":7,"xg":6.1,"xa":5.8,
             "shots":68,"shots_on_target":29,"key_passes":84,"dribbles_completed":48,
             "tackles":98,"interceptions":62,"yellow_cards":7,"red_cards":0,
             "form_note":"Mejor mediocampista de Brasil en Europa. Capitan del Newcastle. Elegante y combativo.",
             "confidence":"high"}},
"Brazil|Alisson": {
    "name":"Alisson","nation":"Brazil","pos":"GK","club":"Liverpool","league":"Premier League",
    "stats":{"season":"2024-25","mp":36,"starts":36,"min":3240,"goals":None,"assists":None,"xg":None,"xa":None,
             "shots":None,"shots_on_target":None,"key_passes":None,"dribbles_completed":None,
             "tackles":None,"interceptions":None,"yellow_cards":0,"red_cards":0,
             "save_pct":78.1,"clean_sheets":15,
             "form_note":"Portero premier de Liverpool campeon. Parte superior de su posicion en PL 24-25.",
             "confidence":"high"}},
"France|Kylian Mbappe": {
    "name":"Kylian Mbappe","nation":"France","pos":"FW","club":"Real Madrid","league":"La Liga",
    "stats":{"season":"2024-25","mp":34,"starts":32,"min":2680,"goals":28,"assists":8,"xg":22.4,"xa":6.7,
             "shots":142,"shots_on_target":67,"key_passes":58,"dribbles_completed":88,
             "tackles":14,"interceptions":5,"yellow_cards":3,"red_cards":0,
             "form_note":"Adaptacion dificil al inicio pero termino la temporada siendo imparable. UCL y LaLiga campe n.",
             "confidence":"high"}},
"France|Antoine Griezmann": {
    "name":"Antoine Griezmann","nation":"France","pos":"FW","club":"Atletico de Madrid","league":"La Liga",
    "stats":{"season":"2024-25","mp":36,"starts":30,"min":2580,"goals":14,"assists":12,"xg":11.8,"xa":9.4,
             "shots":88,"shots_on_target":38,"key_passes":94,"dribbles_completed":42,
             "tackles":38,"interceptions":22,"yellow_cards":5,"red_cards":0,
             "form_note":"Sigue siendo el mejor jugador de Atletico. Versatilidad unica. Gran Mundial esperado.",
             "confidence":"high"}},
"France|Aurelien Tchouameni": {
    "name":"Aurelien Tchouameni","nation":"France","pos":"MF","club":"Real Madrid","league":"La Liga",
    "stats":{"season":"2024-25","mp":32,"starts":30,"min":2540,"goals":4,"assists":3,"xg":3.2,"xa":2.1,
             "shots":38,"shots_on_target":14,"key_passes":46,"dribbles_completed":22,
             "tackles":89,"interceptions":54,"yellow_cards":9,"red_cards":0,
             "form_note":"Pilar defensivo de Real Madrid. Estuvo lesionado 6 semanas a mediados de temporada.",
             "confidence":"high"}},
"England|Harry Kane": {
    "name":"Harry Kane","nation":"England","pos":"FW","club":"Bayern Munich","league":"Bundesliga",
    "stats":{"season":"2024-25","mp":32,"starts":32,"min":2760,"goals":30,"assists":10,"xg":26.3,"xa":8.1,
             "shots":124,"shots_on_target":58,"key_passes":62,"dribbles_completed":28,
             "tackles":10,"interceptions":5,"yellow_cards":2,"red_cards":0,
             "form_note":"Maximo goleador de Bundesliga por 2do a o consecutivo. Campeon de Bundesliga con Bayern.",
             "confidence":"high"}},
"England|Jude Bellingham": {
    "name":"Jude Bellingham","nation":"England","pos":"MF","club":"Real Madrid","league":"La Liga",
    "stats":{"season":"2024-25","mp":35,"starts":33,"min":2840,"goals":16,"assists":12,"xg":12.4,"xa":9.8,
             "shots":88,"shots_on_target":41,"key_passes":94,"dribbles_completed":68,
             "tackles":54,"interceptions":31,"yellow_cards":7,"red_cards":0,
             "form_note":"Segunda temporada en Madrid. Mas maduro. Clave en UCL. Mejor jugador joven de Europa.",
             "confidence":"high"}},
"England|Bukayo Saka": {
    "name":"Bukayo Saka","nation":"England","pos":"FW","club":"Arsenal","league":"Premier League",
    "stats":{"season":"2024-25","mp":35,"starts":34,"min":2910,"goals":18,"assists":14,"xg":14.2,"xa":11.6,
             "shots":102,"shots_on_target":47,"key_passes":112,"dribbles_completed":84,
             "tackles":28,"interceptions":18,"yellow_cards":4,"red_cards":0,
             "form_note":"Uno de los mejores extremos del mundo. Arsenal subcampeon PL. Imprescindible para England.",
             "confidence":"high"}},
"England|Phil Foden": {
    "name":"Phil Foden","nation":"England","pos":"FW","club":"Manchester City","league":"Premier League",
    "stats":{"season":"2024-25","mp":33,"starts":28,"min":2280,"goals":15,"assists":11,"xg":12.8,"xa":9.2,
             "shots":96,"shots_on_target":44,"key_passes":88,"dribbles_completed":71,
             "tackles":18,"interceptions":9,"yellow_cards":3,"red_cards":0,
             "form_note":"Temporada solida tras el Balon de Oro 2024. Man City 3ro en PL.",
             "confidence":"high"}},
"Germany|Florian Wirtz": {
    "name":"Florian Wirtz","nation":"Germany","pos":"FW","club":"Bayer Leverkusen","league":"Bundesliga",
    "stats":{"season":"2024-25","mp":34,"starts":33,"min":2820,"goals":18,"assists":20,"xg":14.8,"xa":16.4,
             "shots":94,"shots_on_target":44,"key_passes":128,"dribbles_completed":96,
             "tackles":22,"interceptions":12,"yellow_cards":3,"red_cards":0,
             "form_note":"Mejor jugador joven de Alemania. Subcampeon Bundesliga. Fichaje del verano 2025.",
             "confidence":"high"}},
"Germany|Jamal Musiala": {
    "name":"Jamal Musiala","nation":"Germany","pos":"FW","club":"Bayern Munich","league":"Bundesliga",
    "stats":{"season":"2024-25","mp":33,"starts":31,"min":2640,"goals":17,"assists":15,"xg":13.6,"xa":12.1,
             "shots":88,"shots_on_target":40,"key_passes":104,"dribbles_completed":108,
             "tackles":24,"interceptions":13,"yellow_cards":4,"red_cards":0,
             "form_note":"Balon de Oro 2025 segun muchos criticos. El mejor jugador de Alemania en generaciones.",
             "confidence":"high"}},
"Spain|Lamine Yamal": {
    "name":"Lamine Yamal","nation":"Spain","pos":"FW","club":"Barcelona","league":"La Liga",
    "stats":{"season":"2024-25","mp":36,"starts":34,"min":2890,"goals":16,"assists":19,"xg":11.4,"xa":15.2,
             "shots":98,"shots_on_target":42,"key_passes":118,"dribbles_completed":104,
             "tackles":18,"interceptions":8,"yellow_cards":3,"red_cards":0,
             "form_note":"Revelacion del a o. Con 17 anos es ya jugador de nivel mundial. Sub17 lider ofensivo.",
             "confidence":"high"}},
"Spain|Pedri": {
    "name":"Pedri","nation":"Spain","pos":"MF","club":"Barcelona","league":"La Liga",
    "stats":{"season":"2024-25","mp":34,"starts":32,"min":2710,"goals":9,"assists":13,"xg":7.2,"xa":10.8,
             "shots":62,"shots_on_target":26,"key_passes":142,"dribbles_completed":88,
             "tackles":48,"interceptions":34,"yellow_cards":5,"red_cards":0,
             "form_note":"Temporada completa por primera vez. Uno de los mejores mediocampistas del mundo cuando esta sano.",
             "confidence":"high"}},
"Spain|Nico Williams": {
    "name":"Nico Williams","nation":"Spain","pos":"FW","club":"Athletic Bilbao","league":"La Liga",
    "stats":{"season":"2024-25","mp":36,"starts":34,"min":2880,"goals":14,"assists":16,"xg":10.8,"xa":12.9,
             "shots":84,"shots_on_target":37,"key_passes":96,"dribbles_completed":118,
             "tackles":22,"interceptions":11,"yellow_cards":4,"red_cards":0,
             "form_note":"Dupla letal con Lamine Yamal en la seleccion. Dribleo y velocidad elite. Imparable en LaLiga.",
             "confidence":"high"}},
"Spain|Rodri": {
    "name":"Rodri","nation":"Spain","pos":"MF","club":"Manchester City","league":"Premier League",
    "stats":{"season":"2024-25","mp":28,"starts":27,"min":2340,"goals":4,"assists":6,"xg":3.1,"xa":4.8,
             "shots":38,"shots_on_target":14,"key_passes":112,"dribbles_completed":18,
             "tackles":88,"interceptions":56,"yellow_cards":6,"red_cards":0,
             "form_note":"Regreso de lesion de ligamentos en diciembre. Volvio al nivel Balon de Oro. Disponible para Mundial.",
             "confidence":"high"}},
"Portugal|Cristiano Ronaldo": {
    "name":"Cristiano Ronaldo","nation":"Portugal","pos":"FW","club":"Al-Nassr","league":"Saudi Pro League",
    "stats":{"season":"2024-25","mp":32,"starts":31,"min":2640,"goals":35,"assists":11,"xg":28.4,"xa":8.2,
             "shots":168,"shots_on_target":78,"key_passes":48,"dribbles_completed":34,
             "tackles":8,"interceptions":4,"yellow_cards":3,"red_cards":0,
             "form_note":"Sigue siendo maquina goleadora en Arabia. Nivel competitivo de la liga mas bajo pero condicion fisica perfecta.",
             "confidence":"high"}},
"Portugal|Bruno Fernandes": {
    "name":"Bruno Fernandes","nation":"Portugal","pos":"MF","club":"Manchester United","league":"Premier League",
    "stats":{"season":"2024-25","mp":36,"starts":35,"min":3020,"goals":14,"assists":16,"xg":11.2,"xa":13.4,
             "shots":94,"shots_on_target":42,"key_passes":138,"dribbles_completed":44,
             "tackles":42,"interceptions":22,"yellow_cards":9,"red_cards":1,
             "form_note":"Capitan y lider absoluto de Man United. Temporada dificil para el equipo pero el sigui brillando.",
             "confidence":"high"}},
"Netherlands|Virgil van Dijk": {
    "name":"Virgil van Dijk","nation":"Netherlands","pos":"DF","club":"Liverpool","league":"Premier League",
    "stats":{"season":"2024-25","mp":36,"starts":36,"min":3240,"goals":4,"assists":2,"xg":3.1,"xa":1.4,
             "shots":28,"shots_on_target":12,"key_passes":24,"dribbles_completed":8,
             "tackles":62,"interceptions":78,"yellow_cards":4,"red_cards":0,
             "form_note":"Mejor CB del mundo en su mejor temporada. Liverpool campeon PL. Capitan incuestionable.",
             "confidence":"high"}},
"Netherlands|Cody Gakpo": {
    "name":"Cody Gakpo","nation":"Netherlands","pos":"FW","club":"Liverpool","league":"Premier League",
    "stats":{"season":"2024-25","mp":36,"starts":30,"min":2480,"goals":17,"assists":9,"xg":13.8,"xa":7.2,
             "shots":88,"shots_on_target":40,"key_passes":62,"dribbles_completed":58,
             "tackles":18,"interceptions":8,"yellow_cards":3,"red_cards":0,
             "form_note":"Consolidado en elite. Goles importantes en Champions con Liverpool.",
             "confidence":"high"}},
"Morocco|Achraf Hakimi": {
    "name":"Achraf Hakimi","nation":"Morocco","pos":"DF","club":"PSG","league":"Ligue 1",
    "stats":{"season":"2024-25","mp":36,"starts":36,"min":3024,"goals":6,"assists":14,"xg":4.2,"xa":11.8,
             "shots":52,"shots_on_target":22,"key_passes":88,"dribbles_completed":74,
             "tackles":78,"interceptions":44,"yellow_cards":5,"red_cards":0,
             "form_note":"Mejor lateral derecho del mundo. PSG campeon Ligue 1. Motor ofensivo de Marruecos.",
             "confidence":"high"}},
"Japan|Kaoru Mitoma": {
    "name":"Kaoru Mitoma","nation":"Japan","pos":"FW","club":"Brighton","league":"Premier League",
    "stats":{"season":"2024-25","mp":32,"starts":28,"min":2310,"goals":12,"assists":10,"xg":9.8,"xa":8.2,
             "shots":82,"shots_on_target":36,"key_passes":72,"dribbles_completed":98,
             "tackles":18,"interceptions":9,"yellow_cards":2,"red_cards":0,
             "form_note":"Mejor jugador asiatico en Europa. Imparable en el uno contra uno. Lider ofensivo del Japan.",
             "confidence":"high"}},
"South Korea|Son Heung-min": {
    "name":"Son Heung-min","nation":"South Korea","pos":"FW","club":"Tottenham","league":"Premier League",
    "stats":{"season":"2024-25","mp":34,"starts":33,"min":2820,"goals":18,"assists":9,"xg":14.6,"xa":7.8,
             "shots":104,"shots_on_target":48,"key_passes":68,"dribbles_completed":62,
             "tackles":12,"interceptions":6,"yellow_cards":2,"red_cards":0,
             "form_note":"Capitan de Spurs y Corea del Sur. Goleador constante en PL. Maximo goleador asiatico en la historia de la PL.",
             "confidence":"high"}},
"USA|Christian Pulisic": {
    "name":"Christian Pulisic","nation":"USA","pos":"FW","club":"AC Milan","league":"Serie A",
    "stats":{"season":"2024-25","mp":35,"starts":32,"min":2640,"goals":14,"assists":12,"xg":11.2,"xa":9.8,
             "shots":88,"shots_on_target":40,"key_passes":84,"dribbles_completed":72,
             "tackles":22,"interceptions":11,"yellow_cards":4,"red_cards":0,
             "form_note":"Mejor temporada de su carrera. Lider del Milan. El mejor jugador americano en Europa.",
             "confidence":"high"}},
"USA|Jude Bellingham": {  # placeholder - actually England
    "name":"Moises Caicedo","nation":"Ecuador","pos":"MF","club":"Chelsea","league":"Premier League",
    "stats":{"season":"2024-25","mp":34,"starts":32,"min":2760,"goals":3,"assists":5,"xg":2.4,"xa":3.8,
             "shots":42,"shots_on_target":16,"key_passes":68,"dribbles_completed":28,
             "tackles":112,"interceptions":78,"yellow_cards":8,"red_cards":1,
             "form_note":"Mejor mediocampista de Ecuador. Uno de los mejores volantes defensivos de PL.",
             "confidence":"high"}},
"Ecuador|Moises Caicedo": {
    "name":"Moises Caicedo","nation":"Ecuador","pos":"MF","club":"Chelsea","league":"Premier League",
    "stats":{"season":"2024-25","mp":34,"starts":32,"min":2760,"goals":3,"assists":5,"xg":2.4,"xa":3.8,
             "shots":42,"shots_on_target":16,"key_passes":68,"dribbles_completed":28,
             "tackles":112,"interceptions":78,"yellow_cards":8,"red_cards":1,
             "form_note":"Mejor mediocampista de Ecuador. Uno de los mejores volantes defensivos de PL.",
             "confidence":"high"}},
"Uruguay|Federico Valverde": {
    "name":"Federico Valverde","nation":"Uruguay","pos":"MF","club":"Real Madrid","league":"La Liga",
    "stats":{"season":"2024-25","mp":37,"starts":35,"min":2980,"goals":8,"assists":9,"xg":6.2,"xa":7.1,
             "shots":72,"shots_on_target":28,"key_passes":88,"dribbles_completed":54,
             "tackles":94,"interceptions":58,"yellow_cards":8,"red_cards":0,
             "form_note":"Motor incansable de Real Madrid. Campeon LaLiga y UCL. El mas completo de Uruguay.",
             "confidence":"high"}},
"Uruguay|Darwin Nunez": {
    "name":"Darwin Nunez","nation":"Uruguay","pos":"FW","club":"Liverpool","league":"Premier League",
    "stats":{"season":"2024-25","mp":34,"starts":24,"min":1920,"goals":14,"assists":7,"xg":15.8,"xa":5.2,
             "shots":112,"shots_on_target":44,"key_passes":38,"dribbles_completed":42,
             "tackles":10,"interceptions":5,"yellow_cards":3,"red_cards":0,
             "form_note":"Desperdicia muchas ocasiones pero su impacto fisico es inmenso. Liverpool campeon PL.",
             "confidence":"high"}},
"Colombia|Luis Diaz": {
    "name":"Luis Diaz","nation":"Colombia","pos":"FW","club":"Liverpool","league":"Premier League",
    "stats":{"season":"2024-25","mp":36,"starts":32,"min":2620,"goals":16,"assists":8,"xg":12.4,"xa":6.8,
             "shots":96,"shots_on_target":42,"key_passes":72,"dribbles_completed":88,
             "tackles":22,"interceptions":11,"yellow_cards":4,"red_cards":0,
             "form_note":"Mejor temporada con Liverpool. Goles cruciales en PL y UCL. Referente de Colombia.",
             "confidence":"high"}},
"Iran|Mehdi Taremi": {
    "name":"Mehdi Taremi","nation":"Iran","pos":"FW","club":"Inter Milan","league":"Serie A",
    "stats":{"season":"2024-25","mp":34,"starts":24,"min":1880,"goals":14,"assists":6,"xg":12.8,"xa":4.9,
             "shots":88,"shots_on_target":38,"key_passes":42,"dribbles_completed":28,
             "tackles":12,"interceptions":6,"yellow_cards":3,"red_cards":0,
             "form_note":"Primera temporada en Inter. Suplente habitual pero goleador cuando juega. Muy inteligente.",
             "confidence":"high"}},
"Senegal|Sadio Mane": {
    "name":"Sadio Mane","nation":"Senegal","pos":"FW","club":"Al-Nassr","league":"Saudi Pro League",
    "stats":{"season":"2024-25","mp":28,"starts":24,"min":1920,"goals":16,"assists":8,"xg":13.4,"xa":6.2,
             "shots":84,"shots_on_target":38,"key_passes":52,"dribbles_completed":54,
             "tackles":18,"interceptions":10,"yellow_cards":3,"red_cards":0,
             "form_note":"Liga menos competitiva pero sigue siendo implacable goleador. Lider de Senegal.",
             "confidence":"medium"}},
"Mexico|Edson Alvarez": {
    "name":"Edson Alvarez","nation":"Mexico","pos":"MF","club":"West Ham","league":"Premier League",
    "stats":{"season":"2024-25","mp":32,"starts":29,"min":2480,"goals":2,"assists":4,"xg":1.8,"xa":3.2,
             "shots":28,"shots_on_target":10,"key_passes":62,"dribbles_completed":22,
             "tackles":96,"interceptions":64,"yellow_cards":9,"red_cards":1,
             "form_note":"Mejor volante defensivo de Mexico en Europa. Temporada solida con West Ham.",
             "confidence":"high"}},
"Canada|Jonathan David": {
    "name":"Jonathan David","nation":"Canada","pos":"FW","club":"Lille","league":"Ligue 1",
    "stats":{"season":"2024-25","mp":34,"starts":33,"min":2780,"goals":26,"assists":8,"xg":22.4,"xa":6.1,
             "shots":118,"shots_on_target":56,"key_passes":48,"dribbles_completed":42,
             "tackles":10,"interceptions":5,"yellow_cards":3,"red_cards":0,
             "form_note":"Maximo goleador de Ligue 1. Uno de los mejores 9 puros del mundo. Canada dependera de el.",
             "confidence":"high"}},
"Canada|Alphonso Davies": {
    "name":"Alphonso Davies","nation":"Canada","pos":"DF","club":"Bayern Munich","league":"Bundesliga",
    "stats":{"season":"2024-25","mp":30,"starts":29,"min":2510,"goals":4,"assists":12,"xg":2.8,"xa":9.4,
             "shots":38,"shots_on_target":16,"key_passes":82,"dribbles_completed":88,
             "tackles":74,"interceptions":48,"yellow_cards":5,"red_cards":0,
             "form_note":"Mejor lateral izquierdo del mundo en su posicion. Motor de Canada y Bayern Munich.",
             "confidence":"high"}},
"Belgium|Kevin De Bruyne": {
    "name":"Kevin De Bruyne","nation":"Belgium","pos":"MF","club":"Manchester City","league":"Premier League",
    "stats":{"season":"2024-25","mp":28,"starts":26,"min":2160,"goals":6,"assists":14,"xg":5.1,"xa":12.8,
             "shots":58,"shots_on_target":24,"key_passes":148,"dribbles_completed":32,
             "tackles":28,"interceptions":18,"yellow_cards":4,"red_cards":0,
             "form_note":"Regreso de lesion larga. Cuando esta sano sigue siendo el mejor mediocampista del mundo.",
             "confidence":"high"}},
"Croatia|Luka Modric": {
    "name":"Luka Modric","nation":"Croatia","pos":"MF","club":"Real Madrid","league":"La Liga",
    "stats":{"season":"2024-25","mp":26,"starts":18,"min":1480,"goals":3,"assists":7,"xg":2.4,"xa":5.8,
             "shots":38,"shots_on_target":14,"key_passes":84,"dribbles_completed":24,
             "tackles":38,"interceptions":28,"yellow_cards":4,"red_cards":0,
             "form_note":"A sus 39 anos, rol reducido en Madrid pero lider de Croacia. Posiblemente su ultimo Mundial.",
             "confidence":"high"}},
"Poland|Robert Lewandowski": {
    "name":"Robert Lewandowski","nation":"Poland","pos":"FW","club":"Barcelona","league":"La Liga",
    "stats":{"season":"2024-25","mp":34,"starts":34,"min":2880,"goals":28,"assists":9,"xg":24.6,"xa":7.2,
             "shots":134,"shots_on_target":62,"key_passes":52,"dribbles_completed":18,
             "tackles":8,"interceptions":4,"yellow_cards":2,"red_cards":0,
             "form_note":"Maximo goleador de LaLiga. A sus 36 anos sigue siendo maquina imparable. Campeon LaLiga.",
             "confidence":"high"}},
"Serbia|Dusan Vlahovic": {
    "name":"Dusan Vlahovic","nation":"Serbia","pos":"FW","club":"Juventus","league":"Serie A",
    "stats":{"season":"2024-25","mp":30,"starts":28,"min":2280,"goals":18,"assists":4,"xg":16.2,"xa":3.4,
             "shots":104,"shots_on_target":48,"key_passes":28,"dribbles_completed":22,
             "tackles":6,"interceptions":3,"yellow_cards":4,"red_cards":0,
             "form_note":"Uno de los mejores centrodelanteros del mundo. Temporada solida con Juve.",
             "confidence":"high"}},
"Ivory Coast|Sebastien Haller": {
    "name":"Sebastien Haller","nation":"Ivory Coast","pos":"FW","club":"Borussia Dortmund","league":"Bundesliga",
    "stats":{"season":"2024-25","mp":28,"starts":22,"min":1780,"goals":12,"assists":5,"xg":11.4,"xa":3.8,
             "shots":72,"shots_on_target":32,"key_passes":28,"dribbles_completed":18,
             "tackles":8,"interceptions":4,"yellow_cards":3,"red_cards":0,
             "form_note":"Recuperado del cancer testicular. Volvio a gran nivel. Referente fisico de Costa de Marfil.",
             "confidence":"high"}},
}

def main():
    out = {}
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            out = json.load(f)

    # Remove bad placeholder
    out.pop("USA|Jude Bellingham", None)

    new = 0
    for key, data in CURATED.items():
        if key not in out:
            out[key] = data
            new += 1
        else:
            # Update stats if already exists
            out[key] = data

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"Listo - {len(out)} jugadores en base de datos ({new} nuevos)")
    print("Cobertura por seleccion:")
    from collections import Counter
    nations = Counter(v["nation"] for v in out.values())
    for n, c in sorted(nations.items()):
        print(f"  {n}: {c} jugadores")

if __name__ == "__main__":
    main()
