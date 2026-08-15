"""Curated flavor-pairing data.

Each key is a canonical ingredient name. ``pairs`` lists other ingredients
that classically work well with it, with a short note on why. Pairings are
one-directional here for brevity — flavor_service builds the reverse edges
automatically, since a good pairing works both ways.
"""

INGREDIENTS = {
    "tomato": {
        "category": "vegetable",
        "pairs": [
            ("basil", "Basil's sweet, peppery aroma lifts tomato's acidity — the classic Italian pairing"),
            ("mozzarella", "Mild, creamy cheese balances tomato's tang (think Caprese)"),
            ("garlic", "Garlic's pungency deepens tomato's savoriness in sauces"),
            ("olive oil", "Fat carries tomato's aromatic compounds and rounds out its acidity"),
            ("balsamic vinegar", "Sweetness and acidity mirror and intensify tomato's own profile"),
            ("oregano", "Earthy, slightly bitter herb that's a Mediterranean staple with tomato"),
        ],
    },
    "garlic": {
        "category": "aromatic",
        "pairs": [
            ("olive oil", "Infuses easily into fat, spreading its aroma through a dish"),
            ("ginger", "Both pungent aromatics used together in countless Asian dishes"),
            ("butter", "Garlic butter is a foundational savory combination"),
            ("chili", "Heat and pungency build on each other"),
            ("lemon", "Acidity cuts garlic's sharpness and brightens it"),
            ("rosemary", "Both are assertive, resinous flavors common in roasting"),
        ],
    },
    "onion": {
        "category": "aromatic",
        "pairs": [
            ("garlic", "The base aromatic duo of countless savory dishes"),
            ("thyme", "Thyme's earthiness complements onion's sweetness once cooked"),
            ("beef", "Caramelized onion deepens beef's savory richness"),
            ("butter", "Slow-cooked in butter for sweetness and body"),
            ("balsamic vinegar", "Sweet-and-sour glaze that plays off onion's own sweetness"),
        ],
    },
    "potato": {
        "category": "vegetable",
        "pairs": [
            ("butter", "Classic mash pairing — fat carries flavor and adds richness"),
            ("rosemary", "Roasted potatoes with rosemary is a staple combination"),
            ("cheddar", "Sharp cheese cuts through potato's starchiness"),
            ("bacon", "Smoky, salty fat against potato's mildness"),
            ("chives", "Fresh oniony bite on top of a rich, starchy base"),
            ("sour cream", "Tangy creaminess against a starchy, neutral canvas"),
        ],
    },
    "mushroom": {
        "category": "vegetable",
        "pairs": [
            ("garlic", "Garlic amplifies mushroom's savory, umami depth"),
            ("thyme", "Earthy herb that echoes mushroom's woodsy notes"),
            ("butter", "Butter carries mushroom's umami and adds silkiness"),
            ("parmesan", "Umami-on-umami — deeply savory together"),
            ("cream", "Rich, mellow base that mushroom's earthiness cuts through"),
        ],
    },
    "spinach": {
        "category": "vegetable",
        "pairs": [
            ("garlic", "Sauteed together, garlic tempers spinach's mineral edge"),
            ("lemon", "Brightens spinach's slightly bitter, mineral flavor"),
            ("feta", "Salty tang against spinach's earthy mildness (spanakopita)"),
            ("nutmeg", "A classic warm-spice pairing in creamed spinach"),
            ("pine nuts", "Toasted nuttiness adds crunch and richness"),
        ],
    },
    "carrot": {
        "category": "vegetable",
        "pairs": [
            ("ginger", "Ginger's spice plays off carrot's natural sweetness"),
            ("cumin", "Warm, earthy spice that deepens roasted carrot"),
            ("honey", "Enhances carrot's sweetness when glazed or roasted"),
            ("orange", "Citrus sweetness and carrot's own sugars reinforce each other"),
            ("thyme", "Herbal earthiness balances carrot's sweetness"),
        ],
    },
    "bell pepper": {
        "category": "vegetable",
        "pairs": [
            ("onion", "Classic sauteed base for countless dishes"),
            ("garlic", "Savory backbone under pepper's sweetness"),
            ("cumin", "Warm spice that suits pepper's fruity sweetness"),
            ("olive oil", "Roasting in oil brings out pepper's natural sugars"),
            ("feta", "Salty, tangy contrast to pepper's sweetness"),
        ],
    },
    "eggplant": {
        "category": "vegetable",
        "pairs": [
            ("garlic", "Garlic's sharpness cuts eggplant's spongey mildness"),
            ("tomato", "Classic Mediterranean pairing (ratatouille, caponata)"),
            ("basil", "Herbal brightness against eggplant's earthy flavor"),
            ("olive oil", "Eggplant absorbs oil readily, carrying its flavor"),
            ("cumin", "Warm spice common in Middle Eastern eggplant dishes"),
        ],
    },
    "zucchini": {
        "category": "vegetable",
        "pairs": [
            ("garlic", "Adds savory depth to zucchini's mild, watery flesh"),
            ("parmesan", "Salty umami against zucchini's blandness"),
            ("mint", "Fresh, cooling herb that lifts zucchini's mild flavor"),
            ("lemon", "Brightens what is otherwise a fairly neutral vegetable"),
            ("basil", "Summer herb pairing common in Italian cooking"),
        ],
    },
    "cauliflower": {
        "category": "vegetable",
        "pairs": [
            ("cumin", "Warm spice that gives cauliflower's mildness character"),
            ("turmeric", "Earthy, slightly bitter spice classic in curried cauliflower"),
            ("parmesan", "Umami-rich cheese that boosts cauliflower's blandness"),
            ("butter", "Rich fat that rounds out cauliflower when roasted or pureed"),
            ("garlic", "Savory backbone for roasted or mashed cauliflower"),
        ],
    },
    "sweet potato": {
        "category": "vegetable",
        "pairs": [
            ("cinnamon", "Warm spice that plays up sweet potato's natural sugars"),
            ("ginger", "Spicy warmth against sweet potato's sweetness"),
            ("maple syrup", "Sweet-on-sweet, classic in roasted or mashed preparations"),
            ("butter", "Richness that carries sweet potato's flavor"),
            ("chili", "Heat provides contrast to sweet potato's sweetness"),
        ],
    },
    "avocado": {
        "category": "fruit",
        "pairs": [
            ("lime", "Acidity cuts avocado's richness and prevents blandness"),
            ("cilantro", "Fresh, citrusy herb classic in guacamole"),
            ("chili", "Heat contrasts avocado's cool creaminess"),
            ("tomato", "Acidity and juiciness balance avocado's fattiness"),
            ("salt", "Simple but essential — avocado is very mild without it"),
        ],
    },
    "lemon": {
        "category": "fruit",
        "pairs": [
            ("garlic", "Acidity cuts garlic's pungency — a very common pairing"),
            ("thyme", "Herbal, resinous notes suit lemon's brightness"),
            ("chicken", "Acid brightens and tenderizes chicken"),
            ("butter", "Rich fat balanced by lemon's sharp acidity"),
            ("parsley", "Fresh, grassy herb that echoes lemon's brightness"),
            ("olive oil", "Base of countless vinaigrettes and marinades"),
        ],
    },
    "lime": {
        "category": "fruit",
        "pairs": [
            ("cilantro", "The defining pairing of Mexican and Southeast Asian cooking"),
            ("chili", "Acid and heat play off each other constantly in salsas"),
            ("coconut milk", "Tart acidity cuts coconut's richness"),
            ("mint", "Cooling herb against lime's sharp citrus bite"),
            ("avocado", "Classic guacamole combination"),
        ],
    },
    "orange": {
        "category": "fruit",
        "pairs": [
            ("cinnamon", "Warm spice that complements citrus sweetness"),
            ("chocolate", "Bitter cocoa against orange's bright sweetness — a classic dessert pair"),
            ("ginger", "Spicy warmth against citrus brightness"),
            ("fennel", "Anise notes complement citrus in salads"),
            ("almond", "Nutty richness balances citrus acidity"),
        ],
    },
    "apple": {
        "category": "fruit",
        "pairs": [
            ("cinnamon", "The archetypal warm-spice fruit pairing"),
            ("pork", "Apple's sweetness cuts pork's richness — a classic combination"),
            ("cheddar", "Sharp cheese against apple's sweet-tart crunch"),
            ("walnut", "Nutty bitterness contrasts apple's sweetness"),
            ("caramel", "Sweetness amplified, with caramel's depth adding complexity"),
        ],
    },
    "pear": {
        "category": "fruit",
        "pairs": [
            ("blue cheese", "Sweet fruit against sharp, salty, funky cheese — a classic pairing"),
            ("walnut", "Nutty crunch and bitterness against pear's soft sweetness"),
            ("honey", "Amplifies pear's natural floral sweetness"),
            ("ginger", "Warm spice that adds depth to pear's mild flavor"),
            ("vanilla", "Rounds out pear's sweetness in baking"),
        ],
    },
    "strawberry": {
        "category": "fruit",
        "pairs": [
            ("basil", "Peppery herb note that makes strawberry's sweetness pop"),
            ("balsamic vinegar", "Acidity and sweetness intensify strawberry's flavor"),
            ("black pepper", "A pinch sharpens strawberry's sweetness surprisingly well"),
            ("vanilla", "Classic dessert pairing that rounds out sweetness"),
            ("mint", "Fresh, cooling contrast to strawberry's sweetness"),
        ],
    },
    "mango": {
        "category": "fruit",
        "pairs": [
            ("lime", "Acid cuts mango's tropical sweetness"),
            ("chili", "Heat and sweetness balance in salsas and salads"),
            ("coconut milk", "Tropical richness that pairs naturally with mango"),
            ("cilantro", "Fresh herbal note against mango's sweetness"),
            ("mint", "Cooling herb that lifts mango's tropical flavor"),
        ],
    },
    "peach": {
        "category": "fruit",
        "pairs": [
            ("basil", "Peppery herb that plays up stone fruit's sweetness"),
            ("vanilla", "Rounds out peach's sweetness in desserts"),
            ("ginger", "Warm spice depth against peach's juiciness"),
            ("bourbon", "Caramel and oak notes complement peach's sweetness"),
            ("burrata", "Creamy, mild cheese balanced by peach's sweetness and acid"),
        ],
    },
    "banana": {
        "category": "fruit",
        "pairs": [
            ("chocolate", "Classic dessert pairing — sweetness and bitterness together"),
            ("cinnamon", "Warm spice that deepens banana's sweetness"),
            ("peanut butter", "Rich, nutty fat against banana's soft sweetness"),
            ("honey", "Amplifies banana's natural sugars"),
            ("coconut", "Tropical flavors that reinforce each other"),
        ],
    },
    "fig": {
        "category": "fruit",
        "pairs": [
            ("goat cheese", "Tangy, creamy cheese against fig's honeyed sweetness"),
            ("honey", "Intensifies fig's own natural sweetness"),
            ("prosciutto", "Salty cured meat against fig's sugary flesh"),
            ("walnut", "Earthy crunch that complements fig's softness"),
            ("balsamic vinegar", "Acidity balances fig's richness"),
        ],
    },
    "pineapple": {
        "category": "fruit",
        "pairs": [
            ("coconut milk", "Tropical pairing found throughout island cooking"),
            ("chili", "Sweet heat balance common in salsas"),
            ("mint", "Cooling herb against pineapple's bright acidity"),
            ("pork", "Sweetness and acid cut pork's fattiness"),
            ("lime", "Extra acidity that sharpens pineapple's sweetness"),
        ],
    },
    "basil": {
        "category": "herb",
        "pairs": [
            ("tomato", "Sweet, peppery herb that lifts tomato's acidity"),
            ("garlic", "Base of pesto — pungency and herbal sweetness together"),
            ("mozzarella", "Caprese classic"),
            ("olive oil", "Carries basil's volatile aromatics"),
            ("strawberry", "Unexpected but classic dessert/salad pairing"),
        ],
    },
    "cilantro": {
        "category": "herb",
        "pairs": [
            ("lime", "The defining herb-citrus pairing of Latin and Southeast Asian food"),
            ("chili", "Fresh herbal note against heat"),
            ("cumin", "Warm spice that grounds cilantro's bright, citrusy flavor"),
            ("avocado", "Fresh herb that lifts avocado's richness"),
            ("garlic", "Common aromatic base in salsas and chutneys"),
        ],
    },
    "mint": {
        "category": "herb",
        "pairs": [
            ("lime", "Cooling herb against sharp citrus"),
            ("lamb", "Classic British pairing — mint sauce cuts lamb's richness"),
            ("chocolate", "Cooling freshness against bitter sweetness"),
            ("cucumber", "Both cooling and refreshing together"),
            ("pea", "Traditional pairing in soups and sides"),
        ],
    },
    "rosemary": {
        "category": "herb",
        "pairs": [
            ("garlic", "Resinous herb and pungent aromatic — both assertive, roast well together"),
            ("potato", "Roasted potatoes with rosemary is a staple"),
            ("lamb", "Piney, resinous herb that stands up to lamb's strong flavor"),
            ("lemon", "Brightens rosemary's woodsy intensity"),
            ("olive oil", "Infuses easily, carrying rosemary's aroma"),
        ],
    },
    "thyme": {
        "category": "herb",
        "pairs": [
            ("garlic", "Earthy herb that rounds out garlic's sharpness"),
            ("lemon", "Herbal and citrus brightness together"),
            ("mushroom", "Earthy-on-earthy, a natural match"),
            ("chicken", "Classic roasting herb for poultry"),
            ("butter", "Infuses readily, carrying thyme's aroma into sauces"),
        ],
    },
    "parsley": {
        "category": "herb",
        "pairs": [
            ("lemon", "Fresh, grassy herb that echoes lemon's brightness"),
            ("garlic", "Base of gremolata alongside lemon zest"),
            ("olive oil", "Carries parsley's fresh, green flavor"),
            ("butter", "Classic finishing herb for butter sauces"),
        ],
    },
    "dill": {
        "category": "herb",
        "pairs": [
            ("salmon", "Classic Scandinavian pairing (gravlax)"),
            ("lemon", "Bright, grassy herb against citrus"),
            ("sour cream", "Cool, tangy base that suits dill's fresh flavor"),
            ("cucumber", "Both fresh and cooling — common in salads"),
        ],
    },
    "cinnamon": {
        "category": "spice",
        "pairs": [
            ("apple", "The archetypal warm-spice fruit pairing"),
            ("vanilla", "Both warm baking spices that reinforce each other"),
            ("orange", "Complements citrus sweetness in desserts and drinks"),
            ("chocolate", "Adds warmth and depth to chocolate's bitterness"),
            ("sweet potato", "Warm spice that plays up natural sweetness"),
        ],
    },
    "ginger": {
        "category": "spice",
        "pairs": [
            ("garlic", "Both pungent aromatics, foundational in Asian cooking"),
            ("carrot", "Spice against carrot's natural sweetness"),
            ("honey", "Sweetness balances ginger's heat"),
            ("lime", "Bright acidity against ginger's spice"),
            ("soy sauce", "Umami-salty base that carries ginger's aroma"),
        ],
    },
    "chili": {
        "category": "spice",
        "pairs": [
            ("lime", "Heat and acid constantly paired in salsas and marinades"),
            ("garlic", "Pungency and heat build on each other"),
            ("chocolate", "Heat against bitter sweetness — classic mole pairing"),
            ("cilantro", "Fresh herb that tempers chili's heat"),
            ("honey", "Sweetness balances chili's spice"),
        ],
    },
    "cumin": {
        "category": "spice",
        "pairs": [
            ("cilantro", "Warm spice grounding cilantro's bright citrus note"),
            ("chili", "Common combination in Mexican and Indian cooking"),
            ("carrot", "Earthy spice that deepens carrot's sweetness"),
            ("lime", "Acid brightens cumin's earthy warmth"),
            ("garlic", "Savory base for spice blends"),
        ],
    },
    "black pepper": {
        "category": "spice",
        "pairs": [
            ("strawberry", "A pinch sharpens strawberry's sweetness surprisingly well"),
            ("parmesan", "Classic combination (cacio e pepe)"),
            ("beef", "Standard savory seasoning pairing"),
            ("lemon", "Sharp brightness against pepper's heat"),
            ("honey", "Sweet-and-spicy balance"),
        ],
    },
    "vanilla": {
        "category": "spice",
        "pairs": [
            ("cinnamon", "Both warm baking spices that reinforce each other"),
            ("strawberry", "Classic dessert pairing"),
            ("chocolate", "Rounds out and softens chocolate's bitterness"),
            ("caramel", "Both rich, sweet dessert flavors that build on each other"),
            ("banana", "Sweet, rounded pairing common in baking"),
        ],
    },
    "nutmeg": {
        "category": "spice",
        "pairs": [
            ("spinach", "Classic pairing in creamed spinach"),
            ("cream", "Warm spice that rounds out dairy richness"),
            ("cinnamon", "Common warm-spice blend in baking"),
            ("potato", "Traditional addition to gratins and mash"),
        ],
    },
    "chicken": {
        "category": "protein",
        "pairs": [
            ("lemon", "Acid brightens and tenderizes chicken's mild flavor"),
            ("garlic", "Savory backbone for marinades and roasts"),
            ("thyme", "Classic roasting herb for poultry"),
            ("rosemary", "Resinous herb that suits roasted chicken well"),
            ("honey", "Sweetness that glazes and caramelizes chicken skin"),
        ],
    },
    "beef": {
        "category": "protein",
        "pairs": [
            ("garlic", "Savory backbone for marinades and rubs"),
            ("black pepper", "Standard savory seasoning pairing"),
            ("rosemary", "Resinous herb that stands up to beef's richness"),
            ("onion", "Caramelized onion deepens beef's savory notes"),
            ("red wine", "Acid and tannin cut through beef's fattiness"),
        ],
    },
    "pork": {
        "category": "protein",
        "pairs": [
            ("apple", "Sweetness cuts pork's richness — a classic pairing"),
            ("fennel", "Anise notes complement pork's fattiness"),
            ("garlic", "Savory base for marinades and rubs"),
            ("pineapple", "Sweetness and acid cut through pork's fat"),
            ("mustard", "Sharp tang that balances pork's richness"),
        ],
    },
    "salmon": {
        "category": "protein",
        "pairs": [
            ("dill", "Classic Scandinavian pairing"),
            ("lemon", "Acid brightens salmon's rich, oily flesh"),
            ("garlic", "Savory backbone for glazes and marinades"),
            ("honey", "Sweetness that glazes and caramelizes salmon"),
            ("soy sauce", "Umami-salty depth that suits salmon's richness"),
        ],
    },
    "shrimp": {
        "category": "protein",
        "pairs": [
            ("garlic", "Classic scampi pairing"),
            ("lemon", "Acid brightens shrimp's mild sweetness"),
            ("chili", "Heat contrasts shrimp's delicate flavor"),
            ("cilantro", "Fresh herb common in shrimp dishes"),
            ("butter", "Rich fat that carries garlic and lemon into the dish"),
        ],
    },
    "tofu": {
        "category": "protein",
        "pairs": [
            ("soy sauce", "Umami seasoning that tofu readily absorbs"),
            ("ginger", "Aromatic spice that gives tofu character"),
            ("garlic", "Savory base that tofu takes on well"),
            ("sesame oil", "Nutty richness that flavors tofu's blandness"),
            ("chili", "Heat that contrasts tofu's mild, soft texture"),
        ],
    },
    "eggs": {
        "category": "protein",
        "pairs": [
            ("chives", "Fresh, mild onion flavor that suits eggs well"),
            ("cheddar", "Rich, savory pairing in omelets and scrambles"),
            ("black pepper", "Standard savory seasoning pairing"),
            ("butter", "Classic fat for cooking eggs richly"),
            ("bacon", "Salty, smoky contrast to egg's mildness"),
        ],
    },
    "bacon": {
        "category": "protein",
        "pairs": [
            ("eggs", "Salty, smoky contrast to egg's mildness"),
            ("maple syrup", "Sweet-and-salty balance, classic breakfast pairing"),
            ("potato", "Smoky, salty fat against potato's mildness"),
            ("black pepper", "Standard savory seasoning pairing"),
        ],
    },
    "butter": {
        "category": "dairy",
        "pairs": [
            ("garlic", "Garlic butter is a foundational savory combination"),
            ("thyme", "Infuses readily, carrying thyme's aroma into sauces"),
            ("lemon", "Rich fat balanced by lemon's sharp acidity"),
            ("honey", "Sweet-savory combination common on baked goods"),
        ],
    },
    "mozzarella": {
        "category": "dairy",
        "pairs": [
            ("tomato", "Mild, creamy cheese balances tomato's tang"),
            ("basil", "Caprese classic"),
            ("olive oil", "Carries basil and tomato's flavor over mozzarella's mildness"),
        ],
    },
    "parmesan": {
        "category": "dairy",
        "pairs": [
            ("black pepper", "Classic combination (cacio e pepe)"),
            ("mushroom", "Umami-on-umami — deeply savory together"),
            ("garlic", "Savory depth alongside parmesan's saltiness"),
            ("olive oil", "Rounds out parmesan's sharpness"),
        ],
    },
    "cream": {
        "category": "dairy",
        "pairs": [
            ("mushroom", "Rich, mellow base that mushroom's earthiness cuts through"),
            ("nutmeg", "Warm spice that rounds out dairy richness"),
            ("garlic", "Savory depth against cream's richness"),
            ("parmesan", "Rich, savory combination in sauces"),
        ],
    },
    "feta": {
        "category": "dairy",
        "pairs": [
            ("spinach", "Salty tang against spinach's earthy mildness"),
            ("watermelon", "Salty cheese against sweet, juicy fruit — a classic summer pairing"),
            ("olive oil", "Rounds out feta's sharp saltiness"),
            ("mint", "Fresh herb that lifts feta's briny tang"),
            ("bell pepper", "Salty, tangy contrast to pepper's sweetness"),
        ],
    },
    "goat cheese": {
        "category": "dairy",
        "pairs": [
            ("fig", "Tangy, creamy cheese against fig's honeyed sweetness"),
            ("honey", "Sweetness balances goat cheese's tang"),
            ("walnut", "Earthy crunch against creamy tang"),
            ("beet", "Earthy sweetness that complements goat cheese's sharpness"),
        ],
    },
    "olive oil": {
        "category": "fat",
        "pairs": [
            ("garlic", "Infuses easily, spreading aroma through a dish"),
            ("lemon", "Base of countless vinaigrettes and marinades"),
            ("basil", "Carries basil's volatile aromatics"),
            ("tomato", "Fat carries tomato's aromatic compounds"),
        ],
    },
    "coconut milk": {
        "category": "fat",
        "pairs": [
            ("lime", "Tart acidity cuts coconut's richness"),
            ("chili", "Heat balanced by coconut's cooling richness"),
            ("ginger", "Aromatic spice against coconut's sweetness"),
            ("mango", "Tropical richness that pairs naturally with mango"),
            ("cilantro", "Fresh herb that lifts coconut's heaviness"),
        ],
    },
    "rice": {
        "category": "grain",
        "pairs": [
            ("soy sauce", "Umami seasoning that rice readily absorbs"),
            ("ginger", "Aromatic spice common in rice dishes"),
            ("coconut milk", "Rich, sweet cooking liquid for rice"),
            ("garlic", "Savory aromatic base for fried rice and pilafs"),
        ],
    },
    "chocolate": {
        "category": "other",
        "pairs": [
            ("orange", "Bitter cocoa against orange's bright sweetness — classic dessert pair"),
            ("chili", "Heat against bitter sweetness — classic mole pairing"),
            ("banana", "Classic dessert pairing — sweetness and bitterness together"),
            ("vanilla", "Rounds out and softens chocolate's bitterness"),
            ("sea salt", "Salt sharpens and balances chocolate's sweetness"),
            ("mint", "Cooling freshness against bitter sweetness"),
        ],
    },
    "honey": {
        "category": "other",
        "pairs": [
            ("lemon", "Sweet-tart balance common in dressings and drinks"),
            ("ginger", "Sweetness balances ginger's heat"),
            ("goat cheese", "Sweetness balances goat cheese's tang"),
            ("walnut", "Sweetness against nutty bitterness"),
            ("chili", "Sweet-and-spicy balance"),
        ],
    },
    "soy sauce": {
        "category": "other",
        "pairs": [
            ("ginger", "Umami-salty base that carries ginger's aroma"),
            ("garlic", "Savory foundation of countless Asian sauces"),
            ("honey", "Sweet-salty glaze balance"),
            ("sesame oil", "Nutty richness that rounds out soy's saltiness"),
            ("rice vinegar", "Acid that brightens soy's heavy saltiness"),
        ],
    },
    "coffee": {
        "category": "other",
        "pairs": [
            ("chocolate", "Bitter-on-bitter, deepens chocolate's intensity in desserts"),
            ("cinnamon", "Warm spice that complements coffee's roasted notes"),
            ("vanilla", "Sweetness that rounds out coffee's bitterness"),
            ("cream", "Rich dairy that mellows coffee's bitterness"),
        ],
    },
}
