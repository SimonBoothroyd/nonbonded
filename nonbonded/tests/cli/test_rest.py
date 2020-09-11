from nonbonded.cli.rest import start_server as start_server_cli


class TestRESTCLI:
    def test_start_server(self, monkeypatch, runner):

        import uvicorn

        expected_message = "Start Server"

        def mock_run(*args, **kwargs):
            print(expected_message)

        monkeypatch.setattr(uvicorn, "run", mock_run)

        result = runner.invoke(start_server_cli)

        if result.exit_code != 0:
            raise result.exception

        assert f"{expected_message}\n" == result.output
