from nonbonded.library.utilities.string import camel_to_kebab_case, camel_to_snake_case


def test_camel_to_snake_case():
    assert camel_to_snake_case("SomeName") == "some_name"


def test_camel_to_kebab_case():
    assert camel_to_kebab_case("SomeName") == "some-name"
