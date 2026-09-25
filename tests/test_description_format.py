"""Tests for the structured package description formatter."""
from description_format import format_description

BORACAY = """🌴 Boracay Newcoast: Escape the Crowds

Discover a different side of Boracay at Boracay Newcoast.

✨ What you can see & experience:

🏖️ Relax on Newcoast's white-sand beaches with clear turquoise waters.

🌅 Wake up to beautiful sunrise views along the eastern coastline.

✈️ Package Details

3 Days / 2 Nights

💰 Belmont Hotel — ₱6,999 per person
💰 Savoy Hotel — ₱6,999 per person
💰 Chancellor Hotel — ₱7,499 per person

🎒 Inclusions:

✈️ Roundtrip Airport Transfers
🍳 Daily Buffet Breakfast

🌊 Your Newcoast Boracay Escape Awaits!

Trade the crowds for peaceful coves.

Relax by the sea. 💙✨"""

SIARGAO = """🌴 Siargao: Embrace the Carefree Island Soul

Escape to the laid-back beauty of Siargao.

✨ What you can see & experience:

🏄 Surf at Cloud 9 and experience famous surfing spots
🤿 Swim and snorkel in crystal-clear waters
✈️ Package Details

3 Days / 2 Nights
💰 Price starts at ₱5,499

Inclusions:

🏨 Hotel Accommodation
🍳 Daily Breakfast"""


def html(text):
    return str(format_description(text))


class TestStructure:
    def test_first_line_is_the_headline_and_next_paragraph_the_intro(self):
        out = html(BORACAY)
        assert '<h3 class="rd-headline">🌴 Boracay Newcoast: Escape the Crowds</h3>' in out
        assert '<p class="rd-intro">Discover a different side' in out

    def test_emoji_lines_become_cards_with_their_emoji(self):
        out = html(BORACAY)
        assert out.count('class="rd-card"') == 2
        assert '<span class="rd-icon" aria-hidden="true">🏖️</span>' in out

    def test_colon_lines_become_section_labels_without_the_colon(self):
        out = html(BORACAY)
        assert '<div class="rd-label"><span>What you can see &amp; experience</span></div>' in out

    def test_short_plain_line_becomes_a_detail_pill(self):
        assert '<span class="rd-detail">3 Days / 2 Nights</span>' in html(BORACAY)

    def test_inclusions_become_chips_not_cards(self):
        out = html(BORACAY)
        assert '<span class="rd-chip">Roundtrip Airport Transfers</span>' in out

    def test_last_heading_with_only_paragraphs_after_becomes_closing_box(self):
        out = html(BORACAY)
        assert '<p class="rd-closing-title">Your Newcoast Boracay Escape Awaits!</p>' in out
        assert out.count('class="rd-closing-text"') == 2


class TestPrices:
    def test_several_prices_become_hotel_cards(self):
        out = html(BORACAY)
        assert out.count('class="rd-hotel"') == 3
        assert '<div class="rd-hotel-name">Chancellor Hotel</div>' in out
        assert '<div class="rd-hotel-price">₱7,499</div>' in out

    def test_single_price_becomes_one_row_not_a_lone_card(self):
        out = html(SIARGAO)
        assert 'class="rd-hotel"' not in out
        assert '<span class="rd-price-label">Price starts at</span>' in out
        assert "₱5,499" in out


TRAVEL_DATES = """Hong Kong Getaway

🗓️ Travel Dates
From Manila (2026):

Oct 26 – Nov 5 (+USD 100)
Oct 28 – Nov 7 (+USD 100)
Nov 18 – 28
Dec 23 – Jan 2 (+USD 500)

From Clark:

Oct 25 – Nov 4, 2026 (+USD 100)
Apr 22 – May 2, 2027 (+USD 100)"""


class TestAddOnFees:
    def test_plus_sign_is_kept_on_the_price(self):
        out = html(TRAVEL_DATES)
        assert '<div class="rd-hotel-price">+USD 100</div>' in out
        assert "+USD 500" in out

    def test_add_on_fee_is_labelled(self):
        assert '<span class="rd-unit">additional fee</span>' in html(TRAVEL_DATES)

    def test_full_date_range_is_kept_as_the_label(self):
        out = html(TRAVEL_DATES)
        assert '<div class="rd-hotel-name">Oct 26 – Nov 5</div>' in out
        assert '<div class="rd-hotel-name">Oct 25 – Nov 4, 2026</div>' in out
        assert '<span class="rd-price-label">Dec 23 – Jan 2</span>' in out

    def test_leftover_brackets_are_removed_from_the_label(self):
        assert "()" not in html(TRAVEL_DATES)

    def test_normal_prices_have_no_plus_or_fee_note(self):
        out = html(BORACAY)
        assert "+₱" not in out
        assert "additional fee" not in out


class TestMessySpacing:
    def test_section_name_is_a_label_even_without_a_blank_line_above(self):
        """In real descriptions "Package Details" often sits directly under
        the last bullet - it must still become a label, not a card."""
        out = html(SIARGAO)
        assert '<div class="rd-label"><span>Package Details</span></div>' in out
        assert '<span class="rd-card-text">Package Details</span>' not in out

    def test_detail_line_inside_a_block_is_still_a_pill(self):
        assert '<span class="rd-detail">3 Days / 2 Nights</span>' in html(SIARGAO)


class TestSafety:
    def test_html_in_a_description_is_escaped(self):
        out = html('Title\n\n<script>alert(1)</script>\n\n🏖️ <img src=x onerror=alert(1)> beach day')
        assert "<script>" not in out
        assert "<img" not in out
        assert "&lt;script&gt;" in out

    def test_bold_syntax_still_works(self):
        assert "<strong>Cloud 9</strong>" in html("Title\n\nSurf at **Cloud 9** today.")

    def test_empty_description_renders_nothing(self):
        assert html("") == ""
        assert html("   \n  ") == ""

    def test_plain_unstructured_text_falls_back_to_paragraphs(self):
        out = html("Just a simple package.\n\nNothing special in here, only sentences.")
        assert 'class="rd-headline"' in out
        assert 'class="rd-card"' not in out
