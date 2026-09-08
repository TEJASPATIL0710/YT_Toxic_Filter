from classifier.keyword_classifier import KeywordClassifier


def test_flags_known_toxic_term():
    clf = KeywordClassifier()
    result = clf.classify("You are such an idiot")
    assert result.toxicity_score >= 0.5
    assert result.is_toxic is True
    assert result.classifier_name == "keyword_baseline"


def test_clean_comment_not_flagged():
    clf = KeywordClassifier()
    result = clf.classify("Great video, thanks for sharing!")
    assert result.is_toxic is False
    assert result.toxicity_score == 0.0


def test_all_caps_nudges_score_up():
    clf = KeywordClassifier()
    result = clf.classify("THIS VIDEO IS TRASH AND YOU ARE TOO")
    # "trash" alone is 0.3; ALL CAPS should push it up but likely still
    # under the toxic threshold -- this test just checks the nudge applies
    assert result.toxicity_score > 0.3
