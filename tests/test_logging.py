from cloudops_rag_eval.logging import mask_mapping


def test_masks_sensitive_fields_and_email_values() -> None:
    masked = mask_mapping(
        {
            "authorization": "Bearer secret-token",
            "message": "contact alisher@example.com for access",
            "nested": {"api_key": "sk-test", "owner": "owner@example.com"},
        }
    )

    assert masked["authorization"] == "[masked]"
    assert masked["message"] == "contact [masked-email] for access"
    assert masked["nested"] == {"api_key": "[masked]", "owner": "[masked-email]"}
