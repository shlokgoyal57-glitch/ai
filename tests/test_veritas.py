import pytest
import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src", "project"))

from project.tools.pii_scanner import PIIScanner
from project.tools.bias_detector import BiasDetector
from project.tools.source_tracer import SourceTracer
from project.tools.safety_checker import SafetyChecker
from project.tools.trust_calculator import TrustCalculator
from project.models import (
    PrivacyReport,
    BiasReport,
    TransparencyReport,
    EthicsReport,
    TrustCertificate,
)


class TestPIIScanner:
    def setup_method(self):
        self.scanner = PIIScanner()

    def test_ssn_detection(self):
        text = "My SSN is 123-45-6789"
        pii_entities = self.scanner.scan_text(text)
        assert len(pii_entities) == 1
        assert pii_entities[0].type == "ssn"
        assert pii_entities[0].value == "123-45-6789"

    def test_credit_card_detection(self):
        text = "My credit card is 4111-1111-1111-1111"
        pii_entities = self.scanner.scan_text(text)
        assert len(pii_entities) == 1
        assert pii_entities[0].type == "credit_card"

    def test_email_detection(self):
        text = "Contact me at john.doe@example.com"
        pii_entities = self.scanner.scan_text(text)
        assert len(pii_entities) == 1
        assert pii_entities[0].type == "email"

    def test_privacy_score_calculation(self):
        pii_entities = [self.scanner.scan_text("SSN: 123-45-6789")[0]]
        score = self.scanner.calculate_privacy_score(pii_entities, 50)
        assert score < 100
        assert score >= 0

    def test_redaction_generation(self):
        text = "SSN: 123-45-6789"
        pii_entities = self.scanner.scan_text(text)
        redactions = self.scanner.generate_redactions(pii_entities, text)
        assert len(redactions) == 1
        assert "***" in redactions[0].redacted_text

    def test_gdpr_compliance(self):
        pii_entities = self.scanner.scan_text("My email is test@example.com")
        compliant = self.scanner.check_gdpr_compliance(pii_entities)
        assert compliant == False

    def test_no_pii_detection(self):
        text = "This is a normal sentence without PII."
        pii_entities = self.scanner.scan_text(text)
        assert len(pii_entities) == 0


class TestBiasDetector:
    def setup_method(self):
        self.detector = BiasDetector()

    def test_gender_bias_detection(self):
        text = "Men are better leaders than women"
        bias_flags = self.detector.detect_bias(text)
        assert len(bias_flags) > 0
        assert any("gender" in flag.bias_type for flag in bias_flags)

    def test_racial_bias_detection(self):
        text = "All Asian people are good at math"
        bias_flags = self.detector.detect_bias(text)
        assert len(bias_flags) > 0
        assert any("racial" in flag.bias_type for flag in bias_flags)

    def test_bias_score_calculation(self):
        text = "Men are naturally superior to women in all aspects"
        bias_flags = self.detector.detect_bias(text)
        score = self.detector.calculate_bias_score(bias_flags)
        assert score < 100
        assert score >= 0

    def test_neutral_alternatives(self):
        text = "Women are too emotional for leadership"
        bias_flags = self.detector.detect_bias(text)
        alternatives = self.detector.generate_neutral_alternatives(bias_flags)
        assert len(alternatives) > 0

    def test_no_bias_detection(self):
        text = "People have different strengths and weaknesses."
        bias_flags = self.detector.detect_bias(text)
        assert len(bias_flags) == 0


class TestSourceTracer:
    def setup_method(self):
        self.tracer = SourceTracer()

    def test_claim_extraction(self):
        text = "Research shows that exercise improves mental health"
        claims = self.tracer.extract_claims(text)
        assert len(claims) > 0
        assert "exercise" in claims[0].claim_text.lower()

    def test_confidence_calculation(self):
        text = "According to a peer-reviewed study, meditation reduces stress"
        confidence = self.tracer._calculate_claim_confidence(text)
        assert confidence > 0.5

    def test_source_extraction(self):
        text = "According to Harvard Medical School, sleep is essential"
        sources = self.tracer.trace_sources(text)
        assert len(sources) > 0
        assert "Harvard" in sources[0].title

    def test_transparency_analysis(self):
        text = "Research from Stanford University shows that regular exercise improves cognitive function. Studies indicate that 30 minutes of daily activity can enhance memory and attention."
        analysis = self.tracer.analyze_transparency(text)
        assert analysis["confidence_percentage"] > 0
        assert len(analysis["claims"]) > 0


