PROPERTY = {
    "property_id": "Dallas-NE-75231-MTR-01",
    "location": "Northeast Dallas / Vickery Meadow, Texas 75231",
    "property_type": "Entire furnished apartment",
    "bedrooms": 2,
    "bathrooms": 2,
    "monthly_rent": 3200,
    "minimum_stay_days": 30,
    "furnished": True,
    "utilities_included": True,
    "wifi": True,
    "workspace": True,
    "full_kitchen": True,
    "in_suite_laundry": True,
    "covered_parking_spaces": 2,
    "pets": "Small dog or cat subject to property rules and owner confirmation",
    "smoking": "No smoking inside",
    "nearby_medical_facilities": [
        "Texas Health Presbyterian Hospital Dallas",
        "Medical City Dallas Hospital",
        "First Baptist Medical Center",
        "Kindred Hospital Dallas Central",
    ],
    "highway_access": ["Hwy 75", "635 / LBJ Freeway"],
    "primary_conversion_channel": "Furnished Finder",
    "existing_channels": [
        "Airbnb",
        "Furnished Finder",
        "Booking.com",
        "CircleRN",
    ],
}


# V2 uses one broad, campaign-level discovery request instead of five separate
# model calls. Each request contains multiple intent, geography, and duration
# predicates so web search can maximize recall before AI qualification.
CAMPAIGN_QUERIES = {
    "healthcare": [
        (
            'Dallas OR "North Dallas" OR "Northeast Dallas" OR DFW '
            'healthcare housing demand: '
            '"looking for furnished housing" OR "need temporary housing" OR '
            '"seeking furnished apartment" OR "housing needed" OR '
            '"temporary relocation housing"; '
            'nurse OR "travel nurse" OR physician OR therapist OR medical; '
            '30 days OR "8 weeks" OR "13 weeks" OR "3 months"; '
            'include Texas Health Presbyterian Hospital Dallas and Medical City Dallas'
        )
    ],
    "corporate": [
        (
            'Dallas OR "North Dallas" OR DFW corporate temporary housing demand: '
            '"looking for furnished housing" OR "need temporary housing" OR '
            '"seeking furnished apartment" OR relocation; '
            'consultant OR "project manager" OR banking OR software OR IT; '
            '30 days OR "60 days" OR "90 days" OR "3 months"'
        )
    ],
    "relocation": [
        (
            'Dallas OR "North Dallas" OR DFW relocation housing demand: '
            '"relocating to Dallas" OR "moving to Dallas" OR "between homes" OR '
            '"home closing" OR "temporary relocation housing"; '
            'furnished OR temporary; 30 days OR "60 days" OR "90 days"'
        )
    ],
    "partners": [
        (
            'Dallas organizations arranging 30+ day furnished housing: '
            'travel nurse staffing OR healthcare staffing OR medical staffing OR '
            'corporate relocation OR insurance temporary housing OR displacement housing; '
            'prioritize organizations with evidence they coordinate housing for clients or employees'
        )
    ],
    "social": [
        (
            'Dallas OR "North Dallas" OR DFW public housing-demand signals: '
            '"looking for furnished housing" OR "need a furnished apartment" OR '
            '"temporary housing needed" OR "mid term housing" OR relocation; '
            'professional OR nurse OR consultant; 30 days OR "8 weeks" OR "13 weeks"'
        )
    ],
}
