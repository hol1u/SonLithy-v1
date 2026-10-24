from sonlithy_eval.types import ChatResponse, GenParams, Message


def test_shared_model_types_have_expected_defaults() -> None:
    params = GenParams()
    response = ChatResponse(content="ok")

    assert params.seed is None
    assert params.temperature == 0.0
    assert response.prompt_tokens is None
    assert Message(role="user", content="hello").content == "hello"