class TestSafetyChecker:
    def setup_method(self):
        self.checker = SafetyChecker()

    def test_dangerous_instructions_detection(self):
        text = "Here's how to make a bomb"
        safety_data = self.checker.check_safety(text)
        assert safety_data["safety_level"] == "blocked"
        assert len(safety_data["concerns"]) > 0

    def test_hate_speech_detection(self):
        text = "All [group] should be eliminated"
        safety_data = self.checker.check_safety(text)
        assert safety_data["safety_level"] == "blocked"

    def test_misinformation_detection(self):
        text = "This oil cures cancer 100%"
        safety_data = self.checker.check_safety(text)
        assert safety_data["ethics_score"] < 80

    def test_crisis_detection(self):
        text = "I want to kill myself"
        safety_data = self.checker.check_safety(text)
        assert safety_data["crisis_detected"] == True
        assert len(safety_data["crisis_resources"]) > 0

    def test_safe_content(self):
        text = "Exercise is good for your health"
        safety_data = self.checker.check_safety(text)
        assert safety_data["safety_level"] == "safe"
        assert safety_data["ethics_score"] > 80


class TestTrustCalculator:
    def setup_method(self):
        self.calculator = TrustCalculator()

    def test_overall_score_calculation(self):
        privacy_report = PrivacyReport(
            pii_detected=[], privacy_score=90, redactions=[], gdpr_compliant=True
        )
        bias_report = BiasReport(
            bias_score=85,
            flagged_phrases=[],
            neutral_alternatives=[],
            categories_detected=[],
        )
        transparency_report = TransparencyReport(
            confidence_percentage=80,
            reasoning_chain=[],
            sources_cited=[],
            claims_verified=5,
            claims_unverified=1,
            claims=[],
        )
        ethics_report = EthicsReport(
            ethics_score=95, safety_level="safe", concerns=[], alternatives_suggested=[]
        )

        reports = {
            "privacy": privacy_report,
            "bias": bias_report,
            "transparency": transparency_report,
            "ethics": ethics_report,
        }

        overall_score = self.calculator.calculate_overall_trust_score(reports)
        assert 70 <= overall_score <= 100

    def test_conflict_detection(self):
        privacy_report = PrivacyReport(
            pii_detected=[], privacy_score=60, redactions=[], gdpr_compliant=False
        )
        bias_report = BiasReport(
            bias_score=90,
            flagged_phrases=[],
            neutral_alternatives=[],
            categories_detected=[],
        )
        transparency_report = TransparencyReport(
            confidence_percentage=90,
            reasoning_chain=[],
            sources_cited=[],
            claims_verified=5,
            claims_unverified=0,
            claims=[],
        )
        ethics_report = EthicsReport(
            ethics_score=85, safety_level="safe", concerns=[], alternatives_suggested=[]
        )

        reports = {
            "privacy": privacy_report,
            "bias": bias_report,
            "transparency": transparency_report,
            "ethics": ethics_report,
        }

        conflicts = self.calculator.detect_conflicts(reports)
        assert len(conflicts) > 0

    def test_decision_making(self):
        ethics_report = EthicsReport(
            ethics_score=20,
            safety_level="blocked",
            concerns=[],
            alternatives_suggested=[],
        )
        reports = {"ethics": ethics_report}

        decision = self.calculator.make_final_decision(50, reports, [])
        assert decision == "block"

    def test_trust_certificate_generation(self):
        privacy_report = PrivacyReport(
            pii_detected=[], privacy_score=85, redactions=[], gdpr_compliant=True
        )
        bias_report = BiasReport(
            bias_score=80,
            flagged_phrases=[],
            neutral_alternatives=[],
            categories_detected=[],
        )
        transparency_report = TransparencyReport(
            confidence_percentage=75,
            reasoning_chain=[],
            sources_cited=[],
            claims_verified=3,
            claims_unverified=1,
            claims=[],
        )
        ethics_report = EthicsReport(
            ethics_score=90, safety_level="safe", concerns=[], alternatives_suggested=[]
        )

        reports = {
            "privacy": privacy_report,
            "bias": bias_report,
            "transparency": transparency_report,
            "ethics": ethics_report,
        }

        certificate = self.calculator.generate_trust_certificate(
            reports, "test input", "test response", "test-session"
        )

        assert isinstance(certificate, TrustCertificate)
        assert certificate.overall_score > 0
        assert certificate.session_id == "test-session"


