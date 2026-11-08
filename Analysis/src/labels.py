"""
Русские названия для справочников OSHA/OIICS и нормализация названий.

В данных смешаны редакции OIICS, поэтому одно название встречается под разными
кодами и в разном написании ('Leg(s), unspecified' и 'Leg(s) unspecified').
norm_title() приводит такие варианты к одному ключу, чтобы их можно было объединить.

Использование:

    from src.labels import norm_title, body_part_ru, BODY_DIVISIONS

    df["key"] = df["body_part"].map(norm_title)
    ax.set_yticklabels([body_part_ru(t) if lang == "ru" else t for t in df["body_part"]])
"""

import re

# Разделы частей тела по первой цифре кода OIICS: цифра -> (ru, en)
BODY_DIVISIONS = {
    "1": ("Голова", "Head"),
    "2": ("Шея", "Neck"),
    "3": ("Туловище", "Trunk"),
    "4": ("Верхние конечности", "Upper extremities"),
    "5": ("Нижние конечности", "Lower extremities"),
    "6": ("Системы организма", "Body systems"),
    "8": ("Несколько частей тела", "Multiple body parts"),
    "9": ("Прочее / не классиф.", "Other / nonclassifiable"),
}

# Виды тяжёлых последствий: бит severity_code -> (ru, en)
SEVERITY = {
    4: ("Госпитализация", "Hospitalization"),
    2: ("Ампутация", "Amputation"),
    1: ("Потеря глаза", "Loss of eye"),
}


def norm_title(title: str) -> str:
    """Ключ для объединения одинаковых названий: без регистра, запятых, дефисов и лишних пробелов."""
    return re.sub(r"[\s,\-]+", " ", title).strip().lower()


_BODY_PART_RU = {
    "fingertip(s)": "Кончики пальцев",
    "finger(s) fingernail(s) n.e.c.": "Пальцы, ногти (прочее)",
    "finger(s) fingernail(s) unspecified": "Пальцы, ногти (не уточнено)",
    "finger or thumb tip(s) nail(s)": "Кончики пальцев / большого пальца, ногти",
    "multiple body parts n.e.c.": "Несколько частей тела (прочее)",
    "multiple body parts unspecified": "Несколько частей тела (не уточнено)",
    "body systems": "Системы организма",
    "leg(s) unspecified": "Ноги (не уточнено)",
    "hip(s)": "Тазобедренная область",
    "hip joint(s)": "Тазобедренные суставы",
    "nonclassifiable": "Не классифицировано",
    "brain": "Головной мозг",
    "ankle(s)": "Лодыжки",
    "lower leg(s)": "Голени",
    "hand(s) unspecified": "Кисти рук (не уточнено)",
    "chest except internal location of diseases or disorders": "Грудная клетка",
    "arm(s) unspecified": "Руки (не уточнено)",
    "foot (feet) unspecified": "Стопы (не уточнено)",
    "back including spine spinal cord unspecified": "Спина, позвоночник",
    "thigh(s)": "Бёдра",
    "knee(s)": "Колени",
    "wrist(s)": "Запястья",
    "forearm(s)": "Предплечья",
    "abdomen except internal location of diseases or disorders": "Живот",
    "multiple trunk locations": "Несколько областей туловища",
    "toes(s) toenail(s)": "Пальцы ног, ногти",
    "upper and lower limb(s)": "Верхние и нижние конечности",
    "lumbar region": "Поясничная область",
    "shoulder(s) including clavicle(s) scapula(e)": "Плечи, ключицы, лопатки",
    "pelvis": "Таз",
    "head unspecified": "Голова (не уточнено)",
    "head and trunk": "Голова и туловище",
    "elbow(s)": "Локти",
    "face unspecified": "Лицо (не уточнено)",
    "upper arm(s)": "Плечи (верхняя часть руки)",
    "eye(s)": "Глаза",
    "multiple head locations": "Несколько областей головы",
    "skull": "Череп",
    "hand(s) except finger(s)": "Кисти рук (кроме пальцев)",
    "neck including throat": "Шея, горло",
    "ear(s)": "Уши",
    "nose nasal cavity": "Нос",
    "mouth": "Рот",
    "body systems and other part(s) of body": "Системы организма и другие части тела",
    "hand(s) and arm(s) unspecified": "Кисти и руки (не уточнено)",
    "hand(s) and finger(s)": "Кисти и пальцы",
    "leg(s) n.e.c.": "Ноги (прочее)",
}


