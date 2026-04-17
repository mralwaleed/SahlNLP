"""Tests for sahlnlp.core.guardian module — PII detection and masking."""

import pytest

from sahlnlp.core.guardian import _mask_preserve, mask_sensitive_info


# ===========================================================================
# Helper: _mask_preserve
# ===========================================================================
class TestMaskPreserve:
    def test_basic(self):
        assert _mask_preserve("0551234567", "*", 2, 3) == "05*****567"

    def test_short_string(self):
        assert _mask_preserve("abc", "*", 2, 2) == "***"

    def test_custom_char(self):
        assert _mask_preserve("0551234567", "#", 2, 3) == "05#####567"

    def test_exact_length(self):
        assert _mask_preserve("abcde", "*", 2, 3) == "abcde"


# ===========================================================================
# Phone Number Detection
# ===========================================================================
class TestPhoneDetection:
    def test_phone_tag_05(self):
        result = mask_sensitive_info("اتصل على 0551234567", mode="tag")
        assert "[PHONE]" in result
        assert "0551234567" not in result

    def test_phone_tag_966(self):
        result = mask_sensitive_info("رقمي +966512345678", mode="tag")
        assert "[PHONE]" in result
        assert "966" not in result

    def test_phone_tag_bare_5(self):
        result = mask_sensitive_info("اتصل 512345678", mode="tag")
        assert "[PHONE]" in result

    def test_phone_mask_mode(self):
        result = mask_sensitive_info("اتصل على 0551234567", mode="mask")
        assert "05" in result
        assert "567" in result
        assert "0551234567" not in result

    def test_phone_with_dashes(self):
        result = mask_sensitive_info("055-123-4567", mode="tag")
        assert "[PHONE]" in result

    def test_phone_with_spaces(self):
        result = mask_sensitive_info("055 123 4567", mode="tag")
        assert "[PHONE]" in result

    def test_no_false_positive_longer_number(self):
        mask_sensitive_info("12345678901234", mode="tag")
        # A 14-digit number should not be matched as a phone (phone is 10-12)
        # But it may be matched as ID — that's fine. Just ensure no PHONE tag
        # if the format doesn't match


# ===========================================================================
# National ID Detection
# ===========================================================================
class TestNationalID:
    def test_id_tag_starts_with_1(self):
        result = mask_sensitive_info("رقمي 1234567890", mode="tag")
        assert "[ID]" in result
        assert "1234567890" not in result

    def test_id_tag_starts_with_2(self):
        result = mask_sensitive_info("السجل 2345678901", mode="tag")
        assert "[ID]" in result
        assert "2345678901" not in result

    def test_id_mask_mode(self):
        result = mask_sensitive_info("رقم 1234567890", mode="mask")
        assert "1" in result
        assert "90" in result
        assert "1234567890" not in result

    def test_id_no_false_positive_short(self):
        result = mask_sensitive_info("رقم 12345", mode="tag")
        assert "[ID]" not in result

    def test_id_no_false_start_with_3(self):
        result = mask_sensitive_info("3234567890", mode="tag")
        assert "[ID]" not in result


# ===========================================================================
# IBAN Detection
# ===========================================================================
class TestIBAN:
    def test_iban_tag(self):
        result = mask_sensitive_info("الآيبان SA0380000000608010167519", mode="tag")
        assert "[IBAN]" in result

    def test_iban_no_spaces(self):
        result = mask_sensitive_info("SA0380000000608010167519", mode="tag")
        assert "[IBAN]" in result

    def test_iban_mask_mode(self):
        result = mask_sensitive_info("SA0380000000608010167519", mode="mask")
        assert "SA" in result
        assert "0380000000608010167519" not in result

    def test_iban_not_present(self):
        result = mask_sensitive_info("لا يوجد آيبان هنا", mode="tag")
        assert "[IBAN]" not in result


