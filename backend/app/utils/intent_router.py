"""
Intent Router — Fast-path bypass for greetings and chitchat.
Prevents simple messages like "Hi" from running the full RAG pipeline.
"""

import re

# ── Patterns ──────────────────────────────────────────────────────────────────
_GREETING_RE = re.compile(
    r"^(hi+|hello+|hey+|hii+|namaste|namaskar|jai hind|jai bharat"
    r"|good\s?(morning|afternoon|evening|night)|sup|wassup|howdy)[\s!.?]*$",
    re.IGNORECASE,
)

_HOWRU_RE = re.compile(
    r"^(how are you|how r u|kaise ho|aap kaise hain|kaisa hai|you good)[\s?!.]*$",
    re.IGNORECASE,
)

_THANKS_RE = re.compile(
    r"^(thanks?|thank you|thankyou|shukriya|dhanyawad|ty|thx)[\s!.]*$",
    re.IGNORECASE,
)

_OK_RE = re.compile(
    r"^(ok|okay|alright|sure|theek hai|accha|got it|noted|understood|k)[\s.!]*$",
    re.IGNORECASE,
)

_BYE_RE = re.compile(
    r"^(bye|goodbye|good bye|alvida|see you|see ya|talk later|cya)[\s!.]*$",
    re.IGNORECASE,
)

# ── Instant responses ─────────────────────────────────────────────────────────
_GREETING_RESPONSE = (
    "Namaste! 🙏 I am **Sakhi**, your guide to Indian Government schemes.\n\n"
    "Ask me about any scheme — PM Kisan, Ayushman Bharat, PMAY, MNREGA, "
    "Ration Card, or anything else. How can I help you today?"
)

_HOWRU_RESPONSE = (
    "I'm always ready to help! 😊\n\n"
    "Ask me about any government scheme — eligibility, benefits, or how to apply."
)

_THANKS_RESPONSE = (
    "You're welcome! 🌟 Feel free to ask if you have more questions about any scheme."
)

_OK_RESPONSE = (
    "Sure! Let me know whenever you have a question about government schemes. 👍"
)

_BYE_RESPONSE = (
    "Goodbye! 👋 Come back anytime — I'm here to help with government scheme information."
)

# ── Router function ───────────────────────────────────────────────────────────

def get_chitchat_response(message: str) -> str | None:
    """
    Returns an instant plain-text response if the message is chitchat.
    Returns None if the message should go through the full RAG pipeline.
    
    Typical latency: ~0ms vs 2-4s for RAG.
    """
    msg = message.strip()

    if _GREETING_RE.match(msg):
        return _GREETING_RESPONSE

    if _HOWRU_RE.match(msg):
        return _HOWRU_RESPONSE

    if _THANKS_RE.match(msg):
        return _THANKS_RESPONSE

    if _OK_RE.match(msg):
        return _OK_RESPONSE

    if _BYE_RE.match(msg):
        return _BYE_RESPONSE

    return None  # Needs full RAG pipeline