def body_part_ru(title: str) -> str:
    """Русское название части тела; если перевода нет — исходное английское."""
    return _BODY_PART_RU.get(norm_title(title), title)


# ---------------------------------------------------------------------------
# Источники травмы (Source / Secondary Source)
# ---------------------------------------------------------------------------

# Разделы источников по первой цифре кода OIICS: цифра -> (ru, en)
SOURCE_DIVISIONS = {
    "1": ("Химические вещества", "Chemicals"),
    "2": ("Тара, мебель, оборудование помещений", "Containers, furniture, fixtures"),
    "3": ("Машины и механизмы", "Machinery"),
    "4": ("Детали и материалы", "Parts and materials"),
    "5": ("Люди, растения, животные, минералы", "Persons, plants, animals, minerals"),
    "6": ("Конструкции и поверхности", "Structures and surfaces"),
    "7": ("Инструменты, приборы, оборудование", "Tools, instruments, equipment"),
    "8": ("Транспортные средства", "Vehicles"),
    "9": ("Прочие источники", "Other sources"),
}

# Коды-заглушки вторичного источника (не реальный источник)
SECONDARY_PLACEHOLDERS = (990, 991)

_SOURCE_RU = {
    "floors walkways ground surfaces unspecified": "Полы, проходы, поверхность земли",
    "floor n.e.c.": "Пол (прочее)",
    "floor unspecified": "Пол (не уточнено)",
    "forklift order picker platform truck powered": "Погрузчик (вилочный, комплектовщик)",
    "nonclassifiable": "Не классифицировано",
    "other constructed surface": "Прочие искусственные покрытия",
    "heat environmental": "Жара (окружающая среда)",
    "machinery unspecified": "Машины (не уточнено)",
    "ice sleet snow": "Лёд, мокрый снег, снег",
    "pallet jack powered": "Электрическая паллетная тележка",
    "step ladders": "Стремянки",
    "ladders unspecified": "Лестницы (не уточнено)",
    "movable ladders unspecified": "Переносные лестницы",
    "portable ladders and stairs unspecified": "Переносные лестницы и трапы",
    "extension ladders": "Выдвижные лестницы",
    "semi tractor trailer tanker truck": "Седельный тягач, фура, цистерна",
    "belts gloves neckties scarves": "Ремни, перчатки, галстуки, шарфы",
    "skids pallets": "Поддоны, паллеты",
    "boxes crates cartons": "Ящики, коробки",
    "truck motorized freight hauling and utility unspecified": "Грузовик (не уточнено)",
    "water": "Вода",
    "racks garment and other": "Стеллажи, вешала",
    "scaffolds staging unspecified": "Строительные леса",
    "metal woodworking and special material machinery unspecified": "Металло- и деревообрабатывающие станки",
    "metal woodworking and special material machinery n.e.c.": "Металло- и деревообрабатывающие станки (прочее)",
    "highway vehicle motorized unspecified": "Автомобиль дорожный (не уточнено)",
    "structural elements n.e.c.": "Элементы конструкций (прочее)",
    "butchering machinery": "Оборудование для разделки мяса",
    "roofs unspecified": "Крыши",
    "trailers": "Прицепы",
    "cart dolly hand truck nonpowered": "Ручные тележки",
    "power lines transformers convertors": "ЛЭП, трансформаторы, преобразователи",
    "conveyors powered unspecified": "Конвейеры приводные",
    "conveyors belt": "Ленточные конвейеры",
    "cranes unspecified": "Краны",
    "doors except garage and vehicle": "Двери (кроме гаражных и автомобильных)",
    "ramps loading docks dock plates": "Пандусы, погрузочные платформы",
    "oil drilling rigs and machinery": "Нефтяные буровые установки",
    "bodily motion or position of injured ill worker": "Движение или поза самого работника",
    "stairs steps indoors": "Лестницы, ступени в помещении",
    "stairs steps unspecified": "Лестницы, ступени (не уточнено)",
    "parts and materials unspecified": "Детали и материалы (не уточнено)",
    "sawing machinery stationary n.e.c.": "Стационарные пильные станки",
    "pipes ducts tubing unspecified": "Трубы, воздуховоды",
    "table saws": "Настольные циркулярные пилы",
    "special process machinery n.e.c.": "Специальное технологическое оборудование",
    "parking lot unspecified": "Парковка",
    "parking lot paved": "Парковка (с покрытием)",
    "machine and appliance parts n.e.c.": "Детали машин и приборов",
    "reels rolls spools coils cones": "Катушки, рулоны, бобины",
    "saws powered except chainsaws": "Электропилы (кроме цепных)",
    "food and beverage processing machinery specialized n.e.c.": "Оборудование пищевых производств",
    "vehicle and mobile equipment parts n.e.c.": "Детали транспорта и самоходной техники",
    "aerial lifts scissor lifts except truck mounted": "Подъёмники, ножничные подъёмники",
    "automobile": "Легковой автомобиль",
    "packaging wrapping bundling machinery": "Упаковочное оборудование",
    "tanks bins vats nonconfined space": "Баки, бункеры, чаны",
    "liquids unspecified": "Жидкости",
    "delivery truck or van": "Развозной грузовик, фургон",
    "ground n.e.c.": "Земля, грунт",
    "trees": "Деревья",
    "switchboards switches fuses": "Щиты, выключатели, предохранители",
    "patient": "Пациент",
    "stamping machinery presses except printing": "Штамповочные прессы",
    "beams unattached metal": "Металлические балки",
    "industrial vehicle material hauling and transport powered n.e.c": "Промышленный транспорт (прочее)",
    "knives unspecified or n.e.c.": "Ножи",
    "shelves shelving racks": "Полки, стеллажи",
    "water liquids nonchemical": "Вода, нехимические жидкости",
    "hoses": "Шланги",
    "valves nozzles": "Клапаны, сопла",
    "existing floor opening": "Проём в полу",
    "power cords electrical cords extension cords": "Электрические шнуры, удлинители",
    "walls": "Стены",
    "garbage recycling or refuse truck": "Мусоровоз",
    "carbon monoxide": "Угарный газ",
    "high winds gusts turbulence": "Сильный ветер, порывы",
    "cranes gantry overhead monorail container": "Козловые, мостовые, контейнерные краны",
    "portable ladders and stairs unspecified": "Переносные лестницы и трапы",
    "roof surface": "Поверхность крыши",
    "trucks unspecified": "Грузовики (не уточнено)",
    "conveyors belt slot chain": "Конвейеры ленточные, цепные",
    "other semi tractor trailer": "Прочие тягачи, фуры",
    "hoists lifts scissor telescoping": "Подъёмники, ножничные и телескопические",
    "saws except chainsaws": "Пилы (кроме цепных)",
    "gloves handguards except disposable electric insulating": "Перчатки, защита рук",
    "machine guards": "Защитные ограждения машин",
    "drives belts chains": "Приводы, ремни, цепи",
    "source secondary source unspecified": "Источник не уточнён",
    "secondary source not applicable": "Вторичный источник неприменим",
}


