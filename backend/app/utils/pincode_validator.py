def validate_pincode(pincode: str) -> dict:
    SUPPORTED_STATES = ["Maharashtra", "Delhi", "Karnataka", "Tamil Nadu", "Gujarat"]

    if not isinstance(pincode, str) or len(pincode) != 6 or not pincode.isdigit():
        return {
            "valid": False, "state": None, "district": None,
            "is_supported": False, "languages": []
        }

    prefix = int(pincode[:3])
    prefix_2 = int(pincode[:2])

    state = None
    district = None
    languages = ["English"]

    # --- Precise Prefix Mappings ---
    if prefix == 110:
        state, district, languages = "Delhi", "Delhi", ["Hindi", "English"]
    elif prefix in (111, 112):
        state, district, languages = "Delhi", "Delhi", ["Hindi", "English"]
    elif prefix == 400:
        state, district, languages = "Maharashtra", "Mumbai City", ["Marathi", "Hindi", "English"]
    elif prefix == 401:
        state, district, languages = "Maharashtra", "Thane", ["Marathi", "Hindi", "English"]
    elif prefix == 402:
        state, district, languages = "Maharashtra", "Raigad", ["Marathi", "Hindi", "English"]
    elif prefix == 403:
        state, district, languages = "Goa", "Goa", ["Konkani", "Marathi", "English"]
    elif prefix == 405:
        state, district, languages = "Maharashtra", "Ahmednagar", ["Marathi", "Hindi", "English"]
    elif prefix == 406:
        state, district, languages = "Maharashtra", "Latur", ["Marathi", "Hindi", "English"]
    elif prefix == 407:
        state, district, languages = "Maharashtra", "Osmanabad", ["Marathi", "Hindi", "English"]
    elif prefix == 408:
        state, district, languages = "Maharashtra", "Satara", ["Marathi", "Hindi", "English"]
    elif prefix == 410:
        state, district, languages = "Maharashtra", "Pune", ["Marathi", "Hindi", "English"]
    elif prefix == 411:
        state, district, languages = "Maharashtra", "Pune City", ["Marathi", "Hindi", "English"]
    elif prefix == 412:
        state, district, languages = "Maharashtra", "Pune Rural", ["Marathi", "Hindi", "English"]
    elif prefix == 413:
        state, district, languages = "Maharashtra", "Solapur", ["Marathi", "Hindi", "English"]
    elif prefix == 414:
        state, district, languages = "Maharashtra", "Ahmednagar", ["Marathi", "Hindi", "English"]
    elif prefix == 415:
        state, district, languages = "Maharashtra", "Satara", ["Marathi", "Hindi", "English"]
    elif prefix == 416:
        state, district, languages = "Maharashtra", "Kolhapur", ["Marathi", "Hindi", "English"]
    elif prefix == 417:
        state, district, languages = "Maharashtra", "Sangli", ["Marathi", "Hindi", "English"]
    elif prefix == 418:
        state, district, languages = "Maharashtra", "Nanded", ["Marathi", "Hindi", "English"]
    elif prefix == 422:
        state, district, languages = "Maharashtra", "Nashik", ["Marathi", "Hindi", "English"]
    elif prefix == 423:
        state, district, languages = "Maharashtra", "Nashik Rural", ["Marathi", "Hindi", "English"]
    elif prefix == 424:
        state, district, languages = "Maharashtra", "Dhule", ["Marathi", "Hindi", "English"]
    elif prefix == 425:
        state, district, languages = "Maharashtra", "Jalgaon", ["Marathi", "Hindi", "English"]
    elif prefix == 431:
        state, district, languages = "Maharashtra", "Aurangabad", ["Marathi", "Hindi", "English"]
    elif prefix == 440:
        state, district, languages = "Maharashtra", "Nagpur City", ["Marathi", "Hindi", "English"]
    elif prefix == 441:
        state, district, languages = "Maharashtra", "Nagpur Rural", ["Marathi", "Hindi", "English"]
    elif prefix == 442:
        state, district, languages = "Maharashtra", "Wardha", ["Marathi", "Hindi", "English"]
    elif prefix == 443:
        state, district, languages = "Maharashtra", "Buldana", ["Marathi", "Hindi", "English"]
    elif prefix == 444:
        state, district, languages = "Maharashtra", "Akola", ["Marathi", "Hindi", "English"]
    elif prefix == 445:
        state, district, languages = "Maharashtra", "Yavatmal", ["Marathi", "Hindi", "English"]
    elif 500 <= prefix <= 509:
        state, district, languages = "Telangana", "Hyderabad", ["Telugu", "English"]
    elif 560 <= prefix <= 562:
        state, district, languages = "Karnataka", "Bengaluru", ["Kannada", "English"]
    elif 570 <= prefix <= 577:
        state, district, languages = "Karnataka", "Karnataka", ["Kannada", "English"]
    elif 600 <= prefix <= 603:
        state, district, languages = "Tamil Nadu", "Chennai", ["Tamil", "English"]
    elif 620 <= prefix <= 643:
        state, district, languages = "Tamil Nadu", "Tamil Nadu", ["Tamil", "English"]
    elif 380 <= prefix <= 396:
        state, district, languages = "Gujarat", "Gujarat", ["Gujarati", "Hindi", "English"]
    elif 700 <= prefix <= 743:
        if prefix == 700:
            district = "Kolkata"
        else:
            district = "West Bengal"
        state, languages = "West Bengal", ["Bengali", "English"]
    elif 800 <= prefix <= 855:
        state, district, languages = "Bihar/Jharkhand", "Bihar", ["Hindi", "English"]
    elif prefix == 226:
        state, district, languages = "Uttar Pradesh", "Lucknow", ["Hindi", "English"]
    elif 201 <= prefix <= 285:
        state, district, languages = "Uttar Pradesh", "Uttar Pradesh", ["Hindi", "English"]
    elif 302 <= prefix <= 345:
        state, district, languages = "Rajasthan", "Rajasthan", ["Hindi", "English"]
    elif 160 <= prefix <= 161:
        state, district, languages = "Chandigarh", "Chandigarh", ["Punjabi", "Hindi", "English"]
    elif prefix_2 == 40 or prefix_2 == 41 or prefix_2 == 42 or prefix_2 == 43 or prefix_2 == 44:
        # Catch-all for Maharashtra
        state, district, languages = "Maharashtra", "Maharashtra", ["Marathi", "Hindi", "English"]

    if state is None:
        return {
            "valid": True,
            "state": "Unknown",
            "district": "Unknown",
            "is_supported": False,
            "languages": ["English"]
        }

    return {
        "valid": True,
        "state": state,
        "district": district,
        "is_supported": state in SUPPORTED_STATES,
        "languages": languages
    }
