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


# V2 uses one campaign-level discovery request. These are intentionally broad
# discovery briefs, not literal Boolean search expressions. AI qualification
# applies the strict lead rules after broad public-web discovery.
CAMPAIGN_QUERIES = {
    "healthcare": [
        (
            "Find recent public Dallas-area healthcare temporary-housing demand signals. "
            "Search several variations covering: people explicitly seeking furnished or "
            "temporary housing; travel nurses, physicians, therapists, technicians, and "
            "other medical professionals starting temporary Dallas assignments; staffing "
            "or healthcare organizations that arrange housing; and 30-day, 8-week, "
            "13-week, 90-day, or similar temporary assignments. Include Dallas, North "
            "Dallas, Northeast Dallas, DFW, Texas Health Presbyterian Hospital Dallas, "
            "Medical City Dallas, First Baptist Medical Center, and Kindred Hospital "
            "Dallas Central where useful. Do not require every result to contain all of "
            "these terms. Prioritize direct housing requests first, then organization "
            "leads, then credible assignment signals."
        )
    ],
    "corporate": [
        (
            "Find recent public Dallas-area corporate temporary-housing demand signals. "
            "Search several variations for consultants, project managers, banking and "
            "financial-services contractors, software and IT professionals, temporary "
            "assignments, corporate relocation, and people seeking furnished housing. "
            "Include Dallas, North Dallas, and DFW. Do not require an explicit housing "
            "request when a credible temporary assignment or relocation signal exists."
        )
    ],
    "relocation": [
        (
            "Find recent public Dallas-area relocation and displacement housing demand. "
            "Search several variations for people relocating to Dallas, moving between "
            "homes, waiting on a home closing, insurance-displaced households, temporary "
            "relocation, and furnished housing needs expected to last about 30 days or "
            "longer. Include Dallas, North Dallas, and DFW."
        )
    ],
    "partners": [
        (
            "Find Dallas-area organizations that may create or coordinate 30+ day furnished "
            "housing demand. Search healthcare staffing firms, travel-nurse staffing, "
            "medical staffing, corporate relocation firms, insurance temporary-housing "
            "coordinators, displacement-housing organizations, and employers arranging "
            "temporary lodging. Prioritize public evidence that the organization actively "
            "coordinates housing or temporary assignments in Dallas."
        )
    ],
    "social": [
        (
            "Find recent public Dallas-area social or community signals showing temporary "
            "housing demand. Search variations for people looking for furnished housing, "
            "temporary apartments, mid-term rentals, relocation housing, travel-nurse "
            "housing, consultant housing, and stays of roughly 30 days or longer. Include "
            "Dallas, North Dallas, Northeast Dallas, and DFW."
        )
    ],
}