def source_ru(title: str) -> str:
    """Русское название источника; если перевода нет — исходное английское."""
    return _SOURCE_RU.get(norm_title(title), title)


# ---------------------------------------------------------------------------
# Характер травмы (Nature)
# ---------------------------------------------------------------------------

_NATURE_RU = {
    "fractures": "Переломы",
    "amputations": "Ампутации",
    "soreness pain hurt nonspecified injury": "Боль без уточнения травмы",
    "cuts lacerations": "Порезы, рваные раны",
    "amputations avulsions enucleations unspecified": "Ампутации, отрывы (не уточнено)",
    "heat (thermal) burns unspecified": "Термические ожоги",
    "intracranial injuries unspecified": "Внутричерепные травмы",
    "traumatic injuries and disorders unspecified": "Травмы (не уточнено)",
    "crushing injuries": "Размозжения",
    "amputations involving bone loss": "Ампутации с потерей кости",
    "internal injuries to organs and blood vessels of the trunk": "Повреждения внутренних органов",
    "puncture wounds except gunshot wounds": "Колотые раны",
    "traumatic injuries or exposures unspecified": "Травмы или воздействия (не уточнено)",
    "fractures and other injuries n.e.c.": "Переломы и другие травмы",
    "electrical burns unspecified": "Электрические ожоги",
    "concussions": "Сотрясения мозга",
    "second degree heat (thermal) burns": "Термические ожоги II степени",
    "effects of heat and light unspecified": "Воздействие жары и света",
    "bruises contusions": "Ушибы",
    "effects of heat and light n.e.c.": "Воздействие жары и света (прочее)",
    "fractures and dislocations": "Переломы и вывихи",
    "chemical burns and corrosions unspecified": "Химические ожоги",
    "electrocutions electric shocks": "Поражение электротоком",
    "third or fourth degree heat (thermal) burns": "Термические ожоги III–IV степени",
    "avulsions enucleations": "Отрывы тканей",
}