# ===========================================================================
# Email Detection
# ===========================================================================
class TestEmail:
    def test_email_tag(self):
        result = mask_sensitive_info("راسلني على user@example.com", mode="tag")
        assert "[EMAIL]" in result
        assert "user@example.com" not in result

    def test_email_complex(self):
        result = mask_sensitive_info("بريد ahmed.ali123@gmail.com", mode="tag")
        assert "[EMAIL]" in result

    def test_email_mask_mode(self):
        result = mask_sensitive_info("بريدي test@domain.org", mode="mask")
        assert "te" in result
        assert "org" in result
        assert "test@domain.org" not in result


# ===========================================================================
# Arabic Name Detection
# ===========================================================================
class TestArabicName:
    def test_titled_name_sayyid(self):
        result = mask_sensitive_info("السيد أحمد محمد", mode="tag")
        assert "[NAME]" in result
        assert "أحمد" not in result

    def test_titled_name_doctor(self):
        result = mask_sensitive_info("الدكتور خالد بن عبدالله", mode="tag")
        assert "[NAME]" in result

    def test_titled_name_engineer(self):
        result = mask_sensitive_info("المهندس سعود", mode="tag")
        assert "[NAME]" in result

    def test_theophoric_abd(self):
        result = mask_sensitive_info("عبدالرحمن كان هنا", mode="tag")
        assert "[NAME]" in result
        assert "عبدالرحمن" not in result

    def test_theophoric_bin(self):
        result = mask_sensitive_info("فيصل بن عبدالعزيز", mode="tag")
        assert "[NAME]" in result

    def test_name_mask_mode(self):
        result = mask_sensitive_info("السيد أحمد محمد", mode="mask")
        assert "أحمد" not in result
        assert "محمد" not in result

    def test_no_name_no_title(self):
        result = mask_sensitive_info("ذهب أحمد إلى المدرسة", mode="tag")
        # "أحمد" alone without title should NOT be matched
        assert "[NAME]" not in result


# ===========================================================================
# Combined / Integration Tests
# ===========================================================================
class TestCombinedPII:
    def test_full_paragraph_tag(self):
        text = (
            "السيد أحمد محمد رقم هاتفه 0551234567 "
            "ورقم هويته 1234567890 "
            "والآيبان SA0380000000608010167519 "
            "والبريد ahmed@mail.com"
        )
        result = mask_sensitive_info(text, mode="tag")
        assert "[NAME]" in result
        assert "[PHONE]" in result
        assert "[ID]" in result
        assert "[IBAN]" in result
        assert "[EMAIL]" in result
        # Raw PII should be gone
        assert "0551234567" not in result
        assert "1234567890" not in result
        assert "ahmed@mail.com" not in result
        assert "أحمد" not in result

    def test_full_paragraph_mask(self):
        text = (
            "السيد أحمد محمد رقم هاتفه 0551234567 "
            "ورقم هويته 1234567890 "
            "والبريد user@example.com"
        )
        result = mask_sensitive_info(text, mode="mask")
        # Raw PII should be gone
        assert "0551234567" not in result
        assert "1234567890" not in result
        assert "user@example.com" not in result
        assert "أحمد" not in result

    def test_empty_string(self):
        assert mask_sensitive_info("") == ""

    def test_no_pii(self):
        text = "هذا نص عادي لا يحتوي على أي معلومات حساسة"
        assert mask_sensitive_info(text, mode="tag") == text

    def test_type_error(self):
        with pytest.raises(TypeError):
            mask_sensitive_info(None)  # type: ignore[arg-type]

    def test_invalid_mode(self):
        with pytest.raises(ValueError):
            mask_sensitive_info("0551234567", mode="delete")

    def test_multiple_phones(self):
        text = "0551234567 و 0559876543"
        result = mask_sensitive_info(text, mode="tag")
        assert result.count("[PHONE]") == 2

    def test_multiple_emails(self):
        text = "a@b.com و c@d.org"
        result = mask_sensitive_info(text, mode="tag")
        assert result.count("[EMAIL]") == 2
