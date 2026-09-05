import re
from .schemas import QueryIntent, Subquestion

def decompose_query(query: str) -> list[Subquestion]:
    """
    Decompose a query into independent subquestions with specific intents.
    Uses deterministic rules based on explicit phrases.
    """
    q = query.lower()
    subquestions = []
    
    if "unknown" in q:
        subquestions.append(Subquestion(id="q_unknown", query=query, intent=QueryIntent.UNKNOWN))
        return subquestions

    # Define explicit phrase patterns for decomposition
    patterns = {
        QueryIntent.HISTORICAL_VERSION: [r"latest revision", r"historical version", r"previous version", r"current version", r"latest version"],
        QueryIntent.TESTING_FEE: [r"testing fee", r"testing charges", r"testing cost", r"fee for", r"charges for", r"fee\b", r"charge\b", r"cost\b"],
        QueryIntent.LABORATORY_SCOPE: [r"laboratory scope", r"lab scope", r"tests covered under", r"scope for"],
        QueryIntent.LABORATORY_LOOKUP: [r"which laboratories", r"which labs", r"laboratory for", r"labs for", r"laboratory\b", r"laboratories\b", r"labs?\b"],
        QueryIntent.QCO_APPLICABILITY: [r"mandatory certification", r"qco", r"compulsory certification", r"is mandatory", r"certification requirement"],
        QueryIntent.LICENCE_PROCEDURE: [r"how to apply", r"apply for", r"licence procedure", r"license procedure"],
        QueryIntent.CONSUMER_COMPLAINT: [r"complaint", r"bis care"],
        QueryIntent.HALLMARKING: [r"hallmarking", r"gold jewellery", r"huid"],
        QueryIntent.STANDARD_LOOKUP: [r"what is is \d+", r"title of is \d+", r"standard requirement", r"standard\b", r"is \d+"]
    }
    
    matched_intents = set()
    for intent, phrases in patterns.items():
        for phrase in phrases:
            if re.search(r'\b' + phrase + r'\b', q):
                matched_intents.add(intent)
                break
                
    # Specific IS matching without being caught by phrases
    if QueryIntent.STANDARD_LOOKUP not in matched_intents and re.search(r'\bis\s*\d+', q) and not matched_intents:
        # Only fallback to standard lookup if no specific sub-question matched (e.g. "What is IS 616?")
        matched_intents.add(QueryIntent.STANDARD_LOOKUP)
        
    if not matched_intents:
        # Fallback broad intents
        if "fee" in q or "charge" in q or "cost" in q:
            matched_intents.add(QueryIntent.TESTING_FEE)
        elif "laboratory" in q or "laboratories" in q or re.search(r'\blabs?\b', q):
            matched_intents.add(QueryIntent.LABORATORY_LOOKUP)
        elif "mandatory" in q or "compulsory" in q:
            matched_intents.add(QueryIntent.QCO_APPLICABILITY)
        elif "apply" in q or "certification" in q:
            matched_intents.add(QueryIntent.LICENCE_PROCEDURE)
        else:
             matched_intents.add(QueryIntent.GENERAL_BIS_INFORMATION)
             
    # Create subquestion for each matched intent (sorted for determinism)
    for i, intent in enumerate(sorted(matched_intents, key=lambda x: x.name)):
        subq_id = f"q_{intent.value.lower()}_{i}"
        subquestions.append(Subquestion(id=subq_id, query=query, intent=intent))
        
    return subquestions