def nature_ru(title: str) -> str:
    """Русское название вида травмы; если перевода нет — исходное английское."""
    return _NATURE_RU.get(norm_title(title), title)


# Укрупнённые категории травм — те же правила, что в SQL/06_nature.sql (порядок важен:
# первая подходящая категория). ru, en, ключевые слова (ищутся в названии без регистра)
NATURE_CATEGORIES = [
    ("Ампутации", "Amputations", ["amputat", "avulsion", "enucleation"]),
    ("Переломы", "Fractures", ["fracture"]),
    ("Ожоги", "Burns", ["burn"]),
    ("Поражение электротоком", "Electrocution", ["electrocution", "electric shock"]),
    ("Тепловой удар / перегрев", "Heat illness", ["heat", "hyperthermia"]),
    ("Черепно-мозговые травмы", "Brain injuries", ["intracranial", "concussion"]),
    ("Раны (порезы, проколы)", "Wounds (cuts, punctures)", ["cuts", "laceration", "puncture"]),
    ("Размозжения", "Crushing injuries", ["crush"]),
    ("Вывихи, растяжения", "Dislocations, sprains", ["dislocation", "sprain", "strain"]),
    ("Внутренние повреждения", "Internal injuries", ["internal injur"]),
    ("Боль без уточнения", "Unspecified pain", ["soreness", "pain"]),
]
NATURE_OTHER = ("Прочее", "Other")


def nature_category(title: str) -> tuple[str, str]:
    """Категория травмы (ru, en) по названию из nature_lookup."""
    t = title.lower()
    for ru, en, words in NATURE_CATEGORIES:
        if any(w in t for w in words):
            return ru, en
    return NATURE_OTHER


# ---------------------------------------------------------------------------
# Типы происшествий (Event)
# ---------------------------------------------------------------------------

EVENT_DIVISIONS = {
    "1": ("Насилие, травмы от людей и животных", "Violence, injuries by persons or animals"),
    "2": ("Транспортные происшествия", "Transportation incidents"),
    "3": ("Пожары и взрывы", "Fires and explosions"),
    "4": ("Падения, поскальзывания, спотыкания", "Falls, slips, trips"),
    "5": ("Воздействие вредных веществ и среды", "Exposure to harmful substances or environments"),
    "6": ("Контакт с предметами и оборудованием", "Contact with objects and equipment"),
    "7": ("Перенапряжение и реакция организма", "Overexertion and bodily reaction"),
    "9": ("Не классифицировано", "Nonclassifiable"),
}