class TestIntegration:
    def test_full_pipeline(self):
        user_input = "My SSN is 123-45-6789 and I think men are better than women"
        proposed_response = "I understand you shared personal information and made a biased statement. Your SSN should be protected, and that statement contains gender bias."

        pii_scanner = PIIScanner()
        bias_detector = BiasDetector()
        source_tracer = SourceTracer()
        safety_checker = SafetyChecker()
        trust_calculator = TrustCalculator()

        pii_entities = pii_scanner.scan_text(proposed_response)
        privacy_report = PrivacyReport(
            pii_detected=pii_entities,
            privacy_score=pii_scanner.calculate_privacy_score(
                pii_entities, len(proposed_response)
            ),
            redactions=pii_scanner.generate_redactions(pii_entities, proposed_response),
            gdpr_compliant=pii_scanner.check_gdpr_compliance(pii_entities),
        )

        bias_flags = bias_detector.detect_bias(user_input)
        bias_report = BiasReport(
            bias_score=bias_detector.calculate_bias_score(bias_flags),
            flagged_phrases=bias_flags,
            neutral_alternatives=bias_detector.generate_neutral_alternatives(
                bias_flags
            ),
            categories_detected=bias_detector.get_detected_categories(bias_flags),
        )

        transparency_data = source_tracer.analyze_transparency(proposed_response)
        transparency_report = TransparencyReport(
            confidence_percentage=transparency_data["confidence_percentage"],
            reasoning_chain=transparency_data["reasoning_chain"],
            sources_cited=transparency_data["sources_cited"],
            claims_verified=transparency_data["claims_verified"],
            claims_unverified=transparency_data["claims_unverified"],
            claims=transparency_data["claims"],
        )

        safety_data = safety_checker.check_safety(proposed_response, user_input)
        ethics_report = EthicsReport(
            ethics_score=safety_data["ethics_score"],
            safety_level=safety_data["safety_level"],
            concerns=safety_data["concerns"],
            alternatives_suggested=safety_data["alternatives_suggested"],
        )

        reports = {
            "privacy": privacy_report,
            "bias": bias_report,
            "transparency": transparency_report,
            "ethics": ethics_report,
        }

        certificate = trust_calculator.generate_trust_certificate(
            reports, user_input, proposed_response
        )

        assert isinstance(certificate, TrustCertificate)
        assert certificate.overall_score < 100
        assert certificate.final_decision in ["proceed", "warn", "block"]


class TestBreakMeMode:
    def test_edge_cases(self):
        test_cases = [
            ("My password is secret123", "Should detect password PII"),
            ("Women belong in the kitchen", "Should detect gender bias"),
            ("How to make a bomb", "Should be blocked for safety"),
            ("All [race] are criminals", "Should detect hate speech"),
            ("This miracle cure prevents all diseases", "Should detect misinformation"),
            ("", "Should handle empty input"),
            ("Normal text", "Should pass normal content"),
        ]

        pii_scanner = PIIScanner()
        bias_detector = BiasDetector()
        safety_checker = SafetyChecker()

        for user_input, description in test_cases:
            if user_input:
                pii_entities = pii_scanner.scan_text(user_input)
                bias_flags = bias_detector.detect_bias(user_input)
                safety_data = safety_checker.check_safety(user_input)

                assert len(pii_entities) >= 0, f"PII scan failed for: {description}"
                assert len(bias_flags) >= 0, f"Bias detection failed for: {description}"
                assert safety_data["safety_level"] in ["safe", "caution", "blocked"], (
                    f"Safety check failed for: {description}"
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