_EVENT_RU = {
    "caught in running equipment or machinery during regular operation": "Затянуло в работающее оборудование (штатная работа)",
    "other fall to lower level unspecified": "Падение с высоты (не уточнено)",
    "caught in running equipment or machinery during maintenance cleaning": "Затянуло в оборудование при обслуживании, чистке",
    "compressed or pinched by shifting objects or equipment": "Сдавило смещающимися предметами, оборудованием",
    "other fall to lower level less than 6 feet": "Падение с высоты менее 1,8 м",
    "other fall to lower level 6 to 10 feet": "Падение с высоты 1,8–3 м",
    "other fall to lower level 11 to 15 feet": "Падение с высоты 3,4–4,6 м",
    "fall on same level due to slipping": "Падение на одном уровне: поскользнулся",
    "fall on same level due to tripping over an object": "Падение на одном уровне: споткнулся о предмет",
    "fall on same level due to slip or trip": "Падение на одном уровне: поскользнулся или споткнулся",
    "fall on same level n.e.c.": "Падение на одном уровне (прочее)",
    "fall on same level unspecified": "Падение на одном уровне (не уточнено)",
    "fall on same level due to tripping unspecified": "Падение на одном уровне: споткнулся",
    "struck against moving part of machinery or equipment": "Удар о движущуюся часть машины",
    "caught in or compressed by equipment or objects unspecified": "Захват или сдавливание оборудованием (не уточнено)",
    "exposure to environmental heat": "Воздействие жары окружающей среды",
    "exposure to environmental heat outdoor": "Воздействие жары на улице",
    "injured by slipping or swinging object held by injured worker": "Травма соскользнувшим инструментом в руках",
    "struck by falling object or equipment n.e.c.": "Удар падающим предметом (прочее)",
    "struck by falling object or equipment unspecified": "Удар падающим предметом (не уточнено)",
    "contact with hot objects or substances": "Контакт с горячими предметами, веществами",
    "struck by object falling from vehicle or machinery other than vehicle part": "Удар предметом, упавшим с транспорта или машины",
    "struck by running powered equipment during maintenance cleaning testing": "Удар работающим оборудованием при обслуживании",
    "part of occupant s body caught between vehicle and other object in nonroadway transport incident": "Зажатие между транспортом и предметом (вне дорог)",
    "caught entangled in running powered equipment normal operation": "Затягивание в работающее оборудование",
    "contact with objects and equipment unspecified": "Контакт с предметами, оборудованием (не уточнено)",
    "caught in running equipment or machinery unspecified": "Затянуло в оборудование (не уточнено)",
    "caught in running equipment or machinery n.e.c.": "Затянуло в оборудование (прочее)",
    "pedestrian struck by vehicle in nonroadway area unspecified": "Наезд на пешехода вне дорог",
    "pedestrian struck by vehicle backing up in nonroadway area": "Наезд задним ходом на пешехода вне дорог",
    "struck by dislodged flying object particle": "Удар отлетевшим предметом, частицей",
    "struck by discharged object or substance": "Удар выброшенным предметом, веществом",
    "direct exposure to electricity unspecified": "Прямое воздействие электричества",
    "struck by swinging part of powered vehicle": "Удар качающейся частью техники",
    "struck by or caught in swinging door or gate": "Удар или защемление дверью, воротами",
    "inhalation of harmful substance single episode": "Вдыхание вредного вещества (однократно)",
    "nonclassifiable": "Не классифицировано",
}


def event_ru(title: str) -> str:
    """Русское название типа происшествия; если перевода нет — исходное английское."""
    return _EVENT_RU.get(norm_title(title), title)


# ---------------------------------------------------------------------------
# Отрасли (NAICS)
# ---------------------------------------------------------------------------

def sector_code(naics) -> str:
    """Сектор NAICS по коду отрасли; секторы-диапазоны объединены как в SQL."""
    if not isinstance(naics, str) or not naics:
        return "нет кода"
    p = naics[:2]
    return {"31": "31-33", "32": "31-33", "33": "31-33",
            "44": "44-45", "45": "44-45", "48": "48-49", "49": "48-49"}.get(p, p)


# Сектор -> (ru, en кратко)
SECTORS = {
    "31-33": ("Обрабатывающая промышленность", "Manufacturing"),
    "23": ("Строительство", "Construction"),
    "48-49": ("Транспорт и складирование", "Transportation & warehousing"),
    "44-45": ("Розничная торговля", "Retail trade"),
    "42": ("Оптовая торговля", "Wholesale trade"),
    "56": ("Адм. услуги, утилизация отходов", "Admin. support & waste mgmt"),
    "62": ("Здравоохранение, соц. помощь", "Health care & social assistance"),
    "21": ("Добыча полезных ископаемых, нефти, газа", "Mining, oil & gas"),
    "72": ("Гостиницы и общепит", "Accommodation & food services"),
    "81": ("Прочие услуги", "Other services"),
    "11": ("Сельское, лесное хозяйство, рыболовство", "Agriculture, forestry, fishing"),
    "54": ("Профессиональные и научно-техн. услуги", "Professional & technical services"),
    "22": ("Коммунальные услуги", "Utilities"),
    "71": ("Искусство, развлечения, отдых", "Arts, entertainment, recreation"),
    "92": ("Государственное управление", "Public administration"),
    "53": ("Недвижимость, прокат техники и транспорта", "Real estate, rental & leasing"),
    "51": ("Информация и связь", "Information"),
    "61": ("Образование", "Educational services"),
    "52": ("Финансы и страхование", "Finance & insurance"),
    "55": ("Управление компаниями", "Management of companies"),
    "99": ("Не классифицировано", "Nonclassifiable"),
    "нет кода": ("Нет кода", "No code"),
}

_NAICS_RU = {
    # подсекторы (3 цифры)
    "238": "Специализированные строительные работы",
    "311": "Пищевая промышленность",
    "332": "Производство металлоизделий",
    "561": "Административные и вспомогательные услуги",
    "237": "Инфраструктурное строительство",
    "236": "Строительство зданий",
    "423": "Оптовая торговля товарами длит. пользования",
    "336": "Производство транспортного оборудования",
    "333": "Машиностроение",
    "424": "Оптовая торговля товарами кратк. пользования",
    "622": "Больницы",
    "331": "Металлургия",
    "321": "Деревообработка",
    "213": "Вспомогательные работы в добыче",
    "445": "Продуктовые магазины",
    "484": "Грузовые автоперевозки",
    "326": "Производство изделий из пластмасс и резины",
    "493": "Складское хозяйство",
    "325": "Химическая промышленность",
    "541": "Профессиональные и научно-техн. услуги",
    "562": "Сбор и утилизация отходов",
    "327": "Производство неметаллических минеральных изделий",
    "322": "Целлюлозно-бумажная промышленность",
    "491": "Почтовая служба",
    "722": "Общепит",
    "811": "Ремонт и обслуживание",
    "488": "Вспомогательные транспортные услуги",
    "452": "Универсальные магазины",
    "453": "Прочие розничные магазины",
    "221": "Коммунальные услуги",
    "623": "Дома престарелых и интернаты",
    "713": "Развлечения, азартные игры, отдых",
    "441": "Продажа автомобилей и запчастей",
    "444": "Стройматериалы и товары для сада",
    "621": "Амбулаторная медицинская помощь",
    "492": "Курьерская доставка",
    "337": "Производство мебели",
    "335": "Производство электрооборудования",
    "339": "Прочие производства",
    "112": "Животноводство и аквакультура",
    "532": "Прокат техники и транспорта",
    "721": "Гостиницы",
    "517": "Телекоммуникации",
    "531": "Недвижимость",
    "611": "Образование",
    "111": "Растениеводство",
    # отрасли (6 цифр)
    "622110": "Больницы общего профиля",
    "445110": "Супермаркеты и продуктовые магазины",
    "238210": "Электромонтажные работы",
    "236220": "Строительство коммерческих зданий",
    "213112": "Обслуживание нефтегазовых скважин",
    "237310": "Строительство дорог и мостов",
    "493110": "Склады общего назначения",
    "491110": "Почтовая служба",
    "238160": "Кровельные работы",
    "238220": "Сантехника, отопление, кондиционирование",
    "561730": "Ландшафтные работы",
    "484121": "Дальние грузоперевозки (полная загрузка)",
    "311615": "Переработка птицы",
    "326199": "Прочие изделия из пластмасс",
    "238990": "Прочие специализированные строительные работы",
    "238910": "Подготовка строительных площадок",
    "238110": "Бетонные фундаменты и конструкции",
    "238120": "Монтаж стальных и сборных ЖБ конструкций",
    "237110": "Прокладка водопровода и канализации",
    "321113": "Лесопильные заводы",
}


# Английские названия старых кодов NAICS (редакция 2017), которых нет в справочнике 2022
NAICS_LEGACY_EN = {
    "452": "General Merchandise Stores",
    "453": "Miscellaneous Store Retailers",
    "446": "Health and Personal Care Stores",
    "447": "Gasoline Stations",
    "448": "Clothing and Clothing Accessories Stores",
    "451": "Sporting Goods, Hobby, Musical Instrument, and Book Stores",
    "454": "Nonstore Retailers",
}


def naics_ru(code: str, title: str) -> str:
    """Русское название подсектора/отрасли по коду NAICS; если перевода нет — английское."""
    return _NAICS_RU.get(code, title)


# ---------------------------------------------------------------------------
# Время: месяцы, сезоны, дни недели
# ---------------------------------------------------------------------------

MONTHS = {
    1: ("Янв", "Jan"), 2: ("Фев", "Feb"), 3: ("Мар", "Mar"), 4: ("Апр", "Apr"),
    5: ("Май", "May"), 6: ("Июн", "Jun"), 7: ("Июл", "Jul"), 8: ("Авг", "Aug"),
    9: ("Сен", "Sep"), 10: ("Окт", "Oct"), 11: ("Ноя", "Nov"), 12: ("Дек", "Dec"),
}

# Метеорологические сезоны северного полушария: декабрь относится к зиме
SEASONS = {
    "winter": ("Зима", "Winter", (12, 1, 2)),
    "spring": ("Весна", "Spring", (3, 4, 5)),
    "summer": ("Лето", "Summer", (6, 7, 8)),
    "autumn": ("Осень", "Autumn", (9, 10, 11)),
}
MONTH_TO_SEASON = {m: key for key, (_, _, months) in SEASONS.items() for m in months}

WEEKDAYS = {
    1: ("Пн", "Mon"), 2: ("Вт", "Tue"), 3: ("Ср", "Wed"), 4: ("Чт", "Thu"),
    5: ("Пт", "Fri"), 6: ("Сб", "Sat"), 7: ("Вс", "Sun"),
}


# ---------------------------------------------------------------------------
# Штаты
# ---------------------------------------------------------------------------

_STATE_RU = {
    "TEXAS": "Техас", "FLORIDA": "Флорида", "PENNSYLVANIA": "Пенсильвания", "OHIO": "Огайо",
    "ILLINOIS": "Иллинойс", "GEORGIA": "Джорджия", "NEW YORK": "Нью-Йорк", "WISCONSIN": "Висконсин",
    "ALABAMA": "Алабама", "MISSOURI": "Миссури", "COLORADO": "Колорадо", "NEW JERSEY": "Нью-Джерси",
    "LOUISIANA": "Луизиана", "MASSACHUSETTS": "Массачусетс", "OKLAHOMA": "Оклахома",
    "ARKANSAS": "Арканзас", "KANSAS": "Канзас", "MISSISSIPPI": "Миссисипи", "NEBRASKA": "Небраска",
    "CONNECTICUT": "Коннектикут", "IDAHO": "Айдахо", "WEST VIRGINIA": "Западная Виргиния",
    "NORTH DAKOTA": "Северная Дакота", "MAINE": "Мэн", "SOUTH DAKOTA": "Южная Дакота",
    "NEW HAMPSHIRE": "Нью-Гэмпшир", "MONTANA": "Монтана", "DELAWARE": "Делавэр",
    "CALIFORNIA": "Калифорния", "RHODE ISLAND": "Род-Айленд", "DISTRICT OF COLUMBIA": "Округ Колумбия",
    "SOUTH CAROLINA": "Южная Каролина", "NORTH CAROLINA": "Северная Каролина", "VIRGINIA": "Виргиния",
    "MARYLAND": "Мэриленд", "MICHIGAN": "Мичиган", "INDIANA": "Индиана", "KENTUCKY": "Кентукки",
    "TENNESSEE": "Теннесси", "IOWA": "Айова", "MINNESOTA": "Миннесота", "ARIZONA": "Аризона",
    "NEVADA": "Невада", "UTAH": "Юта", "NEW MEXICO": "Нью-Мексико", "OREGON": "Орегон",
    "WASHINGTON": "Вашингтон", "WYOMING": "Вайоминг", "VERMONT": "Вермонт", "HAWAII": "Гавайи",
    "ALASKA": "Аляска", "PUERTO RICO": "Пуэрто-Рико", "GUAM": "Гуам",
    "NORTHERN MARIANA ISLANDS": "Северные Марианские острова", "AMERICAN SAMOA": "Американское Самоа",
    "VIRGIN ISLANDS": "Виргинские острова",
}

# Штаты с собственной программой охраны труда (State Plan), охватывающей частный сектор:
# о травмах там сообщают в программу штата, поэтому в федеральных данных OSHA их мало
STATE_PLAN = {
    "ALASKA", "ARIZONA", "CALIFORNIA", "HAWAII", "INDIANA", "IOWA", "KENTUCKY", "MARYLAND",
    "MICHIGAN", "MINNESOTA", "NEVADA", "NEW MEXICO", "NORTH CAROLINA", "OREGON", "PUERTO RICO",
    "SOUTH CAROLINA", "TENNESSEE", "UTAH", "VERMONT", "VIRGINIA", "WASHINGTON", "WYOMING",
}


def state_ru(state: str) -> str:
    """Русское название штата; если перевода нет — исходное."""
    return _STATE_RU.get(state.upper(), state.title())


def state_en(state: str) -> str:
    """Название штата в обычном регистре: 'NEW YORK' -> 'New York'."""
    return state.title()
